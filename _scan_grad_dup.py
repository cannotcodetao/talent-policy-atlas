# -*- coding: utf-8 -*-
"""Phase 34 调研：grad_subsidy 维度两类数据质量问题全量扫描。
1. 跨维度污染：cash/house_voucher 字段含「购房补贴/购房」关键词（应归 anju 维度）
2. 同档重复条目：同一 level 出现多条，且含无金额条（无 cash 无 house_voucher 或金额为 0）
"""
import json, sys, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

BUY_KW = ['购房补贴', '购房总额', '购房款', '房票', '购房']
AMT_RE = re.compile(r'(\d+(?:\.\d+)?)\s*(?:万元|万|元)')

def has_amount(s):
    return bool(AMT_RE.search(str(s or '')))

print('=== 问题1: grad_subsidy 条目 cash/house_voucher 含购房关键词（跨维度污染）===')
p1 = []
for c, cd in cities.items():
    for i, it in enumerate(cd['dimensions']['grad_subsidy'].get('items', [])):
        for fld in ('cash', 'house_voucher'):
            v = str(it.get(fld, '') or '')
            if any(k in v for k in BUY_KW):
                p1.append((c, i, fld, it.get('level', ''), v[:90]))
for c, i, fld, lv, v in p1:
    print(f'  {c} grad[{i}] [{lv}] {fld}: {v}')
print(f'  合计 {len(p1)} 处')

print()
print('=== 问题2: 同一 level 多条 + 无金额条（同档重复拆条）===')
p2 = []
for c, cd in cities.items():
    items = cd['dimensions']['grad_subsidy'].get('items', [])
    by_lv = defaultdict(list)
    for i, it in enumerate(items):
        by_lv[it.get('level', '')].append((i, it))
    for lv, lst in by_lv.items():
        if len(lst) >= 2:
            empties = [(i, it) for i, it in lst
                       if not has_amount(it.get('cash', '')) and not has_amount(it.get('house_voucher', ''))]
            if empties:
                p2.append((c, lv, len(lst), len(empties),
                           [(i, str(it.get('cash', '') or it.get('house_voucher', ''))[:50]) for i, it in lst]))
for c, lv, n, ne, lst in p2:
    print(f'  {c} [{lv}] 共{n}条 其中{ne}条无金额:')
    for i, v in lst:
        print(f'      grad[{i}]: {v}')
print(f'  合计 {len(p2)} 城')

print()
print('=== 统计: 每城 grad_subsidy 条目数 + 同 level 最多条数 ===')
for c, cd in cities.items():
    items = cd['dimensions']['grad_subsidy'].get('items', [])
    by_lv = defaultdict(int)
    for it in items:
        by_lv[it.get('level', '')] += 1
    maxn = max(by_lv.values()) if by_lv else 0
    if maxn >= 3 or len(items) >= 8:
        print(f'  {c}: 共{len(items)}条 各档={dict(by_lv)}')
