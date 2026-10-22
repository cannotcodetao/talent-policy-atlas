// 功能验收脚本：在 jsdom 中加载生成的 HTML，执行其内嵌 JS，逐一模拟交互并断言。
// 运行：node _test_functions.js
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const BASE = __dirname;
const HTML = path.join(BASE, '浙江人才引进政策_2026.html');
const html = fs.readFileSync(HTML, 'utf-8');

const dom = new JSDOM(html, { runScripts: 'dangerously', pretendToBeVisual: true });
const { window } = dom;
const { document } = window;
// jsdom 不实现 scrollIntoView，补 stub，避免 buildCompareTable 抛错
window.HTMLElement.prototype.scrollIntoView = function () {};
window.Element.prototype.scrollIntoView = function () {};

// 等待内嵌脚本在构造期执行完（同步脚本，构造后即就绪）
const results = [];
function chk(name, ok, detail = '') {
  results.push({ name, ok: !!ok, detail });
  console.log(`[${ok ? 'PASS' : 'FAIL'}] ${name}${detail ? '  :: ' + detail : ''}`);
}

const ORDER = ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'];
const $ = (s) => document.querySelector(s);
const $$ = (s) => Array.from(document.querySelectorAll(s));

// ---------- F1 初始索引渲染 ----------
const rows0 = $$('#cityIndex .cityrow');
chk('F1 初始索引渲染(11 城)', rows0.length === 11, `rows=${rows0.length}`);

// ---------- F2 搜索仅按城市名过滤 ----------
function fireSearch(v) {
  const inp = document.getElementById('search');
  inp.value = v;
  inp.dispatchEvent(new window.Event('input', { bubbles: true }));
}
fireSearch('绍');
let r = $$('#cityIndex .cityrow');
chk('F2a 搜"绍"→仅绍兴', r.length === 1 && r[0].textContent.includes('绍兴'), `rows=${r.length}`);
fireSearch('杭州');
r = $$('#cityIndex .cityrow');
chk('F2b 搜"杭州"→仅杭州', r.length === 1 && r[0].textContent.includes('杭州'), `rows=${r.length}`);
fireSearch('xyz不存在');
r = $$('#cityIndex .cityrow');
const emptyOk = r.length === 0 && !!$('#cityIndex .empty');
chk('F2c 搜无关词→未找到匹配城市', emptyOk, `rows=${r.length}, empty=${!!$('#cityIndex .empty')}`);
fireSearch('');

