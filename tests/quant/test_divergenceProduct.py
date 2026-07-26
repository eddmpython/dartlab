from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import polars as pl


def _ohlcv(n: int = 120) -> pl.DataFrame:
    start = date(2025, 1, 1)
    close = np.linspace(100.0, 150.0, n)
    return pl.DataFrame(
        {
            "date": [start + timedelta(days=index) for index in range(n)],
            "open": close,
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "volume": [1000] * n,
        }
    )


def testDivergenceProductClassifiesUnderReaction() -> None:
    from dartlab.quant.product import buildDivergenceResult

    result = buildDivergenceResult(
        "005930",
        "KR",
        technical={"verdict": "약세", "score": -3, "rsi": 35.0},
        earnings={
            "sue": 2.5,
            "earningsTrend": "consistent_growth",
            "years": ["2022", "2023", "2024"],
        },
        expectation={"score": 1.2, "year": "2024", "universe": 500},
        priceAsOf="2025-04-30",
        asOf="2025-05-01",
    )

    assert result["classification"] == "underReaction"
    assert result["divergence"] == "괴리"
    assert result["product"]["status"] == "usable"
    assert result["product"]["identity"]["axis"] == "괴리"
    assert result["product"]["payload"]["blockRefs"] == ["fundamental", "expectation", "price"]
    relation = next(row for row in result["product"]["claims"] if row["id"] == "quant.fundamentalPriceRelation")
    assert relation["relation"] == "underReaction"
    assert relation["evidenceRefs"] == ["quant.fundamental", "quant.expectation", "quant.price"]
    assert any(gap["id"] == "quant.analystConsensus" for gap in result["product"]["gaps"])


def testDivergenceProductDoesNotHideMissingEvidence() -> None:
    from dartlab.quant.product import buildDivergenceResult

    result = buildDivergenceResult(
        "AAPL",
        "US",
        technical=None,
        earnings={"error": "finance.parquet 없음"},
        expectation=None,
        priceAsOf=None,
        asOf="2025-05-01",
    )

    product = result["product"]
    assert result["classification"] == "inconclusive"
    assert product["status"] == "blocked"
    assert product["confidence"]["level"] == "blocked"
    assert {gap["id"] for gap in product["gaps"]} >= {
        "quant.fundamental",
        "quant.expectationProxy",
        "quant.priceReaction",
    }


def testInconclusiveClassificationCannotHaveHighConfidence() -> None:
    from dartlab.quant.product import buildDivergenceResult

    result = buildDivergenceResult(
        "005930",
        "KR",
        technical={"verdict": "중립", "score": 0},
        earnings={"sue": 0.1, "earningsTrend": "mixed", "years": ["2023", "2024"]},
        expectation={"score": 0.0, "year": "2024", "universe": 500},
        priceAsOf="2025-04-30",
        asOf="2025-05-01",
    )

    assert result["classification"] == "inconclusive"
    assert result["product"]["confidence"]["level"] == "medium"
    assert result["product"]["confidence"]["score"] == 65.0


def testPublicDivergenceCombinesDisclosureExpectationAndPrice(monkeypatch) -> None:
    from dartlab.quant.alphas import earningsSurprise
    from dartlab.quant.screen import axTechnical
    from dartlab.quant.signal import analyzer, earningsMomentum

    monkeypatch.setattr(axTechnical, "_getOhlcv", lambda stockCode, **kwargs: (_ohlcv(), None))
    monkeypatch.setattr(
        analyzer,
        "technicalVerdict",
        lambda *args, **kwargs: {"verdict": "강세", "score": 3, "rsi": 58.0},
    )
    monkeypatch.setattr(
        earningsMomentum,
        "calcEarnings",
        lambda *args, **kwargs: {
            "sue": -2.2,
            "earningsTrend": "mostly_declining",
            "years": ["2022", "2023", "2024"],
        },
    )
    monkeypatch.setattr(
        earningsSurprise,
        "calcEarningsSurprise",
        lambda **kwargs: {"score": -1.5, "year": "2024", "universe": 600},
    )

    result = axTechnical.calcDivergence("005930", market="KR")

    assert result["classification"] == "overOptimism"
    assert result["fundamental"]["direction"] == "negative"
    assert result["price"]["direction"] == "positive"
    assert len(result["product"]["evidence"]) == 3
