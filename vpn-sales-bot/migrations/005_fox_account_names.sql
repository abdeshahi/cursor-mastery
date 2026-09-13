-- Stable customer-facing account names for new VPN subscriptions.
-- Existing Marzban users are not renamed; their current username remains the
-- account label so active links and renewal behavior stay compatible.

CREATE SEQUENCE vpn_account_number_seq
  AS BIGINT
  START WITH 1001
  INCREMENT BY 1
  NO CYCLE;

ALTER TABLE orders
  ADD COLUMN account_name TEXT;

ALTER TABLE subscriptions
  ADD COLUMN account_name TEXT;

UPDATE subscriptions
SET account_name = marzban_username
WHERE account_name IS NULL;

UPDATE orders o
SET account_name = s.account_name
FROM subscriptions s
WHERE s.order_id = o.id
  AND o.kind = 'new'
  AND o.account_name IS NULL;

ALTER TABLE subscriptions
  ALTER COLUMN account_name SET NOT NULL;

CREATE UNIQUE INDEX orders_account_name_unique_idx
  ON orders (account_name)
  WHERE account_name IS NOT NULL;

CREATE UNIQUE INDEX subscriptions_account_name_unique_idx
  ON subscriptions (account_name);

-- If this migration is applied to an installation that already has FOX
-- usernames, continue after the largest observed number. With no FOX users,
-- the first nextval() is exactly 1001.
SELECT setval(
  'vpn_account_number_seq',
  GREATEST(
    1000,
    COALESCE(
      (
        SELECT max(substring(account_name FROM 4)::BIGINT)
        FROM subscriptions
        WHERE account_name ~ '^FOX[0-9]+$'
      ),
      1000
    )
  ),
  TRUE
);
