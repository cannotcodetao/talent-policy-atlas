# -*- coding: utf-8 -*-
# Phase 40 T3：区级政策合并脚本（多城泛化版，替代 Phase 38 杭州专用 _merge_district_data.py）
#
# 数据来源：_district_raw/{py}_districts.json（并行检索子代理产出）
# 目标：
#   浙江 → zhejiang-talent-data.json[城市]
#   广东 → guangdong_raw/{py}.json（注意：高层次维度写源头用旧名 talent_highlevel，
#          _build_combined_data.py 合并时映射回 anju_highlevel）
#
# 硬规则（继承 Phase 38）：
#   - 只合并 source.url 以 .gov.cn 结尾的条目（ALLOW_PORT_HOSTS 白名单例外）
#   - 每条强制 district 字段；指纹幂等去重；备份后再写
#
# 用法：
#   python _merge_district_data_v2.py --city 宁波            # 单城合并
#   python _merge_district_data_v2.py --city 宁波 --dry-run  # 只打印
#   python _merge_district_data_v2.py --batch 宁波,温州,…    # 多城批量

import json, os, re, sys, shutil, glob
from datetime import datetime
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
GD_DIR = os.path.join(BASE, 'guangdong_raw')
RAW_DIR = os.path.join(BASE, '_district_raw')

ZJ_CITY_PY = {
    '杭州': 'hangzhou', '宁波': 'ningbo', '温州': 'wenzhou', '嘉兴': 'jiaxing',
    '湖州': 'huzhou', '绍兴': 'shaoxing', '金华': 'jinhua', '衢州': 'quzhou',
    '舟山': 'zhoushan', '台州': 'taizhou', '丽水': 'lishui',
}
GD_CITY_PY = {
    '广州': 'guangzhou', '深圳': 'shenzhen', '珠海': 'zhuhai', '汕头': 'shantou',
    '佛山': 'foshan', '韶关': 'shaoguan', '湛江': 'zhanjiang', '肇庆': 'zhaoqing',
    '江门': 'jiangmen', '茂名': 'maoming', '惠州': 'huizhou', '梅州': 'meizhou',
    '汕尾': 'shanwei', '河源': 'heyuan', '阳江': 'yangjiang', '清远': 'qingyuan',
    '东莞': 'dongguan', '中山': 'zhongshan', '潮州': 'chaozhou', '揭阳': 'jieyang',
    '云浮': 'yunfu',
}

ALLOW_PORT_HOSTS = {'larc.linan.gov.cn', 'ssdj.shengsi.gov.cn'}

# 子代理统一字段 → 各维度 SCHEMA 字段映射（titleKey = SCHEMA 第一个非空字段）
FIELD_MAP = {
    'grad_subsidy':   {'level': 'level',   'cash': 'cash',     'house_voucher': 'house_voucher', 'condition': 'condition', 'note': 'note'},
    'welfare':        {'level': 'type',    'cash': 'detail',   'house_voucher': None,            'condition': 'condition', 'note': 'note'},
    'startup':        {'level': 'type',    'cash': 'detail',   'house_voucher': None,            'condition': 'condition', 'note': 'note'},
    'anju_subsidy':   {'level': 'name',    'cash': 'discount', 'house_voucher': None,            'condition': 'constraint', 'note': 'note'},
    'anju_highlevel': {'level': 'class',   'cash': 'subsidy',  'house_voucher': None,            'condition': 'condition', 'note': 'note'},
}
CONDITION_TO_NOTE_DIMS = {'welfare', 'startup', 'anju_highlevel'}
# 广东源头高层次维度用旧名（_build_combined_data.py 映射回 anju_highlevel）
GD_DIM_REMAP = {'anju_highlevel': 'talent_highlevel'}


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
    return (it.get('district', ''),
            str(it.get('name') or it.get('level') or it.get('class') or it.get('type') or ''),
            str(it.get('cash') or it.get('discount') or it.get('subsidy') or it.get('detail') or ''))


