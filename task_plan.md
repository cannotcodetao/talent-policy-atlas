
# Phase 42 · 门户 + 多仓库 git 自动部署（2026-09-20，用户已确认方案）

## 用户决策
- 架构：全新门户首页做域名根 `/`，卡片入口 → /hub/（AI工具站）、/talent-policy/（政策页）、预留位；撤销 hub 侧栏入口
- git 部署：release 分支模式（本地 build 纯静态产物 push 到各仓库 release 分支，服务器 git pull，无需 Node）
- 服务器：直连 GitHub 拉取；cron 定时自动 pull（每 5 分钟）
- 门户风格：Editorial Ink（浅色纸面+衬线+单色强调，与 hub 一致）；自包含静态 HTML 零依赖
- 仓库布局：多仓库独立——personal-portal（新建）、ai-agents-hub（现有）、talent-policy-atlas（政策目录新 init）

## 任务
- T1 portal：D:/AI/project/IdeaCreate/personal-portal/（Editorial Ink 门户 index.html + _deploy release 脚本 + README）
- T2 hub：撤销 Sidebar 侧栏入口；vite base='/hub/'；删 public/talent-policy/；加 _deploy.sh；重建验证 dist 资源路径 /hub/assets/...
- T3 政策仓库：人才政策目录 git init（main = 源码+脚本，.gitignore 排除 _bak_*/.workbuddy/_*.txt）；_deploy.sh（HTML→release 分支 index.html）
- T4 本地组装验证：portal 根 + hub/ + talent-policy/ 三合一目录，http.server 验证 200 与资源路径
- T5 服务器侧交付物：一次性初始化命令（3 个 clone + Nginx 根目录指向 + cron 脚本）——命令文本交用户执行
- T6 GitHub 建库与首推：用户执行（外部动作）
- T7 簿记：task_plan/progress/memory

## 状态：🚧 执行中
�类展示不解析不换算）
- 渲染结构化堆叠：①金额行（.amt 加粗主题金色，多金额用 / 分隔）②条件行 ③备注行 ④来源行（细粒度格式见 T2）——各字段独占一行，不再 ｜ 串联
- 【待确认 Q1】布局选型：A 三列式（项目｜金额｜说明，金额独立成列）vs B 两列内堆叠（金额行置顶加粗）
- 【待确认 Q2】cash_quote（Phase 39 的「原文现金原话」）去留：删除（金额行本身即原文）vs 保留为金额行内小字
### T2 来源数据模型 + 细粒度渲染
- source 新增 `title`（文件全称）、`effective`（生效/修订说明，可选）；`scope`（适用范围）由 district 构建时自动派生「适用：{city}·{district}」，零编造
- 来源行格式：有文号→`《title》（doc_no）· unit · 发布 date · 生效/修订 effective · 适用 scope · URL`；无文号→`unit · 《页面标题/文件名》 · date · …`
- doc_no 清洗规范：只保留真实文号形态（X〔YYYY〕N号），混入的文件名移入 title、混入的备注移入 effective——只搬运不新增
### T3 逐城来源回源核验（32 城，子代理 lite，7 波×5 城）
- 每城一个子代理：输入该城条目清单（fingerprint+url+现有 source），逐 URL WebFetch/curl 回源提取 文件全称/文号/发布机构/发布日期/生效时间·修订版本
- 硬规则：只填页面上实际可核验的字段，查不到留空（渲染时降级为「unit+日期+URL」），绝不编造；顺带发现死链记入报告（死链不删条目，标注待查）
- 输出 `_source_refine/{py}.json`（fingerprint → {title, doc_no, date, effective, unit}）；合并脚本 `_merge_source_refine.py` 按 fingerprint 只增改 source 字段、不动业务字段
- 波次顺序：①杭州(试点) ②浙江5 ③浙江4+佛山 ④广东5 ⑤广东5 ⑥广东6 ⑦广东4（东莞/中山含在内）
### T4 收尾
- 每波合并后：重建 + 五件套（全 PASS 才进下一波）+ 来源字段覆盖率统计（title/doc_no/date 覆盖率曲线）
- 终验：评分快照 diff 必须 = 0（来源重写不影响评分口径）；`_test_district.js` 若断言 DOM 结构需同步更新
- 簿记：task_plan/progress/memory + SKILL.md Phase 41 段 + 交付

## 验收标准（AC41）
- AC41a 表格金额独立显示、条件/备注换行、结构清晰（jsdom 断言金额行存在且置顶）
- AC41b 全库来源行符合细粒度格式：有文号→全称+文号；无文号→机构+标题+日期；区级带适用范围
- AC41c 零编造：所有新增字段均有 URL 回源依据；查不到留空
- AC41d 每波五件套全 PASS；终验评分 diff=0
- AC41e 逐一城市推进：32 城每城独立子代理+独立合并，可断点续传

## 状态：✅ 计划已确认（2026-09-19 用户拍板）
- Q1 布局 = **A 三列式**（项目｜金额｜说明）
- Q2 cash_quote = **保留为金额行内小字**
- Q3 核验范围 = **仅问题条目**（477 条缺文号 + 文号形态混杂，约 700 条；其余沿用现有 source）
- 执行顺序：T1/T2 全局渲染改造 → T3 问题条目按城分波核验 → T4 收尾
普通毕业生政策（若有则数据修正；若确无本科档则评分记0或按Q1）。
- **T4 重建 + 回归四件套 + 排名模拟（按各学历口径）**
- **T5 技能同步 + 日志 + 交付**

## 验收指标（草稿）
- AC27a 全32城 grad_subsidy 本科档不含更高学历金额（0命中，已闭环）。
- AC27b 购房补贴评分不再取高层次人才档金额当普通毕业生口径（8处污染清除）。
- AC27c `_anju_subsidy_wan` 同时扫 discount + price_base（广州黄埔房票10/15/25万可被正确命中）。
- AC27d 首页学历筛选5按钮（全部/专科/本科/硕士/博士），选定后城市徽标/总榜/对比表按该学历口径排名刷新。
- AC27e 回归四件套全 PASS；排名模拟各学历口径数值合理。

## Phase 27 执行结果（2026-08-27 完成 ✅）
- 调研实证：问题1（学历串档）= 0 处（Phase 25 已修）；问题2（购房评分高层次污染）= 8 处。
- 三决策（AskUserQuestion）：无该学历档→记0；三维度全按学历重算；数据保留仅排名不取。
- T1 评分函数修正：`_anju_subsidy_wan`/`_welfare_rent_wan`/`_grad_item_wan` 加 `edu` 参数 + 加扫 `price_base` + `HIGH_LEVEL_KW` 黑名单禁高层次兜底；生成 `RANK_SCORES_BY_EDU`（5学历档）注入 JS。
- T2 学历筛选 UI：工具栏 `#eduFilter` + 抽屉 `#drawerEdu` + 对比弹窗 `#cmpEdu` 三处联动；`cityRankScore` 读 `RANK_SCORES_BY_EDU[eduFilter]`；切换学历→徽标/总榜/对比表全刷新。
- T3 数据复查：8处污染城市数据无误，问题在评分函数（已修），数据保留。
- T4 重建 1.18MB；回归四件套全 PASS（合规0/0/0 + 结构11/11 + redesign ALL PASS）；8处污染清除（7城购房=0，茂名=3万非高层次）；广州黄埔房票 price_base 加扫成功（本科10/硕士15/博士30万）；学历口径排名合理。
- T5 技能同步：SKILL.md 加 Hard Rule「评分口径按学历·禁高层次兜底」；日志+交付。
- 验收 AC27a–e 全达成。

---

# Phase 28 普适口径修正：排除特定人才计划金额（2026-08-30 完成 ✅）

## 目标（用户指令）
云浮「50万生活补贴（机关事业单位紧缺人才计划）」「27号文博士住房补贴16.68万（已到期）」等**特定人才**不要纳入排行榜计算，需要**普适的，即满足学历要求即可**。

## 调研结论（实证扫描全32城）
- 云浮各档几乎全非普适：50万需机关事业单位紧缺人才计划+3年合同+本科院校列入《优秀大学毕业生高校目录》；27号文16.68万**已过期**（2021-08到期，2022/2025清理未延长）；本科80万为创业人才项目（择优遴选，数据自标"非普惠"）。
- **根因**：`_grad_item_wan` 对 cash 文本所有「万」金额取最高，而很多条目 cash 混列普适与需认定金额 → 取到需认定的高值。
- 同类（8+城）：阳江博士500万实为**院士**第一类；珠海博士100万需认定高层次三类（普适仅25万）；韶关博士100万需认定创新创业人才；汕尾110万需善美英才+急需紧缺目录+5年合同+考核；肇庆60万限后备干部计划+事业单位/国企；潮州60万需韩江人才计划+认定高青人才；河源/中山/江门/揭阳/茂名/梅州/湛江均有复合条件。

## 已确认决策（AskUserQuestion）
- Q1 急需紧缺目录 → **排除**（严格按"满足学历要求即可"）。
- Q2 实施方式 → **关键词排除 + 逐条复核**。
- Q3 清理范围 → **三维度全清理**（毕业生补贴/租房/购房）。

