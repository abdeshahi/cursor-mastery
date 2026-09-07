import type { Environment } from '../config/env.js';
import type { Logger } from '../config/logger.js';
import type { Repositories, SubscriptionRow } from '../database/repositories.js';
import { MarzbanClient, MarzbanError } from '../marzban/client.js';
import {
  assignNode,
  bytesFromGb,
  marzbanUsernameForOrder,
  nextExpiry,
  resolveSubscriptionUrl,
  unixSeconds,
} from '../utils/provisioning.js';
import { canStartProvisioning } from '../utils/state-machine.js';

export interface Notifier {
  notifyCustomer(telegramId: number, html: string): Promise<void>;
  notifyAdmins(html: string): Promise<void>;
}

export class ProvisioningService {
  constructor(
    private readonly env: Environment,
    private readonly logger: Logger,
    private readonly db: Repositories,
    private readonly marzban: MarzbanClient,
    private readonly notifier: Notifier,
  ) {}

  async recoverStuckOrders(): Promise<void> {
    const orders = await this.db.listRecoverableOrders();
    for (const order of orders) {
      this.logger.warn('order.recover.start', { orderId: order.id, status: order.status });
      await this.provisionOrder(order.id);
    }
  }

  async provisionOrder(orderId: number): Promise<SubscriptionRow | null> {
    const order = await this.db.getOrder(orderId);
    if (order === null) {
      this.logger.error('order.missing', { orderId });
      return null;
    }

    const decision = canStartProvisioning(order.status);
    if (decision === 'skip') {
      return this.db.getSubscriptionByOrder(orderId);
    }
    if (decision === 'conflict') {
      this.logger.warn('order.provision.conflict', { orderId, status: order.status });
      return null;
    }

    const claimed = await this.db.updateOrderStatus(
      orderId,
      decision === 'start' ? ['paid'] : ['paid', 'provisioning', 'failed'],
      'provisioning',
    );
    if (claimed === null) {
      const current = await this.db.getOrder(orderId);
      if (current?.status === 'completed') {
        return this.db.getSubscriptionByOrder(orderId);
      }
      this.logger.warn('order.provision.already_claimed', { orderId });
      return null;
    }

    try {
      const plan = await this.db.getPlan(claimed.plan_id);
      const user = await this.db.getUserById(claimed.user_id);
      if (plan === null || user === null) {
        throw new Error('plan or user missing for order');
      }

      const now = new Date();
      const node = assignNode(plan.node, this.env.DEFAULT_NODE);
      const proxies = this.proxiesForPlan(plan.marzban_profile);

      let subscription: SubscriptionRow;
      if (claimed.kind === 'renewal' && claimed.renewal_subscription_id !== null) {
        subscription = await this.renewExisting(claimed, plan, node, now, proxies);
      } else {
        subscription = await this.createNew(claimed, plan, node, now, proxies);
      }

      const completed = await this.db.updateOrderStatus(orderId, ['provisioning'], 'completed');
      if (completed === null) {
        this.logger.warn('order.complete.race', { orderId });
      }

      await this.notifier.notifyCustomer(
        Number(user.telegram_id),
        this.deliveryMessage(plan.name, subscription),
      );
      return subscription;
    } catch (error) {
      const detail = error instanceof Error ? error.message : String(error);
      this.logger.error('order.provision.failed', { orderId, detail });
      await this.db.updateOrderStatus(orderId, ['provisioning'], 'failed');
      await this.notifier.notifyAdmins(
        `Provisioning failed for order <code>${orderId}</code>\n${escapePlain(detail)}`,
      );
      if (error instanceof MarzbanError) {
        return null;
      }
      return null;
    }
  }

  private async createNew(
    order: { id: number; user_id: number },
    plan: { traffic_gb: number; duration_days: number; marzban_profile: string | null },
    node: string,
    now: Date,
    extra: { proxies?: Record<string, unknown>; inbounds?: Record<string, unknown> },
  ): Promise<SubscriptionRow> {
    const username = marzbanUsernameForOrder(order.id);
    const expireAt = nextExpiry(null, now, plan.duration_days);
    const existing = await this.marzban.getUser(username);
    const user =
      existing === null
        ? await this.marzban.createUser({
            username,
            expireUnix: unixSeconds(expireAt),
            dataLimitBytes: bytesFromGb(plan.traffic_gb),
            note: `order:${order.id}`,
            ...extra,
          })
        : await this.marzban.modifyUser(username, {
            expireUnix: unixSeconds(expireAt),
            dataLimitBytes: bytesFromGb(plan.traffic_gb),
            status: 'active',
          });

    const url = resolveSubscriptionUrl(user.subscription_url, this.env.MARZBAN_SUBSCRIPTION_URL_PREFIX);
    return this.db.insertSubscription({
      userId: order.user_id,
      orderId: order.id,
      marzbanUsername: username,
      subscriptionUrl: url,
      trafficGb: plan.traffic_gb,
      startAt: now,
      expireAt,
      node,
    });
  }

