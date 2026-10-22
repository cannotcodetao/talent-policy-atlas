#!/usr/bin/env python3
"""
Phase 36 修复脚本：金华 grad_subsidy 同档合并（4组×2条→4条）
- 专科：保留不动（仅1条）
- 普通本科：合并金人社发〔2023〕13号（购房货币补助8万）+ 2024生活补助（最高4万）
- 双一流本科：合并金人社发〔2023〕13号（购房货币补助15万）+ 2024生活补助（最高8万/5万）
- 硕士：合并金人社发〔2023〕13号（购房货币补助20万）+ 2024生活补助（最高10万）
- 博士：合并金人社发〔2023〕13号（购房货币补助40万）+ 2024生活补助（最高25万）

合并原则（用户决策 D36-1）：
1. 字段语义互斥：现金列(cash)放生活补助，购房货币补助放房票列(house_voucher)
2. 主 source 取支撑最高金额者；副 source 文号+URL 完整写进 note
3. 评分不变（max 口径下合并同档金额不改变维度分）
"""
import json, os, shutil
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
RAW_FILE = os.path.join(BASE, 'zhejiang-talent-data.json')

# 备份（若尚未备份）
import datetime
bk = os.path.join(BASE, '_bak_20260906_phase36', f'zhejiang-talent-data.json.pre-fix_{datetime.datetime.now().strftime("%H%M%S")}')
os.makedirs(os.path.dirname(bk), exist_ok=True)
shutil.copy(RAW_FILE, bk)
print(f"备份: {bk}")

with open(RAW_FILE, encoding='utf-8') as f:
    zj = json.load(f)

jh = zj['金华']
grad = jh['dimensions']['grad_subsidy']['items']
print(f"原始金华 grad 条目: {len(grad)}")

# 备份原始条目以便 old_cash 断言
ORIG = list(grad)

# 按 level 分组
by_level = defaultdict(list)
for i, it in enumerate(grad):
    by_level[it.get('level','')].append((i, it))

# 合并映射
NEW_CASH = {
    '普通本科': '生活补助 最高4万元（按单位性质分档：市区属民营企业/社工机构/农村乡镇中小学医疗卫生服务机构4万、市区属事业单位国企2万，分5年发放；金华籍及在金高校应届毕业生可提档）',
    '双一流本科': '生活补助 最高8万元（按单位性质分档：市区属民营企业/社工机构/农村乡镇中小学医疗卫生服务机构8万、市区属事业单位国企5万，分5年发放；金华籍及在金高校应届毕业生可提档）',
    '硕士': '生活补助 最高10万元（市属高校引进的最高5万），分5年发放',
    '博士': '生活补助 最高25万元，分5年发放',
}
NEW_HV = {
    '普通本科': '购房货币补助 最高8万元',
    '双一流本科': '购房货币补助 最高15万元',
    '硕士': '购房货币补助 最高20万元',
    '博士': '购房货币补助 最高40万元',
}
NEW_NOTE = {
    '普通本科': (
        '〔政策1：智选金华·购房货币补助〕金人社发〔2023〕13号 https://www.jinhua.gov.cn/art/2023/3/27/art_1229715437_1797752.html 购房补助按购房价比例计算，非固定额度；所购住房限售5年。'
        '〔政策2：2024年9月11日后引进人才生活补助〕 http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html'
    ),
    '双一流本科': (
        '〔政策1：智选金华·购房货币补助〕金人社发〔2023〕13号 https://www.jinhua.gov.cn/art/2023/3/27/art_1229715437_1797752.html 购房补助按购房价比例计算；所购住房限售5年。'
        '〔政策2：2024年9月11日后引进人才生活补助（双一流本科）〕 http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html'
    ),
    '硕士': (
        '〔政策1：智选金华·购房货币补助〕金人社发〔2023〕13号 https://www.jinhua.gov.cn/art/2023/3/27/art_1229715437_1797752.html 购房补助按购房价比例计算；所购住房限售5年。'
        '〔政策2：2024年9月11日后引进人才生活补助（硕士）〕 http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html'
    ),
    '博士': (
        '〔政策1：智选金华·购房货币补助〕金人社发〔2023〕13号 https://www.jinhua.gov.cn/art/2023/3/27/art_1229715437_1797752.html 购房补助按购房价比例计算；所购住房限售5年。'
        '〔政策2：2024年9月11日后引进人才生活补助（博士）〕 http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html'
    ),
}
# 主 source: 取支撑该档最高金额者（生活补助为最高，故取生活补助 source）
NEW_SOURCE = {
    '普通本科': {
        'unit': '金华市人社局',
        'doc_no': '生活补助申报兑付操作流程（2024年9月11日后引进人才）',
        'date': '2024-09-11',
        'url': 'http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html',
    },
    '双一流本科': {
        'unit': '金华市人社局',
        'doc_no': '生活补助申报兑付操作流程（2024年9月11日后引进人才）',
        'date': '2024-09-11',
        'url': 'http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html',
    },
    '硕士': {
        'unit': '金华市人社局',
        'doc_no': '生活补助申报兑付操作流程（2024年9月11日后引进人才）',
        'date': '2024-09-11',
        'url': 'http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html',
    },
    '博士': {
        'unit': '金华市人社局',
        'doc_no': '生活补助申报兑付操作流程（2024年9月11日后引进人才）',
        'date': '2024-09-11',
        'url': 'http://rsj.jinhua.gov.cn/art/2025/11/4/art_1229307088_58718747.html',
    },
}
NEW_CONDITION = {
    '普通本科': '2024年9月11日（含）后首次在金华大市范围内参加社会保险，与金华市区属企事业单位签订劳动合同并按规定缴纳养老保险；按首次在市区缴纳社保时的学历核定标准',
    '双一流本科': '同"普通本科"通道（双一流高校本科毕业生）',
    '硕士': '同"普通本科"通道（硕士研究生）',
    '博士': '同"普通本科"通道（博士研究生）',
}

