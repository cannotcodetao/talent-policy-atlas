# -*- coding: utf-8 -*-
# 合并构建：把既有「浙江 11 城 13 维」(zhejiang-talent-data.json) 与「广东 11 城 13 维」
# (guangdong_raw/{pinyin}.json) 合并为省份包裹结构的全量数据集 talent-data.json。
# 广东原始数据在此处做红线兜底：剔除 DENY_NAMES 名单 + 纯租赁关键词；空维度填占位。
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
GD = os.path.join(BASE, 'guangdong_raw')
OUT = os.path.join(BASE, 'talent-data.json')

DIM_ORDER = ['grad_subsidy','hukou','welfare','startup','apply_path',
             'anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise',
             'anju_highlevel',  # Phase 37 恢复：独立维度·仅查阅·不参与排名
             'timing','risk']
ANJU_DIMS = ['anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise','anju_highlevel']
ANJU_LABEL = {'anju_rent2sale':'先租后售人才房','anju_discount':'定向优惠价购房',
              'anju_subsidy':'人才购房补贴/房票','anju_enterprise':'企业内部福利房',
              'anju_highlevel':'高层次人才专项'}
DIM_LABEL = {'grad_subsidy':'毕业生补贴','hukou':'落户','startup':'创业扶持',
             'welfare':'配套保障','timing':'时效提醒','risk':'风险提示','apply_path':'申报路径',
             'anju_rent2sale':'先租后售人才房','anju_discount':'定向优惠价购房','anju_subsidy':'人才购房补贴/房票',
             'anju_enterprise':'企业内部福利房','anju_highlevel':'高层次人才专项'}
DROP_DIMS = {'anju_shared'}  # Phase 37 移除 talent_highlevel → 改名为 anju_highlevel 并恢复

GD_ORDER = ['广州','深圳','珠海','佛山','东莞','中山','惠州','江门','肇庆','汕头','湛江',
            '韶关','茂名','梅州','汕尾','河源','阳江','清远','潮州','揭阳','云浮']
PINYIN_GD = {'广州':'guangzhou','深圳':'shenzhen','珠海':'zhuhai','佛山':'foshan','东莞':'dongguan',
             '中山':'zhongshan','惠州':'huizhou','江门':'jiangmen','肇庆':'zhaoqing','汕头':'shantou','湛江':'zhanjiang',
             '韶关':'shaoguan','茂名':'maoming','梅州':'meizhou','汕尾':'shanwei','河源':'heyuan',
             '阳江':'yangjiang','清远':'qingyuan','潮州':'chaozhou','揭阳':'jieyang','云浮':'yunfu'}

# 红线兜底名单（广东复查若有纯租赁/非人才定向条目，加进此处重跑即可剔除）
DENY_NAMES = set()
PURE_RENTAL_KW = ['只租不售','公租房','公共租赁','保障性租赁住房']

