"""rank 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations

METRICS = {
    "revenue": {
        "label": "매출",
        "description": "최근 연도 매출액 기준 전체 시장 + 섹터 내 순위",
    },
    "totalAssets": {
        "label": "자산",
        "description": "총자산 기준 전체 시장 + 섹터 내 순위",
    },
    "revenueGrowth3Y": {
        "label": "3년 매출 성장률",
        "description": "3년 매출 CAGR 기준 순위",
    },
}


def buildSpec() -> dict:
    """rank 엔진 스펙 반환."""
    return {
        "name": "rank",
        "description": "전체 상장사 규모 순위 (매출/자산/성장률)",
        "summary": {
            "metrics": list(METRICS.keys()),
            "scope": "전체 상장사 ~2,700개",
            "sizeClasses": ["대형", "중형", "소형"],
        },
        "detail": {name: meta for name, meta in METRICS.items()},
    }
