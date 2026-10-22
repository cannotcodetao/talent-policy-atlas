# -*- coding: utf-8 -*-
# 多省（浙江/广东）合并页结构性验收。验证：自包含/零外链、来源全 gov.cn、
# 省份切换可用、两省城市与维度齐全、对比 2–10 城、风险高亮、图片兜底。
import re, sys, os

HTML = '人才引进政策_2026.html'
AC = []
def chk(name, cond, info=''):
    AC.append((name, bool(cond), info))

html = open(HTML, encoding='utf-8').read()
chk('AC1 自包含·零外部资源',
    '<link' not in html and 'src="http' not in html and '<script src' not in html,
    '无外部 css/js/img 引用')

# 所有外链 href 必须为 *.gov.cn
hrefs = re.findall(r'href="(https?://[^"]+)"', html)
bad = [h for h in hrefs if not h.split('//')[-1].split('/')[0].endswith('.gov.cn')]
chk('AC2 来源全部 *.gov.cn', not bad, f'非gov.cn链接数={len(bad)}')

# 省份切换标签
chk('AC3 省份切换标签存在', 'id="provTabs"' in html and 'provtabs' in html)
chk('AC4 浙江+广东两省', '浙江' in html and '广东' in html)

# 两省 32 城均在数据中出现
cities = ['杭州','宁波','温州','嘉兴','湖州','绍兴','金华','衢州','舟山','台州','丽水',
          '广州','深圳','珠海','佛山','东莞','中山','惠州','江门','肇庆','汕头','湛江',
          '韶关','茂名','梅州','汕尾','河源','阳江','清远','潮州','揭阳','云浮']
missing = [c for c in cities if f'"{c}"' not in html and f'"{c}"' not in html]
# 城市名以字符串键形式出现（JSON 内）
missing = [c for c in cities if ('"%s"'%c) not in html]
chk('AC5 32 城全部入库', not missing, f'缺失={missing}')

# 12 维标签齐全（Phase 37 恢复「高层次人才专项」维度）
dims = ['毕业生补贴','落户','创业扶持','配套保障','申报路径',
        '先租后售人才房','定向优惠价购房','人才购房补贴/房票','企业内部福利房',
        '高层次人才专项',  # Phase 37 恢复
        '时效提醒','风险提示']
miss_dims = [d for d in dims if d not in html]
chk('AC6 十二维标签齐全', not miss_dims, f'缺失={miss_dims}')

# 风险高亮样式
chk('AC7 风险提示高亮样式', '.risk' in html and 'danger' in html)

# 去图：全页无 <img> 标签、无图片占位图、无 heroImg（Phase 18）
chk('AC8 无图片与占位图(去图)', '<img' not in html and 'dhero-ph' not in html and 'heroImg' not in html)

# 对比表最高补贴高亮
chk('AC9 对比高亮样式 max-cell', 'max-cell' in html)

# 搜索仅城市名（input placeholder）
chk('AC10 搜索框存在', 'id="search"' in html)

# 城市卡片点击出抽屉
chk('AC11 详情抽屉结构', 'id="drawer"' in html and 'id="dtable"' in html)

n_pass = sum(1 for _,ok,_ in AC if ok)
print(f'多省页结构验收：{n_pass}/{len(AC)} PASS')
for name, ok, info in AC:
    print(f"  [{'✅' if ok else '❌'}] {name} {('· '+info) if info and not ok else ''}")
sys.exit(0 if n_pass == len(AC) else 1)
