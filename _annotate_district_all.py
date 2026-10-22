# -*- coding: utf-8 -*-
# Phase 40 T1：全库（31 城）既有条目补 district 字段（杭州已在 Phase 38 标注，跳过）
#
# 判定逻辑与 _annotate_district.py（Phase 38 试点）完全一致：
#   P1 URL 域名（保守：仅收录高置信 pinyin.gov.cn 域名）
#   P2 政策名 + 首选发文单位文本（剥括号 + 抹泛指词）
#   P3 兜底 → 市级
#
# 特殊：东莞、中山不设区（直筒子市）→ 全部市级。
#       汕尾"城区"/阳江"江城区"/清远"清城区" 等含 GENERIC 词「城区」，
#       P2 天然不误判（泛指词先抹除），其区级条目由子代理采集时显式带 district。
#
# 用法：
#   python _annotate_district_all.py --dry-run          # 全 31 城只打印
#   python _annotate_district_all.py                    # 全 31 城写入
#   python _annotate_district_all.py --city 宁波        # 单城

import json, os, re, sys, shutil
from datetime import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
GD_DIR = os.path.join(BASE, 'guangdong_raw')

ZJ_CITIES = ['宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水']
GD_CITY_PY = {
    '广州': 'guangzhou', '深圳': 'shenzhen', '珠海': 'zhuhai', '汕头': 'shantou',
    '佛山': 'foshan', '韶关': 'shaoguan', '湛江': 'zhanjiang', '肇庆': 'zhaoqing',
    '江门': 'jiangmen', '茂名': 'maoming', '惠州': 'huizhou', '梅州': 'meizhou',
    '汕尾': 'shanwei', '河源': 'heyuan', '阳江': 'yangjiang', '清远': 'qingyuan',
    '东莞': 'dongguan', '中山': 'zhongshan', '潮州': 'chaozhou', '揭阳': 'jieyang',
    '云浮': 'yunfu',
}

CITY_DISTRICTS = {
    '宁波': ['海曙区', '江北区', '北仑区', '镇海区', '鄞州区', '奉化区', '余姚市', '慈溪市', '象山县', '宁海县'],
    '温州': ['鹿城区', '龙湾区', '瓯海区', '洞头区', '瑞安市', '乐清市', '龙港市', '永嘉县', '平阳县', '苍南县', '文成县', '泰顺县'],
    '嘉兴': ['南湖区', '秀洲区', '嘉善县', '海盐县', '海宁市', '平湖市', '桐乡市'],
    '湖州': ['吴兴区', '南浔区', '德清县', '长兴县', '安吉县'],
    '绍兴': ['越城区', '柯桥区', '上虞区', '诸暨市', '嵊州市', '新昌县'],
    '金华': ['婺城区', '金东区', '武义县', '浦江县', '磐安县', '兰溪市', '义乌市', '东阳市', '永康市'],
    '衢州': ['柯城区', '衢江区', '江山市', '常山县', '开化县', '龙游县'],
    '舟山': ['定海区', '普陀区', '岱山县', '嵊泗县'],
    '台州': ['椒江区', '黄岩区', '路桥区', '温岭市', '临海市', '玉环市', '三门县', '天台县', '仙居县'],
    '丽水': ['莲都区', '龙泉市', '青田县', '云和县', '庆元县', '缙云县', '遂昌县', '松阳县', '景宁畲族自治县'],
    '广州': ['荔湾区', '越秀区', '海珠区', '天河区', '白云区', '黄埔区', '番禺区', '花都区', '南沙区', '从化区', '增城区'],
    '深圳': ['福田区', '罗湖区', '南山区', '盐田区', '宝安区', '龙岗区', '龙华区', '坪山区', '光明区'],
    '珠海': ['香洲区', '斗门区', '金湾区'],
    '汕头': ['金平区', '龙湖区', '濠江区', '澄海区', '潮阳区', '潮南区', '南澳县'],
    '佛山': ['禅城区', '南海区', '顺德区', '三水区', '高明区'],
    '韶关': ['浈江区', '武江区', '曲江区', '乐昌市', '南雄市', '新丰县', '翁源县', '始兴县', '仁化县', '乳源瑶族自治县'],
    '湛江': ['赤坎区', '霞山区', '坡头区', '麻章区', '廉江市', '雷州市', '吴川市', '遂溪县', '徐闻县'],
    '肇庆': ['端州区', '鼎湖区', '高要区', '四会市', '广宁县', '德庆县', '封开县', '怀集县'],
    '江门': ['蓬江区', '江海区', '新会区', '台山市', '开平市', '鹤山市', '恩平市'],
    '茂名': ['茂南区', '电白区', '高州市', '化州市', '信宜市'],
    '惠州': ['惠城区', '惠阳区', '惠东县', '博罗县', '龙门县'],
    '梅州': ['梅江区', '梅县区', '兴宁市', '平远县', '蕉岭县', '大埔县', '丰顺县', '五华县'],
    '汕尾': ['城区', '海丰县', '陆丰市', '陆河县'],
    '河源': ['源城区', '东源县', '龙川县', '紫金县', '连平县', '和平县'],
    '阳江': ['江城区', '阳东区', '阳西区', '阳春市'],
    '清远': ['清城区', '清新区', '英德市', '连州市', '佛冈县', '连山壮族瑶族自治县', '连南瑶族自治县', '阳山县'],
    '东莞': [],
    '中山': [],
    '潮州': ['湘桥区', '潮安区', '饶平县'],
    '揭阳': ['榕城区', '揭东区', '普宁市', '惠来县', '揭西县'],
    '云浮': ['云城区', '云安区', '罗定市', '新兴县', '郁南县'],
}

