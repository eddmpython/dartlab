"""L2 . buildFactors 의 팩터 형성 시점 계약 회귀.

정렬 정보는 수익률 구간보다 앞서야 한다. 전년도 회계연도말 재무와 전년 말 시총으로
5분위를 가르고, 그 재무가 공시된 뒤인 당해 4 월부터의 수익률만 귀속한다. 같은 패키지의
`_factorIC.calcFactorIC` 가 이미 쓰는 규약이고 이 테스트가 `build` 쪽을 결박한다.

외부 의존(scan parquet, KRX 가격)은 monkeypatch 로 격리한다. 검증 대상은 값이 아니라
어느 연도와 어느 구간을 요청하는가다.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from dartlab.quant.factor import build as owner

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def clearCaches():
    """모듈 전역 캐시가 테스트 사이로 새지 않게 비운다."""
    owner._FACTOR_CACHE.clear()
    owner._PORTFOLIO_CACHE.clear()
    yield
    owner._FACTOR_CACHE.clear()
    owner._PORTFOLIO_CACHE.clear()


def _metrics(count: int = 200) -> dict[str, dict[str, float]]:
    """5분위를 가를 수 있는 최소 규모의 합성 universe."""
    return {
        f"{index:06d}": {
            "bookEquity": 1000.0 + index,
            "marketCap": 5000.0 + index * 3,
            "totalAssets": 4000.0 + index,
            "netIncome": 100.0 + index,
            "roe": 0.05 + index / 10000.0,
            "bookRatio": 0.25,
            "bookToMarket": 0.2 + index / 10000.0,
            "assetGrowth": 0.01 + index / 10000.0,
        }
        for index in range(count)
    }


def testBuildFactorsSortsOnPriorYearAndEarnsFromApril(monkeypatch: pytest.MonkeyPatch) -> None:
    """전년 재무로 정렬하고 당해 4 월부터의 수익률만 귀속해야 한다."""

    requestedFundYears: list[str] = []
    requestedReturnYears: list[str] = []

    monkeypatch.setattr(owner, "loadScanParquet", lambda *_args, **_kwargs: pl.LazyFrame({"x": [1]}))
    monkeypatch.setattr(owner, "extractAnnualConsolidated", lambda frame: pl.DataFrame({"x": [1]}))
    monkeypatch.setattr(owner, "_latestYear", lambda *_args, **_kwargs: "2025")

    def fakeMetrics(_market: str, year: str) -> dict[str, dict[str, float]]:
        """요청된 펀더멘털 연도를 기록한다."""
        requestedFundYears.append(year)
        return _metrics()

    def fakeReturns(_codes, _market, year, maxN: int = 30):
        """요청된 수익률 연도를 기록하고 결정적 시계열을 낸다."""
        requestedReturnYears.append(year)
        return np.linspace(0.001, 0.002, 180)

    monkeypatch.setattr(owner, "_buildUniverseMetrics", fakeMetrics)
    monkeypatch.setattr(owner, "_portfolioReturns", fakeReturns)

    result = owner.buildFactors("KR")

    assert result is not None
    assert set(requestedFundYears) == {"2024"}
    assert set(requestedReturnYears) == {"2025"}
    assert result["fundYear"] == "2024"
    assert result["retYear"] == "2025"
    assert result["returnWindow"] == "2025-04-01~2025-12-31"
    # 소비자가 읽는 `year` 는 팩터 시계열이 덮는 연도다.
    assert result["year"] == "2025"


def testPortfolioReturnsRequestOnlyPostFormationWindow(monkeypatch: pytest.MonkeyPatch) -> None:
    """가격 조회 구간이 연초가 아니라 형성 시점 이후여야 한다."""

    captured: dict[str, str] = {}

    def fakeLoadFiltered(*, start: str, end: str, adjustment: str, **_kwargs):
        """요청 구간을 잡아 두고 빈 결과를 낸다."""
        captured["start"] = start
        captured["end"] = end
        captured["adjustment"] = adjustment
        return None

    monkeypatch.setattr("dartlab.gather.bulkData.hfBulk.loadFiltered", fakeLoadFiltered)

    owner._portfolioReturns(["005930", "000660"], "KR", "2025")

    assert captured["start"] == "2025-04-01"
    assert captured["end"] == "2025-12-31"
    # 연초 시작은 아직 공시되지 않은 재무로 가른 포트폴리오에 그 이전 수익률을 붙인다.
    assert captured["start"] != "2025-01-01"


def testFormationWindowMatchesSiblingIcConvention() -> None:
    """형성 규약이 같은 패키지의 IC 경로와 어긋나면 두 수치가 다른 계약이 된다."""

    from dartlab.quant.factor import _factorIC

    source = _factorIC.__file__
    assert source is not None
    text = open(source, encoding="utf-8").read()
    # IC 경로는 전년 펀더멘털과 4 월 시작 수익률을 쓴다. build 도 같아야 한다.
    assert 'f"{ret_year}-04-01"' in text
    assert owner._RETURN_WINDOW_START == "04-01"
    assert owner._RETURN_WINDOW_END == "12-31"
