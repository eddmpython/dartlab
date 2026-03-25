"""재무 DataFrame → Rich Table 렌더링."""

from __future__ import annotations

import re

import polars as pl
from rich.console import Console
from rich.table import Table

_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _formatValue(v: float | int | None) -> str:
    """숫자를 한국어 단위로 포맷."""
    if v is None:
        return "[dim]-[/dim]"
    if not isinstance(v, (int, float)):
        return str(v)
    absV = abs(v)
    sign = "-" if v < 0 else ""
    if absV >= 1e12:
        return f"{sign}{absV / 1e12:,.1f}조"
    if absV >= 1e8:
        return f"{sign}{absV / 1e8:,.0f}억"
    if absV >= 1e4:
        return f"{sign}{absV / 1e4:,.0f}만"
    if isinstance(v, float):
        return f"{v:,.1f}"
    return f"{v:,}"


def _yoyMark(cur: float | None, prev: float | None) -> str:
    """증감 마크 생성."""
    if cur is None or prev is None or prev == 0:
        return ""
    pct = (cur - prev) / abs(prev) * 100
    if pct > 0:
        return f" [green]▲{pct:.1f}%[/green]"
    if pct < 0:
        return f" [red]▼{abs(pct):.1f}%[/red]"
    return " [dim]━[/dim]"


def _periodColumns(df: pl.DataFrame) -> list[str]:
    """기간 컬럼만 추출 (최신 먼저)."""
    cols = [c for c in df.columns if _PERIOD_RE.match(c)]
    return sorted(cols, reverse=True)


def _labelColumn(df: pl.DataFrame) -> str | None:
    """계정명 컬럼 찾기."""
    for candidate in ("계정명", "label", "account_nm", "topic"):
        if candidate in df.columns:
            return candidate
    return None


def renderFinance(df: pl.DataFrame, *, topic: str = "") -> Table:
    """재무 DataFrame → Rich Table 객체."""
    periodCols = _periodColumns(df)
    labelCol = _labelColumn(df)

    title = topic if topic else None
    table = Table(title=title, show_header=True, header_style="bold cyan", expand=False)

    # 레이블 컬럼
    if labelCol:
        table.add_column(labelCol, style="bold", no_wrap=True, max_width=30)

    # 기간 컬럼
    for col in periodCols:
        table.add_column(col, justify="right", no_wrap=True)

    # 행 추가
    for row in df.iter_rows(named=True):
        cells: list[str] = []

        if labelCol:
            cells.append(str(row.get(labelCol, "")))

        prevVal: float | None = None
        # 기간 역순이라 YoY는 다음 컬럼과 비교
        for i, col in enumerate(periodCols):
            val = row.get(col)
            if isinstance(val, str):
                cells.append(val)
                prevVal = None
                continue

            formatted = _formatValue(val)
            # 전년과 비교 (periodCols는 역순이므로 i+1이 이전 기간)
            nextCol = periodCols[i + 1] if i + 1 < len(periodCols) else None
            nextVal = row.get(nextCol) if nextCol else None
            if isinstance(val, (int, float)) and isinstance(nextVal, (int, float)):
                formatted += _yoyMark(val, nextVal)

            cells.append(formatted)
            prevVal = val

        table.add_row(*cells)

    return table


def show(df: pl.DataFrame, *, topic: str = "") -> None:
    """재무 DataFrame을 Rich로 콘솔 출력."""
    table = renderFinance(df, topic=topic)
    console = Console()
    console.print(table)
