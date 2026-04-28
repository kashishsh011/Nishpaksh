"""
backend/report/pdf_builder.py
Nishpaksh — Enhanced PDF Builder
Adds: executive summary table, hire-rate bar charts, colour-coded metric
      scorecards, before/after mitigation visual, deduplication of findings.
"""

from __future__ import annotations

import io
from datetime import date
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand palette ─────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#1B2A6B")
INDIGO    = colors.HexColor("#3D4EAC")
TEAL      = colors.HexColor("#0D9488")
AMBER     = colors.HexColor("#D97706")
CORAL     = colors.HexColor("#E11D48")
SAND      = colors.HexColor("#F5F0E8")
LIGHT_BG  = colors.HexColor("#F8F7F4")
MID_GREY  = colors.HexColor("#9CA3AF")
DARK_TEXT = colors.HexColor("#1F2937")
WHITE     = colors.white

# Matplotlib hex equivalents
M_TEAL   = "#0D9488"
M_AMBER  = "#D97706"
M_CORAL  = "#E11D48"
M_NAVY   = "#1B2A6B"
M_SAND   = "#F5F0E8"
M_GREY   = "#E5E7EB"

W, H = A4


# ── Styles ────────────────────────────────────────────────────────────────────
def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="Helvetica-Bold",
            fontSize=28, textColor=WHITE, leading=34, alignment=TA_CENTER,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="Helvetica",
            fontSize=13, textColor=colors.HexColor("#CBD5E1"),
            leading=18, alignment=TA_CENTER,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="Helvetica",
            fontSize=10, textColor=colors.HexColor("#94A3B8"),
            leading=14, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", fontName="Helvetica-Bold",
            fontSize=16, textColor=NAVY, leading=22, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2", fontName="Helvetica-Bold",
            fontSize=12, textColor=INDIGO, leading=16, spaceBefore=8, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica",
            fontSize=9.5, textColor=DARK_TEXT, leading=15, spaceAfter=6,
        ),
        "caption": ParagraphStyle(
            "caption", fontName="Helvetica-Oblique",
            fontSize=8, textColor=MID_GREY, leading=11, alignment=TA_CENTER,
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica-Bold",
            fontSize=8, textColor=DARK_TEXT, leading=11,
        ),
        "tag_risk": ParagraphStyle(
            "tag_risk", fontName="Helvetica-Bold",
            fontSize=8, textColor=WHITE, leading=10, alignment=TA_CENTER,
        ),
        "tag_ok": ParagraphStyle(
            "tag_ok", fontName="Helvetica-Bold",
            fontSize=8, textColor=WHITE, leading=10, alignment=TA_CENTER,
        ),
        "footer": ParagraphStyle(
            "footer", fontName="Helvetica",
            fontSize=7.5, textColor=MID_GREY, alignment=TA_CENTER,
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _hr(colour=INDIGO, thickness=0.5) -> HRFlowable:
    return HRFlowable(width="100%", thickness=thickness, color=colour, spaceAfter=8)


def _spacer(h: float = 0.4) -> Spacer:
    return Spacer(1, h * cm)


def _status_color(status: str) -> colors.Color:
    s = status.upper()
    if "RISK" in s:     return CORAL
    if "REVIEW" in s:   return AMBER
    return TEAL


def _severity_color(sev: str) -> colors.Color:
    s = sev.upper()
    if s == "HIGH":    return CORAL
    if s == "MEDIUM":  return AMBER
    return TEAL


def _buf_to_image(buf: io.BytesIO, width: float, height: float) -> Image:
    buf.seek(0)
    img = Image(buf, width=width, height=height)
    return img


def _dedupe_findings(findings: list[dict]) -> list[dict]:
    """Remove duplicate proxy findings (same column + mechanism)."""
    seen: set[tuple] = set()
    out: list[dict] = []
    for f in findings:
        key = (f.get("column", ""), f.get("mechanism", ""), f.get("affected_group", ""))
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


# ── Chart generators ──────────────────────────────────────────────────────────
def _hire_rate_chart(findings: list[dict], overall_rate: float) -> io.BytesIO:
    """Horizontal bar chart: affected vs comparison group per finding."""
    n = len(findings)
    fig_h = max(2.5, n * 1.4)
    fig, ax = plt.subplots(figsize=(6.5, fig_h))
    fig.patch.set_facecolor(M_SAND)
    ax.set_facecolor(M_SAND)

    y_pos = np.arange(n)
    affected_rates  = [f.get("affected_rate",  0) * 100 for f in findings]
    comparison_rates = [f.get("comparison_rate", 0) * 100 for f in findings]
    labels = [
        f"{f.get('column','')}\n({f.get('affected_group','affected')})"
        for f in findings
    ]

    bar_h = 0.32
    bars_cmp = ax.barh(y_pos + bar_h/2, comparison_rates, bar_h,
                       color=M_TEAL, alpha=0.85, label="Comparison group")
    bars_aff = ax.barh(y_pos - bar_h/2, affected_rates,   bar_h,
                       color=M_CORAL, alpha=0.85, label="Affected group")

    # Value labels
    for bar in bars_cmp:
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height()/2,
                f"{bar.get_width():.1f}%", va="center", fontsize=7.5,
                color=M_NAVY, fontweight="bold")
    for bar in bars_aff:
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height()/2,
                f"{bar.get_width():.1f}%", va="center", fontsize=7.5,
                color=M_CORAL, fontweight="bold")

    # Overall average line
    ax.axvline(overall_rate * 100, color=M_NAVY, linewidth=1.2,
               linestyle="--", alpha=0.6, label=f"Overall avg ({overall_rate*100:.1f}%)")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8, color=M_NAVY)
    ax.set_xlabel("Hire Rate (%)", fontsize=8, color=M_NAVY)
    ax.set_xlim(0, 105)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="x", colors=M_NAVY, labelsize=7.5)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.set_tick_params(labelsize=7.5)
    ax.legend(fontsize=7.5, loc="lower right",
              facecolor=M_SAND, edgecolor="none")
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=M_SAND)
    plt.close(fig)
    return buf


