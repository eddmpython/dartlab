"""Gather 도메인 레지스트리 — fallback 순서 정의."""

from __future__ import annotations

# 데이터 유형별 fallback 순서
PRICE_FALLBACK = ["naver", "yahoo"]
CONSENSUS_FALLBACK = ["naver"]
FLOW_FALLBACK = ["naver"]
HISTORY_FALLBACK = ["yahoo"]


def load_domain(name: str):
    """도메인 모듈 lazy import."""
    if name == "naver":
        from . import naver

        return naver
    if name == "yahoo":
        from . import yahoo

        return yahoo
    raise ValueError(f"알 수 없는 도메인: {name}")
