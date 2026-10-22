# -*- coding: utf-8 -*-
"""Phase 34 预验证：模拟「从 cash 剥离购房补贴分句」后，评分是否变化。

用 exec 注入 _build_html.py 头部复用评分函数（Phase 33 技巧）。
三坑：补 __file__、sys.argv 剥参数、动态定位 TEMPLATE = r 行。
"""
import json, sys, re, io, copy

sys.stdout.reconfigure(encoding='utf-8')
src = open('_build_html.py', encoding='utf-8').read()
lines = src.split('\n')
# 动态定位 TEMPLATE = r''' 起始行，只取其上的头部（函数定义部分）
cut = len(lines)
for i, ln in enumerate(lines):
    if re.match(r'^TEMPLATE\s*=\s*r?[\'"]', ln):
        cut = i
        break
head = '\n'.join(lines[:cut])
g = {'__file__': '_build_html.py', '__name__': '__sim__'}
_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    exec(compile(head, '_build_html.py', 'exec'), g)
finally:
    sys.argv = _argv

city_dim_score = g['city_dim_score']
_grad_item_wan = g.get('_grad_item_wan')

d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

BUY_KW = ['购房补贴', '购房补助', '购房总额', '购房款', '房票', '购房']

def strip_buy(s):
    """把 cash 中描述购房补贴的分句删掉，保留现金/生活/租房类分句。"""
    if not s:
        return s
    parts = re.split(r'[；;。]', str(s))
    keep = [p for p in parts if not any(k in p for k in BUY_KW)]
    out = '；'.join(p.strip() for p in keep if p.strip())
    return out

# 记录变更前后的 grad 维度评分
before, after, changed = {}, {}, []
for c, cd in cities.items():
    items = cd['dimensions']['grad_subsidy'].get('items', [])
    b = city_dim_score(cd, 'grad_subsidy')
    before[c] = b
    new_items = []
    for it in items:
        ni = copy.deepcopy(it)
        cash = str(it.get('cash', '') or '')
        if any(k in cash for k in BUY_KW):
            ni['cash'] = strip_buy(cash)
        new_items.append(ni)
    cd2 = copy.deepcopy(cd)
    cd2['dimensions']['grad_subsidy']['items'] = new_items
    a = city_dim_score(cd2, 'grad_subsidy')
    after[c] = a
    if abs((b or 0) - (a or 0)) > 1e-9:
        changed.append((c, b, a))

print('=== 剥离 cash 中购房补贴分句后，grad_subsidy 评分变化 ===')
if not changed:
    print('  ✅ 无任何城市评分变化（证明购房补贴本就被 _GRAD_NEG 排除）')
else:
    print(f'  ⚠️ {len(changed)} 城评分变化：')
    for c, b, a in changed:
        print(f'    {c}: {b} -> {a}  (diff {round((a or 0)-(b or 0), 4)})')
print()
print('=== 抽样：剥离前后 cash 字段对照（宁波/嘉兴/湖州/金华/舟山）===')
for c in ['宁波', '嘉兴', '湖州', '金华', '舟山']:
    for i, it in enumerate(cities[c]['dimensions']['grad_subsidy'].get('items', [])):
        cash = str(it.get('cash', '') or '')
        if any(k in cash for k in BUY_KW):
            print(f'  {c}[{i}] [{it.get("level","")}]')
            print(f'      原: {cash}')
            print(f'      新: {strip_buy(cash)}')
    print()
