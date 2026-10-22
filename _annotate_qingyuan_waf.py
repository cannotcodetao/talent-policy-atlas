# -*- coding: utf-8 -*-
"""Phase 33：清远 www.gdqy.gov.cn 全域 WAF 标注。

背景：清远市政府门户网站 gdqy.gov.cn 已全站启用人机验证（WAF），
curl/WebFetch 等自动化工具均无法核验该站任何链接的可达性（返回 412/405 或"正在验证您是否是真人"）。
已实证该站存在真实失效链接（post_1835696 返回 404），故其余同域链接虽非 404，
亦属"无法核验"状态，须在 note 中明示，避免读者误判为已核验。
"""
import json, re, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = 'guangdong_raw/qingyuan.json'
BAK = SRC + '.bak_waf_20260902'
TAG = '【来源核验受限】'

shutil.copyfile(SRC, BAK)
d = json.load(open(SRC, encoding='utf-8'))
cd = d.get('清远') or d

CAVEAT = (TAG + 'gdqy.gov.cn 全站已启用人机验证（WAF），自动化工具无法核验本链接可达性'
          '（非 404，但亦不能证明有效）；请在浏览器中手动打开确认。'
          '清远高新区类政策另有清远高新区政企互通服务信息化平台 https://qyzqht.cn/ 可作交叉入口。')

n_url = 0
n_note = 0
for dim, node in cd['dimensions'].items():
    for it in node.get('items', []):
        u = str((it.get('source') or {}).get('url', ''))
        if 'www.gdqy.gov.cn' not in u:
            continue
        n_url += 1
        note = str(it.get('note') or '')
        if TAG in note:
            continue
        it['note'] = (CAVEAT + note) if note else CAVEAT
        n_note += 1

json.dump(d, open(SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'清远 www.gdqy.gov.cn 条目 {n_url} 处，本次加注 note {n_note} 条（已备份 {BAK}）')
