# -*- coding: utf-8 -*-
"""模拟：租房补贴按政策标注的最长月数累计（而非固定年化12个月）对各城评分的影响。"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(BASE, '_build_html.py'), encoding='utf-8').read().split('\n')
head = '\n'.join(src[:533])
g = {'__name__': '__sim__', '__file__': os.path.join(BASE, '_build_html.py')}
sys.argv = sys.argv[:1]
exec(compile(head, '_head', 'exec'), g)

cds = g['RANK_SCORES_BY_EDU']; allc = g['_allcities']; RANK_DIMS = g['RANK_DIMS']
_MONTHLY = re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*月')
_DUR_M = re.compile(r'(?:最长|不超过|最多|累计不超过|期限)[^，。；]{0,8}?(\d+)\s*个?月')
_DUR_Y = re.compile(r'(?:最长|不超过|最多|累计不超过|期限)[^，。；]{0,8}?(\d+)\s*年')

def max_months(txt):
    n = 12
    for m in _DUR_M.finditer(txt):
        n = max(n, int(m.group(1)))
    for m in _DUR_Y.finditer(txt):
        n = max(n, int(m.group(1)) * 12)
    return min(n, 60)

print('=== 影响面：welfare 维度「元/月」条目按期限累计后的变化 ===')
rows = []
for c in allc:
    old = {e: cds[e]['welfare'][c] for e in ['专科', '本科', '硕士', '博士']}
    new = dict(old)
    for it in allc[c]['dimensions'].get('welfare', {}).get('items', []) or []:
        txt = str(it.get('detail', '') or '')
        ms = list(_MONTHLY.finditer(txt))
        if not ms:
            continue
        n = max_months(txt)
        if n <= 12:
            continue
        for e in ['专科', '本科', '硕士', '博士']:
            one = g['_welfare_rent_wan'](txt, e, it)
            if one > 0:
                new[e] = max(new[e], round(one * n / 12, 3))
    if any(new[e] != old[e] for e in old):
        rows.append((c, old, new))
for c, old, new in sorted(rows, key=lambda x: -(sum(x[2].values()) - sum(x[1].values()))):
    print(f'  {c:4s} 旧=' + ' '.join(f'{e}{old[e]}' for e in old) +
          ' → 新=' + ' '.join(f'{e}{new[e]}' for e in new) +
          f'  Δ本科={round(new["本科"]-old["本科"],2)}')
print(f'  涉及 {len(rows)} 城')

print('\n=== 本科档总额 TOP10（修复前 → 修复后）===')
def total(c, e, welfare_override=None):
    s = 0
    for dim in RANK_DIMS:
        v = welfare_override if (dim == 'welfare' and welfare_override is not None) else cds[e][dim][c]
        s += v
    return round(s, 2)
ovmap = {c: new for c, old, new in rows}
before = {c: total(c, '本科') for c in allc}
after = {c: total(c, '本科', ovmap.get(c, {}).get('本科')) for c in allc}
for c in sorted(allc, key=lambda x: -after[x])[:12]:
    print(f'  {c:4s} {before[c]:8.2f} → {after[c]:8.2f}')
