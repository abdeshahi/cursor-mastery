#!/usr/bin/env node
/**
 * Local DRY RUN logic test (no WooCommerce / n8n required).
 */
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  buildProductPlan,
  parsePrice,
  shouldImportImage,
  PRICE_CHANGE_THRESHOLD,
} from '../lib/product-sync-logic.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const sample = JSON.parse(readFileSync(join(__dir, '../sample-input.json'), 'utf8'));

let failed = 0;

function assert(cond, msg) {
  if (!cond) {
    console.error('FAIL:', msg);
    failed += 1;
  } else {
    console.log('OK:', msg);
  }
}

assert(parsePrice('3,500,000') === 3500000, 'parsePrice commas');
assert(parsePrice('') === null, 'parsePrice empty');

const existingProduct = {
  id: 99,
  name: 'Existing',
  regular_price: '10000000',
  sale_price: '',
  stock_quantity: 10,
  status: 'publish',
  images: [{ src: 'https://cttel.ir/wp-content/uploads/existing.png' }],
};

const planUpdate = buildProductPlan(
  {
    sku: 'CTTEL-PRICE-APPROVAL-TEST',
    regular_price: '12000000',
    stock_quantity: 2,
  },
  existingProduct
);
assert(planUpdate.action === 'price_approval', 'price change >15% triggers approval');
assert(
  planUpdate.percentage_change > PRICE_CHANGE_THRESHOLD,
  'percentage_change computed'
);

const planCreate = buildProductPlan(
  {
    sku: 'NEW-1',
    name: 'New Product',
    regular_price: '500000',
    stock_quantity: 3,
    installment_available: true,
  },
  null
);
assert(planCreate.action === 'create', 'create when no existing');
assert(planCreate.payload.meta_data[0].value === 'yes', 'installment meta yes');

const planStockZero = buildProductPlan({ sku: 'S1', regular_price: '100', stock_quantity: 0 }, null);
assert(planPlanStockZeroFix(planStockZero), 'stock zero outofstock');

function planPlanStockZeroFix(plan) {
  return plan.payload.stock_status === 'outofstock' && plan.payload.stock_quantity === 0;
}

assert(
  !shouldImportImage('https://cttel.ir/wp-content/uploads/existing.png', existingProduct.images),
  'skip duplicate image URL'
);
assert(
  shouldImportImage('https://cdn.example/new.png', existingProduct.images),
  'import new image URL'
);

for (const product of sample.products) {
  const plan = buildProductPlan(product, product.sku.includes('PRICE') ? existingProduct : null);
  console.log('Sample plan', product.sku, '→', plan.action);
}

if (failed > 0) {
  process.exit(1);
}
console.log('\nDRY RUN logic: PASS');
