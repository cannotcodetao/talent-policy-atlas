# -*- coding: utf-8 -*-
"""评分快照：导出全 32 城 × 4 维度评分（按学历档），供 before/after diff。

用法：python _score_snapshot.py <输出文件>
"""
import json, sys, re

sys.stdout.reconfigure(encoding='utf-8')
out = sys.argv[1] if len(sys.argv) > 1 else '_score_snap.json'

src = open('_build_html.py', encoding='utf-8').read()
lines = src.split('\n')
cut = len(lines)
for i, ln in enumerate(lines):
    if re.match(r'^TEMPLATE\s*=\s*r?[\'"]', ln):
        cut = i
        break
g = {'__file__': '_build_html.py', '__name__': '__snap__'}
_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    exec(compile('\n'.join(lines[:cut]), '_build_html.py', 'exec'), g)
finally:
    sys.argv = _argv

city_dim_score = g['city_dim_score']
RANK_DIMS = g['RANK_DIMS']
EDU_LEVELS = g['EDU_LEVELS']

d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

# 完整复刻 _build_html.py 的 RANK_SCORES_BY_EDU 生成逻辑：
# 必须传 city（UNIV_OVERRIDE 以 (city,dim,edu) 为键），且 edu='全部' → None
snap = {}
for edu in EDU_LEVELS:
    e = None if edu == '全部' else edu
    snap[edu] = {dim: {c: city_dim_score(cities[c], dim, e, c) for c in cities}
                 for dim in RANK_DIMS}

json.dump(snap, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'✅ 快照已存 {out}（{len(EDU_LEVELS)} 学历档 × {len(cities)} 城 × {len(RANK_DIMS)} 维度）')
for edu in EDU_LEVELS:
    top = sorted(cities, key=lambda x: -(snap[edu]['grad_subsidy'][x] or 0))[:5]
    print(f"  [{edu}] grad TOP5: " + '、'.join(f'{c}{snap[edu]["grad_subsidy"][c]}' for c in top))
