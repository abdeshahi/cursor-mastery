import type { Pool, QueryResult } from 'pg';

import type { OrderStatus, PaymentStatus } from '../utils/state-machine.js';

export interface UserRow {
  id: number;
  telegram_id: string;
  telegram_username: string | null;
  first_name: string | null;
  phone: string | null;
  status: 'active' | 'blocked';
}

export interface PlanRow {
  id: number;
  name: string;
  traffic_gb: number;
  duration_days: number;
  price: number;
  currency: string;
  marzban_profile: string | null;
  node: string | null;
  is_active: boolean;
}

export interface OrderRow {
  id: number;
  user_id: number;
  plan_id: number;
  amount: number;
  status: OrderStatus;
  kind: 'new' | 'renewal';
  renewal_subscription_id: number | null;
  paid_at: Date | null;
  provisioning_started_at: Date | null;
  completed_at: Date | null;
}

export interface PaymentRow {
  id: number;
  order_id: number;
  user_id: number;
  amount: number;
  method: string;
  reference: string | null;
  receipt_file_id: string | null;
  receipt_kind: 'photo' | 'document' | null;
  status: PaymentStatus;
  verified_by: string | null;
  reviewed_by: string | null;
  reviewed_at: Date | null;
  rejection_reason: string | null;
}

export interface SubscriptionRow {
  id: number;
  user_id: number;
  order_id: number;
  marzban_username: string;
  subscription_url: string;
  traffic_gb: number;
  start_at: Date;
  expire_at: Date;
  status: 'active' | 'expired' | 'suspended' | 'cancelled';
  node: string | null;
  plan_name: string | null;
}

function num(value: unknown): number {
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new Error(`invalid numeric id: ${String(value)}`);
  }
  return parsed;
}

function str(value: unknown): string {
  if (typeof value !== 'string') {
    throw new Error('expected string');
  }
  return value;
}

function optionalStr(value: unknown): string | null {
  return value === null || value === undefined ? null : str(value);
}

export class Repositories {
  constructor(private readonly db: Pool) {}

  private async query<T extends Record<string, unknown>>(
    text: string,
    params: unknown[] = [],
  ): Promise<QueryResult<T>> {
    return this.db.query<T>(text, params);
  }

  async upsertUser(input: {
    telegramId: number;
    username?: string;
    firstName?: string;
  }): Promise<UserRow> {
    const result = await this.query(
      `INSERT INTO users (telegram_id, telegram_username, first_name, status)
       VALUES ($1, $2, $3, 'active')
       ON CONFLICT (telegram_id) DO UPDATE SET
         telegram_username = EXCLUDED.telegram_username,
         first_name = EXCLUDED.first_name,
         updated_at = now()
       RETURNING id, telegram_id, telegram_username, first_name, phone, status`,
      [input.telegramId, input.username ?? null, input.firstName ?? null],
    );
    return this.mapUser(result.rows[0]);
  }

  async getUserById(id: number): Promise<UserRow | null> {
    const result = await this.query(
      `SELECT id, telegram_id, telegram_username, first_name, phone, status
       FROM users WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapUser(row);
  }

  async listActivePlans(): Promise<PlanRow[]> {
    const result = await this.query(
      `SELECT id, name, traffic_gb, duration_days, price, currency, marzban_profile, node, is_active
       FROM plans
       WHERE is_active = TRUE
       ORDER BY sort_order ASC, id ASC`,
    );
    return result.rows.map((row) => this.mapPlan(row));
  }

  async getPlan(id: number): Promise<PlanRow | null> {
    const result = await this.query(
      `SELECT id, name, traffic_gb, duration_days, price, currency, marzban_profile, node, is_active
       FROM plans WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPlan(row);
  }

  async createOrder(input: {
    userId: number;
    planId: number;
    amount: number;
    kind: 'new' | 'renewal';
    renewalSubscriptionId?: number;
  }): Promise<OrderRow> {
    const result = await this.query(
      `INSERT INTO orders (user_id, plan_id, amount, status, kind, renewal_subscription_id)
       VALUES ($1, $2, $3, 'waiting_payment', $4, $5)
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
                 provisioning_started_at, completed_at`,
      [input.userId, input.planId, input.amount, input.kind, input.renewalSubscriptionId ?? null],
    );
    return this.mapOrder(result.rows[0]);
  }

  async getOrder(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
              provisioning_started_at, completed_at
       FROM orders WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async findOpenOrderForUser(userId: number): Promise<OrderRow | null> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
              provisioning_started_at, completed_at
       FROM orders
       WHERE user_id = $1 AND status = 'waiting_payment'
       ORDER BY created_at DESC
       LIMIT 1`,
      [userId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async cancelOpenOrders(userId: number): Promise<void> {
    await this.query(
      `UPDATE orders
       SET status = 'cancelled', updated_at = now()
       WHERE user_id = $1 AND status IN ('pending', 'waiting_payment')`,
      [userId],
    );
  }

  async cancelOrder(orderId: number, userId: number): Promise<boolean> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'cancelled', updated_at = now()
       WHERE id = $1 AND user_id = $2 AND status IN ('pending', 'waiting_payment')
       RETURNING id`,
      [orderId, userId],
    );
    if ((result.rowCount ?? 0) === 0) {
      return false;
    }
    await this.query(
      `UPDATE payments
       SET status = 'rejected', verified_at = now()
       WHERE order_id = $1 AND status = 'pending'`,
      [orderId],
    );
    return true;
  }

