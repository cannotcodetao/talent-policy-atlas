# -*- coding: utf-8 -*-
"""Phase 33：清远 6 个 www.gdqy.gov.cn 失效/不可核验链接替换为可核验来源。

用户决策 D3 = "全部找替代可核验来源"。已逐条检索 + curl 实测 200 + 内容核对。
5 个找到可核验替代（省政府公报/12345热线/清企通/清远日报）；1 个（市政协答复函）
确无 gov.cn 外全文转载，回退 WAF 说明（由 _annotate_qingyuan_waf.py 续处理）。
"""
import json, shutil, sys

sys.stdout.reconfigure(encoding='utf-8')
SRC = 'guangdong_raw/qingyuan.json'
BAK = SRC + '.bak_replace_20260902'
shutil.copyfile(SRC, BAK)

# old_url -> (new_url, doc_no_for_note, note_explain)
MAP = {
    'https://www.gdqy.gov.cn/xxgk/zzjg/zfjg/srlzyhshbz/zcfg/zcwj/content/post_2164773.html': (
        'https://www.gd.gov.cn/zwgk/gongbao/2026/16/content/mpost_4921748.html',
        '粤人社规〔2026〕20号《广东省就业创业补贴补助申请办理指导清单（2026年修订版）》'
        '（广东省人社厅、财政厅 2026-06-17 联合印发，省级原文；清远市人社局全文转载执行）',
        '原 gdqy.gov.cn 转载页 post_2164773 同站 WAF 不可核验，改用广东省政府公报省级原文（含完整指导清单）。'),
    'https://www.gdqy.gov.cn/gdqy/newxxgk/fgwj/zcjd/wzjd/content/post_1948909.html': (
        'https://12345.gdqy.gov.cn/201809/page/km/FAQ/faqDetail.html?klpId=875608&page=56',
        '清府〔2024〕37号《清远市人民政府关于调整户口迁移条件的实施意见》'
        '（含政策解读；2022-04-08 起施行，有效期 5 年）',
        '原 gdqy.gov.cn 政策解读页 post_1948909 同站 WAF 不可核验，改用 12345 热线知识库全文转载'
        '（含实施意见全文 + 解读，城镇落户零门槛、人才入户条款）。'),
    'https://www.gdqy.gov.cn/xxgk/zzjg/zfjg/srlzyhshbz/zcfg/zcwj/content/post_297829.html': (
        'https://12345.gdqy.gov.cn/201809/page/km/FAQ/faqDetail.html?klpId=875641&page=180',
        '清高管办〔2021〕26号《清远高新区过渡性人才公寓管理办法》'
        '（2025 修订版为清高管办〔2025〕1号，原文 PDF 在 gdqy.gov.cn/qygxjsglh WAF 域不可核验）',
        '原 gdqy.gov.cn 页 post_297829 同站 WAF 不可核验。人才公寓核心制度（只租不售/周转居住/免租金）'
        '由 12345 热线知识库 2021 过渡性办法全文印证；2025 修订版 PDF 仍挂 gdqy.gov.cn/qygxjsglh 路径，'
        '待该站 WAF 解除后补齐修订版直链。'),
    'https://www.gdqy.gov.cn/qyrlzybzj/gkmlpt/content/2/2063/post_2063384.html': (
        'https://qqt.gdqy.gov.cn/web/policy/policy_detail.ptl?navType=2&policyId=190000264',
        '清人社〔2020〕27号《清远市创业担保贷款担保基金和贴息资金管理办法》'
        '（依据粤人社规〔2019〕15号；清企通平台全文）',
        '原 gdqy.gov.cn 转载页 post_2063384 同站 WAF 不可核验，改用清企通（清远市政企互通平台）'
        '政策原文页（含个人30万/小微企业500万额度、贴息50%、办理流程全文）。'),
    'https://www.gdqy.gov.cn/qyzfcxjsglj/gkmlpt/content/2/2098/post_2098874.html': (
        'https://www.qyrb.cn/content/0EynlL06ZA.html',
        '《清远市配售型保障性住房管理办法（试行）》（清远市住建局 2025-12-29 印发，2026-01-29 施行）',
        '原 gdqy.gov.cn 印发通知页 post_2098874 同站 WAF 不可核验，改用清远日报（新清远）2025-12-31 '
        '全文解读转载（含封闭管理、回购、保障对象人才条件、2026-01-29 施行原文）。'),
    # post_2174825 政协答复函：无 gov.cn 外全文转载，回退 WAF 说明（由 _annotate_qingyuan_waf.py 处理）
}

d = json.load(open(SRC, encoding='utf-8'))
cd = d.get('清远') or d

n_url = n_note = 0
for dim, node in cd['dimensions'].items():
    for it in node.get('items', []):
        src = it.get('source') or {}
        u = str(src.get('url', '')).strip()
        if u not in MAP:
            continue
        new_url, doc_no, explain = MAP[u]
        src['url'] = new_url
        if doc_no:
            src['doc_no'] = doc_no
        note = str(it.get('note') or '')
        tag = '【来源已升级】'
        if tag not in note:
            it['note'] = (tag + explain + ' ' + note).strip()
        n_url += 1

json.dump(d, open(SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'替换 {n_url} 处 source.url（5 个不同 URL 各配可核验替代源）；备份 {BAK}')
print('剩余 post_2174825（市政协答复函）将由 _annotate_qingyuan_waf.py 加 WAF 说明')
