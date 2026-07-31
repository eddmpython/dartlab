"""synth 추정 불가 상황의 비발행 계약 회귀.

추정하지 못한 것을 추정값처럼 보고하지 않는 것, 특히 그 값이 유의성 판정이나 WACC 로
흘러 사용자 결론을 바꾸지 않는 것을 고정한다.
"""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.synth.eventStudy import _marketModel, calcCAR
from dartlab.synth.impliedERP import calcImpliedERP

pytestmark = pytest.mark.unit


class TestMarketModelEstimability:
    """시장모형을 추정하지 못하면 상수를 추정값으로 내지 않는다."""

    def testTooFewObservationsIsNotEstimable(self) -> None:
        """20 관측 미만은 (0.0, 1.0, 0.01) 이 아니라 None 이다 (결함 회귀)."""
        assert _marketModel(np.zeros(10), np.zeros(10)) is None

    def testLengthMismatchIsNotEstimable(self) -> None:
        """길이 불일치도 상수 대체 없이 None 이다."""
        assert _marketModel(np.zeros(30), np.zeros(25)) is None

    def testCalcCarRefusesInsteadOfFabricatingSignificance(self) -> None:
        """추정 불가 구간은 유의성 판정 대신 모듈 관례인 error 를 낸다 (결함 회귀)."""
        rng = np.random.default_rng(0)
        stock = rng.normal(0, 0.02, 200)
        market = rng.normal(0, 0.01, 200)

        result = calcCAR(stock, market, eventIdx=150, estimationWindow=(-15, -6), eventWindow=(-5, 5))

        assert "error" in result
        for fabricated in ("sigma", "tStat", "isSignificant", "interpretation"):
            assert fabricated not in result

    def testEstimableWindowStillReportsRealEstimates(self) -> None:
        """추정 가능한 구간의 정상 경로는 그대로다 (회귀 가드)."""
        rng = np.random.default_rng(0)
        stock = rng.normal(0, 0.02, 200)
        market = rng.normal(0, 0.01, 200)

        result = calcCAR(stock, market, eventIdx=150, estimationWindow=(-120, -30), eventWindow=(-5, 5))

        assert "error" not in result
        # 고정 상수가 아니라 실제 추정치가 나온다.
        assert result["sigma"] != 0.01
        assert result["beta"] != 1.0
        assert isinstance(result["isSignificant"], bool)


class TestImpliedErpWithdrawn:
    """가격 SSOT 없이 implied ERP 를 발행하지 않는다."""

    @pytest.mark.parametrize("country", ["KR", "US"])
    def testImpliedErpIsNotPublished(self, country: str) -> None:
        """역산 값은 항상 None 이고 비발행이 키로 드러난다 (결함 회귀)."""
        result = calcImpliedERP(country)

        assert result["impliedERP"] is None
        assert result["method"] == "none"
        assert result["source"] == "fallback_historical"
        assert result["sampleCount"] == 0

    def testStaticErpStaysCurated(self) -> None:
        """정적 ERP 는 큐레이션 값 그대로다. 옛 역산은 클램프 상한 12.0 을 냈다."""
        result = calcImpliedERP("KR")

        assert result["countryCode"] == "KR"
        assert result["totalERP"] < 12.0
        assert result["totalERP"] == pytest.approx(result["matureMarketERP"] + result["countryRiskPremium"], abs=0.01)
