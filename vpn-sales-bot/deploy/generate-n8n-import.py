#!/usr/bin/env python3
"""Generate n8n credential + workflow JSON for Phase 1 import."""

from __future__ import annotations

import json
import re
import sqlite3
import sys
import uuid
from pathlib import Path

PROXY = "http://127.0.0.1:8118"
PROJECT_ID = "7itV1t8r4OB29gvG"
N8N_DB = "/opt/n8n-app/.n8n/.n8n/database.sqlite"

INSERT_REMINDERS_SQL = """
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
""".strip()

REMINDER_DETAILS_SQL = """
SELECT u.telegram_id,
       s.expire_at,
       p.name AS plan_name,
       rl.reminder_type
FROM reminder_logs rl
JOIN subscriptions s ON s.id = rl.subscription_id
JOIN users u ON u.id = s.user_id
JOIN plans p ON p.id = s.plan_id
WHERE rl.subscription_id = {{ $json.subscription_id }}
  AND rl.reminder_type = '{{ $json.reminder_type }}'
  AND rl.created_at > now() - INTERVAL '10 minutes';
""".strip()

DAILY_REPORT_SQL = """
SELECT
  (SELECT count(*) FROM orders WHERE created_at::date = CURRENT_DATE) AS total_orders,
  (SELECT count(*) FROM orders WHERE status = 'completed' AND updated_at::date = CURRENT_DATE) AS completed_orders,
  (SELECT coalesce(sum(amount), 0) FROM orders WHERE status = 'completed' AND paid_at::date = CURRENT_DATE) AS revenue,
  (SELECT count(*) FROM users WHERE created_at::date = CURRENT_DATE) AS new_users,
  (SELECT count(*) FROM orders WHERE kind = 'renewal' AND status = 'completed' AND paid_at::date = CURRENT_DATE) AS renewals,
  (SELECT count(*) FROM payments WHERE status = 'pending') AS pending_payments,
  (SELECT count(*) FROM orders WHERE status = 'failed' AND updated_at::date = CURRENT_DATE) AS failed_provisioning;
""".strip()

ALERT_INSERT_SQL = """
INSERT INTO alert_states (key, last_status, last_sent_at)
VALUES ('marzban', 'unhealthy', now())
ON CONFLICT (key) DO UPDATE
SET last_status = 'unhealthy',
    last_sent_at = now()
WHERE alert_states.last_status IS DISTINCT FROM 'unhealthy'
   OR alert_states.last_sent_at < now() - INTERVAL '2 hours'
RETURNING key;
""".strip()

LEAD_INSERT_SQL = """
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
""".strip()

LEAD_USER_SQL = """
SELECT telegram_id FROM users WHERE id = {{ $json.user_id }};
""".strip()


def env_get(text: str, key: str) -> str:
    for line in text.splitlines():
        match = re.match(rf"^\s*{re.escape(key)}\s*=\s*(.*)$", line)
        if not match:
            continue
        value = match.group(1).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        return value
    return ""


def node_id() -> str:
    return str(uuid.uuid4())


def pg_node(name: str, query: str, x: int, y: int) -> dict:
    return {
        "parameters": {"operation": "executeQuery", "query": query, "options": {}},
        "id": node_id(),
        "name": name,
        "type": "n8n-nodes-base.postgres",
        "typeVersion": 2.5,
        "position": [x, y],
        "credentials": {"postgres": {"name": "VPN Sales Postgres"}},
    }


def schedule_node(name: str, cron: str, x: int, y: int) -> dict:
    return {
        "parameters": {
            "rule": {"interval": [{"field": "cronExpression", "expression": cron}]}
        },
        "id": node_id(),
        "name": name,
        "type": "n8n-nodes-base.scheduleTrigger",
        "typeVersion": 1.2,
        "position": [x, y],
    }


def if_has_items(name: str, x: int, y: int) -> dict:
    return {
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "typeValidation": "strict"},
                "combinator": "and",
                "conditions": [
                    {
                        "id": node_id(),
                        "leftValue": "={{ $input.all().length }}",
                        "rightValue": 0,
                        "operator": {"type": "number", "operation": "gt"},
                    }
                ],
            }
        },
        "id": node_id(),
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [x, y],
    }


