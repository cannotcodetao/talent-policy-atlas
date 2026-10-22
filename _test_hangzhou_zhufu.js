const { JSDOM } = require('jsdom');
const fs = require('fs');
const html = fs.readFileSync('人才引进政策_2026.html','utf-8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable' });
const { document, window } = dom.window;

const dataOk = window.DATA && window.DATA['杭州'];
console.log('DATA loaded?', !!dataOk);

window.openDrawer('杭州');
const rows = [...document.querySelectorAll('#dtable tr')];
let hzfCount = 0, srcPresent = 0, srcMissing = 0;
for (const tr of rows) {
  const text = tr.textContent;
  if (!text.includes('租房') && !text.includes('租赁')) continue;
  hzfCount++;
  const srcSpan = tr.querySelector('.src');
  const hasSrc = !!srcSpan;
  if (hasSrc) srcPresent++; else srcMissing++;
  console.log('--row--');
  console.log(text.replace(/\s+/g,' ').slice(0, 220));
  console.log('  source:', srcSpan ? (srcSpan.querySelector('a')?.href || '(no a)') : 'NONE');
}
console.log(`\nTotal rows mentioning 租房/租赁: ${hzfCount}; with .src: ${srcPresent}; missing .src: ${srcMissing}`);
