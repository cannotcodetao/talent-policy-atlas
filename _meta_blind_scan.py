#!/usr/bin/env python3
"""
Phase 36 元盲区扫描器（scripts/_meta_blind_scan.py）
====================================================

不依赖用户报问题，自驱发现以下盲区：
1. grad 同 level 多条（用户视角'重复学历'）—— Phase 36 起源
2. 现金+房票双空条目（理论不应存在）
3. 同档多条 cash 文本高度相似（合并未尽）
4. 跨维度同档金额重复（grad ↔ welfare ↔ anju_subsidy）
5. 现金列内含"或/及/及以"并列结构（可能合并未尽的金额错配）
6. 现金列内多个相同数字（分期/分单位发放在数据层独立计分但用户感知重复）
7. source.url 字段为空但有金额（C 类缺失来源）
8. 现金/房票金额超出阈值（异常值哨兵）
9. 维度字段 schema 不一致（如某条用 target 而同维度其它用 level）
10. 现金列字段空但 note 有金额（金额被埋没在 note 里不参与计分）

输出：JSON 报告 + 可读文本
"""
import json, os, re, sys
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, 'talent-data.json')

def normalize(s):
    if not s: return ''
    s = re.sub(r'\d+(?:\.\d+)?', 'N', s)
    s = re.sub(r'[\s，。；;,、（）()]', '', s)
    return s

def load():
    with open(DATA_FILE, encoding='utf-8') as f:
        return json.load(f)

def scan_blind_dots():
    """返回盲区命中列表（每条含 city/dim/idx/level/描述/严重度）"""
    d = load()
    hits = []
    
    for prov in ['zhejiang','guangdong']:
        for city, cdata in d[prov].items():
            grad = cdata['dimensions'].get('grad_subsidy',{}).get('items',[])
            welfare = cdata['dimensions'].get('welfare',{}).get('items',[])
            anju = cdata['dimensions'].get('anju_subsidy',{}).get('items',[])
            
            # === 盲区 1: grad 同 level 多条 ===
            by_level = defaultdict(list)
            for i, it in enumerate(grad):
                by_level[it.get('level','')].append(i)
            for level, idxs in by_level.items():
                if len(idxs) > 1:
                    hits.append({
                        'blind': 1, 'sev': 'high',
                        'city': city, 'dim': 'grad_subsidy',
                        'idx': idxs, 'level': level,
                        'desc': f'grad 同 level "{level}" 多 {len(idxs)} 条（用户视角重复）'
                    })
            
            # === 盲区 2: cash+hv 双空 ===
            for i, it in enumerate(grad):
                cash = (it.get('cash','') or '').strip()
                hv = (it.get('house_voucher','') or '').strip()
                if cash in ['','—','-','无'] and hv in ['','—','-','无']:
                    hits.append({
                        'blind': 2, 'sev': 'high',
                        'city': city, 'dim': 'grad_subsidy', 'idx': i,
                        'level': it.get('level',''),
                        'desc': 'cash+hv 双空（理论不应存在）'
                    })
            
            # === 盲区 3: 同档 cash 文本高度相似（合并未尽）===
            for level, idxs in by_level.items():
                if len(idxs) < 2: continue
                for i in range(len(idxs)):
                    for j in range(i+1, len(idxs)):
                        it1 = grad[idxs[i]]
                        it2 = grad[idxs[j]]
                        n1 = normalize(it1.get('cash',''))
                        n2 = normalize(it2.get('cash',''))
                        if n1 and n2 and len(n1) > 8 and (n1 in n2 or n2 in n1):
                            hits.append({
                                'blind': 3, 'sev': 'mid',
                                'city': city, 'dim': 'grad_subsidy',
                                'idx': [idxs[i], idxs[j]], 'level': level,
                                'desc': f'同档 cash 高度相似（归一化后包含）'
                            })
            
            # === 盲区 4: 跨维度同档金额重复 ===
            grad_texts = [(i, normalize(it.get('cash',''))) for i, it in enumerate(grad)]
            welfare_texts = [(i, normalize(it.get('detail','') or it.get('cash',''))) for i, it in enumerate(welfare)]
            for gi, gt in grad_texts:
                for wi, wt in welfare_texts:
                    if gt and wt and len(gt) > 8 and (gt in wt or wt in gt):
                        hits.append({
                            'blind': 4, 'sev': 'high',
                            'city': city, 'dim': 'grad↔welfare',
                            'idx': [gi, wi],
                            'desc': f'grad[{gi}] ↔ welfare[{wi}] 文本一致'
                        })
            
            # === 盲区 5: 现金列含"或/及"并列结构 ===
            for i, it in enumerate(grad):
                cash = it.get('cash','') or ''
                if re.search(r'\d+\s*万\s*[、或及]\s*\d+\s*万', cash):
                    hits.append({
                        'blind': 5, 'sev': 'low',
                        'city': city, 'dim': 'grad_subsidy', 'idx': i,
                        'level': it.get('level',''),
                        'desc': f'现金列含"或/及"并列结构: {cash[:50]}'
                    })
            
            # === 盲区 6: 现金列内多个相同数字（设计内提示）===
            for i, it in enumerate(grad):
                cash = it.get('cash','') or ''
                amounts = re.findall(r'(\d+(?:\.\d+)?)\s*万', cash)
                if amounts and len(amounts) != len(set(amounts)):
                    hits.append({
                        'blind': 6, 'sev': 'info',
                        'city': city, 'dim': 'grad_subsidy', 'idx': i,
                        'level': it.get('level',''),
                        'desc': f'现金列内含相同数字 x{len(amounts)-len(set(amounts))}（分期或合并计分提示）'
                    })
            
            # === 盲区 7: source.url 为空但有金额 ===
            for dim_name, items_list in [('grad', grad), ('welfare', welfare)]:
                for i, it in enumerate(items_list):
                    cash = it.get('cash','') or it.get('detail','') or it.get('t','')
                    src = it.get('source',{})
                    if not src.get('url','') and re.search(r'\d+\s*万', cash):
                        hits.append({
                            'blind': 7, 'sev': 'mid',
                            'city': city, 'dim': dim_name, 'idx': i,
                            'desc': '有金额但 source.url 为空'
                        })
            
            # === 盲区 8: 异常值哨兵 ===
            for dim_name, items_list, field_name in [
                ('grad_subsidy', grad, 'cash'),
                ('anju_subsidy', anju, 't'),
            ]:
                for i, it in enumerate(items_list):
                    text = it.get(field_name,'') or ''
                    m = re.search(r'(\d+(?:\.\d+)?)\s*万', text)
                    if m and float(m.group(1)) > 100:
                        hits.append({
                            'blind': 8, 'sev': 'mid',
                            'city': city, 'dim': dim_name, 'idx': i,
                            'desc': f'单笔金额>{100}万（哨兵阈值）: {m.group(1)}'
                        })
            
            # === 盲区 9: 字段 schema 不一致（同维不同字段）===
            for dim_name in ['grad_subsidy', 'anju_subsidy']:
                items_list = cdata['dimensions'].get(dim_name,{}).get('items',[])
                fields_seen = set()
                for it in items_list:
                    if 'level' in it: fields_seen.add('level')
                    if 'target' in it: fields_seen.add('target')
                    if 'type' in it: fields_seen.add('type')
                if len(fields_seen) > 1:
                    hits.append({
                        'blind': 9, 'sev': 'high',
                        'city': city, 'dim': dim_name,
                        'desc': f'同维度字段不一致: {fields_seen}'
                    })
            
            # === 盲区 10: 现金空但 note 有金额 ===
            for i, it in enumerate(grad):
                cash = (it.get('cash','') or '').strip()
                note = it.get('note','') or ''
                if cash in ['','—','-','无'] and re.search(r'\d+\s*万', note):
                    hits.append({
                        'blind': 10, 'sev': 'info',
                        'city': city, 'dim': 'grad_subsidy', 'idx': i,
                        'level': it.get('level',''),
                        'desc': 'cash 空，金额埋在 note（不参与评分）'
                    })
    
    return hits