# P1 域名映射（保守：只收录高置信区县官网主域；P2 文本判定为主力）
DISTRICT_HOSTS = {
    '宁波': {'haishu.gov.cn': '海曙区', 'beilun.gov.cn': '北仑区', 'zhenhai.gov.cn': '镇海区',
             'yinzhou.gov.cn': '鄞州区', 'fenghua.gov.cn': '奉化区', 'yuyao.gov.cn': '余姚市',
             'cixi.gov.cn': '慈溪市', 'xiangshan.gov.cn': '象山县', 'ninghai.gov.cn': '宁海县'},
    '温州': {'lucheng.gov.cn': '鹿城区', 'longwan.gov.cn': '龙湾区', 'ouhai.gov.cn': '瓯海区',
             'dongtou.gov.cn': '洞头区', 'ruian.gov.cn': '瑞安市', 'yueqing.gov.cn': '乐清市',
             'longgang.gov.cn': '龙港市'},
    '嘉兴': {'nanhu.gov.cn': '南湖区', 'xiuzhou.gov.cn': '秀洲区', 'jiashan.gov.cn': '嘉善县',
             'haiyan.gov.cn': '海盐县', 'haining.gov.cn': '海宁市', 'pinghu.gov.cn': '平湖市',
             'tongxiang.gov.cn': '桐乡市'},
    '湖州': {'wuxing.gov.cn': '吴兴区', 'nanxun.gov.cn': '南浔区', 'deqing.gov.cn': '德清县',
             'changxing.gov.cn': '长兴县', 'anji.gov.cn': '安吉县'},
    '绍兴': {'yuecheng.gov.cn': '越城区', 'keqiao.gov.cn': '柯桥区', 'shangyu.gov.cn': '上虞区',
             'zhuji.gov.cn': '诸暨市', 'shengzhou.gov.cn': '嵊州市', 'xinchang.gov.cn': '新昌县'},
    '金华': {'wucheng.gov.cn': '婺城区', 'jindong.gov.cn': '金东区', 'yiwu.gov.cn': '义乌市',
             'yongkang.gov.cn': '永康市', 'dongyang.gov.cn': '东阳市', 'lanxi.gov.cn': '兰溪市',
             'wuyi.gov.cn': '武义县', 'pujiang.gov.cn': '浦江县', 'panan.gov.cn': '磐安县'},
    '衢州': {'kecheng.gov.cn': '柯城区', 'jiangshan.gov.cn': '江山市', 'changshan.gov.cn': '常山县',
             'kaihua.gov.cn': '开化县', 'longyou.gov.cn': '龙游县'},
    '舟山': {'dinghai.gov.cn': '定海区', 'daishan.gov.cn': '岱山县', 'shengsi.gov.cn': '嵊泗县'},
    '台州': {'jiaojiang.gov.cn': '椒江区', 'huangyan.gov.cn': '黄岩区', 'luqiao.gov.cn': '路桥区',
             'wenling.gov.cn': '温岭市', 'linhai.gov.cn': '临海市', 'yuhuan.gov.cn': '玉环市',
             'sanmen.gov.cn': '三门县', 'tiantai.gov.cn': '天台县', 'xianju.gov.cn': '仙居县'},
    '丽水': {'liandu.gov.cn': '莲都区', 'longquan.gov.cn': '龙泉市', 'qingtian.gov.cn': '青田县',
             'yunhe.gov.cn': '云和县', 'jinyun.gov.cn': '缙云县', 'suichang.gov.cn': '遂昌县',
             'songyang.gov.cn': '松阳县', 'jingning.gov.cn': '景宁畲族自治县'},
    '广州': {'huangpu.gov.cn': '黄埔区', 'nansha.gov.cn': '南沙区', 'panyu.gov.cn': '番禺区',
             'haizhu.gov.cn': '海珠区', 'tianhe.gov.cn': '天河区', 'yuexiu.gov.cn': '越秀区',
             'liwan.gov.cn': '荔湾区', 'conghua.gov.cn': '从化区', 'zengcheng.gov.cn': '增城区',
             'huadu.gov.cn': '花都区'},
    '深圳': {'szft.gov.cn': '福田区', 'szlh.gov.cn': '罗湖区', 'szns.gov.cn': '南山区',
             'szbaoan.gov.cn': '宝安区', 'szlhq.gov.cn': '龙华区', 'szpsq.gov.cn': '坪山区',
             'szgm.gov.cn': '光明区'},
    '珠海': {'xiangzhou.gov.cn': '香洲区', 'doumen.gov.cn': '斗门区', 'jinwan.gov.cn': '金湾区'},
    '汕头': {'jinping.gov.cn': '金平区', 'longhu.gov.cn': '龙湖区', 'haojiang.gov.cn': '濠江区',
             'chenghai.gov.cn': '澄海区', 'chaoyang.gov.cn': '潮阳区', 'chaonan.gov.cn': '潮南区',
             'nanao.gov.cn': '南澳县'},
    '佛山': {'nanhai.gov.cn': '南海区', 'shunde.gov.cn': '顺德区', 'chancheng.gov.cn': '禅城区',
             'gaoming.gov.cn': '高明区', 'ss.gov.cn': '三水区'},
    '韶关': {'lechang.gov.cn': '乐昌市', 'nanxiong.gov.cn': '南雄市'},
    '湛江': {'lianjiang.gov.cn': '廉江市', 'leizhou.gov.cn': '雷州市', 'wuchuan.gov.cn': '吴川市',
             'suixi.gov.cn': '遂溪县', 'xuwen.gov.cn': '徐闻县'},
    '肇庆': {'sihui.gov.cn': '四会市', 'gaoyao.gov.cn': '高要区', 'dinghu.gov.cn': '鼎湖区'},
    '江门': {'pengjiang.gov.cn': '蓬江区', 'xinhui.gov.cn': '新会区', 'taishan.gov.cn': '台山市',
             'kaiping.gov.cn': '开平市', 'heshan.gov.cn': '鹤山市', 'enping.gov.cn': '恩平市'},
    '茂名': {'maonan.gov.cn': '茂南区', 'dianbai.gov.cn': '电白区', 'gaozhou.gov.cn': '高州市',
             'huazhou.gov.cn': '化州市', 'xinyi.gov.cn': '信宜市'},
    '惠州': {'huicheng.gov.cn': '惠城区', 'huiyang.gov.cn': '惠阳区', 'huidong.gov.cn': '惠东县',
             'boluo.gov.cn': '博罗县', 'longmen.gov.cn': '龙门县'},
    '梅州': {'meixian.gov.cn': '梅县区', 'xingning.gov.cn': '兴宁市', 'dapu.gov.cn': '大埔县',
             'fengshun.gov.cn': '丰顺县', 'wuhua.gov.cn': '五华县', 'pingyuan.gov.cn': '平远县',
             'jiaoling.gov.cn': '蕉岭县'},
    '汕尾': {'haifeng.gov.cn': '海丰县', 'lufeng.gov.cn': '陆丰市', 'luhe.gov.cn': '陆河县'},
    '河源': {'dongyuan.gov.cn': '东源县', 'longchuan.gov.cn': '龙川县', 'zijin.gov.cn': '紫金县',
             'lianping.gov.cn': '连平县', 'heping.gov.cn': '和平县'},
    '阳江': {'yangdong.gov.cn': '阳东区', 'yangxi.gov.cn': '阳西区', 'yangchun.gov.cn': '阳春市'},
    '清远': {'yingde.gov.cn': '英德市', 'lianzhou.gov.cn': '连州市', 'fogang.gov.cn': '佛冈县',
             'yangshan.gov.cn': '阳山县'},
    '潮州': {'chaoan.gov.cn': '潮安区', 'raoping.gov.cn': '饶平县'},
    '揭阳': {'jiedong.gov.cn': '揭东区', 'puning.gov.cn': '普宁市', 'huilai.gov.cn': '惠来县',
             'jiexi.gov.cn': '揭西县'},
    '云浮': {'luoding.gov.cn': '罗定市', 'xinxing.gov.cn': '新兴县', 'yunan.gov.cn': '云安区'},
}

