// Audit: every city, render drawer, check 租房/租赁 mentions for missing .src link
const { JSDOM, VirtualConsole } = require('jsdom');
const fs = require('fs');

const html = fs.readFileSync('人才引进政策_2026.html','utf-8');
const vc = new VirtualConsole();
vc.on('jsdomError', e => {/*console.log('JSE:', e.message.slice(0,200));*/});
const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true, virtualConsole: vc });
const w = dom.window;
const doc = w.document;

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

(async () => {
  // Eval inline script in window context so const META/DATA/EDU become visible
  const scriptText = doc.querySelectorAll('script')[0].textContent;
  // Wrap to expose consts via window assignment（Phase 27 后 EDU 常量已由 eduFilter 取代，不再暴露）
  const wrappedScript = scriptText
    + '\n;window.__META = META;\nwindow.__DATA = DATA;\n';
  try {
    w.eval(wrappedScript);
  } catch(e) {
    console.log('eval FAIL:', e.message.slice(0,300));
    process.exit(1);
  }
  console.log('Inline script eval done.');
  console.log('  __META provinces:', w.__META.provinces.length);
  console.log('  __DATA cities:', Object.keys(w.__DATA).length);
  console.log('  openDrawer:', typeof w.openDrawer);
  console.log('  buildCompareTable:', typeof w.buildCompareTable);

  const cities = w.__META.provinces.flatMap(p => p.cities);
  const missing = [];
  const summary = {};
  for (const c of cities) {
    w.openDrawer(c);
    const rows = [...doc.querySelectorAll('#dtable tr')];
    let hzfCount = 0, srcMissing = 0;
    const noSrcRows = [];
    for (const tr of rows) {
      const text = tr.textContent;
      if (!text.includes('租房') && !text.includes('租赁')) continue;
      hzfCount++;
      const srcSpan = tr.querySelector('.src');
      if (!srcSpan) {
        srcMissing++;
        noSrcRows.push(text.replace(/\s+/g,' ').slice(0, 180));
      }
    }
    summary[c] = {rows: hzfCount, missing: srcMissing};
    if (srcMissing > 0) missing.push({city: c, hzfCount, srcMissing, noSrcRows});
  }
  console.log('\n--- summary ---');
  for (const [c, s] of Object.entries(summary)) {
    const tag = s.missing > 0 ? '*' : ' ';
    console.log(`  ${tag} ${c}: rows=${s.rows}, missing=${s.missing}`);
  }
  console.log('\nCities with missing source:', missing.length);
  for (const m of missing) {
    console.log(`\n[${m.city}] rows=${m.hzfCount}, missing=${m.srcMissing}`);
    m.noSrcRows.forEach((t,i)=>console.log(`   #${i}: ${t}`));
  }
  process.exit(0);
})();
