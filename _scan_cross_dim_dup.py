# -*- coding: utf-8 -*-
"""Phase 34 T3：检查其它城市是否存在与广州同类的「重复」问题。

T3a 跨维度重复：grad_subsidy 与 hukou 维度内容重复（广州式）。
    ⚠️ schema 对齐：hukou 用 target + rule；grad_subsidy 用 level + condition。
    首轮扫描正是因只查 condition 而漏判广州，此处按归一化后的文本做相似度比对。
T3b 同档多条：grad_subsidy 同一 level 出现多条（多政策并列 vs 真重复）。
T3c grad 房票列与 anju_subsidy 是否同一笔购房补贴写了两遍。
"""
import json, sys, re, difflib
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

PUNCT = re.compile(r'[\s，,；;。、（）()：:「」""\'\'—\-\d]+')
def norm(s):
    return PUNCT.sub('', str(s or ''))

def sim(a, b):
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()

print('=== T3a 跨维度重复：grad_subsidy.condition ≈ hukou.rule（相似度 ≥ 0.55）===')
hits_a = []
for c, cd in cities.items():
    grad = cd['dimensions'].get('grad_subsidy', {}).get('items', [])
    huk = cd['dimensions'].get('hukou', {}).get('items', [])
    if not huk:
        continue
    for i, gi in enumerate(grad):
        gc = norm(gi.get('condition', ''))
        if len(gc) < 8:
            continue
        for j, hi in enumerate(huk):
            hr = norm(hi.get('rule', ''))
            if len(hr) < 8:
                continue
            s = sim(gc, hr)
            if s >= 0.55:
                hits_a.append((c, i, gi.get('level', ''), j, hi.get('target', ''), round(s, 3),
                               str(gi.get('condition', ''))[:60], str(hi.get('rule', ''))[:60]))
for c, i, lv, j, tg, s, gc, hr in hits_a:
    print(f'  {c}: grad[{i}]({lv}) ≈ hukou[{j}]({tg})  sim={s}')
    print(f'      grad.cond : {gc}')
    print(f'      hukou.rule: {hr}')
print(f'  合计 {len(hits_a)} 处')
print()

print('=== T3b 同档多条：grad_subsidy 同一 level 出现 ≥2 条 ===')
hits_b = []
for c, cd in cities.items():
    grad = cd['dimensions'].get('grad_subsidy', {}).get('items', [])
    by = defaultdict(list)
    for i, it in enumerate(grad):
        by[str(it.get('level', ''))].append(i)
    for lv, idxs in by.items():
        if len(idxs) >= 2:
            n_amt = sum(1 for i in idxs
                        if re.search(r'\d', str(grad[i].get('cash', '') or '') + str(grad[i].get('house_voucher', '') or '')))
            hits_b.append((c, lv, len(idxs), n_amt))
for c, lv, n, na in sorted(hits_b, key=lambda x: (-x[2], x[0])):
    flag = '⚠️含无金额条' if na < n else '全部有金额'
    print(f'  {c} [{lv}] {n} 条（{na} 条有金额）{flag}')
print(f'  合计 {len(hits_b)} 个城市-档位')
print()

print('=== T3c grad 房票列 与 anju_subsidy 是否同一笔购房补贴写两遍 ===')
AMT = re.compile(r'(\d+(?:\.\d+)?)\s*万')
hits_c = []
for c, cd in cities.items():
    grad = cd['dimensions'].get('grad_subsidy', {}).get('items', [])
    anju = cd['dimensions'].get('anju_subsidy', {}).get('items', [])
    if not anju:
        continue
    anju_txt = norm(' '.join(str(x) for x in anju))
    for i, gi in enumerate(grad):
        hv = str(gi.get('house_voucher', '') or '')
        if not AMT.search(hv):
            continue
        # 提取 grad 房票列里的金额
        for m in AMT.finditer(hv):
            amt = m.group(1)
            # 在 anju 维度全文中找同金额
            if re.search(re.escape(amt) + r'\s*万', ' '.join(
                    str(a.get('cash', '') or '') + ' ' + str(a.get('house_voucher', '') or '')
                    + ' ' + str(a.get('name', '') or '') for a in anju)):
                hits_c.append((c, i, gi.get('level', ''), amt, hv[:70]))
                break
for c, i, lv, amt, hv in hits_c:
    print(f'  {c} grad[{i}]({lv}) 房票 {amt}万 在 anju_subsidy 亦出现: {hv}')
print(f'  合计 {len(hits_c)} 处（注：两维度设计上均记录购房补贴，评分上 grad 已排除购房，不重复计分）')