# 泛指词：命中这些不判为区级（与 Phase 38 完全一致）
GENERIC_RE = re.compile(r'市区|全市|各县|各区|辖区|地区|社区|小区|片区|山区|灾区|城区|园区|高新区|开发区|新区')


def district_from_url(url, city):
    if not url:
        return None
    hosts = DISTRICT_HOSTS.get(city, {})
    low = url.lower()
    for host, dist in hosts.items():
        if host in low:
            return dist
    return None


def district_from_text(it, districts):
    name = str(it.get('name') or '')
    # unit 可能在顶层，也可能在 source 内（全库实际存放位置）
    unit = str(it.get('unit') or (it.get('source') or {}).get('unit') or '')
    unit_main = re.split(r'[；;。]', unit)[0]
    blob = name + ' ' + unit_main
    blob = re.sub(r'[（(【\[][^）)】\]]*[）)】\]]', ' ', blob)
    blob = GENERIC_RE.sub(' ', blob)
    for d in districts:
        if d and d in blob:
            return d
    return None


def district_from_text_strict(it, city, districts):
    """P2 严格主体判定。返回 (区名 or None, 市级主体是否确证)。

    规则：
      ① 区名出现在 blob 前 14 字（发文主体开头）内，或紧跟市名之后
        （「嘉兴市秀洲区」「衢州市柯城区」，允许中间夹「市」）→ 区级
      ② 否则 blob 前 14 字含市名 / 市委 / 市政府 → 市级主体确证
        （防两类误判：区县网站转载市级文件 URL 误导 P1；
          联合发文名单末尾出现的县名，如「…、惠来县人民政府」）
      ③ 都不命中 → 返回 (None, False)，交给 P1 URL / 兜底
    """
    name = str(it.get('name') or '')
    # unit 可能在顶层，也可能在 source 内（全库实际存放位置）
    unit = str(it.get('unit') or (it.get('source') or {}).get('unit') or '')
    unit_main = re.split(r'[；;。]', unit)[0]
    blob = name + ' ' + unit_main
    blob = re.sub(r'[（(【\[][^）)】\]]*[）)】\]]', ' ', blob)
    blob = GENERIC_RE.sub(' ', blob).strip()
    head = blob[:14]
    for d in districts:
        if not d:
            continue
        if d in head or re.search(re.escape(city) + r'市?' + re.escape(d), blob):
            return d, False
    if (city in head) or ('市委' in head) or ('市政府' in head):
        return None, True
    return None, False