  async updateOrderStatus(
    id: number,
    from: OrderStatus[],
    to: OrderStatus,
    extra: { paidAt?: Date } = {},
  ): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = $3,
           paid_at = COALESCE($4, paid_at),
           updated_at = now()
       WHERE id = $1 AND status = ANY($2::text[])
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
                 provisioning_started_at, completed_at`,
      [id, from, to, extra.paidAt ?? null],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async claimOrderForProvisioning(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'provisioning',
           provisioning_started_at = now(),
           updated_at = now()
       WHERE id = $1 AND status IN ('paid', 'failed')
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
                 provisioning_started_at, completed_at`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async completeProvisioning(id: number): Promise<OrderRow | null> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'completed',
           completed_at = now(),
           updated_at = now()
       WHERE id = $1 AND status = 'provisioning'
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
                 provisioning_started_at, completed_at`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapOrder(row);
  }

  async releaseStaleProvisioningClaims(staleMinutes = 5): Promise<OrderRow[]> {
    const result = await this.query(
      `UPDATE orders
       SET status = 'failed', updated_at = now()
       WHERE status = 'provisioning'
         AND provisioning_started_at < now() - ($1 * INTERVAL '1 minute')
       RETURNING id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
                 provisioning_started_at, completed_at`,
      [staleMinutes],
    );
    return result.rows.map((row) => this.mapOrder(row));
  }

  async listRecoverableOrders(): Promise<OrderRow[]> {
    const result = await this.query(
      `SELECT id, user_id, plan_id, amount, status, kind, renewal_subscription_id, paid_at,
              provisioning_started_at, completed_at
       FROM orders
       WHERE status IN ('paid', 'failed')
       ORDER BY id ASC`,
    );
    return result.rows.map((row) => this.mapOrder(row));
  }

  async upsertPendingPayment(input: {
    orderId: number;
    userId: number;
    amount: number;
    receiptFileId: string;
    receiptKind: 'photo' | 'document';
  }): Promise<PaymentRow> {
    const result = await this.query(
      `INSERT INTO payments (order_id, user_id, amount, method, receipt_file_id, receipt_kind, status)
       VALUES ($1, $2, $3, 'card_to_card', $4, $5, 'pending')
       ON CONFLICT (order_id) WHERE status = 'pending'
       DO UPDATE SET
         receipt_file_id = EXCLUDED.receipt_file_id,
         receipt_kind = EXCLUDED.receipt_kind,
         amount = EXCLUDED.amount
       RETURNING id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
                 status, verified_by, reviewed_by, reviewed_at, rejection_reason`,
      [input.orderId, input.userId, input.amount, input.receiptFileId, input.receiptKind],
    );
    return this.mapPayment(result.rows[0]);
  }

  async getPayment(id: number): Promise<PaymentRow | null> {
    const result = await this.query(
      `SELECT id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
              status, verified_by, reviewed_by, reviewed_at, rejection_reason
       FROM payments WHERE id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async approvePayment(id: number, adminTelegramId: number): Promise<PaymentRow | null> {
    const result = await this.query(
      `UPDATE payments p
       SET status = 'approved',
           verified_at = now(),
           verified_by = $2,
           reviewed_at = now(),
           reviewed_by = $2,
           rejection_reason = NULL
       FROM orders o
       WHERE p.id = $1
         AND p.status = 'pending'
         AND o.id = p.order_id
         AND o.status IN ('pending', 'waiting_payment', 'paid', 'provisioning', 'failed')
       RETURNING p.id, p.order_id, p.user_id, p.amount, p.method, p.reference,
                 p.receipt_file_id, p.receipt_kind, p.status, p.verified_by,
                 p.reviewed_by, p.reviewed_at, p.rejection_reason`,
      [id, adminTelegramId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async rejectPayment(
    id: number,
    adminTelegramId: number,
    rejectionReason?: string,
  ): Promise<PaymentRow | null> {
    const result = await this.query(
      `UPDATE payments
       SET status = 'rejected',
           verified_at = now(),
           verified_by = $2,
           reviewed_at = now(),
           reviewed_by = $2,
           rejection_reason = $3
       WHERE id = $1 AND status = 'pending'
       RETURNING id, order_id, user_id, amount, method, reference, receipt_file_id, receipt_kind,
                 status, verified_by, reviewed_by, reviewed_at, rejection_reason`,
      [id, adminTelegramId, rejectionReason?.trim() || null],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapPayment(row);
  }

  async getSubscriptionByOrder(orderId: number): Promise<SubscriptionRow | null> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       WHERE s.order_id = $1`,
      [orderId],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapSubscription(row);
  }

  async getSubscription(id: number): Promise<SubscriptionRow | null> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       WHERE s.id = $1`,
      [id],
    );
    const row = result.rows[0];
    return row === undefined ? null : this.mapSubscription(row);
  }

  async listUserSubscriptions(userId: number): Promise<SubscriptionRow[]> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, p.name AS plan_name
       FROM subscriptions s
       JOIN orders o ON o.id = s.order_id
       JOIN plans p ON p.id = o.plan_id
       WHERE s.user_id = $1 AND s.status IN ('active', 'expired', 'suspended')
       ORDER BY s.status ASC, s.expire_at DESC`,
      [userId],
    );
    return result.rows.map((row) => this.mapSubscription(row));
  }

  async insertSubscription(input: {
    userId: number;
    orderId: number;
    marzbanUsername: string;
    subscriptionUrl: string;
    trafficGb: number;
    startAt: Date;
    expireAt: Date;
    node: string;
  }): Promise<SubscriptionRow> {
    const result = await this.query(
      `INSERT INTO subscriptions (
         user_id, order_id, marzban_username, subscription_url, traffic_gb,
         start_at, expire_at, status, node
       ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', $8)
       ON CONFLICT (order_id) DO UPDATE SET
         subscription_url = EXCLUDED.subscription_url,
         traffic_gb = EXCLUDED.traffic_gb,
         expire_at = EXCLUDED.expire_at,
         status = 'active',
         node = EXCLUDED.node,
         updated_at = now()
       RETURNING id, user_id, order_id, marzban_username, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, NULL::text AS plan_name`,
      [
        input.userId,
        input.orderId,
        input.marzbanUsername,
        input.subscriptionUrl,
        input.trafficGb,
        input.startAt,
        input.expireAt,
        input.node,
      ],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async updateSubscriptionUrl(id: number, subscriptionUrl: string): Promise<SubscriptionRow> {
    const result = await this.query(
      `UPDATE subscriptions
       SET subscription_url = $2, updated_at = now()
       WHERE id = $1
       RETURNING id, user_id, order_id, marzban_username, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, NULL::text AS plan_name`,
      [id, subscriptionUrl],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async listActiveSubscriptions(): Promise<SubscriptionRow[]> {
    const result = await this.query(
      `SELECT s.id, s.user_id, s.order_id, s.marzban_username, s.subscription_url, s.traffic_gb,
              s.start_at, s.expire_at, s.status, s.node, p.name AS plan_name
       FROM subscriptions s
       LEFT JOIN orders o ON o.id = s.order_id
       LEFT JOIN plans p ON p.id = o.plan_id
       WHERE s.status = 'active'
       ORDER BY s.id ASC`,
    );
    return result.rows.map((row) => this.mapSubscription(row));
  }

  async updateSubscriptionRenewal(input: {
    id: number;
    subscriptionUrl: string;
    trafficGb: number;
    expireAt: Date;
    node: string;
  }): Promise<SubscriptionRow> {
    const result = await this.query(
      `UPDATE subscriptions
       SET subscription_url = $2,
           traffic_gb = $3,
           expire_at = $4,
           status = 'active',
           node = $5,
           updated_at = now()
       WHERE id = $1
       RETURNING id, user_id, order_id, marzban_username, subscription_url, traffic_gb,
                 start_at, expire_at, status, node, NULL::text AS plan_name`,
      [input.id, input.subscriptionUrl, input.trafficGb, input.expireAt, input.node],
    );
    return this.mapSubscription(result.rows[0]);
  }

  async markExpiredSubscriptions(now: Date = new Date()): Promise<number> {
    const result = await this.query(
      `UPDATE subscriptions
       SET status = 'expired', updated_at = now()
       WHERE status = 'active' AND expire_at <= $1`,
      [now],
    );
    return result.rowCount ?? 0;
  }

  private mapUser(row: Record<string, unknown> | undefined): UserRow {
    if (row === undefined) {
      throw new Error('user row missing');
    }
    return {
      id: num(row['id']),
      telegram_id: String(row['telegram_id']),
      telegram_username: optionalStr(row['telegram_username']),
      first_name: optionalStr(row['first_name']),
      phone: optionalStr(row['phone']),
      status: str(row['status']) as UserRow['status'],
    };
  }

  private mapPlan(row: Record<string, unknown> | undefined): PlanRow {
    if (row === undefined) {
      throw new Error('plan row missing');
    }
    return {
      id: num(row['id']),
      name: str(row['name']),
      traffic_gb: num(row['traffic_gb']),
      duration_days: num(row['duration_days']),
      price: num(row['price']),
      currency: str(row['currency']),
      marzban_profile: optionalStr(row['marzban_profile']),
      node: optionalStr(row['node']),
      is_active: Boolean(row['is_active']),
    };
  }

  private mapOrder(row: Record<string, unknown> | undefined): OrderRow {
    if (row === undefined) {
      throw new Error('order row missing');
    }
    return {
      id: num(row['id']),
      user_id: num(row['user_id']),
      plan_id: num(row['plan_id']),
      amount: num(row['amount']),
      status: str(row['status']) as OrderStatus,
      kind: str(row['kind']) as OrderRow['kind'],
      renewal_subscription_id:
        row['renewal_subscription_id'] === null ? null : num(row['renewal_subscription_id']),
      paid_at: row['paid_at'] instanceof Date ? row['paid_at'] : null,
      provisioning_started_at:
        row['provisioning_started_at'] instanceof Date ? row['provisioning_started_at'] : null,
      completed_at: row['completed_at'] instanceof Date ? row['completed_at'] : null,
    };
  }

  private mapPayment(row: Record<string, unknown> | undefined): PaymentRow {
    if (row === undefined) {
      throw new Error('payment row missing');
    }
    return {
      id: num(row['id']),
      order_id: num(row['order_id']),
      user_id: num(row['user_id']),
      amount: num(row['amount']),
      method: str(row['method']),
      reference: optionalStr(row['reference']),
      receipt_file_id: optionalStr(row['receipt_file_id']),
      receipt_kind:
        row['receipt_kind'] === null || row['receipt_kind'] === undefined
          ? null
          : (str(row['receipt_kind']) as PaymentRow['receipt_kind']),
      status: str(row['status']) as PaymentStatus,
      verified_by:
        row['verified_by'] === null || row['verified_by'] === undefined
          ? null
          : String(row['verified_by']),
      reviewed_by:
        row['reviewed_by'] === null || row['reviewed_by'] === undefined
          ? null
          : String(row['reviewed_by']),
      reviewed_at: row['reviewed_at'] instanceof Date ? row['reviewed_at'] : null,
      rejection_reason: optionalStr(row['rejection_reason']),
    };
  }

  private mapSubscription(row: Record<string, unknown> | undefined): SubscriptionRow {
    if (row === undefined) {
      throw new Error('subscription row missing');
    }
    const startAt = row['start_at'];
    const expireAt = row['expire_at'];
    if (!(startAt instanceof Date) || !(expireAt instanceof Date)) {
      throw new Error('invalid subscription timestamps');
    }
    return {
      id: num(row['id']),
      user_id: num(row['user_id']),
      order_id: num(row['order_id']),
      marzban_username: str(row['marzban_username']),
      subscription_url: str(row['subscription_url']),
      traffic_gb: num(row['traffic_gb']),
      start_at: startAt,
      expire_at: expireAt,
      status: str(row['status']) as SubscriptionRow['status'],
      node: optionalStr(row['node']),
      plan_name: optionalStr(row['plan_name']),
    };
  }
}
