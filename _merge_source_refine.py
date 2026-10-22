# -*- coding: utf-8 -*-
"""Phase 41 T3：来源细粒度核验结果合并。

读取 _source_refine/results/{py}.json（子代理产出，key → {title,doc_no,date,effective,unit,dead_link}），
按 key 精确匹配源数据条目，只增改 source 的 5 个字段（title/doc_no/date/effective/unit），
绝不触碰业务字段（cash/discount/detail/note/condition 等）。

用法：
  python _merge_source_refine.py --batch 杭州,宁波 [--dry-run]
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REFINE_DIR = ROOT / '_source_refine' / 'results'
PY2FILE = {
    '杭州': 'zhejiang-talent-data.json', '宁波': 'zhejiang-talent-data.json',
    '温州': 'zhejiang-talent-data.json', '嘉兴': 'zhejiang-talent-data.json',
    '湖州': 'zhejiang-talent-data.json', '绍兴': 'zhejiang-talent-data.json',
    '金华': 'zhejiang-talent-data.json', '衢州': 'zhejiang-talent-data.json',
    '舟山': 'zhejiang-talent-data.json', '台州': 'zhejiang-talent-data.json',
    '丽水': 'zhejiang-talent-data.json',
}
GD_DIMS = {'grad_subsidy', 'anju_subsidy', 'welfare', 'anju_highlevel'}
UPDATABLE = ('title', 'doc_no', 'date', 'effective', 'unit')


def entry_key(city, dim, it):
    name = str(it.get('name') or it.get('level') or it.get('class') or it.get('type')
               or it.get('item') or it.get('platform') or '')
    main = str(it.get('cash') or it.get('discount') or it.get('subsidy') or it.get('detail') or '')
    return '|'.join([city, dim, it.get('district', ''), name, main[:60]])


def load_results(pinyin):
    fp = REFINE_DIR / f'{pinyin}.json'
    if not fp.exists():
        return None
    data = json.load(open(fp, encoding='utf-8'))
    return data.get('results', data) if isinstance(data, dict) else data


def refine_obj(city, obj, results, dry):
    """返回 (匹配数, 更新数, 未匹配 keys)。"""
    matched = updated = 0
    unmatched = []
    for dim, dd in obj.get('dimensions', {}).items():
        for it in dd.get('items', []):
            if it.get('official') is False:
                continue
            key = entry_key(city, dim, it)
            rec = results.get(key)
            if rec is None:
                continue
            matched += 1
            src = it.get('source')
            if not isinstance(src, dict):
                src = {}
                it['source'] = src
            changed = []
            for f in UPDATABLE:
                v = rec.get(f)
                if v is None or str(v).strip() == '':
                    continue  # 空值不写，不覆盖既有
                if str(src.get(f, '')) != str(v):
                    if not dry:
                        src[f] = str(v)
                    changed.append(f'{f}:{str(src.get(f, ""))[:14]!r}→{str(v)[:24]!r}')
            if rec.get('dead_link'):
                print(f'    [死链待查] {key[:60]}')
            if changed:
                updated += 1
                nm = str(it.get('name') or it.get('level') or it.get('class') or it.get('type') or '')[:22]
                print(f'    [{dim}] {nm} ｜ ' + ' ； '.join(changed))
    used = set()
    for dim, dd in obj.get('dimensions', {}).items():
        for it in dd.get('items', []):
            if it.get('official') is False:
                continue
            used.add(entry_key(city, dim, it))
    unmatched = [k[:60] for k in results if k not in used]
    return matched, updated, unmatched


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', required=True, help='逗号分隔城市名')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    cities = [c.strip() for c in args.batch.split(',') if c.strip()]

    # 城市名 → 拼音（简报文件名即拼音）
    briefs = {fp.stem: fp for fp in (ROOT / '_source_refine' / 'briefs').glob('*.json')}
    city2py = {}
    for fp in briefs.values():
        data = json.load(open(fp, encoding='utf-8'))
        city2py[data['city']] = fp.stem

    zj = json.load(open(ROOT / 'zhejiang-talent-data.json', encoding='utf-8'))
    gd_cache = {}

    for city in cities:
        py = city2py.get(city)
        if not py:
            print(f'{city}: ⚠️ 无简报文件，跳过')
            continue
        results = load_results(py)
        if not results:
            print(f'{city}: ⚠️ 无核验结果 _source_refine/results/{py}.json，跳过')
            continue
        print(f'=== {city}（{len(results)} 条核验记录）===')
        if city in zj and isinstance(zj[city], dict) and 'dimensions' in zj[city]:
            obj = zj[city]
        else:
            gfp = ROOT / 'guangdong_raw' / f'{py}.json'
            if not gfp.exists():
                print(f'{city}: ❌ 找不到源文件')
                continue
            if py not in gd_cache:
                gd_cache[py] = json.load(open(gfp, encoding='utf-8'))
            obj = gd_cache[py]
        matched, updated, unmatched = refine_obj(city, obj, results, args.dry_run)
        print(f'  匹配 {matched} ｜ 更新 {updated} ｜ 未匹配结果 {len(unmatched)}')
        if unmatched:
            for k in unmatched[:5]:
                print(f'    [未匹配] {k}')

    if args.dry_run:
        print('\n[dry-run] 未写盘')
        return
    shutil.copy2(ROOT / 'zhejiang-talent-data.json',
                 ROOT / f'_bak_20260919_phase41/zhejiang-talent-data.json.pre_refine')
    json.dump(zj, open(ROOT / 'zhejiang-talent-data.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    for py, obj in gd_cache.items():
        shutil.copy2(ROOT / 'guangdong_raw' / f'{py}.json',
                     ROOT / f'_bak_20260919_phase41/gd_{py}.json.pre_refine')
        json.dump(obj, open(ROOT / 'guangdong_raw' / f'{py}.json', 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=2)
    print('\n✅ 已写盘（备份于 _bak_20260919_phase41/）')


if __name__ == '__main__':
    main()
