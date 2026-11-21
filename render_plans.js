// Prints plan.html -> <name>.pdf (Letter landscape) and a PNG of every page, for each folder given.
// One Chromium at a time, closed right away. Run under:  flock /tmp/freebies-chromium.lock node render_plans.js dir1 dir2 ...
// Playwright is looked up through NODE_PATH (for example NODE_PATH=/opt/carmax/node_modules).
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1056, height: 816 }, deviceScaleFactor: 1.6 });
    for (const dir of process.argv.slice(2)) {
      const abs = path.resolve(dir);
      const name = fs.readFileSync(path.join(abs, 'plan.name'), 'utf8').trim();
      await page.goto('file://' + path.join(abs, 'plan.html'), { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const report = await page.evaluate(() => [...document.querySelectorAll('.page')].map((p, i) => {
        const foot = p.querySelector('.foot');
        const limit = foot.getBoundingClientRect().top;
        let max = 0;
        p.querySelectorAll('.grid, .views, .box').forEach(el => { max = Math.max(max, el.getBoundingClientRect().bottom); });
        return `${i + 1}:${Math.round(limit - max)}`;
      }));
      console.log(name, 'spare px per page', report.join(' '));
      await page.pdf({ path: path.join(abs, name + '.pdf'), width: '11in', height: '8.5in', printBackground: true,
        margin: { top: '0', right: '0', bottom: '0', left: '0' }, preferCSSPageSize: true });
      const pages = await page.$$('.page');
      fs.mkdirSync(path.join(abs, 'img'), { recursive: true });
      for (let i = 0; i < pages.length; i++) {
        await pages[i].screenshot({ path: path.join(abs, 'img', `${name}-sheet-${i + 1}.png`) });
      }
    }
  } finally {
    await browser.close();
  }
})();
