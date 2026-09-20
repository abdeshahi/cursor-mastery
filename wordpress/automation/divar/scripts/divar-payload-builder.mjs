/**
 * Map WooCommerce normalized payload → Divar-oriented structure.
 * Exact Kenar JSON schema fields MUST be taken from Swagger for your category slug.
 * This builder prepares a stable CTTEL layer; n8n fills official schema in Code node.
 */

/**
 * @param {Record<string, unknown>} p from cttel_divar_build_payload / WC meta
 * @param {{ businessToken?: string, categorySchema?: Record<string, unknown> }} opts
 */
export function buildDivarLayer(p, opts = {}) {
  const descriptionParts = [];
  const desc = String(p.description || '').trim();
  if (desc) descriptionParts.push(desc);
  if (p.body_condition) descriptionParts.push(`وضعیت بدنه: ${p.body_condition}`);
  if (p.repair_history) descriptionParts.push(`سوابق تعمیر: ${p.repair_history}`);
  if (p.accessories) descriptionParts.push(`لوازم: ${p.accessories}`);
  if (p.warranty) descriptionParts.push(`گارانتی/تست: ${p.warranty}`);
  if (p.registered === 'yes') descriptionParts.push('رجیستر شده');
  if (p.box === 'yes') descriptionParts.push('جعبه دارد');

  return {
    _cttel_note: 'Map fields below into Kenar category JSON schema from Swagger before live submit',
    title: String(p.divar_title || p.name || '').trim(),
    price: Number(String(p.divar_price || '').replace(/,/g, '')),
    city_slug: String(p.divar_city || ''),
    category_slug: String(p.divar_category_slug || ''),
    description: descriptionParts.join('\n\n'),
    image_urls: Array.isArray(p.images) ? p.images : [],
    attributes: {
      condition: p.condition || null,
      battery_health: p.battery_health || null,
      storage: p.storage || null,
      color: p.color || null,
      repair_history: p.repair_history || null,
      registered: p.registered === 'yes',
      box: p.box === 'yes',
    },
    business_token: opts.businessToken || 'SET_IN_N8N_CREDENTIALS',
    wc_product_id: p.product_id,
    wc_sku: p.sku,
    wc_url: p.wc_url,
    existing_post_token: p.divar_post_token || null,
  };
}
