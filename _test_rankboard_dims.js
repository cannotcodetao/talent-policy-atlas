// Phase 31 验证：总榜移到页面最前 + 统计维度多选筛选（与对比区 rankSel 联动共用）
const fs=require('fs');
const {JSDOM}=require('jsdom');
const html=fs.readFileSync('人才引进政策_2026.html','utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true});
const w=dom.window, d=w.document;
let pass=0,fail=0;
function ok(n,c,extra){ if(c){pass++;console.log('  [PASS] '+n);} else {fail++;console.log('  [FAIL] '+n+(extra?'  '+extra:''));} }
function click(el){ el.dispatchEvent(new w.MouseEvent('click',{bubbles:true})); }

// T1 总榜位于省份Tab之前（页面最前）
const board=d.getElementById('rankBoard'), tabs=d.getElementById('provTabs');
ok('T1 总榜在省份Tab之前(页面最前)', !!(board && tabs && board.nextElementSibling===tabs || (board.compareDocumentPosition(tabs)&w.Node.DOCUMENT_POSITION_FOLLOWING)), '');
// T1b 总榜在 header 之后
const mast=d.querySelector('header.masthead');
ok('T1b 总榜在 masthead 之后', !!(mast && (mast.compareDocumentPosition(board)&w.Node.DOCUMENT_POSITION_FOLLOWING)));
// T2 简介段落移到页面最后（footer 之前）
const lede=d.querySelector('p.lede'), footer=d.querySelector('footer.global');
ok('T2 简介在 footer 之前', !!(lede && footer && (lede.compareDocumentPosition(footer)&w.Node.DOCUMENT_POSITION_FOLLOWING)));
const cityIndex=d.getElementById('cityIndex');
ok('T2b 简介在城市索引之后', !!(cityIndex && (cityIndex.compareDocumentPosition(lede)&w.Node.DOCUMENT_POSITION_FOLLOWING)));
// T2c 简介文案已更新（不再出现"页面下方另设"）
ok('T2c 简介文案更新为页首总榜', lede.textContent.indexOf('页首另设 32 城力度总榜')>=0 && lede.textContent.indexOf('页面下方另设')<0);
// T3 总榜维度筛选容器存在且渲染 3 个 chips
const rbDims=d.getElementById('rbDims');
const rchips=d.getElementById('rchips');
ok('T3 #rbDims 存在', !!rbDims);
const rbChips=rbDims.querySelectorAll('.rchip');
ok('T3b #rbDims 渲染 3 个维度 chips', rbChips.length===3, '实际 '+rbChips.length);
// T4 默认 3 个 chips 全部选中
ok('T4 默认全部选中', Array.from(rbChips).every(c=>c.classList.contains('on')));
// T5 总榜标题默认含三维名称
const head0=board.querySelector('.rb-head').textContent;
ok('T5 总榜标题含三维', head0.indexOf('毕业生补贴 + 租房补贴 + 购房补贴/房票')>=0, head0);
// T6 点击 #rbDims 第1个 chip（取消毕业生补贴）→ 总榜标题更新 + #rchips 同步
click(rbChips[0]);
const head1=board.querySelector('.rb-head').textContent;
ok('T6a 取消毕业生补贴后总榜标题更新', head1.indexOf('毕业生补贴')<0 && head1.indexOf('租房补贴 + 购房补贴/房票')>=0, head1);
const rcAfter=Array.from(rchips.querySelectorAll('.rchip')).map(c=>c.classList.contains('on'));
ok('T6b 对比区 #rchips 状态同步(off,on,on)', JSON.stringify(rcAfter)===JSON.stringify([false,true,true]), JSON.stringify(rcAfter));
// T7 点击 #rchips 的 chip → #rbDims 同步
click(rchips.querySelectorAll('.rchip')[1]); // 取消租房补贴 → 只剩购房
const rbAfter=Array.from(rbDims.querySelectorAll('.rchip')).map(c=>c.classList.contains('on'));
ok('T7 对比区点击后 #rbDims 同步(off,off,on)', JSON.stringify(rbAfter)===JSON.stringify([false,false,true]), JSON.stringify(rbAfter));
ok('T7b 总榜标题=单维', board.querySelector('.rb-head').textContent.indexOf('购房补贴/房票')>=0 && board.querySelector('.rb-head').textContent.indexOf('租房')<0);
// T8 全部取消 → 至少保留 1 个维度
click(rchips.querySelectorAll('.rchip')[2]); // 取消最后一个
const rbFinal=Array.from(rbDims.querySelectorAll('.rchip')).map(c=>c.classList.contains('on'));
ok('T8 全取消后至少保留1维', rbFinal.filter(Boolean).length===1, JSON.stringify(rbFinal));
// T9 总榜城市点击仍打开抽屉
const btns=board.querySelectorAll('button.rbcity[data-city]');
ok('T9a 总榜32城可点击', btns.length===32, '实际 '+btns.length);
click(btns[0]);
ok('T9b 点击城市打开抽屉', d.getElementById('drawer').classList.contains('on'));
console.log('\n结果: '+pass+' PASS / '+fail+' FAIL');
process.exit(fail?1:0);