def main():
    print(f"=== 元盲区扫描器（_meta_blind_scan.py）===")
    print(f"数据文件: {DATA_FILE}")
    print(f"扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    hits = scan_blind_dots()
    
    # 按盲区分组
    by_blind = defaultdict(list)
    for h in hits:
        by_blind[h['blind']].append(h)
    
    blind_names = {
        1: 'grad 同 level 多条（用户视角重复学历）',
        2: 'cash+hv 双空条目',
        3: '同档 cash 高度相似（合并未尽）',
        4: '跨维度同档金额重复（grad ↔ welfare）',
        5: '现金列含"或/及"并列结构',
        6: '现金列内多个相同数字（分期/分单位）',
        7: '有金额但 source.url 为空',
        8: '单笔金额>100万（哨兵）',
        9: '维度字段 schema 不一致',
        10: 'cash 空，金额埋在 note',
    }
    
    print("=== 元盲区扫描结果 ===")
    print(f"总命中: {len(hits)}")
    print()
    for blind_num in sorted(by_blind.keys()):
        hits_at = by_blind[blind_num]
        sev_high = sum(1 for h in hits_at if h['sev'] == 'high')
        print(f"盲区 {blind_num}: {blind_names[blind_num]} → {len(hits_at)} 条 (高危 {sev_high})")
        for h in hits_at[:5]:  # 每盲区最多列5条
            print(f"  [{h['sev']}] {h['city']} / {h['dim']} / {h.get('level','-')} / {h['desc']}")
        if len(hits_at) > 5:
            print(f"  ...还有 {len(hits_at)-5} 条")
        print()
    
    # 保存 JSON 报告
    report_file = os.path.join(BASE, '_meta_blind_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            'scan_time': datetime.now().isoformat(),
            'total_hits': len(hits),
            'by_blind': {blind_names[k]: len(v) for k, v in by_blind.items()},
            'hits': hits,
        }, f, ensure_ascii=False, indent=2)
    print(f"报告已保存: {report_file}")

if __name__ == '__main__':
    main()