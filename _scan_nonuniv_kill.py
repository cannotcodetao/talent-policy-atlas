# -*- coding: utf-8 -*-
"""Phase 34 T3a：扫描全库 grad_subsidy 中「条目级非普适判定导致整条归零」的情况。

重点识别两类误杀：
- P1 并列资格误杀：政策原文是「博士（或特级技师）」这类并列通道，
  学历档本身普适，却因并列了非普适资格被整条排除。
- P2 合并/杂烩污染：一条里既写普适金额又写特定人才类别关键词，
  关键词在 condition/house_voucher 里把整条普适金额一起拖零。

判定逻辑：条目 _item_non_univ=True 且 cash 中确有金额 → 疑似误杀。
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

_item_non_univ = g['_item_non_univ']
_grad_item_wan = g['_grad_item_wan']
NON_UNIV_NEAR = g['NON_UNIV_NEAR']
NON_UNIV_ITEM_RE = g['NON_UNIV_ITEM_RE']
NON_UNIV_RE = g['NON_UNIV_RE']

AMT = re.compile(r'\d+(?:\.\d+)?\s*(?:万元|万)')
# 并列资格标志：括号内「或/和」连接的非学历通道
PARALLEL_RE = re.compile(r'[（(][^）)]{0,30}[或和/][^）)]{0,30}[）)]')

d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

rows = []
for c, cd in cities.items():
    for i, it in enumerate(cd['dimensions']['grad_subsidy'].get('items', [])):
        if not _item_non_univ(it):
            continue
        cash = str(it.get('cash', '') or '')
        hv = str(it.get('house_voucher', '') or '')
        if not (AMT.search(cash) or AMT.search(hv)):
            continue  # 本来就没金额，排除不算误杀
        hits = defaultdict(list)
        for f in ('condition', 'cash', 'house_voucher', 'note'):
            t = str(it.get(f, '') or '')
            if not t:
                continue
            for k in NON_UNIV_NEAR:
                if k in t:
                    hits[f].append(k)
            for r in NON_UNIV_RE:
                if r.search(t):
                    hits[f].append('RE:' + r.pattern)
            for r in NON_UNIV_ITEM_RE:
                if r.search(t):
                    hits[f].append('ITEM:' + r.pattern)
        par = bool(PARALLEL_RE.search(cash) or PARALLEL_RE.search(str(it.get('condition', '') or '')))
        rows.append((c, i, it.get('level', ''), dict(hits), par, cash[:70]))

print(f'=== grad_subsidy 中「非普适整条归零」且含金额：共 {len(rows)} 条 ===')
print()
print('--- P1 疑似并列资格误杀（含括号并列通道）---')
n1 = 0
for c, i, lv, hits, par, cash in rows:
    if par:
        n1 += 1
        print(f'  {c} grad[{i}] [{lv}] hits={hits}')
        print(f'      cash: {cash}')
print(f'  小计 {n1} 条')
print()
print('--- P2 其它含金额却被整条排除 ---')
n2 = 0
for c, i, lv, hits, par, cash in rows:
    if not par:
        n2 += 1
        print(f'  {c} grad[{i}] [{lv}] hits={hits}')
        print(f'      cash: {cash}')
print(f'  小计 {n2} 条')
print()
print('=== 命中词频统计（定位高频误杀词）===')
freq = defaultdict(int)
for c, i, lv, hits, par, cash in rows:
    for f, ks in hits.items():
        for k in set(ks):
            freq[k] += 1
for k, v in sorted(freq.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v} 次')
