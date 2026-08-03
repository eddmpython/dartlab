"""DCFValuation tool smoke + contract 검증.

마스터 플랜 트랙 1 PR-1 동행 단위 테스트. dartlab 데이터 의존 무거운 경로는 patch 로 분리.

검증 영역:
1. registry 등록 (executeTool 진입 + listToolNames 노출)
2. stockCode 누락 → missing_stock_code error
3. company_not_resolved (잘못된 코드) → company_not_resolved error
4. _scenarioDict / _safeBaseScore helper 결정론
5. legacy snake_case 매핑 (dcf_valuation → DCFValuation)
6. default tool 노출 (_DEFAULT_TOOL_NAMES) 회귀 가드 (2026-05-17 default 미노출 패턴)
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools import executeTool, listToolNames

pytestmark = pytest.mark.unit


def test_dcfValuation_registered() -> None:
    """registry 등록 검증 — 마스터 플랜 트랙 1 PR-1."""
    assert "DCFValuation" in listToolNames()


def test_dcfValuation_missing_stock_code() -> None:
    """stockCode 빈 입력 → missing_stock_code error."""
    result = executeTool("DCFValuation", {"stockCode": ""})
    assert result["ok"] is False
    assert result["error"] == "missing_stock_code"


def test_dcfValuation_invalid_stock_code() -> None:
    """잘못된 stockCode → company_not_resolved (Company 생성 실패)."""
    result = executeTool("DCFValuation", {"stockCode": "999999"})
    assert result["ok"] is False
    assert result["error"] in {"company_not_resolved", "series_unavailable", "dcf_all_failed"}


def test_dcfValuation_legacy_snake_alias() -> None:
    """legacy snake_case 매핑 — dcf_valuation → DCFValuation."""
    result = executeTool("dcf_valuation", {"stockCode": ""})
    assert result["ok"] is False
    assert result["error"] == "missing_stock_code"


def test_dcfValuation_default_exposed_to_llm() -> None:
    """default tool 노출 회귀 가드.

    옛 도구가 registry 등록만 됐다가 default 미노출이라 LLM 호출 0 회 회귀
    (2026-05-17 OAuth probe). 본 검증으로 DCFValuation 도 동일 회귀 차단.
    """
    from dartlab.ai.agent import _DEFAULT_TOOL_NAMES

    assert "DCFValuation" in _DEFAULT_TOOL_NAMES


def test_dcfValuation_scenarioDict_helper_keys() -> None:
    """_scenarioDict — DCFResult 의 핵심 8 키 보존."""
    from dartlab.ai.tools.dcfValuationTool import _scenarioDict

    class FakeDcf:
        discountRate = 10.0
        growthRateInitial = 5.0
        terminalGrowth = 2.5
        enterpriseValue = 1_000_000.0
        equityValue = 800_000.0
        perShareValue = 80_000.0
        marginOfSafety = 5.5

    out = _scenarioDict(FakeDcf(), "base")
    assert out["scenario"] == "base"
    assert out["perShareValue"] == 80_000.0
    assert out["marginOfSafety"] == 5.5
    assert set(out) == {
        "scenario",
        "discountRate",
        "growthRateInitial",
        "terminalGrowth",
        "enterpriseValue",
        "equityValue",
        "perShareValue",
        "marginOfSafety",
    }


def test_dcfValuation_scenarioRows_areCanonicalTableContent() -> None:
    """시나리오 매트릭스가 evidence projection 뒤에도 빈 표가 되지 않는다."""
    from dartlab.ai.tools.dcfValuationTool import _scenarioRows

    results = {
        "bull": {"scenario": "bull", "perShareValue": 120_000.0},
        "bear": {"scenario": "bear", "perShareValue": 60_000.0},
        "base": {"scenario": "base", "perShareValue": 90_000.0},
    }

    rows = _scenarioRows(results)

    assert [row["scenario"] for row in rows] == ["bear", "base", "bull"]
    assert rows[1]["perShareValue"] == 90_000.0


def test_dcfValuation_confidence_uses_forecast_method() -> None:
    """SSOT — DCF confidence 는 core/confidence.py 의 ``forecast`` (30) 사용.

    "dcf" 는 forecast subtype — confidenceMethod 라벨에만 노출, 점수는 30.
    """
    from dartlab.core.confidence import baseScore

    assert baseScore("forecast") == 30


# ── 입력 해석기: 살아 있는 공급원을 보는가 ──


class _ContractCompany:
    """DCF 입력 세 갈래를 계약/내부 공급원으로만 제공하는 Company 대역."""

    stockCode = "999999"
    corpName = "테스트기업"

    def _getFinanceBuild(self, period: str = "q", fsDivPref: str = "CFS"):
        return ({"IS": {"sales": [1.0]}, "BS": {"total_assets": [2.0]}, "CF": {}}, ["2025Q4"])

    def __init__(self) -> None:
        # 주식수 공급원은 회사 자기 정기보고서다. 시장 전체를 훑는 capital 축이 아니다.
        self._profileAccessor = type("Profile", (), {"sharesOutstanding": 1000})()


def test_resolveSeries_usesFinanceBuild() -> None:
    """재무 시계열은 회사의 finance 빌드에서 나온다.

    예전에는 `company.finance.timeseries` 를 읽었다. `finance` 는 표면에서 빠진 이름이라
    늘 None 이었고, 호출부가 곧바로 series_unavailable 로 끝내서 이 도구가 어느 회사에서도
    결과를 못 냈다.
    """
    from dartlab.ai.tools.dcfValuationTool import _resolveSeries

    series = _resolveSeries(_ContractCompany())

    assert series and set(series) >= {"IS", "BS"}


def test_resolveShares_usesCompanyOwnReport() -> None:
    """발행주식수는 회사 자기 정기보고서에서 나온다.

    옛 세 후보 이름(sharesOutstanding · shares · totalShares)은 전부 표면에 없었다. 한때
    ``capital`` 축을 거쳤는데 그 축은 전종목 스캔이라 회사당 8 초에 시장 프레임을 통째로
    메모리에 올린다. 한 회사의 주식수를 알자고 시장을 훑을 이유가 없다.
    """
    from dartlab.ai.tools.dcfValuationTool import _resolveShares

    assert _resolveShares(_ContractCompany()) == 1000


def test_resolveShares_withoutProfileIsNone() -> None:
    """공급원이 없으면 None. 0 이나 추정치로 메우지 않는다."""
    from dartlab.ai.tools.dcfValuationTool import _resolveShares

    assert _resolveShares(object()) is None
    assert _resolveShares(None) is None


def test_resolveCurrentPrice_usesGatherContract(monkeypatch) -> None:
    """현재 주가는 공개 계약 `dartlab.gather("price", 코드)` 에서 나온다."""
    import polars as pl

    import dartlab
    from dartlab.ai.tools.dcfValuationTool import _resolveCurrentPrice

    monkeypatch.setattr(dartlab, "gather", lambda axis, code: pl.DataFrame({"close": [100.0, 220.0]}))

    assert _resolveCurrentPrice(_ContractCompany()) == 220.0
