# 网页功能清单与验收记录（浙江人才引进政策_2026.html）

> 测试方式：jsdom 无头 DOM 加载生成的 HTML，执行其内嵌 JS，逐一模拟交互并断言。
> 运行命令（PowerShell）：
> `$env:NODE_PATH="C:/Users/24237/.workbuddy/binaries/node/workspace/node_modules"; & "C:/Program Files/nodejs/node.exe" _test_functions.js`
> 配套结构化校验：`python _validate_redesign.py`（AC1–AC10，全部 PASS）

## 一、功能清单（F1–F8）

| 编号 | 功能 | 入口 / 函数 | 行为 |
|---|---|---|---|
| F1 | 城市索引初始渲染 | `renderIndex('')` | 按字母序渲染 11 城（杭州…丽水），可点击 |
| F2 | 搜索仅按城市名过滤 | `#search` input 事件 → `renderIndex(filter)` | 输入"绍"→仅绍兴；"杭州"→仅杭州；无关词→"未找到匹配城市"；不搜政策内容 |
| F3 | 点击城市 → 居中弹窗单城表格 | `openDrawer(c)` → `cityTableHTML(c)` | 弹出居中模态，内含该城 2 列政策表格（8 维分区标题 + 来源脚注）；风险维红框；标题吸顶、图片随滚动 |
| F4 | 关闭弹窗 | `#dclose` / scrim 点击 → `closeDrawer()` | 收回弹窗 |
| F5 | 对比选择（2–5 城）+ 超量禁用 | `compareBtn`→`renderChips`/`validateCmp` | 选 2–5 城生成按钮可用；选 6 城按钮禁用并提示"最多对比 5 个" |
| F6 | 生成并排对比表 + 最高补贴金色高亮 | `genBtn`→`buildCompareTable(cities)` | 生成固定布局等宽对比表；`grad_subsidy`/`talent_highlevel` 维度给力度最高城市加金色背景（并列同标）；风险维不参与高亮 |
| F7 | 城市主视觉图映射 | `openDrawer` 内 `pinyin(c)` | 非杭州城 → `images/{pinyin小写}.png`；杭州特例 → `images/hangzhou.png`（onerror 回退 `hangzhou_ai.png`） |
| F8 | 来源合规 | 全局 `a[href^=http]` | 全部以 `*.gov.cn` 结尾；无外部脚本/字体/图片 |

## 二、验收结果（20 项断言）

| 项 | 断言 | 结果 |
|---|---|---|
| F1 | 初始索引 11 城 | ✅ PASS (rows=11) |
| F2a | 搜"绍"→仅绍兴 | ✅ PASS (rows=1) |
| F2b | 搜"杭州"→仅杭州 | ✅ PASS (rows=1) |
| F2c | 搜无关词→未找到匹配城市 | ✅ PASS (rows=0, empty=true) |
| F3a | 杭州弹窗打开(on+scrim) | ✅ PASS |
| F3b | 杭州弹窗含 8 维分区表格 | ✅ PASS (sec=8) |
| F3c | 杭州表格来源链接均 *.gov.cn | ✅ PASS (n=26) |
| F3d | 绍兴弹窗含风险红框行 | ✅ PASS |
| F3e | 关闭按钮收回弹窗 | ✅ PASS |
| F7a | 宁波主视觉=images/ningbo.png（小写） | ✅ PASS（修复后） |
| F7b | 杭州主视觉=hangzhou.png（含 onerror 回退） | ✅ PASS |
| F5a | 对比面板打开 | ✅ PASS |
| F5b | 选 2 城→生成按钮可用 | ✅ PASS |
| F5c | 选 6 城→按钮禁用+超量提醒 | ✅ PASS |
| F5d | 回到 5 城→按钮恢复可用 | ✅ PASS |
| F6a | 对比表已生成（≥8 行） | ✅ PASS (rows=9) |
| F6b | 毕业生补贴高亮=衢州（115 万冠军） | ✅ PASS |
| F6c | 高层次人才高亮=宁波（2000 万冠军） | ✅ PASS |
| F6d | 风险行不参与最高补贴高亮 | ✅ PASS |
| F8 | 全页 a[href^=http] 均 *.gov.cn | ✅ PASS (total=26, bad=0) |

**总判定：20/20 PASS ✅**

## 三、测试中发现并修复的问题

- **[BUG-1 已修复] 城市主视觉图路径大小写不一致**：`openDrawer` 用 `pinyin(c)`（首字母大写，如 `Ningbo`）拼图片路径，但磁盘文件为全小写 `ningbo.png`。Windows 大小写不敏感文件系统下可加载，但部署到 Linux/Mac/大小写敏感服务器会破图。已在 `_build_html.py` 改为 `images/${py.toLowerCase()}.png`，重新生成 HTML 后 F7a 通过。
- **[测试代码误报，已修正] F6a 初版断言检查 `#ctable.innerHTML` 是否含 `<table`**，但 `<table>` 元素的 innerHTML 不含自身标签，导致误报 FAIL；改判 `tr` 行数 ≥ 8 后通过。真实渲染与高亮逻辑（F6b–F6d）始终正确。

## 四、结论

既有交付物（浙江人才引进政策_2026.html）功能完整、来源合规、交互正确，可作为后续「安居购房」政策合并展示的基座。
