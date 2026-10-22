// 全量 11 城文件快速核验：新城市(温州)抽屉 13 维分区 + 对比表 13 行。
const fs = require('fs');
const { JSDOM } = require('jsdom');
const BASE = __dirname;
const HTML = path = require('path').join(BASE, '浙江人才引进政策_2026.html');
const dom = new JSDOM(fs.readFileSync(HTML, 'utf-8'), { runScripts: 'dangerously', pretendToBeVisual: true });
const { window } = dom; const { document } = window;
window.HTMLElement.prototype.scrollIntoView = function () {};
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));
function openCity(c){ const row = $$('#cityIndex .cityrow').find(e=>e.textContent.includes(c)); if(row) row.click(); }
function chk(n,ok,d=''){ console.log(`[${ok?'PASS':'FAIL'}] ${n} ${d?':: '+d:''}`); if(!ok) process.exitCode=1; }

openCity('温州');
const dt = $('#dtable').innerHTML;
const secs = [...dt.matchAll(/class="[^"]*\bsec\b[^"]*"><td colspan="2">([^<]+)<\/td>/g)].map(m=>m[1].trim());
const anju=['先租后售人才房','定向优惠价购房','人才购房补贴/房票','共有产权房','企业内部福利房'];
chk('温州抽屉 13 维分区', secs.length===13, `n=${secs.length}`);
chk('温州含五维安居', anju.every(a=>secs.some(s=>s.includes(a))), secs.filter(s=>anju.some(a=>s.includes(a))).join('|'));
chk('温州先租后售=占位非编造', dt.includes('暂未查询到官方公开政策'));
$('#dclose').click();

document.getElementById('compareBtn').click();
['杭州','温州','绍兴'].forEach(c=>{ const chip=$$('#cmpChips .chip').find(e=>e.textContent.trim()===c); if(chip) chip.click(); });
document.getElementById('genCmp').click();
const rows=$$('#ctable tbody tr');
chk('对比表 13 维行', rows.length===13, `rows=${rows.length}`);
const labels=rows.map(r=>{const th=r.querySelector('th');return th?th.textContent.trim():'';});
chk('对比表含五维安居标签', anju.every(a=>labels.some(l=>l.includes(a))));
console.log('DONE');
