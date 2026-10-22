# -*- coding: utf-8 -*-
"""Phase 33 诊断：①租房补贴「最长N个月/年」未计入 → 金额对不上；②全量来源 URL 死链清单。"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(BASE, 'talent-data.json'), encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

_MONTHLY = re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*月')
_DUR_MONTH = re.compile(r'(?:最长|最长不超过|不超过|最多|累计不超过|期限不超过|可享受|享受期限|发放期限|补贴期限|租期|期限)[^，。；]{0,6}?(\d+)\s*个?月')
_DUR_YEAR = re.compile(r'(?:最长|最长不超过|不超过|最多|累计不超过|发放期限|享受期限|补贴期限|期限)[^，。；]{0,6}?(\d+)\s*年')

print('=== ① 租房补贴「按月 × 有期限」但未按期限累计的城市/条目 ===')
hits = []
for c, cd in cities.items():
    for dim in ('welfare', 'grad_subsidy'):
        for it in cd['dimensions'].get(dim, {}).get('items', []) or []:
            txt = ' '.join(str(it.get(k, '') or '') for k in ('detail', 'cash', 'name', 'type'))
            if not _MONTHLY.search(txt):
                continue
            dm = _DUR_MONTH.search(txt)
            dy = _DUR_YEAR.search(txt)
            n = int(dm.group(1)) if dm else (int(dy.group(1)) * 12 if dy else 12)
            if n > 12:
                hits.append((c, dim, n, txt[:120]))
for c, dim, n, t in sorted(hits, key=lambda x: -x[2]):
    print(f'  {c:4s} {dim:13s} {n:3d}月 | {t}')
print(f'  合计 {len(hits)} 条 / 涉及 {len({h[0] for h in hits})} 城')

print('\n=== ② 各城市「元/月」租房条目（不论期限）===')
cnt = 0
for c, cd in cities.items():
    for dim in ('welfare', 'grad_subsidy'):
        for it in cd['dimensions'].get(dim, {}).get('items', []) or []:
            txt = ' '.join(str(it.get(k, '') or '') for k in ('detail', 'cash', 'name', 'type'))
            if _MONTHLY.search(txt):
                cnt += 1
print(f'  共 {cnt} 条')

# ---- URL 死链 ----
print('\n=== ③ 来源 URL 状态（读取 _url_scan_result.json）===')
try:
    r = json.load(open(os.path.join(BASE, '_url_scan_result.json'), encoding='utf-8'))
except FileNotFoundError:
    print('  未找到扫描结果')
    r = None
if r:
    res, um = r['results'], r['url_map']
    bad = {u: v for u, v in res.items() if not (v[0] == 200 and v[1] in ('ok', 'anti-bot'))}
    bycity = {}
    for u, (s, n) in bad.items():
        for c, dim, doc in um[u]:
            bycity.setdefault(c, []).append((s, n, u, dim, doc))
    for c in sorted(bycity):
        print(f'  {c:4s} 异常 {len(bycity[c])} 处')
        for s, n, u, dim, doc in bycity[c][:12]:
            print(f'       [{s}] {n[:26]:26s} {doc[:24]:24s} {u[:95]}')
