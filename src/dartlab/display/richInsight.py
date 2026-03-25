"""AnalysisResult → Rich Panel 렌더링."""

from __future__ import annotations

from typing import Any

_GRADE_SCORE = {"A": 90, "B": 75, "C": 60, "D": 45, "F": 20}
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


def _gradeBar(grade: str, width: int = 20) -> str:
    """등급 → 프로그레스 바."""
    score = _GRADE_SCORE.get(grade, 50)
    filled = int(score / 100 * width)
    empty = width - filled
    if grade in ("A",):
        color = "green"
    elif grade in ("B",):
        color = "cyan"
    elif grade in ("C",):
        color = "yellow"
    else:
        color = "red"
    bar = f"[{color}]{'█' * filled}{'░' * empty}[/{color}]"
    return f"[{grade}] {bar} {score}"


def renderInsight(result: Any) -> str:
    """AnalysisResult → Rich Panel 문자열."""
    from rich.console import Console
    from rich.panel import Panel

    lines: list[str] = []
    grades = result.grades()

    for area, grade in grades.items():
        label = _AREA_LABELS.get(area, area)
        lines.append(f"  {label:<6s} {_gradeBar(grade)}")

    anomalyCount = len(getattr(result, "anomalies", []))
    summaryLine = f"  종합: {getattr(result, 'profile', '')}"
    if anomalyCount:
        summaryLine += f"   이상치: {anomalyCount}건"
    lines.append("")
    lines.append(summaryLine)

    body = "\n".join(lines)
    corpName = getattr(result, "corpName", "")

    panel = Panel(
        body,
        title=f"[bold]{corpName} 인사이트[/bold]",
        border_style="bright_blue",
        expand=False,
        padding=(0, 1),
    )

    console = Console(record=True, width=60)
    console.print(panel)
    return console.export_text()
