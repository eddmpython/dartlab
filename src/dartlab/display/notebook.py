"""노트북(Jupyter/Marimo) HTML 렌더링."""

from __future__ import annotations

import re
from typing import Any

import polars as pl

from dartlab.display._detect import hasGreatTables, hasItables

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")

# ── 색상 ──

_GREEN = "#16a34a"
_RED = "#dc2626"
_GRAY = "#9ca3af"


def _periodColumns(df: pl.DataFrame) -> list[str]:
    """기간 컬럼 추출 (최신 먼저)."""
    cols = [c for c in df.columns if _PERIOD_RE.match(c)]
    return sorted(cols, reverse=True)


def _labelColumn(df: pl.DataFrame) -> str | None:
    """계정명 컬럼 찾기."""
    for candidate in ("계정명", "label", "account_nm", "topic"):
        if candidate in df.columns:
            return candidate
    return None


# ── Great Tables ──


def htmlFinance(df: pl.DataFrame, *, topic: str = "") -> Any:
    """재무 DataFrame → Great Tables HTML."""
    if not hasGreatTables():
        return _htmlFinanceFallback(df, topic=topic)

    from great_tables import GT, loc, style

    periodCols = _periodColumns(df)
    labelCol = _labelColumn(df)

    # 표시 컬럼만 선택
    showCols = []
    if labelCol:
        showCols.append(labelCol)
    showCols.extend(periodCols)
    display = df.select(showCols)

    gt = GT(display)

    if topic:
        gt = gt.tab_header(title=topic)

    # 숫자 포맷: 천단위 콤마
    for col in periodCols:
        dtype = df.schema.get(col)
        if dtype and dtype.is_float():
            gt = gt.fmt_number(columns=col, decimals=0, use_seps=True)
        elif dtype and dtype.is_integer():
            gt = gt.fmt_integer(columns=col, use_seps=True)

    # YoY 색상: 양수 green, 음수 red
    for i, col in enumerate(periodCols):
        if i + 1 >= len(periodCols):
            break
        prevCol = periodCols[i + 1]
        try:
            gt = gt.tab_style(
                style=style.text(color=_GREEN),
                locations=loc.body(columns=col, rows=pl.col(col) > pl.col(prevCol)),
            )
            gt = gt.tab_style(
                style=style.text(color=_RED),
                locations=loc.body(columns=col, rows=pl.col(col) < pl.col(prevCol)),
            )
        except (TypeError, ValueError):
            pass

    return gt


def _htmlFinanceFallback(df: pl.DataFrame, *, topic: str = "") -> str:
    """Great Tables 없을 때 기본 HTML 테이블."""
    periodCols = _periodColumns(df)
    labelCol = _labelColumn(df)

    rows: list[str] = []
    # 헤더
    headers = []
    if labelCol:
        headers.append(f"<th style='text-align:left;padding:4px 8px'>{labelCol}</th>")
    for col in periodCols:
        headers.append(f"<th style='text-align:right;padding:4px 8px'>{col}</th>")
    rows.append(f"<tr>{''.join(headers)}</tr>")

    # 데이터
    for row in df.iter_rows(named=True):
        cells = []
        if labelCol:
            cells.append(f"<td style='padding:4px 8px;font-weight:bold'>{row.get(labelCol, '')}</td>")
        for i, col in enumerate(periodCols):
            val = row.get(col)
            if val is None:
                cells.append("<td style='text-align:right;padding:4px 8px;color:#9ca3af'>-</td>")
                continue
            if isinstance(val, str):
                cells.append(f"<td style='text-align:right;padding:4px 8px'>{val}</td>")
                continue

            formatted = f"{val:,.0f}" if isinstance(val, (int, float)) else str(val)

            # YoY 색상
            color = ""
            if i + 1 < len(periodCols):
                prevVal = row.get(periodCols[i + 1])
                if isinstance(val, (int, float)) and isinstance(prevVal, (int, float)) and prevVal != 0:
                    if val > prevVal:
                        color = f"color:{_GREEN}"
                    elif val < prevVal:
                        color = f"color:{_RED}"

            styleAttr = f"text-align:right;padding:4px 8px;{color}"
            cells.append(f"<td style='{styleAttr}'>{formatted}</td>")
        rows.append(f"<tr>{''.join(cells)}</tr>")

    title = f"<caption style='font-weight:bold;padding:8px'>{topic}</caption>" if topic else ""
    return (
        f"<table style='font-size:13px;border-collapse:collapse;border:1px solid #e5e7eb'>"
        f"{title}{''.join(rows)}</table>"
    )


# ── itables ──


def interactiveTable(df: pl.DataFrame, *, pageLength: int = 25) -> Any:
    """대형 DataFrame → itables 인터랙티브 테이블."""
    if not hasItables():
        return df

    import itables

    return itables.show(df.to_pandas(), paging=True, pageLength=pageLength, scrollX=True)


