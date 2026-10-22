# -*- coding: utf-8 -*-
"""Phase 32：全量来源 URL 可达性扫描（必须带浏览器 UA，无 UA 会被政府站反爬误判 403/412）。"""
import json, sys, re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, build_opener
from urllib.error import HTTPError, URLError

sys.stdout.reconfigure(encoding='utf-8')
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'

d = json.load(open('talent-data.json', encoding='utf-8'))
cities = {}
for p in d['meta']['provinces']:
    cities.update(d[p['key']])

# 递归收集所有 source.url（含 note 中列出的备用 URL 不算，只收 source.url 字段）
url_map = {}   # url -> [(city, dim, doc_no)]
def collect(city, dim, items):
    for it in items or []:
        src = it.get('source') or {}
        u = str(src.get('url') or '').strip()
        if u.startswith('http'):
            url_map.setdefault(u, []).append((city, dim, str(src.get('doc_no') or '')[:40]))
for c, cd in cities.items():
    for dim, dv in cd['dimensions'].items():
        collect(c, dim, dv.get('items'))

print(f'共 {len(cities)} 城，去重后 {len(url_map)} 个来源 URL')
results = {}   # url -> (status, note)

def check(url):
    op = build_opener()
    op.addheaders = [('User-Agent', UA), ('Accept', 'text/html,application/xhtml+xml,*/*;q=0.8')]
    op.timeout = 20
    try:
        r = op.open(url)
        body = r.read(600).decode('utf-8', 'ignore') if r.status == 200 else ''
        anti = any(k in body for k in ['真人', '验证您', '安全验证', '请开启 JavaScript', 'captcha', 'Checking your browser'])
        return url, r.status, ('anti-bot' if anti else 'ok')
    except HTTPError as e:
        return url, e.code, 'http-error'
    except URLError as e:
        return url, 0, f'conn-fail({str(e.reason)[:30]})'
    except Exception as e:
        return url, -1, f'err({str(e)[:30]})'

with ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(check, u) for u in url_map]
    for i, f in enumerate(as_completed(futs), 1):
        u, st, note = f.result()
        results[u] = (st, note)
        if i % 50 == 0:
            print(f'  进度 {i}/{len(url_map)}')

ok    = [u for u, (s, n) in results.items() if s == 200 and n == 'ok']
anti  = [u for u, (s, n) in results.items() if s == 200 and n == 'anti-bot']
bad   = {u: (s, n) for u, (s, n) in results.items() if not (s == 200 and n in ('ok', 'anti-bot'))}

print(f'\n=== 汇总 ===')
print(f'  200 正常      : {len(ok)}')
print(f'  200 但反爬页  : {len(anti)}（无法机器判定，需人工浏览器复核）')
print(f'  异常          : {len(bad)}')
print('\n=== 异常 URL 明细 ===')
for u, (s, n) in sorted(bad.items(), key=lambda x: -(x[1][0] if isinstance(x[1][0], int) else 999)):
    cites = url_map[u]
    cs = ','.join(sorted({f'{c}/{dim}' for c, dim, _ in cites}))
    print(f'  [{s or n}] {u}')
    print(f'        引用: {cs} ({len(cites)}处)')

json.dump({'results': {u: list(v) for u, v in results.items()},
           'url_map': url_map},
          open('_url_scan_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n结果已存 _url_scan_result.json')
