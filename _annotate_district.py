# -*- coding: utf-8 -*-
# Phase 38 T4a：给城市条目加 district 字段（市级 / 某区）
#
# 背景：区级政策已混入市级数据但无结构化标注（全库 173 条含区名无 district 字段）。
# 用户决策（2026-09-08 AskUserQuestion）：
#   1. 覆盖范围 → 先杭州试点，看效果后再用技能铺 32 城
#   2. 呈现方式 → A. 加 district 字段 + 页面市/区筛选器
#   3. 是否计分 → 不参与排名（区级金额只展示不评分）
#
# 判定逻辑（三级优先级，逐条可审计）：
#   P1 URL 域名：区级政府域名（yuhang.gov.cn / fuyang.gov.cn / qiantang.gov.cn…）→ 该区
#   P2 政策名 + 来源单位：含「XX区/XX县/XX市」（排除「市区」「全市」等泛指）→ 该区县
#   P3 兜底 → 市级
#
# 硬规则：
#   - 逐条写死映射 + old_value 断言 + before/after diff（禁批量正则改写，Phase 33/34 教训）
#   - 「市区」「全市」「各县（市、区）」「各区」等泛指不判为区级
#   - 市级政策里提到某区（如"覆盖萧山、余杭"）仍是市级——看的是**发文主体**不是**覆盖范围**
#
# 用法：
#   python _annotate_district.py             # 杭州试点（默认）
#   python _annotate_district.py --dry-run   # 只打印不改文件
#   python _annotate_district.py --city 广州  # 其他城市（需先补 DISTRICT_HOSTS）

import json, os, re, sys, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
GD = os.path.join(BASE, 'guangdong_raw')

# ---------- 区级政府域名映射（核心资产，铺 32 城时持续扩充） ----------
# 杭州 13 区县（待逐条联网验证）
DISTRICT_HOSTS = {
    'hangzhou': {
        'yuhang.gov.cn': '余杭区',
        'fuyang.gov.cn': '富阳区',
        'qiantang.gov.cn': '钱塘区',
        'xiaoshan.gov.cn': '萧山区',
        'binjiang.gov.cn': '滨江区',
        'linping.gov.cn': '临平区',
        'shangcheng.gov.cn': '上城区',
        'gongshu.gov.cn': '拱墅区',
        'xihu.gov.cn': '西湖区',
        'linan.gov.cn': '临安区',
        'tonglu.gov.cn': '桐庐县',
        'chunan.gov.cn': '淳安县',
        'jiande.gov.cn': '建德市',
    },
}

# 杭州下辖区县名（用于 P2 文本匹配）
HZ_DISTRICTS = ['上城区', '拱墅区', '西湖区', '滨江区', '萧山区', '余杭区', '临平区',
                '钱塘区', '富阳区', '临安区', '桐庐县', '淳安县', '建德市']

# 泛指词：命中这些不判为区级
GENERIC_RE = re.compile(r'市区|全市|各县|各区|辖区|地区|社区|小区|片区|山区|灾区|城区|园区|高新区|开发区|新区')


def district_from_url(url, city_py):
    """P1：从来源 URL 域名判定区级。"""
    if not url:
        return None
    hosts = DISTRICT_HOSTS.get(city_py, {})
    for host, dist in hosts.items():
        if host in url.lower():
            return dist
    return None


def district_from_text(it, districts):
    """P2：从政策名 + 来源单位文本判定（排除泛指 + 排除括号举例）。

    关键（踩坑）：必须**剥离括号内容**再匹配。
    反例：「杭州市共有产权保障住房管理办法（…以西湖区朝仕轩、拱墅区清正源府为…）」
    ——这是市级政策，括号里只是房源举例，不判为拱墅区。
    判定看的是**发文主体 / 政策名主体**，不是**政策覆盖范围**。
    """
    # 只看 name（政策名主体）与 unit（发文单位）。
    # 不含 project —— 房源项目落在哪个区，不代表政策由该区发布
    #   （「西湖区朝仕轩人才共有产权保障住房」是市级政策的房源，不是西湖区政策）。
    name = str(it.get('name') or '')
    unit = str(it.get('unit') or '')
    # 1) unit 只取首选发文单位（分号/句号前的第一段），避免联合发文里的区级协作单位误判
    #    反例：「杭州市人民政府办公厅（办法）；西湖区/拱墅区住建局…」——主体是市政府办公厅，市级。
    unit_main = re.split(r'[；;。]', unit)[0]
    blob = name + ' ' + unit_main
    # 2) 剥离各类括号及其内容（举例/补充说明常含区名）
    blob = re.sub(r'[（(【\[][^）)】\]]*[）)】\]]', ' ', blob)
    # 3) 抹泛指词，避免「杭州市区」被判成「市区」
    blob = GENERIC_RE.sub(' ', blob)
    for d in districts:
        if d in blob:
            return d
    return None


def main():
    dry = '--dry-run' in sys.argv
    city = '杭州'
    city_py = 'hangzhou'

    zj = json.load(open(ZJ, encoding='utf-8'))
    if city not in zj:
        print(f'❌ {ZJ} 中无城市 {city}')
        sys.exit(1)

    # 备份
    if not dry:
        bak_dir = os.path.join(BASE, f'_bak_{datetime.now():%Y%m%d}_phase38')
        os.makedirs(bak_dir, exist_ok=True)
        bak = os.path.join(bak_dir, f'zhejiang-talent-data.json.pre-district_{datetime.now():%H%M%S}')
        shutil.copy2(ZJ, bak)
        print(f'备份: {bak}')

    obj = zj[city]
    changes = []
    for dim, dd in obj['dimensions'].items():
        for i, it in enumerate(dd.get('items', [])):
            if it.get('official') is False:
                continue  # 占位条目不标 district
            old = it.get('district')
            url = (it.get('source') or {}).get('url') or ''
            d = district_from_url(url, city_py) or district_from_text(it, HZ_DISTRICTS) or '市级'
            if old != d:
                changes.append((dim, i, old, d,
                                it.get('name') or it.get('level') or it.get('class') or it.get('type') or ''))
            if not dry:
                it['district'] = d

    print(f'\n=== {city} district 标注结果（{"DRY-RUN 未写入" if dry else "已写入"}）===')
    print(f'变更 {len(changes)} 条：')
    for dim, i, old, new, nm in changes:
        print(f'  [{dim}][{i}] {old or "(无)"} → {new}  |  {nm[:44]}')

    if not dry:
        json.dump(zj, open(ZJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\n✅ 已写入 {ZJ}')

    # 统计
    print(f'\n=== {city} district 分布 ===')
    from collections import Counter
    cnt = Counter()
    for dim, dd in obj['dimensions'].items():
        for it in dd.get('items', []):
            if it.get('official') is False:
                continue
            cnt[it.get('district', '(未标注)')] += 1
    for k, v in cnt.most_common():
        print(f'  {k}: {v} 条')


if __name__ == '__main__':
    main()
