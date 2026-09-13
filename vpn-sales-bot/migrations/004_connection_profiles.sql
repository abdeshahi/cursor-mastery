-- Phase 1.5: normalized connection profiles and privacy-minimal field reports.
-- This migration records the existing Reality service as data. It does not
-- create, modify, restart, or remove any Marzban/Xray inbound.

CREATE TABLE nodes (
  id               BIGSERIAL PRIMARY KEY,
  name             TEXT NOT NULL UNIQUE,
  enabled          BOOLEAN NOT NULL DEFAULT TRUE,
  priority         INTEGER NOT NULL DEFAULT 100,
  notes            TEXT,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (length(btrim(name)) > 0)
);

INSERT INTO nodes (name)
VALUES ('node1')
ON CONFLICT (name) DO NOTHING;

INSERT INTO nodes (name)
SELECT DISTINCT btrim(node)
FROM (
  SELECT node FROM plans
  UNION ALL
  SELECT node FROM subscriptions
) existing_nodes
WHERE node IS NOT NULL AND btrim(node) <> ''
ON CONFLICT (name) DO NOTHING;

CREATE TABLE connection_profiles (
  id                        BIGSERIAL PRIMARY KEY,
  node_id                   BIGINT NOT NULL REFERENCES nodes (id),
  name                      TEXT NOT NULL,
  protocol                  TEXT NOT NULL,
  transport                 TEXT NOT NULL,
  security                  TEXT NOT NULL,
  port                      INTEGER NOT NULL CHECK (port BETWEEN 1 AND 65535),
  sni                       TEXT,
  flow                      TEXT,
  fingerprint               TEXT,
  marzban_inbound_tag       TEXT NOT NULL,
  marzban_proxies           JSONB NOT NULL DEFAULT '{}'::jsonb,
  marzban_inbounds          JSONB NOT NULL DEFAULT '{}'::jsonb,
  enabled                   BOOLEAN NOT NULL DEFAULT FALSE,
  priority                  INTEGER NOT NULL DEFAULT 100,
  notes                     TEXT,
  created_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (node_id, name),
  CHECK (length(btrim(name)) > 0),
  CHECK (length(btrim(protocol)) > 0),
  CHECK (length(btrim(transport)) > 0),
  CHECK (length(btrim(security)) > 0),
  CHECK (length(btrim(marzban_inbound_tag)) > 0),
  CHECK (jsonb_typeof(marzban_proxies) = 'object'),
  CHECK (jsonb_typeof(marzban_inbounds) = 'object')
);

-- One enabled baseline per known node. This only describes the currently
-- deployed inbound; it does not enable a new protocol or listener.
INSERT INTO connection_profiles (
  node_id,
  name,
  protocol,
  transport,
  security,
  port,
  sni,
  flow,
  fingerprint,
  marzban_inbound_tag,
  marzban_proxies,
  marzban_inbounds,
  enabled,
  priority,
  notes
)
SELECT
  id,
  'VLESS Reality baseline',
  'vless',
  'tcp',
  'reality',
  443,
  'www.apple.com',
  'xtls-rprx-vision',
  'chrome',
  'VLESS TCP REALITY',
  '{"vless":{"flow":"xtls-rprx-vision"}}'::jsonb,
  '{"vless":["VLESS TCP REALITY"]}'::jsonb,
  TRUE,
  10,
  'Existing production baseline recorded on 2026-09-11; not an Iran-wide compatibility claim.'
FROM nodes
ON CONFLICT (node_id, name) DO NOTHING;

CREATE TABLE plan_connection_profiles (
  plan_id       BIGINT NOT NULL REFERENCES plans (id) ON DELETE CASCADE,
  profile_id    BIGINT NOT NULL REFERENCES connection_profiles (id),
  is_default    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (plan_id, profile_id)
);

CREATE UNIQUE INDEX plan_connection_profiles_one_default_idx
  ON plan_connection_profiles (plan_id)
  WHERE is_default;

INSERT INTO plan_connection_profiles (plan_id, profile_id, is_default)
SELECT p.id, cp.id, TRUE
FROM plans p
JOIN nodes n ON n.name = COALESCE(NULLIF(btrim(p.node), ''), 'node1')
JOIN connection_profiles cp
  ON cp.node_id = n.id
 AND cp.name = 'VLESS Reality baseline'
ON CONFLICT (plan_id, profile_id) DO NOTHING;

ALTER TABLE orders
  ADD COLUMN connection_profile_id BIGINT;

UPDATE orders o
SET connection_profile_id = pcp.profile_id
FROM plan_connection_profiles pcp
WHERE pcp.plan_id = o.plan_id
  AND pcp.is_default
  AND o.connection_profile_id IS NULL;

ALTER TABLE orders
  ADD CONSTRAINT orders_connection_profile_fk
    FOREIGN KEY (connection_profile_id) REFERENCES connection_profiles (id),
  ADD CONSTRAINT orders_plan_connection_profile_fk
    FOREIGN KEY (plan_id, connection_profile_id)
    REFERENCES plan_connection_profiles (plan_id, profile_id);

ALTER TABLE subscriptions
  ADD COLUMN connection_profile_id BIGINT;

UPDATE subscriptions s
SET connection_profile_id = o.connection_profile_id
FROM orders o
WHERE o.id = s.order_id
  AND s.connection_profile_id IS NULL;

ALTER TABLE subscriptions
  ADD CONSTRAINT subscriptions_connection_profile_fk
  FOREIGN KEY (connection_profile_id) REFERENCES connection_profiles (id);

CREATE INDEX orders_connection_profile_idx ON orders (connection_profile_id);
CREATE INDEX subscriptions_connection_profile_idx ON subscriptions (connection_profile_id);
CREATE INDEX connection_profiles_enabled_priority_idx
  ON connection_profiles (enabled, priority, id);

CREATE TABLE profile_test_results (
  id                 BIGSERIAL PRIMARY KEY,
  profile_id         BIGINT NOT NULL REFERENCES connection_profiles (id),
  isp                TEXT NOT NULL,
  network_type       TEXT NOT NULL,
  province_or_city   TEXT,
  connected          BOOLEAN NOT NULL,
  latency_ms         INTEGER CHECK (latency_ms IS NULL OR latency_ms >= 0),
  download_ok        BOOLEAN,
  client_app         TEXT NOT NULL,
  client_version     TEXT,
  failure_stage      TEXT,
  source             TEXT NOT NULL DEFAULT 'customer_bot',
  notes              TEXT,
  tested_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (length(btrim(isp)) > 0),
  CHECK (network_type IN ('4g', '5g', 'td_lte', 'adsl', 'vdsl', 'fiber', 'fixed_wireless', 'other')),
  CHECK (length(btrim(client_app)) > 0),
  CHECK (source IN ('customer_bot', 'support', 'operator', 'controlled_test'))
);

CREATE INDEX profile_test_results_profile_tested_idx
  ON profile_test_results (profile_id, tested_at DESC);

CREATE INDEX profile_test_results_compatibility_idx
  ON profile_test_results (isp, network_type, profile_id, tested_at DESC);