def annotate_city(city, obj, dry):
    """返回 (变更数, 区级条目数, 总条目数)。直接原地修改 obj。

    优先级：P2 严格主体判定 > P1 URL 域名 > 市级兜底。
    Phase 40 实证修正两类误判：
      a. 区县政府网站转载/挂载市级政策文件（嘉兴 timing/risk 挂 xiuzhou.gov.cn、
         揭阳市级文件 PDF 挂 huilai.gov.cn）——P1 优先会误判区级；
      b. 联合发文名单用「、」分隔，县名出现在末尾。
    """
    districts = CITY_DISTRICTS.get(city, [])
    changes = 0
    n_dis = 0
    n_tot = 0
    for dim, dd in obj.get('dimensions', {}).items():
        for it in dd.get('items', []):
            if it.get('official') is False:
                continue
            n_tot += 1
            old = it.get('district')
            url = (it.get('source') or {}).get('url') or ''
            d, mun = district_from_text_strict(it, city, districts)
            if d is None and not mun:
                d = district_from_url(url, city)
            if d is None:
                d = '市级'
            if old != d:
                changes += 1
                nm = it.get('name') or it.get('level') or it.get('class') or it.get('type') or ''
                print(f'    [{dim}] {old or "(无)"} → {d}  |  {str(nm)[:40]}')
            it['district'] = d
            if d != '市级':
                n_dis += 1
    return changes, n_dis, n_tot


