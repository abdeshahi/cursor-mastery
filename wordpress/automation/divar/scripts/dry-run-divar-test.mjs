#!/usr/bin/env node
import { validateDivarProduct } from './divar-validate.mjs';
import { buildDivarLayer } from './divar-payload-builder.mjs';

const sample = {
  product_id: 999,
  sku: 'USED-TEST-001',
  name: 'iPhone 13 Pro Max 256GB',
  used_phone: true,
  publish_to_divar: true,
  divar_title: 'آیفون 13 پرو مکس 256 گیگ',
  divar_price: '42500000',
  divar_city: 'tehran',
  divar_category_slug: 'mobile-phones',
  condition: 'very_good',
  battery_health: '87',
  storage: '256GB',
  color: 'Graphite',
  body_condition: 'خط و خش جزئی',
  repair_history: 'not_repaired',
  registered: 'yes',
  box: 'no',
  accessories: 'کابل شارژ',
  warranty: '7 روز مهلت تست CTTEL',
  description: 'گوشی دست‌دوم تست CTTEL — DRY RUN',
  images: ['https://cttel.ir/wp-content/uploads/example-real-photo.jpg'],
  divar_post_token: '',
  divar_status: 'pending',
  wc_url: 'https://cttel.ir/product/used-test-001/',
};

const v = validateDivarProduct(sample);
if (!v.ok) {
  console.error('Validation FAIL', v.errors);
  process.exit(1);
}
const layer = buildDivarLayer(sample);
console.log('Validation PASS');
console.log(JSON.stringify(layer, null, 2));
console.log('\nDRY RUN: no Divar HTTP call made.');
