# -*- coding: utf-8 -*-
"""Phase 34 精确扫描：区分 grad_subsidy 三类情况。

列定义（_build_html.py:919）：grad_subsidy = 学历 | 现金(cash) | 房票(house_voucher) | 条件 | 备注
语义：cash=现金类补贴，house_voucher=房票/购房补贴类。

- A 类【真重复】cash 与 house_voucher 同时含购房/房票关键词 → 同一笔写两遍
- B 类【错置】  仅 cash 含购房关键词（house_voucher 为否定/空）→ 购房补贴错放进现金列
- C 类【正常】  仅 house_voucher 含购房关键词 → 字段本义，不修
"""
import json, sys, re
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

BUY_KW = ['购房补贴', '购房补助', '购房总额', '购房款', '房票', '购房']
# 否定表述：说明本档没有购房补贴，不是「把购房补贴写进现金列」
NEG_PAT = re.compile(r'(无|未|暂|没有|停止|取消|详见|见\s*anju|不)', re.I)

def has_kw(s):
    s = str(s or '')
    return any(k in s for k in BUY_KW)

A, B, C = [], [], []
for c, cd in cities.items():
    for i, it in enumerate(cd['dimensions']['grad_subsidy'].get('items', [])):
        cash = str(it.get('cash', '') or '')
        hv = str(it.get('house_voucher', '') or '')
        ck, hk = has_kw(cash), has_kw(hv)
        lv = it.get('level', '')
        if ck and hk:
            A.append((c, i, lv, cash, hv))
        elif ck and not hk:
            B.append((c, i, lv, cash, hv))
        elif hk and not ck:
            C.append((c, i, lv, hv))

def show(tag, rows, n=100):
    print(f'=== {tag}  共 {len(rows)} 处 ===')
    for c, i, lv, cash, hv in rows:
        print(f'  {c} grad[{i}] [{lv}]')
        print(f'      cash : {cash[:110]}')
        print(f'      hv   : {hv[:110]}')
    print()

show('A 类【真重复】cash 与 house_voucher 同时含购房关键词（同一笔写两遍）', A)
show('B 类【错置】仅 cash 含购房关键词（购房补贴放进现金列）', B)
print(f'=== C 类【正常】仅 house_voucher 含购房关键词：共 {len(C)} 处（字段本义，不修）===')
by_city = defaultdict(int)
for c, i, lv, hv in C:
    by_city[c] += 1
print('  分布:', dict(by_city))
print()

print('=== 问题2 补充：grad_subsidy 中 cash 和 house_voucher 全空的条目 ===')
tot = 0
for c, cd in cities.items():
    for i, it in enumerate(cd['dimensions']['grad_subsidy'].get('items', [])):
        cash = str(it.get('cash', '') or '').strip()
        hv = str(it.get('house_voucher', '') or '').strip()
        if not cash and not hv:
            tot += 1
            cond = str(it.get('condition', '') or '')[:80]
            note = str(it.get('note', '') or '')[:80]
            print(f'  {c} grad[{i}] [{it.get("level","")}] cond={cond}')
            print(f'      note={note}')
print(f'  合计 {tot} 条')
