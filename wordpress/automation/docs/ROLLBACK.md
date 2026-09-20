# Rollback strategy — CTTEL product automation

## Disable automation immediately

1. n8n → **CTTEL Product Sync** → toggle **Inactive** (stops webhook).
2. Revoke WooCommerce REST key: **WooCommerce → Settings → Advanced → REST API → Revoke** `CTTEL n8n Automation`.

No WordPress reinstall or database reset required.

## Undo bad product writes

- **Single product**: wp-admin → **Products → Edit** → restore price/stock/image manually.
- **Bulk recent changes**: use WooCommerce **product revisions** (if enabled) or restore from nightly backup:

```bash
# On VPS — existing backup script only
cd /opt/cttel-wordpress/app
./scripts/backup.sh
# Restore from backups/YYYYmmdd_* if needed (DB + files) — ops procedure
```

Automation never deletes products; rollback is edit or DB restore from backup.

## Remove REST meta plugin only

```bash
docker exec wp_app rm -f /var/www/html/wp-content/mu-plugins/cttel-wc-rest-automation.php
```

Storefront and installment display unchanged (`cttel-product-cards.php` remains).

## Clear n8n logs

Workflow **Static Data** (`global.logs`) — in n8n Code node or reset workflow static data from UI if log volume is an issue. No external DB to migrate.

## Re-enable safely

1. Fix source data / workflow
2. Run `dry_run: true`
3. Review Telegram + JSON response
4. Set `dry_run: false` for limited SKU pilot
5. Expand batch size gradually
