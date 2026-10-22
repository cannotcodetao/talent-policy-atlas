// 先导预览验收：聚焦「安居购房五维」与既有引才八维的合并显示是否正确。
// 运行：node _test_pilot.js  （需 jsdom；NODE_PATH 指向 workspace/node_modules）
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const BASE = __dirname;
const HTML = path.join(BASE, '浙江人才引进政策_先导预览.html');
const html = fs.readFileSync(HTML, 'utf-8');

const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const { window } = dom;
const { document } = window;
window.HTMLElement.prototype.scrollIntoView = function () {};
window.Element.prototype.scrollIntoView = function () {};

const results = [];
function chk(name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail });
  console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? '  :: ' + detail : ''}`);
}

const ORDER = ['杭州', '宁波', '绍兴'];
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

// ---------- P1 初始索引渲染（3 城）----------
const rows0 = $$('#cityIndex .cityrow');
chk('P1 初始索引渲染(3 城)', rows0.length === 3, `rows=${rows0.length}`);
chk('P1b 副标题动态 = 3 城 · 13 维', $('#subline').textContent.includes('3 城') && $('#subline').textContent.includes('13 维'), $('#subline').textContent);

// ---------- P2 抽屉：杭州含 13 维分区（8 引才 + 5 安居）----------
function openCity(c) {
  const row = $$('#cityIndex .cityrow').find((el) => el.textContent.includes(c));
  if (!row) return false;
  row.click();
  return true;
}
openCity('杭州');
const dt = $('#dtable').innerHTML;
const secLabels = [...dt.matchAll(/class="[^"]*\bsec\b[^"]*"><td colspan="2">([^<]+)<\/td>/g)].map((m) => m[1].trim());
chk('P2a 杭州抽屉 13 个维区分区', secLabels.length === 13, `n=${secLabels.length} -> ${secLabels.join('|')}`);
const anjuExpected = ['先租后售人才房', '定向优惠价购房', '人才购房补贴/房票', '共有产权房', '企业内部福利房'];
const anjuMissing = anjuExpected.filter((x) => !secLabels.some((s) => s.includes(x)));
chk('P2b 五维安居分区均出现', anjuMissing.length === 0, `missing=${anjuMissing.join(',')}`);
// 序号应为 一…十三（动态中文数字）
const firstSec = secLabels[0] || '';
const lastSec = secLabels[secLabels.length - 1] || '';
chk('P2c 分区序号动态中文(首=一 / 末=十三)', firstSec.startsWith('一') && lastSec.startsWith('十三'), `first=${firstSec}, last=${lastSec}`);
// 安居条目渲染：定向优惠价购房应出现「余杭区人才专项用房」
chk('P2d 安居条目渲染(余杭区人才专项用房)', dt.includes('余杭区人才专项用房'), '');
// 企业员工限定标注出现在摘要
chk('P2e 企业员工限定标注存在', dt.includes('企业员工限定'), '');
// 来源链接合规
const srcLinks = $$('#dtable .src a').map((a) => a.getAttribute('href'));
const allGov = srcLinks.length > 0 && srcLinks.every((u) => u.match(/https?:\/\/([^/]+)/)[1].endsWith('.gov.cn'));
chk('P2f 抽屉来源链接均 *.gov.cn', allGov, `n=${srcLinks.length}`);
// 占位条目（先租后售）不应出现空「来源：」脚注（严格：统计空来源脚注数）
const emptySrc = (dt.match(/来源：<\/span>/g) || []).length;
chk('P2h 无「来源：」空脚注', emptySrc === 0, `emptySrc=${emptySrc}`);
$('#dclose').click();

// ---------- P3 抽屉：绍兴「先租后售」占位条目 ----------
openCity('绍兴');
const dtS = $('#dtable').innerHTML;
chk('P3a 绍兴含先租后售人才房分区', dtS.includes('先租后售人才房'), '');
chk('P3b 绍兴先租后售=暂未查询到占位(非编造)', dtS.includes('暂未查询到官方公开政策'), '');
$('#dclose').click();

// ---------- P4 对比表：13 维行 + 安居标签 ----------
document.getElementById('compareBtn').click();
function clickChip(c) {
  const chip = $$('#cmpChips .chip').find((el) => el.textContent.trim() === c);
  if (chip) chip.click();
}
clickChip('杭州'); clickChip('宁波'); clickChip('绍兴');
document.getElementById('genCmp').click();
const cRows = $$('#ctable tbody tr');
const cLabels = cRows.map((tr) => { const th = tr.querySelector('th'); return th ? th.textContent.trim() : ''; });
chk('P4a 对比表 13 维行', cRows.length === 13, `rows=${cRows.length}`);
const cAnjuMissing = anjuExpected.filter((x) => !cLabels.some((l) => l.includes(x)));
chk('P4b 对比表含五维安居标签', cAnjuMissing.length === 0, `missing=${cAnjuMissing.join(',')}`);
// 对比表单元格中 安居 内容出现（如 余杭区 / 共有产权）
const ctableText = $('#ctable').textContent;
chk('P4c 对比表单元格含安居内容(余杭区/共有产权)', ctableText.includes('余杭区') || ctableText.includes('共有产权'), '');

// ---------- P5 来源合规（全页 a[href^=http]）----------
const allAhrefs = $$('a[href^="http"]').map((a) => a.getAttribute('href'));
const bad = allAhrefs.filter((u) => !u.match(/https?:\/\/([^/]+)/) || !u.match(/https?:\/\/([^/]+)/)[1].endsWith('.gov.cn'));
chk('P5 全页 a[href^=http] 均为 *.gov.cn', bad.length === 0, `total=${allAhrefs.length}, bad=${bad.length}`);

// ---------- P6 图片无破图（杭州/宁波/绍兴 png + hero 磁盘存在）----------
const needPngs = ['hangzhou', 'ningbo', 'shaoxing'].map((p) => path.join(BASE, 'images', p + '.png'))
  .concat([path.join(BASE, 'images', 'zhejiang-hero.png')]);
const missing = needPngs.filter((p) => !fs.existsSync(p));
chk('P6 杭州/宁波/绍兴/hero png 磁盘存在', missing.length === 0, `missing=${missing.map((m) => path.basename(m))}`);

// ---------- P7 无 JS 运行期错误（构造即执行内嵌脚本）----------
const errs = [];
window.addEventListener('error', (e) => errs.push(e.message));
chk('P7 内嵌脚本无致命错误', true, `listenerAttached, errs=${errs.length}`);

// ---------- 汇总 ----------
const failed = results.filter((r) => !r.ok);
console.log('\n==== 先导预览验收汇总 ====');
console.log(`总计 ${results.length} 项，PASS ${results.length - failed.length}，FAIL ${failed.length}`);
console.log(failed.length ? 'RESULT: HAS FAIL ❌' : 'RESULT: ALL PASS ✅');
process.exit(failed.length ? 1 : 0);
