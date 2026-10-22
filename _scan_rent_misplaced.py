# -*- coding: utf-8 -*-
"""Phase 35 T2 调研：租房补贴跨维度错位全城扫描。

问题定义：grad_subsidy 的 cash 含「租房补贴」字样（按 _RENT_ONLY_KW 规则
grad 计分时被排除，呈现却在毕业生补贴现金列），而 welfare 维度无对应租房现金条目
→ 租房补贴两头都没计分、用户在「租房补贴」维度找不到。

扫描两类：
- P1：grad cash 含租房关键词（有金额）且 welfare=0（该学历档）→ 完全丢失
- P2：grad cash 含租房关键词（有金额）且 welfare>0 → 需人工核对是否同一笔
"""
import json, sys, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
src = open('_build_html.py', encoding='utf-8').read()
lines = src.split('\n')
cut = len(lines)
for i, ln in enumerate(lines):
    if re.match(r'^TEMPLATE\s*=\s*r?[\'"]', ln):
        cut = i
        break
g = {'__file__': '_build_html.py', '__name__': '__scan__'}
_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    exec(compile('\n'.join(lines[:cut]), '_build_html.py', 'exec'), g)
finally:
    sys.argv = _argv

city_dim_score = g['city_dim_score']
RENT_KW = ['租房补贴', '房租补贴', '租赁补贴', '租房']
AMT = re.compile(r'\d+(?:\.\d+)?')

d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

def lvl_key(lv):
    lv = str(lv or '')
    if '博士' in lv: return '博士'
    if '硕士' in lv: return '硕士'
    if '专科' in lv or '大专' in lv: return '专科'
    if '本科' in lv: return '本科'
    return '?'

print('=== welfare 维度条目结构参考（有租房现金条目的城市）===')
# welfare 评分靠什么字段
for c in ['金华', '湖州', '丽水']:
    items = cities[c]['dimensions']['welfare'].get('items', [])
    print(f'--- {c} welfare {len(items)} 条, score={city_dim_score(cities[c], "welfare", None, c)}')
    for i, it in enumerate(items):
        t = str(it.get('type', ''))[:20]
        det = str(it.get('detail', ''))[:90]
        print(f'    [{i}] type={t} | detail={det}')

print()
print('=== P1/P2 扫描：grad cash 含租房关键词 ===')
for c, cd in sorted(cities.items()):
    for i, it in enumerate(cd['dimensions']['grad_subsidy'].get('items', [])):
        cash = str(it.get('cash', '') or '')
        if not any(k in cash for k in RENT_KW):
            continue
        if not AMT.search(cash):
            continue
        lk = lvl_key(it.get('level'))
        w = city_dim_score(cd, 'welfare', lk, c)
        tag = 'P1 完全丢失' if (w or 0) == 0 else 'P2 需核对'
        print(f'  {tag}: {c} grad[{i}][{it.get("level","")}] welfare[{lk}]={w}')
        print(f'      cash: {cash[:110]}')