# ── Insight HTML ──

_GRADE_SCORE = {"A": 90, "B": 75, "C": 60, "D": 45, "F": 20}
_GRADE_COLOR = {"A": _GREEN, "B": "#0891b2", "C": "#ca8a04", "D": "#ea580c", "F": _RED}
_AREA_LABELS = {
    "performance": "실적",
    "profitability": "수익성",
    "health": "건전성",
    "cashflow": "현금흐름",
    "governance": "지배구조",
    "risk": "리스크",
    "opportunity": "기회",
    "predictability": "예측성",
    "uncertainty": "불확실성",
    "coreEarnings": "핵심이익",
}


def htmlInsight(result: Any) -> str:
    """AnalysisResult → HTML 등급 바 차트."""
    grades = result.grades()
    corpName = getattr(result, "corpName", "")
    anomalyCount = len(getattr(result, "anomalies", []))
    profile = getattr(result, "profile", "")

    rows: list[str] = []
    for area, grade in grades.items():
        label = _AREA_LABELS.get(area, area)
        score = _GRADE_SCORE.get(grade, 50)
        color = _GRADE_COLOR.get(grade, _GRAY)
        barWidth = score
        rows.append(
            f"<tr>"
            f"<td style='padding:3px 8px;font-weight:bold;white-space:nowrap'>{label}</td>"
            f"<td style='padding:3px 4px;text-align:center;font-weight:bold;color:{color}'>[{grade}]</td>"
            f"<td style='padding:3px 8px;width:200px'>"
            f"<div style='background:#e5e7eb;border-radius:4px;height:18px;width:100%'>"
            f"<div style='background:{color};border-radius:4px;height:18px;width:{barWidth}%'></div>"
            f"</div></td>"
            f"<td style='padding:3px 8px;text-align:right'>{score}</td>"
            f"</tr>"
        )

    footer = f"종합: {profile}"
    if anomalyCount:
        footer += f" &nbsp; 이상치: {anomalyCount}건"

    return (
        f"<div style='font-family:sans-serif;max-width:500px'>"
        f"<h3 style='margin:0 0 8px'>{corpName} 인사이트</h3>"
        f"<table style='font-size:13px;border-collapse:collapse;width:100%'>{''.join(rows)}</table>"
        f"<p style='font-size:12px;color:#6b7280;margin:8px 0 0'>{footer}</p>"
        f"</div>"
    )


# ── Distress HTML ──

_LEVEL_COLOR = {
    "safe": _GREEN,
    "watch": "#0891b2",
    "warning": "#ca8a04",
    "danger": "#ea580c",
    "critical": _RED,
}


def htmlDistress(result: Any) -> str:
    """DistressResult → HTML 스코어카드."""
    level = getattr(result, "level", "")
    overall = getattr(result, "overall", 0)
    creditGrade = getattr(result, "creditGrade", "")
    creditDesc = getattr(result, "creditDescription", "")
    levelColor = _LEVEL_COLOR.get(level, _GRAY)

    # 헤더
    header = (
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:12px'>"
        f"<span style='font-size:24px;font-weight:bold;color:{levelColor}'>{overall:.1f}</span>"
        f"<span style='font-size:14px;color:{levelColor}'>{level.upper()}</span>"
        f"<span style='font-size:14px;color:#6b7280'>| {creditGrade} ({creditDesc})</span>"
        f"</div>"
    )

    # 축 바
    axisRows: list[str] = []
    for axis in getattr(result, "axes", []):
        pct = int(axis.weight * 100)
        score = axis.score
        barColor = _LEVEL_COLOR.get("safe" if score < 30 else "warning" if score < 60 else "danger", _GRAY)
        axisRows.append(
            f"<tr>"
            f"<td style='padding:3px 8px;white-space:nowrap'>{axis.name} ({pct}%)</td>"
            f"<td style='padding:3px 8px;width:160px'>"
            f"<div style='background:#e5e7eb;border-radius:4px;height:14px'>"
            f"<div style='background:{barColor};border-radius:4px;height:14px;width:{score}%'></div>"
            f"</div></td>"
            f"<td style='padding:3px 8px;text-align:right'>{score:.1f}</td>"
            f"</tr>"
        )

    # 위험 요인
    riskHtml = ""
    riskFactors = getattr(result, "riskFactors", [])
    if riskFactors:
        items = "".join(f"<li>{rf}</li>" for rf in riskFactors)
        riskHtml = f"<div style='margin-top:8px'><strong>위험 요인:</strong><ul style='margin:4px 0;padding-left:20px'>{items}</ul></div>"

    return (
        f"<div style='font-family:sans-serif;max-width:500px'>"
        f"{header}"
        f"<table style='font-size:13px;border-collapse:collapse;width:100%'>{''.join(axisRows)}</table>"
        f"{riskHtml}"
        f"</div>"
    )
