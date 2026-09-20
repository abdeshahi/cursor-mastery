# CTTEL Used Phone → Divar (Kenar Open Platform)

WooCommerce remains **source of truth**. Divar is a **publish channel** only.

## Architecture

```
wp-admin Product [✓ Used Phone] [✓ Publish to Divar]
        ↓ (optional wp_remote_post)
n8n Webhook: cttel-divar-publish
        ↓
GET /wp-json/cttel/v1/divar-product/{id}
        ↓
Validate → build Divar layer → (DRY_RUN | LIVE gated)
        ↓
Kenar API open-api.divar.ir (after approval)
        ↓
Update WC meta: _cttel_divar_post_token, _cttel_divar_status
        ↓
Telegram (CTTEL bot — not VPN bot)
```

Sold path:

```
WC stock_status → outofstock (used phone)
        ↓
n8n Webhook: cttel-divar-sold
        ↓
DELETE /v1/open-platform/post/{token} (if permitted) OR Telegram manual close
```

## WordPress setup

1. Deploy mu-plugin `cttel-used-phone-divar.php`
2. Set webhook URLs (not in git), e.g. on VPS:

```bash
wp option update cttel_n8n_divar_webhook_url 'https://<n8n-host>/webhook/cttel-divar-publish' --allow-root
wp option update cttel_n8n_divar_sold_webhook_url 'https://<n8n-host>/webhook/cttel-divar-sold' --allow-root
```

## n8n setup

| Workflow | File |
|----------|------|
| Publish | `workflows/cttel-used-phone-divar-publish.json` |
| Sold | `workflows/cttel-used-phone-divar-sold.json` |

Environment (n8n):

| Variable | Default | Meaning |
|----------|---------|---------|
| `DRY_RUN` | `true` | No Divar writes |
| `DIVAR_LIVE_SUBMIT` | `false` | **Live Writes DISABLED** until you set `true` |
| `TELEGRAM_CTTEL_CHAT_ID` | — | CTTEL automation chat |

Credentials in n8n only:

- WooCommerce API (CTTEL n8n Automation)
- Kenar: API key header + OAuth tokens + business token
- Telegram: **CTTEL Automation** bot

## First test (single product)

1. Create **one** used-phone test product in wp-admin.
2. Fill Divar fields + real images.
3. Check **Publish to Divar**, save → status `pending`.
4. POST webhook with `{ "dry_run": true, "product_id": <id> }`.
5. Review Telegram + JSON `divar_layer` preview.
6. **Do not** set `DIVAR_LIVE_SUBMIT=true` until Divar permissions + owner approval.

```bash
node automation/divar/scripts/dry-run-divar-test.mjs
```

## Docs

- `docs/DIVAR-API.md` — official endpoints & permissions
- `docs/MAPPING.md` — field mapping
- `../docs/CREDENTIALS-CHECKLIST.md` — shared WooCommerce creds

## Live Writes

**DISABLED by default** in workflow logic (`DRY_RUN` + `DIVAR_LIVE_SUBMIT=false`).
