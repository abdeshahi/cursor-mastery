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
    const released = await this.db.releaseStaleProvisioningClaims();
    if (released.length > 0) {
      this.logger.warn('order.recover.stale_released', { count: released.length });
    }
    const orders = await this.db.listRecoverableOrders();
    for (const order of orders) {
      this.logger.warn('order.recover.start', { orderId: order.id, status: order.status });
      await this.provisionOrder(order.id);
    }
  }

  async recoverExpiredProvisioningClaims(): Promise<void> {
    const orders = await this.db.releaseStaleProvisioningClaims();
    for (const order of orders) {
      this.logger.warn('order.recover.lease_expired', { orderId: order.id });
      await this.provisionOrder(order.id);
    }
  }

  /** Marzban rotates /sub tokens on restart; keep DB links in sync. */
  async syncSubscriptionUrls(): Promise<void> {
    const rows = await this.db.listActiveSubscriptions();
    for (const row of rows) {
      try {
        await this.refreshSubscriptionUrl(row);
      } catch (error) {
        this.logger.warn('subscription.url.sync_failed', {
          subscriptionId: row.id,
          username: row.marzban_username,
          detail: error instanceof Error ? error.message : String(error),
        });
      }
    }
  }

  async refreshSubscriptionUrl(subscription: SubscriptionRow): Promise<SubscriptionRow> {
    const user = await this.marzban.getUser(subscription.marzban_username);
    if (user === null) {
      throw new Error(`marzban user missing: ${subscription.marzban_username}`);
    }
    const freshUrl = resolveSubscriptionUrl(
      user.subscription_url,
      this.env.MARZBAN_SUBSCRIPTION_URL_PREFIX,
    );
    if (freshUrl === subscription.subscription_url) {
      return subscription;
    }
    this.logger.info('subscription.url.refreshed', {
      subscriptionId: subscription.id,
      username: subscription.marzban_username,
    });
    return this.db.updateSubscriptionUrl(subscription.id, freshUrl);
  }

  async provisionOrder(orderId: number): Promise<SubscriptionRow | null> {
    const order = await this.db.getOrder(orderId);
    if (order === null) {
      this.logger.error('order.missing', { orderId });
      return null;
    }

    if (order.status === 'completed') {
      return this.subscriptionForCompletedOrder(order);
    }
    if (order.status !== 'paid' && order.status !== 'failed') {
      this.logger.warn('order.provision.conflict', { orderId, status: order.status });
      return null;
    }

    // Database compare-and-swap: only one caller can move paid/failed to
    // provisioning. A concurrent caller sees no row and must not call Marzban.
    const claimed = await this.db.claimOrderForProvisioning(orderId);
    if (claimed === null) {
      const current = await this.db.getOrder(orderId);
      if (current?.status === 'completed') {
        return this.subscriptionForCompletedOrder(current);
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
        const existingSubscription = await this.db.getSubscriptionByOrder(orderId);
        subscription =
          existingSubscription ??
          (await this.createNew(claimed, plan, node, now, proxies));
      }

      const completed = await this.db.completeProvisioning(orderId);
      if (completed === null) {
        throw new Error('order provisioning claim was lost before completion');
      }

      subscription = await this.refreshSubscriptionUrl(subscription);
      try {
        const configLinks = await this.fetchConfigLinks(subscription.subscription_url);
        await this.notifier.notifyCustomer(
          Number(user.telegram_id),
          this.deliveryMessage(plan.name, subscription, configLinks),
        );
      } catch (error) {
        // Provisioning is already complete. A Telegram outage must not roll it
        // back or cause the VPN account to be recreated on retry.
        this.logger.error('customer.provision.notify_failed', {
          orderId,
          detail: error instanceof Error ? error.message : String(error),
        });
      }
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

  private async subscriptionForCompletedOrder(
    order: {
      id: number;
      kind: 'new' | 'renewal';
      renewal_subscription_id: number | null;
    },
  ): Promise<SubscriptionRow | null> {
    if (order.kind === 'renewal' && order.renewal_subscription_id !== null) {
      return this.db.getSubscription(order.renewal_subscription_id);
    }
    return this.db.getSubscriptionByOrder(order.id);
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

  async formatServiceMessage(subscription: SubscriptionRow): Promise<string> {
    const refreshed = await this.refreshSubscriptionUrl(subscription);
    const configLinks = await this.fetchConfigLinks(refreshed.subscription_url);
    return this.serviceMessage(refreshed, configLinks);
  }

  private async fetchConfigLinks(subscriptionUrl: string): Promise<string[]> {
    try {
      return await this.marzban.fetchSubscriptionLinks(subscriptionUrl);
    } catch (error) {
      this.logger.warn('subscription.links.fetch_failed', {
        detail: error instanceof Error ? error.message : String(error),
      });
      return [];
    }
  }

  private deliveryMessage(
    planName: string,
    subscription: SubscriptionRow,
    configLinks: string[],
  ): string {
    return this.serviceMessage(subscription, configLinks, planName);
  }

  private serviceMessage(
    subscription: SubscriptionRow,
    configLinks: string[],
    planName?: string,
  ): string {
    const lines: string[] = [];
    if (planName !== undefined) {
      lines.push('✅ سرویس VPN شما فعال شد.', '');
      lines.push(`📦 پلن: ${escapePlain(planName)}`);
    }
    lines.push(
      `📊 حجم: ${subscription.traffic_gb} گیگابایت`,
      `⏳ اعتبار تا: ${subscription.expire_at.toLocaleString('fa-IR', { timeZone: 'Asia/Tehran' })}`,
      '',
    );

    if (configLinks.length > 0) {
      lines.push('⚡ کانفیگ VLESS (حتماً از این استفاده کنید):');
      for (const link of configLinks) {
        lines.push(`<code>${escapePlain(link)}</code>`);
      }
      lines.push('');
    }

    lines.push('🔗 لینک اشتراک:');
    lines.push(`<code>${escapePlain(subscription.subscription_url)}</code>`);
    lines.push('');
    lines.push('📱 v2rayNG:');
    lines.push('۱. کانفیگ قبلی را حذف کنید');
    lines.push('۲. لینک ⚡ را کپی → + → Import config from clipboard');
    lines.push('   یا لینک اشتراک را از بخش Subscription group settings وارد کنید');
    lines.push('۳. Flow باید xtls-rprx-vision باشد (خودکار پر می‌شود)');
    lines.push('۴. تست پینگ → اتصال');
    lines.push('');
    lines.push('اگر مشکلی بود از منوی پشتیبانی پیام بدهید.');
    return lines.join('\n');
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