def _mitigation_chart(metrics_before: dict, metrics_after: dict) -> io.BytesIO:
    """Grouped bar chart: before vs after mitigation for each metric."""
    metric_keys   = ["DPD", "EOD", "DIR"]
    metric_labels = ["Demographic\nParity Diff", "Equalized\nOdds Diff", "Disparate\nImpact Ratio"]
    thresholds    = [0.10, 0.10, 0.80]
    # For DIR higher is better; for DPD/EOD lower is better
    higher_better = [False, False, True]

    before_vals = [metrics_before.get(k, 0) for k in metric_keys]
    after_vals  = [metrics_after.get(k, 0)  for k in metric_keys]

    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.6))
    fig.patch.set_facecolor(M_SAND)

    for i, ax in enumerate(axes):
        ax.set_facecolor(M_SAND)
        vals   = [before_vals[i], after_vals[i]]
        thresh = thresholds[i]

        def _bar_color(v, hb):
            if hb:   return M_TEAL if v >= thresh else M_CORAL
            else:    return M_TEAL if v <= thresh else M_CORAL

        bar_colors = [_bar_color(vals[0], higher_better[i]),
                      _bar_color(vals[1], higher_better[i])]

        bars = ax.bar(["Before", "After"], vals, color=bar_colors,
                      alpha=0.85, width=0.5)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                    f"{v:.3f}", ha="center", fontsize=7.5,
                    color=M_NAVY, fontweight="bold")

        # Threshold line
        ax.axhline(thresh, color=M_AMBER, linewidth=1,
                   linestyle="--", alpha=0.8, label=f"Threshold {thresh}")
        ax.set_title(metric_labels[i], fontsize=7.5, color=M_NAVY,
                     fontweight="bold", pad=4)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="both", labelsize=7, colors=M_NAVY, length=0)
        ax.set_ylim(0, max(max(vals) * 1.35, thresh * 1.35))

    plt.suptitle("Bias Metrics: Before vs After Mitigation",
                 fontsize=8.5, color=M_NAVY, fontweight="bold", y=1.02)
    plt.tight_layout(pad=0.5)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=M_SAND)
    plt.close(fig)
    return buf


