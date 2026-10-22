const fs = require('fs');
const html = fs.readFileSync('人才引进政策_2026.html', 'utf8');
const m = html.match(/const RANK_SCORES = ([\s\S]*?);/);
const RANK_SCORES = JSON.parse(m[1]);

// 复刻 HTML 内的排名逻辑（cityRankScore / rankMap）
let rankSel = new Set(['grad_subsidy','anju_subsidy','welfare','startup']); // 默认全选
function allCities(){
  const meta = JSON.parse(html.match(/const META = ([\s\S]*?);/)[1]);
  const out=[]; meta.provinces.forEach(p=>p.cities.forEach(c=>out.push(c))); return out;
}
function cityRankScore(c){ let s=0; rankSel.forEach(d=>s+=(RANK_SCORES[d]&&RANK_SCORES[d][c])||0); return s; }
function rankMap(){
  const arr=allCities().map(c=>({c,s:cityRankScore(c)})).sort((a,b)=>b.s-a.s);
  const map={}; let r=0,prev=null;
  arr.forEach((o,i)=>{ if(o.s!==prev){r=i+1;prev=o.s;} map[o.c]=r; }); return map;
}

function show(label){
  const rm=rankMap();
  const ranked=allCities().map(c=>({c,sc:cityRankScore(c),r:rm[c]})).sort((a,b)=>b.sc-a.sc).slice(0,5);
  console.log(`\n[${label}] 选中=${[...rankSel].join('+')}`);
  ranked.forEach(x=>console.log(`  第${x.r}  ${x.c}  ${x.sc}万`));
}

// 默认：全选 -> 总额
show('默认(总额)');
// 仅 配套保障(租房)
rankSel=new Set(['welfare']); show('仅租房');
// 仅 毕业生补贴
rankSel=new Set(['grad_subsidy']); show('仅毕业生补贴');
// 仅 创业扶持
rankSel=new Set(['startup']); show('仅创业扶持');
// 购房+租房
rankSel=new Set(['anju_subsidy','welfare']); show('购房+租房');

// 断言：租房单维 深圳应排第1
rankSel=new Set(['welfare']);
const rm=rankMap();
console.log('\n断言 租房单维: 深圳='+rm['深圳']+', 佛山='+rm['佛山']+', 东莞='+rm['东莞']);
console.log('  预期 深圳<佛山<东莞 (数值1.5>1.2>0.6) ->', rm['深圳']<rm['佛山'] && rm['佛山']<rm['东莞'] ? 'PASS' : 'FAIL');
// 断言：创业单维 湛江不应为1000相关异常（湛江=5.2）
rankSel=new Set(['startup']);
console.log('断言 创业单维: 湛江='+cityRankScore('湛江')+'万 (预期5.2, 非1000) ->', Math.abs(cityRankScore('湛江')-5.2)<1e-6?'PASS':'FAIL');
