"""EDGAR scan report 빌더 — shareholderReturnRows 가 배당 연도 시계열(ShareholderReturnYear 동형)을
XBRL facts 에서 정확히 뽑는지 + 태그 폴백 머지. 합성 facts → 네트워크/OOM 무관.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _facts(rows: list[dict]) -> pl.DataFrame:
    """shareholderReturnRows 입력 facts 합성 — namespace='us-gaap'·fp='FY' 기본."""
    base = {"namespace": "us-gaap", "fp": "FY", "filed": "2025-11-01"}
    return pl.DataFrame([{**base, **r} for r in rows])


def test_shareholder_return_dividend_payout():
    """dps·totalDividend·eps·payoutPct 연도별 정확 — payout = totalDividend/netIncome×100."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts(
        [
            {"tag": "CommonStockDividendsPerShareDeclared", "val": 1.0, "fy": 2024},
            {"tag": "PaymentsOfDividendsCommonStock", "val": 1_000_000.0, "fy": 2024},
            {"tag": "NetIncomeLoss", "val": 5_000_000.0, "fy": 2024},
            {"tag": "EarningsPerShareDiluted", "val": 4.0, "fy": 2024},
        ]
    )
    rows = shareholderReturnRows(facts, "TEST")
    assert len(rows) == 1
    r = rows[0]
    assert r["year"] == "2024"
    assert r["dps"] == 1.0
    assert r["totalDividend"] == 1_000_000.0
    assert r["eps"] == 4.0
    assert r["payoutPct"] == 20.0  # 1e6 / 5e6 × 100
    assert r["stockCode"] == "TEST"


def test_tag_fallback_merge_fills_gaps():
    """totalDividend 태그 전환(연도별 상이) — 이른 태그 우선, 빈 연도는 다음 태그가 채움."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts(
        [
            {"tag": "CommonStockDividendsPerShareDeclared", "val": 0.9, "fy": 2017},
            {"tag": "CommonStockDividendsPerShareDeclared", "val": 1.0, "fy": 2024},
            {"tag": "PaymentsOfDividendsCommonStock", "val": 100.0, "fy": 2017},  # 옛 태그
            {"tag": "PaymentsOfDividends", "val": 200.0, "fy": 2024},  # 새 태그(2017 없음)
        ]
    )
    rows = {r["year"]: r for r in shareholderReturnRows(facts, "X")}
    assert rows["2017"]["totalDividend"] == 100.0  # 옛 태그
    assert rows["2024"]["totalDividend"] == 200.0  # 폴백 머지로 새 태그가 채움


def test_no_shareholder_signal_excluded():
    """배당·자사주 신호 전무(eps 만) 연도는 제외 — 무배당 성장주 빈 패널."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts([{"tag": "EarningsPerShareDiluted", "val": 3.0, "fy": 2024}])
    assert shareholderReturnRows(facts, "GROWTH") == []


def test_latest_filed_restatement_wins():
    """같은 연도 정정공시 — 최신 filed 값 채택."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = pl.DataFrame(
        [
            {
                "namespace": "us-gaap",
                "fp": "FY",
                "tag": "CommonStockDividendsPerShareDeclared",
                "val": 1.0,
                "fy": 2024,
                "filed": "2024-11-01",
            },
            {
                "namespace": "us-gaap",
                "fp": "FY",
                "tag": "CommonStockDividendsPerShareDeclared",
                "val": 1.1,
                "fy": 2024,
                "filed": "2025-02-01",
            },
        ]
    )
    rows = shareholderReturnRows(facts, "R")
    assert rows[0]["dps"] == 1.1  # 최신 filed