# ── Cover page ────────────────────────────────────────────────────────────────
def _cover_page(canvas, doc):
    canvas.saveState()
    # Navy gradient header band
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 7*cm, W, 7*cm, fill=1, stroke=0)
    # Accent stripe
    canvas.setFillColor(TEAL)
    canvas.rect(0, H - 7*cm, W, 0.35*cm, fill=1, stroke=0)
    # Footer band
    canvas.setFillColor(colors.HexColor("#1B2A6B"))
    canvas.rect(0, 0, W, 1.6*cm, fill=1, stroke=0)
    canvas.restoreState()


# ── Main builder ──────────────────────────────────────────────────────────────
def generate_pdf(
    company_name: str,
    findings: list[dict],
    metrics: dict[str, Any],
    narrative: list[dict],
    checklist: list[dict],
    overall_hire_rate: float = 0.0,
) -> bytes:
    """
    Build and return the full audit PDF as bytes.

    findings  — list of proxy finding dicts from proxy_detector
    metrics   — dict with keys: before (dict), after (dict), accuracy (float)
    narrative — list of {title, content} dicts from narrative_builder
    checklist — list of {article, description, status} dicts
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=f"Nishpaksh Audit — {company_name}",
        author="Nishpaksh AI Audit Platform",
    )
    S = _styles()
    story: list = []

    # Deduplicate findings
    findings = _dedupe_findings(findings)

    audit_date = date.today().strftime("%d %B %Y")

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 5.2*cm))   # space under navy band
    story.append(Paragraph("NISHPAKSH", S["cover_title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("Hiring Bias Audit Report", S["cover_sub"]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"{company_name} &nbsp;·&nbsp; {audit_date}", S["cover_meta"]
    ))
    story.append(Spacer(1, 1*cm))
    story.append(_hr(TEAL, 1))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Plain-language findings aligned to India's DPDP Act and "
        "Articles 14, 15, and 16 of the Constitution.",
        S["cover_sub"],
    ))
    story.append(PageBreak())

    # ── Executive Summary Table ───────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", S["h1"]))
    story.append(_hr())
    story.append(_spacer(0.3))

    # Risk badge helper
    def _badge(status: str) -> Table:
        col = _status_color(status)
        t = Table([[Paragraph(status, S["tag_risk"])]], colWidths=[2.8*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), col),
            ("ROUNDEDCORNERS", [4]),
            ("TOPPADDING",    (0,0), (-1,-1), 3),
            ("BOTTOMPADDING", (0,0), (-1,-1), 3),
            ("LEFTPADDING",   (0,0), (-1,-1), 4),
            ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ]))
        return t

    # Summary table data
    sum_header = [
        Paragraph("Proxy Type", S["label"]),
        Paragraph("Groups Compared", S["label"]),
        Paragraph("Affected Rate", S["label"]),
        Paragraph("Comparison Rate", S["label"]),
        Paragraph("Disparity", S["label"]),
        Paragraph("Status", S["label"]),
    ]
    sum_rows = [sum_header]
    for f in findings:
        aff_r = f.get("affected_rate", 0)
        cmp_r = f.get("comparison_rate", 0)
        ratio = f.get("disparity_ratio", (cmp_r / aff_r) if aff_r else 0)
        sev   = f.get("severity", "MEDIUM").upper()
        status_str = "AT RISK" if sev == "HIGH" else ("REVIEW" if sev == "MEDIUM" else "OK")
        proxy_type = f.get("proxy_type", f.get("type", "")).title()
        sum_rows.append([
            Paragraph(proxy_type, S["body"]),
            Paragraph(
                f"{f.get('affected_group','—')} vs {f.get('comparison_group','—')}",
                S["body"],
            ),
            Paragraph(f"{aff_r*100:.1f}%", S["body"]),
            Paragraph(f"{cmp_r*100:.1f}%", S["body"]),
            Paragraph(f"{ratio:.2f}×", S["body"]),
            _badge(status_str),
        ])

    col_w = [2.8*cm, 4.5*cm, 2.2*cm, 2.5*cm, 1.8*cm, 2.4*cm]
    sum_table = Table(sum_rows, colWidths=col_w, repeatRows=1)
    sum_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0),  8),
        ("BOTTOMPADDING", (0,0), (-1,0),  6),
        ("TOPPADDING",    (0,0), (-1,0),  6),
        # Body
        ("FONTSIZE",      (0,1), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ("TOPPADDING",    (0,1), (-1,-1), 5),
        ("BOTTOMPADDING", (0,1), (-1,-1), 5),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        # Grid
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(sum_table)
    story.append(_spacer(0.6))

    # ── Hire Rate Chart ───────────────────────────────────────────────────────
    if findings:
        story.append(Paragraph("Hire Rate Comparison by Proxy Group", S["h2"]))
        chart_buf = _hire_rate_chart(findings, overall_hire_rate)
        chart_img = _buf_to_image(chart_buf, width=15.5*cm, height=max(5*cm, len(findings)*2.8*cm))
        story.append(chart_img)
        story.append(Paragraph(
            "Red bars = affected group · Teal bars = comparison group · "
            "Dashed line = overall hire rate average",
            S["caption"],
        ))
        story.append(_spacer(0.5))

    # ── Narrative sections ────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Detailed Findings & Legal Analysis", S["h1"]))
    story.append(_hr())
    story.append(_spacer(0.3))

    for section in narrative:
        title   = section.get("title", "")
        content = section.get("content", "")
        if title:
            story.append(Paragraph(title, S["h2"]))
        if content:
            for para in content.split("\n\n"):
                para = para.strip()
                if para:
                    story.append(Paragraph(para, S["body"]))
        story.append(_spacer(0.3))

    # ── Proxy Finding Cards ───────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Proxy Discrimination Findings", S["h1"]))
    story.append(_hr())
    story.append(_spacer(0.3))

    for f in findings:
        sev     = f.get("severity", "MEDIUM").upper()
        sev_col = _severity_color(sev)
        col     = f.get("column", "—")
        ptype   = f.get("proxy_type", f.get("type", "—")).title()
        mech    = f.get("mechanism", "—")
        aff_g   = f.get("affected_group", "—")
        cmp_g   = f.get("comparison_group", "—")
        aff_r   = f.get("affected_rate", 0)
        cmp_r   = f.get("comparison_rate", 0)
        ratio   = f.get("disparity_ratio", (cmp_r / aff_r) if aff_r else 0)
        n       = f.get("sample_size", "—")
        note    = f.get("legal_note", "")

        card_data = [
            # Row 0: column + severity badge
            [
                Paragraph(f"<b>Column:</b> {col} &nbsp;|&nbsp; <b>Type:</b> {ptype} &nbsp;|&nbsp; <b>Mechanism:</b> {mech}", S["body"]),
                Paragraph(sev, S["tag_risk"]),
            ],
            # Row 1: stats
            [
                Paragraph(
                    f"Affected: <b>{aff_g}</b> ({aff_r*100:.1f}% hire rate) &nbsp;&nbsp; "
                    f"Comparison: <b>{cmp_g}</b> ({cmp_r*100:.1f}% hire rate) &nbsp;&nbsp; "
                    f"Disparity: <b>{ratio:.2f}&times;</b> &nbsp;&nbsp; n={n}",
                    S["body"],
                ),
                "",
            ],
        ]
        if note:
            card_data.append([Paragraph(f"<i>{note}</i>", S["body"]), ""])

        card = Table(card_data, colWidths=[13.5*cm, 2.5*cm])
        card.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LIGHT_BG),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LINEABOVE",     (0,0), (-1,0),  3, sev_col),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",         (1,0), (1,0),   "RIGHT"),
            ("BACKGROUND",    (1,0), (1,0),   sev_col),
            ("SPAN",          (0,1), (-1,1)),
            *([("SPAN", (0,2), (-1,2))] if note else []),
        ]))
        story.append(card)
        story.append(_spacer(0.4))

    # ── Bias Metrics ──────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Bias Metrics (Fairlearn)", S["h1"]))
    story.append(_hr())
    story.append(_spacer(0.3))

    before = metrics.get("before", {})
    after  = metrics.get("after",  {})
    acc    = metrics.get("accuracy", None)

    # Metrics table
    thresholds_map = {"DPD": "< 0.10", "EOD": "< 0.10", "DIR": "> 0.80"}
    metric_full    = {"DPD": "Demographic Parity Difference",
                      "EOD": "Equalized Odds Difference",
                      "DIR": "Disparate Impact Ratio"}

    def _met_status(key, val):
        if key == "DIR": return "PASS" if val >= 0.80 else "FAIL"
        return "PASS" if val <= 0.10 else "FAIL"

    met_header = [
        Paragraph("Metric", S["label"]),
        Paragraph("Before Mitigation", S["label"]),
        Paragraph("After Mitigation", S["label"]),
        Paragraph("Threshold", S["label"]),
        Paragraph("Status", S["label"]),
    ]
    met_rows = [met_header]
    for key, full in metric_full.items():
        bv = before.get(key, 0)
        av = after.get(key, 0)
        st = _met_status(key, av)
        met_rows.append([
            Paragraph(full, S["body"]),
            Paragraph(f"{bv:.3f}", S["body"]),
            Paragraph(f"{av:.3f}", S["body"]),
            Paragraph(thresholds_map[key], S["body"]),
            _badge("PASS" if st == "PASS" else "AT RISK"),
        ])
    if acc is not None:
        met_rows.append([
            Paragraph("Model Accuracy", S["body"]),
            Paragraph(f"{acc:.3f}", S["body"]),
            Paragraph("—", S["body"]),
            Paragraph("—", S["body"]),
            Paragraph("", S["body"]),
        ])

    met_table = Table(met_rows, colWidths=[5.5*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm], repeatRows=1)
    met_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#E5E7EB")),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(met_table)
    story.append(_spacer(0.6))

    # Before/After mitigation chart
    if before and after:
        story.append(Paragraph("Before vs After Mitigation — Visual Comparison", S["h2"]))
        mit_buf = _mitigation_chart(before, after)
        mit_img = _buf_to_image(mit_buf, width=15.5*cm, height=6*cm)
        story.append(mit_img)
        story.append(Paragraph(
            "Teal bars = within legal threshold · Red bars = outside threshold · "
            "Amber dashed line = legal threshold",
            S["caption"],
        ))
        story.append(_spacer(0.5))

    # ── DPDP Checklist ────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("DPDP Act & Constitutional Compliance Checklist", S["h1"]))
    story.append(_hr())
    story.append(_spacer(0.3))

    for item in checklist:
        article = item.get("article", "")
        desc    = item.get("description", "")
        status  = item.get("status", "COMPLIANT")
        col     = _status_color(status)

        row_data = [[
            Paragraph(f"<b>{article}</b><br/><font size='8' color='#6B7280'>{desc}</font>", S["body"]),
            _badge(status),
        ]]
        row_table = Table(row_data, colWidths=[13.5*cm, 2.5*cm])
        row_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), LIGHT_BG),
            ("LINEABOVE",     (0,0), (-1,0),  2.5, col),
            ("TOPPADDING",    (0,0), (-1,-1), 7),
            ("BOTTOMPADDING", (0,0), (-1,-1), 7),
            ("LEFTPADDING",   (0,0), (-1,-1), 10),
            ("RIGHTPADDING",  (0,0), (-1,-1), 8),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ("ALIGN",         (1,0), (1,0),   "RIGHT"),
        ]))
        story.append(row_table)
        story.append(_spacer(0.25))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(_spacer(0.8))
    story.append(_hr(MID_GREY, 0.3))
    story.append(Paragraph(
        f"Generated by Nishpaksh AI Audit Platform · {audit_date} · Confidential — "
        "Data processed in-memory and not retained after report generation.",
        S["footer"],
    ))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_cover_page, onLaterPages=_later_pages)
    return buf.getvalue()


def _later_pages(canvas, doc):
    """Thin navy top bar + page number on all pages after cover."""
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, H - 1.1*cm, W, 1.1*cm, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.rect(0, H - 1.1*cm, W, 0.2*cm, fill=1, stroke=0)

    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(WHITE)
    canvas.drawString(2*cm, H - 0.75*cm, "NISHPAKSH  ·  Hiring Bias Audit Report")
    canvas.drawRightString(W - 2*cm, H - 0.75*cm, f"Page {doc.page}")

    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, 0.8*cm, fill=1, stroke=0)
    canvas.restoreState()