def main():
    dry = '--dry-run' in sys.argv
    only = None
    if '--city' in sys.argv:
        only = sys.argv[sys.argv.index('--city') + 1]

    targets = []  # (城市名, obj, 持久化函数)
    zj = json.load(open(ZJ, encoding='utf-8'))
    for c in ZJ_CITIES:
        if c not in zj:
            print(f'⚠ 浙江源文件缺 {c}')
            continue
        if only and c != only:
            continue
        targets.append((c, zj[c], None))

    gd_cache = {}
    for c, py in GD_CITY_PY.items():
        if only and c != only:
            continue
        fp = os.path.join(GD_DIR, f'{py}.json')
        if not os.path.exists(fp):
            print(f'⚠ 广东源文件缺 {fp}')
            continue
        gd_cache.setdefault(fp, json.load(open(fp, encoding='utf-8')))
        targets.append((c, gd_cache[fp], fp))

    if not dry:
        bak_dir = os.path.join(BASE, '_bak_20260908_phase40')
        os.makedirs(bak_dir, exist_ok=True)
        shutil.copy2(ZJ, os.path.join(bak_dir, 'zhejiang-talent-data.json.pre-annotate'))
        for fp, d in gd_cache.items():
            shutil.copy2(fp, os.path.join(bak_dir, 'gd_' + os.path.basename(fp) + '.pre-annotate'))
        print(f'备份目录: {bak_dir}')

    print(f'=== district 全库标注（{"DRY-RUN" if dry else "写入"}）目标 {len(targets)} 城 ===')
    total_changes = 0
    for city, obj, fp in targets:
        ch, n_dis, n_tot = annotate_city(city, obj, dry)
        total_changes += ch
        print(f'  {city}: 总 {n_tot} · 区级 {n_dis} · 变更 {ch}')
        if not dry and fp:
            json.dump(obj, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    if not dry:
        json.dump(zj, open(ZJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print(f'\n✅ 已写入 {ZJ} + {len(gd_cache)} 个广东文件')
    print(f'\n总变更 {total_changes} 条')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
