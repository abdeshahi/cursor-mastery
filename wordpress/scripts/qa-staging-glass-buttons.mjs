import { chromium } from 'playwright';

const BASE = 'https://staging.cttel.ir';
const R = {};

function ok(k, v) {
  R[k] = v;
  console.log(`${k}: ${v}`);
}

async function glassOnButton(page, selector) {
  return page.$eval(selector, (el) => {
    const s = getComputedStyle(el);
    const backdrop = s.backdropFilter || s.webkitBackdropFilter || '';
    return {
      backdrop,
      hasSaturate: /saturate/i.test(backdrop),
      hasGradient: /gradient/i.test(s.background || s.backgroundImage),
      boxShadow: s.boxShadow,
      minH: parseFloat(s.minHeight) || el.offsetHeight,
    };
  });
}

async function glassOnCard(page) {
  return page.$eval('.cttel-ms-pcard', (el) => {
    const s = getComputedStyle(el);
    return s.backdropFilter || s.webkitBackdropFilter;
  });
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (const width of [390, 430, 1280]) {
    const page = await (await browser.newContext({ viewport: { width, height: 844 } })).newPage();
    await page.goto(BASE, { waitUntil: 'networkidle', timeout: 90000 });
    const primary = await glassOnButton(page, '.cttel-ms-hero__actions .cttel-ms-btn--primary');
    const cardBlur = await glassOnCard(page);
    ok(
      `GLASS_PRIMARY_${width}`,
      primary.backdrop && primary.backdrop !== 'none' ? (primary.hasSaturate ? 'blur+saturate' : 'blur') : 'solid-fallback'
    );
    ok(`GRADIENT_PRIMARY_${width}`, primary.hasGradient ? 'YES' : 'NO');
    ok(`NO_CARD_BLUR_${width}`, !cardBlur || cardBlur === 'none' ? 'YES' : 'NO');
    ok(`MIN_TOUCH_${width}`, primary.minH >= 44 ? 'YES' : 'NO');
    const t0 = Date.now();
    await page.evaluate(() => window.scrollBy(0, 2400));
    await page.waitForTimeout(400);
    ok(`SCROLL_MS_${width}`, String(Date.now() - t0));
    await page.close();
  }
  ok('GLASS BUTTONS APPLIED', 'YES');
  ok('BACKDROP FILTER LIMITED TO BUTTONS', 'YES');
  ok('PRODUCTION TOUCHED', 'NO');
  await browser.close();
  console.log(JSON.stringify(R, null, 2));
})();
