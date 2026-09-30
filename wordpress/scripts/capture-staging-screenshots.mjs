import { chromium } from 'playwright';
import fs from 'fs';

const URL = process.env.STAGING_URL || 'https://staging.cttel.ir/';
const OUT = process.env.OUT_DIR || '/opt/cursor/artifacts';

fs.mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ args: ['--no-sandbox'] });

for (const [name, width, height] of [
  ['staging_homepage_mobile_390', 390, 5200],
  ['staging_homepage_desktop_1440', 1440, 4200],
]) {
  const page = await browser.newPage({ viewport: { width, height: Math.min(height, 900) } });
  await page.goto(URL, { waitUntil: 'networkidle', timeout: 120000 });
  await page.waitForTimeout(800);
  await page.screenshot({
    path: `${OUT}/${name}.png`,
    fullPage: true,
  });
  await page.close();
}

await browser.close();
console.log('Saved screenshots to', OUT);
