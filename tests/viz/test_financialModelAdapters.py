"""재무 판별 시각화가 별도 공식을 만들지 않고 analysis 원장을 소비하는 회귀."""

from __future__ import annotations

import pytest

from dartlab.viz.catalog.finance import FINANCE_CARDS
from dartlab.viz.display import adapters

pytestmark = [pytest.mark.unit]


class _Company:
    pass


def _altmanResult(score: float = -1.25) -> dict:
    return {
        "status": "ok",
        "latestScore": score,
        "history": [
            {
                "period": "2025",
                "zScore": score,
                "x1_wcTa": -0.1,
                "x2_reTa": 0.2,
                "x3_ebitTa": 0.05,
                "x4_bveTl": 0.4,
            }
        ],
    }


def testDistressGaugeConsumesAnalysisResultAndSupportsNegativeScores(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapters, "_safeCall", lambda *_args, **_kwargs: _altmanResult())

    result = adapters.buildDistressGauge(_Company())

    assert result["value"] == -1.25
    assert result["minValue"] <= -1.25
    assert [(band["toValue"], band["label"]) for band in result["bands"][:2]] == [
        (1.1, "위험"),
        (2.6, "주의"),
    ]
    assert "Z''" in result["subtitle"]


def testDistressDecompUsesFourCanonicalZppComponents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapters, "_safeCall", lambda *_args, **_kwargs: _altmanResult())

    result = adapters.buildDistressDecomp(_Company())

    assert len(result["items"]) == 4
    assert {item["label"].split()[0] for item in result["items"]} == {"X1", "X2", "X3", "X4"}
    assert all("X5" not in item["label"] for item in result["items"])


def testDistressAdaptersFailClosedOnUnavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapters, "_safeCall", lambda *_args, **_kwargs: {"status": "unavailable"})

    assert adapters.buildDistressGauge(_Company()) == {}
    assert adapters.buildDistressDecomp(_Company()) == {}


def testAltmanTrendCardCallsAnalysisSsot() -> None:
    plan = FINANCE_CARDS["altmanZ"]["seriesPlan"][0]

    assert "ratio" not in plan
    assert plan["analysisCall"] == {
        "module": "financial._stabilityDistress",
        "fn": "calcDistressScore",
        "outputKey": "history.zScore",
        "outputType": "timeseries",
    }
