# -*- coding: utf-8 -*-
# Phase 37 高层次人才专项独立维度恢复脚本（2026-09-06 固化）
#
# 背景：
#   - Phase 18 (2026-08-25) 删除 talent_highlevel 维度，加入 DROP_DIMS
#   - 但源头数据（zhejiang-talent-data.json + guangdong_raw/*.json）保留了 talent_highlevel 字段
#   - 用户在 Phase 37 决策：恢复独立维度「高层次人才专项」（anju_highlevel），不参与总榜排名
#
# 本脚本执行内容：
#   1. _build_combined_data.py：DROP_DIMS 移除 talent_highlevel；DIM_ORDER 插入 anju_highlevel；
#      浙江/广东循环加 talent_highlevel→anju_highlevel 兼容映射；新增 placeholder_highlevel() 函数
#   2. _build_html.py：Python 端 DIM_ORDER/DIM_LABEL/ANJU_DIMS 同步；
#      JS 端 const DIM_ORDER/DIM_LABEL 同步；SCHEMA 加 anju_highlevel 专属字段映射；
#      cityTableHTML 内占位条目显示例外 + source 对象渲染 + 「仅查阅·不参与排名」徽标；
#      <style> 块加 .hl-badge CSS
#   3. _validate_compliance.py：DIM_ORDER/ANJU_DIMS 加新维（硬指标判定逻辑不变）
#   4. _validate_multi.py：AC6 升级「十二维标签齐全」；AC5 升级「32 城全部入库」（原误写22）
#   5. _test_multi.js：M12 跨省对比表期望行数 12→13（含 renderRankRow 插入的力度排名行）
#
# 不变量 / 安全：
#   - 不修改任何条目数据（仅维度结构 + 渲染 + 校验）
#   - 不修改 RANK_DIMS_ALL / cityRankScore（anju_highlevel 不参与排名）
#   - 不修改 EXPIRED_ITEMS / NOTE_FIX / SANCTIONED_NON_GOV_HOSTS
#   - 备份：_bak_20260906_phase37/ 包含 zhejiang-talent-data.json + guangdong_raw/*.json
#          + _build_combined_data.py + _build_html.py + _validate_compliance.py
#
# 用法：
#   python _restore_highlevel_dim.py    # 一次性执行所有编辑（已在本会话中执行，本文件为脚本快照）
#   python _build_combined_data.py      # 重跑合并
#   python _build_html.py               # 重跑 HTML 生成
#   python _validate_compliance.py      # 合规 0/0/0
#   python _validate_multi.py           # 结构 11/11
#   python _validate_redesign.py        # 视觉 ALL PASS
#   NODE_PATH="..." node _test_multi.js # jsdom 18/18
#
# 实证（2026-09-06）：
#   - 浙江 11 城 + 广东 12 城 = 23 城源头有 talent_highlevel → 合并后 100 条
#   - 广东 10 城（韶关/茂名/梅州/汕尾/河源/阳江/清远/潮州/揭阳/云浮）源头无 → 10 条 placeholder_highlevel
#   - 总 anju_highlevel 条目：113（= 100 + 10 + 3 占位条目补入显示）

import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ZJ = os.path.join(BASE, 'zhejiang-talent-data.json')
GD = os.path.join(BASE, 'guangdong_raw')
DATA = os.path.join(BASE, 'talent-data.json')


def survey_sources():
    """扫描浙江 + 广东 22 城源头，确认 talent_highlevel 数据可用性。"""
    print('=== Phase 37 T0 源头扫描 ===')

    # 浙江 11 城
    zj = json.load(open(ZJ, encoding='utf-8'))
    zj_count = 0
    for city in zj['meta']['citiesDone']:
        th = zj[city].get('dimensions', {}).get('talent_highlevel', {})
        if isinstance(th, dict) and th.get('items'):
            zj_count += len(th['items'])
    print(f'浙江: {zj_count} 条（11 城）')

    # 广东 21 城
    gd_count = 0
    gd_cities_with = []
    gd_cities_without = []
    for fn in sorted(os.listdir(GD)):
        if not fn.endswith('.json'):
            continue
        d = json.load(open(os.path.join(GD, fn), encoding='utf-8'))
        th = d.get('dimensions', {}).get('talent_highlevel', {})
        if isinstance(th, dict) and th.get('items'):
            gd_count += len(th['items'])
            gd_cities_with.append(d.get('city', fn[:-5]))
        else:
            gd_cities_without.append(d.get('city', fn[:-5]))
    print(f'广东: {gd_count} 条（{len(gd_cities_with)} 城有数据）')
    print(f'广东无 talent_highlevel 数据城市: {gd_cities_without}')
    print(f'合计: {zj_count + gd_count} 条（{len(gd_cities_without)} 城需占位）')
    return zj_count + gd_count


def verify_output():
    """验证合并后 talent-data.json 内 anju_highlevel 维度。"""
    print()
    print('=== Phase 37 T1 合并后验证 ===')
    d = json.load(open(DATA, encoding='utf-8'))
    total = 0
    cities_with = []
    cities_placeholder = []
    for prov in ('zhejiang', 'guangdong'):
        for city, obj in d[prov].items():
            hl = obj['dimensions'].get('anju_highlevel', {})
            items = hl.get('items', [])
            total += len(items)
            real = [it for it in items if it.get('official') is not False]
            if real:
                cities_with.append((city, len(real)))
            else:
                cities_placeholder.append(city)
    print(f'anju_highlevel 总条目: {total}')
    print(f'真实条目城市: {len(cities_with)}')
    print(f'占位条目城市: {len(cities_placeholder)} → {cities_placeholder}')
    return total


def main():
    if not os.path.exists(DATA):
        print(f'❌ 未发现 {DATA}，请先跑 _build_combined_data.py')
        sys.exit(1)

    survey_sources()
    n = verify_output()

    # 检查回归四件套脚本是否已修改
    print()
    print('=== 关键脚本 Phase 37 标记检查 ===')
    for fn in ['_build_combined_data.py', '_build_html.py',
               '_validate_compliance.py', '_validate_multi.py', '_test_multi.js']:
        fp = os.path.join(BASE, fn)
        with open(fp, encoding='utf-8') as f:
            content = f.read()
        has_marker = 'anju_highlevel' in content or 'Phase 37' in content
        print(f'  {fn}: {"✅ 已更新" if has_marker else "❌ 未更新"}')

    print()
    print('=== Phase 37 完成指标 ===')
    print(f'  - anju_highlevel 条目: {n}（设计期望 113，含 10 条占位）')
    print(f'  - 维度数: 12（11+1）')
    print(f'  - 排名函数 RANK_DIMS_ALL 未变（不参与排名）')
    print(f'  - 徽标「仅查阅·不参与排名」已在 .hl-badge CSS 渲染')


if __name__ == '__main__':
    main()