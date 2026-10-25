# -*- coding: utf-8 -*-
import json, os, sys, re
sys.stdout.reconfigure(encoding='utf-8')

BASE = os.path.dirname(os.path.abspath(__file__))
# 支持命令行指定数据文件与输出文件（便于先导预览 / 技能复用）
DATA = os.path.join(BASE, sys.argv[1]) if len(sys.argv) > 1 else os.path.join(BASE, 'talent-data.json')
OUT = os.path.join(BASE, sys.argv[2]) if len(sys.argv) > 2 else os.path.join(BASE, '人才引进政策_2026.html')

d = json.load(open(DATA, encoding='utf-8'))
PROV = d['meta']['provinces']  # 省份包裹结构
# 扁平化所有省份城市（浙江/广东城市名不冲突，可直接按 city 取数据）
_allcities = {}
for p in PROV:
    _allcities.update(d[p['key']])
ORDER = PROV[0]['cities']  # 初始激活省份的城市列表（浙江）

DIM_ORDER = ['grad_subsidy','hukou','welfare','startup','apply_path',
             'anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise',
             'anju_highlevel',  # Phase 37 恢复：独立维度·仅查阅·不参与排名
             'timing','risk']
DIM_LABEL = {
    'grad_subsidy':'毕业生补贴', 'hukou':'落户',
    'startup':'创业扶持', 'welfare':'配套保障', 'timing':'时效提醒',
    'risk':'风险提示', 'apply_path':'申报路径',
    'anju_rent2sale':'先租后售人才房', 'anju_discount':'定向优惠价购房', 'anju_subsidy':'人才购房补贴/房票',
    'anju_enterprise':'企业内部福利房',
    'anju_highlevel':'高层次人才专项'  # Phase 37
}
ANJU_DIMS = ['anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise','anju_highlevel']

def clean(v):
    if v is None: return ''
    s = str(v).strip()
    return '' if s in ('—','-','无','None','') else s

def anju_line(it):
    """安居购房条目 → 对比表单行摘要（抽屉表由 SCHEMA 逐字段展示，不依赖此函数）。"""
    name = clean(it.get('name'))
    if not name:
        return '暂未查询到官方公开政策'
    discount = clean(it.get('discount'))
    eff = clean(it.get('effective'))
    eo = it.get('enterprise_only')
    tag = ''
    if eo == '是':
        tag = ' 〔仅企业员工〕'
    elif eo == '部分':
        tag = ' 〔含企业员工〕'
    disc = discount
    if disc and len(disc) > 70:
        cut = re.search(r'[。；]', disc[:90])
        disc = (disc[:cut.end()] if cut else disc[:70]) + '…'
    line = name
    if eff:
        line += f'（{eff}）'
    if disc:
        line += '｜' + disc
    line += tag
    return line

EDU_KW = {
    '专科': ['专科', '大专'],
    '本科': ['本科', '学士'],
    '硕士': ['硕士', '研究生'],
    '博士': ['博士'],
}
EDU_ORDER = ['专科', '本科', '硕士', '博士', '不限']
def edu_tags(it, dim):
    """自动派生学历适用标签：grad_subsidy 用 level 字段，其余维度扫描政策文本关键词。"""
    tags = set()
    texts = []
    if dim == 'grad_subsidy':
        texts.append(str(it.get('level', '')))
    for k in ('detail', 'note', 'condition', 'name', 'rule', 'target', 'subsidy',
              'cash', 'house_voucher', 'type', 'project', 'discount', 'person_req', 'biz_req', 'enterprise_only'):
        v = it.get(k)
        if v:
            texts.append(str(v))
    blob = ' '.join(texts)
    for lvl, kws in EDU_KW.items():
        if any(kw in blob for kw in kws):
            tags.add(lvl)
    if not tags:
        tags.add('不限')
    return [x for x in EDU_ORDER if x in tags]

def summary_lines(city):
    dm = city['dimensions']
    out = {}
    for dim in DIM_ORDER:
        items = dm.get(dim, {}).get('items', [])
        recs = []
        for it in items:
            if it.get('official') is False:
                continue
            if dim == 'grad_subsidy':
                lvl = clean(it.get('level')); cash = clean(it.get('cash')); hv = clean(it.get('house_voucher'))
                t = f"{lvl}：{cash}" if lvl else cash
                if hv:
                    sep = '' if hv.startswith('房票') else '房票 '
                    if hv not in cash:
                        t += f"｜{sep}{hv}"
            elif dim == 'hukou':
                t = f"{clean(it.get('target'))}：{clean(it.get('rule'))}"
            elif dim == 'startup':
                t = f"{clean(it.get('type'))}：{clean(it.get('detail'))}"
            elif dim == 'welfare':
                t = f"{clean(it.get('type'))}：{clean(it.get('detail'))}"
            elif dim == 'timing':
                t = f"{clean(it.get('item'))}：{clean(it.get('detail'))}"
            elif dim == 'risk':
                t = f"{clean(it.get('item'))}：{clean(it.get('detail'))}"
            elif dim == 'apply_path':
                parts = [f"平台 {clean(it.get('platform'))}", clean(it.get('process')), f"咨询 {clean(it.get('phone'))}"]
                t = '｜'.join([p for p in parts if p])
            elif dim in ANJU_DIMS:
                t = anju_line(it)
            else:
                t = ''
            recs.append({'t': t, 'e': edu_tags(it, dim)})
        out[dim] = recs
    return out

cities_payload = {}
summary_payload = {}
edu_payload = {}
for c in _allcities:
    cities_payload[c] = _allcities[c]
    summary_payload[c] = summary_lines(_allcities[c])
    edu_payload[c] = {dim: [edu_tags(it, dim) for it in _allcities[c]['dimensions'].get(dim, {}).get('items', [])]
                       for dim in DIM_ORDER}

# ---- 力度评分（单位：万元）----
# RANK_DIMS = 参与「力度排名」的四个现金维度；非现金维度（落户/时效/风险/申报路径/折扣购房）不参与金额排名
_AMT_WAN = re.compile(r'(\d+(?:\.\d+)?)\s*万')
_AMT_YUAN = re.compile(r'(\d+(?:\.\d+)?)\s*元')
_MONTHLY = re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*月')
_AMT_YUAN_YEAR = re.compile(r'(\d+(?:\.\d+)?)\s*元\s*/\s*年')
_DUR_MONTH = re.compile(r'(?:最长?|租期|可租)\s*(\d+)\s*个月?')
_DUR_YEAR = re.compile(r'(\d+)\s*年')

# ---- Phase 33：按月补贴的「最长期限」解析 ----
# 根因（金华实证）：政策原文写「租房补贴 600元/月，最长36个月」，但评分一律年化 12 个月
# （600×12/10000 = 0.72万），与政策文本「最长36个月」对不上 → 显示 0.72 万、实为 2.16 万。
# 同类 9 城 24 条（宁波60月/梅州60月/嘉兴·湖州·金华·茂名·清远36月/佛山36月/深圳24月）。
_DUR_KW = r'(?:最长|最长不超过|不超过|最多|累计不超过|期限|连续|可享受|享受期限|发放期限|补贴期限|资助期限)'
_DUR_M_RE = re.compile(_DUR_KW + r'[^，。；、（）]{0,8}?(\d+)\s*个月')
_DUR_Y_RE = re.compile(_DUR_KW + r'[^，。；、（）]{0,8}?(\d+)\s*年')
# 「N元/月 × 2年」乘号格式（舟山市级「就业津贴 800元/月×2年」）——无关键词，需单列。
# 不含「分N年发放」：那是分期兑付，不是可领期限（金华生活补助「4万元…分5年发放」误配会虚高 60 倍）。
_DUR_X_M_RE = re.compile(r'×\s*(\d+)\s*个月')
_DUR_X_Y_RE = re.compile(r'×\s*(\d+)\s*年')
# 「分5年发放」是【分期兑付】不是【可领期限】→ 关键词表里不含「分…年」，避免把一次性
# 总额按年放大（金华生活补助「最高4万元…分5年发放」若误配会变成 4×60，灾难性虚高）。
RENT_MONTH_CAP = 60

def _dur_spans(s):
    """返回 [(出现位置, 月数)]，按位置升序。"""
    out = []
    for rx, k in ((_DUR_M_RE, 1), (_DUR_Y_RE, 12), (_DUR_X_M_RE, 1), (_DUR_X_Y_RE, 12)):
        for m in rx.finditer(s):
            out.append((m.start(), int(m.group(1)) * k))
    out.sort()
    return out

def _rent_months(s, pos=None, default=12):
    """按月补贴的可领月数。
    - 条目内只有【一个】期限 → 全条目采用。覆盖「大学生租房补贴（最长36个月）：博士…/硕士…/
      本科…/专科…」这类「期限前置、多个金额共享」的高频格式（金华/湖州/嘉兴/梅州实证）。
    - 条目内有【多个不同】期限 → 就近匹配：优先「金额之后、同句内」的期限
      （深圳「过渡性住房…最长36个月）或申领安居补贴（1250元/月…最长24个月）→ 取 24）；
      其次「金额之前最近」的期限；再取不到则用条目内【最小】期限（保守，防止张冠李戴）。
    """
    spans = _dur_spans(str(s or ''))
    if not spans:
        return default
    months = sorted({min(n, RENT_MONTH_CAP) for _, n in spans})
    if len(months) == 1:
        return months[0]
    if pos is None:
        return months[0]
    end = len(s)
    for ch in '。；;\n':
        i = s.find(ch, pos)
        if i != -1:
            end = min(end, i)
    after = [min(n, RENT_MONTH_CAP) for p, n in spans if pos <= p < end]
    if after:
        return after[0]
    before = [min(n, RENT_MONTH_CAP) for p, n in spans if p < pos]
    if before:
        return before[-1]
    return months[0]

# 「合计/共计/总计/累计最高」是【分项汇总】，分项金额会各自计入（且可能分属不同维度），
# 若再取合计必然重复计分（清远「购房补贴7.2万 + 生活补助3.6万，合计最高约10.8万」→
# 取 10.8 会同时吃掉安居维度的 7.2 万）。故汇总分句一律跳过。
_SUM_KW = ['合计', '共计', '总计', '累计最高', '最高合计']

# 分句扫描：把政策文本按中文标点/顿号/斜杠拆成「分句」，对含排除词的分句整体跳过。
# 相比固定字符窗口，分句法能稳健处理「关键词离金额较远」的情形（如「创新创业团队…1000万元」）。
_CLAUSE_SEP = re.compile(r'[，,；;：:\n、/]')
def _clauses(text):
    return [c for c in _CLAUSE_SEP.split(str(text)) if c.strip()]

# 分句「主体词」：判断该分句是否自带政策主体（补贴/补助/安家/引进…）。
# 无主体词的悬挂金额句（如「最高8万元」）是上一分句的限定延续，应继承其排除状态。
_SUBJ_KW = ['补贴','补助','安家','资助','奖励','津贴','生活','租房','创业','经费','扶持','培养','引进','薪酬','待遇','奖']
def _scan_wan(clauses, neg=(), pos=None, inherit_neg=False):
    """在分句列表里取最高「万」金额。
    neg：含该关键词的分句整体跳过（排除购房/贷款/团队资助等非目标金额）。
    pos：若给出，仅保留含 pos 关键词的分句（避免把无关金额计入）。
    inherit_neg（Phase 32）：悬挂上限句继承上一分句的排除词——
    「购房货币补助 购房价8%、最高8万元」中「、」把上限句与「购房」主体割裂，
    原逻辑会漏判，导致购房补助泄入毕业生补贴维度并与购房维度双重计分（金华/湖州/佛山实证）。"""
    best = 0.0
    prev_neg = False
    for cl in clauses:
        cl_neg = bool(neg) and any(k in cl for k in neg)
        if inherit_neg and not cl_neg and prev_neg and not any(k in cl for k in _SUBJ_KW):
            cl_neg = True
        if not cl_neg and not (pos and not any(k in cl for k in pos)):
            for m in _AMT_WAN.finditer(cl):
                v = float(m.group(1))
                r = cl[m.end():m.end()+10]
                mm = _DUR_MONTH.search(r)
                if mm: v *= int(mm.group(1))   # 「万/月 × 月数」情形
                best = max(best, v)
        prev_neg = cl_neg
    return best

def _scan_yuan_to_wan(clauses, neg=(), pos=None):
    """元 → 万元（用于小额补贴，如 6000元租金补贴）。"""
    best = 0.0
    for cl in clauses:
        if neg and any(k in cl for k in neg): continue
        if pos and not any(k in cl for k in pos): continue
        for m in _AMT_YUAN.finditer(cl):
            best = max(best, float(m.group(1)) / 10000.0)
    return best