// ---------- F3 点击城市 → 居中弹窗内表格 ----------
function openCity(c) {
  const row = $$('#cityIndex .cityrow').find((el) => el.textContent.includes(c));
  if (!row) return false;
  row.click();
  return true;
}
function drawerState() {
  return {
    on: $('#drawer').classList.contains('on'),
    scrim: $('#scrim').classList.contains('on'),
  };
}
// 测试杭州
openCity('杭州');
let st = drawerState();
let dt = $('#dtable').innerHTML;
let secCount = (dt.match(/class="[^"]*\bsec\b[^"]*"/g) || []).length;
let srcLinks = $$('#dtable .src a').map((a) => a.getAttribute('href'));
let allGov = srcLinks.length > 0 && srcLinks.every((u) => /https?:\/\/([^/]+)/.test(u) && u.match(/https?:\/\/([^/]+)/)[1].endsWith('.gov.cn'));
chk('F3a 杭州弹窗打开(on+scrim)', st.on && st.scrim, JSON.stringify(st));
chk('F3b 杭州弹窗含 8 维分区表格', secCount >= 8, `sec=${secCount}`);
chk('F3c 杭州表格来源链接均 *.gov.cn', allGov, `n=${srcLinks.length}`);
// 风险维度（绍兴有 risk 条目）→ 红色样式
openCity('绍兴');
dt = $('#dtable').innerHTML;
let hasRiskRow = /class="[^"]*\brisk\b[^"]*"/.test(dt);
chk('F3d 绍兴弹窗含风险红框行', hasRiskRow);
// 关闭
$('#dclose').click();
chk('F3e 关闭按钮收回弹窗', !drawerState().on);

// ---------- F7 主视觉图映射（pinyin + 杭州特例）----------
openCity('宁波');
let heroImg = $('#dhero img');
chk('F7a 宁波主视觉=images/ningbo.png', heroImg && heroImg.getAttribute('src') === 'images/ningbo.png', heroImg && heroImg.getAttribute('src'));
$('#dclose').click();
openCity('杭州');
heroImg = $('#dhero img');
const hangzhouOk = heroImg && (heroImg.getAttribute('src') === 'images/hangzhou.png' || heroImg.getAttribute('src') === 'images/hangzhou_ai.png');
chk('F7b 杭州主视觉=hangzhou.png(含 onerror 回退)', hangzhouOk, heroImg && heroImg.getAttribute('src'));
$('#dclose').click();

// ---------- F5 对比选择：2–5 城 + >5 禁用 ----------
document.getElementById('compareBtn').click();
chk('F5a 对比面板打开', $('#cmp').classList.contains('on'));
function clickChip(c) {
  const chip = $$('#cmpChips .chip').find((el) => el.textContent.trim() === c);
  if (chip) chip.click();
}
// 选 2 城
clickChip('杭州'); clickChip('宁波');
chk('F5b 选2城→生成按钮可用', !document.getElementById('genCmp').disabled);
// 再选到 6 城
['温州', '嘉兴', '湖州', '绍兴'].forEach(clickChip);
const genDisabled = document.getElementById('genCmp').disabled;
const warnTxt = document.getElementById('cmpWarn').textContent;
chk('F5c 选6城→生成按钮禁用+超量提醒', genDisabled && /最多对比 5/.test(warnTxt), `disabled=${genDisabled}, warn="${warnTxt}"`);
// 取消到 5 城
clickChip('绍兴'); // 取消绍兴 → 回到 5
chk('F5d 回到5城→按钮恢复可用', !document.getElementById('genCmp').disabled);

// ---------- F6 生成对比表 + 最高补贴金色高亮 ----------
// 选含冠军城市：衢州(grad 115万) 与 宁波(talent 2000万)
const sel = ['杭州', '宁波', '衢州'];
// 重置选择
document.getElementById('cmpClose').click();
document.getElementById('compareBtn').click();
sel.forEach(clickChip);
document.getElementById('genCmp').click();
const ctableRows = $('#ctable').querySelectorAll('tr').length;
chk('F6a 对比表已生成(≥8行:1表头+8维)', ctableRows >= 8, `rows=${ctableRows}`);
// 更精确：解析 SCORES 逻辑
// 直接取 DOM：找出"毕业生补贴"维度行，检查 max-cell 所在列的表头城市
function cellCityOfMaxRow(dimLabel) {
  const rows = $$('#ctable tbody tr');
  for (const tr of rows) {
    const th = tr.querySelector('th');
    if (th && th.textContent.trim() === dimLabel) {
      const tds = Array.from(tr.querySelectorAll('td'));
      const maxTd = tds.find((td) => td.classList.contains('max-cell'));
      if (!maxTd) return null;
      const idx = tds.indexOf(maxTd);
      const headTh = $$('#ctable thead th')[idx + 1]; // +1 跳过首列空 th
      return headTh ? headTh.textContent.trim() : null;
    }
  }
  return undefined;
}
const gradMaxCity = cellCityOfMaxRow('毕业生补贴');
const talentMaxCity = cellCityOfMaxRow('高层次人才');
chk('F6b 毕业生补贴高亮=衢州(115万冠军)', gradMaxCity === '衢州', `highlighted=${gradMaxCity}`);
chk('F6c 高层次人才高亮=宁波(2000万冠军)', talentMaxCity === '宁波', `highlighted=${talentMaxCity}`);
// 风险行不参与高亮（无 max-cell）
const riskRow = $$('#ctable tbody tr').find((tr) => tr.querySelector('th') && tr.querySelector('th').textContent.trim() === '风险提示');
const riskHasMax = riskRow && riskRow.querySelector('td.max-cell');
chk('F6d 风险行不参与最高补贴高亮', !riskHasMax);

// ---------- F8 全局来源合规（DOM 内所有 a[href^=http]）----------
const allAhrefs = $$('a[href^="http"]').map((a) => a.getAttribute('href'));
const bad = allAhrefs.filter((u) => !/https?:\/\/([^/]+)/.test(u) || !u.match(/https?:\/\/([^/]+)/)[1].endsWith('.gov.cn'));
chk('F8 全页 a[href^=http] 均为 *.gov.cn', bad.length === 0, `total=${allAhrefs.length}, bad=${bad.length}`);

// ---------- 汇总 ----------
const failed = results.filter((r) => !r.ok);
console.log('\n==== 功能验收汇总 ====');
console.log(`总计 ${results.length} 项，PASS ${results.length - failed.length}，FAIL ${failed.length}`);
console.log(failed.length ? 'RESULT: HAS FAIL ❌' : 'RESULT: ALL PASS ✅');
process.exit(failed.length ? 1 : 0);
