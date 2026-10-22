# -*- coding: utf-8 -*-
# 2026-08-23 租房补贴来源补齐：为 22 城审计中发现「提及租房/租赁/租金补贴但缺 source」
# 的 9 个真实政策条目写入官方来源（均已 curl 实证 200 可达，且全部为 *.gov.cn）。
# 占位条目（"暂未查询到官方公开政策"）本身无对应政策，不加来源。
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))

# (文件, 城市, 维度, 条目序号, source 字典, 可选 note 覆盖)
FIXES_ZJ = {
    'zhejiang-talent-data.json': [
        ('温州', 'apply_path', 0, {
            'unit': '温州市住房和城乡建设局',
            'doc_no': '温住建发〔2025〕20号《温州市人才租房补贴政策实施细则》',
            'date': '2025-07',
            'url': 'https://www.zjpy.gov.cn/art/2025/7/23/art_1382365_59127390.html'
        }, None),
        ('湖州', 'apply_path', 0, {
            'unit': '湖州南太湖新区管理委员会',
            'doc_no': '《新引进高校毕业生（技能人才）购房、租房补贴实施办法》',
            'date': '2025',
            'url': 'https://taihu.huzhou.gov.cn/col/col1229211024/art/2025/art_8175108ae4914cb1bc41cb4cda346402.html'
        }, None),
        ('金华', 'apply_path', 0, {
            'unit': '金华市人力资源和社会保障局',
            'doc_no': '人才租房补助操作流程（浙里办·浙里人才之家）',
            'date': '2023-10',
            'url': 'http://rsj.jinhua.gov.cn/art/2023/10/10/art_1229165045_58716413.html'
        }, None),
    ]
}

FIXES_GD = [
    ('guangzhou.json', '广州', 'apply_path', 2, {
        'unit': '广州市住房和城乡建设局（广东政务服务网·配售型保障房申购）',
        'doc_no': '',
        'date': '',
        'url': 'https://www.gz.gov.cn/zwfw/zxfw/zffw/content/post_10953679.html'
    }, None),
    ('shenzhen.json', '深圳', 'welfare', 2, {
        'unit': '深圳市住房和建设局',
        'doc_no': '深建规〔2025〕18号《深圳市青年人才住房支持实施办法》',
        'date': '2025',
        'url': 'https://zjj.sz.gov.cn/gkmlpt/content/12/12554/post_12554794.html'
    }, None),
    ('foshan.json', '佛山', 'startup', 2, {
        'unit': '佛山市人民政府门户（知识库：禅城区/三水区创业租金补贴办事指南）',
        'doc_no': '',
        'date': '',
        'url': 'https://www.foshan.gov.cn/zsk/?kCode=BCC00001382'
    }, '创业租金补贴按区受理：禅城、三水等区在市政府门户知识库均有办事指南（每年最高6000元、'
        '累计不超过3年）；孵化载体场地30%免费提供给高校毕业生为省统一要求。'),
    ('zhongshan.json', '中山', 'apply_path', 1, {
        'unit': '中山市人力资源和社会保障局',
        'doc_no': '《关于2025年度市级人才房租金补贴申报的通告》',
        'date': '2025',
        'url': 'https://hrss.zs.gov.cn/gkmlpt/content/2/2609/mpost_2609903.html'
    }, None),
    ('zhaoqing.json', '肇庆', 'apply_path', 3, {
        'unit': '肇庆市鼎湖区人民政府（户籍管理专栏·户政窗口）；广东政务服务网',
        'doc_no': '',
        'date': '',
        'url': 'https://www.zqdh.gov.cn/zwgk/ztzl/jczwgk/gkly/hjgl'
    }, None),
    ('shantou.json', '汕头', 'welfare', 2, {
        'unit': '汕头市人民政府',
        'doc_no': '汕府〔2024〕29号',
        'date': '2024',
        'url': 'https://www.shantou.gov.cn/cnst/gkml/zwgk/gzwj/gfxwj/szf/content/post_2343767.html'
    }, None),
]

def main():
    n = 0
    for fname, fixes in FIXES_ZJ.items():
        p = os.path.join(BASE, fname)
        data = json.load(open(p, encoding='utf-8'))
        for city, dim, idx, src, note in fixes:
            it = data[city]['dimensions'][dim]['items'][idx]
            it['source'] = src
            if note is not None:
                it['note'] = note
            print(f'[OK] {city}/{dim}#{idx} <- {src["url"]}')
            n += 1
        json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    for fname, city, dim, idx, src, note in FIXES_GD:
        p = os.path.join(BASE, 'guangdong_raw', fname)
        data = json.load(open(p, encoding='utf-8'))
        it = data['dimensions'][dim]['items'][idx]
        it['source'] = src
        if note is not None:
            it['note'] = note
        json.dump(data, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'[OK] {city}/{dim}#{idx} <- {src["url"]}')
        n += 1
    print(f'共写入 {n} 条来源')

if __name__ == '__main__':
    main()
