# -*- coding: utf-8 -*-
"""Phase 34 T1 验证：广州 grad 重构前后评分逐档对比。

改前数据取自备份 guangdong_raw/guangzhou.json.bak_20260906
改后数据取自 guangdong_raw/guangzhou.json
用 exec 注入 _build_html.py 头部复用评分函数（Phase 33 技巧）。
"""
import json, sys, re

sys.stdout.reconfigure(encoding='utf-8')
src = open('_build_html.py', encoding='utf-8').read()
lines = src.split('\n')
cut = len(lines)
for i, ln in enumerate(lines):
    if re.match(r'^TEMPLATE\s*=\s*r?[\'"]', ln):
        cut = i
        break
g = {'__file__': '_build_html.py', '__name__': '__verify__'}
_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    exec(compile('\n'.join(lines[:cut]), '_build_html.py', 'exec'), g)
finally:
    sys.argv = _argv

city_dim_score = g['city_dim_score']
_grad_item_wan = g['_grad_item_wan']

old = json.load(open('guangdong_raw/guangzhou.json.bak_20260906', encoding='utf-8'))
new = json.load(open('guangdong_raw/guangzhou.json', encoding='utf-8'))

print('=== 广州 grad_subsidy 维度评分 ===')
o = city_dim_score(old, 'grad_subsidy')
n = city_dim_score(new, 'grad_subsidy')
print(f'  改前: {o}')
print(f'  改后: {n}')
print(f'  结论: {"✅ 不变" if abs((o or 0)-(n or 0)) < 1e-9 else "⚠️ 变化 " + str(round((n or 0)-(o or 0), 4))}')

print()
print('=== 分档逐条评分明细 ===')
def detail(d, tag):
    print(f'  --- {tag} ---')
    for i, it in enumerate(d['dimensions']['grad_subsidy']['items']):
        s = _grad_item_wan(it)
        lv = it.get('level', '')
        if s and s > 0:
            print(f'    [{i}] {lv}: {s} 万   cash={str(it.get("cash",""))[:60]}')
    print()

detail(old, '改前（12 条）')
detail(new, '改后（4 条）')

# 目标值校验
targets = {'本科档维度分': 3.0}
print('=== 哨兵校验 ===')
print(f'  广州 grad 维度分目标 3.0（本科档）: 实际 {n} -> {"✅" if abs((n or 0)-3.0) < 1e-9 else "❌"}')

# 其它维度不受影响
print()
print('=== 其它维度评分（应完全不变）===')
for dim in ['hukou', 'welfare', 'anju_subsidy', 'startup', 'apply_path']:
    a = city_dim_score(old, dim)
    b = city_dim_score(new, dim)
    flag = '✅' if abs((a or 0)-(b or 0)) < 1e-9 else '⚠️'
    print(f'  {dim}: {a} -> {b}  {flag}')
