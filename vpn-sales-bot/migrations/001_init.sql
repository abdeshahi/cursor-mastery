CREATE TABLE IF NOT EXISTS schema_migrations (
  id          TEXT PRIMARY KEY,
  applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS users (
  id                 BIGSERIAL PRIMARY KEY,
  telegram_id        BIGINT NOT NULL UNIQUE,
  telegram_username  TEXT,
  first_name         TEXT,
  phone              TEXT,
  status             TEXT NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active', 'blocked')),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plans (
  id                 BIGSERIAL PRIMARY KEY,
  name               TEXT NOT NULL,
  traffic_gb         INTEGER NOT NULL CHECK (traffic_gb > 0),
  duration_days      INTEGER NOT NULL CHECK (duration_days > 0),
  price              BIGINT NOT NULL CHECK (price >= 0),
  currency           TEXT NOT NULL DEFAULT 'TOMAN',
  marzban_profile    TEXT,
  node               TEXT,
  is_active          BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order         INTEGER NOT NULL DEFAULT 0,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS orders (
  id                         BIGSERIAL PRIMARY KEY,
  user_id                    BIGINT NOT NULL REFERENCES users (id),
  plan_id                    BIGINT NOT NULL REFERENCES plans (id),
  amount                     BIGINT NOT NULL CHECK (amount >= 0),
  status                     TEXT NOT NULL
                             CHECK (status IN (
                               'pending',
                               'waiting_payment',
                               'paid',
                               'provisioning',
                               'completed',
                               'cancelled',
                               'failed'
                             )),
  kind                       TEXT NOT NULL DEFAULT 'new'
                             CHECK (kind IN ('new', 'renewal')),
  renewal_subscription_id    BIGINT,
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  paid_at                    TIMESTAMPTZ,
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS payments (
  id                BIGSERIAL PRIMARY KEY,
  order_id          BIGINT NOT NULL REFERENCES orders (id),
  user_id           BIGINT NOT NULL REFERENCES users (id),
  amount            BIGINT NOT NULL CHECK (amount >= 0),
  method            TEXT NOT NULL DEFAULT 'card_to_card',
  reference         TEXT,
  receipt_file_id   TEXT,
  receipt_kind      TEXT CHECK (receipt_kind IN ('photo', 'document')),
  status            TEXT NOT NULL
                    CHECK (status IN ('pending', 'approved', 'rejected')),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  verified_at       TIMESTAMPTZ,
  verified_by       BIGINT
);

CREATE TABLE IF NOT EXISTS subscriptions (
  id                  BIGSERIAL PRIMARY KEY,
  user_id             BIGINT NOT NULL REFERENCES users (id),
  order_id            BIGINT NOT NULL UNIQUE REFERENCES orders (id),
  marzban_username    TEXT NOT NULL UNIQUE,
  subscription_url    TEXT NOT NULL,
  traffic_gb          INTEGER NOT NULL,
  start_at            TIMESTAMPTZ NOT NULL,
  expire_at           TIMESTAMPTZ NOT NULL,
  status              TEXT NOT NULL
                      CHECK (status IN ('active', 'expired', 'suspended', 'cancelled')),
  node                TEXT,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE orders
  DROP CONSTRAINT IF EXISTS orders_renewal_subscription_fk;

ALTER TABLE orders
  ADD CONSTRAINT orders_renewal_subscription_fk
  FOREIGN KEY (renewal_subscription_id) REFERENCES subscriptions (id);

CREATE UNIQUE INDEX IF NOT EXISTS payments_one_pending_per_order
  ON payments (order_id)
  WHERE status = 'pending';

CREATE UNIQUE INDEX IF NOT EXISTS payments_one_approved_per_order
  ON payments (order_id)
  WHERE status = 'approved';

CREATE INDEX IF NOT EXISTS orders_user_status_idx ON orders (user_id, status);
CREATE INDEX IF NOT EXISTS subscriptions_user_status_idx ON subscriptions (user_id, status);
CREATE INDEX IF NOT EXISTS subscriptions_expire_idx ON subscriptions (expire_at, status);

CREATE TABLE IF NOT EXISTS reminder_logs (
  id                BIGSERIAL PRIMARY KEY,
  subscription_id   BIGINT NOT NULL REFERENCES subscriptions (id),
  reminder_type     TEXT NOT NULL,
  sent_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (subscription_id, reminder_type)
);

CREATE TABLE IF NOT EXISTS lead_followups (
  id          BIGSERIAL PRIMARY KEY,
  user_id     BIGINT NOT NULL UNIQUE REFERENCES users (id),
  sent_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS alert_states (
  key            TEXT PRIMARY KEY,
  last_status    TEXT NOT NULL,
  last_sent_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
