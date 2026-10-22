# -*- coding: utf-8 -*-
# 合并构建：把 11 城「安居购房五维」原始研究(anju_raw/{pinyin}.json) 并入
# 既有「引才八维」base(zhejiang-talent-data.json)，输出 13 维全量数据。
# 红线：纯租赁/非人才定向/商品房伪装 → 由采集 agent 已剔除；此处再做 DENY 名单兜底。
import json, os, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, 'zhejiang-talent-data.json')
BAK = os.path.join(BASE, 'zhejiang-talent-data-8dim-backup.json')
RAW = os.path.join(BASE, 'anju_raw')

ANJU_DIMS = ['anju_rent2sale','anju_discount','anju_subsidy','anju_shared','anju_enterprise']
ANJU_LABEL = {
    'anju_rent2sale':'先租后售人才房','anju_discount':'定向优惠价购房',
    'anju_subsidy':'人才购房补贴/房票','anju_shared':'共有产权房','anju_enterprise':'企业内部福利房'
}
FIELDS = ['mode','mode_label','name','unit','effective','expiry','project','rent_years',
          'price_base','rent_deduct','biz_req','person_req','discount','constraint',
          'channel','enterprise_only','official','source','note']
SOURCE_SUB = ['unit','doc_no','date','url']
PINYIN = {'杭州':'hangzhou','宁波':'ningbo','温州':'wenzhou','嘉兴':'jiaxing','湖州':'huzhou',
          '绍兴':'shaoxing','金华':'jinhua','衢州':'quzhou','舟山':'zhoushan','台州':'taizhou','丽水':'lishui'}

# 红线兜底名单（如复查发现某条属纯租赁/非人才定向，加入此处后重跑本脚本即可剔除）
#  substring 匹配：原始 name 含以下片段则整条丢弃
DENY_NAMES = {'杭州市人才专项租赁住房', '越城区共同富裕安居工程'}
# 名称级纯租赁红线（命中即丢弃，不依赖 note 描述）
PURE_RENTAL_KW = ['只租不售', '公租房', '公共租赁', '保障性租赁住房']

def clean_policy(po, dim):
    out = {}
    for f in FIELDS:
        if f == 'source':
            s = po.get('source') or {}
            out['source'] = {k: (s.get(k) or '') for k in SOURCE_SUB}
        else:
            out[f] = po.get(f) or ''
    out['mode'] = dim
    out['mode_label'] = ANJU_LABEL[dim]
    # 字段规范化
    eo = (out.get('enterprise_only') or '').strip()
    if eo not in ('是','部分','否'):
        eo = ''
    out['enterprise_only'] = eo
    if not isinstance(out.get('official'), bool):
        out['official'] = bool(out.get('official'))
    return out

def placeholder(dim, city):
    return {
        'mode': dim, 'mode_label': ANJU_LABEL[dim],
        'name': '暂未查询到官方公开政策', 'unit':'','effective':'','expiry':'','project':'',
        'rent_years':'','price_base':'','rent_deduct':'','biz_req':'','person_req':'',
        'discount':'','constraint':'','channel':'','enterprise_only':'','official': False,
        'source':{'unit':'','doc_no':'','date':'','url':''},
        'note': f'本次检索未发现{city}市级或各区官方发布的「{ANJU_LABEL[dim]}」落地政策；若有更新请以各地最新政府文件及「浙里办」为准。'
    }

def main():
    if not os.path.exists(BAK):
        shutil.copy(SRC, BAK)
        print('已备份原 8 维数据 ->', os.path.basename(BAK))
    d = json.load(open(SRC, encoding='utf-8'))
    cities = d['meta']['citiesDone']
    coverage = {}
    stats = []
    for c in cities:
        py = PINYIN[c]
        rp = os.path.join(RAW, py + '.json')
        by_mode = {dim: [] for dim in ANJU_DIMS}
        cov = {'excluded': [], 'note': ''}
        if os.path.exists(rp):
            raw = json.load(open(rp, encoding='utf-8'))
            cov['excluded'] = raw.get('excluded', []) or []
            cov['note'] = raw.get('coverage_note', '') or ''
            for po in raw.get('policies', []):
                m = po.get('mode')
                nm = (po.get('name') or '').strip()
                if m not in ANJU_DIMS:
                    continue
                if any(dn in nm for dn in DENY_NAMES):
                    continue
                if any(kw in nm for kw in PURE_RENTAL_KW):
                    continue
                by_mode[m].append(clean_policy(po, m))
        # 写回安居维度
        dims = d[c]['dimensions']
        for dim in ANJU_DIMS:
            items = by_mode[dim] if by_mode[dim] else [placeholder(dim, c)]
            dims[dim] = {'desc': ANJU_LABEL[dim], 'items': items}
        coverage[c] = cov
        n = sum(len(v) for v in by_mode.values())
        stats.append((c, n, {dim: len(by_mode[dim]) for dim in ANJU_DIMS}))
    d['coverage'] = coverage
    d['meta']['updated'] = '2026-08-19'
    json.dump(d, open(SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('已写入 13 维全量数据 ->', os.path.basename(SRC))
    print('各城安居政策条数：')
    for c, n, dist in stats:
        print(f'  {c}: 共{n} 条  {dist}')

if __name__ == '__main__':
    main()
