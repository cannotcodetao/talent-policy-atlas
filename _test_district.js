// Phase 38：市/区范围筛选器 + 区级政策仅查阅·不参与排名 的 jsdom 功能测试
const { JSDOM } = require('jsdom');
const fs = require('fs');

const file = '人才引进政策_2026.html';
const html = fs.readFileSync(file, 'utf-8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true });
const { window } = dom;
const doc = window.document;

const results = [];
function chk(name, cond, info = '') {
  results.push({ name, ok: !!cond, info });
  console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name}${info ? ' :: ' + info : ''}`);
}
function $(sel) { return doc.querySelector(sel); }
function $all(sel) { return [...doc.querySelectorAll(sel)]; }
function click(el) { if (el) el.dispatchEvent(new window.MouseEvent('click', { bubbles: true })); }

setTimeout(run, 600);

function openCity(name) {
  const row = $all('#cityIndex .cityrow').find(r => r.textContent.includes(name));
  click(row);
}

function run() {
  try {
    // 打开杭州抽屉（该市有 12 个区级政策）
    openCity('杭州');
    chk('D1 杭州抽屉已打开', $('#drawer').classList.contains('on'), 'on=' + $('#drawer').classList.contains('on'));

    // 市/区筛选器渲染
    const distBox = $('#drawerDist');
    const chips = $all('#drawerDist .dchip');
    chk('D2 市/区筛选器可见且有选项', distBox && distBox.style.display !== 'none' && chips.length >= 3, 'chips=' + chips.length);
    const labels = chips.map(c => c.textContent);
    chk('D3 含「全市/仅市级」及至少一个区', labels.includes('全市') && labels.includes('仅市级') && labels.some(l => l.endsWith('区')), labels.join(','));
    chk('D4 口径说明 note 存在', !!$('.dist-note') && /不计入力度排名/.test($('.dist-note').textContent), $('.dist-note') ? $('.dist-note').textContent.slice(0, 20) : 'null');

    // 默认「全市」：表格里有区级条目（带 .dist-tag）
    const tagAll = $all('#dtable .dist-tag');
    chk('D5 默认全市模式含区级标签(>=1)', tagAll.length >= 1, 'tags=' + tagAll.length);
    const distSetAll = new Set(tagAll.map(t => t.textContent));
    chk('D6 默认全市覆盖多个区', distSetAll.size >= 3, [...distSetAll].join(','));

    // 选「仅市级」：表格里应无任何 .dist-tag
    const onlyCity = chips.find(c => c.textContent === '仅市级');
    click(onlyCity);
    const tagCityOnly = $all('#dtable .dist-tag');
    chk('D7 选「仅市级」后表格无区级标签', tagCityOnly.length === 0, 'tags=' + tagCityOnly.length);

    // 选具体区「余杭区」：表格应含 市级条目(无tag) + 余杭区条目(仅余杭区tag)，不得混入其他区
    // 先记录当前 32 城总榜杭州分（筛选前），用于验证「筛选不影响排名」
    const boardRows0 = $all('#rankBoard .rbitem');
    const hzRow0 = boardRows0.find(r => r.textContent.includes('杭州'));
    const hzScore0 = hzRow0 ? hzRow0.querySelector('.rbscore').textContent : '';

    const yuHang = chips.find(c => c.textContent === '余杭区');
    chk('D8 余杭区 chip 存在', !!yuHang);
    if (yuHang) {
      click(yuHang);
      const tags = $all('#dtable .dist-tag').map(t => t.textContent);
      const hasOtherDistrict = tags.some(t => t !== '余杭区');
      // 市级条目无 tag，余杭区条目 tag=余杭区 → 全部 tag 都应为余杭区，且无其他区
      chk('D9 选余杭区后仅含余杭区标签(无其它区混入)', tags.length >= 1 && !hasOtherDistrict, tags.join(','));
      // 排名分数不应因筛选改变（筛选只影响展示；排名是 build-time 预计算）
      const boardRows = $all('#rankBoard .rbitem');
      const hzRow = boardRows.find(r => r.textContent.includes('杭州'));
      const hzScore = hzRow ? hzRow.querySelector('.rbscore').textContent : '';
      chk('D10 32城总榜杭州分与区级筛选无关(前后一致)', hzScore === hzScore0 && /万/.test(hzScore), `前=${hzScore0} 后=${hzScore}`);
    }

    // 重新打开验证筛选器可重复渲染（不开重复 note）
    // Phase 40：宁波已并入区级数据（筛选器应显示），改用永无区级的直筒子市东莞
    // （东莞属广东 → 须先切省页签，索引才会渲染东莞行）
    const gdTab = $all('#provTabs .chip').find(t => t.textContent === '广东');
    click(gdTab);
    openCity('东莞'); // 东莞不设区 → 筛选器应隐藏
    const nbDist = $('#drawerDist');
    chk('D11 无区级数据的城市(东莞)筛选器隐藏', nbDist && nbDist.style.display === 'none', 'display=' + (nbDist && nbDist.style.display));

    const pass = results.filter(r => r.ok).length;
    console.log(`\nDONE ${pass}/${results.length} PASS`);
    process.exit(pass === results.length ? 0 : 1);
  } catch (e) {
    console.error('TEST ERROR:', e);
    process.exit(2);
  }
}
