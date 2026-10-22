# -*- coding: utf-8 -*-
"""Phase 34 诊断：定位广州合并后本科/博士归零的根因。"""
import json, sys, re

sys.stdout.reconfigure(encoding='utf-8')
src = open('_build_html.py', encoding='utf-8').read()
lines = src.split('\n')
cut = len(lines)
for i, ln in enumerate(lines):
    if re.match(r'^TEMPLATE\s*=\s*r?[\'"]', ln):
        cut = i
        break
g = {'__file__': '_build_html.py', '__name__': '__diag__'}
_argv = sys.argv
sys.argv = sys.argv[:1]
try:
    exec(compile('\n'.join(lines[:cut]), '_build_html.py', 'exec'), g)
finally:
    sys.argv = _argv

_item_non_univ = g['_item_non_univ']
NON_UNIV_NEAR = g['NON_UNIV_NEAR']
NON_UNIV_ITEM_RE = g['NON_UNIV_ITEM_RE']
NON_UNIV_RE = g['NON_UNIV_RE']
_grad_item_wan = g['_grad_item_wan']

def scan_hits(text, tag):
    if not text:
        return
    hits = [k for k in NON_UNIV_NEAR if k in text]
    hits_re = [r.pattern for r in NON_UNIV_RE if r.search(text)]
    hits_item = [r.pattern for r in NON_UNIV_ITEM_RE if r.search(text)]
    if hits or hits_re or hits_item:
        print(f'    [{tag}] 命中: NEAR={hits} RE={hits_re} ITEM_RE={hits_item}')

for tag, path in [('改前', 'guangdong_raw/guangzhou.json.bak_20260906'),
                  ('改后', 'guangdong_raw/guangzhou.json')]:
    d = json.load(open(path, encoding='utf-8'))
    print(f'########## {tag} ##########')
    for i, it in enumerate(d['dimensions']['grad_subsidy']['items']):
        lv = it.get('level', '')
        s = _grad_item_wan(it)
        nonuniv = _item_non_univ(it)
        print(f'  [{i}] {lv}: _grad_item_wan={s}  _item_non_univ={nonuniv}')
        if nonuniv or (not s):
            for f in ('condition', 'note', 'cash', 'house_voucher'):
                scan_hits(str(it.get(f, '') or ''), f)
    print()
