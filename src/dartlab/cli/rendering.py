"""Rich rendering utilities for CLI output.

Markdown table → Rich Table conversion, snapshot display, grade colorization.
No dependency on ai/ modules — pure data→Rich transformation.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Brand colors (synced with chat.py / landing brand.ts)
# ---------------------------------------------------------------------------

_CLR = "#ea4647"  # primary (brand.ts primary — 로고/강조)
_CLR_SUCCESS = "#34d399"  # success (brand.ts success)
_CLR_WARN = "#fbbf24"  # warning (brand.ts warning)
_CLR_DANGER = "#ea4647"  # primary (brand.ts primary — 위험/음수)
_CLR_MUTED = "#94a3b8"  # textMuted (brand.ts textMuted)

_STATUS_COLORS = {
    "good": _CLR_SUCCESS,
    "caution": _CLR_WARN,
    "danger": _CLR_DANGER,
}

# ---------------------------------------------------------------------------
# Grade rendering
# ---------------------------------------------------------------------------

_GRADE_COLORS = {
    "A+": "bold green",
    "A": "green",
    "A-": "green",
    "B+": "cyan",
    "B": "cyan",
    "B-": "cyan",
    "C+": "yellow",
    "C": "yellow",
    "C-": "yellow",
    "D+": "#fb923c",
    "D": "#fb923c",
    "D-": "#fb923c",
    "F": "bold red",
}


def renderGrade(grade: str) -> str:
    """Map grade letter to Rich color markup."""
    style = _GRADE_COLORS.get(grade.strip().upper(), "dim")
    return f"[{style}]{grade}[/]"


# ---------------------------------------------------------------------------
# Trend indicator
# ---------------------------------------------------------------------------


def renderTrendIndicator(current: float, previous: float) -> str:
    """Return ^ (green), v (red), or - (dim). No emoji."""
    if current > previous * 1.01:
        return f"[{_CLR_SUCCESS}]^[/]"
    if current < previous * 0.99:
        return f"[{_CLR_DANGER}]v[/]"
    return "[dim]-[/]"


# ---------------------------------------------------------------------------
# Number detection & colorization
# ---------------------------------------------------------------------------

_NUM_RE = re.compile(r"^[(\-]?\s*[\d,.]+%?\s*\)?$")
_NEGATIVE_RE = re.compile(r"^\(?[\-]?\s*[\d,.]+%?\s*\)?$|^-[\d,.]+")


def isNumericColumn(values: list[str]) -> bool:
    """Check if most values in a column are numeric."""
    if not values:
        return False
    numCount = sum(1 for v in values if v.strip() and _NUM_RE.match(v.strip()))
    return numCount > len(values) * 0.5


def colorizeNumber(text: str, *, humanize: bool = True) -> str:
    """Positive → green, negative → red in Rich markup. Optionally convert to 조/억."""
    stripped = text.strip()
    if not stripped:
        return text
    display = formatKoreanUnit(text) if humanize else text
    if _NEGATIVE_RE.match(stripped):
        return f"[{_CLR_DANGER}]{display}[/]"
    if _NUM_RE.match(stripped):
        return f"[{_CLR_SUCCESS}]{display}[/]"
    return text


# ---------------------------------------------------------------------------
# Korean unit formatting (조/억)
# ---------------------------------------------------------------------------

_BARE_NUM_RE = re.compile(r"^-?[\d,]+\.?\d*$")


def formatKoreanUnit(text: str) -> str:
    """Convert large numbers to 조/억 notation for readability."""
    stripped = text.strip().replace(",", "")
    if not _BARE_NUM_RE.match(stripped):
        return text
    try:
        val = float(stripped)
    except ValueError:
        return text
    absVal = abs(val)
    sign = "-" if val < 0 else ""
    if absVal >= 1_000_000_000_000:
        return f"{sign}{absVal / 1_000_000_000_000:.1f}조"
    if absVal >= 100_000_000:
        return f"{sign}{absVal / 100_000_000:.0f}억"
    return text


# ---------------------------------------------------------------------------
# Sparkline (ASCII mini chart)
# ---------------------------------------------------------------------------

_SPARK_CHARS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    """Return ASCII sparkline string for a list of numeric values."""
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:
        return _SPARK_CHARS[4] * len(values)
    result = []
    for v in values:
        idx = int((v - lo) / span * (len(_SPARK_CHARS) - 1))
        result.append(_SPARK_CHARS[idx])
    return "".join(result)


# ---------------------------------------------------------------------------
# Markdown table parsing
# ---------------------------------------------------------------------------


def parseMarkdownTable(text: str) -> tuple[list[str], list[list[str]]] | None:
    """Parse markdown table into (headers, rows). Returns None if no table."""
    lines = text.strip().splitlines()
    tableLines = [ln for ln in lines if ln.strip().startswith("|")]
    if len(tableLines) < 3:
        return None

    def _splitRow(line: str) -> list[str]:
        cells = line.strip().strip("|").split("|")
        return [c.strip() for c in cells]

    headers = _splitRow(tableLines[0])

    # skip separator line (|---|---|)
    startIdx = 1
    if tableLines[1].replace("|", "").replace("-", "").replace(":", "").strip() == "":
        startIdx = 2

    rows: list[list[str]] = []
    for ln in tableLines[startIdx:]:
        row = _splitRow(ln)
        if len(row) == len(headers):
            rows.append(row)
        elif len(row) > len(headers):
            rows.append(row[: len(headers)])

    if not rows:
        return None
    return headers, rows


# ---------------------------------------------------------------------------
# Rich Table rendering
# ---------------------------------------------------------------------------


def renderFinancialTable(
    headers: list[str],
    rows: list[list[str]],
    console: Any,
    *,
    title: str = "",
    maxRows: int = 30,
) -> None:
    """Render financial data as a Rich Table with colored numbers."""
    from rich.table import Table

    table = Table(
        title=title if title else None,
        title_style=f"bold {_CLR}",
        show_header=True,
        header_style=f"bold {_CLR}",
        border_style="dim",
        padding=(0, 1),
        show_lines=False,
        expand=False,
    )

    # detect numeric columns
    numericCols: list[bool] = []
    for colIdx in range(len(headers)):
        colValues = [r[colIdx] for r in rows if colIdx < len(r)]
        numericCols.append(isNumericColumn(colValues))

    for i, h in enumerate(headers):
        justify = "right" if i > 0 and i < len(numericCols) and numericCols[i] else "left"
        table.add_column(h, justify=justify, no_wrap=(i == 0))

    displayRows = rows[:maxRows]
    for rowIdx, row in enumerate(displayRows):
        styled: list[str] = []
        for colIdx, cell in enumerate(row):
            if colIdx < len(numericCols) and numericCols[colIdx]:
                styled.append(colorizeNumber(cell))
            else:
                styled.append(cell)
        style = "on #1a1a2e" if rowIdx % 2 == 1 else ""
        table.add_row(*styled, style=style)

    if len(rows) > maxRows:
        table.add_row(f"[dim](+{len(rows) - maxRows} more rows)[/]", *[""] * (len(headers) - 1))

    console.print()
    console.print(table)


# ---------------------------------------------------------------------------
# Snapshot rendering
# ---------------------------------------------------------------------------


def renderSnapshot(items: list[dict], console: Any) -> None:
    """Render company key metrics as a compact 2-column grid."""
    if not items:
        return

    from rich.table import Table

    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=False,
    )
    table.add_column("label1", style="dim", min_width=14)
    table.add_column("value1", min_width=10)
    table.add_column("label2", style="dim", min_width=14)
    table.add_column("value2", min_width=10)

    # pair items into 2-column rows
    for i in range(0, len(items), 2):
        left = items[i]
        leftVal = _colorizeStatus(left.get("value", ""), left.get("status"))

        if i + 1 < len(items):
            right = items[i + 1]
            rightVal = _colorizeStatus(right.get("value", ""), right.get("status"))
            table.add_row(left["label"], leftVal, right["label"], rightVal)
        else:
            table.add_row(left["label"], leftVal, "", "")

    console.print()
    console.print("  ", table)


def _colorizeStatus(value: str, status: str | None) -> str:
    """Apply status-based color to a value."""
    if status and status in _STATUS_COLORS:
        return f"[{_STATUS_COLORS[status]}]{value}[/]"
    return value


# ---------------------------------------------------------------------------
# Tool result rendering (main entry point for chat.py)
# ---------------------------------------------------------------------------


def renderToolResult(resultText: str, console: Any) -> bool:
    """Render tool result data. Returns True if rendered, False for fallback."""
    if not resultText or resultText.startswith("[Error]"):
        return False

    parsed = parseMarkdownTable(resultText)
    if parsed:
        headers, rows = parsed
        renderFinancialTable(headers, rows, console)
        return True

    return False
