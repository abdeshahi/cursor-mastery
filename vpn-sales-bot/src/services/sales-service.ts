import type { Environment } from '../config/env.js';
import { isAdmin } from '../config/env.js';
import type { Logger } from '../config/logger.js';
import type { PlanRow, Repositories, SubscriptionRow } from '../database/repositories.js';
import { escapeHtml, formatAmount, formatDate } from '../utils/format.js';
import { nextPaymentApproval, nextPaymentRejection } from '../utils/state-machine.js';
import type { ProvisioningService } from './provisioning-service.js';

export class SalesService {
  constructor(
    private readonly env: Environment,
    private readonly logger: Logger,
    private readonly db: Repositories,
    private readonly provisioning: ProvisioningService,
  ) {}

  async ensureUser(from: {
    id: number;
    username?: string;
    first_name?: string;
  }): Promise<{ id: number; blocked: boolean }> {
    const user = await this.db.upsertUser({
      telegramId: from.id,
      username: from.username,
      firstName: from.first_name,
    });
    return { id: user.id, blocked: user.status === 'blocked' };
  }

  async activePlans(): Promise<PlanRow[]> {
    return this.db.listActivePlans();
  }

  async createPurchase(userId: number, planId: number): Promise<{ orderId: number; plan: PlanRow }> {
    const plan = await this.db.getPlan(planId);
    if (plan === null || !plan.is_active) {
      throw new Error('PLAN_NOT_FOUND');
    }
    await this.db.cancelOpenOrders(userId);
    const order = await this.db.createOrder({
      userId,
      planId: plan.id,
      amount: plan.price,
      kind: 'new',
    });
    this.logger.info('order.created', { orderId: order.id, userId, planId });
    return { orderId: order.id, plan };
  }

  async cancelOrder(userId: number, orderId: number): Promise<boolean> {
    return this.db.cancelOrder(orderId, userId);
  }

  async createRenewal(
    userId: number,
    subscriptionId: number,
    planId: number,
  ): Promise<{ orderId: number; plan: PlanRow }> {
    const subscription = await this.db.getSubscription(subscriptionId);
    if (subscription === null || subscription.user_id !== userId) {
      throw new Error('SUBSCRIPTION_NOT_FOUND');
    }
    if (subscription.status === 'cancelled') {
      throw new Error('SUBSCRIPTION_NOT_FOUND');
    }
    const plan = await this.db.getPlan(planId);
    if (plan === null || !plan.is_active) {
      throw new Error('PLAN_NOT_FOUND');
    }
    await this.db.cancelOpenOrders(userId);
    const order = await this.db.createOrder({
      userId,
      planId: plan.id,
      amount: plan.price,
      kind: 'renewal',
      renewalSubscriptionId: subscription.id,
    });
    this.logger.info('order.renewal.created', { orderId: order.id, subscriptionId, planId });
    return { orderId: order.id, plan };
  }

  paymentInstructions(plan: PlanRow, orderId: number): string {
    const bank = this.env.PAYMENT_BANK_NAME.trim();
    return [
      'سفارش ثبت شد. لطفاً مبلغ را کارت‌به‌کارت کنید.',
      '',
      `شماره سفارش: <code>${orderId}</code>`,
      `پلن: ${escapeHtml(plan.name)}`,
      `مبلغ: <b>${formatAmount(plan.price, plan.currency)}</b>`,
      '',
      bank.length > 0 ? `بانک: ${escapeHtml(bank)}` : '',
      `شماره کارت: <code>${escapeHtml(this.env.PAYMENT_CARD_NUMBER)}</code>`,
      `به نام: ${escapeHtml(this.env.PAYMENT_CARD_HOLDER)}`,
      '',
      escapeHtml(this.env.PAYMENT_NOTE),
    ]
      .filter((line) => line.length > 0)
      .join('\n');
  }

  async saveReceipt(input: {
    telegramId: number;
    fileId: string;
    kind: 'photo' | 'document';
  }): Promise<
    | { paymentId: number; orderId: number; plan: PlanRow; amount: number; userLabel: string }
    | { error: string }
  > {
    const user = await this.db.upsertUser({ telegramId: input.telegramId });
    if (user.status === 'blocked') {
      return { error: 'حساب شما مسدود است.' };
    }
    const order = await this.db.findOpenOrderForUser(user.id);
    if (order === null) {
      return { error: 'سفارش باز برای پرداخت پیدا نشد. از منو «خرید VPN» را بزنید.' };
    }
    const plan = await this.db.getPlan(order.plan_id);
    if (plan === null) {
      return { error: 'پلن سفارش پیدا نشد. پشتیبانی را خبر کنید.' };
    }
    const payment = await this.db.upsertPendingPayment({
      orderId: order.id,
      userId: user.id,
      amount: order.amount,
      receiptFileId: input.fileId,
      receiptKind: input.kind,
    });
    this.logger.info('payment.receipt.saved', { paymentId: payment.id, orderId: order.id });
    return {
      paymentId: payment.id,
      orderId: order.id,
      plan,
      amount: order.amount,
      userLabel: this.userLabel(user.telegram_id, user.telegram_username, user.first_name),
    };
  }

  adminReceiptCaption(input: {
    userLabel: string;
    orderId: number;
    plan: PlanRow;
    amount: number;
    paymentId: number;
  }): string {
    return [
      'رسید پرداخت جدید',
      `کاربر: ${escapeHtml(input.userLabel)}`,
      `سفارش: <code>${input.orderId}</code>`,
      `پرداخت: <code>${input.paymentId}</code>`,
      `پلن: ${escapeHtml(input.plan.name)}`,
      `مبلغ: ${formatAmount(input.amount, input.plan.currency)}`,
    ].join('\n');
  }

