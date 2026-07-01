"""EDGAR scan report 빌더 — 3관점(주주환원·부채만기·임원보수)을 XBRL facts 에서 정확히 뽑는지 +
태그 폴백 머지 + ecd 연도 도출. 합성 facts → 네트워크/OOM 무관.
"""

from __future__ import annotations

from datetime import date

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


def test_buyback_amount_qty_and_total_payout():
    """자사주매입 금액·소각주식수 채움 + totalPayoutPct=(배당+매입)/순이익 — 미국 자본환원 핵심."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts(
        [
            {"tag": "PaymentsOfDividendsCommonStock", "val": 15_000_000.0, "fy": 2024},
            {"tag": "PaymentsForRepurchaseOfCommonStock", "val": 45_000_000.0, "fy": 2024},
            {"tag": "StockRepurchasedAndRetiredDuringPeriodShares", "val": 135_000.0, "fy": 2024},
            {"tag": "NetIncomeLoss", "val": 100_000_000.0, "fy": 2024},
        ]
    )
    rows = shareholderReturnRows(facts, "AAPL")
    assert len(rows) == 1
    r = rows[0]
    assert r["buybackAmount"] == 45_000_000.0
    assert r["buybackQty"] == 135_000.0  # 소각 주식수(treasury 없어도)
    assert r["payoutPct"] == 15.0  # 배당만 15%
    assert r["totalPayoutPct"] == 60.0  # (15+45)/100 × 100


def test_buyback_only_year_included():
    """배당 없이 자사주매입만 있는 연도도 포함 — 무배당 성장주의 buyback 스토리."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts([{"tag": "PaymentsForRepurchaseOfCommonStock", "val": 9_000_000.0, "fy": 2023}])
    rows = shareholderReturnRows(facts, "GROWTH")
    assert len(rows) == 1
    assert rows[0]["buybackAmount"] == 9_000_000.0
    assert rows[0]["totalDividend"] is None


def test_polluted_fiscal_year_dropped():
    """오염 fy(엑셀 시리얼·오타 미래연도)는 제외. 패널에 '43830년' 류 표시 차단."""
    from dartlab.scan.builders.edgar.report.build import shareholderReturnRows

    facts = _facts(
        [
            {"tag": "CommonStockDividendsPerShareDeclared", "val": 1.0, "fy": 2024},
            {"tag": "CommonStockDividendsPerShareDeclared", "val": 9.0, "fy": 43830},  # 오염 fy
            {"tag": "PaymentsOfDividendsCommonStock", "val": 500.0, "fy": 2107},  # 오타 미래연도
        ]
    )
    years = {r["year"] for r in shareholderReturnRows(facts, "WTBA")}
    assert years == {"2024"}  # 1990~2035 밖은 드롭


def test_debt_maturity_ladder():
    """부채 만기 사다리 y1~y5·after5·총장기부채 연도별 추출."""
    from dartlab.scan.builders.edgar.report.build import debtMaturityRows

    facts = _facts(
        [
            {"tag": "LongTermDebtMaturitiesRepaymentsOfPrincipalInNextTwelveMonths", "val": 12.0, "fy": 2024},
            {"tag": "LongTermDebtMaturitiesRepaymentsOfPrincipalInYearTwo", "val": 10.0, "fy": 2024},
            {"tag": "LongTermDebtMaturitiesRepaymentsOfPrincipalAfterYearFive", "val": 49.0, "fy": 2024},
            {"tag": "LongTermDebt", "val": 90.0, "fy": 2024},
        ]
    )
    rows = debtMaturityRows(facts, "AAPL")
    assert len(rows) == 1
    r = rows[0]
    assert r["y1"] == 12.0
    assert r["y2"] == 10.0
    assert r["y5"] is None  # 미공시 버킷은 null
    assert r["after5"] == 49.0
    assert r["longTermDebt"] == 90.0


def test_debt_maturity_empty_when_no_buckets():
    """만기 버킷 전무면 빈 list(장기부채만 있어도 사다리 없으면 제외)."""
    from dartlab.scan.builders.edgar.report.build import debtMaturityRows

    facts = _facts([{"tag": "LongTermDebt", "val": 50.0, "fy": 2024}])
    assert debtMaturityRows(facts, "X") == []


def test_exec_comp_from_ecd_year_from_end():
    """임원보수 — ecd(PvP) CEO·평균NEO 보수, fy 없어 기간 end 의 연도로 키."""
    from dartlab.scan.builders.edgar.report.build import execCompRows

    facts = pl.DataFrame(
        [
            {
                "namespace": "ecd",
                "tag": "PeoTotalCompAmt",
                "val": 29_000_000.0,
                "fp": None,
                "fy": None,
                "filed": "2026-04-01",
                "end": date(2026, 1, 31),
            },
            {
                "namespace": "ecd",
                "tag": "NonPeoNeoAvgTotalCompAmt",
                "val": 25_000_000.0,
                "fp": None,
                "fy": None,
                "filed": "2026-04-01",
                "end": date(2026, 1, 31),
            },
            {
                "namespace": "ecd",
                "tag": "TotalShareholderRtnAmt",
                "val": 272.0,
                "fp": None,
                "fy": None,
                "filed": "2026-04-01",
                "end": date(2026, 1, 31),
            },
        ]
    )
    rows = execCompRows(facts, "WMT")
    assert len(rows) == 1
    r = rows[0]
    assert r["year"] == "2026"  # end 연도
    assert r["ceoTotalComp"] == 29_000_000.0
    assert r["neoAvgTotalComp"] == 25_000_000.0
    assert r["companyTsr"] == 272.0


def test_exec_comp_empty_without_ecd():
    """ecd 미제출사(us-gaap 만)는 빈 list — proxy 인라인 XBRL 부재."""
    from dartlab.scan.builders.edgar.report.build import execCompRows

    facts = _facts([{"tag": "NetIncomeLoss", "val": 5.0, "fy": 2024}]).with_columns(
        pl.lit(None).cast(pl.Date).alias("end")
    )
    assert execCompRows(facts, "MSFT") == []