## 执行
- **T1 三层普适判定**：`NON_UNIV_NEAR`（院士/认定/择优/特定计划/急需紧缺/单位限定/招聘公告/非普适明示/已失效/附加苛刻条件/夫妻双方）+ `NON_UNIV_RE`（到X事业单位、事业单位[、和或]、第X至Y类）+ `NON_UNIV_ITEM_RE`（经X认定、纳入X计划、已到期…）；`_mask_non_univ()` 按分句掩蔽（覆盖万+元）。
- **T2 三维度应用**：`_grad_wan`/`_anju_subsidy_wan`/`_welfare_rent_wan` 全部套用；`_item_non_univ` 条目级过滤。
- **T3 逐条复核（修3个bug）**：① 只查前置窗口→云浮标记在金额后方漏判，改**分句级且括号不切分**；② 分句左边界回溯越界→汕尾普适"7000元粤东西北就业补贴"被下一句"善美英才"误杀，改严格取分句；③ 条目级只查 name→毕业生补贴无 name 字段，补查 condition。另加 `UNIV_OVERRIDE`（中山博士52→20万、韶关博士50→20万）、"夫妻双方"标记（绍兴双博士150万）、`纳入.{0,14}计划`（江门）。
- **T4 回归+交付**：合规0/0/0 + 结构11/11 + redesign ALL PASS；源数据 1030 条未改动（数据保留、仅排名不取）；技能同步+日志+present_files。

## 验收
- AC28a 云浮全档 = 0（50/20/80/16.68万 均不计入）。
- AC28b 阳江博士500万（院士）→0；珠海博士100万→25万（普适保留）。
- AC28c 汕尾购房62.4万（善美英才）→0；绍兴博士150万（夫妻双博士）→取70万常规档。
- AC28d 中山博士52万（出站+境外复合）→20万；韶关博士50万（博士后出站专享）→20万。
- AC28e 三维度均普适口径；学历筛选联动排名正常。
- AC28f 回归四件套全 PASS；源数据条目数不变（1030）。
- AC28g SKILL.md 加「普适口径·禁特定人才计划」Hard Rule（三层判定+5条踩坑固化）。

## 结果（普适口径）
- 本科 TOP5：绍兴31 / 金华30 / 宁波19 / 舟山18 / 清远18
- 硕士 TOP5：绍兴41 / 金华40 / 丽水29 / 宁波27 / 湖州25
- 博士 TOP5：金华80 / 绍兴79 / 湖州50 / 嘉兴42.2 / 宁波40
- 归零 7 城（粤东西北）：云浮/阳江/潮州/揭阳/茂名/汕尾/梅州 —— 补贴全部依赖急需紧缺目录或特定计划，按 Q1 严格决策归 0；详情页仍可见，仅不参与排名。

## 验收 AC28a–g 全达成。

---

# Phase 29 佛山总额排查 + 全部档跨档兜底修复 + 总榜可点击（2026-08-30 完成 ✅）

## 目标（用户三条指令）
① 同步更新技能避免以后犯同样错误；② 32城力度总榜同样可点击城市跳出弹窗；③ 佛山排榜总额为什么是20.9万？有问题则排查其它城市同样问题。

## 排查结论（实证）
- **佛山 20.9万 = bug**。`全部档` 兜底「本科优先 → 否则取非高层次金额最小值」**不区分学历档** → 取到「博士/副高购房20万」+「硕士租房0.9万(750元/月)」；而本科档正确返回 0（佛山本科唯一来源"高明区购房补贴"因 person_req 提到"领军"被整条误排除）。**自相矛盾：全部 20.9万 vs 本科 0**。
- **全32城排查：14 城存在「全部≠本科」跨档虚高**（佛山20.9、肇庆13、中山20→10、汕头12.4→2.4、湖州20→15、温州3.012、衢州5.6、江门1、河源1、宁波/嘉兴/舟山/深圳/东莞小额）。

## 已确认决策（AskUserQuestion）
- Q1 全部档 → **≡ 本科档**（禁跨学历档兜底）。
- Q2 本科档 → **优先「普通本科」金额**；双一流/985/211/QS 属院校额外门槛，仅无普通本科时才用。

## 执行
- **T1 全部档 ≡ 本科档**：`city_dim_score`(grad)、`_anju_subsidy_wan`、`_welfare_rent_wan` 三处 `edu=None` 改「直接取本科档，无则 0」；删 Phase 28 遗留 `('中山','grad_subsidy',None):20.0`。
- **T2 本科分档 + 字段可信度分级**：
  - 新增 `ELITE_KW`（双一流/985/211/重点院校/QS/泰晤士/世界一流/名校/一流大学…）。
  - 学历档识别改「**分段优先 + 无命中回退 20 字窗口**」——`/` 既可作分档分隔（双一流本科4万/普通本科2万）又可作并列限定（本科/中级职称最高16万），固定 12 字窗口两种情形必错其一。
  - 否定表述「非'双一流'本科」判普通类（probe 含「非」）。
  - `_item_non_univ` 改**字段可信度分级**：name/condition 用全量词表；note/person_req/constraint **仅用强判定正则**。修 3 例误杀：佛山高明区 person_req 分层枚举、河源 note 描述他档、金华/丽水 constraint 旁支限制。
  - 恢复误删的 `_is_high_level_item(name)` 整条排除 + 词表补「高层次」「A类–F类」——修绍兴本科购房一度取到 500 万。
- **T3 总榜可点击**：`.rbcity` span → `<button data-city>`，点击 `openDrawer(city)`；绑定置于 `renderRankBoard()` 末尾（重渲染后重新绑定）；加 hover/虚线下划线/focus-visible CSS。

## 验收
- AC29a 佛山 20.9 → 2.0（普通本科档），全部档 = 本科档。
- AC29b 全32城「全部≠本科」不一致 = **0**。
- AC29c 异常值（购房>100万 或 总额>200万）命中 = **0**。
- AC29d 总榜城市为可点击 button，点击打开对应城市详情抽屉；切城市/切维度后仍生效。
- AC29e 回归四件套全 PASS + jsdom 总榜点击 10/10 PASS；源数据 1030 条未改动。
- AC29f 技能 SKILL.md 补「全部档≡本科」「院校门槛不算普适」「字段可信度分级」「总榜可点击」+ 重构勿丢 `_is_high_level_item` 警告。

## 结果（全部档 ≡ 本科档）
- 本科 TOP10：金华23 / 绍兴21 / 舟山20 / 宁波19 / 清远18 / 湖州15 / 丽水12 / 中山10 / 嘉兴7 / 衢州3.6
- 硕士 TOP10：绍兴41 / 金华40 / 丽水29 / 宁波27 / 湖州25 / 清远22.32 / 嘉兴18.48 / 河源15.7 / 佛山14.9 / 韶关8
- 博士 TOP10：金华80 / 绍兴79 / 湖州50 / 嘉兴42.2 / 宁波40 / 佛山30 / 惠州30 / 湛江30 / 清远27 / 江门26

## 验收 AC29a–f 全达成。

---

# Phase 32/33 清远 404 + 金华金额对不上 + 全城同类排查 + 技能同步（2026-09-02 发起）

> 注：Phase 30（来源—内容对应性审计）、Phase 31（总榜前置+统计维度筛选联动）已完成，详情见 `progress.md`；task_plan 未补段，此处接续。

## 目标（用户四条指令，原文）
1. 清远来源 `http://www.gdqy.gov.cn/.../post_1835696.html` 点击 404 not found → 解决并**记录原因**
2. 金华金额对不上 → 解决并**记录原因**
3. 查询**其它城市**是否存在同样的问题（死链 + 金额口径）
4. **同步更新技能**

## 已确认决策（AskUserQuestion）
- D1 租房期限口径 → **期限累计 + 毕业生补贴里的按月补贴也一并计入**（最激进方案）
- D2 清远来源替换 → **南方+（南方日报）政策全文 + 申报平台入口**
- D3 清远剩余 13 处 gdqy.gov.cn 链接 → **全部找替代可核验来源**（用户选 B；尽力检索，确实无单页全文转载版者回退 WAF 说明）

## 已完成（本会话前半，规划文件此前未记录）
- **清远 404（指令①）** ✅：根因 = gdqy.gov.cn 网站改版迁移致 post_1835696 失效，且该站全站部署滑块 WAF，外部工具无法核验任一该站链接。政策本身现行有效（2026-03-02 管委会仍发布申报通知；南方+/西安交大就业网/清远高新区知识产权平台均载第十九条原文）。已将 6 条政策（grad 1-4/anju 0/timing 2）source.url 换为南方+ 全文转载 `static.nfnews.com/content/202403/04/c8655791.html`（实测 200 + 含「2000元/月」「1000元/月」「36个月」原文），并补官方申报平台入口 `https://qyzqht.cn/`。
- **金华金额对不上（指令②）** ✅：根因 = 租房补贴一律按 12 个月年化，而政策原文是「最长 36 个月」（600元/月×36÷10000=2.16 万，原算 0.72 万）。修复后金华本科 grad 4.0+anju 8.0+welfare 2.16=14.16 万（原 12.72）。
- **全城同类排查（指令③）** ✅：重跑全量 URL 扫描（362 个），**真 404 = 0**；41 处异常全为环境性误报——梅州 6×521（CDN 屏蔽数据中心 IP，WebFetch 复测可达）、清远 6×405/412（WAF，已实证存在真 404 故同域高风险）、深圳 10×+河源 12×+英德 1× SSL（curl `-k` 复测河源 200=证书链不完整、深圳 200=transient）。
- **评分逻辑修复** ✅（`_build_html.py` 6 处）：① 新增期限解析 `_dur_spans`/`_rent_months`（支持「N个月」「N年」「×N年」乘号；不含「分N年发放」避免金华 4万×5年虚高 60 倍）；② 汇总金额排除 `_SUM_KW`（合计/共计/总计/累计最高）防清远 10.8 万重复吃掉安居 7.2 万；③ 死链误判剥离 `_DEAD_LINK_RE`（note 里「链接已失效」被误当「政策已失效」致清远整条归零，误杀 8 处）；④ 新增 `_grad_monthly_wan`（毕业生补贴按月现金计入）；⑤ `_grad_item_wan` 并入按月值；⑥ `_welfare_rent_wan` 按月累计。连带修 3 bug：跨维度重复计分（租房排除 `_RENT_ONLY_KW`）、租房排除漏网（分段+悬挂继承）、乘号期限格式（舟山 ×2年）。
- **diff 审计** ✅：30 处评分变更逐条核对合理；异常值哨兵（startup>200/anju>120/其它>60）0 命中；清远本科 grad 3.6+anju 7.2=10.8 与政策原文「合计最高约10.8万元」完全吻合。
- **HTML 重建** ✅：`_build_html.py` → `人才引进政策_2026.html`（1.20 MB）。