  async approve(paymentId: number, actorTelegramId: number): Promise<{ message: string; duplicate: boolean }> {
    if (!isAdmin(this.env, actorTelegramId)) {
      this.logger.warn('admin.approve.denied', { actorTelegramId, paymentId });
      return { message: 'اجازه این کار را ندارید.', duplicate: false };
    }

    const current = await this.db.getPayment(paymentId);
    if (current === null) {
      return { message: 'پرداخت پیدا نشد.', duplicate: false };
    }

    const decision = nextPaymentApproval(current.status);
    if (decision === 'invalid') {
      return { message: 'این پرداخت قابل تأیید نیست.', duplicate: false };
    }

    let payment = current;
    if (decision === 'approve') {
      const updated = await this.db.approvePayment(paymentId, actorTelegramId);
      if (updated === null) {
        const again = await this.db.getPayment(paymentId);
        if (again?.status === 'approved') {
          payment = again;
        } else {
          return { message: 'تأیید انجام نشد (احتمالاً همزمان رد شده).', duplicate: true };
        }
      } else {
        payment = updated;
        const paid = await this.db.updateOrderStatus(payment.order_id, ['waiting_payment', 'pending'], 'paid', {
          paidAt: new Date(),
        });
        if (paid === null) {
          const order = await this.db.getOrder(payment.order_id);
          if (
            order?.status !== 'paid' &&
            order?.status !== 'provisioning' &&
            order?.status !== 'completed' &&
            order?.status !== 'failed'
          ) {
            return { message: 'سفارش دیگر قابل تأیید نیست.', duplicate: false };
          }
        }
      }
    }

    const order = await this.db.getOrder(payment.order_id);
    if (order?.status === 'completed') {
      return { message: 'قبلاً تأیید و سرویس فعال شده است.', duplicate: true };
    }

    await this.provisioning.provisionOrder(payment.order_id);
    const fresh = await this.db.getOrder(payment.order_id);
    if (fresh?.status === 'completed') {
      return {
        message:
          decision === 'duplicate' ? 'قبلاً تأیید شده بود؛ سرویس فعال است.' : 'تأیید شد و سرویس ساخته شد.',
        duplicate: decision === 'duplicate',
      };
    }
    if (fresh?.status === 'failed') {
      return {
        message: 'پرداخت تأیید شد ولی ساخت VPN شکست خورد. جزئیات برای ادمین ارسال شد.',
        duplicate: false,
      };
    }
    return { message: 'تأیید شد. در حال ساخت سرویس.', duplicate: decision === 'duplicate' };
  }

  async reject(paymentId: number, actorTelegramId: number): Promise<{
    message: string;
    customerTelegramId?: number;
    duplicate: boolean;
  }> {
    if (!isAdmin(this.env, actorTelegramId)) {
      this.logger.warn('admin.reject.denied', { actorTelegramId, paymentId });
      return { message: 'اجازه این کار را ندارید.', duplicate: false };
    }

    const current = await this.db.getPayment(paymentId);
    if (current === null) {
      return { message: 'پرداخت پیدا نشد.', duplicate: false };
    }
    const decision = nextPaymentRejection(current.status);
    if (decision === 'invalid') {
      return { message: 'این پرداخت قابل رد نیست.', duplicate: false };
    }
    if (decision === 'duplicate') {
      return { message: 'این پرداخت قبلاً رد شده است.', duplicate: true };
    }

    const updated = await this.db.rejectPayment(paymentId, actorTelegramId);
    if (updated === null) {
      return { message: 'رد انجام نشد (احتمالاً همزمان تأیید شده).', duplicate: true };
    }
    await this.db.updateOrderStatus(updated.order_id, ['waiting_payment', 'pending'], 'cancelled');
    const user = await this.db.getUserById(updated.user_id);
    this.logger.info('payment.rejected', { paymentId, orderId: updated.order_id });
    return {
      message: 'پرداخت رد شد.',
      customerTelegramId: user === null ? undefined : Number(user.telegram_id),
      duplicate: false,
    };
  }

  async myServices(userId: number) {
    await this.db.markExpiredSubscriptions();
    return this.db.listUserSubscriptions(userId);
  }

  async liveServiceText(row: SubscriptionRow): Promise<string> {
    try {
      return await this.provisioning.formatServiceMessage(row);
    } catch (error) {
      this.logger.warn('service.live_config.failed', {
        subscriptionId: row.id,
        detail: error instanceof Error ? error.message : String(error),
      });
      return this.serviceText(row);
    }
  }

  serviceText(row: {
    plan_name: string | null;
    status: string;
    traffic_gb: number;
    expire_at: Date;
    subscription_url: string;
  }): string {
    return [
      `📦 ${escapeHtml(row.plan_name ?? 'VPN')}`,
      `وضعیت: ${escapeHtml(row.status)}`,
      `حجم: ${row.traffic_gb} گیگابایت`,
      `انقضا: ${formatDate(row.expire_at)}`,
      '',
      'لینک اشتراک:',
      `<code>${escapeHtml(row.subscription_url)}</code>`,
    ].join('\n');
  }

  private userLabel(telegramId: string, username: string | null, firstName: string | null): string {
    const name = firstName ?? 'بدون‌نام';
    const handle = username === null ? '' : `@${username}`;
    return `${name} ${handle} (${telegramId})`.trim();
  }
}
