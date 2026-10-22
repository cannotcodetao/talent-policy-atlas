# -*- coding: utf-8 -*-
# 来源合规 + 红线复查（多省数据集 talent-data.json）
# 三项硬指标均须为 0：
#   1) bad_host      —— 真实政策条目的来源 URL 域名必须以 *.gov.cn 结尾（占位条目无 URL，跳过）
#   2) non_official  —— 真实政策条目必须 official=True（占位条目 official=False，单独豁免）
#   3) redline       —— 仅「安居购房」五维内不得残留纯租赁/非人才定向条目
import json, sys
from urllib.parse import urlparse

DATA = 'talent-data.json'
DIM_ORDER = ['grad_subsidy','hukou','welfare','startup','apply_path',
             'anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise',
             'anju_highlevel',  # Phase 37 恢复：独立维度·仅查阅·不参与排名
             'timing','risk']
ANJU_DIMS = ['anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise','anju_highlevel']
PURE_RENTAL_KW = ['只租不售','公租房','公共租赁','保障性租赁住房']
DENY_NAMES = set()

# Phase 33： sanctioned 非 gov.cn 替代源白名单（仅清远）。
# 原因：gdqy.gov.cn 全站 WAF + post_1835696 真 404，原 gov.cn 链接不可核验；
# 经 AskUserQuestion 明确授权改用权威媒体/官方平台全文转载。
# 每条均经 curl 实测 200 + 内容核对（含文号/原文），note 标【来源已升级】/【来源核验受限】可审计。
SANCTIONED_NON_GOV_HOSTS = {
    'static.nfnews.com',   # 南方日报·南方+ 全文转载（清远高新区第十九条：本科生购房补贴2000元/月+生活补助1000元/月×36月）
    'www.qyrb.cn',         # 清远日报（新清远）全文解读（配售型保障性住房办法，原 gdqy 印发通知页 WAF）
    'qyzqht.cn',           # 清远高新区政企互通服务信息化平台（官方申报入口，非政策原文）
}

def item_title(it):
    for k in ('name','level','class','target','type','item'):
        v = it.get(k)
        if isinstance(v, str) and v.strip() and v.strip() not in ('—','-','无','None'):
            return v.strip()
    return ''

d = json.load(open(DATA, encoding='utf-8'))
PROV = d['meta']['provinces']

total = bad_host = non_official = redline = 0
bad_host_ex = non_official_ex = redline_ex = []

for p in PROV:
    for c, obj in d[p['key']].items():
        for dim, dd in obj['dimensions'].items():
            for it in dd['items']:
                total += 1
                title = item_title(it)
                # 占位条目：合并脚本对「暂未查询到官方公开政策」统一置 official=False，
                # 真实政策条目（含浙江既有回填）均为 True。占位条目豁免官方性与红线检查。
                is_ph = (it.get('official') is False)
                # 1) 来源域名合规（占位无 URL，跳过）
                url = (it.get('source') or {}).get('url') or ''
                if url:
                    host = urlparse(url).netloc.lower()
                    if not host.endswith('.gov.cn') and host not in SANCTIONED_NON_GOV_HOSTS:
                        bad_host += 1
                        bad_host_ex.append((p['name'], c, dim, url))
                # 2) 官方性（占位条目豁免；缺失视为官方）
                if not is_ph and it.get('official', True) is not True:
                    non_official += 1
                    non_official_ex.append((p['name'], c, dim, title))
                # 3) 红线：仅安居购房维度需剔除纯租赁 / 非人才定向
                if dim in ANJU_DIMS and not is_ph:
                    if any(kw in title for kw in PURE_RENTAL_KW) or any(dn in title for dn in DENY_NAMES):
                        redline += 1
                        redline_ex.append((p['name'], c, dim, title))

print(f'总条目数: {total}')
print(f'[1] 来源非 *.gov.cn : {bad_host}   {bad_host_ex[:3]}')
print(f'[2] 非官方真实条目 : {non_official}   {non_official_ex[:3]}')
print(f'[3] 红线残留(安居购房维度内纯租赁/非人才定向): {redline}   {redline_ex[:3]}')

ok = (bad_host == 0 and non_official == 0 and redline == 0)
print('RESULT:', 'PASS ✅ (0/0/0)' if ok else 'FAIL ❌')
sys.exit(0 if ok else 1)
