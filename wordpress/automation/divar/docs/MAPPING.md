# WooCommerce → Divar mapping (CTTEL)

| WooCommerce / CTTEL field | Divar layer | Kenar official schema |
|---------------------------|-------------|------------------------|
| `name` / `_cttel_divar_title` | `title` | Category template «title» |
| `_cttel_divar_price` or `regular_price` | `price` (IRT, no conversion) | Price field per schema |
| Gallery + featured image | `image_urls` → upload URLs API | Image references after upload |
| `_cttel_divar_city` | `city_slug` | City enum from schema |
| `_cttel_divar_category_slug` | `category_slug` | Select category in submit request |
| `_cttel_divar_description` + attrs | `description` | Description + optional attrs |
| `_cttel_divar_condition` | `attributes.condition` | Category-specific field |
| `_cttel_divar_battery_health` | `attributes.battery_health` | Category-specific field |
| `_cttel_divar_storage` | `attributes.storage` | Category-specific field |
| `_cttel_divar_color` | `attributes.color` | Category-specific field |
| `_cttel_divar_body_condition` | in `description` | — |
| `_cttel_divar_repair_history` | `attributes.repair_history` | Category-specific field |
| `_cttel_divar_registered` | `attributes.registered` | Category-specific field |
| `_cttel_divar_box` | `attributes.box` | In description or schema field |
| `_cttel_divar_accessories` | in `description` | — |
| `_cttel_divar_warranty` | in `description` | — |
| `_cttel_divar_post_token` | `existing_post_token` | Update: `PUT .../post/{token}` |

**SEO / source of truth:** WooCommerce product page stays published when Divar ad goes live. On sale, set `stock_status=outofstock` only; do not trash the product.
