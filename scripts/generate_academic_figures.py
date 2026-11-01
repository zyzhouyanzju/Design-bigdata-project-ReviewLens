# -*- coding: utf-8 -*-
"""Generate unified academic group-meeting figures for the project progress report."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib as mpl
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "academic_figures"
ARTIFACT_DIR = Path(r"C:\Users\Zhou Yan\.gemini\antigravity\brain\2c010095-757a-4e19-bedb-d8274f839709")

# Unified Academic Blue-and-White Palette (蓝白极简学术配色)
BG_CANVAS = "#F8FAFC"       # 极浅冰白画布底色
BG_CARD = "#FFFFFF"         # 纯白卡片底色
BORDER_COLOR = "#CBD5E1"    # 浅灰蓝边框
NAVY = "#0F2942"            # 深海学术蓝 (主标题/主色)
NAVY_MID = "#1E3A8A"        # 皇家深蓝 (次级强调)
TEAL = "#2563EB"            # 经典钴蓝 (主高亮蓝)
TEAL_LIGHT = "#EFF6FF"      # 极浅冰蓝填充
ORANGE = "#3B82F6"          # 科技天蓝 (辅助蓝)
ORANGE_LIGHT = "#F0F7FF"    # 极浅云蓝填充
CRIMSON = "#475569"         # 冷岩灰蓝 (对比项/负向态，避免刺眼红橙)
CRIMSON_LIGHT = "#F1F5F9"   # 极浅冷灰白填充
SLATE = "#475569"           # 次要正文灰蓝
SLATE_LIGHT = "#E2E8F0"     # 分割线/表头浅灰蓝
GOLD = "#1D4ED8"

PRODUCT_NAMES = {
    "B0C337TNGS": "Beats Powerbeats Pro",
    "B0C338S8M7": "Beats Studio Buds",
    "B09PRC3WC5": "TOZO A1 Mini",
}
PRODUCT_COLORS = {
    "B0C337TNGS": "#0F2942",  # 深海蓝 (Deep Navy)
    "B0C338S8M7": "#2563EB",  # 经典钴蓝 (Cobalt Blue)
    "B09PRC3WC5": "#60A5FA",  # 浅天蓝 (Sky Blue)
}


def setup_matplotlib() -> None:
    mpl.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"]
    mpl.rcParams["axes.unicode_minus"] = False
    mpl.rcParams["figure.facecolor"] = BG_CANVAS
    mpl.rcParams["axes.facecolor"] = BG_CARD


def create_canvas(tag: str, title: str, subtitle: str, footnote: str, figsize=(18, 10.5)):
    fig = plt.figure(figsize=figsize, dpi=220, facecolor=BG_CANVAS)
    # Top academic banner accent line
    bg_ax = fig.add_axes([0, 0, 1, 1], zorder=-10)
    bg_ax.set_xlim(0, 1)
    bg_ax.set_ylim(0, 1)
    bg_ax.axis("off")

    # Header bar
    bg_ax.add_patch(mpatches.Rectangle((0.03, 0.962), 0.94, 0.005, color=NAVY, transform=bg_ax.transAxes))
    bg_ax.add_patch(mpatches.Rectangle((0.03, 0.962), 0.18, 0.005, color=ORANGE, transform=bg_ax.transAxes))

    fig.text(0.03, 0.938, tag, fontsize=10, fontweight="bold", color=TEAL)
    fig.text(0.03, 0.902, title, fontsize=21, fontweight="bold", color=NAVY)
    fig.text(0.03, 0.873, subtitle, fontsize=11.5, color=SLATE)

    # Bottom footer line and caption
    bg_ax.add_patch(mpatches.Rectangle((0.03, 0.036), 0.94, 0.0015, color=BORDER_COLOR, transform=bg_ax.transAxes))
    fig.text(0.03, 0.016, footnote, fontsize=9.5, color=SLATE)
    fig.text(
        0.97,
        0.016,
        "《设计大数据基础》课程研究汇报 · 3240103297 周衍",
        fontsize=9.5,
        fontweight="bold",
        color=NAVY_MID,
        ha="right",
    )
    return fig, bg_ax


def draw_card(bg_ax, x, y, w, h, title="", badge="", header_color=NAVY):
    """Draw a clean blue-and-white academic card container in figure normalized coordinates."""
    # Subtle shadow
    bg_ax.add_patch(
        FancyBboxPatch(
            (x + 0.002, y - 0.003),
            w,
            h,
            boxstyle="round,pad=0.004,rounding_size=0.010",
            facecolor="#E2E8F0",
            edgecolor="none",
            zorder=-5,
        )
    )
    # Main white card
    bg_ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.004,rounding_size=0.010",
            facecolor=BG_CARD,
            edgecolor=BORDER_COLOR,
            linewidth=1.1,
            zorder=-4,
        )
    )
    if title:
        # Clean light ice-blue header strip with deep navy bottom border
        bg_ax.add_patch(
            FancyBboxPatch(
                (x, y + h - 0.038),
                w,
                0.038,
                boxstyle="round,pad=0.004,rounding_size=0.010",
                facecolor="#EFF6FF",
                edgecolor="none",
                zorder=-3,
            )
        )
        bg_ax.add_patch(
            mpatches.Rectangle(
                (x - 0.004, y + h - 0.042),
                w + 0.008,
                0.014,
                facecolor="#EFF6FF",
                edgecolor="none",
                zorder=-3,
            )
        )
        bg_ax.add_patch(
            mpatches.Rectangle(
                (x - 0.003, y + h - 0.042),
                w + 0.006,
                0.002,
                facecolor="#BFDBFE",
                edgecolor="none",
                zorder=-2,
            )
        )
        if badge:
            bg_ax.text(
                x + 0.012,
                y + h - 0.020,
                badge,
                fontsize=9.2,
                fontweight="bold",
                color="#FFFFFF",
                va="center",
                ha="left",
                bbox=dict(boxstyle="round,pad=0.24", facecolor=NAVY, edgecolor="none"),
                zorder=-2,
            )
            bg_ax.text(
                x + 0.045,
                y + h - 0.020,
                title,
                fontsize=11.8,
                fontweight="bold",
                color=NAVY,
                va="center",
                ha="left",
                zorder=-2,
            )
        else:
            bg_ax.text(
                x + 0.012,
                y + h - 0.020,
                title,
                fontsize=11.8,
                fontweight="bold",
                color=NAVY,
                va="center",
                ha="left",
                zorder=-2,
            )


def draw_box(ax, x, y, w, h, title, body, fc="#FFFFFF", ec=NAVY, title_color=NAVY, body_color="#2C3E50", title_size=10.5, body_size=8.8, badge=None, badge_color=ORANGE, header_gap=0.052, badge_offset=0.115):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.008,rounding_size=0.02",
            facecolor=fc,
            edgecolor=ec,
            linewidth=1.5,
            zorder=2,
        )
    )
    top_pad = min(0.026, h * 0.16)
    if badge:
        ax.text(
            x + 0.015,
            y + h - top_pad,
            badge,
            fontsize=8.0,
            fontweight="bold",
            color="white",
            va="top",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.20", facecolor=badge_color, edgecolor="none"),
            zorder=4,
        )
        ax.text(
            x + badge_offset,
            y + h - top_pad,
            title,
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            va="top",
            ha="left",
            zorder=3,
        )
    else:
        ax.text(
            x + 0.016,
            y + h - top_pad,
            title,
            fontsize=title_size,
            fontweight="bold",
            color=title_color,
            va="top",
            ha="left",
            zorder=3,
        )
    if body:
        ax.text(
            x + 0.016,
            y + h - top_pad - header_gap,
            body,
            fontsize=body_size,
            color=body_color,
            va="top",
            ha="left",
            linespacing=1.36,
            zorder=3,
        )


def generate_fig01_dataset_construction(raw_df: pd.DataFrame) -> Path:
    """Fig 01: Dataset Construction Pipeline, Funnel & Target Product Profiles."""
    fig, bg_ax = create_canvas(
        tag="ACADEMIC GROUP MEETING · PART I : DATASET CONSTRUCTION & PROTOCOL",
        title="图 1  可复现评论数据集的构建流程、两阶段筛选漏斗与样本结构",
        subtitle="从 Amazon Reviews'23 (4,388 万条原始流) 到子句级结构化证据库 (43,102 条) 的全链路数据工程",
        footnote="数据来源：McAuley Lab Amazon Reviews'23 (Electronics, 截至 2023-09) | 提取脚本：scripts/extract_earphone_metadata.py, scripts/extract_target_amazon_reviews.py | 校验：SHA-256 Run Manifest",
    )

    # Left Card: 5-Stage Data Funnel & Engineering Protocol
    draw_card(bg_ax, 0.03, 0.06, 0.48, 0.79, "两阶段定向采集与五级数据提纯漏斗 (Five-Stage Data Refinement Funnel)", badge="A", header_color=NAVY)
    ax_funnel = fig.add_axes([0.04, 0.07, 0.46, 0.72])
    ax_funnel.set_xlim(0, 1)
    ax_funnel.set_ylim(0, 1)
    ax_funnel.axis("off")

    stages = [
        (
            "STAGE 1",
            "官方全量原始流 (Raw Category Archive)",
            "• 源数据：Electronics.jsonl.gz (6.02 GB) + Meta 商品元数据\n• 规模：扫描 43,886,944 条原始评论 | 试采扫描 71,928 个商品元数据",
            "43,886,944 条",
            0.94,
            "#F8FAFC",
            "#0F2942",
        ),
        (
            "STAGE 2",
            "本体与配件位置启发式过滤 (Metadata Filtering)",
            "• 算法：正则白名单 (earbuds/tws) + 配件词位置偏移判据\n  若命中配件词 (case/cover/tips) 且 start(配件) < start(设备功能词) 则剔除",
            "646 个候选本体\n→ 锁定 3 款标杆",
            0.84,
            "#F0F7FF",
            "#1E3A8A",
        ),
        (
            "STAGE 3",
            "O(1) 内存流式定向抽取 (Streaming ASIN Extraction)",
            "• 算法：gzip 流式单遍扫描匹配 parent_asin + .partial 原子重命名落盘\n• 结果：完整提取三款真无线耳机全量历史评论 (截至 2023-09)",
            "24,084 条\n原始目标评论",
            0.74,
            "#EFF6FF",
            "#1D4ED8",
        ),
        (
            "STAGE 4",
            "规范化清洗与确定性指纹去重 (Normalization & Dedup)",
            "• 算法：HTML 实体反转义与标签剥离 + SHA-256(pid, uid, ts, text)[:20]\n• 剔除：421 条重复评论 + 71 条缺失正文记录 (保留率 97.96%)",
            "23,592 条\n独立有效评论",
            0.66,
            "#F0F7FF",
            "#2563EB",
        ),
        (
            "STAGE 5",
            "转折子句切分与细粒度证据提取 (Clause Evidence Extraction)",
            "• 算法：按标点与转折连词 (but/however/although/yet) 切分子句并保留偏移\n• 产出：43,102 条结构化证据 + 120 个「型号×维度×场景」聚合单元",
            "43,102 条\n子句级证据",
            0.58,
            "#EFF6FF",
            "#3B82F6",
        ),
    ]

    y_tops = [0.97, 0.77, 0.57, 0.37, 0.17]
    box_h = 0.155
    for idx, (st_code, st_title, st_desc, st_metric, width_ratio, fc, ec) in enumerate(stages):
        y = y_tops[idx] - box_h
        # Left description card
        ax_funnel.add_patch(
            FancyBboxPatch(
                (0.01, y),
                0.68,
                box_h,
                boxstyle="round,pad=0.008,rounding_size=0.018",
                facecolor=fc,
                edgecolor=ec,
                linewidth=1.5,
            )
        )
        ax_funnel.text(
            0.025,
            y + box_h - 0.025,
            st_code,
            fontsize=8.2,
            fontweight="bold",
            color="white",
            va="top",
            bbox=dict(boxstyle="round,pad=0.22", facecolor=ec, edgecolor="none"),
        )
        ax_funnel.text(
            0.155,
            y + box_h - 0.023,
            st_title,
            fontsize=10.5,
            fontweight="bold",
            color=NAVY,
            va="top",
        )
        ax_funnel.text(
            0.025,
            y + box_h - 0.068,
            st_desc,
            fontsize=8.6,
            color="#2C3E50",
            va="top",
            linespacing=1.35,
        )

        # Right funnel metric badge
        funnel_w = 0.26 * (0.65 + 0.35 * width_ratio)
        funnel_x = 0.85 - funnel_w / 2
        ax_funnel.add_patch(
            FancyBboxPatch(
                (funnel_x, y + 0.015),
                funnel_w,
                box_h - 0.03,
                boxstyle="round,pad=0.008,rounding_size=0.02",
                facecolor=ec,
                edgecolor="none",
            )
        )
        ax_funnel.text(
            0.85,
            y + box_h / 2,
            st_metric,
            fontsize=10,
            fontweight="bold",
            color="white",
            va="center",
            ha="center",
            linespacing=1.25,
        )

        if idx < len(stages) - 1:
            next_y = y_tops[idx + 1]
            ax_funnel.annotate(
                "",
                xy=(0.35, next_y + 0.005),
                xytext=(0.35, y - 0.005),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.45", color=ec, lw=1.8),
            )
            ax_funnel.annotate(
                "",
                xy=(0.85, next_y + 0.012),
                xytext=(0.85, y + 0.005),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.45", color=ec, lw=1.8),
            )

    # Right Top Card: Pilot vs Targeted Extraction Comparison
    draw_card(
        bg_ax,
        0.53,
        0.52,
        0.44,
        0.33,
        "采集策略演进验证：随机关键词试采 vs. 按父 ID 定向全量抽取",
        badge="B",
        header_color=NAVY_MID,
    )
    ax_cmp = fig.add_axes([0.55, 0.54, 0.40, 0.25])
    ax_cmp.set_xlim(0, 1)
    ax_cmp.set_ylim(0, 1)
    ax_cmp.axis("off")

    # Table-like visual comparison inside Card B
    draw_box(
        ax_cmp,
        0.01,
        0.04,
        0.46,
        0.91,
        "早期方案：随机片段 + 关键词试采",
        "• 文件：earphone_reviews_pilot.jsonl\n• 扫描范围：前 64 MiB (4,627 条记录)\n• 命中样本：300 条评论分散在 287 个商品\n• 单品最大样本量：仅 3 条 / 型号\n• 达到 N≥20 比较门槛型号：0 个 (0%)\n• 缺陷：混入大量耳机壳配件，单品极度稀疏\n• 结论：[×] 无法支撑具体型号级的需求冲突比较",
        fc=CRIMSON_LIGHT,
        ec=CRIMSON,
        title_color=CRIMSON,
        badge="PILOT",
        badge_color=CRIMSON,
        title_size=9.5,
        body_size=8.3,
        header_gap=0.11,
        badge_offset=0.125,
    )
    draw_box(
        ax_cmp,
        0.52,
        0.04,
        0.47,
        0.91,
        "正式方案：元数据筛本体 + ASIN 抽取",
        "• 文件：amazon_target_earbuds_reviews.jsonl\n• 扫描范围：全量 6.02 GB (43,886,944 条记录)\n• 命中样本：24,084 条评论集中于 3 款本体\n• 单品最小样本量：6,874 条 / 型号\n• 达到 N≥20 比较门槛型号：3 个 (100%)\n• 优势：彻底排除配件污染，单品证据高度饱和\n• 结论：[√] 支撑型号×维度×场景三维统计与检验",
        fc=TEAL_LIGHT,
        ec=TEAL,
        title_color="#096B68",
        badge="FORMAL",
        badge_color=TEAL,
        title_size=9.5,
        body_size=8.3,
        header_gap=0.11,
        badge_offset=0.145,
    )
    ax_cmp.annotate(
        "",
        xy=(0.515, 0.50),
        xytext=(0.475, 0.50),
        arrowprops=dict(arrowstyle="-|>,head_width=0.4,head_length=0.5", color=ORANGE, lw=2.5),
    )

    # Right Bottom Card: 3 Target Earbuds Product Profiles with Product Photos
    draw_card(
        bg_ax,
        0.53,
        0.06,
        0.44,
        0.43,
        "三款典型真无线耳机标杆样本档案 (Target Product Profiles)",
        badge="C",
        header_color=TEAL,
    )

    products_meta = [
        (
            "B0C337TNGS",
            "Beats Powerbeats Pro",
            "高端运动挂耳式 · 物理按键",
            ROOT / "ppt_visual_assets" / "products" / "powerbeats_pro.jpg",
            "8,989 条",
            "18,546 条",
            "3.58 ★",
            "90.1%",
            "2019.05 – 2023.09",
            "#0F2942",
            "#F8FAFC",
        ),
        (
            "B0C338S8M7",
            "Beats Studio Buds",
            "主动降噪通勤款 · 入耳无柄",
            ROOT / "ppt_visual_assets" / "products" / "studio_buds.jpg",
            "6,874 条",
            "11,472 条",
            "3.31 ★",
            "93.6%",
            "2021.06 – 2023.09",
            "#2563EB",
            "#F8FAFC",
        ),
        (
            "B09PRC3WC5",
            "TOZO A1 Mini",
            "平价轻巧便携款 · 触控操作",
            ROOT / "ppt_visual_assets" / "products" / "tozo_a1.jpg",
            "8,221 条",
            "13,084 条",
            "4.05 ★",
            "98.1%",
            "2021.10 – 2023.09",
            "#3B82F6",
            "#F8FAFC",
        ),
    ]

    card_xs = [0.545, 0.687, 0.829]
    card_w = 0.128
    for idx, (asin, name, tag_str, img_path, rev_cnt, ev_cnt, mean_rt, vp_rate, span, col, bg_col) in enumerate(products_meta):
        cx = card_xs[idx]
        # Subcard background
        bg_ax.add_patch(
            FancyBboxPatch(
                (cx, 0.078),
                card_w,
                0.355,
                boxstyle="round,pad=0.004,rounding_size=0.01",
                facecolor=bg_col,
                edgecolor=col,
                linewidth=1.4,
                zorder=-2,
            )
        )
        # Product Image thumbnail
        if img_path.exists():
            img = Image.open(img_path)
            ax_img = fig.add_axes([cx + 0.014, 0.312, card_w - 0.028, 0.108])
            ax_img.imshow(img)
            ax_img.axis("off")

        bg_ax.text(cx + card_w / 2, 0.292, name, fontsize=9.6, fontweight="bold", color=NAVY, ha="center")
        bg_ax.text(
            cx + card_w / 2,
            0.262,
            f"ASIN: {asin}",
            fontsize=7.8,
            fontweight="bold",
            color="white",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=col, edgecolor="none"),
        )
        bg_ax.text(cx + card_w / 2, 0.232, tag_str, fontsize=8.0, color=SLATE, ha="center")

        metrics_text = (
            f"• 定向评论数：{rev_cnt}\n"
            f"• V2 子句证据：{ev_cnt}\n"
            f"• 样本平均星级：{mean_rt}\n"
            f"• 验证购买比例：{vp_rate}\n"
            f"• 评论跨度：{span}"
        )
        bg_ax.text(cx + 0.008, 0.208, metrics_text, fontsize=8.0, color="#1F2D3D", va="top", linespacing=1.40)

    out_path = OUT_DIR / "fig01_dataset_construction.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def generate_fig02_dataset_eda_overview(raw_df: pd.DataFrame, ev_df: pd.DataFrame) -> Path:
    """Fig 02: Multi-panel EDA of the current dataset."""
    fig, bg_ax = create_canvas(
        tag="ACADEMIC GROUP MEETING · PART II : EXPLORATORY DATA ANALYSIS (EDA)",
        title="图 2  现有数据集多维统计特征：星级极化、时间演进、体验维度情感与场景密度",
        subtitle="基于 23,592 条去重有效评论与 43,102 条 V2 子句级证据的真实分布统计",
        footnote="数据来源：data/raw/amazon_target_earbuds_reviews.jsonl & outputs/engine_v2/evidence.csv | 注：同一条评论可包含多个体验维度子句",
    )

    # 4 Cards Layout
    draw_card(bg_ax, 0.03, 0.47, 0.45, 0.38, "三款耳机星级分布对比 (Rating Polarization Distribution)", badge="A", header_color=NAVY)
    draw_card(bg_ax, 0.50, 0.47, 0.47, 0.38, "评论样本时间序列分布 (Quarterly Review Volume 2019–2023)", badge="B", header_color=NAVY_MID)
    draw_card(bg_ax, 0.03, 0.06, 0.45, 0.38, "8 大体验维度子句证据量与情感极性构成 (V2 Aspect-Sentiment)", badge="C", header_color=TEAL)
    draw_card(bg_ax, 0.50, 0.06, 0.47, 0.38, "显式使用场景 × 产品型号证据密度热力图 (每千条评论提及数)", badge="D", header_color=ORANGE)

    # Panel A: Rating Distribution (%)
    ax_a = fig.add_axes([0.07, 0.515, 0.39, 0.275])
    ratings = [1, 2, 3, 4, 5]
    x = np.arange(len(ratings))
    width = 0.25
    for idx, (asin, label) in enumerate(PRODUCT_NAMES.items()):
        sub = raw_df[raw_df["parent_asin"] == asin]
        counts = sub["rating"].round().value_counts()
        pcts = [counts.get(r, 0) / len(sub) * 100 for r in ratings]
        mean_r = sub["rating"].mean()
        bars = ax_a.bar(
            x + (idx - 1) * width,
            pcts,
            width=width,
            color=PRODUCT_COLORS[asin],
            label=f"{label} (均分 {mean_r:.2f}★)",
            edgecolor="white",
            linewidth=0.6,
            zorder=3,
        )
        for bar, val in zip(bars, pcts):
            if val >= 6:
                ax_a.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.8,
                    f"{val:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=7.5,
                    fontweight="bold",
                    color=NAVY,
                )
    ax_a.set_xticks(x, ["1 星 (差评)", "2 星", "3 星 (中评)", "4 星", "5 星 (好评)"], fontsize=9.5, fontweight="bold")
    ax_a.set_ylabel("占该型号总评论比例 (%)", fontsize=9.5, color=NAVY)
    ax_a.set_ylim(0, 72)
    ax_a.grid(axis="y", linestyle="--", alpha=0.5, color="#CBD5E1", zorder=0)
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)
    ax_a.legend(loc="upper left", frameon=True, facecolor="#FAF8F5", edgecolor="none", fontsize=8.5)
    ax_a.text(
        0.02,
        0.64,
        "洞察：呈现显著的「J型/U型极化」——\n5星与1星同时高企，平均星级掩盖了\n具体体验维度的两极分化。",
        transform=ax_a.transAxes,
        fontsize=8.2,
        color=NAVY,
        bbox=dict(boxstyle="round,pad=0.35", facecolor=ORANGE_LIGHT, edgecolor=ORANGE, alpha=0.9),
    )

    # Panel B: Quarterly Review Volume Trend
    ax_b = fig.add_axes([0.545, 0.515, 0.405, 0.275])
    raw_df["dt"] = pd.to_datetime(raw_df["timestamp"], unit="ms")
    raw_df["quarter"] = raw_df["dt"].dt.to_period("Q").astype(str)
    q_filtered = raw_df[raw_df["dt"] >= "2020-01-01"]
    quarters = sorted(q_filtered["quarter"].unique())
    qx = np.arange(len(quarters))
    for asin, label in PRODUCT_NAMES.items():
        sub = q_filtered[q_filtered["parent_asin"] == asin]
        q_counts = sub.groupby("quarter").size()
        vals = [q_counts.get(q, 0) for q in quarters]
        ax_b.plot(
            qx,
            vals,
            marker="o",
            markersize=4.5,
            linewidth=2.2,
            color=PRODUCT_COLORS[asin],
            label=label,
            zorder=3,
        )
        ax_b.fill_between(qx, vals, alpha=0.08, color=PRODUCT_COLORS[asin])
    ax_b.set_xticks(qx[::2], [quarters[i] for i in range(0, len(quarters), 2)], rotation=25, fontsize=8.2)
    ax_b.set_ylabel("每季度新增评论数 (条)", fontsize=9.5, color=NAVY)
    ax_b.grid(True, linestyle="--", alpha=0.5, color="#CBD5E1", zorder=0)
    ax_b.spines["top"].set_visible(False)
    ax_b.spines["right"].set_visible(False)
    ax_b.legend(loc="upper left", frameon=True, facecolor="#FAF8F5", edgecolor="none", fontsize=8.5)
    ax_b.annotate(
        "2022Q3–2023Q2 评论密集期\n(数据集截止于 2023-09)",
        xy=(qx[-3], 1350),
        xytext=(qx[-8], 1650),
        fontsize=8.2,
        color=NAVY,
        bbox=dict(boxstyle="round,pad=0.3", facecolor=TEAL_LIGHT, edgecolor=TEAL),
        arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.2),
    )

    # Panel C: Aspect Sentiment Breakdown (V2 Engine 43,102 rows)
    ax_c = fig.add_axes([0.095, 0.105, 0.365, 0.285])
    asp_piv = ev_df.groupby(["aspect", "sentiment"]).size().unstack(fill_value=0)
    asp_piv["total"] = asp_piv.sum(axis=1)
    asp_piv = asp_piv.sort_values("total", ascending=True)
    y_pos = np.arange(len(asp_piv))
    pos_vals = asp_piv.get("positive", pd.Series(0, index=asp_piv.index)).values
    neg_vals = asp_piv.get("negative", pd.Series(0, index=asp_piv.index)).values
    unk_vals = asp_piv.get("unknown", pd.Series(0, index=asp_piv.index)).values

    ax_c.barh(y_pos, pos_vals, color="#1D4ED8", height=0.62, label="正面 (Positive)", zorder=3)
    ax_c.barh(y_pos, neg_vals, left=pos_vals, color="#60A5FA", height=0.62, label="负面 (Negative)", zorder=3)
    ax_c.barh(y_pos, unk_vals, left=pos_vals + neg_vals, color="#CBD5E1", height=0.62, label="无显式极性词 (Unknown，拒绝星级污染)", zorder=3)

    for idx, (tot, p_v, n_v) in enumerate(zip(asp_piv["total"], pos_vals, neg_vals)):
        ratio = p_v / (p_v + n_v) * 100 if (p_v + n_v) > 0 else 0
        ax_c.text(
            tot + 180,
            idx,
            f"{tot:,} 条 (正比 {ratio:.0f}%)",
            va="center",
            ha="left",
            fontsize=8.0,
            fontweight="bold",
            color=NAVY,
        )

    ax_c.set_yticks(y_pos, asp_piv.index, fontsize=9.5, fontweight="bold")
    ax_c.set_xlabel("子句级证据数量 (条)", fontsize=9.5, color=NAVY)
    ax_c.set_xlim(0, max(asp_piv["total"]) * 1.30)
    ax_c.grid(axis="x", linestyle="--", alpha=0.5, color="#CBD5E1", zorder=0)
    ax_c.spines["top"].set_visible(False)
    ax_c.spines["right"].set_visible(False)
    ax_c.legend(loc="lower right", frameon=True, facecolor="#FAF8F5", edgecolor="none", fontsize=8.0)

    # Panel D: Explicit Scene × Product Density Heatmap (per 1,000 reviews)
    ax_d = fig.add_axes([0.56, 0.115, 0.38, 0.265])
    rev_totals = raw_df.groupby("parent_asin").size().to_dict()
    scenes_order = ["运动", "办公通话", "长时间佩戴", "通勤", "居家"]
    pids_order = ["B0C337TNGS", "B0C338S8M7", "B09PRC3WC5"]

    heat_mat = np.zeros((len(scenes_order), len(pids_order)))
    raw_counts_mat = np.zeros((len(scenes_order), len(pids_order)), dtype=int)
    scene_df = ev_df[ev_df["scene"].isin(scenes_order)]
    for i, sc in enumerate(scenes_order):
        for j, pid in enumerate(pids_order):
            c = len(scene_df[(scene_df["scene"] == sc) & (scene_df["product_id"] == pid)])
            raw_counts_mat[i, j] = c
            heat_mat[i, j] = c / rev_totals[pid] * 1000.0

    im = ax_d.imshow(heat_mat, cmap="Blues", aspect="auto")
    ax_d.set_xticks(np.arange(len(pids_order)), [PRODUCT_NAMES[p] for p in pids_order], fontsize=9.2, fontweight="bold")
    ax_d.set_yticks(np.arange(len(scenes_order)), scenes_order, fontsize=9.5, fontweight="bold")
    for i in range(len(scenes_order)):
        for j in range(len(pids_order)):
            val = heat_mat[i, j]
            cnt = raw_counts_mat[i, j]
            txt_col = "white" if val > 55 else NAVY
            ax_d.text(
                j,
                i,
                f"{val:.1f} ‰\n({cnt} 条)",
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color=txt_col,
            )
    cbar = fig.colorbar(im, ax=ax_d, fraction=0.035, pad=0.03)
    cbar.set_label("每 1,000 条评论场景证据数", fontsize=8.5, color=NAVY)

    out_path = OUT_DIR / "fig02_dataset_eda_overview.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def generate_fig03_algorithm_workflow() -> Path:
    """Fig 03: Detailed Algorithmic Workflow & Mathematical Formulation of review_engine V2."""
    fig, bg_ax = create_canvas(
        tag="ACADEMIC GROUP MEETING · PART III : ALGORITHMIC WORKFLOW & METHODOLOGY",
        title="图 3  可配置评论分析引擎 (review_engine V2) 算法工作流与核心数学机制",
        subtitle="配置解耦 → 转折子句切分 → 最小字符距离情感归属 → Wilson 置信区间与冲突打分 → 去锚词细粒度聚类与评估闭环",
        footnote="核心源码：review_engine/core.py, review_engine/aspect_topics.py, review_engine/sample.py, review_engine/evaluate.py | 单元测试：tests/test_engine.py",
    )

    ax = fig.add_axes([0.03, 0.055, 0.94, 0.80])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Top Pipeline Row: 5 Core Algorithmic Modules
    col_xs = [0.005, 0.205, 0.405, 0.605, 0.805]
    col_w = 0.188
    top_y = 0.47
    top_h = 0.51

    modules = [
        (
            "M1",
            "领域配置与输入清洗\n(Config & Normalize)",
            NAVY,
            "#F0F4F8",
            "【可拔插词典 config/earbuds.json】\n"
            "• 8 大体验维度 (aspects) 词表\n"
            "• 5 大使用场景 (scenes) 词表\n"
            "• 正/负情感词、否定词、质量词\n\n"
            "【normalize() 清洗与稳定哈希】\n"
            "• HTML 反转义 & 正则剥离标签\n"
            "• 缺失 review_id 时计算确定性指纹：\n"
            "  SHA256(pid || uid || ts || text)[:20]\n"
            "• 拦截剔除 421 条重复评论\n"
            "• 输出：23,592 条规范化独立评论",
        ),
        (
            "M2",
            "转折子句切分与偏移追踪\n(Clause Segmentation)",
            NAVY_MID,
            "#EDF3F8",
            "【clauses() 双级切分算法】\n"
            "1. 句级正则切分：\n"
            "   r'[^.!?;]+(?:[.!?;]|$)'\n"
            "2. 转折连词二次切分：\n"
            "   r'\\b(?:but|however|although|yet)\\b'\n\n"
            "【原文字符偏移不变量】\n"
            "• 剥离连词与首尾空白后精确换算：\n"
            "  start = m.start() + lo + lead\n"
            "  end = start + len(content)\n"
            "• 严格保证：text[start:end] == clause\n"
            "• 解决长句正负评价混杂串扰问题",
        ),
        (
            "M3",
            "最小距离情感归属与否定\n(Distance-Based Sentiment)",
            TEAL,
            TEAL_LIGHT,
            "【extract() 细粒度情感绑定】\n"
            "1. 滑动窗口近邻否定翻转：\n"
            "   检查情感词前 3 个 token：\n"
            "   若命中 negations → sign = -sign\n\n"
            "2. 最小字符距离唯一归属准则：\n"
            "   计算情感词 pos 到各维度词距：\n"
            "   d(a) = min |pos - span.start()|\n"
            "   仅当 d(a*) 唯一最小且 d(a*) ≤ 70\n"
            "   时将 sign 计入维度 a*！\n\n"
            "3. 拒绝星级污染：\n"
            "   无匹配情感词标 unknown (不用星级替代)",
        ),
        (
            "M4",
            "Mixed 剥离、Wilson 区间与冲突\n(Aggregation & Conflict Score)",
            ORANGE,
            ORANGE_LIGHT,
            "【aggregate() 评论级聚合】\n"
            "• 按 (product, aspect, scene) 归并到\n"
            "  review_id 粒度\n"
            "• 同一评论含正+负子句 → 标为 mixed\n"
            "  (不重复计入正负分母 n = P + N)\n\n"
            "【Wilson 95% 置信区间 (z=1.96)】\n"
            "• 修正小样本极端比例偏差\n\n"
            "【需求冲突分 (门槛 n ≥ 20)】\n"
            "• 平衡度 × 样本量对数饱和权重：\n"
            "  Score = [2·min(P,N)/n] ·\n"
            "          min(1, ln(1+n)/ln(101))",
        ),
        (
            "M5",
            "去锚词聚类、检索与评估闭环\n(Topics, Retrieval & Eval)",
            "#1E40AF",
            "#F0F7FF",
            "【aspect_topics.py 去锚词聚类】\n"
            "• 停用词 = 英文停用词 ∪ 通用评价词\n"
            "           ∪ 当前维度配置锚词\n"
            "• 1-2gram 稀疏 TF-IDF (12,000维)\n"
            "  + MiniBatchKMeans (8×5=40个子簇)\n\n"
            "【retrieve() 子句向量检索】\n"
            "• 50,000维 Sublinear TF-IDF 余弦检索\n"
            "  + 维度/场景先验过滤 + 评论去重\n\n"
            "【sample.py & evaluate.py】\n"
            "• 90条分层抽样 → 混淆矩阵与 F1 报告",
        ),
    ]

    for idx, (m_code, m_title, ec, fc, body) in enumerate(modules):
        x = col_xs[idx]
        # Card container
        ax.add_patch(
            FancyBboxPatch(
                (x, top_y),
                col_w,
                top_h,
                boxstyle="round,pad=0.006,rounding_size=0.018",
                facecolor=fc,
                edgecolor=ec,
                linewidth=1.8,
            )
        )
        # Header banner
        ax.add_patch(
            FancyBboxPatch(
                (x, top_y + top_h - 0.088),
                col_w,
                0.088,
                boxstyle="round,pad=0.006,rounding_size=0.018",
                facecolor=ec,
                edgecolor="none",
            )
        )
        ax.text(
            x + 0.012,
            top_y + top_h - 0.044,
            m_code,
            fontsize=9.5,
            fontweight="bold",
            color=ec,
            va="center",
            ha="left",
            bbox=dict(boxstyle="round,pad=0.22", facecolor="white", edgecolor="none"),
        )
        ax.text(
            x + 0.048,
            top_y + top_h - 0.044,
            m_title,
            fontsize=10.0,
            fontweight="bold",
            color="white",
            va="center",
            ha="left",
            linespacing=1.22,
        )
        ax.text(
            x + 0.010,
            top_y + top_h - 0.112,
            body,
            fontsize=8.35,
            color="#1E293B",
            va="top",
            ha="left",
            linespacing=1.34,
        )

        if idx < len(modules) - 1:
            ax.annotate(
                "",
                xy=(col_xs[idx + 1] - 0.002, top_y + top_h / 2),
                xytext=(x + col_w + 0.002, top_y + top_h / 2),
                arrowprops=dict(arrowstyle="-|>,head_width=0.38,head_length=0.45", color=NAVY, lw=2.0),
            )

    # Bottom Row: Concrete Worked Example & Mathematical Formulation Box
    # Left Bottom Box: Concrete Clause & Distance Attribution Example
    ax.add_patch(
        FancyBboxPatch(
            (0.005, 0.01),
            0.585,
            0.41,
            boxstyle="round,pad=0.006,rounding_size=0.018",
            facecolor="#FFFFFF",
            edgecolor=TEAL,
            linewidth=1.6,
        )
    )
    ax.text(
        0.018,
        0.392,
        "算法微观运行实例图解：转折切分 + 近邻否定翻转 + 最小字符距离唯一归属 (以 test_engine.py 验证用例为例)",
        fontsize=10.5,
        fontweight="bold",
        color=NAVY,
        va="top",
    )

    # Original review box
    ax.add_patch(FancyBboxPatch((0.02, 0.285), 0.555, 0.068, boxstyle="round,pad=0.005", facecolor=SLATE_LIGHT, edgecolor=BORDER_COLOR))
    ax.text(
        0.03,
        0.319,
        '原始评论 (Input Review):  "The sound is great for running, but the battery is not good."',
        fontsize=9.3,
        fontweight="bold",
        color=NAVY,
        va="center",
    )

    # Split into Clause 1 and Clause 2
    ax.annotate("", xy=(0.16, 0.255), xytext=(0.24, 0.282), arrowprops=dict(arrowstyle="-|>,head_width=0.3", color=TEAL, lw=1.6))
    ax.annotate("", xy=(0.44, 0.255), xytext=(0.36, 0.282), arrowprops=dict(arrowstyle="-|>,head_width=0.3", color=CRIMSON, lw=1.6))
    ax.text(0.30, 0.268, "按转折词 'but' 切分并记录精确偏移 [start, end]", fontsize=8.0, color=SLATE, ha="center")

    # Clause 1 box
    draw_box(
        ax,
        0.02,
        0.03,
        0.265,
        0.22,
        "子句 1 (Offset [0, 30])",
        '文本: "The sound is great for running"\n'
        "• 维度命中: 音质 ('sound' @4), 佩戴稳定 ('running' @23)\n"
        "• 场景命中: 运动 ('running')\n"
        "• 情感词: 'great' (@13, sign = +1)\n"
        "• 距离计算: d(音质)=|13-4|=9 < d(佩戴)=|13-23|=10 ≤ 70\n"
        "• 输出: (音质, 运动, positive) & (佩戴稳定, 运动, unknown)",
        fc=TEAL_LIGHT,
        ec=TEAL,
        title_color="#096B68",
        title_size=9.2,
        body_size=8.0,
    )

    # Clause 2 box
    draw_box(
        ax,
        0.305,
        0.03,
        0.27,
        0.22,
        "子句 2 (Offset [36, 60])",
        '文本: "the battery is not good."\n'
        "• 维度命中: 续航与充电 ('battery' @4)\n"
        "• 情感词: 'good' (@19, 初始极性 +1)\n"
        "• 前3词否定检测: prior=['the','battery','is','not']\n"
        "  命中 'not' ∈ negations → 极性翻转 sign = -1\n"
        "• 距离计算: d(续航)=|19-4|=15 ≤ 70 (唯一最近)\n"
        "• 输出: (续航与充电, 未知, negative)",
        fc=CRIMSON_LIGHT,
        ec=CRIMSON,
        title_color=CRIMSON,
        title_size=9.2,
        body_size=8.0,
    )

    # Right Bottom Box: V1 vs V2 Algorithmic Upgrade & Core Formulas
    ax.add_patch(
        FancyBboxPatch(
            (0.605, 0.01),
            0.388,
            0.41,
            boxstyle="round,pad=0.006,rounding_size=0.018",
            facecolor="#FFFFFF",
            edgecolor=ORANGE,
            linewidth=1.6,
        )
    )
    ax.text(
        0.618,
        0.392,
        "算法引擎演进对比 (V1 试验脚本 → V2 可配置引擎) 与核心统计准则",
        fontsize=10.5,
        fontweight="bold",
        color=NAVY,
        va="top",
    )

    v1_v2_text = (
        "1. 粒度与串扰抑制升级：\n"
        "   • V1 (run_earbud_pilot.py)：整句切分，句内所有维度共享同一情感分；\n"
        "     无情感词时回退使用整条评论星级 (rating≥4 标正面)，导致大量客观描述被污染。\n"
        "   • V2 (review_engine/core.py)：转折子句切分 + 70字符最小距离唯一归属；\n"
        "     彻底废除星级回退 (无情感词标 unknown)，子句证据从 57,342 提纯至 43,102 条。\n\n"
        "2. 评论级去重与 Mixed 态度剥离：\n"
        "   • 同一 review_id 在同一 (产品, 维度, 场景) 下若同时含正负子句，单列为 mixed，\n"
        "     不计入正向比例 P / (P + N)，防止长评多子句主导总体比例。\n\n"
        "3. 需求冲突分与置信区间双重门控：\n"
        "   • 仅当有效正负评论数 n = P + N ≥ 20 时计算冲突分 ConflictScore ∈ [0, 1]；\n"
        "   • 同时输出 Wilson 95% 区间 [wilson_low, wilson_high] 量化样本不确定性。"
    )
    ax.text(0.618, 0.342, v1_v2_text, fontsize=8.35, color="#1E293B", va="top", linespacing=1.38)

    out_path = OUT_DIR / "fig03_algorithm_workflow.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def generate_fig04_conflict_and_topic_results(sum_df: pd.DataFrame, top_df: pd.DataFrame, feat_df: pd.DataFrame) -> Path:
    """Fig 04: Empirical Results - Requirement Conflict Wilson Intervals, PCA Map, Aspect Sub-topics & Evidence Graph."""
    fig, bg_ax = create_canvas(
        tag="ACADEMIC GROUP MEETING · PART IV : EMPIRICAL RESULTS & CONFLICT GRAPH",
        title="图 4  核心实验结果：需求分歧识别 (Wilson 区间与冲突排序)、细粒度话题聚类与证据图谱",
        subtitle="基于 outputs/engine_v2/summary.csv (120 单元) 与 outputs/aspect_topics_v2/topics.csv (40 个细粒度子簇) 的实证发现",
        footnote="数据来源：outputs/engine_v2/summary.csv, outputs/aspect_topics_v2/topics.csv, outputs/earbud_target_full/review_features.csv",
    )

    draw_card(bg_ax, 0.03, 0.46, 0.48, 0.39, "Top 10 高分需求分歧单元：正向比例 Wilson 95% 置信区间与冲突分", badge="A", header_color=NAVY)
    draw_card(bg_ax, 0.53, 0.46, 0.44, 0.39, "评论语义空间分布投影 (PCA 2D + KMeans 聚类簇分布，N=24,084)", badge="B", header_color=NAVY_MID)
    draw_card(bg_ax, 0.03, 0.055, 0.48, 0.375, "去锚词维度内细粒度聚类 (aspect_topics_v2) 典型子话题与代表原句", badge="C", header_color=TEAL)
    draw_card(bg_ax, 0.53, 0.055, 0.44, 0.375, "可追溯需求冲突证据图谱 (Requirement Conflict Evidence Sub-Graph)", badge="D", header_color=ORANGE)

    # Panel A: Forest plot of Wilson 95% CI + Conflict Score for Top 10 Conflict Units
    ax_a = fig.add_axes([0.165, 0.50, 0.33, 0.29])
    valid_sum = sum_df[sum_df["sufficient"] == True].sort_values("conflict_score", ascending=False).head(10).iloc[::-1]

    y_idx = np.arange(len(valid_sum))
    short_p = {"B0C337TNGS": "Powerbeats Pro", "B0C338S8M7": "Studio Buds", "B09PRC3WC5": "TOZO A1 Mini"}
    labels_a = [
        f"{short_p.get(r.product_id, r.product_id)}\n[{r.aspect} · {r.scene}]"
        for r in valid_sum.itertuples()
    ]
    ratios = valid_sum["positive_ratio"].values * 100
    lo_err = (valid_sum["positive_ratio"] - valid_sum["wilson_low"]).values * 100
    hi_err = (valid_sum["wilson_high"] - valid_sum["positive_ratio"]).values * 100
    c_scores = valid_sum["conflict_score"].values

    ax_a.axvline(50, color=CRIMSON, linestyle="--", linewidth=1.4, alpha=0.8, label="50% 正负均势分歧线")
    ax_a.axvspan(40, 60, color=CRIMSON_LIGHT, alpha=0.45, label="强分歧敏感带 (40%–60%)")

    for i, r in enumerate(valid_sum.itertuples()):
        col = PRODUCT_COLORS.get(r.product_id, NAVY)
        ax_a.errorbar(
            ratios[i],
            i,
            xerr=[[lo_err[i]], [hi_err[i]]],
            fmt="o",
            color=col,
            ecolor=col,
            elinewidth=2.2,
            capsize=4,
            markersize=6.5,
            zorder=4,
        )
        ax_a.text(
            valid_sum["wilson_high"].values[i] * 100 + 1.5,
            i,
            f"Conflict={r.conflict_score:.2f} (+{r.positive}/-{r.negative})",
            va="center",
            ha="left",
            fontsize=7.6,
            fontweight="bold",
            color=NAVY,
        )

    ax_a.set_yticks(y_idx, labels_a, fontsize=7.8, fontweight="bold")
    ax_a.set_xlabel("正面证据比例 (%) 及 Wilson 95% 置信区间", fontsize=9.0, color=NAVY)
    ax_a.set_xlim(15, 108)
    ax_a.grid(axis="x", linestyle=":", alpha=0.6, color="#CBD5E1")
    ax_a.spines["top"].set_visible(False)
    ax_a.spines["right"].set_visible(False)
    ax_a.legend(loc="lower left", fontsize=7.6, frameon=True, facecolor="#FAF8F5", edgecolor="none")

    # Panel B: PCA + KMeans Scatter Map from review_features.csv
    ax_b = fig.add_axes([0.57, 0.505, 0.38, 0.285])
    # Subsample slightly for clean high-speed plotting while keeping exact structure
    sample_feat = feat_df.sample(n=min(6000, len(feat_df)), random_state=42)
    cluster_names = {
        0: "簇0: 综合好评与日常音乐",
        1: "簇1: 蓝牙配对与断连反馈",
        2: "簇2: 续航时长与充电盒体验",
        3: "簇3: 佩戴稳固度与耳廓舒适",
        4: "簇4: 降噪效果与通话清晰度",
    }
    cmap_cols = ["#0F2942", "#1D4ED8", "#3B82F6", "#60A5FA", "#64748B"]
    for cid in sorted(sample_feat["kmeans_cluster"].unique()):
        sub = sample_feat[sample_feat["kmeans_cluster"] == cid]
        ax_b.scatter(
            sub["pca_x"],
            sub["pca_y"],
            s=10,
            alpha=0.45,
            color=cmap_cols[cid % len(cmap_cols)],
            label=f"{cluster_names.get(cid, f'Cluster {cid}')} (n={len(feat_df[feat_df['kmeans_cluster']==cid]):,})",
            edgecolors="none",
        )
        cx, cy = sub["pca_x"].mean(), sub["pca_y"].mean()
        ax_b.scatter(cx, cy, s=90, color=cmap_cols[cid % len(cmap_cols)], edgecolor="white", linewidth=1.5, marker="X", zorder=5)

    ax_b.set_xlabel("PCA 第一主成分 (PC1)", fontsize=9.0, color=NAVY)
    ax_b.set_ylabel("PCA 第二主成分 (PC2)", fontsize=9.0, color=NAVY)
    ax_b.grid(True, linestyle="--", alpha=0.4, color="#CBD5E1")
    ax_b.spines["top"].set_visible(False)
    ax_b.spines["right"].set_visible(False)
    ax_b.legend(loc="upper right", fontsize=7.5, frameon=True, facecolor="white", framealpha=0.9, edgecolor=BORDER_COLOR)

    # Panel C: Aspect Sub-Topics Table Showcase (from aspect_topics_v2/topics.csv)
    ax_c = fig.add_axes([0.04, 0.068, 0.46, 0.31])
    ax_c.set_xlim(0, 1)
    ax_c.set_ylim(0, 1)
    ax_c.axis("off")

    curated_topics = [
        ("佩戴稳定 · 簇1", "900 条评论", "ear, don, buds, won ear, constantly", '"They DO NOT stay in my ear." / "always falling out"', CRIMSON),
        ("佩戴稳定 · 簇4", "383 条评论", "small ears, pocket, case, perfectly", '"I have small ears and they fit without falling out"', TEAL),
        ("续航与充电 · 簇0", "252 条评论", "hour, run, 30 minutes, hour shift", '"4 Hour battery life not 6." / "only last for an hour"', CRIMSON),
        ("续航与充电 · 簇2", "1,418 条评论", "case, buds, dead, left, right, charge", '"The case will not charge them on it\'s own"', ORANGE),
        ("触控交互 · 簇1", "770 条评论", "volume, pause, skip, press, button", '"The volume button on the earbud is something I LOVE"', TEAL),
        ("触控交互 · 簇2", "59 条评论", "sensitive, super sensitive, control", '"these earbuds are so sensitive to touch." (误触痛点)', ORANGE),
        ("连接 · 簇1", "288 条评论", "time, won, right, try, ear, connect", '"take them both out and only one will connect." (单耳断连)', CRIMSON),
        ("通话 · 簇2", "940 条评论", "hear, phone, noise, people, breaking up", '"No one could hear me on calls" vs "breaking up"', NAVY_MID),
    ]

    # Header row
    ax_c.add_patch(FancyBboxPatch((0.01, 0.89), 0.98, 0.09, boxstyle="round,pad=0.004", facecolor=SLATE_LIGHT, edgecolor="none"))
    ax_c.text(0.02, 0.935, "维度与子簇编号", fontsize=8.5, fontweight="bold", color=NAVY, va="center")
    ax_c.text(0.22, 0.935, "覆盖评论数", fontsize=8.5, fontweight="bold", color=NAVY, va="center")
    ax_c.text(0.36, 0.935, "去锚词后 Top 特征词 (TF-IDF)", fontsize=8.5, fontweight="bold", color=NAVY, va="center")
    ax_c.text(0.67, 0.935, "簇中心代表性原始证据片段", fontsize=8.5, fontweight="bold", color=NAVY, va="center")

    row_y = np.linspace(0.78, 0.05, len(curated_topics))
    for i, (t_name, t_cnt, t_terms, t_quote, col) in enumerate(curated_topics):
        ry = row_y[i]
        if i % 2 == 0:
            ax_c.add_patch(mpatches.Rectangle((0.01, ry - 0.035), 0.98, 0.095, facecolor="#F8FAFC", edgecolor="none"))
        ax_c.text(
            0.02,
            ry + 0.01,
            t_name,
            fontsize=8.0,
            fontweight="bold",
            color="white",
            va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=col, edgecolor="none"),
        )
        ax_c.text(0.22, ry + 0.01, t_cnt, fontsize=8.0, fontweight="bold", color=NAVY, va="center")
        ax_c.text(0.36, ry + 0.01, t_terms, fontsize=7.8, color=SLATE, va="center")
        ax_c.text(0.67, ry + 0.01, t_quote, fontsize=7.6, color="#1E293B", va="center")

    # Panel D: Evidence Graph Network Diagram
    ax_d = fig.add_axes([0.54, 0.068, 0.42, 0.31])
    ax_d.set_xlim(0, 1)
    ax_d.set_ylim(0, 1)
    ax_d.axis("off")

    # Draw a crisp 4-layer hierarchical graph: Product -> Aspect -> Scene -> Polarized Evidence
    # Layer 1: Product Nodes
    draw_box(ax_d, 0.02, 0.62, 0.21, 0.24, "Powerbeats Pro", "B0C337TNGS\n(运动耳挂型)", fc=ORANGE_LIGHT, ec=ORANGE, title_size=8.8, body_size=7.8)
    draw_box(ax_d, 0.02, 0.16, 0.21, 0.24, "Studio Buds", "B0C338S8M7\n(主动降噪入耳)", fc=TEAL_LIGHT, ec=TEAL, title_size=8.8, body_size=7.8)

    # Layer 2: Aspect & Scene Conflict Nodes
    draw_box(
        ax_d,
        0.31,
        0.60,
        0.25,
        0.28,
        "续航与充电 × 运动",
        "有效正负评论 n=55\n正面 34 vs 负面 21\nConflict Score = 0.67",
        fc="#F0F7FF",
        ec="#1D4ED8",
        title_size=8.6,
        body_size=7.6,
    )
    draw_box(
        ax_d,
        0.31,
        0.14,
        0.25,
        0.28,
        "通话质量 × 日常/办公",
        "有效正负评论 n=103\n正面 52 vs 负面 51\nConflict Score = 0.99",
        fc=TEAL_LIGHT,
        ec=TEAL,
        title_size=8.6,
        body_size=7.6,
    )

    # Layer 3: Opposing Real Review Evidence Nodes
    draw_box(
        ax_d,
        0.64,
        0.74,
        0.34,
        0.21,
        "正面证据 (+34 条, Wilson [48.6%, 73.5%])",
        '• "Great battery life for long runs and gym"\n• 单次运动续航充足，耳挂设计狂甩不掉',
        fc="#EFF6FF",
        ec=TEAL,
        title_color=NAVY,
        title_size=8.0,
        body_size=7.3,
    )
    draw_box(
        ax_d,
        0.64,
        0.49,
        0.34,
        0.21,
        "负面证据 (-21 条 · 充电盒接触痛点)",
        '• "One earbud won\'t charge in the case after sweat"\n• 运动出汗或耳挂回弹导致充电触点接触不良',
        fc=CRIMSON_LIGHT,
        ec=CRIMSON,
        title_color=CRIMSON,
        title_size=8.0,
        body_size=7.3,
    )

    draw_box(
        ax_d,
        0.64,
        0.25,
        0.34,
        0.20,
        "正面证据 (+52 条, 室内安静环境)",
        '• "Sound quality is great, microphone is clear"\n• 室内安静办公会议通话清晰度良好',
        fc="#EFF6FF",
        ec=TEAL,
        title_color=NAVY,
        title_size=8.0,
        body_size=7.3,
    )
    draw_box(
        ax_d,
        0.64,
        0.02,
        0.34,
        0.20,
        "负面证据 (-51 条, 户外/嘈杂背景环境)",
        '• "No one could hear me on calls... picks up noise"\n• 无延伸麦杆，嘈杂环境下拾音降噪能力不足',
        fc=CRIMSON_LIGHT,
        ec=CRIMSON,
        title_color=CRIMSON,
        title_size=8.0,
        body_size=7.3,
    )

    # Directed edges
    arrows = [
        ((0.23, 0.74), (0.31, 0.74), ORANGE),
        ((0.23, 0.28), (0.31, 0.28), TEAL),
        ((0.56, 0.78), (0.64, 0.84), TEAL),
        ((0.56, 0.68), (0.64, 0.60), CRIMSON),
        ((0.56, 0.32), (0.64, 0.35), TEAL),
        ((0.56, 0.22), (0.64, 0.12), CRIMSON),
    ]
    for p1, p2, col in arrows:
        ax_d.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle="-|>,head_width=0.3", color=col, lw=1.6))

    out_path = OUT_DIR / "fig04_conflict_and_topic_results.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def generate_fig05_frontend_prototype() -> Path:
    """Fig 05: Frontend Prototype Functional Architecture & Grounded DeepSeek RAG Workflow."""
    fig, bg_ax = create_canvas(
        tag="ACADEMIC GROUP MEETING · PART V : EXPLAINABLE PROTOTYPE & GROUNDED RAG SYSTEM",
        title="图 5  可解释产品选择辅助系统：前端交互原型功能架构与受控 RAG 证据生成机制",
        subtitle="基于 Streamlit 毛玻璃交互界面 (提交项目/demo.py) 与本地规则检索 + DeepSeek 受控生成的协同架构",
        footnote="原型代码：提交项目/demo.py (163行), 提交项目/agent.py (39行), 提交项目/启动原型.bat | 支持多品类扩展演示與无 API Key 降级核查",
    )

    # Left Card: UI Functional Architecture Mockup & Interaction Flow
    draw_card(
        bg_ax,
        0.03,
        0.06,
        0.52,
        0.79,
        "前端交互原型四大功能层与高保真界面模块拆解 (Streamlit Interactive Prototype)",
        badge="A",
        header_color=NAVY,
    )
    ax_ui = fig.add_axes([0.04, 0.07, 0.50, 0.72])
    ax_ui.set_xlim(0, 1)
    ax_ui.set_ylim(0, 1)
    ax_ui.axis("off")

    # Simulated Browser Window Frame
    ax_ui.add_patch(
        FancyBboxPatch(
            (0.01, 0.01),
            0.98,
            0.97,
            boxstyle="round,pad=0.006,rounding_size=0.02",
            facecolor="#EFF5F7",
            edgecolor=NAVY_MID,
            linewidth=1.6,
        )
    )
    # Browser Top Bar
    ax_ui.add_patch(
        FancyBboxPatch(
            (0.01, 0.93),
            0.98,
            0.05,
            boxstyle="round,pad=0.004,rounding_size=0.015",
            facecolor=NAVY,
            edgecolor="none",
        )
    )
    for idx, dot_col in enumerate(["#93C5FD", "#60A5FA", "#3B82F6"]):
        ax_ui.add_patch(mpatches.Circle((0.035 + idx * 0.022, 0.955), 0.007, color=dot_col))
    ax_ui.text(
        0.50,
        0.955,
        "[Web App] 基于用户评论的需求识别与可解释产品选择辅助系统 (http://127.0.0.1:8501)",
        fontsize=8.6,
        fontweight="bold",
        color="white",
        ha="center",
        va="center",
    )

    # Left Sidebar inside Browser
    ax_ui.add_patch(
        FancyBboxPatch(
            (0.02, 0.025),
            0.23,
            0.89,
            boxstyle="round,pad=0.004,rounding_size=0.012",
            facecolor="#FFFFFF",
            edgecolor=BORDER_COLOR,
        )
    )
    ax_ui.text(0.035, 0.885, "[设置] 产品设置与会话侧边栏", fontsize=8.5, fontweight="bold", color=NAVY)
    sidebar_items = (
        "• 体验用户：\n  student@zju.edu.cn\n\n"
        "• 当前类别：\n  [无线耳机 (已接入)]\n  [智能手表 (结构演示)]\n\n"
        "• 款式筛选下拉框：\n  - 比较全部款式\n  - Powerbeats Pro\n  - Beats Studio Buds\n  - TOZO A1 Mini\n\n"
        "• DeepSeek API Key：\n  [••••••••••••] (可选覆盖)\n"
        "• 模型名称：\n  [deepseek-flash]\n\n"
        "• 状态路由按钮：\n  [切换商品类别]\n  [退出体验]"
    )
    ax_ui.text(0.032, 0.84, sidebar_items, fontsize=7.6, color="#2C3E50", va="top", linespacing=1.34)

    # Main Content Area inside Browser: 4 Stacked Layers
    # Layer 1: Entry Gate & Category Router banner
    draw_box(
        ax_ui,
        0.27,
        0.78,
        0.70,
        0.135,
        "① 门户准入与跨品类路由 (Entry Gate & Multi-Category Router)",
        "• 邮箱正则校验 + 品类识别路由：支持「无线耳机」(完整数据实装) 与「智能手表」(跨品类 UI 框架演示)\n"
        "• 顶部毛玻璃 Hero 横幅：展示当前选中品类、款式范围及「数据截至 2023 年 9 月」明确时间边界提示",
        fc="#0F2942",
        ec="#1E3A8A",
        title_color="#FFFFFF",
        body_color="#E2E8F0",
        title_size=8.6,
        body_size=7.4,
        header_gap=0.042,
    )

    # Layer 2: 3 Product Cards Wall
    draw_box(
        ax_ui,
        0.27,
        0.555,
        0.70,
        0.205,
        "② 商品目录卡片墙与单品聚焦切换 (Interactive Product Catalog)",
        "",
        fc="#FFFFFF",
        ec=BORDER_COLOR,
        title_color=NAVY,
        title_size=8.6,
    )
    sub_cards = [
        (0.285, "Powerbeats Pro", "运动佩戴 · 8,989条", ORANGE, "查看这款"),
        (0.510, "Beats Studio Buds", "日常通勤 · 6,874条", TEAL, "[已选] 比较全部"),
        (0.735, "TOZO A1 Mini", "轻巧便携 · 8,221条", NAVY_MID, "查看这款"),
    ]
    for sx, sname, stag, scol, sbtn in sub_cards:
        ax_ui.add_patch(FancyBboxPatch((sx, 0.57), 0.21, 0.13, boxstyle="round,pad=0.004", facecolor="#F8FAFC", edgecolor=scol, lw=1.2))
        ax_ui.text(sx + 0.105, 0.67, sname, fontsize=7.8, fontweight="bold", color=NAVY, ha="center")
        ax_ui.text(sx + 0.105, 0.635, stag, fontsize=7.0, color=scol, ha="center", fontweight="bold")
        ax_ui.text(
            sx + 0.105,
            0.592,
            sbtn,
            fontsize=6.8,
            color="white",
            ha="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor=scol, edgecolor="none"),
        )

    # Layer 3: 4 Quick Scene Presets
    draw_box(
        ax_ui,
        0.27,
        0.41,
        0.70,
        0.125,
        "③ 四大高频选购场景快捷预设 (One-Click Scenario Presets)",
        "",
        fc="#FFFFFF",
        ec=BORDER_COLOR,
        title_color=NAVY,
        title_size=8.6,
    )
    presets = ["[通勤] 通勤降噪", "[运动] 运动佩戴", "[续航] 全天续航", "[通话] 办公通话"]
    for pidx, plabel in enumerate(presets):
        px = 0.285 + pidx * 0.17
        ax_ui.add_patch(FancyBboxPatch((px, 0.425), 0.155, 0.052, boxstyle="round,pad=0.004", facecolor=TEAL_LIGHT, edgecolor=TEAL))
        ax_ui.text(px + 0.077, 0.451, plabel, fontsize=7.5, fontweight="bold", color="#096B68", ha="center", va="center")

    # Layer 4: Chat UI + Grounded Evidence Expander
    draw_box(
        ax_ui,
        0.27,
        0.025,
        0.70,
        0.365,
        "④ 多轮对话咨询 (Chat UI) + 可展开原始评论证据核查面板 (Evidence Expander)",
        "[用户] 输入：\"我想在跑步时使用，比较在意佩戴稳定和舒适度\"\n"
        "[助手] 回答 (DeepSeek Grounded RAG)：基于跑步场景与佩戴稳定/舒适维度证据对比三款耳机适用性，\n"
        "       明确引用评论编号 (如 review_id #1284) 并提示自动标注局限与样本充足度。\n"
        "[▼ 查看真实评论及覆盖量 (默认展开)]：\n"
        "   • Powerbeats Pro — 佩戴稳定：正面 80 条，负面 12 条 | 佩戴舒适：正面 34 条，负面 3 条\n"
        "   • 展示正/负面代表性原始英文评论片段 + 评论编号 + 所属场景，无 API Key 时仍可独立降级查看！",
        fc="#FFFFFF",
        ec=ORANGE,
        title_color=NAVY,
        body_color="#1E293B",
        title_size=8.6,
        body_size=7.45,
        header_gap=0.052,
    )

    # Right Card: Backend Grounded RAG Architecture & Safety Guardrails
    draw_card(
        bg_ax,
        0.57,
        0.06,
        0.40,
        0.79,
        "本地规则检索与受控大模型协同架构 (Local Grounding + Guardrailed RAG)",
        badge="B",
        header_color=TEAL,
    )
    ax_rag = fig.add_axes([0.58, 0.07, 0.38, 0.72])
    ax_rag.set_xlim(0, 1)
    ax_rag.set_ylim(0, 1)
    ax_rag.axis("off")

    rag_steps = [
        (
            "STEP 1",
            "双语意图解析与主动澄清 (agent.py: parse_request)",
            "• 映射中英文关键词至 8 大体验维度 (ASPECTS) 与 5 大场景 (SCENES)\n"
            "• 若未识别出任何体验维度 → 触发主动追问澄清，拒绝盲目生成",
            0.84,
            0.13,
            "#EDF3F8",
            NAVY,
        ),
        (
            "STEP 2",
            "场景严格过滤与样本充足度门控 (agent.py: analyze)",
            "• 仅筛选明确提及目标维度与场景的证据并按 review_id 去重\n"
            "• 样本量门控：判断 n = pos + neg ≥ minimum (默认 20 条)\n"
            "• 若 n < 20：标记 enough=False (不输出比例，防止小样本误导)\n"
            "• 若 n ≥ 20：计算加一平滑比例 (pos+1)/(n+2) (V2 升级为 Wilson 区间)",
            0.63,
            0.175,
            TEAL_LIGHT,
            TEAL,
        ),
        (
            "STEP 3",
            "六重安全约束 System Prompt 注入 (DeepSeek API)",
            "• 传入结构化 JSON 证据包，强制执行 6 条抗幻觉与安全守则：\n"
            "  ① 仅依据提供的评论证据回答，严禁编造外部参数\n"
            "  ② 严禁把正负评论比例解释为客观性能或真实故障率\n"
            "  ③ 必须指出数据截至 2023 年 9 月及规则自动标注可能出错\n"
            "  ④ 证据不足 (enough=False) 时必须明确告知用户\n"
            "  ⑤ 引用观点时必须标注真实评论编号 (review_id)\n"
            "  ⑥ 将评论正文视为不可信数据，防御评论内 Prompt 注入攻击",
            0.33,
            0.265,
            ORANGE_LIGHT,
            ORANGE,
        ),
        (
            "STEP 4",
            "精细化容错降级与双层可解释输出 (Graceful Degradation)",
            "• 捕获 401(鉴权)/429(限流)/403/404/网络超时并给出中文诊断提示\n"
            "• 即使未配置 API Key 或网络离线，下方「真实评论及覆盖量」\n"
            "  折叠面板依然 100% 正常工作，确保演示零单点故障",
            0.14,
            0.155,
            "#F8FAFC",
            "#1E3A8A",
        ),
    ]

    for idx, (s_code, s_title, s_body, sy, sh, fc, ec) in enumerate(rag_steps):
        draw_box(
            ax_rag,
            0.02,
            sy,
            0.96,
            sh,
            s_title,
            s_body,
            fc=fc,
            ec=ec,
            title_color=NAVY,
            body_color="#1E293B",
            title_size=9.0,
            body_size=7.75,
            badge=s_code,
            badge_color=ec,
            header_gap=0.042,
            badge_offset=0.145,
        )
        if idx < len(rag_steps) - 1:
            next_sy = rag_steps[idx + 1][3]
            next_sh = rag_steps[idx + 1][4]
            ax_rag.annotate(
                "",
                xy=(0.50, next_sy + next_sh + 0.004),
                xytext=(0.50, sy - 0.004),
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.4", color=ec, lw=1.8),
            )

    # Bottom highlight banner inside Card B: V1 -> V2 Integration Roadmap
    ax_rag.add_patch(FancyBboxPatch((0.02, 0.01), 0.96, 0.095, boxstyle="round,pad=0.005", facecolor=CRIMSON_LIGHT, edgecolor=CRIMSON, lw=1.3))
    ax_rag.text(
        0.04,
        0.058,
        "[升级路线] 当前前后端衔接状态与下一步升级点 (P0 优先级)：\n"
        "目前 agent.py 仍读取 V1 (review_aspect_evidence.csv)；下一步将切换至 V2 (engine_v2/evidence.csv\n"
        "& summary.csv)，接入 Wilson 置信区间、Conflict Score 与 TF-IDF 动态相关性检索。",
        fontsize=7.6,
        fontweight="bold",
        color=CRIMSON,
        va="center",
        linespacing=1.32,
    )

    out_path = OUT_DIR / "fig05_frontend_prototype_architecture.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def generate_fig07_method_5steps() -> Path:
    """Generate a 5-column academic figure mapping the 5 steps in '拟采用的方法' to concrete algorithms & code."""
    fig, bg_ax = create_canvas(
        tag="METHODOLOGY & ALGORITHM MAPPING · 「拟采用的方法」五步流程与具体实现算法对照图",
        title="拟采用的方法：五步研究流程与底层具体算法映射",
        subtitle="严格对应开题「1.收集 -> 2.清洗 -> 3.标注 -> 4.分歧 -> 5.呈现」五步框架，每一步均保留原始评价、确定性规则/数学模型与中间结果",
        footnote="代码对应：scripts/extract_*.py -> review_engine/core.py -> review_engine/aspect_topics.py -> agent.py & demo.py",
    )

    steps = [
        {
            "num": "1",
            "title": "收集",
            "desc": "按产品 ID 下载\n评论与元数据",
            "sub_items": ["元数据筛选", "流式 JSONL 定向提取"],
            "algos": [
                ("算法 1.1：位置偏移启发式本体筛选", "正则匹配标题中本体词 (earbuds/watch)\n与配件词 (case/cover/strap) 起始索引：\n仅保留 idx(device) < idx(accessory) 的主商品"),
                ("算法 1.2：O(1) 内存 Gzip 流式哈希过滤", "基于 gzip.open 逐行流式扫描 4,388 万条\nJSONL 评论，通过 parent_asin 哈希集合\nO(1) 命中目标型号并经 .partial 原子落盘"),
                ("对应代码与产出", "• extract_earphone_metadata.py\n• extract_target_amazon_reviews.py\n• 产出：耳机 24,084 条 / 手表 1,324 条"),
            ],
        },
        {
            "num": "2",
            "title": "清洗",
            "desc": "去空值 / 重复\n统一时间、评分",
            "sub_items": ["去重、缺失处理", "配件过滤", "抽样复核"],
            "algos": [
                ("算法 2.1：HTML 剥离与空白规范化", "正则 r'<[^>]+>' 剥离残留 HTML 标签，\n合并 title 与正文并压缩连续空白字符"),
                ("算法 2.2：SHA-256 确定性指纹去重", "缺失 ID 时计算 SHA256(pid|uid|ts|text)[:20]，\n按复合键 (product_id, review_id, lower_text)\n哈希去重（剔除 421 条重复刷屏评论）"),
                ("算法 2.3：分层随机抽样人工复核", "Stratified Sampling (seed=42) 按正/负/待定\n各抽 30 条（共 90 条）双盲复核计算 F1"),
                ("对应代码与产出", "• review_engine/core.py: normalize()\n• review_engine/sample.py & evaluate.py\n• 产出：23,592 条独立去重评论"),
            ],
        },
        {
            "num": "3",
            "title": "标注",
            "desc": "提取“特征—场\n景—情绪”\n三元证据",
            "sub_items": ["方面级情感分析 (ABSA)", "场景词识别"],
            "algos": [
                ("算法 3.1：两级转折词子句切分与偏移追踪", "按标点与转折连词 (but/however/although/\nwhile/yet) 切分子句，维护原文切片不变量：\nreview['text'][start:end] == clause"),
                ("算法 3.2：最小字符距离方面归属 + 近邻否定", "计算观点词到各维度锚词距离 d(a)=|p_w - p_a|，\n仅当唯一最近且 d(a*)<=70 字符时赋极性；\n检测前 3 个词元内否定词 (not/n't/never) 翻转极性"),
                ("算法 3.3：无星级污染兜底 + 二阶段质量归因", "无显式观点词严标 unknown；负面子句经\nTF-IDF + LogisticRegression 剥离硬件缺陷"),
                ("对应代码与产出", "• review_engine/core.py: clauses(), extract()\n• 产出：74,404 条子句三元证据 (Prec=86.9%)"),
            ],
        },
        {
            "num": "4",
            "title": "分歧",
            "desc": "比较正负比例与\n不同场景的差异",
            "sub_items": ["文本向量、PCA", "KMeans / DBSCAN", "冲突分数"],
            "algos": [
                ("算法 4.1：去锚词稀疏 TF-IDF + MiniBatchKMeans", "动态剔除当前维度锚词后构建 1-2 gram\nSublinear TF-IDF 向量，经 PCA 2D 降维与\nMiniBatchKMeans (k=5) 聚类 40 个细粒度子话题"),
                ("算法 4.2：评论级去重与 Wilson 95% 置信区间", "同一评论正负并存归为 mixed；计算拉普拉斯\n平滑好评率与 Wilson Score 95% 置信上下界"),
                ("算法 4.3：极化需求冲突分数 (Conflict Score)", "Conflict = 4*p*(1-p)*(1 - 1/(1 + N_pol/20))\n在 N>=20 门槛下量化正负博弈强度与争议度"),
                ("对应代码与产出", "• review_engine/core.py: wilson(), aggregate()\n• review_engine/aspect_topics.py\n• 产出：summary.csv & topics.csv"),
            ],
        },
        {
            "num": "5",
            "title": "呈现",
            "desc": "输出选择卡与\n可追溯证据片段",
            "sub_items": ["证据图谱", "RAG 检索", "可解释选择卡"],
            "algos": [
                ("算法 5.1：五类节点异构证据图谱构建", "构建 Product -> Aspect -> Scene -> Subtopic\n-> EvidenceClause 五层带权有向图 (87节点/105边)"),
                ("算法 5.2：双语映射 + 子线性 TF-IDF 余弦检索", "中文需求映射至维度/场景并扩展英文锚词，\n计算 query 与候选子句 TF-IDF 余弦相似度 Top-K"),
                ("算法 5.3：六重护栏受控 RAG + 折叠式选择卡", "支持本地确定性引擎与 DeepSeek API 双模生成，\n顶部直观呈现好评进度条，底部默认折叠原句"),
                ("对应代码与产出", "• review_engine/core.py: build_index(), retrieve()\n• agent.py & demo.py (Streamlit 交互系统)"),
            ],
        },
    ]

    x_start = 0.03
    col_w = 0.176
    gap = 0.015

    for idx, st_info in enumerate(steps):
        x = x_start + idx * (col_w + gap)
        # Top card replicating the user's original proposal card
        bg_ax.add_patch(
            FancyBboxPatch(
                (x, 0.635),
                col_w,
                0.205,
                boxstyle="round,pad=0.004,rounding_size=0.012",
                facecolor=BG_CARD,
                edgecolor=TEAL,
                linewidth=1.5,
            )
        )
        # Circle badge
        circle = mpatches.Circle((x + 0.024, 0.805), 0.015, facecolor=TEAL, edgecolor="none")
        bg_ax.add_patch(circle)
        fig.text(x + 0.024, 0.805, st_info["num"], fontsize=10.5, fontweight="bold", color="#FFFFFF", ha="center", va="center")
        fig.text(x + 0.048, 0.805, st_info["title"], fontsize=14, fontweight="bold", color=NAVY, va="center")
        fig.text(x + 0.016, 0.745, st_info["desc"], fontsize=9.8, color=SLATE, va="top", linespacing=1.35)

        # Sub-items pill strip (matching proposal keywords below the card)
        sub_text = "  |  ".join(st_info["sub_items"])
        bg_ax.add_patch(
            FancyBboxPatch(
                (x, 0.578),
                col_w,
                0.040,
                boxstyle="round,pad=0.002,rounding_size=0.008",
                facecolor=TEAL_LIGHT,
                edgecolor="#BFDBFE",
                linewidth=1.0,
            )
        )
        fig.text(x + col_w / 2, 0.598, sub_text, fontsize=8.3, fontweight="bold", color=NAVY_MID, ha="center", va="center")

        # Horizontal arrow between top cards
        if idx < len(steps) - 1:
            arrow_x = x + col_w + 0.002
            bg_ax.add_patch(
                FancyArrowPatch(
                    (arrow_x, 0.738),
                    (arrow_x + gap - 0.004, 0.738),
                    arrowstyle="->,head_width=5,head_length=5",
                    color=TEAL,
                    linewidth=2.0,
                )
            )

        # Downward connector from proposal card to concrete algorithm container
        bg_ax.add_patch(
            FancyArrowPatch(
                (x + col_w / 2, 0.574),
                (x + col_w / 2, 0.542),
                arrowstyle="->,head_width=4,head_length=4",
                color=NAVY_MID,
                linewidth=1.5,
            )
        )

        # Bottom container: Concrete Algorithms
        draw_card(
            bg_ax,
            x,
            0.065,
            col_w,
            0.472,
            title=f"步骤 {st_info['num']} 落地算法与数学模型",
            badge="V2 实装",
            header_color=NAVY if idx % 2 == 0 else NAVY_MID,
        )

        curr_y = 0.486
        n_boxes = len(st_info["algos"])
        for a_title, a_body in st_info["algos"]:
            is_code = a_title.startswith("对应代码")
            if n_boxes == 3:
                box_h = 0.115 if is_code else 0.128
                gap_y = 0.014
            else:
                box_h = 0.084 if is_code else 0.100
                gap_y = 0.008
            bg_ax.add_patch(
                FancyBboxPatch(
                    (x + 0.008, curr_y - box_h),
                    col_w - 0.016,
                    box_h,
                    boxstyle="round,pad=0.002,rounding_size=0.006",
                    facecolor="#F8FAFC" if not is_code else TEAL_LIGHT,
                    edgecolor="#CBD5E1" if not is_code else "#93C5FD",
                    linewidth=0.9,
                )
            )
            fig.text(
                x + 0.014,
                curr_y - 0.013,
                a_title,
                fontsize=8.0,
                fontweight="bold",
                color=TEAL if not is_code else NAVY,
                va="top",
            )
            fig.text(
                x + 0.014,
                curr_y - 0.031,
                a_body,
                fontsize=7.35,
                color=NAVY if is_code else SLATE,
                va="top",
                linespacing=1.24,
            )
            curr_y -= box_h + gap_y

    out_path = OUT_DIR / "fig07_method_5steps_algorithms.png"
    fig.savefig(out_path, dpi=220)
    plt.close(fig)
    return out_path


def main() -> None:
    setup_matplotlib()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading datasets...")
    raw_rows = [
        json.loads(line)
        for line in (ROOT / "data" / "raw" / "amazon_target_earbuds_reviews.jsonl").open(encoding="utf-8")
    ]
    raw_df = pd.DataFrame(raw_rows)
    ev_df = pd.read_csv(ROOT / "outputs" / "engine_v2" / "evidence.csv", keep_default_na=False)
    sum_df = pd.read_csv(ROOT / "outputs" / "engine_v2" / "summary.csv")
    top_df = pd.read_csv(ROOT / "outputs" / "aspect_topics_v2" / "topics.csv")
    feat_df = pd.read_csv(ROOT / "outputs" / "earbud_target_full" / "review_features.csv")

    generated = [
        generate_fig01_dataset_construction(raw_df),
        generate_fig02_dataset_eda_overview(raw_df, ev_df),
        generate_fig03_algorithm_workflow(),
        generate_fig04_conflict_and_topic_results(sum_df, top_df, feat_df),
        generate_fig05_frontend_prototype(),
        generate_fig07_method_5steps(),
    ]

    for path in generated:
        dest = ARTIFACT_DIR / path.name
        shutil.copy2(path, dest)
        print(f"Generated: {path} -> copied to {dest}")


if __name__ == "__main__":
    main()
