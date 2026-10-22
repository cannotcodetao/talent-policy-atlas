# -*- coding: utf-8 -*-
# Phase 38 T4b：把 _district_raw/*.json 的区级政策合并进源头数据
#
# 数据来源：4 个并行检索子代理产出的杭州 13 区县官方政策（全部 *.gov.cn）
# 目标：zhejiang-talent-data.json 的杭州对象，各维度新增区级条目（带 district 字段）
#
# 硬规则：
#   - 只合并 source.url 以 .gov.cn 结尾的条目（带端口的子域也接受，见 ALLOW_PORT_HOSTS）
#   - 每条强制写 district 字段（区名）
#   - 逐维字段映射：子代理统一用 level/cash/condition/note，需按 SCHEMA 重命名
#     （渲染层 titleKey 取 SCHEMA 第一个非空字段，映射错了标题会空白）
#   - 幂等：重复跑不会产生重复条目（按 district + level + cash 指纹去重）
#   - 备份：_bak_YYYYMMDD_phase38/
#
# 用法：
#   python _merge_district_data.py             # 合并（默认杭州）
#   python _merge_district_data.py --dry-run   # 只打印不写

import json, os, re, sys, shutil, glob
from datetime import datetime
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
RAW_DIR = os.path.join(BASE, '_district_raw')

CITY = '杭州'

# 带非标准端口但确属 gov.cn 的子域（人工核实后放行）
ALLOW_PORT_HOSTS = {'larc.linan.gov.cn'}

# ---- 子代理统一字段 → 各维度 SCHEMA 字段映射 ----
# 渲染层 titleKey = SCHEMA 第一个非空字段，故首字段映射决定条目标题
FIELD_MAP = {
    #                level→        cash→          house_voucher→   condition→      note→
    'grad_subsidy':   {'level': 'level',   'cash': 'cash',      'house_voucher': 'house_voucher', 'condition': 'condition', 'note': 'note'},
    'welfare':        {'level': 'type',    'cash': 'detail',    'house_voucher': None,           'condition': 'condition', 'note': 'note'},
    'startup':        {'level': 'type',    'cash': 'detail',    'house_voucher': None,           'condition': 'condition', 'note': 'note'},
    'anju_subsidy':   {'level': 'name',    'cash': 'discount',  'house_voucher': None,           'condition': 'constraint', 'note': 'note'},
    'anju_highlevel': {'level': 'class',   'cash': 'subsidy',   'house_voucher': None,           'condition': 'condition', 'note': 'note'},
}

# welfare/startup/anju_highlevel 的 SCHEMA 不含 condition 字段 → 条件并入 note，避免信息丢失
CONDITION_TO_NOTE_DIMS = {'welfare', 'startup', 'anju_highlevel'}

# ---- 来源 URL 修正（人工核实：子域带端口 → 主站规范页） ----
URL_FIX = {
    'http://larc.linan.gov.cn:8000/a/4074.html':
        'https://www.linan.gov.cn/col/col1229288615/art/2026/art_73e623a9b5c64f79b7403848bf34bd61.html',
}


def host_of(url):
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ''


def is_gov(url):
    if not url:
        return False
    h = host_of(url)
    if not h:
        return False
    bare = h.split(':')[0]
    if bare in ALLOW_PORT_HOSTS:
        return True
    return h.endswith('.gov.cn')


def fingerprint(it):
    """去重指纹：区名 + 标题 + 金额"""
    return (it.get('district', ''),
            str(it.get('name') or it.get('level') or it.get('class') or it.get('type') or ''),
            str(it.get('cash') or it.get('discount') or it.get('subsidy') or it.get('detail') or ''))


def convert(p, district):
    """子代理统一格式 → 目标维度 SCHEMA 格式"""
    dim = p['dim']
    m = FIELD_MAP.get(dim)
    if not m:
        return None
    src = dict(p.get('source') or {})
    url = src.get('url', '')
    if url in URL_FIX:
        url = URL_FIX[url]
        src['url'] = url
    src = {k: (src.get(k) or '') for k in ('unit', 'doc_no', 'date', 'url')}

    out = {'district': district, 'official': True}
    for src_k, dst_k in m.items():
        if dst_k is None:
            continue
        v = p.get(src_k)
        if v:
            out[dst_k] = v
    # condition 在无该字段的维度并入 note
    cond = p.get('condition') or ''
    if dim in CONDITION_TO_NOTE_DIMS and cond:
        note = out.get('note') or ''
        out['note'] = (cond + ('；' if note else '') + note).strip('；')
    out['source'] = src
    return out


def main():
    dry = '--dry-run' in sys.argv

    zj = json.load(open(ZJ, encoding='utf-8'))
    obj = zj[CITY]
    dims = obj['dimensions']

    # 现有指纹（幂等：已合并过的不重复加）
    exist = set()
    for dim, dd in dims.items():
        for it in dd.get('items', []):
            exist.add(fingerprint(it))

    added, skipped_dup, skipped_bad = [], [], []
    for fp in sorted(glob.glob(os.path.join(RAW_DIR, '*.json'))):
        d = json.load(open(fp, encoding='utf-8'))
        for block in d.get('districts', []):
            district = block['district']
            for p in block.get('policies', []):
                dim = p.get('dim')
                url = (p.get('source') or {}).get('url') or ''
                if not is_gov(url):
                    skipped_bad.append((district, dim, url[:70]))
                    continue
                item = convert(p, district)
                if not item:
                    skipped_bad.append((district, dim, f'无映射 dim'))
                    continue
                if fingerprint(item) in exist:
                    skipped_dup.append((district, dim, str(p.get('level'))[:30]))
                    continue
                exist.add(fingerprint(item))
                dims.setdefault(dim, {'desc': '', 'items': []})
                dims[dim]['items'].append(item)
                added.append((district, dim, str(p.get('level'))[:30]))

    print(f'=== 区级政策合并结果（{"DRY-RUN" if dry else "已写入"}）===')
    print(f'\n✅ 新增 {len(added)} 条：')
    from collections import Counter
    c = Counter((a[0]) for a in added)
    for k, v in c.most_common():
        print(f'  {k}: {v} 条')
    print(f'\n  按维度：')
    for k, v in Counter(a[1] for a in added).most_common():
        print(f'    {k}: {v}')
    if skipped_dup:
        print(f'\n⏭  跳过重复 {len(skipped_dup)} 条')
    if skipped_bad:
        print(f'\n❌ 跳过不合规 {len(skipped_bad)} 条：')
        for s in skipped_bad[:10]:
            print(f'    {s}')

    if not dry:
        bak_dir = os.path.join(BASE, f'_bak_{datetime.now():%Y%m%d}_phase38')
        os.makedirs(bak_dir, exist_ok=True)
        bak = os.path.join(bak_dir, f'zhejiang-talent-data.json.pre-merge_{datetime.now():%H%M%S}')
        shutil.copy2(ZJ, bak)
        json.dump(zj, open(ZJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\n备份: {bak}')
        print(f'✅ 已写入 {ZJ}')
        # 分布统计
        cnt = Counter()
        for dim, dd in dims.items():
            for it in dd.get('items', []):
                if it.get('official') is False:
                    continue
                cnt[it.get('district', '(未标注)')] += 1
        print(f'\n=== {CITY} district 分布（合并后）===')
        for k, v in cnt.most_common():
            print(f'  {k}: {v} 条')


if __name__ == '__main__':
    main()
