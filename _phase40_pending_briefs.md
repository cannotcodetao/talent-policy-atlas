# Phase 40 区级铺开 · 进度追踪（2026-09-09 更新）

## 已完成 ✅
- T1 全库 district 标注：31 城 1095 条（`_annotate_district_all.py`，严格主体判定）
- **浙江 10 城全部采集+合并完成**（宁波13/温州20/嘉兴18/湖州13/绍兴10/金华17/衢州11/舟山12/台州15/丽水16），浙江 487→558
  - 舟山嵊泗 4 条死链（`:5443` 端口 404）→ 找到标准端口官方镜像 `ssdj.shengsi.gov.cn/uploads/file/…` 替换；白名单加 ssdj.shengsi.gov.cn
- **广东第 3 波完成 4/5**：广州15/深圳10/珠海8/汕头5 落盘，合并 32 条（广东 749→781）
- 每批回归五件套全 PASS（compliance 0/0/0 · multi 11/11 · redesign ALL · jsdom multi 18/18 + district 11/11 · meta_blind 高危=0）
- 备份 `_bak_20260908_phase40/`（46 份）

## 待执行
- **广东第 3 波剩 1**：佛山 foshan（429 中断于此处）
- **广东第 4 波**：韶关 shaoguan、湛江 zhanjiang、肇庆 zhaoqing、江门 jiangmen、茂名 maoming
- **广东第 5 波**：惠州 huizhou、梅州 meizhou、汕尾 shanwei、河源 heyuan、阳江 yangjiang
- **广东第 6 波**：清远 qingyuan、潮州 chaozhou、揭阳 jieyang、云浮 yunfu
- 跳过：东莞、中山（不设区）

## 合并命令
```bash
python _merge_district_data_v2.py --dry-run --batch 佛山           # 先看去重/不合规
python _merge_district_data_v2.py --batch 佛山,韶关,湛江,肇庆,江门
python _build_combined_data.py && python _build_html.py
# 回归五件套 + _meta_blind_scan.py 高危=0
# _score_snapshot.py _score_phase40_after.json + diff 逐条核对
```

## 子代理简报模板（{city}=城市名、{py}=拼音、{districts}=区县清单）

```
你是人才政策采集专员。任务：采集【{city}】下辖区县的「区级人才政策」（区县自己发布，非市本级），产出结构化 JSON 文件。纯联网调研（WebSearch/WebFetch），只写一个 JSON 文件。

## 区县清单（只采这些）
{districts}

## 采集优先级（现金类为主）
1. dim=grad_subsidy：{level: 专科/本科/硕士/博士, cash: 金额原文, house_voucher, condition}
2. dim=anju_subsidy：{name: 政策名, discount: 金额原文, condition}
3. dim=welfare：{type: 类型名, detail: 内容原文}
4. dim=anju_highlevel（选采）：{class: 人才类别, subsidy: 补贴原文, condition}
每条带 note 与 source: {unit, doc_no, date, url}。

## 硬规则
1. 来源仅 *.gov.cn 且实际可访问（WebFetch 核对金额；失败用 curl -sI）。404/死链不采。
2. 现行有效：2023 年以后优先；废止/过期/征求意见稿不采。
3. 只采区县级发文；市级政策不要；区县网站转载市级文件不要（发文单位是市级机关=市级，跳过）。
4. 金额抄原文，不换算不概括。
5. 无独立政策的区跳过，不编造，宁缺毋滥。
6. 每区 ≤4 条，全城 ≤20 条。

## 输出
Write 到 D:\beifen\desktop\school-job\个人简介&工作\人才政策\_district_raw\{py}_districts.json
{"city":"{city}","districts":[{"district":"XX区","policies":[{"dim":"grad_subsidy","level":"本科","cash":"…","house_voucher":"","condition":"…","note":"…","source":{"unit":"…","doc_no":"…","date":"…","url":"https://…"}}]}]}
dim 仅限：grad_subsidy / anju_subsidy / welfare / anju_highlevel。
完成后回报（150字内）：覆盖区数、条数、文件路径。
```

## 各城区县清单
- 金华：婺城区、金东区、武义县、浦江县、磐安县、兰溪市、义乌市、东阳市、永康市
- 衢州：柯城区、衢江区、江山市、常山县、开化县、龙游县
- 舟山：定海区、普陀区、岱山县、嵊泗县
- 台州：椒江区、黄岩区、路桥区、温岭市、临海市、玉环市、三门县、天台县、仙居县
- 丽水：莲都区、龙泉市、青田县、云和县、庆元县、缙云县、遂昌县、松阳县、景宁畲族自治县
- 广州：荔湾区、越秀区、海珠区、天河区、白云区、黄埔区、番禺区、花都区、南沙区、从化区、增城区
- 深圳：福田区、罗湖区、南山区、盐田区、宝安区、龙岗区、龙华区、坪山区、光明区
- 珠海：香洲区、斗门区、金湾区
- 汕头：金平区、龙湖区、濠江区、澄海区、潮阳区、潮南区、南澳县
- 佛山：禅城区、南海区、顺德区、三水区、高明区
- 韶关：浈江区、武江区、曲江区、乐昌市、南雄市、新丰县、翁源县、始兴县、仁化县、乳源瑶族自治县
- 湛江：赤坎区、霞山区、坡头区、麻章区、廉江市、雷州市、吴川市、遂溪县、徐闻县
- 肇庆：端州区、鼎湖区、高要区、四会市、广宁县、德庆县、封开县、怀集县
- 江门：蓬江区、江海区、新会区、台山市、开平市、鹤山市、恩平市
- 茂名：茂南区、电白区、高州市、化州市、信宜市
- 惠州：惠城区、惠阳区、惠东县、博罗县、龙门县
- 梅州：梅江区、梅县区、兴宁市、平远县、蕉岭县、大埔县、丰顺县、五华县
- 汕尾：城区、海丰县、陆丰市、陆河县
- 河源：源城区、东源县、龙川县、紫金县、连平县、和平县
- 阳江：江城区、阳东区、阳西区、阳春市
- 清远：清城区、清新区、英德市、连州市、佛冈县、连山壮族瑶族自治县、连南瑶族自治县、阳山县
- 潮州：湘桥区、潮安区、饶平县
- 揭阳：榕城区、揭东区、普宁市、惠来县、揭西县
- 云浮：云城区、云安区、罗定市、新兴县、郁南县

## 每波合并后的固定动作
1. `python _merge_district_data_v2.py --batch 城1,城2,…`（先 --dry-run 看去重/不合规）
2. `python _build_combined_data.py && python _build_html.py`
3. 回归五件套 + `_meta_blind_scan.py` 高危=0
4. `_score_snapshot.py` + before/after diff 逐条核对
