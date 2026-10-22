# -*- coding: utf-8 -*-
"""Build a light fashion-magazine style slideshow (16:9) from zhejiang-talent-data.json.
Style D: warm ivory ground + ink black + vermilion hairline + serif display.
Non-infringing: original masthead, system fonts only, image placeholders only.
"""
import json, os, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "zhejiang-talent-data.json")
OUT = os.path.join(BASE, "浙江人才引进政策_幻灯片_2026.html")

d = json.load(open(DATA, encoding="utf-8"))
ORDER = d["meta"]["citiesDone"]
META = {"citiesDone": ORDER, "updated": d["meta"].get("updated", "")}

DIMLAB = {
    "grad_subsidy": "毕业生补贴", "talent_highlevel": "高层次人才", "hukou": "落户",
    "startup": "创业扶持", "welfare": "配套保障", "timing": "时效提醒",
    "risk": "风险提示", "apply_path": "申报路径",
}
DIMORDER = ["grad_subsidy", "talent_highlevel", "hukou", "startup",
            "welfare", "timing", "risk", "apply_path"]


def clean(v):
    s = ("" if v is None else str(v)).strip()
    return "" if s in ("—", "-", "无", "None", "") else s


def fmt_item(dim, it):
    if dim == "grad_subsidy":
        lvl = clean(it.get("level"))
        cash = clean(it.get("cash"))
        hv = clean(it.get("house_voucher"))
        t = f"{lvl}：{cash}" if lvl else cash
        if hv and hv not in cash:
            t += f"｜房票 {hv}"
        return t
    if dim == "talent_highlevel":
        return f"{clean(it.get('class'))}：{clean(it.get('subsidy'))}"
    if dim == "hukou":
        return f"{clean(it.get('target'))}：{clean(it.get('rule'))}"
    if dim in ("startup", "welfare"):
        return f"{clean(it.get('type'))}：{clean(it.get('detail'))}"
    if dim in ("timing", "risk"):
        det = clean(it.get("item")) + ("：" if clean(it.get("item")) else "") + clean(it.get("detail"))
        return det.strip("：")
    if dim == "apply_path":
        p = [f"平台 {clean(it.get('platform'))}", clean(it.get("process")),
             f"咨询 {clean(it.get('phone'))}"]
        return "｜".join(x for x in p if x)
    return ""


# ---- per-city SUMMARY ----
SUMMARY = {}
for c in ORDER:
    dm = d[c]["dimensions"]
    entry = {}
    sources = []
    seen = set()
    for dim in DIMORDER:
        its = dm.get(dim, {}).get("items", [])
        lines = [fmt_item(dim, it) for it in its]
        lines = [x for x in lines if x]
        entry[dim] = lines
        for it in its:
            src = it.get("source") or {}
            u = clean(src.get("url"))
            if u and u not in seen:
                seen.add(u)
                sources.append({"unit": clean(src.get("unit")), "url": u})
    SUMMARY[c] = {"lines": entry, "sources": sources}


# ---- overview lead + compare matrix ----
def find_grad(city, kw):
    for it in d[city]["dimensions"]["grad_subsidy"]["items"]:
        if kw in clean(it.get("level")):
            return it
    return None


def cell_text(it):
    if not it:
        return "—"
    cash = clean(it.get("cash"))
    hv = clean(it.get("house_voucher"))
    if hv and hv not in cash:
        return f"{cash}｜房票{hv}"
    return cash or "—"


COMPARE = {}
for c in ORDER:
    g = d[c]["dimensions"]["grad_subsidy"]["items"]
    zhuan = find_grad(c, "专")
    ben = find_grad(c, "本")
    shuo = find_grad(c, "硕")
    bo = find_grad(c, "博")
    # house voucher (prefer 博士 then 硕士)
    house_it = bo or shuo or ben
    house = clean(house_it.get("house_voucher")) if house_it else ""
    hukou_items = d[c]["dimensions"]["hukou"]["items"]
    hukou = clean(hukou_items[0].get("rule")) if hukou_items else ""
    COMPARE[c] = {
        "zhuan": cell_text(zhuan),
        "ben": cell_text(ben),
        "shuo": cell_text(shuo),
        "bo": cell_text(bo),
        "house": house or "—",
        "hukou": hukou or "—",
    }

