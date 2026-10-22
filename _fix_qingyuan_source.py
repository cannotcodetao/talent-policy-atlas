# -*- coding: utf-8 -*-
"""Phase 33-A：修复清远失效来源（改源头 guangdong_raw/qingyuan.json，非合并产物）。

背景：
  原 source.url = http://www.gdqy.gov.cn/xxgk/zzjg/zfjg/gdqygxqgwh/zwgk/tzgg/content/post_1835696.html
  → 用户浏览器打开为 404；我方请求为 412/405（gdqy.gov.cn 整站已启用人机验证 WAF，
    经 curl 直连、带浏览器 UA 直连、WebFetch 三种方式复核，均被「正在验证您是否是真人」拦截，
    **无法验证该站任何链接**，故不能再引用该域名的未核实链接）。

替换为（均已实测 HTTP 200 且含政策原文）：
  主来源：南方日报·南方+ 2024-03-04 全文转载《清远高新区加强新时代人才工作的若干措施》
          https://static.nfnews.com/content/202403/04/c8655791.html
          → 已核验含「第十九条」「本科生2000元/月」「本科生1000元/月」「36个月」原文
  兑现入口：清远高新区政企互通服务信息化平台 https://qyzqht.cn/
          → 青年人才创业就业补助线上申报官方入口（同步写入 apply_path.platform）
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')
BASE = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, 'guangdong_raw', 'qingyuan.json')

OLD = 'http://www.gdqy.gov.cn/xxgk/zzjg/zfjg/gdqygxqgwh/zwgk/tzgg/content/post_1835696.html'
NEW = 'https://static.nfnews.com/content/202403/04/c8655791.html'
PORTAL = 'https://qyzqht.cn/'

TAIL = ('【来源已更换】原清远市政府门户网站正式印发件链接 post_1835696 已失效（404，网站改版迁移）；'
        'gdqy.gov.cn 整站已启用人机验证，外部工具无法核验该站任何链接，'
        '故改用南方日报·南方+ 2024-03-04 全文转载版（含第十九条原文：本科生购房补贴2000元/月、'
        '生活补助1000元/月，期限最长36个月）。'
        '官方兑现/申报入口：清远高新区政企互通服务信息化平台 ' + PORTAL + '。'
        '待 gdqy.gov.cn 恢复可核验后补齐正式印发件链接。')

raw = open(PATH, encoding='utf-8').read()
d = json.loads(raw)

n_url = n_note = 0
OLD_TAIL_RE = re.compile(r'【来源待升级】[^；]*?正式印发件新链接待检索补齐')
for dim, dv in d['dimensions'].items():
    for it in dv.get('items') or []:
        s = it.get('source') or {}
        if s.get('url') != OLD:
            continue
        s['url'] = NEW
        s['doc_no'] = '清高委办〔2024〕9号《清远高新区加强新时代人才工作的若干措施》第十九条（南方日报·南方+ 全文转载）'
        if '南方日报' not in str(s.get('unit', '')):
            s['unit'] = (str(s.get('unit') or '广东清远高新技术产业开发区管理委员会办公室')
                         + '（印发）；南方日报·南方+（全文转载）')
        n_url += 1
        nt = str(it.get('note') or '')
        nt2 = OLD_TAIL_RE.sub(TAIL, nt)
        if nt2 == nt and '【来源已更换】' not in nt:
            nt2 = (nt.rstrip('；; ') + '；' + TAIL) if nt else TAIL
        if nt2 != nt:
            it['note'] = nt2
            n_note += 1

# apply_path：补官方申报入口 URL
ap_items = (d['dimensions'].get('apply_path') or {}).get('items') or []
for it in ap_items:
    pf = str(it.get('platform') or '')
    if PORTAL in pf or 'qyzqht.cn' in pf:
        it['platform'] = pf.replace('（4）清远高新区政企互通服务信息化平台(qyzqht.cn)',
                                    '（4）清远高新区政企互通服务信息化平台(' + PORTAL + ')')
        it.setdefault('source', {})
        s = it['source']
        s['unit'] = s.get('unit') or '清远高新区管委会党政办公室'
        s['doc_no'] = s.get('doc_no') or '《清远高新区加强新时代人才工作的若干措施》(清高委办〔2024〕9号) 线上申报入口'
        s['url'] = s.get('url') or PORTAL

open(PATH, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2))
print(f'清远源文件已更新：替换 {n_url} 条 source.url，更新 {n_note} 条 note，apply_path 补官方申报入口')
print('剩余 OLD 链接出现次数：', open(PATH, encoding='utf-8').read().count('post_1835696'))
