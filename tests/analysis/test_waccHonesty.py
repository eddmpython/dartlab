"""WACC 산출의 베타 출처와 자본잠식 처리 회귀.

`computeCompanyWacc` 는 이 라이브러리의 거의 모든 가치평가가 쓰는 할인율이다. 두 결함이
겹쳐 있었다.

첫째, 더 정교한 방법을 켜면 오히려 베타가 낮아졌다. 섹터 이름을 `name` 속성에서 읽는데
그런 속성이 없어(`label` 이다) 언제나 "Unknown" 으로 떨어졌고, 그러면 베타 조회가 반드시
실패해 대체값 1.0 이 나온다. 그런데 호출부가 `method` 를 보지 않고 값만 받아서, 섹터
베타 1.2 대신 1.0 이 들어갔다. 할인율이 낮아지면 가치평가는 부풀어 오른다.

둘째, 자본잠식 기업의 음수 자기자본이 그대로 가중치 계산에 들어갔다. 가중치가 -200% 와
300% 처럼 뒤집히고, 그 조합이 하필 WACC 하한에 걸려 가장 위험한 회사가 가장 싼 할인율을
받았다. 자본 크기에 대해 단조롭지도 않아 -200 억과 -400 억이 전혀 다른 값을 냈다.
"""

from __future__ import annotations

import pytest

from dartlab.analysis.financial._proformaCore import computeCompanyWacc
from dartlab.core.sector import getSectorParamsByName


def _series(equity: float | None) -> dict:
    """WACC 계산에 필요한 최소 계열."""

    return {
        "BS": {
            "total_stockholders_equity": [equity],
            "shortterm_borrowings": [100e9],
            "longterm_borrowings": [200e9],
            "debentures": [0],
        },
        "IS": {"profit_before_tax": [50e9], "income_tax_expense": [10e9], "finance_costs": [15e9]},
        "periods": ["2024"],
    }


def testBottomUpOptionNeverDegradesBelowTheSectorBeta() -> None:
    """더 정교한 방법을 켰는데 할인율이 낮아지면 방향이 반대다."""

    sectorParams = getSectorParamsByName("IT")

    plain, plainDetails = computeCompanyWacc(_series(500e9), sectorParams=sectorParams)
    bottomUp, bottomUpDetails = computeCompanyWacc(_series(500e9), sectorParams=sectorParams, bottomUpBeta=True)

    assert bottomUpDetails["beta"] >= plainDetails["beta"]
    assert bottomUp >= plain


def testBetaProvenanceIsReported() -> None:
    """대체값과 계산값이 같은 모양으로 나가면 소비자가 신뢰 판단을 못 한다."""

    _wacc, details = computeCompanyWacc(_series(500e9), sectorParams=getSectorParamsByName("IT"))

    assert details["betaSource"] == "sectorParams"


def testBetaOverrideIsLabeledAsSuch() -> None:
    """외부 주입 베타도 출처가 남아야 한다."""

    _wacc, details = computeCompanyWacc(_series(500e9), betaOverride=1.8)

    assert details["beta"] == 1.8
    assert details["betaSource"] == "override"


def testCapitalWeightsStayWithinBounds() -> None:
    """가중치가 구간을 벗어나면 그 뒤 계산 전체가 의미를 잃는다."""

    for equity in (500e9, -200e9, -400e9, 0.0):
        _wacc, details = computeCompanyWacc(_series(equity), sectorParams=getSectorParamsByName("IT"))
        assert 0.0 <= details["equity_weight"] <= 100.0, equity
        assert 0.0 <= details["debt_weight"] <= 100.0, equity


def testInsolventCompanyDoesNotGetTheCheapestDiscountRate() -> None:
    """자본잠식 기업이 하한 할인율을 받으면 가장 위험한 회사가 가장 싸게 평가된다."""

    healthy, _ = computeCompanyWacc(_series(500e9), sectorParams=getSectorParamsByName("IT"))
    insolvent, _ = computeCompanyWacc(_series(-200e9), sectorParams=getSectorParamsByName("IT"))

    assert insolvent > healthy


def testInsolventCasesAgreeWithEachOther() -> None:
    """자본 크기에 따라 값이 튀면 어느 쪽도 믿을 수 없다."""

    first, _ = computeCompanyWacc(_series(-200e9), sectorParams=getSectorParamsByName("IT"))
    second, _ = computeCompanyWacc(_series(-400e9), sectorParams=getSectorParamsByName("IT"))

    assert first == pytest.approx(second)


def testUnknownEquityValueIsFlagged() -> None:
    """자기자본 가치를 세우지 못했으면 그 사실이 결과에 남아야 한다."""

    _wacc, details = computeCompanyWacc(_series(-200e9), sectorParams=getSectorParamsByName("IT"))

    assert details["equityValueUnknown"] is True


def testHealthyCompanyIsNotFlagged() -> None:
    """정상 기업에 미상 표시가 붙으면 경고가 무의미해진다."""

    _wacc, details = computeCompanyWacc(_series(500e9), sectorParams=getSectorParamsByName("IT"))

    assert details["equityValueUnknown"] is False


def testOptionalMarketExceptionGroupDoesNotBreakLocalWacc(monkeypatch: pytest.MonkeyPatch) -> None:
    """AnyIO가 묶은 offline 오류도 선택적 시장 입력 실패로 강등한다."""
    from dartlab.analysis.financial import _investmentAnalysisRoic as roic
    from dartlab.analysis.financial import proforma
    from dartlab.core.offlineGuard import OfflineViolation

    class _Company:
        stockCode = ""
        currency = "KRW"
        sectorParams = None
        _cache: dict[str, object] = {}

        def _buildFinanceSeries(self, *, freq: str):
            return _series(500e9), ["2024"]

    def _offlineBeta(*_args, **_kwargs):
        raise ExceptionGroup("optional market lookup failed", [OfflineViolation("network blocked")])

    monkeypatch.setattr(proforma, "_fetchBeta", _offlineBeta)
    monkeypatch.setattr(proforma, "computeCompanyWacc", lambda *_args, **_kwargs: (8.5, {}))

    assert roic._estimateWacc(_Company()) == 8.5


def testBetaFetchDegradesOfflineExceptionGroup(monkeypatch: pytest.MonkeyPatch) -> None:
    """직접 beta 조회도 Linux AnyIO의 offline 그룹을 None으로 정규화한다."""
    from dartlab.analysis.financial import _proformaCore as proformaCore
    from dartlab.core.offlineGuard import OfflineViolation
    from dartlab.gather.domains import naver

    async def _offlineHistory(*_args, **_kwargs):
        raise ExceptionGroup("network candidates failed", [OfflineViolation("network blocked")])

    proformaCore._fetchBeta.cache_clear()
    monkeypatch.setattr(naver, "fetchHistory", _offlineHistory)

    assert proformaCore._fetchBeta("999995", "KRW") is None