# 构建新条目（按原顺序：专科、普通本科、双一流本科、硕士、博士）
new_items = []
for level in ['专科', '普通本科', '双一流本科', '硕士', '博士']:
    items_at_level = by_level[level]
    if len(items_at_level) == 1:
        # 专科：不动
        new_items.append(items_at_level[0][1])
    else:
        # 合并 2 条为 1 条
        idx1, it1 = items_at_level[0]
        idx2, it2 = items_at_level[1]
        # old_cash 断言：必须分别有购房货币补助（hv非空）+ 生活补助（cash非空）
        old_hv1 = (it1.get('house_voucher','') or '').strip()
        old_cash2 = (it2.get('cash','') or '').strip()
        old_cash1 = (it1.get('cash','') or '').strip()
        old_hv2 = (it2.get('house_voucher','') or '').strip()
        
        # 通用模式：第1条 cash=—、hv=购房；第2条 cash=生活补助、hv=空
        # 或反之。灵活判定。
        if '购房' in old_hv1 or '购房' in old_hv2:
            # 一条有购房货币补助（hv非空），另一条 cash 有生活补助
            assert old_cash1 != '—' and old_cash1 != '' or old_cash2 != '—' and old_cash2 != '', \
                f"[{level}] 两条都没生活补助，异常"
        
        new_item = {
            'level': level,
            'cash': NEW_CASH[level],
            'house_voucher': NEW_HV[level],
            'condition': NEW_CONDITION[level],
            'source': NEW_SOURCE[level],
            'note': NEW_NOTE[level],
            'official': True,
        }
        new_items.append(new_item)
        print(f"  [{level}] 合并 {len(items_at_level)}→1 条: cash={NEW_CASH[level][:30]}... hv={NEW_HV[level]}")

# 替换
jh['dimensions']['grad_subsidy']['items'] = new_items
print(f"\n合并后金华 grad 条目: {len(new_items)}")

# 写回
with open(RAW_FILE, 'w', encoding='utf-8') as f:
    json.dump(zj, f, ensure_ascii=False, indent=2)
print(f"已写回: {RAW_FILE}")