# 已到期/暂停政策移除清单（keys: (prov, city, dim, item_title)）。
# 经 2026-08-23 联网核实：以下政策原文标注已到期/暂停/窗口期关闭，且无现行同口径替代，
# 故从交付数据中剔除，保证网页仅含「最新且正在实施」的政策。
EXPIRED_ITEMS = {
    # 珠海：珠人社〔2019〕97号 企业新引进人才住房(租房和生活)补贴 已到期失效、2024.9 起暂停受理；
    # 珠海市级未出新本科/硕士现金购房补贴，现行以「一免两减」租赁保障为主（博士 25 万属英才计划仍有效）。
    ('guangdong','珠海','grad_subsidy','普通本科'),
    ('guangdong','珠海','grad_subsidy','双一流本科'),
    ('guangdong','珠海','grad_subsidy','硕士'),
    ('guangdong','珠海','timing','企业新引进人才住房补贴到期'),
    # 中山：原紧缺适用高层次人才购房补贴 申报房产窗口期 2025-12-31 已到期；现行通道为
    # 配售型保障性住房（中建通〔2026〕67号）+「新中山人安家中山」购房消费券。
    ('guangdong','中山','anju_subsidy','原中山紧缺适用高层次人才购房补贴'),
    ('guangdong','中山','timing','原紧缺适用高层次人才购房补贴窗口期'),
    # 中山 risk#1「原紧缺适用高层次人才购房补贴离开即停」同样以已停收新申请的旧政策为主体，
    # 与上方 anju_subsidy/timing 同源，一并剔除；其余特聘人才/入户/配售型保障房风险为现行政策。
    ('guangdong','中山','risk','原紧缺适用高层次人才购房补贴离开即停'),
    # 肇庆：「用工十条」肇人社规〔2022〕1号 有效期3年至 2025-01-31 已到期；已由 2026 新政
    # （购房款比例补贴）+ 高新区人才发展专项资金替代，现有博士10万/高层次人才A·B·C类/
    # 新引进落户 2-10 万购房补贴均为现行。
    ('guangdong','肇庆','grad_subsidy','普通本科'),
    ('guangdong','肇庆','grad_subsidy','专科'),
    ('guangdong','肇庆','grad_subsidy','双一流本科'),
    ('guangdong','肇庆','anju_subsidy','“用工十条”毕业生一次性购房补贴'),
    ('guangdong','肇庆','timing','“用工十条”购房/就业补贴到期'),
    # 温州：鹿城区人才房票（试行 2 年，2023-09-20 至 2025-09-20）已到期，未以房票形式续期，
    # 转为市级配售型人才住房（5–7 折，温委办发〔2022〕69号 + 2026 常态化配售）。
    ('zhejiang','温州','anju_subsidy','温州市鹿城区人才房票补贴'),
    # 湖州：吴兴区原购房补贴（含「才聚湖州 凤栖吴兴」东部新城购房补贴）自 2026-01-01 起不再受理
    # 原政策，属停收新申请的旧政策；现行湖州购房补贴已由南太湖新区 2025.1.1 新政（博士35万/
    # 硕士15万/本科5万，对应 anju_subsidy#2）覆盖。
    ('zhejiang','湖州','anju_subsidy','吴兴区新引进高校毕业生（技能人才）购房补贴 / “才聚湖州 凤栖吴兴”东部新城购房补贴'),
    # 温州：timing「购房补贴已停止」为模糊状态陈述，且所指旧购房补贴（鹿城区房票）已剔除；
    # 现温州仍有瓯海区积分购房补贴（有效期至 2029）等现行政策，该 timing 项易误导，故移除。
    ('zhejiang','温州','timing','购房补贴已停止'),
}

# 注记清理（移除过期政策引用，避免网页呈现误导）：key 同上。
NOTE_FIX = {
    # 珠海：去掉指向已废止旧政策（珠人社〔2019〕97号）的状态措辞，仅说明现行口径
    ('guangdong','珠海','anju_subsidy','高层次人才住房补贴（货币安居补贴）'):
        '属货币化安居补贴（可用于购房）；珠海市级未单独设立“房票”购房补贴，'
        '现行以“一免两减”租赁保障为主。',
    # 深圳：原“新引进人才租房和生活补贴”由 2026 入户补贴接续，去掉“已停发”状态措辞
    ('guangdong','深圳','grad_subsidy','博士'):
        '深圳“新引进人才租房和生活补贴”（本科1.5万/硕士2.5万/博士3万）由2026入户补贴接续；'
        '入户补贴标准详见深人社规〔2025〕6号。',
}

def clean(v):
    s = '' if v is None else str(v).strip()
    return '' if s in ('—','-','无','None') else s

def item_title(it):
    for k in ('name','level','class','target','type','item'):
        if clean(it.get(k)):
            return clean(it.get(k))
    return ''

def placeholder(dim, city):
    lab = ANJU_LABEL.get(dim, DIM_LABEL.get(dim, ''))
    return {'name':'暂未查询到官方公开政策','unit':'','effective':'','expiry':'','project':'',
            'rent_years':'','price_base':'','rent_deduct':'','biz_req':'','person_req':'',
            'discount':'','constraint':'','channel':'','enterprise_only':'','official':False,
            'district':'市级',
            'source':{'unit':'','doc_no':'','date':'','url':''},
            'note':f'本次检索未发现{city}市级或各区官方发布的「{lab}」落地政策；若有更新请以各地最新政府文件为准。'}

def placeholder_highlevel(city):
    """Phase 37：anju_highlevel 维度的占位条目（独立格式，含 class/subsidy 字段，
    与其他维度的 name/条件字段格式不同，前端 SCHEMA 单独识别）。"""
    return {'class':'该市未设独立的高层次人才分类目录',
            'subsidy':'—',
            'source':{'unit':'','doc_no':'','date':'','url':''},
            'note':f'本次检索未发现{city}市级或各区官方发布的「高层次人才专项」独立政策；' \
                    f'部分地市（如韶关丹霞英才、清远高新区等）的人才计划归并在毕业生补贴/创业扶持等维度。',
            'official':False,'district':'市级'}

