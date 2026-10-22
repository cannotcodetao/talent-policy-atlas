// 验证：32城力度总榜的城市可点击 → 打开该城详情抽屉
const fs=require('fs');
const {JSDOM}=require('jsdom');
const html=fs.readFileSync('人才引进政策_2026.html','utf8');
const dom=new JSDOM(html,{runScripts:'dangerously',pretendToBeVisual:true});
const w=dom.window, d=w.document;
let pass=0,fail=0;
function ok(n,c,extra){ if(c){pass++;console.log('  [PASS] '+n);} else {fail++;console.log('  [FAIL] '+n+(extra?'  '+extra:''));} }

// R1 总榜存在
const board=d.getElementById('rankBoard');
ok('R1 总榜容器存在', !!board);
// R2 总榜条目数 = 32
const items=board.querySelectorAll('.rbitem');
ok('R2 总榜条目数=32', items.length===32, '实际 '+items.length);
// R3 城市为 button 且带 data-city
const btns=board.querySelectorAll('button.rbcity[data-city]');
ok('R3 城市为可点击button(32)', btns.length===32, '实际 '+btns.length);
// R4 抽屉初始关闭
const drawer=d.getElementById('drawer');
ok('R4 抽屉初始关闭', !drawer.classList.contains('on'));
// R5 点击第一个总榜城市 → 抽屉打开
const firstCity=btns[0].getAttribute('data-city');
btns[0].dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
ok('R5 点击总榜城市后抽屉打开', drawer.classList.contains('on'));
// R6 抽屉标题 = 被点击城市
const title=d.getElementById('dtitle').textContent||'';
ok('R6 抽屉标题=被点击城市('+firstCity+')', title.indexOf(firstCity)>=0, '实际标题 '+title.slice(0,20));
// R7 抽屉表格有内容
const tbl=d.getElementById('dtable');
ok('R7 抽屉表格已渲染', tbl.querySelectorAll('tr').length>0, 'tr数 '+tbl.querySelectorAll('tr').length);
// R8 点击另一个城市 → 标题切换
const other=Array.from(btns).find(b=>b.getAttribute('data-city')!==firstCity);
const oc=other.getAttribute('data-city');
other.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
const t2=d.getElementById('dtitle').textContent||'';
ok('R8 点击另一城市标题切换为 '+oc, t2.indexOf(oc)>=0, '实际 '+t2.slice(0,20));
// R9 切换维度后总榜重渲染且仍可点击
const chip=d.querySelector('#rchips .rchip');
chip.dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
const btns2=d.querySelectorAll('#rankBoard button.rbcity[data-city]');
ok('R9 切维度后总榜仍可点击(32)', btns2.length===32, '实际 '+btns2.length);
btns2[1].dispatchEvent(new w.MouseEvent('click',{bubbles:true}));
ok('R10 重渲染后点击仍能打开抽屉', drawer.classList.contains('on'));
console.log('\n结果: '+pass+' PASS / '+fail+' FAIL');
process.exit(fail?1:0);