# overview lead line = 博士 or 硕士
OVERVIEW = {}
for c in ORDER:
    lead_it = find_grad(c, "博") or find_grad(c, "硕") or find_grad(c, "本")
    OVERVIEW[c] = cell_text(lead_it)

DATA_JSON = json.dumps(d, ensure_ascii=False)
SUM_JSON = json.dumps(SUMMARY, ensure_ascii=False)
CMP_JSON = json.dumps(COMPARE, ensure_ascii=False)
OVW_JSON = json.dumps(OVERVIEW, ensure_ascii=False)
META_JSON = json.dumps(META, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>浙江省人才引进政策 · 2026 特刊</title>
<style>
:root{
  --ivory:#f5f1e8; --ivory2:#efe8d8; --paper:#faf7f0;
  --ink:#1a1612; --ink2:#5a5148; --mut:#8a8073;
  --vermilion:#b23a2e; --gold:#9a7b3f; --line:#d9cfba;
  --serif:"Songti SC","STSong","Noto Serif SC",Georgia,"Times New Roman",serif;
  --sans:"PingFang SC","Microsoft YaHei","Helvetica Neue",Arial,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{
  background:#231f1a;color:var(--ink);
  font-family:var(--sans);
  display:flex;align-items:center;justify-content:center;
  overflow:hidden;
}
.reader{position:relative;width:100vw;height:100vh;
  display:flex;flex-direction:column;align-items:center;justify-content:center;}
.stage{
  position:relative;width:min(94vw,calc(94vh*16/9));height:min(94vh,calc(94vw*9/16));
  background:var(--ivory);
  box-shadow:0 30px 80px rgba(0,0,0,.55);
  overflow:hidden;
  background-image:
    radial-gradient(circle at 18% 12%,rgba(154,123,63,.06),transparent 40%),
    radial-gradient(circle at 85% 88%,rgba(178,58,46,.05),transparent 45%);
}
.slide{position:absolute;inset:0;padding:5.2% 6%;
  display:flex;flex-direction:column;opacity:0;visibility:hidden;
  transition:opacity .55s ease;overflow:hidden;}
.slide.on{opacity:1;visibility:visible;z-index:2}
.slide.on.prev{opacity:0}

/* masthead */
.mast{display:flex;align-items:baseline;justify-content:center;gap:.8em;
  font-family:var(--serif);letter-spacing:.5em;text-indent:.5em;
  font-size:clamp(13px,1.9vh,22px);font-weight:700;color:var(--ink);}
.mast .en{font-size:.5em;letter-spacing:.32em;color:var(--mut);font-weight:400}
.rule{height:1px;background:var(--vermilion);width:54px;margin:1.1vh auto 0;opacity:.85}
.rule.l{margin-left:0}
.kicker{font-family:var(--serif);letter-spacing:.42em;color:var(--vermilion);
  font-size:clamp(10px,1.5vh,15px);text-transform:uppercase;}

/* cover */
.cover{justify-content:center}
.cover .mastwrap{text-align:center;margin-bottom:3vh}
.cover .bigtitle{font-family:var(--serif);font-weight:700;
  font-size:clamp(34px,7.4vh,86px);line-height:1.04;color:var(--ink);
  letter-spacing:.04em;margin:2.4vh 0 1.2vh;}
.cover .subtitle{font-family:var(--serif);font-size:clamp(14px,2.5vh,26px);
  color:var(--ink2);letter-spacing:.18em;}
.cover .bodyrow{display:flex;gap:4%;margin-top:3.4vh;align-items:stretch}
.cover .lede{flex:1;font-family:var(--serif);font-size:clamp(12px,1.9vh,19px);
  line-height:1.85;color:var(--ink2);border-left:2px solid var(--vermilion);
  padding-left:3%;}
.cover .fig{flex:0 0 30%;min-width:140px}
.figbox{width:100%;height:100%;min-height:170px;border:1px dashed var(--gold);
  background:repeating-linear-gradient(45deg,#faf7f0,#faf7f0 10px,#f1ead9 10px,#f1ead9 20px);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  color:var(--mut);font-family:var(--serif);text-align:center;padding:10px}
.figbox .tag{font-size:clamp(11px,1.7vh,16px);letter-spacing:.2em;color:var(--gold)}
.figbox .cap{font-size:clamp(9px,1.3vh,12px);margin-top:.6em;line-height:1.5;color:var(--mut)}
.cover .foot{margin-top:3.4vh;font-size:clamp(9px,1.35vh,13px);color:var(--mut);
  letter-spacing:.12em;display:flex;justify-content:space-between;border-top:1px solid var(--line);padding-top:1.4vh}

/* generic section title */
.sectitle{font-family:var(--serif);font-weight:700;
  font-size:clamp(22px,4.2vh,46px);color:var(--ink);letter-spacing:.03em;margin-top:1.4vh}
.secsub{font-family:var(--serif);color:var(--ink2);font-size:clamp(12px,1.9vh,18px);
  margin-top:.8vh;letter-spacing:.06em}

/* about */
.about .cols{display:flex;gap:5%;margin-top:3vh;flex:1}
.about .col{flex:1}
.about p{font-family:var(--serif);font-size:clamp(11px,1.7vh,17px);line-height:1.9;
  color:var(--ink2);margin-bottom:1.4vh}
.about .note{border-left:2px solid var(--vermilion);padding-left:2.4%;color:var(--ink)}
.about .small{font-size:clamp(10px,1.4vh,13px);color:var(--mut);letter-spacing:.06em}

/* contents */
.toc{display:grid;grid-template-columns:1fr 1fr;gap:.4vh 6%;margin-top:2.6vh;flex:1;
  align-content:start}
.toc .it{display:flex;align-items:baseline;gap:.8em;padding:1.1vh 0;border-bottom:1px solid var(--line)}
.toc .num{font-family:var(--serif);color:var(--vermilion);font-size:clamp(13px,2vh,20px);min-width:2.2em}
.toc .nm{font-family:var(--serif);font-size:clamp(13px,2.1vh,21px);color:var(--ink)}
.toc .en{margin-left:auto;font-size:clamp(9px,1.3vh,12px);color:var(--mut);letter-spacing:.12em}

/* framework */
.fw{display:grid;grid-template-columns:repeat(4,1fr);gap:2.2% 3%;margin-top:3vh;flex:1;align-content:start}
.fw .card{border:1px solid var(--line);padding:2vh 1.6vh;background:var(--paper)}
.fw .card .n{font-family:var(--serif);color:var(--vermilion);font-size:clamp(14px,2.2vh,22px)}
.fw .card .t{font-family:var(--serif);font-size:clamp(13px,2vh,19px);color:var(--ink);margin:.6vh 0}
.fw .card .d{font-size:clamp(9px,1.35vh,12.5px);color:var(--ink2);line-height:1.7}

/* overview */
.ov{display:grid;grid-template-columns:repeat(4,1fr);gap:2% 2.4%;margin-top:2.8vh;flex:1;align-content:start}
.ov .city{border-top:2px solid var(--ink);padding-top:1vh}
.ov .city .cn{font-family:var(--serif);font-size:clamp(14px,2.2vh,22px);color:var(--ink)}
.ov .city .lead{font-size:clamp(9px,1.35vh,13px);color:var(--ink2);margin-top:.7vh;line-height:1.6;min-height:3.4em}
.ov .city .pin{font-size:clamp(8px,1.2vh,11px);color:var(--vermilion);margin-top:.5vh;letter-spacing:.08em}

/* city */
.city .top{display:flex;align-items:flex-end;justify-content:space-between;border-bottom:2px solid var(--ink);padding-bottom:1vh}
.city .top .cn{font-family:var(--serif);font-weight:700;font-size:clamp(26px,5vh,56px);color:var(--ink);letter-spacing:.05em}
.city .top .en{font-family:var(--serif);color:var(--mut);letter-spacing:.3em;font-size:clamp(11px,1.7vh,17px)}
.city .lead{font-family:var(--serif);color:var(--vermilion);font-size:clamp(12px,1.9vh,18px);margin-top:1.2vh;letter-spacing:.04em}
.city .grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2vh 4%;margin-top:1.6vh;flex:1;align-content:start}
.city .dim{border-left:1px solid var(--line);padding-left:1.6%}
.city .dim .h{font-family:var(--serif);color:var(--ink);font-size:clamp(11px,1.7vh,16px);letter-spacing:.06em}
.city .dim .h::before{content:"·";color:var(--vermilion);margin-right:.4em}
.city .dim ul{list-style:none;margin-top:.5vh}
.city .dim li{font-size:clamp(9px,1.32vh,12.5px);color:var(--ink2);line-height:1.65;padding-left:1em;text-indent:-1em}
.city .dim.risk .h{color:var(--vermilion)}
.city .src{font-size:clamp(8px,1.2vh,11px);color:var(--mut);margin-top:1vh;letter-spacing:.04em;
  border-top:1px dashed var(--line);padding-top:.8vh;line-height:1.5}
.city .fig{position:absolute;right:6%;top:14%;width:22%;height:30%;max-width:200px}

/* compare */
.cmp{margin-top:2.4vh;flex:1;overflow:auto}
.cmp table{width:100%;border-collapse:collapse;font-size:clamp(9px,1.4vh,13px)}
.cmp th,.cmp td{border-bottom:1px solid var(--line);padding:.9vh .6vw;text-align:left;vertical-align:top}
.cmp th{font-family:var(--serif);color:var(--ink);letter-spacing:.06em;
  border-bottom:2px solid var(--ink);position:sticky;top:0;background:var(--ivory)}
.cmp td:first-child,.cmp th:first-child{font-family:var(--serif);color:var(--vermilion);font-weight:700;white-space:nowrap}
.cmp tr:hover td{background:var(--paper)}

/* risk */
.risk .list{display:flex;flex-direction:column;gap:1.4vh;margin-top:2.6vh;flex:1;justify-content:center}
.risk .row{display:flex;gap:2%;border-left:3px solid var(--vermilion);background:var(--paper);padding:1.4vh 2%}
.risk .row .c{font-family:var(--serif);color:var(--vermilion);font-size:clamp(13px,2vh,20px);min-width:3.4em}
.risk .row .t{font-size:clamp(10px,1.5vh,14px);color:var(--ink2);line-height:1.7}

/* closing */
.closing{justify-content:center;text-align:center}
.closing .big{font-family:var(--serif);font-weight:700;font-size:clamp(28px,5.6vh,62px);color:var(--ink);letter-spacing:.04em;line-height:1.1}
.closing .sub{font-family:var(--serif);color:var(--ink2);font-size:clamp(13px,2.1vh,20px);margin-top:2.4vh;letter-spacing:.1em;line-height:1.8}
.closing .seal{margin:3.4vh auto 0;width:84px;height:84px;border:2px solid var(--vermilion);border-radius:50%;
  display:flex;align-items:center;justify-content:center;color:var(--vermilion);
  font-family:var(--serif);font-size:clamp(11px,1.6vh,15px);letter-spacing:.2em;line-height:1.4;text-align:center;
  transform:rotate(-6deg);opacity:.9}

/* HUD */
.hud{position:fixed;bottom:2.2vh;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:18px;z-index:50}
.hud button{width:38px;height:38px;border-radius:50%;border:1px solid #5a5148;background:#2c2722;color:#e8e0d0;
  font-size:20px;cursor:pointer;font-family:var(--serif);transition:.2s}
.hud button:hover{background:#3a342c;color:#fff}
.hud .ct{color:#cfc6b6;font-family:var(--serif);letter-spacing:.2em;font-size:14px;min-width:74px;text-align:center}
.dots{position:fixed;bottom:1vh;left:50%;transform:translateX(-50%);display:flex;gap:7px;z-index:50}
.dots .d{width:7px;height:7px;border-radius:50%;background:#5a5148;opacity:.5;cursor:pointer;transition:.2s}
.dots .d.on{background:var(--vermilion);opacity:1;transform:scale(1.25)}
.brand{position:fixed;top:1.4vh;left:2vw;color:#9a8f7e;font-family:var(--serif);letter-spacing:.3em;font-size:11px;z-index:50}
@media print{
  body{background:#fff}
  .reader,.hud,.dots,.brand{display:none!important}
  .stage{width:100vw;height:100vh;box-shadow:none}
  .slide{position:absolute;opacity:0;visibility:hidden;page-break-after:always}
  .slide.on{opacity:1;visibility:visible}
}
</style>
</head>
<body>
<div class="brand">浙才志 · ZHEJIANG TALENT REVIEW</div>
<div class="reader">
  <div class="stage" id="stage"></div>
</div>
<div class="hud">
  <button id="prev" aria-label="上一页">‹</button>
  <span class="ct" id="ct">01 / 19</span>
  <button id="next" aria-label="下一页">›</button>
</div>
<div class="dots" id="dots"></div>

<script>
const DATA = /*__DATA__*/;
const SUMMARY = /*__SUMMARY__*/;
const COMPARE = /*__COMPARE__*/;
const OVERVIEW = /*__OVERVIEW__*/;
const META = /*__META__*/;
const ORDER = META.citiesDone;
const DIMLAB = {grad_subsidy:"毕业生补贴",talent_highlevel:"高层次人才",hukou:"落户",startup:"创业扶持",welfare:"配套保障",timing:"时效提醒",risk:"风险提示",apply_path:"申报路径"};
const DIMORDER = ["grad_subsidy","talent_highlevel","hukou","startup","welfare","timing","risk","apply_path"];
const UPDATED = META.updated || "2026";

function esc(s){return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

function coverSlide(){
  return `<div class="slide cover">
    <div class="mastwrap">
      <div class="mast">浙才志 <span class="en">ZHEJIANG TALENT REVIEW</span></div>
      <div class="rule"></div>
    </div>
    <div class="bigtitle">浙江省人才引进政策</div>
    <div class="subtitle">全省十一城 · 八大维度 · 政府来源全景</div>
    <div class="bodyrow">
      <div class="lede">本刊汇编浙江省 11 个地级市现行人才引进政策，按「毕业生补贴 / 高层次人才 / 落户 / 创业 / 配套 / 时效 / 风险 / 申报」八维框架呈现。所有数据均来自市县政府及人社、住建、公安等主管部门公开文件（*.gov.cn），不含新闻转述与商业解读。</div>
      <div class="fig"><div class="figbox"><div class="tag">封面图位</div><div class="cap">建议替换：浙江地标拼贴 / 城市天际线原创摄影（1200×1600，竖版）</div></div></div>
    </div>
    <div class="foot"><span>2026 特刊 · 数据截至 ${UPDATED}</span><span>原创信息汇编 · 非任何商业期刊授权</span></div>
  </div>`;
}

function aboutSlide(){
  return `<div class="slide about">
    <div class="kicker">COLOPHON · 刊例与方法</div>
    <div class="sectitle">关于本刊</div>
    <div class="cols">
      <div class="col">
        <p class="note">本刊为原创信息汇编，刊名、版式均为独立设计，不依托、不模仿任何商业期刊品牌，亦未使用其商标或授权素材。</p>
        <p>所有政策条款均摘录自政府公开文件，文末逐条标注发布单位与原文链接，便于读者核验。金额、年限、适用对象以官方最新发布为准。</p>
        <p>本刊不构成法律或申报建议；落地前请以各市人社局、政务服务平台最新口径及个人资质认定结果为准。</p>
      </div>
      <div class="col">
        <p><b>数据范围</b><br>浙江省 11 个地级市（杭州、宁波、温州、嘉兴、湖州、绍兴、金华、衢州、舟山、台州、丽水），以市级政策为主。</p>
        <p><b>八维框架</b><br>毕业生补贴 · 高层次人才 · 落户 · 创业扶持 · 配套保障 · 时效提醒 · 风险提示 · 申报路径。</p>
        <p class="small">图片位均为占位框，须由使用者替换为原创或已授权素材后方可对外发布，以规避肖像权与著作权风险。</p>
      </div>
    </div>
  </div>`;
}

function contentsSlide(){
  const items=[["封面","COVER"],["刊例与方法","COLOPHON"],["目录","CONTENTS"],["八维框架","FRAMEWORK"],
    ["全省速览","OVERVIEW"],["十一城深度","ELEVEN CITIES"],["横向对比","COMPARE"],["风险提示","RISK"],["后记","CLOSING"]];
  let h="";
  items.forEach((it,i)=>{
    const n=String(i+1).padStart(2,"0");
    h+=`<div class="it"><span class="num">${n}</span><span class="nm">${it[0]}</span><span class="en">${it[1]}</span></div>`;
  });
  return `<div class="slide contents">
    <div class="kicker">CONTENTS · 目录</div>
    <div class="sectitle">本期目录</div>
    <div class="toc">${h}</div>
  </div>`;
}

function frameworkSlide(){
  const fw=[
    ["01","毕业生补贴","生活补贴、安家补贴、购房补贴 / 房票，按学历分层。"],
    ["02","高层次人才","A–E（或 F）类认定与对应购房 / 安家 / 租赁待遇。"],
    ["03","落户","学历、职称、技能、合法稳定就业等落户通道与门槛。"],
    ["04","创业扶持","创业担保贷款、场地、贴息、项目资助等。"],
    ["05","配套保障","人才公寓、子女入学、医疗、配偶安置等。"],
    ["06","时效提醒","政策有效期、过渡期、申报窗口与截止节点。"],
    ["07","风险提示","服务期、限售、退回、资质不符等隐性约束。"],
    ["08","申报路径","申报平台、流程、受理部门与咨询电话。"],
  ];
  let h="";
  fw.forEach(c=>{h+=`<div class="card"><div class="n">${c[0]}</div><div class="t">${c[1]}</div><div class="d">${c[2]}</div></div>`;});
  return `<div class="slide framework">
    <div class="kicker">FRAMEWORK · 八维框架</div>
    <div class="sectitle">我们如何拆解一座城市</div>
    <div class="secsub">八个维度，构成每份城市政策档案的统一坐标。</div>
    <div class="fw">${h}</div>
  </div>`;
}

function overviewSlide(){
  let h="";
  ORDER.forEach(c=>{
    const lead=OVERVIEW[c]||"—";
    const pins = SUMMARY[c].sources.length;
    h+=`<div class="city"><div class="cn">${c}</div><div class="lead">${esc(lead)}</div><div class="pin">${pins} 条政府来源</div></div>`;
  });
  return `<div class="slide overview">
    <div class="kicker">OVERVIEW · 全省速览</div>
    <div class="sectitle">十一城，一瞥</div>
    <div class="secsub">各城最高学历档（博士 / 硕士）补贴摘要与来源条数。</div>
    <div class="ov">${h}</div>
  </div>`;
}

function citySlide(c){
  const s=SUMMARY[c];
  let dims="";
  DIMORDER.forEach(dim=>{
    const ls=s.lines[dim];
    if(!ls.length) return;
    const cls = dim==="risk" ? "dim risk":"dim";
    let ul="";
    ls.slice(0,4).forEach(t=>{ul+=`<li>${esc(t)}</li>`;});
    if(ls.length>4) ul+=`<li class="more">…共 ${ls.length} 条</li>`;
    dims+=`<div class="${cls}"><div class="h">${DIMLAB[dim]}</div><ul>${ul}</ul></div>`;
  });
  let src="";
  s.sources.slice(0,3).forEach(x=>{src+=`${esc(x.unit)}　`;});
  if(s.sources.length>3) src+=`等 ${s.sources.length} 个政府来源`;
  return `<div class="slide city">
    <div class="top"><div class="cn">${c}</div><div class="en">${c.toUpperCase()}</div></div>
    <div class="lead">${esc(s.lines.grad_subsidy[0]||"")}</div>
    <div class="grid">${dims}</div>
    <div class="src">来源：${src}</div>
    <div class="fig"><div class="figbox"><div class="tag">${c} 图位</div><div class="cap">建议替换：该市地标原创摄影（1200×500）</div></div></div>
  </div>`;
}

function compareSlide(){
  let rows="";
  ORDER.forEach(c=>{
    const x=COMPARE[c];
    rows+=`<tr><td>${c}</td><td>${esc(x.zhuan)}</td><td>${esc(x.ben)}</td><td>${esc(x.shuo)}</td><td>${esc(x.bo)}</td><td>${esc(x.house)}</td><td>${esc(x.hukou)}</td></tr>`;
  });
  return `<div class="slide compare">
    <div class="kicker">COMPARE · 横向对比</div>
    <div class="sectitle">十一城核心条款对照</div>
    <div class="secsub">毕业生补贴按学历分档；购房 / 房票取最高学历档；落户为一句话摘要。</div>
    <div class="cmp"><table>
      <thead><tr><th>城市</th><th>专科</th><th>本科</th><th>硕士</th><th>博士</th><th>购房/房票(高学历)</th><th>落户摘要</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div>
  </div>`;
}

function riskSlide(){
  const rows=[];
  ORDER.forEach(c=>{
    SUMMARY[c].lines.risk.forEach(t=>{rows.push([c,t]);});
  });
  let h="";
  rows.slice(0,9).forEach(r=>{h+=`<div class="row"><div class="c">${r[0]}</div><div class="t">${esc(r[1])}</div></div>`;});
  return `<div class="slide risk">
    <div class="kicker">RISK · 风险提示</div>
    <div class="sectitle">签约前，先看这些</div>
    <div class="list">${h}</div>
  </div>`;
}

function closingSlide(){
  return `<div class="slide closing">
    <div class="big">读懂政策<br>方能安放理想</div>
    <div class="sub">数据来自政府公开文件，落地请以最新官方口径与个人资质认定为准。<br>愿每份选择，都有据可依。</div>
    <div class="seal">浙才志<br>编辑部</div>
  </div>`;
}

function buildDeck(){
  let html="";
  html+=coverSlide();
  html+=aboutSlide();
  html+=contentsSlide();
  html+=frameworkSlide();
  html+=overviewSlide();
  ORDER.forEach(c=>{html+=citySlide(c);});
  html+=compareSlide();
  html+=riskSlide();
  html+=closingSlide();
  return html;
}

const deck=buildDeck();
const N=deck.split('<div class="slide').length-1;
const stage=document.getElementById("stage");
stage.innerHTML=deck;

// navigation
let idx=0;
const slides=[...stage.querySelectorAll(".slide")];
const ct=document.getElementById("ct");
const dotsBox=document.getElementById("dots");
slides.forEach((s,i)=>{const d=document.createElement("div");d.className="d"+(i===0?" on":"");d.onclick=()=>go(i);dotsBox.appendChild(d);});
function go(i){
  i=Math.max(0,Math.min(N-1,i));
  slides.forEach((s,k)=>s.classList.toggle("on",k===i));
  document.querySelectorAll(".dots .d").forEach((d,k)=>d.classList.toggle("on",k===i));
  ct.textContent=String(i+1).padStart(2,"0")+" / "+String(N).padStart(2,"0");
  idx=i;
}
document.getElementById("prev").onclick=()=>go(idx-1);
document.getElementById("next").onclick=()=>go(idx+1);
document.addEventListener("keydown",e=>{
  if(e.key==="ArrowRight"||e.key==="PageDown")go(idx+1);
  if(e.key==="ArrowLeft"||e.key==="PageUp")go(idx-1);
  if(e.key==="Home")go(0);
  if(e.key==="End")go(N-1);
});
go(0);
</script>
</body>
</html>
"""

html = (TEMPLATE
        .replace("/*__DATA__*/", DATA_JSON)
        .replace("/*__SUMMARY__*/", SUM_JSON)
        .replace("/*__COMPARE__*/", CMP_JSON)
        .replace("/*__OVERVIEW__*/", OVW_JSON)
        .replace("/*__META__*/", META_JSON))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print("OK ->", OUT)
print("bytes:", len(html.encode("utf-8")))
print("cities:", len(ORDER))
print("slides expected: 19 (cover+about+contents+framework+overview+11city+compare+risk+closing)")
