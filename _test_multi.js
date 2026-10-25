// 多省合并页 jsdom 功能测试（系统 Node 26 + jsdom）
const { JSDOM } = require('jsdom');
const fs = require('fs');
const path = require('path');

const file = '人才引进政策_2026.html';
const html = fs.readFileSync(file, 'utf-8');
const dom = new JSDOM(html, { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true });
const { window } = dom;
const doc = window.document;

const results = [];
function chk(name, cond, info='') {
  results.push({ name, ok: !!cond, info });
  console.log(`[${cond ? 'PASS' : 'FAIL'}] ${name}${info ? ' :: ' + info : ''}`);
}

function $(sel){ return doc.querySelector(sel); }
function $all(sel){ return [...doc.querySelectorAll(sel)]; }
function click(el){ if(el) el.dispatchEvent(new window.MouseEvent('click', {bubbles:true})); }

setTimeout(run, 500);

function run(){
  try {
    // 省份标签
    const tabs = $all('#provTabs .chip');
    chk('M1 省份标签渲染 2 个', tabs.length === 2, 'tabs=' + tabs.length);
    chk('M2 默认激活浙江', tabs[0] && tabs[0].textContent === '浙江', tabs[0] && tabs[0].textContent);

    // 默认索引 = 浙江 11 城
    let rows = $all('#cityIndex .cityrow');
    chk('M3 默认索引浙江 11 城', rows.length === 11, 'rows=' + rows.length);

    // 切换广东（Phase 27 后 32 城全量合并：浙江 11 + 广东 21）
    const gd = tabs.find(t => t.textContent === '广东');
    click(gd);
    rows = $all('#cityIndex .cityrow');
    chk('M4 切换广东后索引 21 城', rows.length === 21, 'rows=' + rows.length);
    // M5 规格变更（2026-10-25）：页眉副标题 #subline 与 kicker 已按用户要求移除。
    // 原断言是「副标题含广东」，现改为「副标题确实不存在 + setSub 调用不抛错」。
    // 注意：切换省份仍会调用 setSub()（空实现），这里已在上一步 click(gd) 中覆盖到。
    chk('M5 页眉副标题已移除', $('#subline') === null, '#subline 存在=' + ($('#subline') !== null));

    // 打开广州抽屉，实际有数据的维度（占位维度已隐藏；数据清理后 10 个）
    const gz = $all('#cityIndex .cityrow').find(r => r.textContent.includes('广州'));
    click(gz);
    const secs = $all('#dtable .sec');
    chk('M6 广州抽屉实际维度 10~12', secs.length >= 10 && secs.length <= 12, 'secs=' + secs.length);
    const labels = secs.map(s => s.textContent);
    const anjuValid=['先租后售人才房','定向优惠价购房','人才购房补贴/房票','企业内部福利房'];
    const anjuFound=labels.filter(t=>anjuValid.some(v=>t.includes(v)));
    chk('M7 安居维度均为有效标签(无共有产权房)',
      anjuFound.length>0 && anjuFound.every(t=>anjuValid.some(v=>t.includes(v))) && !labels.some(t=>t.includes('共有产权房')),
      labels.join('|'));

    // 去图：抽屉无图片/占位图
    chk('M8 抽屉无图片与占位图', !$('#dhero') && $all('#drawer img').length === 0, 'dhero=' + !!$('#dhero'));
    // 学历筛选控件（Phase 27 改为 .echip 按钮）
    const eduBtns = $all('#eduFilter .echip');
    chk('M9 学历筛选控件 5 按钮', eduBtns.length === 5, 'btns=' + eduBtns.length);

    // 关闭抽屉
    click($('#dclose'));

    // 跨省对比：对比弹窗显示全部 32 城（按省分组），不限于当前激活省
    click($('#compareBtn'));
    const provGrps = $all('#cmpChips .cmp-prov');
    const allChips = $all('#cmpChips .chip');
    chk('M10 对比弹窗按省分组(2)·共32城', provGrps.length === 2 && allChips.length === 32, 'groups=' + provGrps.length + ' chips=' + allChips.length);
    // 跨省混选：杭州(浙) + 广州(粤)
    click(allChips.find(c => c.textContent === '杭州'));
    click(allChips.find(c => c.textContent === '广州'));
    const genBtn = $('#genCmp');
    chk('M11 跨省选2城生成按钮可用', genBtn.disabled === false, 'disabled=' + genBtn.disabled);
    click(genBtn);
    const crows = $all('#ctable tbody tr');
    // Phase 37：维度 11→12，额外还有 renderRankRow 插入的力度排名行 → 总 13 行
    chk('M12 跨省对比表 12 维行 + 1 排名行', crows.length === 13, 'rows=' + crows.length);
    // 表头跨省标签
    const ths = $all('#ctable thead th');
    const hzTh = ths.find(t => t.textContent.includes('杭州'));
    const gzTh = ths.find(t => t.textContent.includes('广州'));
    chk('M13 表头跨省标签(杭=浙/穗=粤)', hzTh && /浙江/.test(hzTh.textContent) && gzTh && /广东/.test(gzTh.textContent), '杭=' + (hzTh && hzTh.textContent) + ' 穗=' + (gzTh && gzTh.textContent));

    // 来源合规：全页 a[href^=http] 均 *.gov.cn
    const links = $all('a[href^="http"]');
    const bad = links.filter(a => {
      const u = a.href; const m = u.match(/https?:\/\/([^/]+)/); return m && !m[1].endsWith('.gov.cn');
    });
    chk('M14 全页外链均 *.gov.cn', bad.length === 0, `total=${links.length} bad=${bad.length}`);

    // 切回浙江，验证抽屉仍是浙江城市
    const zj = $all('#provTabs .chip').find(t => t.textContent === '浙江');
    click(zj);
    rows = $all('#cityIndex .cityrow');
    chk('M15 切回浙江索引 11 城', rows.length === 11, 'rows=' + rows.length);
    const hz = rows.find(r => r.textContent.includes('杭州'));
    click(hz);
    const secs2 = $all('#dtable .sec');
    chk('M16 杭州抽屉实际维度 10~12', secs2.length >= 10 && secs2.length <= 12, 'secs=' + secs2.length);

    // Phase 41b 双口径：页首学历行(#eduFilter)→总榜口径 boardEdu 默认本科；抽屉(#drawerEdu)/对比(#cmpEdu)→表格过滤 eduFilter 默认全部
    const eduBtns2 = $all('#eduFilter .echip');
    const bk = eduBtns2.find(b => b.textContent === '本科');
    const all0 = eduBtns2.find(b => b.textContent === '全部');
    chk('M17 页首学历行默认本科选中(总榜口径)', bk.classList.contains('on') && !all0.classList.contains('on'), 'bk=' + bk.classList.contains('on') + ' all=' + all0.classList.contains('on'));
    // 评分语义：全部档 ≡ 本科档（Phase 29：无本科档不向下兜底）→ 两者总榜一致是正确行为
    const boardBenke = doc.getElementById('rankBoard').textContent;
    click(all0);
    const boardAll = doc.getElementById('rankBoard').textContent;
    chk('M17b 页首学历行全部≡本科(总榜一致)', boardBenke === boardAll, '一致=' + (boardBenke === boardAll));
    const mast = eduBtns2.find(b => b.textContent === '硕士');
    click(mast);
    const boardMaster = doc.getElementById('rankBoard').textContent;
    chk('M17b2 页首学历行切硕士→总榜口径变化', boardMaster !== boardAll, '变化=' + (boardMaster !== boardAll));
    click(bk); // 恢复默认本科
    // 抽屉学历行：默认全部（各档都有），点本科后仅本科档，且不影响总榜口径
    const deBtns = $all('#drawerEdu .echip');
    const deBenke = deBtns.find(b => b.textContent === '本科');
    const deAll = deBtns.find(b => b.textContent === '全部');
    chk('M17c 抽屉学历行默认全部选中', deAll.classList.contains('on') && !deBenke.classList.contains('on'), 'all=' + deAll.classList.contains('on'));
    const boardBefore = doc.querySelector('#rankBoard .rbitem .rbscore').textContent;
    click(deBenke);
    const boardAfter = doc.querySelector('#rankBoard .rbitem .rbscore').textContent;
    chk('M17d 抽屉学历切换不改变总榜口径', boardBefore === boardAfter, '前=' + boardBefore + ' 后=' + boardAfter);
    const hz2 = $all('#cityIndex .cityrow').find(r => r.textContent.includes('杭州'));
    click(hz2);
    const secs3 = $all('#dtable .sec');
    const rows3 = $all('#dtable tbody tr');
    let cap = false, gsItems = [];
    for (const r of rows3) {
      if (r.classList.contains('sec')) { if (cap) break; if (r.textContent.startsWith('一、毕业生补贴')) cap = true; continue; }
      if (cap) gsItems.push(r);
    }
    chk('M18 抽屉学历切本科后毕业生补贴仅本科档', gsItems.length > 0 && gsItems.every(r => /本科/.test(r.textContent)), 'n=' + gsItems.length);

    const pass = results.filter(r => r.ok).length;
    console.log(`\nDONE ${pass}/${results.length} PASS`);
    window.close();
    process.exit(pass === results.length ? 0 : 1);
  } catch (e) {
    console.log('EXCEPTION', e && e.message);
    process.exit(2);
  }
}
