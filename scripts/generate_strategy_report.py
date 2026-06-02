"""Generate the project strategy report PDF from current backtest artifacts."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Iterable, Optional, Union

import pandas as pd
import yaml
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "量化投资策略报告.pdf"
METRICS_PATH = ROOT / "output" / "reports" / "总览_指标汇总.csv"
SCAN_PATH = ROOT / "output" / "reports" / "双均线_参数扫描.csv"
CONFIG_PATH = ROOT / "configs" / "demo.yaml"
FIGURE_DIR = ROOT / "output" / "figures"

NAVY = colors.HexColor("#1F2A44")
TEAL = colors.HexColor("#137C7A")
GOLD = colors.HexColor("#C98A18")
LIGHT_BLUE = colors.HexColor("#EAF3F8")
LIGHT_TEAL = colors.HexColor("#E8F6F4")
LIGHT_GOLD = colors.HexColor("#FFF5DF")
LIGHT_GRAY = colors.HexColor("#F5F7FA")
MID_GRAY = colors.HexColor("#D8DEE9")
DARK_GRAY = colors.HexColor("#3D4652")


def register_fonts() -> tuple[str, str]:
    """Return normal and bold font names that can render Chinese text."""
    candidates = [
        (Path(r"C:\Windows\Fonts\msyh.ttc"), Path(r"C:\Windows\Fonts\msyhbd.ttc")),
        (Path("/System/Library/Fonts/PingFang.ttc"), Path("/System/Library/Fonts/PingFang.ttc")),
        (Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")),
        (Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc"), Path("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc")),
    ]
    for regular, bold in candidates:
        if regular.exists():
            try:
                pdfmetrics.registerFont(TTFont("ReportSans", str(regular)))
                pdfmetrics.registerFont(TTFont("ReportSans-Bold", str(bold if bold.exists() else regular)))
                return "ReportSans", "ReportSans-Bold"
            except Exception:
                continue

    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    return "STSong-Light", "STSong-Light"


FONT, FONT_BOLD = register_fonts()


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=26,
            leading=34,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=10,
        ),
        "cover_subtitle": ParagraphStyle(
            "cover_subtitle",
            parent=base["Normal"],
            fontName=FONT,
            fontSize=12,
            leading=19,
            textColor=DARK_GRAY,
            alignment=TA_CENTER,
            spaceAfter=16,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=18,
            leading=24,
            textColor=NAVY,
            spaceBefore=4,
            spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=13,
            leading=18,
            textColor=TEAL,
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=9.5,
            leading=15,
            textColor=DARK_GRAY,
            spaceAfter=7,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8,
            leading=12,
            textColor=DARK_GRAY,
        ),
        "caption": ParagraphStyle(
            "caption",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8,
            leading=12,
            textColor=colors.HexColor("#657080"),
            alignment=TA_CENTER,
            spaceBefore=4,
            spaceAfter=8,
        ),
        "table": ParagraphStyle(
            "table",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=8,
            leading=10,
            textColor=DARK_GRAY,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=8,
            leading=10,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=9,
            leading=12,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "card_value": ParagraphStyle(
            "card_value",
            parent=base["BodyText"],
            fontName=FONT_BOLD,
            fontSize=16,
            leading=20,
            textColor=NAVY,
            alignment=TA_CENTER,
        ),
        "card_note": ParagraphStyle(
            "card_note",
            parent=base["BodyText"],
            fontName=FONT,
            fontSize=7.5,
            leading=10,
            textColor=DARK_GRAY,
            alignment=TA_CENTER,
        ),
    }


STYLES = make_styles()


def required_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing required report artifact: {path}")


def load_metrics() -> pd.DataFrame:
    required_file(METRICS_PATH)
    df = pd.read_csv(METRICS_PATH)
    order = {
        "双均线交叉": 1,
        "增强双均线": 2,
        "趋势过滤动量": 3,
        "12-1动量": 4,
        "动量低波多因子": 5,
        "风险平价": 6,
        "低波动": 7,
    }
    df["_order"] = df["策略"].map(order).fillna(99)
    return df.sort_values(["_order", "夏普比率"], ascending=[True, False]).drop(columns="_order")


def load_scan() -> pd.DataFrame:
    required_file(SCAN_PATH)
    df = pd.read_csv(SCAN_PATH)
    return df.sort_values("夏普比率", ascending=False).head(8)


def load_config() -> dict:
    required_file(CONFIG_PATH)
    with CONFIG_PATH.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def build_table(
    rows: list[list[Union[str, Paragraph]]],
    col_widths: list[float],
    *,
    align_right_from: int = 1,
    zebra: bool = True,
) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTNAME", (0, 1), (-1, -1), FONT),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("LEADING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    if align_right_from < len(rows[0]):
        style_cmds.append(("ALIGN", (align_right_from, 1), (-1, -1), "RIGHT"))
    if zebra:
        for row_idx in range(1, len(rows)):
            if row_idx % 2 == 0:
                style_cmds.append(("BACKGROUND", (0, row_idx), (-1, row_idx), LIGHT_GRAY))
    table.setStyle(TableStyle(style_cmds))
    return table


def metric_cards(metrics: pd.DataFrame) -> Table:
    sma = metrics.loc[metrics["策略"] == "双均线交叉"].iloc[0]
    enhanced = metrics.loc[metrics["策略"] == "增强双均线"].iloc[0]
    dd_improvement = abs(sma["最大回撤"]) - abs(enhanced["最大回撤"])
    vol_drop = sma["年化波动率"] - enhanced["年化波动率"]

    cards = [
        ("双均线 30/50", pct(sma["年化收益率"]), f"夏普 {num(sma['夏普比率'])}"),
        ("增强双均线", pct(enhanced["年化收益率"]), f"最大回撤 {pct(enhanced['最大回撤'])}"),
        ("回撤压缩", pct(dd_improvement), "相对普通双均线"),
        ("波动下降", pct(vol_drop), "更接近风控型体验"),
    ]
    rows = [
        [paragraph(title, STYLES["card_title"]) for title, _, _ in cards],
        [paragraph(value, STYLES["card_value"]) for _, value, _ in cards],
        [paragraph(note, STYLES["card_note"]) for _, _, note in cards],
    ]
    table = Table(rows, colWidths=[42 * mm] * 4, hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("BACKGROUND", (0, 1), (-1, 2), LIGHT_TEAL),
                ("GRID", (0, 0), (-1, -1), 0.7, colors.white),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def strategy_metrics_table(metrics: pd.DataFrame) -> Table:
    headers = ["策略", "年化收益", "夏普", "最大回撤", "年化波动", "胜率", "日均换手"]
    rows: list[list[Union[str, Paragraph]]] = [[paragraph(h, STYLES["table_header"]) for h in headers]]
    for _, row in metrics.iterrows():
        rows.append(
            [
                paragraph(str(row["策略"]), STYLES["table"]),
                pct(row["年化收益率"]),
                num(row["夏普比率"]),
                pct(row["最大回撤"]),
                pct(row["年化波动率"]),
                pct(row["胜率"]),
                pct(row["平均每日换手率"], 3),
            ]
        )
    return build_table(rows, [34 * mm, 24 * mm, 19 * mm, 24 * mm, 24 * mm, 21 * mm, 24 * mm])


def scan_table(scan: pd.DataFrame) -> Table:
    headers = ["排名", "短/长均线", "年化收益", "夏普", "最大回撤", "卡玛", "日均换手"]
    rows: list[list[Union[str, Paragraph]]] = [[paragraph(h, STYLES["table_header"]) for h in headers]]
    for rank, (_, row) in enumerate(scan.iterrows(), start=1):
        rows.append(
            [
                str(rank),
                f"{int(row['短均线'])}/{int(row['长均线'])}",
                pct(row["年化收益率"]),
                num(row["夏普比率"]),
                pct(row["最大回撤"]),
                num(row["卡玛比率"]),
                pct(row["平均每日换手率"], 3),
            ]
        )
    return build_table(rows, [15 * mm, 26 * mm, 26 * mm, 20 * mm, 25 * mm, 20 * mm, 26 * mm])


def comparison_table(metrics: pd.DataFrame) -> Table:
    sma = metrics.loc[metrics["策略"] == "双均线交叉"].iloc[0]
    enhanced = metrics.loc[metrics["策略"] == "增强双均线"].iloc[0]
    rows: list[list[Union[str, Paragraph]]] = [
        [paragraph("维度", STYLES["table_header"]), paragraph("普通双均线 30/50", STYLES["table_header"]), paragraph("增强双均线", STYLES["table_header"])],
        ["核心逻辑", "短均线上穿长均线后持有", "突破确认 + 趋势过滤 + 止损 + 波动率仓位"],
        ["年化收益", pct(sma["年化收益率"]), pct(enhanced["年化收益率"])],
        ["夏普比率", num(sma["夏普比率"]), num(enhanced["夏普比率"])],
        ["最大回撤", pct(sma["最大回撤"]), pct(enhanced["最大回撤"])],
        ["适用定位", "进攻型趋势跟随基线", "更适合做可解释的风控样板"],
    ]
    return build_table(rows, [32 * mm, 70 * mm, 70 * mm], align_right_from=1)


def bullet_list(items: Iterable[str]) -> ListFlowable:
    return ListFlowable(
        [ListItem(paragraph(item, STYLES["body"]), bulletColor=TEAL) for item in items],
        bulletType="bullet",
        leftIndent=16,
        bulletFontName=FONT_BOLD,
        bulletFontSize=8,
    )


def scaled_image(path: Path, max_width: float, max_height: float) -> Optional[Image]:
    if not path.exists():
        return None
    with PILImage.open(path) as img:
        width, height = img.size
    scale = min(max_width / width, max_height / height)
    return Image(str(path), width=width * scale, height=height * scale)


def image_block(path: Path, caption: str, max_width: float = 172 * mm, max_height: float = 82 * mm):
    image = scaled_image(path, max_width, max_height)
    if image is None:
        return paragraph(f"图表缺失：{path.name}", STYLES["small"])
    return KeepTogether([image, paragraph(caption, STYLES["caption"])])


def chart_grid(items: list[tuple[Path, str]]) -> Table:
    cells = []
    for path, caption in items:
        img = scaled_image(path, 82 * mm, 60 * mm)
        if img is None:
            cells.append(paragraph(f"图表缺失：{path.name}", STYLES["small"]))
        else:
            cell = Table(
                [[img], [paragraph(caption, STYLES["caption"])]],
                colWidths=[82 * mm],
                hAlign="CENTER",
            )
            cell.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ]
                )
            )
            cells.append(cell)
    rows = [cells[i : i + 2] for i in range(0, len(cells), 2)]
    table = Table(rows, colWidths=[86 * mm, 86 * mm], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def on_page(canvas, doc):
    canvas.saveState()
    width, height = A4
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(colors.HexColor("#7A8491"))
    canvas.drawString(doc.leftMargin, 12 * mm, "Quant Backtest Portfolio AkShare")
    canvas.drawRightString(width - doc.rightMargin, 12 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(MID_GRAY)
    canvas.line(doc.leftMargin, 17 * mm, width - doc.rightMargin, 17 * mm)
    canvas.restoreState()


def cover_banner() -> Optional[Image]:
    path = ROOT / "docs" / "assets" / "readme-cover.png"
    return scaled_image(path, 172 * mm, 62 * mm)


def build_story(metrics: pd.DataFrame, scan: pd.DataFrame, config: dict) -> list:
    assets = "、".join(config.get("assets", []))
    start = config.get("start", "2015-01-01")
    baseline = config.get("baseline", "")
    cost = config.get("cost_bps", 0)
    today = date.today().isoformat()

    story: list = []
    banner = cover_banner()
    if banner:
        story.extend([banner, Spacer(1, 7 * mm)])
    story.extend(
        [
            paragraph("量化投资策略报告", STYLES["cover_title"]),
            paragraph(
                "基于 Python、pandas 与 AkShare 的 A 股策略研究样板：从双均线交叉出发，加入参数扫描、趋势确认、止损与波动率仓位控制。",
                STYLES["cover_subtitle"],
            ),
            metric_cards(metrics),
            Spacer(1, 8 * mm),
            paragraph(
                f"报告日期：{today}<br/>示例资产池：{assets}<br/>基准资产：{baseline} ｜ 回测起点：{start} ｜ 单边交易成本：{cost} bps",
                STYLES["cover_subtitle"],
            ),
            paragraph(
                "本报告用于展示项目能力与研究口径，不构成任何投资建议。历史回测结果不代表未来收益。",
                STYLES["small"],
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("1. 当前策略总览", STYLES["h1"]),
            paragraph(
                "项目当前覆盖趋势跟随、动量轮动、低波组合和风险平价等策略。核心展示重点是双均线交叉的工程化升级：保留简单可解释的入门逻辑，同时增加可复现的参数扫描和多层风控。",
                STYLES["body"],
            ),
            strategy_metrics_table(metrics),
            Spacer(1, 6 * mm),
            paragraph("结果读法", STYLES["h2"]),
            bullet_list(
                [
                    "双均线 30/50 是当前收益和夏普较强的进攻型基线，适合展示趋势跟随的上限。",
                    "增强双均线牺牲部分年化收益，把最大回撤从普通双均线的 -38.10% 压到 -20.32%，更像可长期迭代的策略雏形。",
                    "最大回撤保留负号，因为它表示净值从历史高点向下跌落的比例，负号能直观提醒这是风险而不是收益。",
                    "动量和风险平价策略提供横向对照，让项目不只是一条单策略曲线。",
                ]
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("2. 增强双均线：从入门策略到可研究策略", STYLES["h1"]),
            paragraph(
                "普通双均线的优点是简单、直观、容易复现；缺点也明显：震荡行情里容易反复交易，遇到假突破时回撤较深。增强版围绕“少做噪音、多做趋势、错误尽早退出”做升级。",
                STYLES["body"],
            ),
            comparison_table(metrics),
            Spacer(1, 5 * mm),
            paragraph("增强模块", STYLES["h2"]),
            bullet_list(
                [
                    "突破阈值带：短均线需要超过长均线一定比例，过滤贴线震荡。",
                    "连续确认：信号连续成立若干天后才进场，减少单日脉冲。",
                    "长均线趋势过滤：长均线走平或下行时降低做多冲动。",
                    "固定止损与移动止损：限制错误信号持续放大。",
                    "目标波动率仓位：波动升高时自动降仓，让净值体验更稳定。",
                ]
            ),
            Spacer(1, 4 * mm),
            image_block(FIGURE_DIR / "增强双均线_仓位.png", "增强双均线仓位：持仓不再只有 0/1，而是随波动率目标动态调整。", 172 * mm, 80 * mm),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("3. 参数扫描：让默认参数有证据", STYLES["h1"]),
            paragraph(
                "报告使用同一资产池扫描短均线与长均线组合，并按夏普比率排序。当前默认的 30/50 并非随手填写，而是来自示例扫描结果中综合表现较强的组合。",
                STYLES["body"],
            ),
            scan_table(scan),
            Spacer(1, 6 * mm),
            paragraph("下一步可继续升级", STYLES["h2"]),
            bullet_list(
                [
                    "增加 walk-forward 走前验证，避免只在全样本里选参数。",
                    "把参数扫描扩展为热力图，直观看到参数稳定区域。",
                    "加入训练期/验证期/测试期拆分，让策略展示更接近研究生产流程。",
                ]
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("4. 核心图表", STYLES["h1"]),
            paragraph(
                "下面的图表来自 `output/figures/`，由项目脚本自动生成。净值图用于观察收益路径，回撤图用于观察风险暴露，仓位图用于解释策略如何行动。",
                STYLES["body"],
            ),
            chart_grid(
                [
                    (FIGURE_DIR / "sma_净值.png", "普通双均线净值"),
                    (FIGURE_DIR / "sma_回撤.png", "普通双均线回撤"),
                    (FIGURE_DIR / "增强双均线_净值.png", "增强双均线净值"),
                    (FIGURE_DIR / "增强双均线_回撤.png", "增强双均线回撤"),
                ]
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("5. 组合策略横向观察", STYLES["h1"]),
            paragraph(
                "为了让项目有扩展空间，仓库同时保留了动量、低波、多因子和风险平价策略。它们的定位不是替代增强双均线，而是给研究者提供不同风格的组合样板。",
                STYLES["body"],
            ),
            chart_grid(
                [
                    (FIGURE_DIR / "动量_净值.png", "12-1 动量净值"),
                    (FIGURE_DIR / "多因子_净值.png", "动量低波多因子净值"),
                    (FIGURE_DIR / "风险平价_净值.png", "风险平价净值"),
                    (FIGURE_DIR / "增强双均线_月度收益热力图.png", "增强双均线月度收益热力图"),
                ]
            ),
            PageBreak(),
        ]
    )

    story.extend(
        [
            paragraph("6. 复现方式与项目价值", STYLES["h1"]),
            paragraph("最小复现命令", STYLES["h2"]),
            paragraph(
                "安装依赖后运行 `python main.py` 可生成 CSV 指标与图表；运行 `python scripts/generate_strategy_report.py` 可用最新产物重新生成本 PDF。",
                STYLES["body"],
            ),
            paragraph("适合继续建设的方向", STYLES["h2"]),
            bullet_list(
                [
                    "把增强双均线扩展到指数 ETF 池，减少单只股票样本偶然性。",
                    "加入 benchmark-relative 指标，如信息比率、跟踪误差和超额回撤。",
                    "做 Streamlit 面板，让用户能在线切换资产池、参数和策略。",
                    "增加研究笔记与教程，把项目从代码仓库包装成可学习的量化策略模板。",
                ]
            ),
            paragraph("免责声明", STYLES["h2"]),
            paragraph(
                "本项目和本报告仅用于量化研究、编程学习和开源项目展示，不构成任何投资建议或收益承诺。策略表现依赖数据口径、样本区间、交易成本、调仓频率和实现细节；历史回测结果不能代表未来收益。",
                STYLES["body"],
            ),
        ]
    )
    return story


def build_pdf(output_path: Path) -> None:
    metrics = load_metrics()
    scan = load_scan()
    config = load_config()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=22 * mm,
        title="量化投资策略报告",
        author="Quant Backtest Portfolio AkShare",
    )
    story = build_story(metrics, scan, config)
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate 量化投资策略报告.pdf from output artifacts.")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORT_PATH,
        help="Target PDF path. Defaults to the repository root report file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    build_pdf(output)
    print(f"Generated {output}")


if __name__ == "__main__":
    main()