# 毕业生补贴力度：仅计现金/安家/租房类，排除购房补助、房票、公积金贷款、高层次人才住房补贴
# 末尾 4 项为 Phase 33 新增「汇总金额」排除（详见 _SUM_KW 注释）
_GRAD_NEG = ['购房','房票','公积金','住房贷款','高层次','住房补贴','共有产权','按揭','还款'] + _SUM_KW

# ---- 普适口径（Phase 28 固化）：排名仅计「满足学历要求即可」的金额 ----
# 金额【前后对称窗口】内命中下列标记 → 属特定人才计划/需认定/非普适，不计入排名。
# 对称窗口必须保留：云浮等城格式为「15万元生活补贴（机关事业单位紧缺人才计划…）」，
# 标记词在金额【后方】，只看前置窗口会漏判。
NON_UNIV_NEAR = [
    # 人才层次跨界（非该学历本身可及）
    '院士','诺贝尔','两院','国家级','世界级','杰出','领军','拔尖','首席','特级技师','中华技能大奖','国医大师',
    # 高层次人才分档（A–F 类 / 高层次人才专章）——绍兴「高层次人才房票：A类500万…」即靠此掩蔽
    '高层次','A类','B类','C类','D类','E类','F类','顶尖人才','特色人才','人才认定',
    # 需认定 / 评审 / 择优 / 考核
    '认定','评审','评选','遴选','择优','选拔','评定','经审核','考核合格','备案为','经市人社','经市委','经用人单位',
    # 特定人才计划 / 人才工程（须入选该计划）
    '紧缺人才计划','产业人才项目','创新创业团队','创新创业人才','后备干部','高青人才','善美英才','百团千才',
    '韩江人才','百千万','青梅计划','扬帆计划','启航计划','人才工程','引进计划','专项计划','人才计划','聚才计划',
    '引育工程','储备人才','党政储备','择优遴选',
    # 急需紧缺目录限定
    '急需紧缺','紧缺人才','紧缺专业','人才目录',
    # 单位 / 编制限定（非「满足学历即可」；不含裸"事业单位"，避免误伤"企事业单位"）
    '机关事业单位','市属单位','市属国有企业','市属国企','党政机关','机关事业','编制','入编',
    # 招聘 / 引进公告形式（非普适政策）
    '招聘公告','引进公告',
    # 数据明示非普适
    '非普适','非普惠','非普惠性','不普惠',
    # 已失效 / 已到期（不得计入现行力度）
    '已到期','已失效','已废止','已停发','原有效期',
    # 附加苛刻条件（非纯学历门槛）
    '第一大股东','最大自然人股东','个人投资','高校目录','优秀大学毕业生','指定高校','一事一议',
    # 需双方（夫妻）同时满足：如绍兴「夫妻双方均为全日制博士共同购房可享150万元」
    '夫妻双方','双方均为','双方均',
]
# 正则型标记（字面词难以覆盖的变体）
# 注：不收录裸「第X类」——阳江「第七类（全日制博士）」正是普通博士档，收录会误伤。
NON_UNIV_RE = [re.compile(p) for p in [
    r'到.{0,4}事业单位',      # 潮州「新引进到本市事业单位和…」
    r'事业单位[、和或]',        # 肇庆「引进到事业单位、市属国有企业」
    r'事业单位招聘',
    r'第[一二三四五六七八九十]+至[一二三四五六七八九十]+类',  # 「第四至六类」跨档合并表述
]]
# 条目级强判定：命中即整条视为非普适（用于「须经认定/择优遴选/已到期」等整条均需审批的情形）
NON_UNIV_ITEM_RE = [re.compile(p) for p in [
    r'经.{0,12}认定', r'须.{0,6}认定', r'需.{0,6}认定', r'认定为',
    r'纳入.{0,14}计划',   # 江门「纳入江门市博士人才年度发展计划」——非纯学历门槛
    r'择优', r'遴选', r'评审', r'评选', r'选拔', r'报批',
    r'已到期', r'已失效', r'已废止', r'原有效期.{0,20}到期',
    r'一事一议', r'非普适', r'非普惠', r'非普惠性',
]]
NON_UNIV_WIN_BEFORE = 30  # 金额前置窗口字数
NON_UNIV_WIN_AFTER = 50   # 金额后置窗口字数（捕获「金额（…紧缺人才计划…）」格式）
# 分句定界：用于判定金额的「所属条款」。不按「、」与括号切分——
# 「15万元生活补贴（机关事业单位紧缺人才计划…）」必须与括号内标记同属一句才能命中。
_CLAUSE_BOUND = re.compile(r'[；;。\n，,]')

def _has_non_univ(seg):
    return any(k in seg for k in NON_UNIV_NEAR) or any(r.search(seg) for r in NON_UNIV_RE)

def _amount_clause(s, pos):
    """返回金额所在分句的起止位置（按 ；。\\n，, 定界，括号内不切分）。"""
    start = 0
    for m in _CLAUSE_BOUND.finditer(s):
        if m.start() >= pos: break
        start = m.end()
    end = len(s)
    for m in _CLAUSE_BOUND.finditer(s, start):
        if m.start() >= pos:
            end = m.start(); break
    return start, end

def _item_non_univ(it):
    """条目级判定（命中即整条非普适）：
      A. 政策【名称】本身即特定人才计划（善美英才/韩江人才/紧缺人才计划/后备干部…）→ 整条不计；
      B. 名称/条件/说明中含「须经认定/择优遴选/已到期」等强标记 → 整条不计。
    名称级判定必要：汕尾「善美英才计划人才房票」、潮州「韩江人才计划购房补贴」等
    靠金额窗口无法稳定命中，但名称已明示属特定计划。"""
    # 字段可信度分级（Phase 29 修复）：只有 name / condition 表达「这是什么政策、谁能领」，
    # 可用全量词表；note / person_req / constraint 描述附加说明与限制，只用强判定正则。
    # 三例实测误杀（均已用本分级修复）——
    #   ① person_req 分层枚举：佛山高明区「领军/博士后/博士/职称/学历分层」提到领军，
    #      却含普通本科 2 万档；
    #   ② note 描述他档：河源 note 写「顶尖人才一事一议1400万、正高200万」，
    #      但本体是博士档 121 万；
    #   ③ constraint 旁支限制：金华「C类及以上高层次人才可放宽至二手商品住房」、
    #      丽水「夫妻双方均符合条件的补助总额…」——非资格门槛，
    #      用全量词表扫会把含普通本科 8 万 / 本科 10 万 的整条误排除。
    # Phase 33：「来源链接已失效」≠「政策已失效」。
    # 实证误杀 8 处（杭州 anju_discount、台州 risk、清远 grad×4/anju/timing）：
    # note 里写「原 gdqy.gov.cn 链接已失效（404）」被强判定正则 r'已失效' 命中 →
    # 【整条政策归零】（清远本科购房补贴 7.2 万 + 生活补助 3.6 万 全部消失）。
    # 故判定前先把「链接/来源/网址/页面/地址/附件 ... 已失效 …」这类句子剥离。
    _DEAD_LINK_RE = re.compile(
        r'(?:链接|来源|网址|页面|地址|附件|URL|url|jsp|html|pdf|post_\d+)'
        r'[^。；，]{0,10}?(?:已失效|已无法访问|已下线|打不开)[^。；]{0,26}')
    def _hit(txt, strong_only=False):
        if not txt: return False
        txt = _DEAD_LINK_RE.sub('', str(txt))
        if not strong_only:
            if any(k in txt for k in NON_UNIV_NEAR): return True
            if any(r.search(txt) for r in NON_UNIV_RE): return True
        return any(r.search(txt) for r in NON_UNIV_ITEM_RE)
    name = str(it.get('name', '') or '')
    if _hit(name):
        return True
    # 毕业生补贴条目无 name 字段，必须靠 condition 兜住
    # （揭阳「符合市急需紧缺专业人才目录」、江门「符合属地急需紧缺产业人才目录」、
    #   阳江「经阳江市认定」、江门「纳入博士人才年度发展计划」）。
    if _hit(str(it.get('condition', '') or '')):
        return True
    for k in ('note', 'person_req', 'constraint'):
        if _hit(str(it.get(k, '') or ''), strong_only=True):
            return True
    return False

_AMT_ANY = re.compile(r'(\d+(?:\.\d+)?)\s*(万元|万|元)')
def _mask_non_univ(text, before=NON_UNIV_WIN_BEFORE, after=NON_UNIV_WIN_AFTER):
    """把「非普适」金额替换为 0万/0元（掩蔽），使后续取最高时不再命中。
    同时覆盖「万」与「元」两类金额（租房多为 元/月 小额）。
    判定窗口为金额【前后对称】，且仅限同一字段文本内，避免跨字段误伤。"""
    s = str(text or '')
    if not s:
        return ''
    out, last = [], 0
    for m in _AMT_ANY.finditer(s):
        c0, c1 = _amount_clause(s, m.start())
        # 判定范围 = 「所属分句」本身。禁止向左回溯越界——
        # 否则会拉入上一分句的标记词（如汕尾普适的「7000元粤东西北就业补贴」
        # 会被下一句「善美英才计划」误杀）。分句内已足够覆盖
        # 「第一类院士500万元」「15万元（机关事业单位紧缺人才计划…）」两类格式。
        ctx = s[c0:c1]
        if _has_non_univ(ctx):
            out.append(s[last:m.start()])
            out.append('0' + ('万' if m.group(2).startswith('万') else '元'))
            last = m.end()
    out.append(s[last:])
    return ''.join(out)

def _grad_wan(text):
    return _scan_wan(_clauses(_mask_non_univ(text)), neg=_GRAD_NEG, inherit_neg=True)

def _norm_level(s):
    """把 item.level 归一化为 专科/本科/硕士/博士（空串=无学历标注）。"""
    s = str(s or '')
    if '博士' in s: return '博士'
    if '硕士' in s or '研究生' in s: return '硕士'
    if '本科' in s or '学士' in s: return '本科'
    if '专科' in s or '大专' in s: return '专科'
    return ''
def _level_rank(lv):
    return {'专科':1,'本科':2,'硕士':3,'博士':4}.get(lv, 99)
# 学历关键词映射（用于购房/租房评分精确匹配学历档）
EDU_KW = {'专科':['专科','大专'],'本科':['本科','学士'],'硕士':['硕士','研究生'],'博士':['博士']}
# 院校额外门槛（Phase 29）：命中则该金额带附加筛选条件，不算「满足学历要求即可」
# 如「双一流本科4万 / 普通本科2万」→ 本科档应取 2 万
ELITE_KW = ['双一流','985','211','重点院校','重点高校','世界一流','QS','泰晤士','名校','一流大学',
            '一流学科','双一流高校','双一流大学','原985','原211']
# 高层次人才档关键词（不计入普通毕业生购房/租房评分兜底）
HIGH_LEVEL_KW = ['杰出','优秀','精英','高层次','领军','院士','特级','首席','名家','名师','名医',
                 'A类','B类','C类','D类','E类','F类','领军人才','特色人才','拔尖','经认定','人才认定']
def _is_high_level_item(name):
    """判断该政策条目是否属高层次人才档（不作为普通毕业生兜底）。"""
    n = str(name or '')
    return any(k in n for k in HIGH_LEVEL_KW)
def _is_elite_level(lv):
    """item.level 含重点院校门槛（双一流/985/211…）→ 该条目属精英档，不作普通类优先计入。
    （Phase 29 普通类优先在 grad 维度的对齐：原 _norm_level('双一流本科')→'本科'，
    导致金华「双一流本科购房15万」顶替「普通本科生活补助4万」计入本科档。）"""
    s = str(lv or '')
    return any(k in s for k in ELITE_KW)
