/**
 * Pre-flight validation before Divar submit (shared with n8n Code node).
 */

/**
 * @param {Record<string, unknown>} p Normalized CTTEL payload
 * @returns {{ ok: boolean, errors: string[] }}
 */
export function validateDivarProduct(p) {
  const errors = [];

  if (!p.used_phone) {
    errors.push('not_used_phone');
  }
  if (!p.publish_to_divar) {
    errors.push('publish_to_divar_disabled');
  }
  const title = String(p.divar_title || p.name || '').trim();
  if (title.length < 3) {
    errors.push('missing_title');
  }
  const price = Number(String(p.divar_price || '').replace(/,/g, ''));
  if (!Number.isFinite(price) || price <= 0) {
    errors.push('invalid_price');
  }
  const images = Array.isArray(p.images) ? p.images : [];
  const realImages = images.filter((u) => typeof u === 'string' && /^https?:\/\//.test(u));
  if (realImages.length === 0) {
    errors.push('missing_real_image');
  }
  if (!String(p.divar_city || '').trim()) {
    errors.push('missing_city');
  }
  if (!String(p.divar_category_slug || '').trim()) {
    errors.push('missing_divar_category');
  }

  return { ok: errors.length === 0, errors };
}
