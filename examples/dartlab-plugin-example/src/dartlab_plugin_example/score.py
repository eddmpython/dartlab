"""커스텀 점수 계산 — 플러그인 예제.

이 파일은 Company.show("customScore")가 호출될 때 lazy import된다.
"""

from __future__ import annotations


def customScore(stockCode: str, **kwargs) -> dict | None:
    """커스텀 종합 점수 계산.

    Args:
        stockCode: 종목코드.

    Returns:
        점수 딕셔너리 또는 None.
    """
    try:
        from dartlab.engines.common.extract import getLatest
        from dartlab.engines.dart.company import Company

        c = Company(stockCode)
        ratios = getattr(c, "ratios", None)
        if ratios is None:
            return None

        scores = {}
        # 수익성 점수 (ROE 기반, 0-100)
        roe = getattr(ratios, "roe", None)
        if roe is not None:
            scores["profitability"] = min(max(roe * 5, 0), 100)

        # 안정성 점수 (부채비율 역수 기반, 0-100)
        debt = getattr(ratios, "debtRatio", None)
        if debt is not None and debt > 0:
            scores["stability"] = min(max((300 - debt) / 3, 0), 100)

        if not scores:
            return None

        # 종합 점수
        scores["total"] = sum(scores.values()) / len(scores)
        scores["stockCode"] = stockCode

        return scores
    except (ImportError, FileNotFoundError, OSError, ValueError):
        return None
