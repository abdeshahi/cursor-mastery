/**
 * CTTEL product sync rules (mirrors n8n Code node). Unit-testable without n8n.
 */

export const PRICE_CHANGE_THRESHOLD = 0.15;

/**
 * @param {unknown} value
 * @returns {number|null}
 */
export function parsePrice(value) {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  const n = Number(String(value).replace(/,/g, '').trim());
  if (!Number.isFinite(n)) {
    return null;
  }
  return n;
}

/**
 * @param {number|null} price
 * @param {{ allowZero?: boolean }} opts
 */
export function validatePrice(price, opts = {}) {
  const { allowZero = false } = opts;
  if (price === null) {
    return { ok: false, reason: 'missing_price' };
  }
  if (price < 0) {
    return { ok: false, reason: 'negative_price' };
  }
  if (price === 0 && !allowZero) {
    return { ok: false, reason: 'zero_price_not_allowed' };
  }
  return { ok: true };
}

/**
 * @param {Record<string, unknown>} input
 * @param {Record<string, unknown>|null} existing Woo product from API
 */
export function buildProductPlan(input, existing) {
  const sku = String(input.sku || '').trim();
  if (!sku) {
    return { action: 'error', error: 'missing_sku' };
  }

  const isUpdate = Boolean(existing && existing.id);
  const dryErrors = [];

  const oldRegular = parsePrice(existing?.regular_price);
  const oldSale = parsePrice(existing?.sale_price);
  const oldStock =
    existing?.stock_quantity !== undefined && existing?.stock_quantity !== null
      ? Number(existing.stock_quantity)
      : null;

  /** @type {Record<string, unknown>} */
  const payload = {
    sku,
    name: input.name || (existing?.name ?? sku),
    status: input.status || existing?.status || 'publish',
    manage_stock: input.manage_stock !== false,
  };

  if (input.short_description !== undefined && input.short_description !== '') {
    payload.short_description = input.short_description;
  }
  if (input.description !== undefined && input.description !== '') {
    payload.description = input.description;
  }

  const newRegularRaw = input.regular_price;
  const newRegular = parsePrice(newRegularRaw);
  if (newRegularRaw !== undefined && newRegularRaw !== null && newRegularRaw !== '') {
    const v = validatePrice(newRegular);
    if (!v.ok) {
      dryErrors.push(`regular_price:${v.reason}`);
    } else {
      payload.regular_price = String(newRegular);
    }
  } else if (!isUpdate && newRegular === null) {
    dryErrors.push('regular_price:required_for_create');
  }

  const hasSaleInput =
    input.sale_price !== undefined &&
    input.sale_price !== null &&
    String(input.sale_price).trim() !== '';
  if (hasSaleInput) {
    const newSale = parsePrice(input.sale_price);
    const v = validatePrice(newSale, { allowZero: false });
    if (!v.ok) {
      dryErrors.push(`sale_price:${v.reason}`);
    } else {
      payload.sale_price = String(newSale);
    }
  }

  let stockSkipped = false;
  if (input.stock_quantity === null || input.stock_quantity === undefined || input.stock_quantity === '') {
    stockSkipped = true;
  } else {
    const qty = Number(input.stock_quantity);
    if (!Number.isFinite(qty) || qty < 0) {
      stockSkipped = true;
      dryErrors.push('stock:malformed');
    } else {
      payload.stock_quantity = qty;
      payload.stock_status = qty === 0 ? 'outofstock' : 'instock';
    }
  }

  if (input.featured === true) {
    payload.featured = true;
  } else if (input.featured === false && isUpdate) {
    payload.featured = false;
  }

  const installment = Boolean(input.installment_available);
  payload.meta_data = [
    {
      key: '_cttel_installment_available',
      value: installment ? 'yes' : 'no',
    },
  ];

  const effectiveOld = oldSale ?? oldRegular;
  const effectiveNew = parsePrice(payload.sale_price) ?? parsePrice(payload.regular_price);
  let priceChangePct = null;
  let needsPriceApproval = false;
  if (effectiveOld !== null && effectiveNew !== null && effectiveOld > 0) {
    priceChangePct = Math.abs(effectiveNew - effectiveOld) / effectiveOld;
    needsPriceApproval = priceChangePct > PRICE_CHANGE_THRESHOLD;
  }

  if (needsPriceApproval) {
    return {
      action: isUpdate ? 'price_approval' : 'create_with_price_approval',
      sku,
      existingId: existing?.id ?? null,
      payload,
      old_price: effectiveOld,
      new_price: effectiveNew,
      percentage_change: priceChangePct,
      stockSkipped,
      errors: dryErrors,
    };
  }

  if (dryErrors.length > 0 && dryErrors.some((e) => e.startsWith('regular_price') || e === 'missing_sku')) {
    return { action: 'skip', sku, errors: dryErrors, reason: 'validation' };
  }

  return {
    action: isUpdate ? 'update' : 'create',
    sku,
    existingId: existing?.id ?? null,
    payload,
    old_price: effectiveOld,
    new_price: effectiveNew,
    percentage_change: priceChangePct,
    old_stock: oldStock,
    new_stock: stockSkipped ? null : payload.stock_quantity,
    stockSkipped,
    errors: dryErrors,
    categorySlug: String(input.category || '').trim(),
    brand: String(input.brand || '').trim(),
    image_url: String(input.image_url || '').trim(),
  };
}

/**
 * @param {string} imageUrl
 * @param {Array<{src?: string}>} existingImages
 */
export function shouldImportImage(imageUrl, existingImages) {
  if (!imageUrl || !/^https?:\/\//i.test(imageUrl)) {
    return false;
  }
  if (!existingImages || existingImages.length === 0) {
    return true;
  }
  const norm = imageUrl.split('?')[0];
  return !existingImages.some((img) => img.src && img.src.split('?')[0] === norm);
}