def convert(p, district):
    dim = p.get('dim')
    m = FIELD_MAP.get(dim)
    if not m:
        return None
    src = dict(p.get('source') or {})
    url = src.get('url', '')
    src = {k: (src.get(k) or '') for k in ('unit', 'doc_no', 'date', 'url')}
    out = {'district': district, 'official': True}
    for src_k, dst_k in m.items():
        if dst_k is None:
            continue
        v = p.get(src_k)
        if v:
            out[dst_k] = v
    cond = p.get('condition') or ''
    if dim in CONDITION_TO_NOTE_DIMS and cond:
        note = out.get('note') or ''
        out['note'] = (cond + ('；' if note else '') + note).strip('；')
    out['source'] = src
    return out, dim


def merge_city(city, dry):
    py = ZJ_CITY_PY.get(city) or GD_CITY_PY.get(city)
    if not py:
        print(f'❌ 未知城市 {city}')
        return
    target_gd = city in GD_CITY_PY
    files = sorted(glob.glob(os.path.join(RAW_DIR, f'{py}_*.json')))
    if not files:
        print(f'  {city}: 无原始文件（{py}_*.json），跳过')
        return

    if target_gd:
        src_fp = os.path.join(GD_DIR, f'{py}.json')
        obj = json.load(open(src_fp, encoding='utf-8'))
    else:
        src_fp = ZJ
        zj_all = json.load(open(ZJ, encoding='utf-8'))
        obj = zj_all[city]

    dims = obj['dimensions']
    exist = set()
    for dim, dd in dims.items():
        for it in dd.get('items', []):
            exist.add(fingerprint(it))

    added, skipped_dup, skipped_bad = [], [], []
    for fp in files:
        try:
            d = json.load(open(fp, encoding='utf-8'))
        except Exception as e:
            print(f'  ❌ {os.path.basename(fp)} JSON 解析失败: {e}')
            continue
        for block in d.get('districts', []):
            district = block.get('district') or ''
            if not district or district == '市级':
                continue
            for p in block.get('policies', []):
                url = (p.get('source') or {}).get('url') or ''
                conv = convert(p, district)
                if not conv:
                    skipped_bad.append((district, p.get('dim'), '无映射 dim'))
                    continue
                item, dim = conv
                if not is_gov(url):
                    skipped_bad.append((district, dim, url[:70]))
                    continue
                if target_gd and dim in GD_DIM_REMAP:
                    dim = GD_DIM_REMAP[dim]
                if fingerprint(item) in exist:
                    skipped_dup.append((district, dim, str(p.get('level'))[:30]))
                    continue
                exist.add(fingerprint(item))
                dims.setdefault(dim, {'desc': '', 'items': []})
                dims[dim]['items'].append(item)
                added.append((district, dim, str(p.get('level'))[:30]))

    from collections import Counter
    print(f'  {city}: 新增 {len(added)} · 重复跳过 {len(skipped_dup)} · 不合规跳过 {len(skipped_bad)}')
    for k, v in Counter(a[0] for a in added).most_common():
        print(f'      {k}: {v}')
    if skipped_bad:
        for s in skipped_bad[:5]:
            print(f'      ❌ {s}')

    if not dry and added:
        bak_dir = os.path.join(BASE, '_bak_20260908_phase40')
        os.makedirs(bak_dir, exist_ok=True)
        stamp = f'{datetime.now():%H%M%S}'
        if target_gd:
            shutil.copy2(src_fp, os.path.join(bak_dir, f'gd_{py}.json.pre-merge_{stamp}'))
            json.dump(obj, open(src_fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        else:
            shutil.copy2(src_fp, os.path.join(bak_dir, 'zhejiang-talent-data.json.pre-merge_' + stamp))
            json.dump(zj_all, open(ZJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    dry = '--dry-run' in sys.argv
    cities = []
    if '--batch' in sys.argv:
        cities = [c.strip() for c in sys.argv[sys.argv.index('--batch') + 1].split(',') if c.strip()]
    elif '--city' in sys.argv:
        cities = [sys.argv[sys.argv.index('--city') + 1]]
    else:
        print('用法: --city X | --batch A,B,C [--dry-run]')
        sys.exit(1)
    print(f'=== 区级政策合并（{"DRY-RUN" if dry else "写入"}）{len(cities)} 城 ===')
    for c in cities:
        merge_city(c, dry)


if __name__ == '__main__':
    main()