## 待执行（本会话后半）
- **T1 清远 13 处 gdqy.gov.cn 替代来源检索**（D3，6 个不同 URL）✅ 完成：
  - 检索 + curl 实测 200 + 内容核对，5 个找到可核验替代源、1 个回退 WAF 说明：
    1. `post_2164773`（省级就业创业指导单）→ `gd.gov.cn/zwgk/gongbao/2026/16/content/mpost_4921748.html`（粤人社规〔2026〕20号 省级原文）— grad_subsidy 0 + startup 1
    2. `post_1948909`（落户解读）→ `12345.gdqy.gov.cn/.../faqDetail.html?klpId=875608`（清府〔2024〕37号 全文+解读）— hukou 1/2/3
    3. `post_297829`（人才公寓办法）→ `12345.gdqy.gov.cn/.../faqDetail.html?klpId=875641`（过渡性办法 2021 全文；2025修订版 PDF 仍 WAF'd，note 注明）— welfare 0 + risk 1
    4. `post_2063384`（创业担保贷款）→ `qqt.gdqy.gov.cn/web/policy/policy_detail.ptl?policyId=190000264`（清企通 清人社〔2020〕27号 办事指南全文）— startup 0 + risk 2
    5. `post_2098874`（配售型保障房办法）→ `www.qyrb.cn/content/0EynlL06ZA.html`（清远日报 2025-12-31 全文解读）— timing 3 + risk 0 + anju_discount 0
    6. `post_2174825`（市政协答复函）→ **回退 WAF 说明**（确无 gov.cn 外全文转载，政策实质内容已自包含于 note）— anju_subsidy 1
  - 脚本 `_replace_qingyuan_urls.py`（5 URL 替换 12 处）+ `_annotate_qingyuan_waf.py`（1 处 WAF 标注）。
- **T2 重跑合并 + HTML** ✅：`_build_combined_data.py`（浙江 345 + 广东 699 = 1044 条）+ `_build_html.py`（`人才引进政策_2026.html` 1.207 MB）。
- **T3 回归四件套** ✅ 全 PASS：合规 0/0/0（`_validate_compliance.py` 加 `SANCTIONED_NON_GOV_HOSTS` 白名单登记清远 3 个授权替代域）+ 结构 11/11 + redesign ALL PASS + jsdom 18/18 PASS（node 22.22.2-2；22.12.0 段错误）。
- **T4 技能同步** ✅：scripts/ 更新 `_build_html.py`/`_validate_compliance.py`/`_build_combined_data.py`/`_validate_multi.py` + 新增 `_scan_urls.py`；SKILL.md 新增「Phase 33」段（6 类 Hard Rule + 诊断技巧 + WAF/CDN/TLS 三态知识 + sanctioned 白名单规则）。
- **T5 规划文件 + 记忆** ✅：task_plan.md（本段）+ progress.md 今日 log + findings.md 新发现 + `.workbuddy/memory/2026-09-02.md`。

## 验收指标
- AC33a 清远 post_1835696 404 已替换为可达链接（南方+ 全文，6 处）；6 类 gdqy.gov.cn 同域链接 5 个换可核验替代源 + 1 个回退 WAF 说明，无未处理项 ✅
- AC33b 金华金额按政策最长期限累计（600元/月×36=2.16万）；9 城 24 条按月漏计全修复 ✅
- AC33c 全 32 城 0 真 404（362 URL 扫描）；剩余 41 异常全部定性为环境性（WAF/CDN/TLS）并记录 ✅
- AC33d 评分 diff 30 处逐条合理；异常值哨兵 0 命中；清远本科=10.8 吻合原文 ✅
- AC33e 回归四件套全 PASS（合规0/0/0 + 结构11/11 + redesign ALL PASS + jsdom 18/18）✅
- AC33f 技能 SKILL.md + scripts/ 同步 6 类规则 + 诊断技巧 ✅

## 验收 AC33a–f 全达成 ✅

## 已知限制（非本次范围）
- Phase 30 D 类 11 条【来源待升级】、B 类 14 条主体错配复核
- startup 维度「大赛/项目资助 200 万」（中山/云浮）/100 万（深圳）未走普适口径致本科档 TOP 失真（Phase 28 遗留）
- 杭州富阳富政办〔2019〕9号、台州临海台政办发〔2025〕7号配套细则原 PDF/单页 404 已在 Phase 31 前修（note 标【来源已升级】，本会话重扫确认 0 真 404）

---

# Phase 34 grad_subsidy 字段语义污染 + 同档重复（2026-09-06 发起）

## 目标（用户原文）
> 宁波：购房补贴最高8万 ｜ 房票：购房补贴 最高8万，这两个不是重复了吗？广州为什么出现多处重复学历？解决这些问题并检查其它城市，**避免以后出现同样错误**，先计划再执行，同步更新技能

## 已确认决策（AskUserQuestion 2026-09-06）
- **D1 购房补贴跨列重复（43 处/15 城）** → 从「现金」列剥离，「房票」列保留（信息零丢失；实测 31/32 城评分不变）
- **D2 广州 grad[5][8][11] 落户条（与 hukou 维度完全重复）** → **删除**
- **D3 广州同档多政策（市级/黄埔/南沙/安居）** → **合并为一条汇总**（用户选 C，非推荐项 A）
  - 风险：source 为 dict 不支持数组，合并后仅能挂 1 个主 source
  - 缓解：其余来源的**文号 + URL 完整写入备注**，且均为 gov.cn 域，合规校验不受影响

## 事实基线（调研已完成，见 findings.md Phase 34 段）
- 列定义 `_build_html.py:919`：`grad_subsidy = 学历 | 现金(cash) | 房票(house_voucher) | 条件 | 备注`
- **A 类真重复 34 处/13 城**：宁波4 嘉兴4 湖州4 金华5 衢州1 舟山4 丽水1 中山1 江门1 韶关1 茂名2 汕尾2 清远3 潮州1
- **B 类错置 9 处/4 城**：广州1 佛山5 清远2 潮州1
- **C 类正常 56 处/18 城**：不修（house_voucher 字段本义）
- 广州 grad 12 条：专科1/本科5/硕士3/博士3；全库仅此 3 条 cash+hv 全空
- **清远特例**：cash 用「逗号+加号」连接（购房补贴2000元/月 + 生活补助1000元/月），批量正则会整条删除致 3.6→0.0，**须手工处理保住 3.6**

## 任务
- **T1 广州 grad_subsidy 重构** → 改源 `guangdong_raw/guangzhou.json`
  1. 删除 grad[5][8][11]（落户条，hukou[2][1][0] 已有）
  2. 合并本科 4 条 → 1 条；硕士 2 → 1；博士 2 → 1；专科 1 条不动
  3. 目标：12 条 → 4 条。评分须保持 本科3.0 / 硕士6.0 / 博士12.0 不变
  4. 备注写全各区文号 + URL（穗人社规字〔2022〕1号 / 穗埔人社规字〔2024〕2号 / 南沙人才九条 / 四高四无忧）
- **T2 A/B 类 43 处逐条剥离** → 改源 `zhejiang-talent-data.json` + `guangdong_raw/*.json`
  - **禁用批量正则**（清远误伤教训）；逐城逐条写死「原文 → 新 cash / 新 house_voucher」映射
  - 清远 5 条手工处理（保 3.6）
  - A 类说明性重复（清远 grad[1][3][4] hv 为申领条件）保留 hv 不动
- **T3 扩展排查其它城市同类问题**
  - T3a 跨维度重复：grad_subsidy 与 hukou / anju_subsidy 内容重复（广州式）
  - T3b 同 level 多条（金华 9 条/各档最多 2 条需判性）
  - **注意**：hukou 用 `target`+`rule`，grad 用 `level`+`condition`，跨维度查重须先对齐 schema
- **T4 重跑合并 + HTML**：`_build_combined_data.py` → `_build_html.py`
- **T5 回归四件套 + 评分 diff 逐条核对**
  - 四件套：`_validate_compliance.py`(0/0/0) + `_validate_multi.py`(11/11) + `_validate_redesign.py`(ALL PASS) + jsdom `_test_multi.js`(18/18，**须用 node 22.22.2-2**，22.12.0 段错误)
  - 哨兵：清远=3.6、广州本科=3.0/硕士=6.0/博士=12.0、宁波本科=3.0
- **T6 同步技能** `~/.workbuddy/skills/talent-policy-collector/`
  - SKILL.md 新增 Phase 34 段：**Grad 字段语义规则**（cash 禁含购房/房票，购房只归 house_voucher）+ **跨维度查重规则**（先对齐 schema）+ **合并条目保留多来源规则**（备注写全文号+URL）
  - scripts/ 同步 `_scan_grad_dup2.py`、更新 `_build_combined_data.py`
- **T7 规划文件 + 记忆**：task_plan.md / progress.md / findings.md / `.workbuddy/memory/2026-09-06.md`

## 执行结果

