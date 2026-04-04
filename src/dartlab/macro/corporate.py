"""매크로 기업집계 분석 — scan finance.parquet 기반 독자 매크로 지표.

전종목 재무제표를 집계하여 매크로 사이클을 bottom-up으로 포착한다.
Bloomberg/FactSet 유료 서비스에서나 가능한 기능을 dartlab scan 데이터로 무료 제공.
"""

from __future__ import annotations

import os

import polars as pl

from dartlab.core.finance.corporateAggregate import (
    aggregateEarningsCycle,
    leverageCycle,
    ponziRatio,
)


def _load_scan_finance(market: str) -> pl.DataFrame | None:
    """scan/finance.parquet 로드."""
    if market.upper() == "KR":
        paths = [
            os.path.join("data", "dart", "scan", "finance.parquet"),
            os.path.join(os.path.expanduser("~"), ".dartlab", "data", "dart", "scan", "finance.parquet"),
        ]
    else:
        paths = [
            os.path.join("data", "edgar", "scan", "finance.parquet"),
            os.path.join(os.path.expanduser("~"), ".dartlab", "data", "edgar", "scan", "finance.parquet"),
        ]

    for p in paths:
        if os.path.exists(p):
            return pl.read_parquet(p)

    # HF 자동 다운로드 시도
    try:
        from dartlab.core.dataLoader import loadScanFinance

        return loadScanFinance(market=market)
    except Exception:
        return None


def analyze_corporate(*, market: str = "KR", as_of: str | None = None, overrides: dict | None = None, **kwargs) -> dict:
    """기업집계 매크로 분석.

    Returns:
        dict: earningsCycle, ponziRatio, leverageCycle
    """
    result: dict = {"market": market.upper()}

    df = _load_scan_finance(market)
    if df is None or len(df) == 0:
        result["earningsCycle"] = None
        result["ponziRatio"] = None
        result["leverageCycle"] = None
        result["description"] = "scan/finance.parquet 없음 — dartlab collect --scan 또는 downloadAll('scan') 필요"
        return result

    # 이익 사이클
    try:
        ec = aggregateEarningsCycle(df)
        result["earningsCycle"] = {
            "periods": ec.periods,
            "totalOperatingIncome": ec.totalOperatingIncome,
            "yoyChanges": ec.yoyChanges,
            "currentDirection": ec.currentDirection,
            "currentLabel": ec.currentLabel,
            "companyCount": ec.companyCount,
            "description": ec.description,
        }
    except Exception:
        result["earningsCycle"] = None

    # Ponzi 비율
    try:
        pr = ponziRatio(df)
        result["ponziRatio"] = {
            "periods": pr.periods,
            "ratios": pr.ratios,
            "currentRatio": pr.currentRatio,
            "trend": pr.trend,
            "trendLabel": pr.trendLabel,
            "description": pr.description,
        }
    except Exception:
        result["ponziRatio"] = None

    # 레버리지 사이클
    try:
        lc = leverageCycle(df)
        result["leverageCycle"] = {
            "periods": lc.periods,
            "medianDebtRatio": lc.medianDebtRatio,
            "currentLevel": lc.currentLevel,
            "trend": lc.trend,
            "trendLabel": lc.trendLabel,
            "description": lc.description,
        }
    except Exception:
        result["leverageCycle"] = None

    return result
