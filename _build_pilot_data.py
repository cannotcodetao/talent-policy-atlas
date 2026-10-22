# -*- coding: utf-8 -*-
# 先导数据构建：合并 anju_raw/{city}.json 到主数据，输出 3 城 pilot 数据文件。
# 含红线剔除：纯租赁（只租不售/纯租赁/租赁型）、非人才定向（中低收入困难家庭）不计入优惠购房。
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, 'anju_raw')
MAIN = os.path.join(BASE, 'zhejiang-talent-data.json')
OUT = os.path.join(BASE, 'zhejiang-talent-data-pilot.json')

ANJU_DIMS = ['anju_rent2sale', 'anju_discount', 'anju_subsidy', 'anju_shared', 'anju_enterprise']
ANJU_LABEL = {'anju_rent2sale': '先租后售人才房', 'anju_discount': '定向优惠价购房',
              'anju_subsidy': '人才购房补贴/房票', 'anju_shared': '共有产权房', 'anju_enterprise': '企业内部福利房'}
# 红线剔除：仅剔除"本身"为纯租赁 / 非人才定向的条目（按名称精确否定，避免整段文字误命中）
DENY_NAMES = ['杭州市人才专项租赁住房', '越城区共同富裕安居工程']
PILOT = ['杭州', '宁波', '绍兴']
PINYIN = {'杭州': 'hangzhou', '宁波': 'ningbo', '绍兴': 'shaoxing'}

main = json.load(open(MAIN, encoding='utf-8'))
# 仅取先导 3 城，保留其既有引才维度
pilot = {'meta': {'citiesDone': PILOT, 'updated': '2026-08-19'}, 'coverage': {}}
for c in PILOT:
    pilot[c] = main[c]

for c in PILOT:
    raw = json.load(open(os.path.join(RAW, f'{PINYIN[c]}.json'), encoding='utf-8'))
    dims = {d: [] for d in ANJU_DIMS}
    excluded = []
    for p in raw['policies']:
        if any(dk in p.get('name', '') for dk in DENY_NAMES):
            excluded.append(p.get('name', ''))
            continue
        mode = p.get('mode')
        if mode in dims:
            dims[mode].append(p)
    # 空维度补「暂未查询到官方公开政策」占位（official=false，不编造）
    for d in ANJU_DIMS:
        if not dims[d]:
            dims[d] = [{
                'mode': d, 'mode_label': ANJU_LABEL[d], 'name': '暂未查询到官方公开政策',
                'unit': '', 'effective': '', 'expiry': '', 'project': '', 'rent_years': '',
                'price_base': '', 'rent_deduct': '', 'biz_req': '', 'person_req': '',
                'discount': '', 'constraint': '', 'channel': '', 'enterprise_only': '',
                'official': False,
                'source': {'unit': '', 'doc_no': '', 'date': '', 'url': ''},
                'note': '本次检索（住建/房管/园区管委会/国资平台官网）未找到该模式的人才定向官方公开政策。'
            }]
    # 写入该城 dimensions
    if 'dimensions' not in pilot[c]:
        pilot[c]['dimensions'] = {}
    for d in ANJU_DIMS:
        pilot[c]['dimensions'][d] = {'items': dims[d]}
    pilot['coverage'][c] = {'excluded': excluded, 'note': raw.get('coverage_note', '')}

json.dump(pilot, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('写入:', OUT)
for c in PILOT:
    cnt = {d: len(pilot[c]['dimensions'][d]['items']) for d in ANJU_DIMS}
    print(f"  {c}: 安居维度条目数={cnt} | 红线剔除={pilot['coverage'][c]['excluded']}")
