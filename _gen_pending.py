# -*- coding: utf-8 -*-
# 缺口追踪：扫描 talent-data.json，把所有「全为占位（official=False）」的 (城市, 维度)
# 写成 待检索清单.md，供下次定时更新时重点检索。属可复现步骤，纳入技能 pipeline。
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'talent-data.json')
OUT = os.path.join(BASE, '待检索清单.md')

# 维度中文名（与生成器 DIM_LABEL 对齐）
DIM_CN = {
    'grad_subsidy':'毕业生补贴','talent_highlevel':'高层次人才','hukou':'落户','startup':'创业扶持',
    'welfare':'配套保障','apply_path':'申报路径','anju_rent2sale':'先租后售人才房',
    'anju_discount':'定向优惠价购房','anju_subsidy':'人才购房补贴/房票','anju_enterprise':'企业内部福利房',
    'timing':'时效提醒','risk':'风险提示'
}

d = json.load(open(DATA, encoding='utf-8'))
gaps = []  # (prov_name, city, dim)
for p in d['meta']['provinces']:
    for c, obj in d[p['key']].items():
        for dim, dd in obj['dimensions'].items():
            items = dd.get('items', []) or []
            if items and all(it.get('official') is False for it in items):
                gaps.append((p['name'], c, dim))

# 按省份→城市分组
by_prov = {}
for prov, city, dim in gaps:
    by_prov.setdefault(prov, {}).setdefault(city, []).append(dim)

lines = []
lines.append('# 待检索清单（政策缺口追踪）')
lines.append('')
lines.append(f'> 自动生成于 {datetime.date.today().isoformat()} · 由 `_gen_pending.py` 扫描 `talent-data.json` 得到。')
lines.append('> 下列 (城市, 维度) 在本次检索中**全为占位「暂未查询到官方公开政策」**，页面显示为「暂无」。')
lines.append('> **下次定时更新（每年 6 月 / 1 月）时，应优先重点核查这些缺口**，找到官方文件即补录并移除占位。')
lines.append('')
total = len(gaps)
lines.append(f'## 总计：{total} 处缺口（{len(by_prov.get("浙江",{}))} 城·浙江 / {len(by_prov.get("广东",{}))} 城·广东）')
lines.append('')
for prov in ('浙江','广东'):
    if prov not in by_prov:
        continue
    lines.append(f'## {prov}')
    for city in by_prov[prov]:
        dims = '、'.join(DIM_CN.get(x, x) for x in by_prov[prov][city])
        lines.append(f'- **{city}**：{dims}')
    lines.append('')

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print(f'已写入 {os.path.basename(OUT)} · 缺口 {total} 处')
for prov in ('浙江','广东'):
    if prov in by_prov:
        print(f'  {prov}: {len(by_prov[prov])} 城')
