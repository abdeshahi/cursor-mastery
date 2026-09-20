# n8n & Environment Checklist (no secrets in repo)

## WooCommerce — `CTTEL n8n Automation`

- [ ] REST API key created (Read/Write)
- [ ] n8n credential type: **WooCommerce API**
- [ ] URL: `https://cttel.ir`
- [ ] Consumer key / secret stored only in n8n
- [ ] Linked to workflow node **Process Products**
- [ ] Test: `GET /products?per_page=1` succeeds from n8n (Execute node once with dry_run)

## Telegram

- [ ] Bot created via @BotFather
- [ ] n8n credential: **Telegram API** (bot token)
- [ ] Chat ID known (group/channel or user)
- [ ] n8n env: `TELEGRAM_CHAT_ID=<id>`
- [ ] Linked to **Telegram Summary** and **Telegram Price Approval**

## n8n workflow

- [ ] Imported `workflows/cttel-product-sync.json`
- [ ] Replaced `REPLACE_*` credential IDs in UI (after import)
- [ ] Webhook path: `cttel-product-sync`
- [ ] Workflow **Active**
- [ ] First run: `dry_run: true` with `sample-input.json`

## WordPress (one-time)

- [ ] `cttel-wc-rest-automation.php` deployed to `wp-content/mu-plugins/`
- [ ] Permalinks / REST unchanged (default for WC)

## Optional VPS env (if using n8n on same host)

Do not add to git. Example names only:

- `WC_BASE_URL` — only if overriding in custom nodes (workflow uses credential URL)
- `TELEGRAM_CHAT_ID`