def telegram_http(
    name: str, chat_id: str, text_js: str, x: int, y: int, token: str
) -> dict:
    # chat_id: numeric admin id or n8n expression e.g. "$json.telegram_id"
    chat_ref = chat_id if chat_id.startswith("$") else chat_id
    return {
        "parameters": {
            "method": "POST",
            "url": f"https://api.telegram.org/bot{token}/sendMessage",
            "sendBody": True,
            "specifyBody": "json",
            "jsonBody": f"={{ {{ chat_id: {chat_ref}, text: {text_js} }} }}",
            "options": {"proxy": PROXY},
        },
        "id": node_id(),
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": [x, y],
    }


def workflow(name: str, nodes: list[dict], connections: dict, active: bool = True) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": {"timezone": "Asia/Tehran", "executionOrder": "v1"},
        "active": active,
    }


def chain(*names: str) -> dict:
    connections: dict = {}
    for left, right in zip(names, names[1:]):
        connections.setdefault(left, {"main": [[]]})
        connections[left]["main"][0].append({"node": right, "type": "main", "index": 0})
    return connections


def chain_from_if(if_name: str, true_names: list[str]) -> dict:
    connections: dict = {if_name: {"main": [[], []]}}
    if not true_names:
        return connections
    first = true_names[0]
    connections[if_name]["main"][0].append({"node": first, "type": "main", "index": 0})
    for left, right in zip(true_names, true_names[1:]):
        connections.setdefault(left, {"main": [[]]})
        connections[left]["main"][0].append({"node": right, "type": "main", "index": 0})
    return connections


def build_workflows(env: dict[str, str]) -> list[dict]:
    token = env["BOT_TOKEN"]
    admin = env["ADMIN_TELEGRAM_IDS"].split(",")[0].strip()
    marzban_url = env["MARZBAN_BASE_URL"].rstrip("/")
    marzban_user = env["MARZBAN_USERNAME"]
    marzban_pass = env["MARZBAN_PASSWORD"]

    # --- Workflow 1: renewal reminder ---
    w1_nodes = [
        schedule_node("Daily 10:00", "0 10 * * *", 0, 0),
        pg_node("Insert reminders", INSERT_REMINDERS_SQL, 260, 0),
        if_has_items("Any reminders?", 520, 0),
        pg_node("Load user rows", REMINDER_DETAILS_SQL, 780, 0),
        telegram_http(
            "Send reminder",
            "$json.telegram_id",
            "'سلام! اشتراک ' + $json.plan_name + ' شما ' + ($json.reminder_type === '3d' ? '۳ روز' : '۱ روز') + ' دیگر منقضی می‌شود.\\nبرای تمدید از منوی «سرویس‌های من» استفاده کنید.'",
            1040,
            0,
            token,
        ),
    ]
    w1_conn = {}
    w1_conn.update(chain("Daily 10:00", "Insert reminders", "Any reminders?"))
    w1_conn.update(chain_from_if("Any reminders?", ["Load user rows", "Send reminder"]))

    # --- Workflow 3: daily sales report ---
    report_text = (
        "'📊 گزارش فروش امروز\\n'"
        " + 'سفارش‌ها: ' + $json.total_orders + '\\n'"
        " + 'تکمیل‌شده: ' + $json.completed_orders + '\\n'"
        " + 'درآمد: ' + $json.revenue + ' تومان\\n'"
        " + 'کاربر جدید: ' + $json.new_users + '\\n'"
        " + 'تمدید: ' + $json.renewals + '\\n'"
        " + 'پرداخت معلق: ' + $json.pending_payments + '\\n'"
        " + 'خطای provisioning: ' + $json.failed_provisioning"
    )
    w3_nodes = [
        schedule_node("Daily 21:00", "0 21 * * *", 0, 0),
        pg_node("Sales stats", DAILY_REPORT_SQL, 260, 0),
        telegram_http("Send report", admin, report_text, 520, 0, token),
    ]
    w3_conn = chain("Daily 21:00", "Sales stats", "Send report")

    # --- Workflow 4: Marzban health ---
    w4_nodes = [
        schedule_node("Every 10 min", "*/10 * * * *", 0, 0),
        {
            "parameters": {
                "method": "POST",
                "url": f"{marzban_url}/api/admin/token",
                "sendBody": True,
                "contentType": "form-urlencoded",
                "bodyParameters": {
                    "parameters": [
                        {"name": "username", "value": marzban_user},
                        {"name": "password", "value": marzban_pass},
                        {"name": "grant_type", "value": "password"},
                    ]
                },
                "options": {"allowUnauthorizedCerts": True},
            },
            "id": node_id(),
            "name": "Marzban login",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [260, 0],
        },
        {
            "parameters": {
                "method": "GET",
                "url": f"{marzban_url}/api/system",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "Authorization", "value": "=Bearer {{ $json.access_token }}"}
                    ]
                },
                "options": {"allowUnauthorizedCerts": True},
            },
            "id": node_id(),
            "name": "Marzban system",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [520, 0],
        },
        {
            "parameters": {
                "conditions": {
                    "combinator": "or",
                    "conditions": [
                        {
                            "id": node_id(),
                            "leftValue": "={{ $json.version }}",
                            "operator": {"type": "string", "operation": "notExists"},
                        }
                    ],
                }
            },
            "id": node_id(),
            "name": "Unhealthy?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2.2,
            "position": [780, 0],
        },
        pg_node("Record alert", ALERT_INSERT_SQL, 1040, 0),
        if_has_items("Should notify?", 1300, 0),
        telegram_http(
            "Alert admin",
            admin,
            "'⚠️ Marzban روی VPS پاسخ سالم نمی‌دهد. پنل و provisioning را بررسی کنید.'",
            1560,
            0,
            token,
        ),
    ]
    w4_conn = {}
    w4_conn.update(chain("Every 10 min", "Marzban login", "Marzban system", "Unhealthy?"))
    w4_conn.update(chain_from_if("Unhealthy?", ["Record alert", "Should notify?", "Alert admin"]))

    # --- Workflow 5: lead follow-up ---
    w5_nodes = [
        schedule_node("Daily 11:00", "0 11 * * *", 0, 0),
        pg_node("Insert leads", LEAD_INSERT_SQL, 260, 0),
        if_has_items("New leads?", 520, 0),
        pg_node("Load telegram id", LEAD_USER_SQL, 780, 0),
        telegram_http(
            "Follow up",
            "$json.telegram_id",
            "'سلام! اگر برای خرید VPN سوالی دارید، همین‌جا پیام بدهید یا از منوی ربات پلن‌ها را ببینید.'",
            1040,
            0,
            token,
        ),
    ]
    w5_conn = {}
    w5_conn.update(chain("Daily 11:00", "Insert leads", "New leads?"))
    w5_conn.update(chain_from_if("New leads?", ["Load telegram id", "Follow up"]))

    return [
        workflow("VPN Renewal Reminder", w1_nodes, w1_conn),
        workflow("VPN Daily Sales Report", w3_nodes, w3_conn),
        workflow("VPN Marzban Health Alert", w4_nodes, w4_conn),
        workflow("VPN Lead Follow-up", w5_nodes, w5_conn),
    ]


