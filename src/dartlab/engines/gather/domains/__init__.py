"""Gather 도메인 레지스트리 — fallback 순서 정의."""

from __future__ import annotations

from ..market_config import get_market_config

# 데이터 유형별 fallback 순서 (KR 기본값 — 하위호환)
PRICE_FALLBACK = ["naver", "yahoo_direct", "yahoo"]
CONSENSUS_FALLBACK = ["naver"]
FLOW_FALLBACK = ["naver"]
HISTORY_FALLBACK = ["yahoo_direct", "yahoo"]


def get_price_fallback(market: str = "KR") -> list[str]:
    """시장별 주가 fallback 체인."""
    config = get_market_config(market)
    return list(config.fallback_chain)


def load_domain(name: str):
    """도메인 모듈 lazy import."""
    if name == "naver":
        from . import naver

        return naver
    if name == "yahoo":
        from . import yahoo

        return yahoo
    if name == "yahoo_direct":
        from . import yahoo_direct

        return yahoo_direct
    if name == "fmp":
        from . import fmp

        return fmp
    raise ValueError(f"알 수 없는 도메인: {name}")