# 按月补贴的【分段】定界符（比 _CLAUSE_BOUND 更细：额外含括号与「+」）
_GRAD_MONTHLY_BOUND = re.compile(r'[，,；;。\n、（(）)+]')
# 租房/租房补贴类：只归 welfare 维度，不在毕业生补贴维度计（防跨维度重复计分）
_RENT_ONLY_KW = ['租房', '租金', '房租', '租赁', '租住']
def _grad_monthly_wan(text):
    """毕业生补贴中的「按月」现金（元/月 × 最长期限，万元）。

    Phase 33 新增：此前 grad 维度只扫「万」金额，政策里的「N元/月 × 最长M个月」全部漏计
    （宁波安居补贴1000元/月×60月=6万、梅州生活补贴5500元/月×5年=33万、清远生活补助
    1000元/月×36月=3.6万 等 9 城 24 条）。

    排除口径按【分段】而非【整句】判定——清远格式为
    「购房补贴2000元/月（最长36个月…）+ 生活补助1000元/月（最长36个月…）」，
    整句内同时含「购房」与「生活补助」，按整句判会把应计的生活补助一起误杀；
    按「+ / 括号 / 逗号」分段后，两段各自判定即可正确分离。

    【租房类一律不计入本维度】——租房补贴统一归 welfare（配套保障·租房补贴）维度计分。
    湖州/金华/梅州实证：同一笔「租房补贴 400元/月」在 grad.cash 与 welfare.detail 里各写一遍，
    若两边都计则同一笔钱在总榜里被加两次（湖州本科 grad 1.44 + welfare 1.44）。"""
    s = _mask_non_univ(str(text or ''))
    best = 0.0
    prev_rent = False
    for m in _MONTHLY.finditer(s):
        start = 0
        for i in range(m.start() - 1, -1, -1):
            if _GRAD_MONTHLY_BOUND.match(s[i]):
                start = i + 1
                break
        seg = s[start:m.start()]
        if any(k in seg for k in _GRAD_NEG):
            prev_rent = False
            continue
        # 租房判定用【分段 + 悬挂继承】而非固定字宽窗口：湖州专科
        # 「租房补贴：湖州市属高校专科 400元/月，其他全日制专科高职 200元/月」
        # ——「200元/月」的分段里没有「租房」二字，30 字回看窗口也刚好把「租」字切在外面；
        # 若分段内无主体词（补贴/补助/津贴…）则视为上一分段的同补贴延续，继承其租房判定。
        has_subj = any(k in seg for k in _SUBJ_KW)
        rent = any(k in seg for k in _RENT_ONLY_KW) or (prev_rent and not has_subj)
        prev_rent = rent
        if rent:
            continue
        best = max(best, float(m.group(1)) * _rent_months(s, m.start()) / 10000.0)
    return round(best, 3)

def _grad_item_wan(it, edu=None):
    """单条毕业生补贴条目的现金+房票力度（取二者较高）。
    edu=None 表示不限学历（维持原口径）；否则仅当该 item.level 归一化等于 edu 时计入。
    普适口径：条目级强判定命中（须经认定/择优遴选/已到期）→ 整条记 0。"""
    if edu:
        if _norm_level(it.get('level','')) != edu:
            return 0.0
    if _item_non_univ(it):
        return 0.0
    return max(_grad_wan(it.get('cash','') or ''), _grad_wan(it.get('house_voucher','') or ''),
               _grad_monthly_wan(it.get('cash','') or ''), _grad_monthly_wan(it.get('house_voucher','') or ''))

def _welfare_rent_wan(text, edu=None, item=None):
    """配套保障维度内的租房/安居现金补贴，统一量化为「年化现金（万元）」。
    品级门控：整条需含租房/居住类关键词（租/居住/住房/安居/住宿/驿站/人才公寓）才计入；
    整条文本扫描金额（避免分句割裂跨句上下文），以金额前后 15 字窗口判定：
      - 是否「按月」（含"月"）→ 年化 ×12；否则按一次性 /10000；
      - 学历档（本科/硕士/博士/专科）→ 优先取本科档，否则取最低一档；
    排除购房/贷款/公积金类噪声；纯折扣（6折/免租比例）不计。
    edu=None：本科优先→否则最低档（去高层次污染）；edu=具体学历：仅取该学历档，无则返回0。
    普适口径（Phase 28）：先经 _mask_non_univ 掩蔽特定人才计划/需认定/非普适金额；
    条目级强判定命中（须经认定/择优遴选/已到期）→ 整条记 0。"""
    if item is not None and _item_non_univ(item):
        return 0.0
    s = _mask_non_univ(text)
    RENT_KEYS = ['租', '居住', '住房', '安居', '住宿', '驿站', '人才公寓']
    if not any(k in s for k in RENT_KEYS):
        return 0.0
    # Phase 33：汇总金额（合计/共计/总计）跳过，避免与分项重复计分（见 _SUM_KW 注释）
    NEG = ['贷款', '公积金', '公积', '购房', '房票', '共有产权', '产权'] + _SUM_KW
    def near_neg(i):
        return any(k in s[max(0, i-15):i+15] for k in NEG)
    def edu_of(i):
        # Phase 32：优先「金额所在分段」（按 ；，、/ 等定界）判定学历档——密集档位列表
        # （「博士1500元/月、硕士1000元/月、普通本科600元/月」）中固定 15 字窗口会跨档污染
        # （600元 前窗沾『硕士』）；分段内无学历词再回退 15 字窗口（保留跨句容错）。
        start = 0
        for j in range(i-1, -1, -1):
            if s[j] in '；;，,、/（(【[':
                start = j + 1; break
        seg = s[start:i]
        for scope in (seg, s[max(0, i-15):i+15]):
            # 重点院校门槛（Phase 29 分档对齐）：「双一流本科800元/月」不并入普通本科档
            #（「非'双一流'」否定表述不算门槛，嘉善式「非双一流本科」仍归普通本科）。
            if any(k in scope for k in ELITE_KW) and '非' not in scope:
                return '重点院校'
            for lv in ('博士', '硕士', '本科', '专科'):
                if lv in scope or (lv == '硕士' and '研究生' in scope) or (lv == '本科' and '学士' in scope) or (lv == '专科' and '大专' in scope):
                    return lv
        return ''
    entries = []  # (level, wan)
    # Phase 33：按月补贴按政策标注的【最长期限】累计，而非固定年化 12 个月
    for m in _MONTHLY.finditer(s):
        if near_neg(m.start()): continue
        entries.append(('', float(m.group(1)) * _rent_months(s, m.start()) / 10000.0))
    for m in _AMT_YUAN_YEAR.finditer(s):
        if near_neg(m.start()): continue
        entries.append(('', float(m.group(1)) / 10000.0))
    for m in _AMT_YUAN.finditer(s):
        if near_neg(m.start()): continue
        monthly = '月' in s[max(0, m.start()-15):m.end()+15]
        v = float(m.group(1))
        entries.append((edu_of(m.start()), v * _rent_months(s, m.start()) / 10000.0 if monthly else v / 10000.0))
    for m in _AMT_WAN.finditer(s):
        if near_neg(m.start()): continue
        entries.append((edu_of(m.start()), float(m.group(1))))
    if not entries:
        return 0.0
    if edu:
        # 精确学历档：仅取该学历金额，无则0（不兜底）
        matched = [w for l, w in entries if l == edu]
        return round(max(matched), 3) if matched else 0.0
    # edu=None（"全部"档）≡ 本科档。禁止跨学历档兜底——
    # 原「否则取最低档」会把硕士/博士档租房补贴算进"全部"，
    # 导致佛山全部档 0.9万（实为硕士 750元/月）而本科档为 0，自相矛盾。
    under = [w for l, w in entries if l == '本科']
    return round(max(under), 3) if under else 0.0

def _startup_wan(text):
    """创业扶持力度：仅计面向初创企业/创业者的现金补贴（一次性创业补贴、场租补贴、带动就业补贴等）；
    排除创业担保贷款/贴息，以及人才团队/大赛/基金/创投类项目资助（属高层次人才项目支持，量级不同易失真）。"""
    cs = _clauses(text)
    NEG = ['贷款','借款','贴息','信贷','大赛','项目资助','基金','创投','团队','孵化器','孵化','众创','科技','风投']
    POS = ['补贴','资助','奖励','场租','房租','安家','生活','扶持','金']
    return max(_scan_wan(cs, neg=NEG, pos=POS), _scan_yuan_to_wan(cs, neg=NEG, pos=POS))

def _anju_subsidy_wan(items, edu=None):
    """购房补贴/房票力度（万元）。
    扫描 discount + price_base 两个字段的「万」金额。
    edu=None（"全部"档）≡ 本科档：仅取本科档金额，无则 0。
    edu=具体学历：仅取金额前12字含该学历关键词者，取最高；无该学历档则返回0（不兜底）。
    排除高层次人才档（杰出/优秀/精英/领军/院士/特级/首席/A-F类等）作为普通毕业生兜底。
    普适口径（Phase 28）：各字段先经 _mask_non_univ 掩蔽特定人才计划/需认定/非普适金额。
    本科分档（Phase 29）：优先「普通/其他本科」金额，「双一流/985/211/重点院校」属额外门槛，
      仅在无普通本科金额时才采用（佛山普通本科2万 vs 双一流本科4万 → 取2万）。"""
    best_plain = 0.0   # 命中目标学历档·普通类（无院校门槛）的最高金额
    best_elite = 0.0   # 命中目标学历档·重点院校类的最高金额（无普通类时才用）
    target = edu or '本科'   # edu=None（"全部"档）≡ 本科档
    for it in items:
        if _item_non_univ(it):   # 条目级强判定：须经认定/择优遴选/已到期 → 整条不计
            continue
        if _is_high_level_item(it.get('name', '')):   # 政策名即高层次/领军/杰出档 → 整条不计
            continue
        for field_name in ('discount', 'price_base'):
            txt = _mask_non_univ(it.get(field_name, '') or '')
            for m in _AMT_WAN.finditer(txt):
                amt = float(m.group(1))
                if amt <= 0:
                    continue
                # 学历档识别：优先取「金额所在分段」（按 ；，、/ 定界），
                # 避免「双一流本科4万/普通本科2万」中 2 万的前缀跨过「/」误沾「双一流」。
                # 但「/」也可能只是并列限定（宁波「本科/中级职称最高16万」），
                # 此时分段内无学历词 → 回退到 20 字窗口再判，避免漏匹配。
                start = 0
                for i in range(m.start()-1, -1, -1):
                    if txt[i] in '；;，,、/（(【[':
                        start = i + 1; break
                seg = txt[start:m.start()]
                wide = txt[max(0, m.start()-20):m.start()]
                def _lvl_of(s):
                    for lv, kws in EDU_KW.items():
                        if any(k in s for k in kws):
                            return lv
                    return None
                lvl_hit = _lvl_of(seg)
                probe = seg if lvl_hit else wide
                if lvl_hit is None:
                    lvl_hit = _lvl_of(wide)
                if lvl_hit != target:
                    continue
                # 院校额外门槛；「非'双一流'本科」这类否定表述不算门槛（嘉善县非双一流本科10万）
                elite = any(k in probe for k in ELITE_KW) and '非' not in probe
                if elite:
                    best_elite = max(best_elite, amt)
                else:
                    best_plain = max(best_plain, amt)
    # 普通类优先（无院校额外门槛）→ 否则重点院校类 → 否则 0（禁止跨学历档兜底）
    return round(best_plain if best_plain > 0 else best_elite, 2)

# ---- 人工复核覆盖（关键词无法稳定判定的复合条件，逐条核实后固化）----
# 键 = (城市, 维度, 学历档)；值 = 普适金额（万元）。命中则直接返回，跳过启发式。
# 注：合并后的城市对象仅含 meta/dimensions，无 city 键 → 城市名由 city_dim_score 参数传入。
# 【中山·博士】cash 混列「新培养引进博士20万」与「出站留中山+境外+10万，共52万」；
#   52万需「博士后出站 + 留中山 + 境外引进」复合条件，非博士学历即可 → 取普适的 20 万。
# 【韶关·博士·购房】50万为「博士后出站(基地)后」专享，普通新引进博士为 20 万 → 取 20 万。
UNIV_OVERRIDE = {
    ('中山', 'grad_subsidy', '博士'): 20.0,
    ('韶关', 'anju_subsidy', '博士'): 20.0,
}

def _rankable_items(items):
    """Phase 38：区级政策**不参与排名**（用户 2026-09-08 决策）。

    只保留 district 为「市级」或未标注的条目参与评分。
    未标注（无 district 字段）的条目 = 尚未做区级标注的城市数据，向后兼容全部计入。

    ⚠️ 这条是防护栏：区级政策门槛各异、口径不统一，若计入会把城市总榜拉偏
       （如淳安县本科 4 万 > 杭州市级 1 万，混算会让杭州虚高）。
    """
    return [it for it in items if (it.get('district') or '市级') == '市级']


