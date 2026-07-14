#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 13 张专业图表 - 电商赛道比赛路演"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# ============ 全局配置 ============
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Segoe UI Emoji', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['savefig.facecolor'] = 'white'

CHARTS_DIR = r'd:\18号杭州电商赛道比赛\项目\docs\charts'
os.makedirs(CHARTS_DIR, exist_ok=True)

# 配色方案
DEEP_BLUE = '#1F3864'
ORANGE = '#ED7D31'
LIGHT_GRAY = '#F2F2F2'
GREEN = '#70AD47'
RED = '#C00000'

# 通用参数
DPI = 300
TITLE_SIZE = 14
LABEL_SIZE = 10
TICK_SIZE = 8


def save_fig(fig, filename):
    """保存图表"""
    path = os.path.join(CHARTS_DIR, filename)
    fig.savefig(path, dpi=DPI, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  [OK] {filename}")


def style_ax(ax):
    """通用坐标轴样式"""
    ax.set_facecolor('white')
    ax.grid(True, linestyle='--', alpha=0.3, color='gray')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(axis='both', labelsize=TICK_SIZE)


# ================================================================
# P1 问题场景（3 张）
# ================================================================

def chart_01_pain_points():
    """1. 4 大痛点对比图 - 横向柱状图"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 6))
    fig.suptitle('4 大痛点：传统方案 vs AI 方案对比', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, y=0.98)

    metrics = [
        ('单条视频成本（元）', [500, 9.9], '越低越好'),
        ('多国适配周期（天/国）', [5, 0.1], '越低越好'),
        ('完播率（%）', [12, 35], '越高越好'),
        ('SKU 覆盖率（%）', [8, 85], '越高越好'),
    ]

    for idx, (name, values, note) in enumerate(metrics):
        ax = axes[idx // 2][idx % 2]
        categories = ['传统方案', 'AI方案']
        colors = [RED, GREEN]
        bars = ax.barh(categories, values, color=colors, height=0.5, edgecolor='white', linewidth=1.5)
        ax.set_title(name, fontsize=12, fontweight='bold', pad=8, color=DEEP_BLUE)
        ax.set_facecolor('white')
        ax.grid(True, axis='x', linestyle='--', alpha=0.3, color='gray')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', labelsize=TICK_SIZE)
        # 数值标签
        x_max = max(values)
        for bar, val in zip(bars, values):
            label = f'{val}' if val >= 1 else f'{val}'
            ax.text(bar.get_width() + x_max * 0.03, bar.get_y() + bar.get_height() / 2,
                    label, va='center', ha='left', fontsize=10, fontweight='bold')
        ax.set_xlim(0, x_max * 1.25)
        # 备注
        ax.text(0.98, 0.02, note, transform=ax.transAxes, fontsize=8,
                color='gray', ha='right', va='bottom', style='italic')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    save_fig(fig, 'p1_pain_points.png')


def chart_02_market_size():
    """2. 市场规模数据图 - 双轴图"""
    fig, ax1 = plt.subplots(figsize=(10, 5))
    style_ax(ax1)

    years = ['2022', '2023', '2024', '2025E', '2026E']
    sellers = [30, 45, 60, 70, 80]  # 万家
    market = [100, 160, 220, 300, 400]  # 亿元

    # 柱状图 - 左轴
    bars = ax1.bar(years, sellers, color=DEEP_BLUE, width=0.5, alpha=0.85, label='TikTok Shop 跨境卖家（万家）', zorder=3)
    ax1.set_xlabel('年份', fontsize=LABEL_SIZE, fontweight='bold')
    ax1.set_ylabel('跨境卖家数量（万家）', fontsize=LABEL_SIZE, color=DEEP_BLUE, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=DEEP_BLUE, labelsize=TICK_SIZE)
    ax1.tick_params(axis='x', labelsize=TICK_SIZE)
    ax1.set_ylim(0, 100)

    # 柱状图数值标签
    for bar, val in zip(bars, sellers):
        ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
                 f'{val}', ha='center', va='bottom', fontsize=9, fontweight='bold', color=DEEP_BLUE)

    # 折线图 - 右轴
    ax2 = ax1.twinx()
    ax2.plot(years, market, color=ORANGE, marker='o', markersize=8, linewidth=2.5,
             label='跨境短视频市场规模（亿元）', zorder=4)
    ax2.set_ylabel('市场规模（亿元）', fontsize=LABEL_SIZE, color=ORANGE, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=ORANGE, labelsize=TICK_SIZE)
    ax2.set_ylim(0, 500)
    ax2.spines['top'].set_visible(False)

    # 折线图数值标签
    for i, val in enumerate(market):
        ax2.text(i, val + 15, f'{val}', ha='center', va='bottom', fontsize=9, fontweight='bold', color=ORANGE)

    ax1.set_title('TikTok Shop 跨境市场增长趋势', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)

    # 图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, framealpha=0.9)

    ax1.grid(True, axis='y', linestyle='--', alpha=0.3, color='gray', zorder=0)
    plt.tight_layout()
    save_fig(fig, 'p1_market_size.png')


def chart_03_user_persona():
    """3. 目标用户画像图 - 饼图"""
    fig, ax = plt.subplots(figsize=(9, 6))

    labels = ['中小跨境卖家', '个体创业者', '本地生活经营者', '内容服务商']
    sizes = [55, 25, 12, 8]
    colors = [DEEP_BLUE, ORANGE, GREEN, RED]
    explode = (0.05, 0.02, 0.02, 0.02)

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.1f%%', colors=colors, explode=explode,
        startangle=90, textprops={'fontsize': 10},
        pctdistance=0.75, labeldistance=1.1,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )

    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    ax.set_title('目标用户画像分布', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=20)
    ax.legend(wedges, [f'{l} ({s}%)' for l, s in zip(labels, sizes)],
              loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)

    plt.tight_layout()
    save_fig(fig, 'p1_user_persona.png')


# ================================================================
# P2 解决方案（3 张）
# ================================================================

def chart_04_pipeline():
    """4. 4 步流水线架构图 - 流程图"""
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_facecolor('white')

    steps = [
        ('AI 脚本生成', '多国本土化', '输入: 产品信息+国家\n输出: 本土化脚本'),
        ('AI 数字人出镜', '多语种合成', '输入: 脚本+语种\n输出: 数字人视频'),
        ('AI 批量剪辑', '场景替换', '输入: 素材+模板\n输出: 成片视频'),
        ('AI 数据复盘', '闭环迭代', '输入: 播放数据\n输出: 优化建议'),
    ]

    box_w = 20
    box_h = 22
    y_box = 55
    gap = 6.5
    start_x = 2

    for i, (title, sub, io) in enumerate(steps):
        x = start_x + i * (box_w + gap)

        # 方框
        box = FancyBboxPatch((x, y_box), box_w, box_h,
                             boxstyle="round,pad=0.5", facecolor=DEEP_BLUE, edgecolor='white', linewidth=2)
        ax.add_patch(box)
        # 标题
        ax.text(x + box_w / 2, y_box + box_h * 0.65, f'{i+1}. {title}',
                ha='center', va='center', fontsize=11, fontweight='bold', color='white')
        ax.text(x + box_w / 2, y_box + box_h * 0.3, sub,
                ha='center', va='center', fontsize=9, color=LIGHT_GRAY)

        # 输入输出
        ax.text(x + box_w / 2, y_box - 12, io,
                ha='center', va='top', fontsize=7.5, color=DEEP_BLUE,
                bbox=dict(boxstyle='round,pad=0.3', facecolor=LIGHT_GRAY, edgecolor='gray', alpha=0.8))

        # 箭头
        if i < len(steps) - 1:
            arrow_x = x + box_w
            ax.annotate('', xy=(arrow_x + gap, y_box + box_h / 2),
                        xytext=(arrow_x, y_box + box_h / 2),
                        arrowprops=dict(arrowstyle='->', color=ORANGE, lw=3))

    ax.set_title('AI 本地化短视频生产流水线', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)
    plt.tight_layout()
    save_fig(fig, 'p2_pipeline.png')


def chart_05_comparison():
    """5. 传统 vs AI 方案对比图 - 雷达图"""
    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw=dict(polar=True))

    categories = ['成本效率', '速度', '本地化', '覆盖率', '可迭代性']
    traditional = [3, 2, 4, 2, 3]
    ai = [9, 9, 8, 9, 9]

    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    traditional_closed = traditional + traditional[:1]
    ai_closed = ai + ai[:1]
    angles_closed = angles + angles[:1]

    ax.plot(angles_closed, traditional_closed, 'o-', color=RED, linewidth=2.5, label='传统方案', markersize=7)
    ax.fill(angles_closed, traditional_closed, alpha=0.2, color=RED)
    ax.plot(angles_closed, ai_closed, 'o-', color=GREEN, linewidth=2.5, label='AI 方案', markersize=7)
    ax.fill(angles_closed, ai_closed, alpha=0.2, color=GREEN)

    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=LABEL_SIZE, fontweight='bold')
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=TICK_SIZE)
    ax.grid(True, color='gray', alpha=0.3)

    ax.set_title('传统方案 vs AI 方案综合对比', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=25)
    ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=10)

    plt.tight_layout()
    save_fig(fig, 'p2_comparison.png')


def chart_06_innovation():
    """6. 3 大创新点对比图 - 表格图"""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')
    ax.set_facecolor('white')

    col_labels = ['创新点', '市场现状', '我们的方案']
    cell_text = [
        ['多国批量本地化', '逐国手动适配', '5 国一键批量'],
        ['文化禁忌规避', '人工经验判断', '规则引擎自动'],
        ['数据闭环迭代', '凭感觉优化', '数据反哺自动'],
    ]

    table = ax.table(cellText=cell_text, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5)

    # 表头样式
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(DEEP_BLUE)
        cell.set_text_props(color='white', fontweight='bold', fontsize=12)
        cell.set_edgecolor('white')

    # 数据行样式
    for i in range(1, len(cell_text) + 1):
        for j in range(len(col_labels)):
            cell = table[i, j]
            if j == 0:
                cell.set_facecolor(ORANGE)
                cell.set_text_props(color='white', fontweight='bold', fontsize=11)
            elif j == 1:
                cell.set_facecolor(LIGHT_GRAY)
                cell.set_text_props(color=RED, fontsize=11)
            else:
                cell.set_facecolor(LIGHT_GRAY)
                cell.set_text_props(color=GREEN, fontweight='bold', fontsize=11)
            cell.set_edgecolor('white')

    ax.set_title('3 大核心创新点', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=20)
    plt.tight_layout()
    save_fig(fig, 'p2_innovation.png')


# ================================================================
# P3 Demo 路径（2 张）
# ================================================================

def chart_07_demo_flow():
    """7. 演示流程图 - 竖向流程图"""
    fig, ax = plt.subplots(figsize=(8, 10))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_facecolor('white')

    steps = [
        ('Step 1', '输入产品"便携榨汁杯" + 选择 5 国', '用户提供产品信息并选择目标国家'),
        ('Step 2', 'AI 生成 5 国本土化脚本', '自动适配语言、文化、卖点'),
        ('Step 3', '数字人多语种合成', '5 国面孔 + 5 种语言语音合成'),
        ('Step 4', '批量剪辑产出 5 国视频', '场景替换 + 字幕 + BGM 自动匹配'),
        ('Step 5', '数据复盘与优化建议', '播放数据分析 + 迭代优化建议'),
    ]

    box_w = 70
    box_h = 12
    gap = 5
    start_y = 88

    for i, (step, title, desc) in enumerate(steps):
        y = start_y - i * (box_h + gap)
        x = (100 - box_w) / 2

        # 圆角矩形
        box = FancyBboxPatch((x, y - box_h), box_w, box_h,
                             boxstyle="round,pad=0.8", facecolor=GREEN, edgecolor='white', linewidth=2)
        ax.add_patch(box)

        # 步骤编号
        ax.text(x + 8, y - box_h / 2, step, ha='center', va='center',
                fontsize=10, fontweight='bold', color='white',
                bbox=dict(boxstyle='circle,pad=0.5', facecolor=DEEP_BLUE, edgecolor='white'))

        # 标题
        ax.text(x + 22, y - box_h * 0.35, title, ha='left', va='center',
                fontsize=11, fontweight='bold', color='white')
        # 描述
        ax.text(x + 22, y - box_h * 0.7, desc, ha='left', va='center',
                fontsize=8.5, color=LIGHT_GRAY)

        # 箭头
        if i < len(steps) - 1:
            ax.annotate('', xy=(50, y - box_h - gap), xytext=(50, y - box_h),
                        arrowprops=dict(arrowstyle='->', color=ORANGE, lw=2.5))

    ax.set_title('现场 Demo 演示流程', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)
    plt.tight_layout()
    save_fig(fig, 'p3_demo_flow.png')


def chart_08_countries():
    """8. 5 国视频产出展示图 - 矩阵表格图"""
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.axis('off')
    ax.set_facecolor('white')

    col_labels = ['国家', '旗帜', '语种', '面孔类型', 'BGM 风格']
    cell_text = [
        ['美国 US', 'US', 'en-US', '欧美面孔', 'Pop'],
        ['越南 VN', 'VN', 'vi-VN', '东南亚面孔', 'V-Pop'],
        ['沙特 SA', 'SA', 'ar-SA', '中东面孔', 'Arabic Pop'],
        ['英国 GB', 'GB', 'en-GB', '欧美面孔', 'Indie'],
        ['印尼 ID', 'ID', 'id-ID', '东南亚面孔', 'Dangdut'],
    ]

    # 旗帜 emoji
    flags = ['\U0001F1FA\U0001F1F8', '\U0001F1FB\U0001F1F3', '\U0001F1F8\U0001F1E6',
             '\U0001F1EC\U0001F1E7', '\U0001F1EE\U0001F1E9']
    for i, flag in enumerate(flags):
        cell_text[i][1] = flag

    table = ax.table(cellText=cell_text, colLabels=col_labels, loc='center', cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.2)

    # 表头样式
    for j in range(len(col_labels)):
        cell = table[0, j]
        cell.set_facecolor(DEEP_BLUE)
        cell.set_text_props(color='white', fontweight='bold', fontsize=12)
        cell.set_edgecolor('white')

    # 数据行样式
    country_colors = [LIGHT_GRAY, 'white', LIGHT_GRAY, 'white', LIGHT_GRAY]
    for i in range(1, len(cell_text) + 1):
        for j in range(len(col_labels)):
            cell = table[i, j]
            cell.set_facecolor(country_colors[i - 1])
            if j == 0:
                cell.set_text_props(fontweight='bold', color=DEEP_BLUE, fontsize=11)
            elif j == 1:
                cell.set_text_props(fontsize=14)
            cell.set_edgecolor('gray')

    ax.set_title('5 国视频产出矩阵', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=20)
    plt.tight_layout()
    save_fig(fig, 'p3_countries.png')


# ================================================================
# P4 技术架构（2 张）
# ================================================================

def chart_09_tech_stack():
    """9. 技术栈架构图 - 分层架构图"""
    fig, ax = plt.subplots(figsize=(11, 7))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_facecolor('white')

    layers = [
        ('用户层', '产品输入  +  国家选择', DEEP_BLUE),
        ('编排层', 'MiXer AI 主编排  +  MCP 协议', ORANGE),
        ('Agent 层', '脚本Agent  |  数字人Agent  |  剪辑Agent  |  复盘Agent', GREEN),
        ('资源层', 'LLM  +  数字人API  +  ffmpeg  +  TikTok API', '#555555'),
    ]

    layer_h = 16
    gap = 5
    start_y = 85

    for i, (name, content, color) in enumerate(layers):
        y = start_y - i * (layer_h + gap)
        x = 5
        w = 90

        # 层背景
        box = FancyBboxPatch((x, y - layer_h), w, layer_h,
                             boxstyle="round,pad=0.5", facecolor=color, edgecolor='white', linewidth=2, alpha=0.9)
        ax.add_patch(box)

        # 层名称（左侧标签）
        ax.text(x + 10, y - layer_h / 2, name, ha='center', va='center',
                fontsize=13, fontweight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.2, edgecolor='none'))

        # 层内容
        ax.text(x + 50, y - layer_h / 2, content, ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')

        # 向下箭头
        if i < len(layers) - 1:
            ax.annotate('', xy=(50, y - layer_h - gap + 1), xytext=(50, y - layer_h),
                        arrowprops=dict(arrowstyle='->', color=ORANGE if i < 2 else GREEN, lw=2.5))

    ax.set_title('技术架构分层图', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)
    plt.tight_layout()
    save_fig(fig, 'p4_tech_stack.png')


def chart_10_ai_disclosure():
    """10. AI 使用披露饼图"""
    fig, ax = plt.subplots(figsize=(9, 6))

    labels = ['团队自研', 'AI Coding 辅助', '开源工具', '商业 API']
    sizes = [45, 25, 20, 10]
    colors = [DEEP_BLUE, ORANGE, GREEN, RED]
    explode = (0.03, 0.03, 0.03, 0.03)

    detail_labels = [
        '团队自研 45%\n(Prompt模板/文化禁忌引擎/\nffmpeg脚本/复盘逻辑/编排配置)',
        'AI Coding 25%\n(Cursor/Claude Code 代码生成)',
        '开源工具 20%\n(matplotlib/python-pptx/ffmpeg)',
        '商业 API 10%\n(HeyGen/OpenAI/TikTok API)',
    ]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct='%1.0f%%', colors=colors, explode=explode,
        startangle=90, textprops={'fontsize': 10, 'fontweight': 'bold'},
        pctdistance=0.7, labeldistance=1.08,
        wedgeprops={'edgecolor': 'white', 'linewidth': 2}
    )

    for autotext in autotexts:
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
        autotext.set_color('white')

    ax.set_title('AI 使用披露占比', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=20)
    ax.legend(wedges, detail_labels, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8.5,
              framealpha=0.9)

    plt.tight_layout()
    save_fig(fig, 'p4_ai_disclosure.png')


# ================================================================
# P5 商业化（3 张）
# ================================================================

def chart_11_business_models():
    """11. 商业模式对比图 - 横向柱状图"""
    fig, ax = plt.subplots(figsize=(11, 5.5))
    style_ax(ax)

    dimensions = ['价格水平', '用户容量', '留存/客单价值']
    models = ['SaaS 订阅', '按条计费', '企业定制']
    # 归一化评分（1-4）
    data = np.array([
        [2, 3, 3],   # SaaS: 价格中, 容量高, 留存高
        [1, 4, 2],   # 按条: 价格低, 容量极高, 留存中
        [4, 1, 4],   # 企业: 价格极高, 容量低, 客单极高
    ])
    annotations = [
        ['999元/月', '高', '留存:高'],
        ['9.9元/条', '极高', '留存:中'],
        ['3-10万/项目', '低', '客单:极高'],
    ]
    colors = [DEEP_BLUE, ORANGE, GREEN]

    x = np.arange(len(dimensions))
    width = 0.22

    for i, model in enumerate(models):
        offset = (i - 1) * width
        bars = ax.bar(x + offset, data[i], width, label=model, color=colors[i], edgecolor='white', linewidth=1.5)
        # 标注实际值
        for j, bar in enumerate(bars):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    annotations[i][j], ha='center', va='bottom', fontsize=8.5, fontweight='bold',
                    color=colors[i])

    ax.set_xlabel('对比维度', fontsize=LABEL_SIZE, fontweight='bold')
    ax.set_ylabel('评分（1-4）', fontsize=LABEL_SIZE, fontweight='bold')
    ax.set_title('3 种商业模式对比', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(dimensions, fontsize=LABEL_SIZE)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['低', '中', '高', '极高'], fontsize=TICK_SIZE)
    ax.set_ylim(0, 5.5)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

    plt.tight_layout()
    save_fig(fig, 'p5_business_models.png')


def chart_12_revenue_forecast():
    """12. 收入预测图表 - 折线图+面积图"""
    fig, ax1 = plt.subplots(figsize=(12, 5.5))
    style_ax(ax1)

    months = ['M1','M2','M3','M4','M5','M6','M7','M8','M9','M10','M11','M12']
    monthly = [0.5, 1, 1.5, 2, 3, 4, 6, 8, 10, 12, 15, 18]  # 累计 81 万
    cumulative = np.cumsum(monthly)

    # 面积图 - 累计收入（右轴）
    ax2 = ax1.twinx()
    ax2.fill_between(months, cumulative, alpha=0.15, color=ORANGE, label='累计收入（万元）')
    ax2.plot(months, cumulative, color=ORANGE, linewidth=2, linestyle='--', marker='s', markersize=5)
    ax2.set_ylabel('累计收入（万元）', fontsize=LABEL_SIZE, color=ORANGE, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=ORANGE, labelsize=TICK_SIZE)
    ax2.set_ylim(0, max(cumulative) * 1.3)
    ax2.spines['top'].set_visible(False)

    # 折线图 - 月收入（左轴）
    ax1.plot(months, monthly, color=DEEP_BLUE, marker='o', markersize=8, linewidth=2.5,
             label='月收入（万元）', zorder=5)
    ax1.set_xlabel('月份', fontsize=LABEL_SIZE, fontweight='bold')
    ax1.set_ylabel('月收入（万元）', fontsize=LABEL_SIZE, color=DEEP_BLUE, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=DEEP_BLUE, labelsize=TICK_SIZE)
    ax1.tick_params(axis='x', labelsize=TICK_SIZE)
    ax1.set_ylim(0, max(monthly) * 1.5)

    # 月收入数值标签
    for i, val in enumerate(monthly):
        ax1.text(i, val + max(monthly) * 0.05, f'{val}', ha='center', va='bottom', fontsize=8, fontweight='bold', color=DEEP_BLUE)

    # 里程碑标注
    milestones = {
        2: 'M3 首批付费用户(月入1.5万)',
        5: 'M6 月入4万(稳步增长)',
        11: 'M12 月入18万(年终目标)',
    }
    for idx, label in milestones.items():
        ax1.annotate(label, xy=(idx, monthly[idx]), xytext=(idx, monthly[idx] + max(monthly) * 0.28),
                     fontsize=9, fontweight='bold', color=RED, ha='center',
                     arrowprops=dict(arrowstyle='->', color=RED, lw=1.5),
                     bbox=dict(boxstyle='round,pad=0.3', facecolor=LIGHT_GRAY, edgecolor=RED, alpha=0.9))

    ax1.set_title('首年收入预测（万元）', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=9, framealpha=0.9)

    ax1.grid(True, axis='y', linestyle='--', alpha=0.3, color='gray')
    plt.tight_layout()
    save_fig(fig, 'p5_revenue_forecast.png')


def chart_13_roadmap():
    """13. 迭代路径时间线图 - 横向时间线"""
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    ax.set_facecolor('white')

    milestones = [
        ('Q3 2026', 'MVP 上线\n5 国支持', DEEP_BLUE),
        ('Q4 2026', '扩展东南亚 6 国\n+ 中东 3 国', ORANGE),
        ('Q1 2027', '直播切片自动化\n+ AI 主播', GREEN),
        ('Q2 2027', '选品+素材\n一体化平台', RED),
    ]

    # 时间线
    line_y = 50
    ax.plot([8, 92], [line_y, line_y], color=DEEP_BLUE, linewidth=3, zorder=1)

    x_positions = [15, 38, 61, 84]

    for i, (quarter, desc, color) in enumerate(milestones):
        x = x_positions[i]

        # 圆点
        circle = Circle((x, line_y), 3, color=color, zorder=3, ec='white', lw=2)
        ax.add_patch(circle)

        # 交替上下放置文字
        if i % 2 == 0:
            # 上方
            ax.annotate(quarter, xy=(x, line_y + 3), xytext=(x, line_y + 18),
                        fontsize=11, fontweight='bold', color=color, ha='center',
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            ax.text(x, line_y + 28, desc, fontsize=9, ha='center', va='bottom', color='#333333',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=LIGHT_GRAY, edgecolor=color, alpha=0.9))
        else:
            # 下方
            ax.annotate(quarter, xy=(x, line_y - 3), xytext=(x, line_y - 18),
                        fontsize=11, fontweight='bold', color=color, ha='center',
                        arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
            ax.text(x, line_y - 28, desc, fontsize=9, ha='center', va='top', color='#333333',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor=LIGHT_GRAY, edgecolor=color, alpha=0.9))

    ax.set_title('产品迭代路线图', fontsize=TITLE_SIZE, fontweight='bold', color=DEEP_BLUE, pad=15)
    plt.tight_layout()
    save_fig(fig, 'p5_roadmap.png')


# ================================================================
# 主函数
# ================================================================

def main():
    print("=" * 50)
    print("开始生成 13 张专业图表")
    print(f"输出目录: {CHARTS_DIR}")
    print("=" * 50)

    print("\n【P1 问题场景】")
    chart_01_pain_points()
    chart_02_market_size()
    chart_03_user_persona()

    print("\n【P2 解决方案】")
    chart_04_pipeline()
    chart_05_comparison()
    chart_06_innovation()

    print("\n【P3 Demo 路径】")
    chart_07_demo_flow()
    chart_08_countries()

    print("\n【P4 技术架构】")
    chart_09_tech_stack()
    chart_10_ai_disclosure()

    print("\n【P5 商业化】")
    chart_11_business_models()
    chart_12_revenue_forecast()
    chart_13_roadmap()

    print("\n" + "=" * 50)
    print("全部 13 张图表生成完成！")
    print("=" * 50)

    # 验证
    print("\n【验证结果】")
    files = [f for f in os.listdir(CHARTS_DIR) if f.endswith('.png')]
    print(f"共生成 {len(files)} 张图表")
    for f in sorted(files):
        size = os.path.getsize(os.path.join(CHARTS_DIR, f))
        print(f"  {f}: {size // 1024}KB")


if __name__ == '__main__':
    main()