**T1 广州重构** ✅：`_fix_guangzhou_grad.py`（源 `guangdong_raw/guangzhou.json`，备份 `.bak_20260906`）
- 删除 grad[5][8][11]（与 hukou[2][1][0] 完全重复的落户条）
- 合并：本科 4→1、硕士 2→1、博士 2→1、专科 1 条保留 → **12 条 → 4 条**
- 主 source 取支撑该档最高金额者（南沙），其余来源文号 + URL 写入 note，信息零丢失
- **踩坑与修复（两轮）**：
  - 第 1 轮把安居无忧的「高层次/创新创业/急需紧缺」写进 condition + house_voucher → 触发 `_item_non_univ` 全量词表判定，
    整条判非普适，**南沙3万+黄埔2万+市级社保补贴一起归零（3.0 → 0.0）**。
    修复：触发词移入 note（note 只用强判定正则）→ 恢复 3.0。
  - 博士档改前实得仅 5.0（黄埔），因南沙条的「（或特级技师）」命中 NON_UNIV_NEAR 整条误杀（**存量 bug**）。
    修复：并列资格从 cash/condition 移出、note 说明 → **5.0 → 12.0**。

**T2 A/B 类剥离** ✅：`_fix_grad_buy_dup.py`，逐条写死映射 + `old_cash` 断言，共 **42 条**（43 处 − 广州[0] 已在 T1 处理）
- 覆盖 15 城：宁波4 嘉兴4 湖州4 金华5 衢州1 舟山4 丽水1 中山1 江门1 韶关1 茂名2 汕尾2 清远5 潮州2 佛山5
- 清远 5 条手工处理（cash 用「逗号+加号」连接，正则会整条删除）
- 佛山 B 类 5 条：购房内容从现金列**迁入房票列**；现金列写「—」、说明入 note（避免交叉引用语自指命中扫描器）
- 备份：`_bak_20260906/`（zhejiang-talent-data.json + guangdong_raw/*.json 全量 22 份）

**T3 扩展排查** ✅：`_scan_cross_dim_dup.py`
- T3a 跨维度重复：发现 **3 处**（广州 grad[5][8][11] 已删、广州 grad[0] 合并引入、**珠海 grad[0] 存量**）→ 全部修复，**重扫 0 处**
- T3b 同档多条：修复后仅剩**金华 4 组**，核查为真实多政策并列（金人社发〔2023〕13号 vs 2024 生活补助，两个文号两个来源）→ **判定不需修**
- T3c grad 房票 vs anju：仅肇庆 2 处同金额，属跨维度视角性重复，评分上 grad 已排除购房不重复计分 → **设计内，保留并说明**
- 附带：`_scan_nonuniv_kill.py` 扫出全库 31 条「非普适整条归零且含金额」，逐条判性后确认**仅广州南沙博士 1 例为真误杀**（已修），其余 30 条确需认定/属特定计划，判定正确

**T4 重跑** ✅：`_build_combined_data.py`（浙江 345 + 广东 691 = 1036，广东 699→691 因广州减 8 条）+ `_build_html.py`（1.2015 MB）

**T5 回归** ✅ 四件套全 PASS
- 合规 `_validate_compliance.py` **0/0/0**
- 结构 `_validate_multi.py` **11/11**
- redesign `_validate_redesign.py` **ALL PASS**
- jsdom `_test_multi.js` **18/18**（node 22.22.2-2 + `NODE_PATH` 指向托管 workspace）
- **评分 diff 仅 2 处，均为修复真实漏计**：舟山博士 2.4→10.0（安家补贴从购房同句释放）、广州博士 5.0→12.0（并列资格误杀修复）
- 哨兵全绿：清远本科 3.6、宁波本科 3.0、广州本科 3.0 / 硕士 6.0 / 博士 12.0

**T6 技能同步** ✅：SKILL.md 新增「Phase 34」段（7 条 Hard Rule + 2 个新 bug 型 + 扫描器自指陷阱 + 回归基准）；
scripts/ 新增 `_scan_grad_dup2.py`、`_scan_cross_dim_dup.py`、`_score_snapshot.py`，更新 `_build_combined_data.py`/`_build_html.py`/`_validate_compliance.py`

## 验收指标
- AC34a 宁波 grad「现金」列不再出现购房补贴；全库 A+B 类清零（重扫 **A=0 B=0 空条=0**）✅
- AC34b 广州 grad **12 → 4 条**；专科/本科/硕士/博士各 1 条；无 cash+hv 全空条目 ✅
- AC34c 评分：清远 3.6 / 宁波 3.0 / 广州本科 3.0 硕士 6.0 全部不变；**广州博士 5.0→12.0、舟山博士 2.4→10.0 系修复存量漏计（已逐条核对）** ✅
- AC34d T3 扩展排查完成：T3a 3 处全修（含珠海存量）、T3b 金华判定不需修、T3c 肇庆 2 处设计内保留，结论落 findings.md ✅
- AC34e 回归四件套全 PASS ✅
- AC34f 技能 SKILL.md + scripts/ 同步，含 7 条预防规则 ✅

## 验收 AC34a–f 全达成 ✅

---

# Phase 35 浮点显示异常 + 租房补贴跨维度丢失（2026-09-06 发起）

## 目标（用户原文）
> 为什么嘉兴显示7.4399999999999995 万异常？杭州的政策来源未见到租房补贴，均是生活补贴，解决这些问题并检查其它城市，先计划再执行，同步更新技能

## 调研结论（已完成，详见 findings.md Phase 35 段）
### 问题1 嘉兴浮点异常
- 根因：`_build_html.py` TEMPLATE 中 `cityRankScore()` 求和后未取整：
  `let s=0;rankSel.forEach(d=>s+=(tbl[d]&&tbl[d][c])||0);return s;`
  嘉兴本科 1.0+1.44+5.0 在 IEEE754 下 = 7.4399999999999995，直接 `o.s+' 万'` 拼接显示。
- 影响面：3 处下游（总榜 rbscore、对比表 rkscore、徽标）全走 cityRankScore。
- 修复：cityRankScore 返回 `Math.round(s*100)/100`（一处修复，三处生效）。

### 问题2 杭州租房补贴（来源-内容不对应 + 跨维度丢失）
- 杭州已挂来源 hrss.hangzhou.gov.cn/art/2025/3/3 是《应届毕业生**生活补贴**申请指南》，
  **通篇无租房补贴**——grad cash 里「租房补贴 1万/年×3年」挂错来源（用户观察正确）。
- 真政策：新引进应届大学生租房补贴（市住保房管局），每户每年 1 万、可发 3 年，
  全球本科及以上应届全日制、在杭就业连续参保 6 个月、无房。
  官方来源：fgj.hangzhou.gov.cn/art/2025/3/10/art_1229265015_58878510.html（住保房管局官方解读）。
- 数据缺陷：grad cash 混入租房补贴（按 _RENT_ONLY_KW 计分排除）+ welfare 维度无条目 → **两头都没算**
  （welfare=0，用户在「租房补贴」维度找不到）。

### 全城扫描（_scan_rent_misplaced.py）
**P1 完全丢失**（grad cash 含租房补贴但 welfare=0）——5 城 14 档：
| 城市 | 内容 | 处置 |
|---|---|---|
| 杭州 4 档 | 租房补贴 1万/年×3年（本科及以上） | 补 welfare 条目（计分），来源住保房管局 |
| 丽水 4 档 | 租房补贴 6000元/年×3年 | 补 welfare 条目（计分）+ grad source 修正（44号文已废止且不含此内容） |
| 温州 2 档 | F类 1万/年、E类 2万/年 | 补 welfare 条目（**不计分**——人才分类需认定，普适判定自动排除） |
| 潮州 2 档 | 韩江人才计划 1500-2000元/月×3年 | 补 welfare 条目（**不计分**——需入选计划） |
| 衢州 2 档 | 非衢州户籍企业员工 3000元/年 | 补 welfare 条目（**不计分**——无学历门槛，非毕业生学历档政策） |

**P2 双维度冗余**（welfare 已计分 + grad cash 冗余呈现）——湖州/金华/梅州/佛山：
grad cash 剥离租房分句（沿用 Phase 34 D1 已确认口径，租房归 welfare 呈现）。

### 丽水来源错挂（排查中发现的存量问题）
- grad 5 条挂丽政办发〔2024〕44号——该文**有效性标注「废止」**且原文只有房票/引才/奖励 3 条，
  **不含** grad cash 里的就业奖补与租房补贴。
- 就业奖补真正依据：丽委人〔2022〕2号（丽水经开区 2025/2026 公示页引用，金额本科 2 万/专科 1 万实证吻合）。
- 租房补贴依据：《高校毕业生来丽人才政策指引》（毕业 3 年内每年 6000 元、≤3 年）。
- 修复：grad source 换 kfq.lishui.gov.cn 公示页（引用文号+金额实证，gov.cn 可核验）+ note 注明政策沿革。

## 任务
- **T1 浮点修复**：`cityRankScore()` 返回 `Math.round(s*100)/100`
- **T2 杭州修复**：welfare 补租房补贴条目（fgj.hangzhou.gov.cn 来源）+ grad cash 剥离租房分句
- **T3 P1 四城补条目**：丽水（计分+来源修正）/ 温州 / 潮州 / 衢州（后三城呈现补、计分按普适判定自动排除）
- **T4 P2 四城剥离**：湖州/金华/梅州/佛山 grad cash 剥离租房分句
- **T5 重跑合并 + HTML + 评分 diff**（预期变化：杭州 welfare 本/硕/博 0→3.0；丽水 welfare 0→1.8×4 档）
- **T6 回归四件套**
- **T7 技能同步**：SKILL.md Phase 35 段（浮点规则 + 租房补贴维度归属规则 + 来源-内容对应复核）+ scripts/
- **T8 规划文件 + 记忆**

## 验收指标
- AC35a 嘉兴总榜显示 7.44 万（无浮点尾巴）；全库无 …9995 类显示
- AC35b 杭州 welfare 含租房补贴条目且来源为住保房管局官方页；grad 现金列不含租房补贴
- AC35c P1 五城 welfare 均有租房补贴条目；P2 四城 grad 现金列无租房补贴
- AC35d 评分 diff 逐条核对（预期：杭州/丽水 welfare 变化 + 温州/潮州/衢州不计分确认）
- AC35e 回归四件套全 PASS
- AC35f 技能 SKILL.md + scripts/ 同步

## 硬约束（继承历次 Phase）
1. 必须改**源头文件**（`zhejiang-talent-data.json` / `guangdong_raw/*.json`），改 `talent-data.json` 会被重跑覆盖
2. 改数据前 `.bak` 备份
3. 禁止批量正则改写字段 → 逐条人工核对 + 逐条 diff 验证评分
4. 结论须实证（实际跑命令/查数据），不凭单次扫描妄断

---

# Phase 36 金华重复学历 + 元反思：项目全局盲区扫描（2026-09-06 发起）

## 用户原文
> 金华仍然出现多处重复学历：普通本科、普通本科；解决这些问题并检查其它城市。
> 对于整个项目现在的情况，眼下你最没有把握的事情是什么？关于当前的情况，最大的遗漏是什么？没有意识到什么？
> @skill:planning-with-files 先计划再执行，同步更新技能

## 用户三层指令（拆解）
1. **直接任务**：金华出现重复学历（普通本科、普通本科），排查其它城市同类问题 → 修复 + 全城扫
2. **元反思任务 A**：眼下最没有把握的事情是什么？
3. **元反思任务 B**：最大的遗漏是什么？没有意识到什么？
4. **流程要求**：先 plan → 执行 → 同步技能

## 元反思预判（计划前自检）
基于 36 个 Phase 的累积，对照用户历史指令和痛点，本人最没把握/最可能遗漏的维度：
- **A. 重复模式已演化**——Phase 34 修的是"同档多条（不同政策主体）"，但**合并后**出现"同档单条 cash 内重复"（用户已发现广州模式）；金华现在的"普通本科、普通本科"疑似**合并遗留**（Phase 34 D3 决策合并后未清理）→ 已需查 raw 源文件
- **B. 合并是双刃剑**：Phase 34 D3 决策合并 4 城同档多条为单条，但用户选的是「合并」选项而非「拆分主体」选项 → 合并产物可能仍存在合并未尽的碎片
- **C. 数据层 vs 渲染层未对齐**：raw 源可能干净但合并产物有遗漏；反之亦然
- **D. 跨维度遗漏**：Phase 35 只查 welfare 与 grad 错位，未查其它 9 维的同档重复
- **E. 维度内重复**：11 维内都可能存在"同学历档现金列内重复金额"——比 Phase 34 的"cash+hv 跨列重复"更深一层
- **F. 元数据同档**：多条 entry 的 `level`/`target` 字段完全一致但内容不同（如同档不同时间窗口）—— Phase 34 D3 合并口径可能误合并

## 调研待执行（T0）
- **T0a** 金华重复学历现状实证：grep `level":"普通本科"` 在 talent-data.json 和 zhejiang-talent-data.json 计数；查 9 维逐条 cash 是否含同档重复金额
- **T0b** 全库 11 维 × 32 城 × 5 学历档重复扫描：`_scan_dim_dup_v2.py`——同档多条 + 同条内重复金额 + 跨维度重复
- **T0c** 元盲区扫描——基于 36 Phase 累积的痛点，列出 5 项最可能遗漏的检查点
- **T0d** 元数据 raw 源 vs 合并产物 diff

## 任务（待 T0 完成后定稿）
- **T1** 金华重复学历修复（具体根因待 T0a 揭示）
- **T2** 全库 11 维重复扫描（`_scan_dim_dup_v2.py`）
- **T3** 全库元盲区扫描（基于 T0c 列出的 5 项检查点）
- **T4** 修复 + 重跑合并 + HTML
- **T5** 回归四件套 + 评分 diff
- **T6** 技能同步 + 元反思落 SKILL.md（不是只列规则，而是要把"应该这样问自己盲区"的工作流也固化）

## 验收指标（草稿，待 T0 完补充）
- AC36a 金华普通本科档重复条目 → 0
- AC36b 全库 11 维 × 32 城 重复扫描 = 0（除合理多政策并列）
- AC36c 元盲区 5 项检查点全部过一遍
- AC36d 回归四件套全 PASS
- AC36e 技能新增「元盲区自查清单」（10 个自我提问）—— 防止"最没把握的事"再次出现在用户指令里

## 硬约束（继承历次 Phase）
1. 必须改**源头文件**（`zhejiang-talent-data.json` / `guangdong_raw/*.json`）
2. 改数据前 `.bak` 备份
3. 禁止批量正则改写字段 → 逐条人工核对 + 逐条 diff 验证评分
4. 结论须实证
5. **新增硬约束**：用户问"最没把握/最大遗漏"时，必须把盲区清单连同修复一并落地，不能只回答"已修好"

---

# Phase 37 高层次人才专项独立维度恢复（2026-09-06 发起）

## 用户原文
> 对于杭州E类人才这样特殊的政策该如何加入？
> "E类人才只是举例，具体想问这些特殊人才，还有D类，或者恢复专栏但是不加入总榜也行"
> 恢复独立维度「高层次人才专项」（推荐）

## 目标
1. **恢复 `anju_highlevel`（高层次人才专项）独立维度**（Phase 18 合并前是 `talent_highlevel`，被合并时删除）
2. **位置**：在安居购房 4 维（anju_rent2sale/anju_discount/anju_subsidy/anju_enterprise）之后，timing/risk 之前
3. **不参与总榜排名**：保留 Phase 28 Hard Rule（普适口径·禁高层次兜底）
4. **数据建模**：以 (city, talent_class [A/B/C/D/E/F], 补贴类别, 金额, 条件, 来源) 为主键
5. **UI**：维度标签"高层次人才专项" + 不参与排名徽标（如"【仅查阅】"）

## 调研结论（T0 已完成）
- 杭州当前高层次人才已散落在 welfare[0]（E类40%人才租赁住房优惠）+ anju_subsidy[0]（A-D类市级购房补贴）+ anju_subsidy[1]（A-E类钱塘区区级购房补贴）
- **Phase 29 实证**：杭州钱塘区E类30万曾被误算进本科档，污染 ranking（已修）
- 用户期望：**有专属维度可查、不参与排名**

## 任务
- **T1** 数据迁移：把现有 anju_subsidy/welfare 里含 A-F 类关键词的政策提取到新维度 anju_highlevel
- **T2** 维度建模：以 `talent_class` (A/B/C/D/E/F) 为主键，按 city×class×category 组织条目
- **T3** 渲染层：在 `_build_html.py` 加入 `anju_highlevel` 维度处理 + 维度标签"高层次人才专项" + "【仅查阅，不参与排名】"标识
- **T4** 合规校验：`_validate_compliance.py` 需识别新维度（不计入 PURE_RENTAL_KW 红线判定，因高层次人才公寓本身属于安居购房范畴）
- **T5** 重跑合并 + HTML + 回归四件套（新增维度须 11+1=12 维度验收）
- **T6** 技能同步：SKILL.md 新增 Phase 37 段（高层次人才维度建模 + 不参与排名硬规则）
- **T7** 规划文件 + 记忆

## 验收指标（草稿）
- AC37a 全 32 城 anju_highlevel 维度上线；现有 A-F类政策全部迁移
- AC37b 维度标签"高层次人才专项"在页面 12 维列表中显示
- AC37c 高层次人才维度【仅查阅】徽标可见
- AC37d 总榜评分不受新维度影响（保留 Phase 28 普适口径）
- AC37e 回归四件套全 PASS（结构验收须 12 维度齐全）
- AC37f SKILL.md Phase 37 段同步

## Phase 37 执行结果（2026-09-06 固化）

### 实施摘要
- **T1 数据层** ✅：DROP_DIMS 移除 talent_highlevel；浙江/广东循环加兼容映射；placeholder_highlevel() 专属函数
- **T2+T3 渲染层** ✅：DIM_ORDER 12 维；SCHEMA anju_highlevel 专属字段映射；占位条目显示例外；source 对象渲染；徽标「仅查阅·不参与排名」
- **T4 合规校验** ✅：DIM_ORDER/ANJU_DIMS 加新维
- **T5 回归四件套** ✅：合规 0/0/0、结构 11/11、redesign ALL PASS、jsdom 18/18
- **T6+T7 技能同步** ✅：SKILL.md 新增 Phase 37 段 + _restore_highlevel_dim.py 脚本入库

### 实证指标
- anju_highlevel 总条目：**113 条**（100 条真实 + 13 条占位 = 22 城有数据 + 10 城占位）
- 维度数：**12 维**（11+1）
- HTML 大小：1.27MB（Phase 36 后 1.21MB，新增 113 条高层次人才）
- 回归四件套：
  - `_validate_compliance.py`：0/0/0 PASS（bad_host=0, non_official=0, redline=0）
  - `_validate_multi.py`：11/11 PASS（含 AC5「32 城全部入库」、AC6「十二维标签齐全」）
  - `_validate_redesign.py`：ALL PASS（10 项 AC）
  - `_test_multi.js`：18/18 PASS（M7 显示「九、高层次人才专项 仅查阅·不参与排名」徽标可见）

### 关键决策与设计
- **改名**：`talent_highlevel` → `anju_highlevel`（与 `anju_*` 前缀一致）
- **位置**：DIM_ORDER 第 10 位（安居 4 维之后、timing/risk 之前）
- **不参与总榜**：RANK_DIMS_ALL / cityRankScore 保持不变（仅 `grad_subsidy` / `welfare` / `anju_subsidy`）
- **分类体系保留原文本**：不归一化 A-F 类，各地市保留自有分类（杭州 A-E、广州院士/杰出/优秀专家、佛山领军人才一-四类等）

### 已知遗漏（待下次更新）
- **广东 10 城占位**：韶关/茂名/梅州/汕尾/河源/阳江/清远/潮州/揭阳/云浮 源头无 talent_highlevel 数据；可能存在但未采集（如韶关丹霞英才、清远高新区等可能归并在毕业生补贴/创业扶持维度）。建议下次更新时联网核查这 10 城是否有公开的高层次人才分类目录

### 备份位置
- `_bak_20260906_phase37/`：zhejiang-talent-data.json + guangdong_raw/*.json + _build_combined_data.py + _build_html.py + _validate_compliance.py

---

# Phase 38 · 区级政策搜索与合并 + README 项目定位（2026-09-08 发起）

## 用户原文
> 先做计划写进进度文件，再执行，执行完成后更新进度文件，已完成且不重要的任务可删除，
> 做一个项目定位文件 README.md 文件，简单阐述项目介绍和功能定位。
> 像杭州有些区有各自的政策，这些该如何搜索并将信息合并？
> 如果我的指令不够清晰，则跟我确定之后再执行。

## 现状调研（T0 已完成，实证）
- **区级政策已混入市级数据，且无结构化标注**：全库 **173 条**条目含「XX区」关键词，散布 32 城
  - 杭州：anju_subsidy[1]「钱塘区高层次人才购房补助实施细则」、anju_discount[0]「余杭区人才专项用房」
    anju_discount[1]「富阳区人才公寓」、anju_enterprise[0]「余杭区人才专项用房」、grad_subsidy[0] 提「萧山」
  - 广州（15 条）：南沙/天河/增城/黄埔...；佛山（12 条）：三水/高明...；丽水（12 条）：莲都/经开区...
- **维度 desc 无范围标注**：杭州市级 desc 全是「毕业生补贴（按学历）」等通用描述，看不出市/区
- **Phase 29 已实证风险**：杭州钱塘区 E类 30万 曾误算进本科档污染 ranking（已修）
- **结论**：区级政策**采集到了但没结构化**，用户无法区分市/区，也无法按区筛选

## 待确认决策（T1 · AskUserQuestion）
区级政策的处理口径存在多个关键歧义，必须先确认：
1. **覆盖范围**：仅杭州试点，还是全 32 城铺开？
2. **呈现方式**：
   - A. 加 `district` 字段 + 页面加「市/区」筛选器（市级/区级混排可切）
   - B. 每个区独立成「城市」条目（杭州→杭州、杭州·余杭、杭州·萧山…）→ 城市数爆炸
   - C. 市级为主，区级只作补充信息挂对应维度（不参与评分）
   - D. 新增「区级政策」独立维度（类比 anju_highlevel，仅查阅）
3. **是否参与排名**：区级政策金额是否计入城市总榜？
4. **搜索方法**：要方法论（写进 SKILL.md）还是要实际执行联网采集？

## 任务
- **T1** AskUserQuestion 确认区级政策口径（覆盖/呈现/排名/方法）
- **T2** 写 README.md 项目定位文件（项目介绍 + 功能定位 + 数据口径 + 使用方法）
- **T3** 清理进度文件 + 任务清单：删除已完成且不重要的任务条目
- **T4** 按 T1 确认口径执行区级政策方案（数据建模 + 渲染 + 校验）
- **T5** 回归四件套 + 技能同步 + 更新进度文件

## 验收指标
- AC38a README.md 存在且涵盖：项目是什么/解决什么问题/数据来源与口径/12 维定义/文件结构/使用方法
- AC38b 进度文件已清理（旧任务删除，当前任务状态准确）
- AC38c 区级政策按确认口径落地（待 T1）
- AC38d 回归四件套全 PASS（若改动数据/渲染）
- AC38e SKILL.md 同步区级政策采集与合并方法

---

## Phase 38 执行结果（2026-09-08 已完成）

### 决策回顾（AskUserQuestion）
- 覆盖：先杭州试点并同步技能方法论，用户同意后再用技能铺开 32 城
- 呈现：加 `district` 字段 + 市/区筛选器
- 评分：区级政策不参与排名（仅查阅）

### 任务完成状态
- T1 ✅ 三处决策已确认
- T2 ✅ README.md 已写（项目定位/功能定位/数据口径/文件结构/使用方法/已知缺口）
- T3 ✅ 进度文件 + 任务清单已清理（删 64 旧任务；本轮 4 主任务 + 子任务已结）
- T4 ✅ 区级政策落地：T4a 补 district 字段 / T4b 联网补采 101 条区级 + 合并 / T4c 市/区筛选器渲染
- T5 ✅ 回归五件套全 PASS + SKILL.md Phase 38 段 + 进度文件更新

### 验收对照
- AC38a ✅ README.md 涵盖全部要素
- AC38b ✅ 任务清单已清理（仅留 Phase 38 主任务，已全 completed）
- AC38c ✅ 区级政策按确认口径落地（district 字段 + 筛选器，不参与排名）
- AC38d ✅ 回归五件套全 PASS（compliance 0/0/0 · multi 11/11 · redesign ALL · jsdom 18/18 + 11/11 · meta_blind 高危=0）
- AC38e ✅ SKILL.md Phase 38 段含采集/合并/渲染/回归/32 城铺开方法论

### 下一步（待用户确认）
- 用户查看杭州试点效果 → 同意后执行 32 城铺开（复用 `_annotate_district.py` + `_merge_district_data.py` + 4 组并行子 Agent 模板）

---

# Phase 39 · 萧山死链修复 + 滨江去重 + 现金原话 + 区内排名（2026-09-08 发起）

## 用户指令（原文）
1. 萧山区 PDF `https://www.xiaoshan.gov.cn/module/download/downfile.jsp?classid=0&filename=2f9245f62c34458192a7311ac9e52fdd.pdf` → not found（死链修复）
2. 滨江区的和杭州的是一样的，重复了（去重）
3. 每个政策加上原文关于现金的简短原话，不超过 10 个字（新字段 `cash_quote`）
4. 市里面各个区的政策右上角加个序号，同样用以该市下面所有区排名（区内排名徽标）
5. 给出新版 + 更新方法论（SKILL.md）
6. 先做计划写进进度文件，再执行，执行后更新进度文件，已完成且不重要任务可删除

## 调查结论（执行前已确认）
- 萧山死链：4 条 `grad_subsidy`（博士/硕士/本科双一流/本科其他）引用该 PDF，已 404。
- 滨江：10 条，金额与市级大体一致（生活补贴 1/3/10 万等），但标题措辞不同（"本科"vs"普通本科"）、anju_highlevel 用 A–E 类（市级另一套分类）。是否全移除待确认。
- 数据结构：区级条目含 `district` 字段；金额在 `cash/house_voucher/subsidy/discount/detail`。

## 任务（T1–T5）
- **T1 萧山死链修复**：联网检索萧山区官方现行毕业生补贴文件，替换 4 条 grad_subsidy 的 `source.url`（须 *.gov.cn 可核验）。
- **T2 滨江去重**：按确认范围移除重复条目（全移除 / 仅去重同标题同金额），保留 市级。
- **T3 新增 `cash_quote`**：逐条派生 ≤10 字现金原话（cash/house_voucher/subsidy/discount/detail 优先，否则 note 提取，否则空）。
- **T4 区内排名 + 序号徽标**：每市计算各区力度分（按确认口径），区降序排名，序号徽标显示在区级条目标签右上角。
- **T5 重建 + 回归五件套 + SKILL.md 方法论更新 + 进度文件更新**。

## 待确认（AskUserQuestion）
- Q1 区内排名口径：3 维（毕业生+租房+购房，同 32 城默认）/ 4 维（加创业）/ 2 维（仅现金）
- Q2 滨江去重范围：全移除 / 仅去重
- Q3 cash_quote 生成：从结构化现金字段派生（快速）/ 重抓原文（准确但慢）

## 验收
- AC39a 萧山 4 条链接可用（非 404，*.gov.cn）
- AC39b 滨江重复条目已清理（按确认范围）
- AC39c 每条政策含 `cash_quote`（≤10 字）
- AC39d 区级序号徽标正确渲染且对应区内排名
- AC39e 回归五件套全 PASS（compliance 0/0/0 · multi 11/11 · redesign ALL · jsdom 18/18 + district 11/11 · meta_blind 高危=0）
- AC39f SKILL.md 同步 Phase 39 方法论

## Phase 39 执行结果（2026-09-08 已完成）

### 决策回顾（AskUserQuestion）
- Q1 区内排名口径 = 2 维现金（grad_subsidy + anju_subsidy），本科口径（与城市总榜"全部≡本科"一致）
- Q2 滨江去重 = 全移除（10 条与市级冗余）
- Q3 cash_quote = 从结构化现金字段**派生**（不重抓 136 URL；`cash` 本即政策原文逐字转录）

### 任务完成状态
- T1 ✅ 萧山 4 条 grad_subsidy 死链替换为 zj.gov.cn OSS 同文件镜像（curl 实测 HTTP 200，文件名一致，通过 *.gov.cn 合规）
- T2 ✅ 删除全部 10 条滨江区条目（杭州 136 → 126 条）
- T3 ✅ 新增 `cashQuote(it)`：从 `[cash,house_voucher,subsidy,discount,detail,note]` 派生 ≤10 字现金原话，每行标题下渲染「…」（前端派生，永不失步）
- T4 ✅ 计算 `DISTRICT_RANK[city]={district:{rank,score}}`（2 维现金·本科口径），注入 JS；区级标签右上角圆形序号徽标 `.dist-rank`
- T5 ✅ 重建 HTML（1.34MB，1236 条，32 城×12 维）+ 回归五件套全 PASS + SKILL.md Phase 39 段 + 本段

### 验收对照
- AC39a ✅ 萧山 4 条链接可用（非 404，*.gov.cn）；旧 xiaoshan downfile 死链在 HTML 中 0 命中
- AC39b ✅ 滨江重复条目已清理（全移除 10 条）
- AC39c ✅ 每条政策含 cash_quote（≤10 字，前端派生自原文现金字段）
- AC39d ✅ 区级序号徽标正确渲染且对应区内排名（杭州：萧山#1 13.0万 → … → 钱塘#9 0.0）
- AC39e ✅ 回归五件套全 PASS（compliance 0/0/0 · multi 11/11 · redesign ALL · jsdom 18/18 + district 11/11 · meta_blind 高危=0）
- AC39f ✅ SKILL.md 同步 Phase 39 方法论（含死链修复范式 + cash_quote 派生决策 + 区内排名口径 + 批量 Edit 静默丢编辑 pitfalls）

### 踩坑（重要经验）
- **批量 Edit 静默丢编辑**：同消息 6 个 Edit，部分（追加新行类）未落盘但回报 Success；重建后发现 dist-rank/cash-quote 等标记为 0，grep 才暴露。对策：多 Edit 后逐一 Grep 确认关键字符串落盘，缺失逐个重放（单条 Edit 可靠）。

### 下一步
- 用户查看杭州试点新版（死链修复 + 滨江去重 + 现金原话 + 区内排名徽标）→ 同意后按 Phase 38 方法论铺开 32 城

---

# Phase 40 · 区级政策铺开 32 城（2026-09-08 发起，用户已同意）

## 用户指令（原文）
> 同意，按已固化的方法论铺开 32 城

## 铺开范围与口径（继承 Phase 38/39 已确认决策）
- 每城：既有条目补 `district` 字段（P1 URL 域名 > P2 name+unit 文本 > P3 市级兜底）+ 按区检索合并区级政策
- 区级仅查阅、不参与排名（`_rankable_items` 防护栏不变）；区内排名徽标口径 = 2 维现金·本科（Phase 39）
- **东莞、中山不设区（直筒子市）→ 不检索区级，全部标市级**
- 硬规则：来源仅 *.gov.cn 且现行有效；普适口径；某区无独立政策则跳过不编造

## 区县清单（29 城检索 / 2 城跳过 / 杭州已完成）
- 浙江 10：宁波(10区县) 温州(12) 嘉兴(7) 湖州(5) 绍兴(6) 金华(9) 衢州(6) 舟山(4) 台州(9) 丽水(9)
- 广东 19：广州(11) 深圳(10) 珠海(3) 汕头(7) 佛山(5) 韶关(10) 湛江(9) 肇庆(8) 江门(7) 茂名(5) 惠州(5) 梅州(8) 汕尾(4) 河源(6) 阳江(4) 清远(8) 潮州(3) 揭阳(5) 云浮(5)
- 跳过：东莞、中山（不设区）

## 任务
- **T0 准备**：备份 `_bak_20260908_phase40/` + 评分快照 before（`_score_snapshot.py`）
- **T1 全库 district 标注**：泛化 `_annotate_district.py`（31 城 DISTRICTS 表 + 保守 P1 域名表 + --all），跑全量
- **T2 区级检索**：并行子代理（每城 1 个，5 城一波，共 6 波 / 29 城），输出 `_district_raw/{py}_districts.json`（格式同 Phase 38：`{city, districts:[{district, policies:[{dim,level,cash,house_voucher,condition,note,source}]}]}`）
  - 每区 ≤4 条、每城 ≤20 条，优先 grad_subsidy / anju_subsidy / welfare
- **T3 合并泛化**：`_merge_district_data.py` 加 --city/--py/--target(zj|gd)，按 `{py}*.json` 匹配文件；分省合并
- **T4 重建 + 回归五件套**（浙江批后一次、广东批后一次）+ meta_blind 高危=0
- **T5 评分快照 after + diff 报告**（区级排除导致的 city 分变化逐条核对——预期合理：区级本不该计入）
- **T6 SKILL.md Phase 40 段 + task_plan/progress/memory 更新 + 交付**

## 验收指标
- AC40a 32 城（除东莞/中山）全部有 district 标注；杭州不变
- AC40b 29 城区级原始文件落盘 `_district_raw/`（允许部分城为空——无独立区级政策）
- AC40c 合并后仅 *.gov.cn 条目入库；重跑幂等（指纹去重）
- AC40d 回归五件套全 PASS × 2（浙江批 / 广东批）；meta_blind 高危=0
- AC40e 评分 diff 逐条核对（区级排除导致的降分合理、无区级误标市级漏网）
- AC40f SKILL.md 同步铺开方法论 + 实测数据

## Phase 40 执行进度（2026-09-08 晚，进行中——429 配额中断）

### 已完成
- T0 ✅ 备份 `_bak_20260908_phase40/`（23 份）+ 评分快照 before
- T1 ✅ 全库 district 标注：31 城 1095 条（`_annotate_district_all.py`）。实证修正 3 个判定坑：P1 URL 优先导致区县网站转载市级文件误判（嘉兴 xiuzhou、揭阳 huilai）→ 改「P2 严格主体判定优先 + 市级主体确证禁用 P1」；unit 实存 `source.unit`；联合发文「、」分隔县名在末尾 → 区名须在前 14 字或紧邻市名
- T2 第 1 波 ✅ 浙江 5 城 74 条（宁波13/温州20/嘉兴18/湖州13/绍兴10）；第 2–6 波（24 城）**因 429 配额中断**（09-09 01:17 重置），简报+区县清单+固定动作已落盘 `_phase40_pending_briefs.md`
- T3 ✅ 合并脚本泛化 `_merge_district_data_v2.py`（--batch + GD 维度重映射 talent_highlevel + 指纹幂等）；第 1 波合并新增 53 条（去重 21），浙江 487→528
- T4 ✅ 重建 HTML 1.405MB + 回归五件套全 PASS（D11 断言两次修正：宁波→东莞、东莞需先切广东页签）
- T5 ✅ 评分 diff 33 处逐条核对**全合理**：区级污染为全库存量问题（此前仅杭州清过），宁波 anju 16/20/40→0、广州 grad 3/6/12→0（实为南沙区金额）、湖州/绍兴/佛山/肇庆/嘉兴同口径排除；总榜排名整体下移重排为预期行为

## Phase 40 执行进度（2026-09-09 21:45，✅ 全部完成）
### 本轮（09-09 晚）新增完成
- 佛山补采 ✅：禅城2/高明4（首轮）+ 顺德4（补采，顺峰人才计划；南海/三水区级体系已失效且官方确认，按宁缺毋滥弃采）
- 第 4 波 ✅（lite 模型子代理）：韶关12/湛江6/肇庆8/江门16/茂名7 → 合并新增 44 条（广东 781→827）
- 第 5 波 ✅：惠州17/梅州4/汕尾2/河源5/阳江6 → 合并新增 27 条（827→858 区间）
- 第 6 波 ✅：清远10/潮州1/揭阳11/云浮12 → 合并新增 26 条（广东终值 878）
- **429 应对实证：子代理默认模型 429 时用 `model: "lite"` 全部跑通且质量合格**（韶关 12 条含 2 份扫描 PDF 逐页核对）

### 终验
- 全库 1391 条（浙江 558 + 广东 878 + 其他），区级条目 414，**30/32 城有区级数据**（东莞/中山直筒子市=空，正确）
- 回归五件套终验全 PASS：compliance 0/0/0 · multi 11/11 · redesign ALL · jsdom multi 18/18 + district 11/11 · meta_blind 高危=0
- 评分快照 diff（before vs final）：33 处 / 7 城，全部为区级排除降分（广州 grad 南沙存量污染清除、宁波/湖州/绍兴/嘉兴/肇庆/佛山同因），新并入区级条目 0 参与城市排名——防护栏口径全库一致
- HTML 终版 1.55MB（1552538 bytes），32 城 × 12 维

### AC40 全达成
- AC40a 全库 district 标注（31 城 1095 条，严格主体判定）✅
- AC40b 30/32 城区级政策采集入库（东莞/中山不设区正确跳过）✅
- AC40c 每批合并幂等去重 + 不合规 0 ✅
- AC40d 每批回归五件套全 PASS ✅
- AC40e 评分 diff 逐条核对（33 处全合理）✅
- AC40f SKILL.md 终版 + 簿记更新 + 交付 ✅

## Phase 41b · 学历行迁移 + 双口径拆分（09-19，✅ 完成）
- 用户指令：学历行移到「统计维度」之后；统计维度随学历筛选变更、默认本科；范围决策=B 仅总榜默认本科，处理=A 纯移动
- 实施：#eduFilter 移入 rank-ctrl（统计维度行后）；拆分双口径——boardEdu（页首学历行→总榜/城市徽标/对比排名行，默认本科）与 eduFilter（抽屉/对比学历行→表格条目过滤，默认全部）
- 关键发现：评分语义「全部档≡本科档」（Phase 29 既定，无本科档不向下兜底）→ 默认本科与全部的总榜数字一致，学历对总榜的实际影响在切专科/硕士/博士时体现；M17b 断言按此语义修正（全部≡本科一致 + 硕士≠全部）
- 回归：jsdom multi 22/22（新增 M17b/M17b2/M17c/M17d）· district 11/11 · Python 五件套 PASS · 评分口径零改动

## Phase 42 执行结果（09-20，✅ 本地部分完成）
- T1 ✅ personal-portal 仓库（D:/AI/project/IdeaCreate/personal-portal）：Editorial Ink 门户 index.html（卡片：/hub/ + /talent-policy/ + 预留虚线位）+ release.sh + README + main 首提交
- T2 ✅ hub：Sidebar 入口已撤销；vite base='/hub/'；public/talent-policy 已删；release.sh 就位；重建后 dist 资源路径 /hub/assets/... 验证通过
- T3 ✅ 政策仓库 git init（main=源码+脚本，.gitignore 排除 _bak_*/.workbuddy/pdf/txt）；release.sh 就位
- T4 ✅ 本地三合一组装（_site_preview）：/ 门户 · /hub/ · /talent-policy/ 全 200，hub 资源 /hub/assets/ 200，4400 端口预览中
- 发布脚本实证修复 2 个坑：①相对路径 remote 在 _deploy 子目录解析错位 → URL 统一绝对化（SCRIPT_DIR 拼接）；②沙箱/Windows 环境 find 解析成 FIND.EXE → 镜像逻辑改纯 bash 内建（dotglob 循环）
- 三个脚本均通过逻辑验证（https URL 原样传递、产物树正确、幂等跳过正常）；实际 push 待用户建 GitHub 仓库后首跑
- ⏭ 用户待办：GitHub 建 2 个新仓库（personal-portal、talent-policy-atlas）→ 本地 push main → 各跑 release.sh → 服务器一次性初始化 + cron（命令文本见交付说明）