  private async renewExisting(
    order: { id: number; user_id: number; renewal_subscription_id: number | null },
    plan: { traffic_gb: number; duration_days: number },
    node: string,
    now: Date,
    extra: { proxies?: Record<string, unknown>; inbounds?: Record<string, unknown> },
  ): Promise<SubscriptionRow> {
    if (order.renewal_subscription_id === null) {
      throw new Error('renewal order missing subscription id');
    }
    const current = await this.db.getSubscription(order.renewal_subscription_id);
    if (current === null) {
      throw new Error('subscription to renew not found');
    }

    const expireAt = nextExpiry(current.expire_at, now, plan.duration_days);
    const marzbanUser = await this.marzban.getUser(current.marzban_username);
    if (marzbanUser === null) {
      await this.marzban.createUser({
        username: current.marzban_username,
        expireUnix: unixSeconds(expireAt),
        dataLimitBytes: bytesFromGb(plan.traffic_gb),
        note: `renew-order:${order.id}`,
        ...extra,
      });
    } else {
      await this.marzban.resetTraffic(current.marzban_username);
      await this.marzban.modifyUser(current.marzban_username, {
        expireUnix: unixSeconds(expireAt),
        dataLimitBytes: bytesFromGb(plan.traffic_gb),
        status: 'active',
      });
    }

    const latest = await this.marzban.getUser(current.marzban_username);
    const url = resolveSubscriptionUrl(
      latest?.subscription_url ?? current.subscription_url,
      this.env.MARZBAN_SUBSCRIPTION_URL_PREFIX,
    );

    return this.db.updateSubscriptionRenewal({
      id: current.id,
      orderId: order.id,
      subscriptionUrl: url,
      trafficGb: plan.traffic_gb,
      expireAt,
      node,
    });
  }

  private proxiesForPlan(profile: string | null): {
    proxies?: Record<string, unknown>;
    inbounds?: Record<string, unknown>;
  } {
    if (profile === null || profile.trim().length === 0) {
      return {};
    }
    const trimmed = profile.trim();
    if (trimmed.startsWith('{')) {
      try {
        const parsed: unknown = JSON.parse(trimmed);
        if (parsed !== null && typeof parsed === 'object' && !Array.isArray(parsed)) {
          const object = parsed as Record<string, unknown>;
          return {
            proxies: asObject(object['proxies']),
            inbounds: asObject(object['inbounds']),
          };
        }
      } catch {
        this.logger.warn('plan.marzban_profile.invalid_json', { profile: trimmed });
      }
    }
    return {};
  }

  private deliveryMessage(planName: string, subscription: SubscriptionRow): string {
    return [
      '✅ سرویس VPN شما فعال شد.',
      '',
      `📦 پلن: ${escapePlain(planName)}`,
      `📊 حجم: ${subscription.traffic_gb} گیگابایت`,
      `⏳ اعتبار تا: ${subscription.expire_at.toLocaleString('fa-IR', { timeZone: 'Asia/Tehran' })}`,
      '',
      '🔗 لینک اشتراک:',
      `<code>${escapePlain(subscription.subscription_url)}</code>`,
      '',
      'راهنمای اتصال:',
      `۱. یکی از برنامه‌ها را نصب کنید: ${escapePlain(this.env.CONNECTION_APPS)}`,
      '۲. لینک بالا را کپی کنید.',
      '۳. در برنامه، اشتراک (Subscription) را از کلیپ‌بورد اضافه کنید.',
      '۴. اتصال را روشن کنید.',
      '',
      'اگر مشکلی بود از منوی پشتیبانی پیام بدهید.',
    ].join('\n');
  }
}

function asObject(value: unknown): Record<string, unknown> | undefined {
  if (value === null || value === undefined || typeof value !== 'object' || Array.isArray(value)) {
    return undefined;
  }
  return value as Record<string, unknown>;
}

function escapePlain(value: string): string {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}