def city_dim_score(city_data, dim, edu=None, city=''):
    items = city_data['dimensions'].get(dim, {}).get('items', [])
    # Phase 38：评分只看市级条目，区级仅查阅不计分
    items = _rankable_items(items)
    ov = UNIV_OVERRIDE.get((city, dim, edu))
    if ov is not None:
        return ov
    if dim == 'grad_subsidy':
        # edu=None（"全部"档）≡ 本科档。
        # 禁止「无本科档则取最低学历档」兜底——该兜底会把硕士/博士档现金算进"全部"，
        # 导致中山全部档 20万（实为博士档）而本科档 10万、肇庆全部档 3万而本科档 0，自相矛盾。
        target = edu or '本科'
        pool_all = [it for it in items if _norm_level(it.get('level','')) == target]
        # Phase 29 分档对齐（Phase 32 修复）：普通类优先，重点院校档（level 含双一流/985/211）
        # 仅在普通类无金额时兜底——与 _anju_subsidy_wan 的 best_plain/best_elite 逻辑一致。
        plain = [it for it in pool_all if not _is_elite_level(it.get('level',''))]
        elite = [it for it in pool_all if _is_elite_level(it.get('level',''))]
        v_plain = round(max([_grad_item_wan(it, target) for it in plain], default=0.0), 2)
        v_elite = round(max([_grad_item_wan(it, target) for it in elite], default=0.0), 2)
        return v_plain if v_plain > 0 else v_elite
    if dim == 'anju_subsidy':
        return _anju_subsidy_wan(items, edu)
    if dim == 'welfare':
        return round(max([_welfare_rent_wan(it.get('detail', ''), edu, it) for it in items], default=0.0), 3)
    if dim == 'startup':
        return round(max([_startup_wan(it.get('detail', '') or it.get('type', '')) for it in items], default=0.0), 3)
    return 0.0

RANK_DIMS = ['grad_subsidy','anju_subsidy','welfare','startup']
# 按学历分组的排名评分：RANK_SCORES_BY_EDU[edu][dim][city] = score
# edu='全部' ≡ 本科档（Phase 29：禁跨学历档兜底）；其余按精确学历档
EDU_LEVELS = ['全部','专科','本科','硕士','博士']
RANK_SCORES_BY_EDU = {}
for _edu in EDU_LEVELS:
    _e = None if _edu == '全部' else _edu
    RANK_SCORES_BY_EDU[_edu] = {dim: {c: city_dim_score(_allcities[c], dim, _e, c) for c in _allcities} for dim in RANK_DIMS}
# 兼容旧引用（默认"全部"口径）
RANK_SCORES = RANK_SCORES_BY_EDU['全部']
SCORES = {'grad_subsidy': RANK_SCORES['grad_subsidy']}  # 仅毕业生补贴参与对比表金色高亮

DATA_JSON = json.dumps(cities_payload, ensure_ascii=False)
SUM_JSON = json.dumps(summary_payload, ensure_ascii=False)
SCORES_JSON = json.dumps(SCORES, ensure_ascii=False)
RANK_SCORES_JSON = json.dumps(RANK_SCORES, ensure_ascii=False)
RANK_SCORES_BY_EDU_JSON = json.dumps(RANK_SCORES_BY_EDU, ensure_ascii=False)
# Phase 39 T4：区内力度排名（仅 2 维现金：grad_subsidy + anju_subsidy；本科口径，与城市总榜"全部≡本科"一致）
# city -> {district: {'rank':int(降序), 'score':float(万元)}}
DISTRICT_RANK = {}
for _city, _cd in _allcities.items():
    _ds = {}
    for _dim in ('grad_subsidy', 'anju_subsidy'):
        _items = _cd['dimensions'].get(_dim, {}).get('items', [])
        for _it in _items:
            _d = _it.get('district') or '市级'
            if _d == '市级':
                continue
            if _dim == 'grad_subsidy':
                _amt = _grad_item_wan(_it, '本科')
            else:
                _amt = _anju_subsidy_wan([_it])  # edu=None ≡ 本科
            _ds[_d] = _ds.get(_d, 0.0) + _amt
    _ordered = sorted(_ds.items(), key=lambda x: -x[1])
    DISTRICT_RANK[_city] = {_d: {'rank': i + 1, 'score': round(_s, 2)} for i, (_d, _s) in enumerate(_ordered)}
DISTRICT_RANK_JSON = json.dumps(DISTRICT_RANK, ensure_ascii=False)
EDU_JSON = json.dumps(edu_payload, ensure_ascii=False)
META_JSON = json.dumps({'updated': d['meta'].get('updated',''), 'provinces': PROV, 'order': ORDER}, ensure_ascii=False)

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人才政策图谱 · 引才 + 安居（浙江 / 广东）</title>
<!-- 字体使用系统衬线栈（宋体/Georgia），无外部依赖 -->
<style>
:root{
  --bg:#f5f1e8; --bg2:#efe8d8; --bg3:#faf7f0;
  --ink:#1a1612; --ink-soft:#5a5148; --muted:#8a8073;
  --line:rgba(26,22,18,.12); --line-strong:rgba(26,22,18,.22);
  --gold:#9a7b3f; --danger:#b23a2e; --danger-bg:rgba(178,58,46,.08);
  --serif:"Songti SC","STSong","Noto Serif SC",Georgia,"Times New Roman",serif;
  --latin:Georgia,"Times New Roman",serif;
}
*{box-sizing:border-box;margin:0;padding:0}
html{background:var(--bg);scroll-behavior:smooth}
body{background:var(--bg);color:var(--ink);font-family:var(--serif);line-height:1.7;-webkit-font-smoothing:antialiased;max-width:1200px;margin:0 auto;padding:12px 28px 90px}
a{color:var(--gold);text-decoration:none}
.wrap{width:100%;max-width:none;margin:0;padding:0}
.kicker{font-family:var(--latin);letter-spacing:.42em;text-transform:uppercase;font-size:.72rem;color:var(--muted);text-align:center}
.masthead{padding:64px 0 30px;text-align:center}
.wordmark{font-family:var(--serif);font-weight:600;font-size:clamp(2.6rem,7vw,4.4rem);letter-spacing:.34em;padding-left:.34em;margin:14px 0 10px}
.sub{font-family:var(--latin);letter-spacing:.3em;text-transform:uppercase;font-size:.8rem;color:var(--ink-soft)}
.rule{height:1px;background:var(--line-strong);margin:30px auto 0;max-width:240px;position:relative}
.rule::after{content:"";position:absolute;left:50%;top:-3px;width:7px;height:7px;background:var(--gold);transform:translateX(-50%) rotate(45deg)}
.provtabs{display:flex;gap:12px;justify-content:center;margin:18px 0 4px;flex-wrap:wrap}
.lede{font-size:1.02rem;color:var(--ink-soft);max-width:760px;margin:26px auto 8px;text-align:center;font-weight:400}
.toolbar{display:flex;gap:14px;align-items:center;justify-content:center;flex-wrap:wrap;margin:34px 0 10px;position:sticky;top:0;z-index:30;background:linear-gradient(var(--bg) 78%,transparent);padding:14px 0}
.search{position:relative}
.search input{background:var(--bg2);border:1px solid var(--line-strong);color:var(--ink);font-family:var(--serif);
  font-size:1rem;padding:12px 18px 12px 40px;width:300px;outline:none;letter-spacing:.04em}
.search input:focus{border-color:var(--gold)}
.search::before{content:"⌕";position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--muted);font-size:1.2rem}
.btn{background:transparent;border:1px solid var(--line-strong);color:var(--ink);font-family:var(--serif);
  font-size:.95rem;letter-spacing:.16em;padding:12px 26px;cursor:pointer;transition:.25s}
.btn:hover{border-color:var(--gold);color:var(--gold)}
.btn.solid{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:500}
.btn.solid:hover{background:var(--gold);border-color:var(--gold);color:var(--bg)}
.btn:disabled{opacity:.35;cursor:not-allowed}
/* Phase 42 门户返回入口：固定悬浮左上角，默认隐藏，仅当从门户首页进入时点亮 */
.portal-back{position:fixed;top:14px;left:20px;z-index:60;display:none;align-items:center;gap:8px;
  background:rgba(250,247,240,.94);border:1px solid var(--line-strong);color:var(--ink-soft);
  font-family:var(--serif);font-size:.8rem;letter-spacing:.14em;
  padding:9px 16px 9px 14px;text-decoration:none;backdrop-filter:blur(8px);
  transition:color .22s,border-color .22s,background .22s}
.portal-back.on{display:inline-flex}
.portal-back:hover{color:var(--gold);border-color:var(--gold);background:var(--bg3)}
.portal-back .ar{font-family:var(--latin);font-size:.95rem;line-height:1;letter-spacing:0}
@media print{.portal-back{display:none!important}}
.index{margin:18px 0 60px}
.cityrow{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:22px 6px;border-bottom:1px solid var(--line);
  cursor:pointer;transition:.25s}
.cityrow:hover{padding-left:18px}
.cityrow:hover .cname{color:var(--gold)}
.cname{font-family:var(--serif);font-weight:600;font-size:clamp(1.5rem,3.4vw,2.2rem);letter-spacing:.14em;
  transition:.25s;display:flex;align-items:baseline;gap:16px}
