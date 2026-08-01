"""CreditScorecard tool smoke + contract 검증.

마스터 플랜 트랙 1 PR-6 동행. credit.engine.evaluateCompany wrap. 실제 evaluation 호출은
데이터 무거우니 _compileScorecardLayout helper 결정론 중심.
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools import executeTool, listToolNames

pytestmark = pytest.mark.unit


def test_creditScorecard_registered() -> None:
    """registry 등록."""
    assert "CreditScorecard" in listToolNames()


def test_creditScorecard_missing_stock_code() -> None:
    """stockCode 누락."""
    result = executeTool("CreditScorecard", {})
    assert result["ok"] is False
    assert result["error"] == "missing_stock_code"


def test_creditScorecard_invalid_stock_code() -> None:
    """잘못된 종목 → company_not_resolved 또는 후속 분기."""
    result = executeTool("CreditScorecard", {"stockCode": "999999"})
    assert result["ok"] is False
    assert result["error"] in {
        "company_not_resolved",
        "credit_module_unavailable",
        "evaluate_failed",
        "empty_evaluation",
    }


def test_creditScorecard_legacy_snake_alias() -> None:
    """snake alias credit_scorecard."""
    result = executeTool("credit_scorecard", {})
    assert result["ok"] is False
    assert result["error"] == "missing_stock_code"


def test_creditScorecard_default_exposed() -> None:
    """default tool 노출 회귀 가드."""
    from dartlab.ai.agent import _DEFAULT_TOOL_NAMES

    assert "CreditScorecard" in _DEFAULT_TOOL_NAMES


def test_compileScorecardLayout_basic() -> None:
    """evaluateCompany 가짜 결과 → headline 7 키 + sections + adjustments."""
    from dartlab.ai.tools.creditScorecard import _compileScorecardLayout

    fake_result = {
        "grade": "dCR-AA",
        "score": 25.5,
        "healthScore": 74.5,
        "pdEstimate": 0.15,
        "outlook": "안정적",
        "eCR": "ECR-A",
        "investmentGrade": True,
        "axes": [
            {"name": "채무상환능력", "score": 80.0, "weight": 0.2, "metrics": [{"k": "v"}, {"k": "v"}]},
            {"name": "자본구조", "score": 75.0, "weight": 0.15, "metrics": []},
        ],
        "chsAdjustment": None,
        "notchAdjustment": {"reason": "industry"},
    }
    layout = _compileScorecardLayout(fake_result)
    assert layout["headline"]["grade"] == "dCR-AA"
    assert layout["headline"]["pdEstimate"] == 0.15
    assert layout["headline"]["investmentGrade"] is True
    assert len(layout["sections"]) == 2
    assert layout["sections"][0]["axis"] == "채무상환능력"
    assert layout["sections"][0]["metricCount"] == 2
    assert layout["adjustments"]["notch"] == {"reason": "industry"}
    assert layout["adjustments"]["chs"] is None


def test_compileScorecardLayout_empty_axes() -> None:
    """axes 부재 → sections 빈 list, headline 그대로."""
    from dartlab.ai.tools.creditScorecard import _compileScorecardLayout

    layout = _compileScorecardLayout({"grade": "dCR-B", "score": 60.0})
    assert layout["headline"]["grade"] == "dCR-B"
    assert layout["sections"] == []
    assert layout["adjustments"]["chs"] is None


def test_historical_scorecard_does_not_mix_latest_factors(monkeypatch: pytest.MonkeyPatch) -> None:
    """역사적 평가에 최신 Altman/Beneish 횡단면을 붙이지 않는다."""
    import importlib
    from types import SimpleNamespace

    from dartlab.ai.tools.creditScorecard import creditScorecard

    company = SimpleNamespace(stockCode="005930", corpName="테스트")
    monkeypatch.setattr("dartlab.ai.tools.creditScorecard.resolveCompanyOrNone", lambda _code: company)
    credit_engine = importlib.import_module("dartlab.credit.engine")
    monkeypatch.setattr(credit_engine, "evaluateCompany", lambda _company, **_kwargs: {"grade": "dCR-A", "axes": []})

    result = creditScorecard("005930", basePeriod="2023", includeFactors=True)

    assert result.ok is True
    assert result.data["factors"] == {
        "status": "unavailable",
        "reasonCode": "historical_factor_asof_unsupported",
        "basePeriod": "2023",
    }