def main():
    zj = json.load(open(ZJ, encoding='utf-8'))
    zj_cities = zj['meta']['citiesDone']
    zhejiang = {c: zj[c] for c in zj_cities}  # 形状 {dimensions:{...}}，沿用既有（已含 13 维）
    # 浙江既有数据条目未携带 official 字段（均为既往已核验的官方来源）→ 统一回填 official=True；
    # 占位条目（official=False 已显式设置）保持不变。
    for c, obj in zhejiang.items():
        new_dims = {}
        for dim, dd in obj['dimensions'].items():
            # Phase 37 改名：talent_highlevel → anju_highlevel（保持数据完整、不 DROP）
            if dim == 'talent_highlevel':
                dim = 'anju_highlevel'
            if dim in DROP_DIMS:
                continue
            keep = []
            for it in dd.get('items', []) or []:
                if 'official' not in it or not isinstance(it.get('official'), bool):
                    it['official'] = True
                nm = item_title(it)
                if ('zhejiang', c, dim, nm) in EXPIRED_ITEMS:
                    continue
                keep.append(it)
            new_dims[dim] = {'desc': dd.get('desc', ''), 'items': keep}
        obj['dimensions'] = new_dims

    guangdong = {}
    for c in GD_ORDER:
        py = PINYIN_GD[c]
        rp = os.path.join(GD, py + '.json')
        if not os.path.exists(rp):
            raise SystemExit(f'缺少广东原始数据: {rp}')
        raw = json.load(open(rp, encoding='utf-8'))
        raw_dims = raw.get('dimensions', {}) or {}
        dims = {}
        # Phase 37：广东源头以 `talent_highlevel` 为 key，需要兼容映射到 `anju_highlevel`。
        # 遍历所有原始维度，遇到 talent_highlevel 重命名为 anju_highlevel 后再走标准循环。
        for dim in DIM_ORDER:
            src_key = 'talent_highlevel' if dim == 'anju_highlevel' else dim
            obj = raw_dims.get(src_key, {}) or {}
            items = obj.get('items', []) or []
            cleaned = []
            for it in items:
                nm = item_title(it)
                s = it.get('source') or {}
                it['source'] = {k: (s.get(k) or '') for k in ('unit','doc_no','date','url')}
                if 'official' not in it or not isinstance(it.get('official'), bool):
                    it['official'] = True
                if ('guangdong', c, dim, nm) in EXPIRED_ITEMS:
                    continue
                if ('guangdong', c, dim, nm) in NOTE_FIX:
                    it['note'] = NOTE_FIX[('guangdong', c, dim, nm)]
                if dim in ANJU_DIMS:
                    it['mode'] = dim
                    it['mode_label'] = ANJU_LABEL[dim]
                    eo = str(it.get('enterprise_only') or '').strip()
                    it['enterprise_only'] = eo if eo in ('是','部分','否') else ''
                    # 红线兜底：仅对安居购房维度剔除纯租赁 / 非人才定向条目
                    if any(dn in nm for dn in DENY_NAMES):
                        continue
                    if any(kw in nm for kw in PURE_RENTAL_KW):
                        continue
                cleaned.append(it)
            desc = clean(obj.get('desc')) or ANJU_LABEL.get(dim, DIM_LABEL.get(dim, ''))
            if not cleaned:
                # Phase 37：anju_highlevel 用专属 placeholder（class/subsidy 字段，非 name/条件）
                if dim == 'anju_highlevel':
                    cleaned = [placeholder_highlevel(c)]
                else:
                    cleaned = [placeholder(dim, c)]
            dims[dim] = {'desc': desc, 'items': cleaned}
        guangdong[c] = {
            'meta': {'scope': clean(raw.get('scope')) or '市级',
                     'updated': clean(raw.get('updated')) or '2026-08-20',
                     'sourceRule': clean(raw.get('sourceRule')) or '仅政府单位官网（*.gov.cn），排除新闻与自媒体'},
            'dimensions': dims
        }

    combined = {
        'meta': {
            'updated': zj['meta'].get('updated', '') or '2026-08-20',
            'provinces': [
                {'key': 'zhejiang', 'name': '浙江', 'cities': zj_cities},
                {'key': 'guangdong', 'name': '广东', 'cities': GD_ORDER}
            ]
        },
        'zhejiang': zhejiang,
        'guangdong': guangdong
    }
    json.dump(combined, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    n_zj = sum(len(zhejiang[c]['dimensions'][d]['items']) for c in zj_cities for d in DIM_ORDER)
    n_gd = sum(len(guangdong[c]['dimensions'][d]['items']) for c in GD_ORDER for d in DIM_ORDER)
    print('已写入省份包裹数据集 ->', os.path.basename(OUT))
    print(f'浙江 {len(zj_cities)} 城 / 安居+引才条目 {n_zj}')
    print(f'广东 {len(GD_ORDER)} 城 / 安居+引才条目 {n_gd}')

if __name__ == '__main__':
    main()
