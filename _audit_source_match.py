#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
来源—内容对应性审计（Source↔Content Correspondence Audit）

用途：逐条检查 talent-data.json 中每条政策的「内容」是否能被其「来源」佐证，
      输出高风险条目清单，供人工联网复核。不自动改数据。

四类风险信号：
  A 主题错配   —— 来源文号/标题属「入户·落户·户籍·居住证」类，却挂着补贴金额
  B 主体错配   —— 内容涉及多个行政区（≥2 个），但只有单一来源
  C 来源缺失   —— 有金额但 source.url 为空
  D 弱来源     —— 来源为新闻/媒体转载/问答页，而非政策原文
                 （url 含 news/xwzx/xwlb/rdzt 或 doc_no 为空或含「转载」）

用法： python _audit_source_match.py [talent-data.json] [--all]
      默认只输出高风险条目；--all 输出全部含金额条目。
"""
import json, re, sys
from urllib.parse import urlparse

DISTRICTS = ['黄埔','南沙','白云','花都','增城','从化','越秀','荔湾','海珠','天河','番禺',
    '奉化','余姚','慈溪','北仑','镇海','鄞州','象山','宁海','海曙','江北',
    '柯桥','上虞','诸暨','嵊州','新昌','越城','滨海',
    '南湖','秀洲','嘉善','海盐','海宁','平湖','桐乡',
    '吴兴','南浔','德清','长兴','安吉','南太湖',
    '定海','普陀','岱山','嵊泗',
    '莲都','龙泉','青田','缙云','遂昌','松阳','云和','庆元','景宁',
    '禅城','南海','顺德','三水','高明','莞城','南城','万江','石碣',
    '香洲','斗门','金湾','蓬江','江海','新会','台山','开平','鹤山','恩平',
    '濠江','潮阳','潮南','澄海','南澳','赤坎','霞山','坡头','麻章','遂溪','徐闻','廉江','雷州','吴川',
    '武江','浈江','曲江','乐昌','南雄','仁化','始兴','翁源','乳源','新丰',
    '茂南','电白','高州','化州','信宜','梅江','梅县','兴宁','平远','蕉岭','大埔','丰顺','五华',
    '城区','陆丰','海丰','陆河','源城','东源','和平','龙川','紫金','连平',
    '江城','阳东','阳西','阳春','清城','清新','佛冈','阳山','连山','连南','英德','连州',
    '湘桥','潮安','饶平','榕城','揭东','揭西','惠来','普宁','云城','云安','新兴','郁南','罗定']

# 金额：先抹掉人数/面积等计数表述，再提取「万」金额。
# 必须允许「万」与量词间夹少量字——「目标25万左右非户籍人口」「年度落户完成1.08万人」
# 中「万」后接的是「左右」「人」，仅靠负向断言 `万(?!人)` 会漏判「25万左右」。
COUNTABLE = re.compile(r'\d+(?:\.\d+)?\s*万[^，。；、\s]{0,4}?(?:人|人口|户|套|㎡|平方米|人次|家|个|辆|吨|亩)')
AMT_ALL = re.compile(r'(\d+(?:\.\d+)?)\s*万')
HKU_DOC = re.compile(r'入户|落户|户籍|居住证')
# 弱来源只认「真新闻栏目 / 互动交流问答 / 明确标注媒体转载」，
# 不要把 /gkmlpt/ /zwgk/ /zcwj/ 等正常政务公开路径误判为新闻（初次版本即误伤 115 条）
WEAK_URL = re.compile(r'/news/|/xwlb/|/xwzx/|hdjlpt|yjsz|wenda')
MEDIA_UNIT = re.compile(r'日报|晚报|记者|媒体|转载|新闻发布会|融媒')
CONTENT_KEYS = ['cash','house_voucher','condition','discount','price_base','detail','note','name','rule','constraint']

def audit(path='talent-data.json'):
    data = json.load(open(path, encoding='utf-8'))
    rows = []
    for prov in data['meta']['provinces']:
        pk = prov['key']
        for c, cd in data[pk].items():
            for dim, dv in cd['dimensions'].items():
                for it in dv.get('items', []):
                    if it.get('official') is False:
                        continue
                    src = it.get('source', {}) or {}
                    url = str(src.get('url', '') or '')
                    doc = str(src.get('doc_no', '') or '')
                    unit = str(src.get('unit', '') or '')
                    blob = ' '.join(str(it.get(k, '') or '') for k in CONTENT_KEYS)
                    # 先抹掉「25万左右非户籍人口」「1.08万人」等计数表述，再提取金额
                    amts = [float(x) for x in AMT_ALL.findall(COUNTABLE.sub('【计数】', blob))]
                    if not amts:
                        continue
                    maxamt = max(amts)
                    ds = sorted({d for d in DISTRICTS if d in blob})
                    risks = []
                    if not url:
                        risks.append('C-来源缺失')
                    if HKU_DOC.search(doc) and maxamt >= 1:
                        risks.append('A-主题错配(入户/落户类却含金额)')
                    if len(ds) >= 2:
                        risks.append(f'B-主体错配(内容涉{len(ds)}区但来源单一)')
                    weak = (bool(WEAK_URL.search(url)) or bool(MEDIA_UNIT.search(unit))
                            or (doc in ('', '—', '-') and bool(MEDIA_UNIT.search(unit))))
                    if weak and maxamt >= 1:
                        risks.append('D-弱来源(新闻转载/问答页)')
                    if risks:
                        rows.append(dict(city=c, prov=pk, dim=dim, amt=maxamt, ds=ds,
                                         doc=doc, unit=unit, url=url, host=urlparse(url).netloc,
                                         risks=risks))
    return rows

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'talent-data.json'
    show_all = '--all' in sys.argv
    rows = sorted(audit(path), key=lambda r: (-r['amt'], r['city']))
    print(f'=== 来源—内容对应性审计 · {path} ===')
    if not show_all:
        print(f'高风险条目: {len(rows)} 条\n')
    from collections import Counter
    cnt = Counter()
    for r in rows:
        for k in r['risks']:
            cnt[k.split('(')[0]] += 1
    print('风险分布:', dict(cnt), '\n')
    for r in rows:
        print(f"{r['city']}[{r['dim']}] {r['amt']}万  {'/'.join(r['risks'])}")
        print(f"    文号={r['doc'][:40]}  单位={r['unit'][:30]}")
        print(f"    host={r['host']}  区={r['ds'][:6]}")
        print(f"    url={r['url'][:100]}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
