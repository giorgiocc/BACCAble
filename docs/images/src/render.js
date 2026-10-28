// Renders every docs/images/src/*.svg to docs/images/<name>.png (uses the preinstalled Playwright Chromium).
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const src = __dirname;
  const out = path.join(src, '..');
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1.5 });
  for (const f of fs.readdirSync(src).filter((n) => n.endsWith('.svg'))) {
    const svg = fs.readFileSync(path.join(src, f), 'utf8');
    const w = +svg.match(/width="(\d+)"/)[1];
    const h = +svg.match(/height="(\d+)"/)[1];
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({ path: path.join(out, f.replace('.svg', '.png')), clip: { x: 0, y: 0, width: w, height: h } });
    console.log('rendered', f);
  }
  await browser.close();
})();
