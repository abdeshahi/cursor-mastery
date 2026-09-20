# WooCommerce REST API — CTTEL n8n Automation

## Readiness check

Public endpoint (no secrets):

```bash
./automation/scripts/verify-wc-api.sh
```

Expected: **HTTP 401** on `GET /wp-json/wc/v3/products` (API exists, auth required).

Live store: `https://cttel.ir` — currency **IRT (تومان)**; do not convert in n8n.

## Create API key (wp-admin)

1. Log in: `https://cttel.ir/wp-admin`
2. **WooCommerce → Settings → Advanced → REST API**
3. **Add key**
   - Description: `CTTEL n8n Automation`
   - User: administrator dedicated to automation (recommended) or existing admin
   - Permissions: **Read/Write**
4. Copy **Consumer key** and **Consumer secret** once.

## Store secrets (never in git)

| Where | What |
|-------|------|
| n8n Credentials → **WooCommerce API** | URL `https://cttel.ir`, Consumer key, Consumer secret |
| n8n Credentials → **Telegram** | Bot token |
| n8n Environment | `TELEGRAM_CHAT_ID` |
| VPS `CREDENTIALS.md` (optional, gitignored) | Backup reference for ops |

Do **not** commit keys to this repository or hard-code in workflow JSON.

## Permissions scope

The REST key has WooCommerce Read/Write only (no separate scope UI). Use a dedicated WP user with `manage_woocommerce` / product edit caps; avoid sharing personal admin keys.

## Installment meta

Mu-plugin `cttel-wc-rest-automation.php` registers `_cttel_installment_available` for REST (`yes` / `no`). Deploy to production before relying on automation for installment flags.

## Verify authenticated access (on VPS or trusted machine)

```bash
# Replace placeholders locally — do not paste secrets into tickets
curl -s -u "ck_XXXX:cs_XXXX" \
  "https://cttel.ir/wp-json/wc/v3/products?per_page=1" | head -c 200
```

Expect JSON array (possibly empty), not 401.
