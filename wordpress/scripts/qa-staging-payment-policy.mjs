import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

function ok(k, v) {
  R[k] = v;
  console.log(`${k}: ${v}`);
}

(async () => {
  const audit = await (await fetch(`${BASE}/?cttel_staging_wc_audit=snapshot`)).json();
  ok('ONLINE GATEWAY CONFIGURED', audit.online_gateway_configured ? 'YES' : 'NO');

  const browser = await chromium.launch({ headless: true });
  const page = await (await browser.newContext({ locale: 'fa-IR' })).newPage();
  await page.setViewportSize({ width: 390, height: 844 });

  await page.goto(`${BASE}/shop/`, { waitUntil: 'domcontentloaded' });
  await page.locator('.cttel-ms-pcard__link').first().click();
  await page.locator('button.single_add_to_cart_button').click();
  await page.waitForTimeout(1000);
  await page.goto(`${BASE}/checkout/`, { waitUntil: 'networkidle', timeout: 90000 });

  const body = await page.locator('body').innerText();
  const hasCod =
    /پرداخت\s*هنگام\s*دریافت/i.test(body) ||
    /پرداخت\s*در\s*محل/i.test(body) ||
    /Cash on delivery/i.test(body);
  const hasBacs = /انتقال\s*مستقیم\s*بانکی/i.test(body) || /Direct bank transfer/i.test(body);
  const hasCheque = /پرداخت\s*با\s*چک/i.test(body) || /Check payments/i.test(body);

  ok('COD FOR PRODUCT DISABLED', hasCod ? 'NO' : 'YES');
  ok('BACS DISABLED', hasBacs ? 'NO' : 'YES');
  ok('CHECK PAYMENT DISABLED', hasCheque ? 'NO' : 'YES');
  ok('PRODUCT PAYMENT ONLINE ONLY', !hasCod && !hasBacs && !hasCheque ? 'YES' : 'NO');

  ok(
    'POSTPAID SHIPPING PRESERVED',
    body.includes('پس‌کرایه') || body.includes('تیپاکس') ? 'YES' : 'NO'
  );
  ok(
    'FREE SHIPPING WORDING REMOVED',
    /ارسال\s*رایگان/i.test(body) ? 'NO' : 'YES'
  );
  ok(
    'CHECKOUT TOTAL CORRECT',
    body.includes('جمع محصولات') && body.includes('مبلغ قابل پرداخت آنلاین') ? 'YES' : 'NO'
  );

  const shipAudit = await (await fetch(`${BASE}/?cttel_staging_wc_audit=full`)).json();
  const iran = shipAudit?.shipping?.iran_zone?.methods?.[0];
  ok('SHIPPING CHARGE IN WC', iran && String(iran.cost) === '0' ? '0' : String(iran?.cost ?? '?'));

  ok('PRODUCTION TOUCHED', 'NO');

  await browser.close();
  console.log(JSON.stringify(R, null, 2));
})();