## Phase 42b · 子站「返回首页」入口（10-13，✅ 完成）
- 用户指令：给每个子网站添加返回首页的按钮。四项决策：①hub 嵌进 Sidebar 顶部 ②政策页固定悬浮左上角 ③各自适配本站风格 ④仅从门户进入时显示
- 来路判定（两站同一套语义）：`sessionStorage['portal-entry']` → 同源 referrer 且 pathname 为 `/` 或 `/index.html`；非同源 / `origin==='null'`(file://) / 直接输入地址 一律不显示。sessionStorage 按标签页隔离，新标签直接开子站不会误显示，同时兼容子站内刷新
- hub：新增 `src/components/BackToPortal.tsx`（ArrowLeft + mono 微字 + accent 悬停，Editorial Ink 同色系），挂在 Sidebar `<aside>` 顶部；另在 `loadError` 分支单独渲染（该分支不渲染 Sidebar，否则用户被困错误页）
- 政策页：`_build_html.py` 加 `.portal-back`（fixed top:14px/left:20px，z-index:60 高于吸顶工具栏 z-index:30）+ `<body>` 首个元素 + 来路判定 IIFE；生成 1,564,303 bytes
- **顺带修掉真实 Bug**：hub `fetch('/data/agents.json')`、`fetch('/data/trending.json')` 为绝对路径，部署到 `/hub/` 下会 404 并整页进「数据加载失败」。改为 `` fetch(`${import.meta.env.BASE_URL}data/...`) ``，实测请求变为 `/hub/data/agents.json`、`/hub/data/trending.json`
- 回归：compliance 0/0/0 · multi 11/11 · redesign ALL PASS · jsdom multi 22/22 · district 11/11（政策页改动零副作用）
- **端到端验证（真实 Edge + playwright）12/12 PASS**：直接访问 /hub/ 按钮不可见·数据正常渲染·数据请求全带 /hub/ 前缀；门户→hub 按钮可见 href=/ → 点击回门户；直接访问 /talent-policy/ 不可见；门户→政策页可见且坐落 (20,14) → 滚动后仍可见 → 点击回门户
- 新增脚本：`personal-portal/_test_portal_back.js`（端到端回归，12 断言）、`_shot_portal_back.js`（三处截图，输出 `_shots/`）
- 预览服务：`python -m http.server 4410 --bind 127.0.0.1`（docroot = personal-portal/_site_preview）

## Phase 42c · 部署 SOP 文档（10-14，✅ 完成）
- 用户指令：做一份「项目文件上传 Git 仓库 + 宝塔部署上线」的 SOP，HTML 格式，联网搜索教程并为步骤标注来源
- 产出：`personal-portal/docs/DEPLOY_SOP.html`（86.6 KB 自包含单文件，17 章节，固定 TOC + 滚动高亮 + 代码复制按钮 + 4 类 callout + 响应式 + 打印样式）
- 来源：18 项，正文 16 处 `[n]` 上标引用，文末按「官方文档 [1]-[7] / 社区教程 [8]-[18]」分组索引并注明各自用于哪几章
- 检索带来的 6 处实质性修正（非单纯找链接）：①`--force-with-lease` 与 cron 后台 fetch 冲突（git 官方文档）→ 确认 `release.sh` 用 `--force` 正确 ②Deploy Key 不能跨仓库复用 → 3 仓库须 3 把密钥 + config 别名 ③宝塔 cron 以 www 用户运行/环境极窄/默认 cwd 为 /root/必须绝对路径 ④known_hosts 必须预写否则 cron 卡在 yes/no ⑤try_files 子目录兜底须写 `/hub/index.html`，写错会返回门户首页（比 404 更难查）⑥强制 HTTPS 会导致证书续期失败
- 顺带防护：`personal-portal/.gitignore` 加 `hub/`、`talent-policy/`（服务器上门户仓库在站点根、两子站点是其子目录，忽略后 reset/clean 不会误删）；README 补「文档」「服务器目录结构」两节
- 校验：新增 `_check_sop.js`（playwright 真实 Edge + file:// 直开）→ 11/11 PASS（无 JS 报错 · 17 锚点全命中 · 来源引用双向一致 · 编号 1..18 无断号 · 35 代码块复制按钮实测可用）
- 技术坑记录：Chromium `getComputedStyle(el,'::before').content` 不解析 `counter()`；CSS counter 不受 `<ol start>` 影响需 `counter-reset: s 7` 续编

## Phase 43 · 主站+多子站目录结构与自动部署（10-22，✅ 本地部分完成）
- 用户提供完整方案文档（1 主站 + 暂定 6 子站、独立仓库、同域路径、releases+软链接、GitHub Actions rsync）
- **四项决策**：①全面切到新方案，废弃 release.sh + 服务器 cron ②沿用现有代号 `hub`/`talent-policy`，预留 4 个位凑满 6 ③政策仓库瘦身重建，前提「功能不变」 ④域名/服务器先用占位符
- **方案与现状的 3 处冲突**：①部署机制互斥（实体目录 vs 软链接，同路径不能共存）②命名前缀不一致（方案用 `site-*`，实际是 `hub`/`talent-policy`，主站 `--exclude site-*` 规则失效）③政策仓库已提交 183.5MB 其中 139.7MB 是视频，与「媒体不入 Git」原则冲突
- **读方案发现的 4 个坑，落地时全部修掉**：①`ln -sfn` 遇实体目录会钻进去建链接（旧内容继续服务且看似成功；旧方案切新方案首次部署必然触发）②cleanup 按 mtime 排序不可靠（rsync 会改 mtime）+ 并发竞态 → 改目录名字典序（UTC 时间戳）+ flock ③主站 rsync 的 `--exclude site-*` 匹配不到现有代号 → 显式列出 ④主站不走 releases 且不加 `--delete` → 回滚不彻底（已在文档标注为已知限制）
- **产出**：`D:/AI/project/IdeaCreate/my-sites/`
  - `README.md` 总规范；`docs/01-占位符替换清单.md`（8 个文件逐条）、`02-迁移与运维.md`、`03-上线检查清单.md`、`04-决策记录.md`（D1–D8）
  - `main-site/`（index.html 改造为 sites.json 驱动 + sites.json 6 个位置 + favicon.svg + deploy.yml + README）
  - `shared/`（css/base.css + deploy.yml + README）、`server/`（init/rollback/cleanup.sh + README）、`_templates/deploy-subsite.yml`、`_media/`
  - 两个子站仓库各加 `.github/workflows/deploy.yml`（hub 7 步 / talent-policy 7 步，均含构建产物验收）
- **政策仓库瘦身**：`mv .git _bak_git_20261022`（316MB 保留）→ 重写 .gitignore → 重建 → commit
  - 183.5MB → **7.29MB / 198 文件**；`.git` 316MB → **8.8MB**（size-pack 1.63MiB）
  - 排除 `_video_build/`(158.8MB)、`images/`(19.5MB)、`_tmp_repos/`(35.9MB)、`_bak*`、`*.pdf`
  - **构建可复现性验证**：瘦身前基准 MD5 `ae9864945deb918722d56092828cdf8f` → 重建后重跑 `_build_html.py` 仍为同值，1,564,303 bytes / 32 城，逐字节一致
  - 同步改 `_validate_redesign.py` AC8：历史 11 城配图改为「存在才校验」，适配媒体不入库
  - **发现**：`_validate_redesign.py` 第 5 行校验的是 `浙江人才引进政策_2026.html`（387KB 旧版单省页，有 2 个 img），不是当前 32 城产物；且硬编码 `D:\beifen\...` 绝对路径，CI 里跑不了 → 属历史脚本，当前有效验证集是另外四项
- **回归**：compliance 0/0/0 PASS · multi 全 ✅ · redesign ALL PASS · jsdom multi 22/22 · district 11/11
- **主站渲染验证（真实 Edge + playwright）12/12 PASS**：6 张卡（2 live + 4 预留）、live 在前、路径标签一致、无 JS 错误、375px 单列
  - 过程中修掉两个自己引入的 bug：①基础卡片样式写在 `a.card` 上，预留位是 `<div>` 拿不到 flex/padding，`justify-content` 对 block 无效 → 改 `.card` ②`.card p{flex:1}` 被子元素继承把预留卡正文撑满、文字顶到上沿 → `.card.ghost p{flex:0 0 auto}`
  - 加 `favicon.svg` 消除浏览器自动请求 `/favicon.ico` 的 404
- **产物校验**：5 个 YAML 全部解析通过（主站 5 步 / shared 4 步 / 模板 6 步 / hub 7 步 / 政策 7 步）；3 个 shell 脚本 `bash -n` 通过；8 个文件均为纯 LF（`grep -c $'\r'` 在 Git Bash 下会匹配字面 r，属误报，须用二进制计数复核）
- ⏭ 用户待执行：确认域名/服务器信息 → 替换 8 处 `SITE_ROOT` 占位 → 建 4 仓库配 Secrets → 按 docs/02 迁移 → 停旧 cron