def main() -> None:
    env_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    text = env_path.read_text(encoding="utf-8")
    env = {
        "POSTGRES_PASSWORD": env_get(text, "POSTGRES_PASSWORD"),
        "BOT_TOKEN": env_get(text, "BOT_TOKEN"),
        "ADMIN_TELEGRAM_IDS": env_get(text, "ADMIN_TELEGRAM_IDS"),
        "MARZBAN_BASE_URL": env_get(text, "MARZBAN_BASE_URL"),
        "MARZBAN_USERNAME": env_get(text, "MARZBAN_USERNAME"),
        "MARZBAN_PASSWORD": env_get(text, "MARZBAN_PASSWORD"),
    }
    missing = [k for k, v in env.items() if not v.strip()]
    if missing:
        print(f"ERROR: missing in .env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    creds = [
        {
            "id": str(uuid.uuid4()),
            "name": "VPN Sales Postgres",
            "type": "postgres",
            "data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database": "vpn_sales",
                "user": "vpn",
                "password": env["POSTGRES_PASSWORD"],
                "ssl": "disable",
            },
        },
        {
            "id": str(uuid.uuid4()),
            "name": "VPN Sales Telegram",
            "type": "telegramApi",
            "data": {"accessToken": env["BOT_TOKEN"]},
        },
    ]

    workflows = build_workflows(env)

    (out_dir / "credentials.json").write_text(json.dumps(creds, indent=2), encoding="utf-8")
    (out_dir / "workflows.json").write_text(json.dumps(workflows, indent=2), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({"projectId": PROJECT_ID}), encoding="utf-8")
    print(f"Generated {len(creds)} credentials and {len(workflows)} workflows in {out_dir}")


if __name__ == "__main__":
    main()
