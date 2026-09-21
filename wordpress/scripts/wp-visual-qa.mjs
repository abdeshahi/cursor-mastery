import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const OUT = '/opt/cursor/artifacts/wp-real-home';
const URL = 'http://127.0.0.1/';

fs.mkdirSync(OUT, { recursive: true });

function overflowAudit(page) {
  return page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const offenders = [];
    document.querySelectorAll('body *').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.width <= 0 || r.height <= 0) return;
      if (r.right > vw + 1 || r.left < -1) {
        const cs = getComputedStyle(el);
        offenders.push({
          tag: el.tagName.toLowerCase(),
          id: el.id || '',
          cls: (el.className && String(el.className).slice(0, 80)) || '',
          right: Math.round(r.right),
          left: Math.round(r.left),
          width: Math.round(r.width),
          vw,
          scrollW: el.scrollWidth,
        });
      }
    });
    offenders.sort((a, b) => b.right - a.right);
    return {
      vw,
      bodyScrollWidth: document.body.scrollWidth,
      docScrollWidth: document.documentElement.scrollWidth,
      hasOverflow: document.documentElement.scrollWidth > vw + 1,
      scrollWidthExact: document.documentElement.scrollWidth === vw,
      top: offenders.slice(0, 12),
    };
  });
}

async function scrollToSelector(page, selector) {
  const box = await page.locator(selector).first().boundingBox();
  if (!box) return;
  await page.evaluate((y) => window.scrollTo(0, Math.max(0, y - 8)), box.y);
  await page.waitForTimeout(350);
}

const shots = [
  { name: '390-header-hero', width: 390, prepare: async (page) => page.evaluate(() => window.scrollTo(0, 0)) },
  { name: '390-rail-mosaic', width: 390, prepare: (page) => scrollToSelector(page, '.cttel-home-rail') },
  { name: '390-products', width: 390, prepare: (page) => scrollToSelector(page, '.cttel-home-products') },
  { name: '390-used-installment', width: 390, prepare: (page) => scrollToSelector(page, '.cttel-home-used'), height: 980 },
  { name: '1440-header-hero', width: 1440, prepare: async (page) => page.evaluate(() => window.scrollTo(0, 0)) },
  { name: '1440-mosaic-products', width: 1440, prepare: (page) => scrollToSelector(page, '.cttel-home-mosaic') },
  { name: '1440-lower-home', width: 1440, prepare: (page) => scrollToSelector(page, '.cttel-home-used'), height: 1000 },
];

const browser = await chromium.launch({ args: ['--no-sandbox'] });

for (const shot of shots) {
  const context = await browser.newContext({
    viewport: { width: shot.width, height: shot.width === 390 ? 844 : 900 },
    locale: 'fa-IR',
  });
  const page = await context.newPage();
  await page.goto(URL, { waitUntil: 'networkidle', timeout: 120000 });
  if (shot.prepare) await shot.prepare(page);
  if (shot.width === 390) {
    const audit = await overflowAudit(page);
    fs.writeFileSync(
      path.join(OUT, `390-overflow-${shot.name.replace('390-', '')}.json`),
      JSON.stringify(audit, null, 2)
    );
  }
  const height = shot.height || (shot.width === 390 ? 820 : 980);
  await page.screenshot({
    path: path.join(OUT, `${shot.name}.png`),
    clip: { x: 0, y: 0, width: shot.width, height },
  });
  await context.close();
}

await browser.close();
console.log('Saved to', OUT);
