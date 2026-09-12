# n8n workflows (Phase 1)

n8n is **not** the sales brain. The Telegram bot writes orders, payments, and subscriptions to PostgreSQL.

Use the **existing** n8n 2.37.10 install on port 5678. Do not reinstall, replace, or containerize it again.

Payment approval already notifies the admin from the bot. **Do not duplicate Workflow 2.**

Credential: see `deploy/n8n-postgres-credential.md`. Telegram credential: same `BOT_TOKEN` as the bot.

---

## Workflow 1 — Renewal reminder

**Trigger:** Schedule, once per day (10:00 Asia/Tehran).

```sql
INSERT INTO reminder_logs (subscription_id, reminder_type)
SELECT s.id,
       CASE
         WHEN s.expire_at::date = (CURRENT_DATE + INTERVAL '3 days')::date THEN '3d'
         WHEN s.expire_at::date = (CURRENT_DATE + INTERVAL '1 day')::date THEN '1d'
       END
FROM subscriptions s
JOIN users u ON u.id = s.user_id
WHERE s.status = 'active'
  AND u.status = 'active'
  AND (
    s.expire_at::date = (CURRENT_DATE + INTERVAL '3 days')::date
    OR s.expire_at::date = (CURRENT_DATE + INTERVAL '1 day')::date
  )
ON CONFLICT (subscription_id, reminder_type) DO NOTHING
RETURNING subscription_id, reminder_type;
```

Then fetch rows and send one Telegram reminder per user. Unique `(subscription_id, reminder_type)` blocks duplicates.

---

## Workflow 2 — Payment notification

**Skip.** The bot already sends the receipt + Approve/Reject buttons.

---

## Workflow 3 — Daily sales report

**Trigger:** Schedule, once per day.

```sql
SELECT
  (SELECT count(*) FROM orders WHERE created_at::date = CURRENT_DATE) AS total_orders,
  (SELECT count(*) FROM orders WHERE status = 'completed' AND updated_at::date = CURRENT_DATE) AS completed_orders,
  (SELECT coalesce(sum(amount), 0) FROM orders WHERE status = 'completed' AND paid_at::date = CURRENT_DATE) AS revenue,
  (SELECT count(*) FROM users WHERE created_at::date = CURRENT_DATE) AS new_users,
  (SELECT count(*) FROM orders WHERE kind = 'renewal' AND status = 'completed' AND paid_at::date = CURRENT_DATE) AS renewals,
  (SELECT count(*) FROM payments WHERE status = 'pending') AS pending_payments,
  (SELECT count(*) FROM orders WHERE status = 'failed' AND updated_at::date = CURRENT_DATE) AS failed_provisioning;
```

Send one Telegram message to each admin ID.

---

## Workflow 4 — Node health alert

**Trigger:** every 10 minutes.

HTTP GET `{MARZBAN_BASE_URL}/api/system` with a Marzban token. On unhealthy:

```sql
INSERT INTO alert_states (key, last_status, last_sent_at)
VALUES ('marzban', 'unhealthy', now())
ON CONFLICT (key) DO UPDATE
SET last_status = 'unhealthy',
    last_sent_at = now()
WHERE alert_states.last_status IS DISTINCT FROM 'unhealthy'
   OR alert_states.last_sent_at < now() - INTERVAL '2 hours'
RETURNING key;
```

Notify admin only if `RETURNING` has a row.

---

## Workflow 5 — Lead follow-up (optional)

```sql
INSERT INTO lead_followups (user_id)
SELECT u.id
FROM users u
WHERE u.status = 'active'
  AND u.created_at < now() - INTERVAL '24 hours'
  AND NOT EXISTS (
    SELECT 1 FROM orders o
    WHERE o.user_id = u.id AND o.status = 'completed'
  )
ON CONFLICT (user_id) DO NOTHING
RETURNING user_id;
```

Send **one** follow-up message per user.
