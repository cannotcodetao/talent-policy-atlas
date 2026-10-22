# -*- coding: utf-8 -*-
"""诊断：金华（及全量城市）各学历档·各维度评分明细，定位金额对不上问题。"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
target_arg = sys.argv[1] if len(sys.argv) > 1 else '金华'
sys.argv = sys.argv[:1]   # _build_html 头部用 sys.argv[1] 当数据文件路径，先剥离
src = open(os.path.join(BASE, '_build_html.py'), encoding='utf-8').read().split('\n')
head = '\n'.join(src[:533])
g = {'__name__': '__diag__', '__file__': os.path.join(BASE, '_build_html.py')}
exec(compile(head, '_build_html_head', 'exec'), g)

cds = g['RANK_SCORES_BY_EDU']; allc = g['_allcities']; RANK_DIMS = g['RANK_DIMS']

target = target_arg
print('=== 全量 TOP6（各学历档总额）===')
for edu in ['全部', '专科', '本科', '硕士', '博士']:
    tot = {c: round(sum(cds[edu][dim][c] for dim in RANK_DIMS), 2) for c in allc}
    top = sorted(tot.items(), key=lambda x: -x[1])[:6]
    print(' ', edu, top)

print(f'\n=== {target} 各档各维度 ===')
for edu in ['全部', '专科', '本科', '硕士', '博士']:
    row = {dim: cds[edu][dim][target] for dim in RANK_DIMS}
    print(' ', edu, row, '总=', round(sum(row.values()), 2))

# 逐条目拆解
print(f'\n=== {target} 逐条目拆解 ===')
cd = allc[target]
for dim in RANK_DIMS:
    items = cd['dimensions'].get(dim, {}).get('items', [])
    print(f'\n-- {dim} ({len(items)}条)')
    for i, it in enumerate(items):
        vals = []
        for edu in ['专科', '本科', '硕士', '博士']:
            e = None if edu == '全部' else edu
            try:
                v = g['city_dim_score']({dim: {'items': [it]}} if False else {'dimensions': {dim: {'items': [it]}}}, dim, e, target)
            except Exception as ex:
                v = f'ERR{ex}'
            vals.append(f'{edu}={v}')
        if any(str(x).split('=')[1] not in ('0', '0.0') for x in vals):
            key = it.get('level') or it.get('name') or it.get('type') or ''
            print(f'   [{i}] {str(key)[:30]} | ' + ' '.join(vals))
