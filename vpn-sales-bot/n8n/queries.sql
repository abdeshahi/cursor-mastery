-- Queries used by n8n. See WORKFLOWS.md.

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

SELECT
  (SELECT count(*) FROM orders WHERE created_at::date = CURRENT_DATE) AS total_orders,
  (SELECT count(*) FROM orders WHERE status = 'completed' AND updated_at::date = CURRENT_DATE) AS completed_orders,
  (SELECT coalesce(sum(amount), 0) FROM orders WHERE status = 'completed' AND paid_at::date = CURRENT_DATE) AS revenue,
  (SELECT count(*) FROM users WHERE created_at::date = CURRENT_DATE) AS new_users,
  (SELECT count(*) FROM orders WHERE kind = 'renewal' AND status = 'completed' AND paid_at::date = CURRENT_DATE) AS renewals,
  (SELECT count(*) FROM payments WHERE status = 'pending') AS pending_payments,
  (SELECT count(*) FROM orders WHERE status = 'failed' AND updated_at::date = CURRENT_DATE) AS failed_provisioning;

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
