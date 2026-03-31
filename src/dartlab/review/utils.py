"""review 유틸리티 — 금액 포맷팅 등."""

from __future__ import annotations


def fmtAmt(value, unit: str = "won") -> str:
    """금액을 조/억 또는 B/M 단위로 포맷."""
    if value is None:
        return "-"

    absVal = abs(value)
    sign = "-" if value < 0 else ""

    if unit == "usd":
        if absVal >= 1_000_000_000:
            return f"{sign}${absVal / 1_000_000_000:.1f}B"
        if absVal >= 1_000_000:
            return f"{sign}${absVal / 1_000_000:.0f}M"
        if absVal >= 1_000:
            return f"{sign}${absVal / 1_000:.0f}K"
        return f"{sign}${absVal:,.0f}"

    if unit == "won":
        if absVal >= 1_0000_0000_0000:
            return f"{sign}{absVal / 1_0000_0000_0000:.1f}조"
        if absVal >= 1_0000_0000:
            return f"{sign}{absVal / 1_0000_0000:.0f}억"
        if absVal >= 1_0000:
            return f"{sign}{absVal / 1_0000:.0f}만"
        return f"{sign}{absVal:,.0f}"

    # 백만원 단위 (segments, salesOrder 등)
    if absVal >= 1_000_000:
        return f"{sign}{absVal / 1_000_000:.1f}조"
    if absVal >= 100:
        return f"{sign}{absVal / 100:.0f}억"
    if absVal >= 1:
        return f"{sign}{absVal:.0f}백만"
    return f"{sign}{absVal:,.0f}"


def fmtAmtScale(value, scale: str) -> str:
    """고정 스케일(조/억/B/M)로 금액 포맷."""
    if value is None:
        return "-"
    sign = "-" if value < 0 else ""
    absVal = abs(value)
    if scale == "조":
        return f"{sign}{absVal:.1f}조"
    if scale == "억":
        return f"{sign}{absVal:.0f}억"
    if scale == "B":
        return f"{sign}${absVal:.1f}B"
    if scale == "M":
        return f"{sign}${absVal:.0f}M"
    return f"{sign}{absVal:,.0f}"


def unifyTableScale(
    rawRows: list[dict],
    labelCol: str,
    valueCols: list[str],
    unit: str = "won",
) -> list[dict]:
    """테이블의 숫자를 같은 스케일(조/억)로 통일."""
    # % 행과 금액 행 분리
    amtRows = []
    pctRows = []
    for row in rawRows:
        label = row.get(labelCol, "")
        if "비중" in label or "%" in label:
            pctRows.append(row)
        else:
            amtRows.append(row)

    if not amtRows:
        return rawRows

    # 전체 금액의 최대값으로 스케일 결정
    maxVal = 0.0
    for row in amtRows:
        for vc in valueCols:
            v = row.get(vc)
            if v is not None and isinstance(v, (int, float)):
                maxVal = max(maxVal, abs(v))

    # 원 → 조/억 또는 USD → B/M 변환 기준값 결정
    if unit == "usd":
        if maxVal >= 1_000_000_000:
            scale = "B"
            divisor = 1_000_000_000
        elif maxVal >= 1_000_000:
            scale = "M"
            divisor = 1_000_000
        else:
            scale = ""
            divisor = 1
    elif unit == "won":
        if maxVal >= 1_0000_0000_0000:
            scale = "조"
            divisor = 1_0000_0000_0000
        elif maxVal >= 1_0000_0000:
            scale = "억"
            divisor = 1_0000_0000
        else:
            scale = ""
            divisor = 1
    else:  # millions
        if maxVal >= 1_000_000:
            scale = "조"
            divisor = 1_000_000
        elif maxVal >= 100:
            scale = "억"
            divisor = 100
        else:
            scale = ""
            divisor = 1

    # 금액 행 변환
    result = []
    for row in amtRows:
        fmtRow = {labelCol: row[labelCol]}
        for vc in valueCols:
            v = row.get(vc)
            if v is not None and isinstance(v, (int, float)):
                scaled = v / divisor if divisor != 1 else v
                fmtRow[vc] = fmtAmtScale(scaled, scale)
            else:
                fmtRow[vc] = row.get(vc, "-")
        result.append(fmtRow)

    # % 행은 포맷 변환 없이 그대로
    for row in pctRows:
        fmtRow = {}
        for k, v in row.items():
            fmtRow[k] = v if isinstance(v, str) else (f"{v:.0f}%" if v is not None else "-")
        result.append(fmtRow)

    return result


def padLabel(text: str, width: int) -> str:
    """한글 폭(2) 감안한 고정폭 패딩."""
    import unicodedata

    w = sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)
    return text + " " * max(0, width - w)


def isTerminal() -> bool:
    """터미널 환경인지 판별."""
    import sys

    if hasattr(sys, "ps1"):
        return False
    try:
        from IPython import get_ipython

        if get_ipython() is not None:
            return False
    except ImportError:
        pass
    return sys.stderr.isatty()
