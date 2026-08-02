"""PeerCompareN tool smoke + percentile rank 검증.

마스터 플랜 트랙 1 PR-2 동행. 옛 max 3 한계 확장(2~12 종목 단일 비교 도구) +
peer-internal percentile rank 결정론 검증.
"""

from __future__ import annotations

import pytest

from dartlab.ai.tools import executeTool, listToolNames

pytestmark = pytest.mark.unit


def test_peerCompareN_registered() -> None:
    """registry 등록 검증."""
    assert "PeerCompareN" in listToolNames()


def test_peerCompareN_single_code_rejected() -> None:
    """단일 종목 → peer 비교 의미 0 → error."""
    result = executeTool("PeerCompareN", {"stockCodes": ["005930"]})
    assert result["ok"] is False
    assert result["error"] == "insufficient_stock_codes"


def test_peerCompareN_empty_list_rejected() -> None:
    """빈 list → error."""
    result = executeTool("PeerCompareN", {"stockCodes": []})
    assert result["ok"] is False
    assert result["error"] == "insufficient_stock_codes"


def test_peerCompareN_legacy_snake_alias() -> None:
    """snake alias peer_compare_n → PeerCompareN."""
    result = executeTool("peer_compare_n", {"stockCodes": []})
    assert result["ok"] is False
    assert result["error"] == "insufficient_stock_codes"


def test_peerCompareN_default_exposed() -> None:
    """default tool 노출 회귀 가드."""
    from dartlab.ai.agent import _DEFAULT_TOOL_NAMES

    assert "PeerCompareN" in _DEFAULT_TOOL_NAMES


def test_calcPercentileRanks_higher_is_better() -> None:
    """ROE 등 높을수록 좋은 metric — 큰 값이 percentile 1.0."""
    from dartlab.ai.tools.peerCompareN import _calcPercentileRanks

    rows = [
        {"stockCode": "A", "roe": 5.0},
        {"stockCode": "B", "roe": 10.0},
        {"stockCode": "C", "roe": 15.0},
    ]
    ranks = _calcPercentileRanks(rows, "roe")
    assert ranks["C"] == 1.0  # best
    assert ranks["A"] == 0.0  # worst
    assert 0.0 < ranks["B"] < 1.0


def test_calcPercentileRanks_lower_is_better() -> None:
    """debtRatio 등 낮을수록 좋은 metric — 작은 값이 percentile 1.0."""
    from dartlab.ai.tools.peerCompareN import _calcPercentileRanks

    rows = [
        {"stockCode": "A", "debtRatio": 50.0},
        {"stockCode": "B", "debtRatio": 100.0},
        {"stockCode": "C", "debtRatio": 200.0},
    ]
    ranks = _calcPercentileRanks(rows, "debtRatio")
    assert ranks["A"] == 1.0  # best (낮음)
    assert ranks["C"] == 0.0


def test_calcPercentileRanks_single_value() -> None:
    """N=1 → 그 값이 1.0."""
    from dartlab.ai.tools.peerCompareN import _calcPercentileRanks

    rows = [{"stockCode": "A", "roe": 10.0}]
    ranks = _calcPercentileRanks(rows, "roe")
    assert ranks == {"A": 1.0}


def test_calcPercentileRanks_skips_none() -> None:
    """metric 이 None 인 row 는 rank 안 부여."""
    from dartlab.ai.tools.peerCompareN import _calcPercentileRanks

    rows = [
        {"stockCode": "A", "roe": 5.0},
        {"stockCode": "B", "roe": None},
        {"stockCode": "C", "roe": 15.0},
    ]
    ranks = _calcPercentileRanks(rows, "roe")
    assert "B" not in ranks
    assert ranks["A"] == 0.0
    assert ranks["C"] == 1.0


def test_calcPercentileRanks_empty_returns_empty() -> None:
    """전부 None / 빈 list → 빈 dict."""
    from dartlab.ai.tools.peerCompareN import _calcPercentileRanks

    assert _calcPercentileRanks([], "roe") == {}
    assert _calcPercentileRanks([{"stockCode": "A", "roe": None}], "roe") == {}


def test_peerCompareN_max_slots_truncate(monkeypatch: pytest.MonkeyPatch) -> None:
    """N > 12 → 앞 12 개로 자름. company_not_resolved error 가 N 만큼 row 누적 (12 개 보존 검증)."""
    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.resolveCompanyOrNone", lambda _code: None)
    codes = [f"99999{i:01d}" for i in range(15)]  # 모두 잘못된 코드 → company_not_resolved row
    result = executeTool("PeerCompareN", {"stockCodes": codes})
    assert result["ok"] is True
    assert len(result["data"]["rows"]) == 12  # 앞 12 개만


def test_peerCompareNEmitsPerTargetValueDateAndExecutionEvidence(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCompany:
        def __init__(self, stockCode: str):
            self.stockCode = stockCode
            self.corpName = stockCode

    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.resolveCompanyOrNone", lambda code: FakeCompany(code))
    monkeypatch.setattr(
        "dartlab.ai.tools.peerCompareN.companyMetrics",
        lambda company: {
            "revenue": 100.0 if company.stockCode == "A" else 200.0,
            "sourcePeriods": {"IS": "2025Q4", "BS": "2025Q4"},
        },
    )
    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.getDcrBadge", lambda _company: None)
    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.getIndustryBadge", lambda _company: None)

    result = executeTool("PeerCompareN", {"stockCodes": ["A", "B"], "metrics": ["revenue"]})
    kinds = [ref["kind"] for ref in result["refs"]]

    assert result["ok"] is True
    assert result["data"]["complete"] is True
    assert kinds.count("valueRef") == 2
    assert kinds.count("dateRef") == 4
    assert kinds.count("executionRef") == 1


def test_peerCompareNMarksMissingCellsAsIncomplete(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeCompany:
        corpName = "회사"

        def __init__(self, stockCode: str):
            self.stockCode = stockCode

    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.resolveCompanyOrNone", lambda code: FakeCompany(code))
    monkeypatch.setattr(
        "dartlab.ai.tools.peerCompareN.companyMetrics",
        lambda _company: {"revenue": None, "sourcePeriods": {"IS": "2025Q4", "BS": "2025Q4"}},
    )
    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.getDcrBadge", lambda _company: None)
    monkeypatch.setattr("dartlab.ai.tools.peerCompareN.getIndustryBadge", lambda _company: None)

    result = executeTool("PeerCompareN", {"stockCodes": ["A", "B"], "metrics": ["revenue"]})

    assert result["ok"] is True
    assert result["data"]["complete"] is False
    assert result["data"]["missingCells"] == [
        {"stockCode": "A", "metric": "revenue"},
        {"stockCode": "B", "metric": "revenue"},
    ]
