-- Phase 1 production hardening. Additive and backward-compatible.

ALTER TABLE orders
  ADD COLUMN IF NOT EXISTS provisioning_started_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

UPDATE orders
SET provisioning_started_at = COALESCE(provisioning_started_at, updated_at)
WHERE status = 'provisioning';

UPDATE orders
SET completed_at = COALESCE(completed_at, updated_at)
WHERE status = 'completed';

ALTER TABLE payments
  ADD COLUMN IF NOT EXISTS reviewed_by BIGINT,
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS rejection_reason TEXT;

UPDATE payments
SET reviewed_by = COALESCE(reviewed_by, verified_by),
    reviewed_at = COALESCE(reviewed_at, verified_at)
WHERE status IN ('approved', 'rejected');

-- 001_init.sql already creates equivalent constraints. Named indexes protect
-- deployments that started from an older schema without changing existing rows.
CREATE UNIQUE INDEX IF NOT EXISTS subscriptions_order_id_unique_idx
  ON subscriptions (order_id);

CREATE UNIQUE INDEX IF NOT EXISTS subscriptions_marzban_username_unique_idx
  ON subscriptions (marzban_username);

CREATE INDEX IF NOT EXISTS orders_provisioning_recovery_idx
  ON orders (status, provisioning_started_at)
  WHERE status = 'provisioning';
