"""통화별 포맷팅 헬퍼."""

from __future__ import annotations


def fmtBig(value: float, currency: str = "KRW") -> str:
    """대규모 금액 포맷 (억/M)."""
    if currency == "USD":
        return f"${value / 1e6:,.0f}M"
    return f"{value / 1e8:,.0f}억"


def fmtPrice(value: float, currency: str = "KRW") -> str:
    """주당 가격 포맷 (원/$)."""
    if currency == "USD":
        return f"${value:,.2f}"
    return f"{value:,.0f}원"


def fmtUnit(currency: str = "KRW") -> str:
    """통화 단위 레이블."""
    if currency == "USD":
        return "$"
    return "원"
