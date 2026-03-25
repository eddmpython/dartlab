"""데이터 커버리지/신뢰도 점수."""

from __future__ import annotations


def calcCoverageScore(
    *,
    hasFinance: bool = False,
    hasDocs: bool = False,
    hasInsight: bool = False,
    hasMarket: bool = False,
    hasValuation: bool = False,
    hasForecast: bool = False,
    hasEsg: bool = False,
    hasSectorKpis: bool = False,
    hasRisk: bool = False,
    hasPeer: bool = False,
    hasNarrative: bool = False,
) -> float:
    """0~1 커버리지 점수."""
    weights = {
        "finance": (hasFinance, 0.18),
        "insight": (hasInsight, 0.15),
        "valuation": (hasValuation, 0.13),
        "market": (hasMarket, 0.10),
        "forecast": (hasForecast, 0.08),
        "risk": (hasRisk, 0.08),
        "peer": (hasPeer, 0.06),
        "docs": (hasDocs, 0.06),
        "esg": (hasEsg, 0.05),
        "sectorKpis": (hasSectorKpis, 0.05),
        "narrative": (hasNarrative, 0.06),
    }
    score = sum(w for available, w in weights.values() if available)
    return round(min(score, 1.0), 2)