.cname .en{font-family:var(--latin);font-size:.9rem;letter-spacing:.28em;color:var(--muted);text-transform:uppercase}
.ctag{font-family:var(--latin);font-size:.74rem;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.crankscore{margin-left:auto;font-family:var(--latin);font-size:.78rem;letter-spacing:.02em;color:var(--ink-soft);font-weight:500;white-space:nowrap;text-align:right;line-height:1.5}
.crankscore .rk-line{display:block}
.crankscore b{font-family:var(--serif);font-size:1.05rem;color:var(--gold);font-weight:700}
.rankboard{margin:26px auto 6px;max-width:980px}
.rb-head{font-family:var(--serif);font-size:1.05rem;letter-spacing:.12em;color:var(--ink);margin:14px 0 14px;border-left:4px solid var(--gold);padding-left:12px}
.rb-head span{color:var(--gold);font-weight:600}
.rblist{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px}
.rbitem{display:flex;align-items:center;gap:10px;padding:9px 13px;border:1px solid var(--line);border-radius:8px;background:var(--bg2)}
.rbno{font-family:var(--serif);font-weight:700;font-size:1.05rem;color:var(--gold);min-width:24px;text-align:center}
.rbcity{font-family:var(--serif);font-weight:600;letter-spacing:.08em;flex:1;
  background:transparent;border:0;padding:0;margin:0;text-align:left;color:inherit;cursor:pointer;
  border-bottom:1px dashed var(--line-strong);transition:color .15s,border-color .15s}
.rbcity:hover{color:var(--gold);border-bottom-color:var(--gold)}
.rbcity:focus-visible{outline:2px solid var(--gold);outline-offset:3px;border-radius:3px}
.rbprov{font-size:.68rem;color:var(--muted);letter-spacing:.1em;white-space:nowrap}
.rbscore{font-family:var(--latin);font-size:.78rem;color:var(--ink);white-space:nowrap}
.empty{text-align:center;color:var(--muted);padding:40px;font-family:var(--latin);letter-spacing:.2em}
/* drawer */
.scrim{position:fixed;inset:0;background:rgba(0,0,0,.6);opacity:0;visibility:hidden;transition:.3s;z-index:40}
.scrim.on{opacity:1;visibility:visible}
.drawer{position:fixed;inset:0;width:100vw;height:100vh;max-height:none;overflow-y:auto;background:var(--bg2);border:none;
  transform:none;opacity:0;visibility:hidden;transition:.3s cubic-bezier(.2,.7,.2,1);z-index:50}
.drawer.on{opacity:1;visibility:visible;transform:none}
.dhead{padding:40px 44px 26px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg2);z-index:2}
.dclose{position:absolute;top:24px;right:30px;background:var(--danger,#d9483b);border:1px solid var(--danger,#d9483b);color:#fff;
  width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:1.18rem;font-family:var(--latin);line-height:1;
  box-shadow:0 2px 10px rgba(217,72,59,.35);transition:.2s}
.dclose:hover{background:#b6372b;border-color:#b6372b;box-shadow:0 4px 14px rgba(217,72,59,.5)}
.dhead-edu{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:16px}
.cmp-edu{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.edufilter{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.edulabel{font-family:var(--latin);letter-spacing:.2em;text-transform:uppercase;font-size:.72rem;color:var(--muted);margin-right:2px}
.echip{background:transparent;border:1px solid var(--line-strong);color:var(--ink-soft);font-family:var(--serif);
  font-size:.82rem;letter-spacing:.12em;padding:6px 14px;cursor:pointer;transition:.2s;border-radius:2px}
.echip:hover{border-color:var(--gold);color:var(--gold)}
.echip.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.echip.on:hover{background:var(--gold);border-color:var(--gold);color:var(--bg)}
.dtitle{font-family:var(--serif);font-weight:600;font-size:2.4rem;letter-spacing:.16em;margin-top:6px}
.dtitle .en{display:block;font-family:var(--latin);font-size:.8rem;letter-spacing:.3em;color:var(--muted);text-transform:uppercase;margin-top:6px}
.dbody{padding:10px 44px 60px}
.sec{margin-top:30px}
.seclabel{font-family:var(--latin);letter-spacing:.3em;text-transform:uppercase;font-size:.72rem;color:var(--gold);
  border-bottom:1px solid var(--line);padding-bottom:8px;margin-bottom:14px;display:flex;align-items:center;gap:12px}
.seclabel::before{content:"";width:18px;height:1px;background:var(--gold)}
.item{padding:12px 0;border-bottom:1px dotted var(--line);font-size:.97rem}
.item .ih{color:var(--ink);font-weight:500;letter-spacing:.04em}
.item .ib{color:var(--ink-soft);display:block;margin-top:3px;font-size:.93rem}
.src{display:block;margin-top:7px;font-family:var(--latin);font-size:.72rem;letter-spacing:.04em;color:var(--muted)}
.src a{color:var(--muted);text-decoration:underline;text-underline-offset:2px}
.risk .seclabel{color:var(--danger)}
.risk .item{background:var(--danger-bg);border:1px solid rgba(201,122,106,.28);padding:12px 14px;margin-bottom:8px}
.risk .ih{color:var(--danger)}
/* city detail table (参考文件表格形式) */
table.dt{width:100%;border-collapse:collapse;font-size:.9rem;margin-top:6px}
table.dt th,table.dt td{border:1px solid var(--line);padding:10px 13px;text-align:left;vertical-align:top}
table.dt thead th{background:var(--bg3);font-family:var(--serif);font-weight:600;letter-spacing:.08em;color:var(--ink)}
table.dt tr.sec td{background:var(--bg3);font-weight:700;letter-spacing:.04em;color:var(--ink);font-size:.96rem}
table.dt td.dim{font-weight:600;color:var(--ink);min-width:118px;width:26%}
table.dt td.amtcell{width:26%;vertical-align:top;background:rgba(154,123,63,.04)}
table.dt td .amt{color:var(--gold);font-weight:700;line-height:1.5}
table.dt td .noamt{color:var(--muted);opacity:.6}
.frow{margin-top:3px}
.frow .flab{color:var(--muted)}
table.dt .src{display:block;margin-top:7px;font-family:var(--latin);font-size:.72rem;letter-spacing:.02em;color:var(--muted);word-break:break-all}
table.dt .src a{color:var(--muted);text-decoration:underline;text-underline-offset:2px}
table.dt tr.risk td{background:var(--danger-bg)}
table.dt tr.risk td.dim{color:var(--danger)}
/* Phase 37：高层次人才专项·「仅查阅·不参与排名」徽标 */
.hl-badge{display:inline-block;margin-left:10px;padding:2px 8px;font-size:.7rem;letter-spacing:.06em;
  color:var(--gold);border:1px solid rgba(154,123,63,.45);background:rgba(154,123,63,.08);
  border-radius:2px;vertical-align:middle;font-weight:400}
/* Phase 38：市/区范围筛选器 + 区名标签 */
.dhead-dist{display:flex;gap:8px;align-items:center;justify-content:center;flex-wrap:wrap;margin-top:14px}
.dchip{padding:5px 12px;font-size:.8rem;letter-spacing:.08em;background:transparent;
  border:1px solid var(--line-strong);color:var(--ink-soft);cursor:pointer;border-radius:2px;
  transition:.18s;font-family:inherit}
.dchip:hover{border-color:var(--gold);color:var(--gold)}
.dchip.on{background:var(--gold);border-color:var(--gold);color:#fff}
.dist-tag{display:inline-block;position:relative;margin-right:8px;padding:1px 7px;font-size:.68rem;letter-spacing:.05em;
  color:var(--ink-soft);border:1px solid var(--line-strong);border-radius:2px;vertical-align:middle;
  background:rgba(26,22,18,.03)}
.dist-tag.city{color:var(--gold);border-color:rgba(154,123,63,.4);background:rgba(154,123,63,.06)}
/* Phase 39 T4：区级政策右上角序号徽标（区内力度排名） */
.dist-rank{position:absolute;top:-7px;right:-7px;min-width:15px;height:15px;line-height:15px;text-align:center;
  font-size:.56rem;font-weight:700;color:#fff;background:var(--gold);border-radius:50%;padding:0 2px;
  box-shadow:0 1px 3px rgba(0,0,0,.28);font-family:var(--latin)}
/* Phase 39 T3：每条政策附「原文关于现金的简短原话」（≤10字） */
.cash-quote{margin-top:5px;font-size:.7rem;color:var(--gold);letter-spacing:.03em;font-family:var(--serif)}
.dist-note{display:block;margin-top:8px;font-size:.72rem;color:var(--muted);letter-spacing:.04em}
/* compare overlay */
.cmp-scrim{position:fixed;inset:0;background:rgba(0,0,0,.72);opacity:0;visibility:hidden;transition:.3s;z-index:60}
.cmp-scrim.on{opacity:1;visibility:visible}
.cmp{position:fixed;left:50%;top:50%;transform:translate(-50%,-46%);width:min(720px,94vw);max-height:86vh;overflow-y:auto;
  background:var(--bg2);border:1px solid var(--line-strong);padding:34px 36px;z-index:70;opacity:0;visibility:hidden;transition:.3s}
.cmp.on{opacity:1;visibility:visible;transform:translate(-50%,-50%)}
.cmp h3{font-family:var(--serif);font-weight:600;letter-spacing:.14em;font-size:1.5rem;margin-bottom:6px}
.cmp .hint{color:var(--ink-soft);font-size:.9rem;margin-bottom:18px}
.cmp-close{position:absolute;top:16px;right:18px;background:var(--danger,#d9483b);border:1px solid var(--danger,#d9483b);color:#fff;
  width:38px;height:38px;border-radius:50%;cursor:pointer;font-size:1.18rem;font-family:var(--latin);line-height:1;
  box-shadow:0 2px 10px rgba(217,72,59,.35);transition:.2s;z-index:3}
.cmp-close:hover{background:#b6372b;border-color:#b6372b;box-shadow:0 4px 14px rgba(217,72,59,.5)}
.chips{display:flex;flex-direction:column;gap:14px;margin-bottom:18px}
.cmp-prov-h{font-family:var(--latin);letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:var(--gold);margin:0 0 8px}
.cmp-prov-cities{display:flex;flex-wrap:wrap;gap:10px}
.chip{border:1px solid var(--line-strong);padding:9px 16px;cursor:pointer;font-family:var(--serif);letter-spacing:.1em;
  color:var(--ink-soft);transition:.2s;user-select:none}
.chip:hover{border-color:var(--gold)}
.chip.on{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:500}
.cmp-actions{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.cwarn{color:var(--danger);font-size:.88rem;letter-spacing:.04em;min-height:1.2em}
/* compare table */
.ctable-wrap{margin-top:22px;overflow-x:auto}
/* 等宽：固定布局 + 首列定宽，其余城市列自动均分 → 每栏宽度一致 */
table.ct{width:100%;border-collapse:collapse;font-size:.86rem;table-layout:fixed;min-width:560px}
table.ct th,table.ct td{border:1px solid var(--line);padding:11px 12px;text-align:left;vertical-align:top;
  overflow-wrap:anywhere;word-break:break-word}
table.ct thead th{font-family:var(--serif);font-weight:600;letter-spacing:.1em;background:var(--bg3);
  position:sticky;top:0;color:var(--ink)}
table.ct thead th:first-child{width:96px}
table.ct thead th .prov{display:block;font-family:var(--latin);letter-spacing:.12em;text-transform:uppercase;font-size:.62rem;color:var(--gold);font-weight:500;margin-top:3px}
table.ct tbody th{font-family:var(--latin);letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;
  color:var(--gold);background:var(--bg3);white-space:nowrap;width:96px}
/* 补贴力度最高城市高亮（口径A：最高档总补贴=现金+房票，单位万；金色背景） */
table.ct td.max-cell{background:linear-gradient(135deg,#f6ecce,#e7d29a);box-shadow:inset 0 0 0 2px var(--gold);
  font-weight:600;color:var(--ink)}
table.ct td.max-cell .ln:first-child::after{content:" ★";color:var(--gold);font-weight:700}
table.ct td .ln{display:block;padding:2px 0;border-bottom:1px dotted var(--line);font-size:.83rem}
table.ct td .ln:last-child{border-bottom:none}
table.ct tr.risk td{background:var(--danger-bg)}
table.ct tr.risk th{color:var(--danger)}
.cmp-legend{display:flex;align-items:center;gap:10px;margin:0 0 10px;font-size:.82rem;color:var(--ink-soft)}
.cmp-legend .swatch{display:inline-block;width:18px;height:14px;border-radius:3px;
  background:linear-gradient(135deg,#f6ecce,#e7d29a);box-shadow:inset 0 0 0 2px var(--gold);flex:0 0 auto}
/* 力度排名控件 + 排名行 */
.rank-ctrl{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin:14px 0 8px}
.rank-ctrl .rlabel{font-family:var(--latin);letter-spacing:.16em;text-transform:uppercase;font-size:.72rem;color:var(--gold)}
.rchips{display:flex;gap:8px;flex-wrap:wrap}
.rchip{border:1px solid var(--line-strong);padding:7px 14px;cursor:pointer;font-family:var(--serif);
  letter-spacing:.04em;color:var(--ink-soft);transition:.2s;user-select:none;font-size:.86rem}
.rchip:hover{border-color:var(--gold)}
.rchip.on{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:500}
table.ct tr.rankrow th{color:#3f6b3f;background:linear-gradient(135deg,#eef6ee,#dcecdc)}
table.ct td.rankcell{background:linear-gradient(135deg,#eef6ee,#dcecdc);box-shadow:inset 0 0 0 2px #6e9e6e;
  font-weight:600;text-align:center;vertical-align:middle}
table.ct td.rankcell .rkscore{display:block;font-family:var(--latin);font-size:.64rem;color:var(--ink-soft);font-weight:400;margin-top:3px}
.csection{max-width:none;margin:0;padding:20px 0 80px}
.csection h2{font-family:var(--serif);font-weight:600;letter-spacing:.16em;font-size:1.8rem;margin:20px 0 6px}
.csection .back{margin-bottom:14px}
footer.global{text-align:center;padding:40px 20px 70px;color:var(--muted);font-size:.82rem;border-top:1px solid var(--line);margin-top:30px}
footer.global .src-note{font-family:var(--latin);letter-spacing:.12em}
footer.global .beian{margin-top:16px;display:flex;flex-wrap:wrap;gap:6px 20px;justify-content:center;align-items:center;font-family:var(--latin);letter-spacing:.04em;font-size:.78rem}
footer.global .beian a{display:inline-flex;align-items:center;gap:5px;color:var(--muted);text-decoration:none;border-bottom:1px solid transparent;transition:color .18s,border-color .18s}
footer.global .beian a:hover{color:var(--gold);border-bottom-color:var(--gold)}
@media(max-width:620px){
  .wrap{padding:0 18px}
  .search input{width:100%}
  .drawer{padding:0}
  .dhead,.dbody{padding-left:22px;padding-right:22px}
  .dbody{padding-left:22px;padding-right:22px}
}
</style>
</head>
<body>

<!-- Phase 42 门户返回入口：默认隐藏，仅当从门户首页进入时由脚本点亮 -->
<a class="portal-back" id="portalBack" href="/"><span class="ar">←</span>返回首页</a>

<header class="masthead wrap">
  <h1 class="wordmark">人才政策</h1>
  <div class="rule"></div>
</header>

<div class="rank-ctrl wrap" id="rbCtrl">
  <span class="rlabel">统计维度（可多选 · 按所选维度总额排名）</span>
  <div class="rchips" id="rbDims"></div>
  <span class="rlabel" style="margin-left:16px">学历</span>
  <div class="rchips" id="eduFilter"></div>
</div>

<section class="rankboard wrap" id="rankBoard"></section>

<div class="provtabs wrap" id="provTabs"></div>

<div class="toolbar wrap">
  <div class="search"><input id="search" type="text" placeholder="搜索城市名…" autocomplete="off"></div>
  <button class="btn" id="compareBtn">对比城市</button>
</div>

<nav class="index wrap" id="cityIndex"></nav>

<p class="lede wrap">本图谱汇集浙江省与广东省各地级市的人才引进与人才安居政策，按「毕业生补贴 / 落户 / 配套保障 / 创业扶持 / 申报路径」五维引才，叠加「先租后售人才房 / 定向优惠价购房 / 人才购房补贴·房票 / 企业内部福利房」四维安居，共十二维结构化整理（含时效提醒、风险提示与高层次人才专项）。全部条目来源均为政府单位（*.gov.cn），逐条附来源单位、文号与原文链接可溯源，且已剔除新闻、自媒体转述及已到期/暂停政策。点击省份切换查看对应城市，点城市看细则（按钮旁即显全省 + 全国双力度排名），详情页可切「全市 / 仅市级 / 具体区」查看区级加码（区级条目右上角数字为区内力度排名，区级金额不计入城市总榜），或选 2–10 城并排对比（对比表按所选城市相对排名）；对比表支持按政策力度排名。页首另设 32 城力度总榜与统计维度筛选（毕业生补贴 / 租房补贴 / 购房补贴·房票，可多选，随维度选择器联动，可切单维/总额），总榜与统计维度默认按<b>本科口径</b>评分（紧邻的学历行可切全部 / 专科 / 硕士 / 博士），抽屉与对比表内的学历筛选则默认「全部」、只影响表格显示条目，点击总榜城市名可查看该城细则。</p>

<footer class="global">
  <div class="src-note">SOURCE · 所有政策条目均引自政府单位（*.gov.cn），采集截至 <span id="updated"></span></div>
  <div style="margin-top:8px">本页为结构化整理，非官方发布；落地申报请以各地最新政府文件及「浙里办」为准。</div>
  <!-- 备案信息：工信部要求首页底部标明 ICP 备案编号并链接 beian.miit.gov.cn；
       公安联网备案要求在首页底部悬挂编号并链接 beian.gov.cn。
       盾牌图标用内联 SVG 而非官方外链图片，以维持本页「零外部资源」的自包含约束。 -->
  <div class="beian">
    <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener noreferrer">粤ICP备2026107109号-1</a>
    <a class="police" href="https://www.beian.gov.cn/portal/registerSystemInfo?recordcode=33019202003186" target="_blank" rel="noopener noreferrer" title="公安联网备案查询"><svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path fill="currentColor" d="M8 1 2 3.2v4.3C2 11.4 4.6 14.2 8 15c3.4-.8 6-3.6 6-7.5V3.2L8 1zm0 1.6 4.4 1.6v3.3c0 3-1.9 5.2-4.4 5.9-2.5-.7-4.4-2.9-4.4-5.9V4.2L8 2.6z"/><path fill="currentColor" d="M7.2 9.9 5.1 7.8l.9-.9 1.2 1.2 2.6-2.6.9.9z"/></svg>浙公网安备33019202003186号</a>
  </div>
</footer>

<!-- 详情抽屉 -->
<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer">
  <div class="dhead">
    <button class="dclose" id="dclose">✕</button>
    <div class="dtitle" id="dtitle"></div>
    <div class="dhead-edu" id="drawerEdu"></div>
    <div class="dhead-dist" id="drawerDist"></div>
  </div>
  <div class="dbody" id="dbody">
    <div id="dtable"></div>
  </div>
</aside>

<!-- 对比选择 -->
<div class="cmp-scrim" id="cmpScrim"></div>
<div class="cmp" id="cmp">
  <button class="cmp-close" id="cmpCloseX" aria-label="关闭">✕</button>
  <h3>对比城市</h3>
  <div class="hint">可跨省选择 2–10 个城市并排对比（最多 10 个）。点击城市卡片切换选中，支持浙江 + 广东混选。</div>
  <div class="cmp-edu" id="cmpEdu"></div>
  <div class="chips" id="cmpChips"></div>
  <div class="cmp-actions">
    <button class="btn solid" id="genCmp" disabled>生成对比表</button>
    <button class="btn" id="cmpClose">取消</button>
    <span class="cwarn" id="cmpWarn"></span>
  </div>
</div>

<!-- 对比结果 -->
<section class="csection" id="cmpResult" style="display:none">
  <button class="btn back" id="cmpBack">← 返回选择</button>
  <h2 id="cmpTitle">城市政策对比</h2>
  <div class="rank-ctrl" id="rankCtrl">
    <span class="rlabel">力度排名维度（勾选 ≥2 按总额）</span>
    <div class="rchips" id="rchips"></div>
  </div>
  <div class="ctable-wrap"><table class="ct" id="ctable"></table></div>
</section>

<script>
/* Phase 42 门户来路判定：仅当从门户首页进入时才显示「返回首页」。
   判定顺序：① 本标签页已记录（sessionStorage，兼容站内刷新）
             ② 同源 referrer 且路径为门户根（/ 或 /index.html）
   非同源、file:// 打开、直接输入地址访问 → 一律不显示。 */
(function(){
  var KEY='portal-entry';
  function detect(){
    try{ if(sessionStorage.getItem(KEY)==='1') return true; }catch(e){}
    var r='';
    try{ r=document.referrer||''; }catch(e){ return false; }
    if(!r) return false;
    try{
      var u=new URL(r);
      if(!u.origin||u.origin==='null'||u.origin!==location.origin) return false;
      if(/^\/(index\.html)?$/.test(u.pathname)){
        try{ sessionStorage.setItem(KEY,'1'); }catch(e){}
        return true;
      }
    }catch(e){}
    return false;
  }
  function apply(){
    if(!detect()) return;
    var el=document.getElementById('portalBack');
    if(el) el.className='portal-back on';
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply);
  else apply();
})();
const DATA = /*__DATA__*/;
const SUMMARY = /*__SUMMARY__*/;
const SCORES = /*__SCORES__*/;
const RANK_SCORES = /*__RANK_SCORES__*/;
const RANK_SCORES_BY_EDU = /*__RANK_SCORES_BY_EDU__*/;
const DISTRICT_RANK = /*__DISTRICT_RANK__*/;
const META = /*__META__*/;
const DIM_ORDER = ['grad_subsidy','hukou','welfare','startup','apply_path',
  'anju_rent2sale','anju_discount','anju_subsidy','anju_enterprise',
  'anju_highlevel',  // Phase 37 恢复：独立维度·仅查阅·不参与排名
  'timing','risk'];
const DIM_LABEL = {grad_subsidy:'毕业生补贴',hukou:'落户',startup:'创业扶持',welfare:'配套保障',timing:'时效提醒',risk:'风险提示',apply_path:'申报路径',
  anju_rent2sale:'先租后售人才房',anju_discount:'定向优惠价购房',anju_subsidy:'人才购房补贴/房票',anju_enterprise:'企业内部福利房',
  anju_highlevel:'高层次人才专项'  // Phase 37
};
const SCHEMA = {
  grad_subsidy:[['level','学历'],['cash','现金'],['house_voucher','房票'],['condition','条件'],['note','备注']],
  hukou:[['target','对象'],['rule','规则']],
  startup:[['type','类型'],['detail','内容'],['note','备注']],
  welfare:[['type','类型'],['detail','内容']],
  timing:[['item','事项'],['detail','说明']],
  risk:[['item','风险'],['detail','说明']],
  apply_path:[['platform','平台'],['materials','材料'],['process','流程'],['phone','咨询']],
  anju_rent2sale:[['name','政策'],['expiry','到期'],['project','房源项目'],['rent_years','租期/可租年限'],['price_base','价格基准'],['rent_deduct','租金抵扣'],['biz_req','企业要求'],['person_req','个人要求'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['enterprise_only','企业员工限定'],['note','说明']],
  anju_discount:[['name','政策'],['expiry','到期'],['project','房源项目'],['price_base','价格基准'],['biz_req','企业要求'],['person_req','个人要求'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['enterprise_only','企业员工限定'],['note','说明']],
  anju_subsidy:[['name','政策'],['expiry','到期'],['biz_req','企业要求'],['person_req','个人要求'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['enterprise_only','企业员工限定'],['note','说明']],
  anju_enterprise:[['name','政策'],['expiry','到期'],['project','房源项目'],['price_base','价格基准'],['biz_req','企业要求'],['person_req','个人要求'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['enterprise_only','企业员工限定'],['note','说明']],
  // Phase 37：高层次人才专项——独立维度·仅查阅·不参与排名
  // 数据格式 {class, subsidy, source, note}。source 是对象，前端渲染跳过对象字段，
  // 仅展示 class/subsidy/note 三列。来源链接在统一脚注块（policySource）输出。
  anju_highlevel:[['class','人才类别'],['subsidy','补贴/待遇'],['note','备注']]
};
// 三安居维度减篇幅：仅展示核心字段
const TRIM_FIELDS = {
  anju_discount:[['name','政策'],['price_base','价格基准'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['note','说明']],
  anju_subsidy:[['name','政策'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['note','说明']],
  anju_enterprise:[['name','政策'],['discount','优惠力度'],['constraint','约束/退出'],['channel','办理渠道'],['note','说明']]
};
document.getElementById('updated').textContent = META.updated;
// 页眉副标题（#subline）与上方 kicker 已按用户要求移除。
// setSub 保留为空实现：切换省份 / 筛选时仍会调用它，删掉函数会 ReferenceError。
// 不要误当成 bug 去「修」。
let activeProv = META.provinces[0];
let activeOrder = activeProv.cities.slice();
let curCity=null; let lastCmp=[];
function setSub(){}
function renderProvTabs(){
  const box=document.getElementById('provTabs'); if(!box) return;
  box.innerHTML='';
  META.provinces.forEach(p=>{
    const el=document.createElement('div');
    el.className='chip'+(p.key===activeProv.key?' on':'');
    el.textContent=p.name;
    el.onclick=()=>{
      activeProv=p; activeOrder=p.cities.slice();
      renderProvTabs(); setSub(); renderIndex('');
      closeDrawer(); document.getElementById('cmpResult').style.display='none';
    };
    box.appendChild(el);
  });
}
setSub(); renderProvTabs();

function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
// 维度序号 → 中文数字（支持到 13 维：一…十、十一、十二、十三）
function cnNum(n){const u=['','一','二','三','四','五','六','七','八','九','十'];if(n<=10)return u[n];if(n<20)return '十'+u[n-10];const t=Math.floor(n/10),o=n%10;return u[t]+'十'+(o?u[o]:'');}

// ---- 城市索引 ----
const indexEl = document.getElementById('cityIndex');
let curFilter='';
function refreshRanks(){ renderIndex(curFilter); }
function renderIndex(filter){
  curFilter=filter||'';
  const full = activeOrder; // 当前省份城市
  const provRank = rankWithin(full);
  const total = full.length;
  const natRank = rankWithin(ALL_CITIES); // 全部 32 城排名
  const natTotal = ALL_CITIES.length;
  indexEl.innerHTML='';
  const cities = full.filter(c=>!curFilter || c.includes(curFilter));
  if(!cities.length){indexEl.innerHTML='<div class="empty">未找到匹配城市</div>';return;}
  cities.forEach(c=>{
    const row=document.createElement('div');
    row.className='cityrow';
    row.innerHTML=`<div class="cinfo"><div class="cname">${esc(c)}<span class="en">${esc(pinyin(c))}</span></div>
      <div class="ctag">市级 · ${DIM_ORDER.length} 维已采集</div></div>
      <div class="crankscore">
        <div class="rk-line">全省 <b>第 ${provRank[c]}</b> / ${total}</div>
        <div class="rk-line">全国 <b>第 ${natRank[c]}</b> / ${natTotal}</div>
      </div>`;
    row.onclick=()=>openDrawer(c);
    indexEl.appendChild(row);
  });
}
const PY={杭州:'Hangzhou',宁波:'Ningbo',温州:'Wenzhou',嘉兴:'Jiaxing',湖州:'Huzhou',绍兴:'Shaoxing',金华:'Jinhua',衢州:'Quzhou',舟山:'Zhoushan',台州:'Taizhou',丽水:'Lishui',
广州:'Guangzhou',深圳:'Shenzhen',珠海:'Zhuhai',佛山:'Foshan',东莞:'Dongguan',中山:'Zhongshan',惠州:'Huizhou',江门:'Jiangmen',肇庆:'Zhaoqing',汕头:'Shantou',湛江:'Zhanjiang'};
function pinyin(c){return PY[c]||'';}

// 单城政策表格（参考文件表格形式：行=维度/项目，列=该城市内容，含分区标题+来源脚注）
// Phase 39 T3：从现金类字段优先派生「原文关于现金的简短原话」（≤10字），用于每条政策展示
function cashQuote(it){
  const src=[it.cash,it.house_voucher,it.subsidy,it.discount,it.detail,it.note]
    .filter(function(v){return v&&String(v).trim();})
    .map(function(v){return String(v);}).join(' ');
  if(!src) return '';
  let q='';
  const m=src.match(/[\s\S]*?万/);
  if(m) q=m[0];
  else { const m2=src.match(/[\s\S]*?[元年月条]/); q=m2?m2[0]:src.slice(0,10); }
  if(q.length>10) q=q.slice(0,10);
  return q;
}
// ---- Phase 41 T1：金额优先三列式 ----
// 金额字段映射（仅分类展示既有文本，不解析、不换算、不编造）
const AMT_FIELDS={
  grad_subsidy:['cash','house_voucher'],
  anju_subsidy:['discount'],
  anju_discount:['discount'],
  anju_enterprise:['discount','price_base'],
  anju_rent2sale:['price_base','rent_deduct','discount'],
  anju_highlevel:['subsidy']
};
function amountish(v){const s=String(v||'');return /\d/.test(s)&&/(万|元|折|%|％|月|平米|㎡|年)/.test(s);}
function amtCellHTML(it,dim){
  const keys=AMT_FIELDS[dim]||[];
  let vals=keys.map(k=>it[k]).filter(v=>v&&String(v).trim()&&String(v).trim()!=='—').map(v=>String(v).trim());
  // welfare/startup 无独立金额字段：detail 含金额特征时整体放金额列（仍为原文）
  if(!vals.length&&(dim==='welfare'||dim==='startup')&&amountish(it.detail)) vals=[String(it.detail).trim()];
  if(!vals.length) return '<span class="noamt">—</span>';
  let h=vals.map(v=>`<div class="amt">${esc(v)}</div>`).join('');
  const q=cashQuote(it);
  if(q) h+=`<div class="cash-quote">原文「${esc(q)}」</div>`;
  return h;
}
// ---- Phase 41 T2：doc_no 展示级拆分（只搬运既有文字，不新增内容）----
// 形态：纯文号 / 文号《全称》 / 文号（备注） / 纯文件名 → 拆出 文号 / 全称 / 备注
function splitDocNo(doc){
  const out={doc:'',title:'',note:''};
  let s=String(doc||'').trim(); if(!s) return out;
  const m=s.match(/[^《》（）]*[〔\[]\s*\d{4}\s*[〕\]]\s*\d+\s*号/);
  if(m){out.doc=m[0].trim();s=s.replace(m[0],'').trim();}
  const t=s.match(/《([^》]+)》/);
  if(t){out.title=t[1];s=s.replace(t[0],'').trim();}
  const n=s.match(/（([^）]+）)/);
  if(n){out.note=n[1];s=s.replace(n[0],'').trim();}
  if(!out.doc&&!out.title&&s){out.title=s;s='';}
  else if(s){out.note=out.note?(out.note+'；'+s):s;}
  return out;
}
// ---- Phase 41 T2：细粒度来源行 ----
// 有文号：《全称》（文号）· 机构 · 发布 日期 · 生效/修订 · 适用 · URL
// 无文号：机构 · 《标题》 · 发布 日期 · 适用 · URL
function fineSource(it,city){
  const s=it.source||{};
  const sp=splitDocNo(s.doc_no);
  const title=s.title||sp.title||'';
  const doc=sp.doc||'';
  const parts=[];
  if(title) parts.push('《'+esc(title)+'》');
  if(doc) parts.push(esc(doc));
  if(s.unit) parts.push(esc(s.unit));
  if(s.date) parts.push('发布 '+esc(s.date));
  if(s.effective) parts.push(esc(s.effective));
  if(sp.note&&!s.effective) parts.push(esc(sp.note));
  if(it.district&&it.district!=='市级') parts.push('适用：'+esc(city)+'·'+esc(it.district));
  const u=s.url?`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.url)}</a>`:'';
  if(!parts.length&&!u) return '';
  return `<span class="src">来源：${parts.join(' · ')}${u?((parts.length?' ｜ ':'')+u):''}</span>`;
}
function cityTableHTML(city){
  const data=DATA[city];
  const CN=DIM_ORDER.map((_,i)=>cnNum(i+1));
  let html='<table class="dt"><thead><tr><th>维度 / 项目</th><th>金额 / 优惠</th><th>说明 · 来源</th></tr></thead><tbody>';
  let vi=0;
  DIM_ORDER.forEach((dim,idx)=>{
    const orig=(data.dimensions[dim].items||[]);
    // Phase 38：先按市/区范围过滤，再走占位 + 学历过滤
    let items=orig.filter(it=> it.official !== false && eduMatchTags(eduTagsJS(it, dim)) && distMatch(it));
    // Phase 37：高层次人才专项维度·占位条目也显示一行提示（其他维度占位条目仍按默认隐藏）
    if (dim === 'anju_highlevel' && !items.length) {
      const ph = orig.find(it=> it.official === false);
      if (ph) items = [ph];
    }
    if(!items.length) return;
    vi++;
    const fields=TRIM_FIELDS[dim] || SCHEMA[dim];
    const titleKeys=fields.map(f=>f[0]).filter(k=>k!=='note'&&k!=='condition');
    const amtKeys=new Set(AMT_FIELDS[dim]||[]);
    // Phase 37：高层次人才专项·徽标「仅查阅·不参与排名」
    const hlBadge = dim === 'anju_highlevel' ? ' <span class="hl-badge">仅查阅·不参与排名</span>' : '';
    html+=`<tr class="${dim==='risk'?'sec risk':'sec'}"><td colspan="3">${cnNum(vi)}、${esc(DIM_LABEL[dim])}${hlBadge}</td></tr>`;
    items.forEach(it=>{
      let title='', usedKey='';
      for(const k of titleKeys){ const v=it[k]; if(v!=null&&String(v).trim()!==''&&String(v).trim()!=='—'){ title=esc(v); usedKey=k; break; } }
      // 说明列：除标题键与金额键外的字段，逐字段一行
      let frows='';
      fields.forEach(([k,lab])=>{
        if(k==='source'||k===usedKey||amtKeys.has(k)) return;
        const v=it[k];
        if(v==null||String(v).trim()===''||String(v).trim()==='—') return;
        frows+=`<div class="frow"><span class="flab">${esc(lab)}：</span>${esc(v)}</div>`;
      });
      const src=fineSource(it,city);
      const dRankInfo = (it.district && it.district !== '市级' && DISTRICT_RANK[city] && DISTRICT_RANK[city][it.district]) ? DISTRICT_RANK[city][it.district] : null;
      const dTag = (!it.district || it.district === '市级') ? '' : `<span class="dist-tag">${esc(it.district)}<span class="dist-rank">${dRankInfo?dRankInfo.rank:''}</span></span>`;
      html+=`<tr class="${dim==='risk'?'risk':''}"><td class="dim">${dTag}${title}</td><td class="amtcell">${amtCellHTML(it,dim)}</td><td>${frows}${src}</td></tr>`;
    });
  });
  html+='</tbody></table>';
  return html;
}

// ---- 搜索（仅城市名）----
document.getElementById('search').addEventListener('input',e=>{
  renderIndex(e.target.value.trim());
});

// ---- 学历筛选（Phase 41b 拆分双口径）----
// 页首「学历」行（#eduFilter，位于统计维度之后）：控制总榜/统计维度评分口径 boardEdu，默认本科
// 抽屉（#drawerEdu）/对比（#cmpEdu）的学历行：控制表格显示哪些学历条目 eduFilter，默认全部
const EDU_BTNS = ['全部','专科','本科','硕士','博士'];
let eduFilter = '全部';
let boardEdu = '本科';
const EDU_KW = {'专科':['专科','大专'],'本科':['本科','学士'],'硕士':['硕士','研究生'],'博士':['博士']};
const EDU_ORDER = ['专科','本科','硕士','博士','不限'];
function eduTagsJS(it, dim){
  // 与 Python edu_tags 同源：grad_subsidy 用 level 字段，其余维度扫描政策文本关键词
  const texts = [];
  if (dim === 'grad_subsidy') texts.push(it.level || '');
  for (const k of ['detail','note','condition','name','rule','target','cash','house_voucher','type','project','discount','person_req','biz_req','enterprise_only']){
    const v = it[k]; if (v) texts.push(String(v));
  }
  const blob = texts.join(' ');
  const tags = new Set();
  for (const lvl in EDU_KW){ if (EDU_KW[lvl].some(kw => blob.includes(kw))) tags.add(lvl); }
  if (!tags.size) tags.add('不限');
  return EDU_ORDER.filter(x => tags.has(x));
}
function eduMatchTags(tags){
  if (eduFilter === '全部') return true;
  return tags && tags.indexOf(eduFilter) >= 0;
}
function renderEduChips(){
  // 页首学历行 → 总榜口径 boardEdu（切「全部」即看全学历总额口径）
  const bf = document.getElementById('eduFilter');
  if (bf) {
    bf.innerHTML = '';
    const lab = document.createElement('span'); lab.className='edulabel'; lab.textContent='学历'; bf.appendChild(lab);
    EDU_BTNS.forEach(lbl=>{
      const b = document.createElement('button');
      b.className = 'echip' + (lbl === boardEdu ? ' on' : '');
      b.textContent = lbl;
      b.onclick = ()=>{ boardEdu = lbl; syncEduUI(); refreshRanks(); renderRankBoard(); if(lastCmp.length) buildCompareTable(lastCmp); };
      bf.appendChild(b);
    });
  }
  // 抽屉学历行 → 表格条目过滤 eduFilter
  const de = document.getElementById('drawerEdu');
  if (de) {
    de.innerHTML = '';
    if (!de.querySelector('.edulabel')) { const lab=document.createElement('span'); lab.className='edulabel'; lab.textContent='学历'; de.appendChild(lab); }
    EDU_BTNS.forEach(lbl=>{
      const b = document.createElement('button');
      b.className = 'echip' + (lbl === eduFilter ? ' on' : '');
      b.textContent = lbl;
      b.onclick = ()=>{ eduFilter = lbl; syncEduUI(); if(curCity) document.getElementById('dtable').innerHTML = cityTableHTML(curCity); };
      de.appendChild(b);
    });
  }
  // 对比学历行 → 对比表条目过滤 eduFilter
  const ce = document.getElementById('cmpEdu');
  if (ce) {
    ce.innerHTML = '';
    if (!ce.querySelector('.edulabel')) { const lab=document.createElement('span'); lab.className='edulabel'; lab.textContent='学历'; ce.appendChild(lab); }
    EDU_BTNS.forEach(lbl=>{
      const b = document.createElement('button');
      b.className = 'echip' + (lbl === eduFilter ? ' on' : '');
      b.textContent = lbl;
      b.onclick = ()=>{ eduFilter = lbl; syncEduUI(); if(lastCmp.length) buildCompareTable(lastCmp); };
      ce.appendChild(b);
    });
  }
}
function syncEduUI(){
  document.querySelectorAll('#eduFilter .echip').forEach(b=>b.classList.toggle('on', b.textContent === boardEdu));
  document.querySelectorAll('#drawerEdu .echip, #cmpEdu .echip').forEach(b=>b.classList.toggle('on', b.textContent === eduFilter));
}
function applyEduAndRanks(){
  // 兼容旧调用名：重渲当前抽屉 + 对比表 + 城市按钮徽标 + 32城总榜
  if (curCity) document.getElementById('dtable').innerHTML = cityTableHTML(curCity);
  if (lastCmp.length) buildCompareTable(lastCmp);
  refreshRanks();
  renderRankBoard();
}
function applyEdu(){
  // 兼容旧调用名
  applyEduAndRanks();
}

// ---- Phase 38：市/区范围筛选（区级政策仅查阅·不参与排名）----
// 取值：'全市'(默认·市级+所有区) / '仅市级' / 具体区名(市级+该区，因市级在该区同样适用)
let distFilter = '全市';
function cityDistricts(city){
  // 该城市出现的全部区名（按出现顺序去重）；无区级数据则返回空数组
  const set = new Set();
  DIM_ORDER.forEach(dim=>{
    (DATA[city].dimensions[dim].items||[]).forEach(it=>{
      const d = it.district;
      if (d && d !== '市级') set.add(d);
    });
  });
  return [...set];
}
function distMatch(it){
  const d = it.district || '市级';
  if (distFilter === '全市') return true;
  if (distFilter === '仅市级') return d === '市级';
  // 选具体区：市级通用政策 + 该区自己的政策（市级在该区同样生效，隐藏会误导）
  return d === '市级' || d === distFilter;
}
function renderDistChips(city){
  const box = document.getElementById('drawerDist'); if (!box) return;
  const dists = cityDistricts(city);
  box.innerHTML = '';
  // 该市无区级数据 → 不显示筛选器
  if (!dists.length) { box.style.display = 'none'; return; }
  box.style.display = 'flex';
  if (distFilter !== '全市' && distFilter !== '仅市级' && !dists.includes(distFilter)) distFilter = '全市';
  const opts = ['全市', '仅市级', ...dists];
  opts.forEach(lbl=>{
    const b = document.createElement('button');
    b.className = 'dchip' + (lbl === distFilter ? ' on' : '');
    b.textContent = lbl;
    b.onclick = ()=>{ distFilter = lbl; renderDistChips(city); document.getElementById('dtable').innerHTML = cityTableHTML(city); };
    box.appendChild(b);
  });
  // 口径说明，避免用户误以为区级金额计入了排名（先清旧 note 再挂，防重复）
  const oldNote = box.parentNode.querySelector('.dist-note');
  if (oldNote) oldNote.remove();
  const note = document.createElement('span');
  note.className = 'dist-note';
  note.textContent = '区级政策仅查阅、不计入力度排名（各区门槛口径不统一，混算会拉偏总榜）';
  box.parentNode.appendChild(note);
}

// ---- 详情抽屉 ----
const drawer=document.getElementById('drawer'), scrim=document.getElementById('scrim');
function openDrawer(city){
  const data=DATA[city];
  curCity=city;
  distFilter='全市';
  document.getElementById('dtitle').innerHTML=`${esc(city)}<span class="en">${esc(pinyin(city))}</span>`;
  document.getElementById('dtable').innerHTML=cityTableHTML(city);
  renderDistChips(city);
  drawer.classList.add('on'); scrim.classList.add('on'); drawer.scrollTop=0;
}
function closeDrawer(){drawer.classList.remove('on');scrim.classList.remove('on');}
document.getElementById('dclose').onclick=closeDrawer;
scrim.onclick=closeDrawer;

// ---- 对比 ----
const cmp=document.getElementById('cmp'), cmpScrim=document.getElementById('cmpScrim');
const cmpChips=document.getElementById('cmpChips'), genBtn=document.getElementById('genCmp'), cmpWarn=document.getElementById('cmpWarn');
let selected=new Set();
document.getElementById('compareBtn').onclick=()=>{
  selected.clear(); renderChips(); validateCmp();
  cmp.classList.add('on'); cmpScrim.classList.add('on');
};
function closeCmp(){cmp.classList.remove('on');cmpScrim.classList.remove('on');}
document.getElementById('cmpClose').onclick=closeCmp;
document.getElementById('cmpCloseX').onclick=closeCmp;
cmpScrim.onclick=closeCmp;
const CITY2PROV={};
META.provinces.forEach(p=>p.cities.forEach(c=>{CITY2PROV[c]=p.name;}));
function renderChips(){
  cmpChips.innerHTML='';
  META.provinces.forEach(p=>{
    const grp=document.createElement('div'); grp.className='cmp-prov';
    const h=document.createElement('div'); h.className='cmp-prov-h'; h.textContent=p.name;
    const box=document.createElement('div'); box.className='cmp-prov-cities';
    p.cities.forEach(c=>{
      const el=document.createElement('div');
      el.className='chip'+(selected.has(c)?' on':'');
      el.textContent=c;
      el.onclick=()=>{
        if(selected.has(c)) selected.delete(c); else selected.add(c);
        renderChips(); validateCmp();
      };
      box.appendChild(el);
    });
    grp.appendChild(h); grp.appendChild(box);
    cmpChips.appendChild(grp);
  });
}
function validateCmp(){
  const n=selected.size;
  genBtn.disabled = !(n>=2 && n<=10);
  if(n>10) cmpWarn.textContent='⚠ 最多对比 10 个城市，已选 '+n+' 个，请取消 '+(n-10)+' 个。';
  else if(n===1) cmpWarn.textContent='再选至少 1 个城市即可对比。';
  else cmpWarn.textContent='';
}
genBtn.onclick=()=>{
  if(selected.size<2||selected.size>10) return;
  lastCmp=[...selected];
  buildCompareTable(lastCmp);
  closeCmp();
};
// ---- 力度排名（交互）----
const RANK_DIMS_ALL=[['grad_subsidy','毕业生补贴'],['welfare','租房补贴'],['anju_subsidy','购房补贴/房票']];
let rankSel=new Set(RANK_DIMS_ALL.map(x=>x[0])); // 默认全选 3 维
const rchips=document.getElementById('rchips');
const ALL_CITIES = META.provinces.flatMap(p=>p.cities);
// 32 城力度总榜：始终跨浙江+广东全部城市排序，跟随上方「力度排名维度」选择器（单维/总额）联动
function renderRankBoard(){
  const el=document.getElementById('rankBoard'); if(!el) return;
  const label=RANK_DIMS_ALL.filter(x=>rankSel.has(x[0])).map(x=>x[1]).join(' + ');
  const arr=ALL_CITIES.map(c=>({c,s:cityRankScore(c),prov:CITY2PROV[c]||''})).sort((a,b)=>b.s-a.s);
  let html='<div class="rb-head">'+ALL_CITIES.length+' 城力度总榜 · <span>'+esc(label)+'</span></div><ol class="rblist">';
  let r=0,prev=null;
  arr.forEach((o,i)=>{ if(o.s!==prev){r=i+1;prev=o.s;}
    html+='<li class="rbitem"><span class="rbno">'+r+'</span>'
        + '<button class="rbcity" type="button" data-city="'+esc(o.c)+'" title="查看 '+esc(o.c)+' 政策详情">'+esc(o.c)+'</button>'
        + '<span class="rbprov">'+esc(o.prov)+'</span><span class="rbscore">'+o.s+' 万</span></li>'; });
  html+='</ol>';
  el.innerHTML=html;
  // 总榜城市可点击 → 直接打开该城详情抽屉（与城市索引行为一致）
  el.querySelectorAll('.rbcity').forEach(b=>{
    b.onclick=()=>{ openDrawer(b.getAttribute('data-city')); };
  });
}
function buildRankChips(container){
  container.innerHTML='';
  RANK_DIMS_ALL.forEach(([k,lab])=>{
    const el=document.createElement('span');
    el.className='rchip'+(rankSel.has(k)?' on':'');
    el.textContent=lab;
    el.onclick=()=>toggleRankDim(k);
    container.appendChild(el);
  });
}
function toggleRankDim(k){
  if(rankSel.has(k)) rankSel.delete(k); else rankSel.add(k);
  if(rankSel.size===0) rankSel.add(k); // 至少保留 1 个维度
  renderRankChips();   // 同步两处 chips（总榜 + 对比区）
  refreshRanks();      // 同步城市按钮徽标
  renderRankBoard();   // 同步 32 城总榜
  if(lastCmp.length) buildCompareTable(lastCmp);
}
// 总榜页首与对比结果区共用同一 rankSel 状态，任一处切换两处同步
function renderRankChips(){
  buildRankChips(rchips);
  const rb=document.getElementById('rbDims');
  if(rb) buildRankChips(rb);
}
function cityRankScore(c){
  // Phase 41b：总榜/统计口径用 boardEdu（页首学历行，默认本科）；抽屉/对比表格过滤用 eduFilter
  const tbl = RANK_SCORES_BY_EDU[boardEdu] || RANK_SCORES_BY_EDU['全部'];
  let s=0;rankSel.forEach(d=>s+=(tbl[d]&&tbl[d][c])||0);
  return Math.round(s*100)/100;   // Phase 35：浮点尾数修复（1.0+1.44+5.0=7.4399999999999995）
}
function rankWithin(list){
  const arr=list.map(c=>({c,s:cityRankScore(c)})).sort((a,b)=>b.s-a.s);
  const map={};let r=0,prev=null;
  arr.forEach((o,i)=>{ if(o.s!==prev){r=i+1;prev=o.s;} map[o.c]=r; });
  return map;
}
function renderRankRow(t, cities){
  if(rankSel.size===0) return;
  const rm=rankWithin(cities); // 相对排名：仅在所选城市内排序
  const label=RANK_DIMS_ALL.filter(x=>rankSel.has(x[0])).map(x=>x[1]).join(' + ');
  let rk=`<tr class="rankrow"><th>力度排名<br><span style="font-weight:400;font-size:.6rem;letter-spacing:0">${esc(label)}</span></th>`;
  cities.forEach(c=>{
    const sc=cityRankScore(c); const r=rm[c];
    rk+=`<td class="rankcell">第 ${r} / ${cities.length}<span class="rkscore">${sc} 万</span></td>`;
  });
  rk+='</tr>';
  t.insertAdjacentHTML('afterbegin', rk);
}
const HL_DIMS=['grad_subsidy']; // 仅毕业生补贴维度可量化，参与金色高亮
function buildCompareTable(cities){
  const res=document.getElementById('cmpResult');
  document.getElementById('cmpTitle').textContent='城市政策对比 · '+cities.join(' / ');
  const t=document.getElementById('ctable');
  // 图例（仅插入一次）
  const wrap=document.querySelector('#cmpResult .ctable-wrap');
  if(!wrap.querySelector('.cmp-legend')){
    const leg=document.createElement('div'); leg.className='cmp-legend';
    leg.innerHTML='<span class="swatch"></span><span>金色背景 = 该维度「补贴力度最高」城市（口径：现金取各档最高、房票取各档最高，二者相加，单位万元）；并列最高则同标注。</span>';
    wrap.insertBefore(leg, wrap.firstChild);
  }
  let html='<thead><tr><th></th>'+cities.map(c=>`<th>${esc(c)}<span class="prov">${esc(CITY2PROV[c]||'')}</span></th>`).join('')+'</tr></thead><tbody>';
  DIM_ORDER.forEach(dim=>{
    html+=`<tr class="${dim==='risk'?'risk':''}"><th>${esc(DIM_LABEL[dim])}</th>`;
    const maxScore = HL_DIMS.includes(dim) ? Math.max(...cities.map(c=>SCORES[dim][c]||0)) : 0;
    cities.forEach(c=>{
      const recs=(SUMMARY[c][dim]||[]).filter(r=>eduMatchTags(r.e));
      const lines=recs.map(r=>r.t);
      const cell=lines.length?lines.map(l=>`<span class="ln">${esc(l)}</span>`).join(''):'<span class="ln" style="color:var(--muted)">—</span>';
      let cls='', title='';
      if(HL_DIMS.includes(dim) && maxScore>0 && (SCORES[dim][c]||0)===maxScore){
        cls=' class="max-cell"';
        title=` title="本维度补贴力度最高：${SCORES[dim][c]} 万（口径：现金取各档最高 + 房票取各档最高）"`;
      }
      html+=`<td${cls}${title}>${cell}</td>`;
    });
    html+='</tr>';
  });
  html+='</tbody>';
  t.innerHTML=html;
  renderRankRow(t, cities);
  res.style.display='block';
  if(res.scrollIntoView) res.scrollIntoView({behavior:'smooth'});
}
document.getElementById('cmpBack').onclick=()=>{
  document.getElementById('cmpResult').style.display='none';
  cmp.classList.add('on'); cmpScrim.classList.add('on');
};

renderRankChips();
renderEduChips();
renderRankBoard();
renderIndex('');
</script>
</body>
</html>
"""

html = (TEMPLATE
        .replace('/*__DATA__*/', DATA_JSON)
        .replace('/*__SUMMARY__*/', SUM_JSON)
        .replace('/*__SCORES__*/', SCORES_JSON)
        .replace('/*__RANK_SCORES__*/', RANK_SCORES_JSON)
        .replace('/*__RANK_SCORES_BY_EDU__*/', RANK_SCORES_BY_EDU_JSON)
        .replace('/*__DISTRICT_RANK__*/', DISTRICT_RANK_JSON)
        .replace('/*__META__*/', META_JSON))

open(OUT, 'w', encoding='utf-8', newline='\n').write(html)
print("写入:", OUT)
print("文件大小:", os.path.getsize(OUT), "bytes")
print("城市数:", len(cities_payload), "| 维度序:", DIM_ORDER)
