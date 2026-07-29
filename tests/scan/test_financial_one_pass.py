"""KR 최신기간 재무축의 공통 one-pass 계정 집계 회귀."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _financeRows() -> pl.DataFrame:
    common = {
        "stockCode": "A",
        "bsns_year": "2025",
        "reprt_nm": "4분기",
        "fs_nm": "연결재무제표",
    }
    accounts = [
        ("IS", "Revenue", "매출액", "1000000000"),
        ("IS", "CostOfSales", "매출원가", "500000000"),
        ("IS", "ProfitLoss", "당기순이익", "20000000"),
        ("BS", "Assets", "자산총계", "400000000"),
        ("BS", "CurrentAssets", "유동자산", "200000000"),
        ("BS", "CurrentLiabilities", "유동부채", "100000000"),
        ("BS", "Inventories", "재고자산", "100000000"),
        ("BS", "ShortTermTradeReceivables", "매출채권", "200000000"),
        ("BS", "PropertyPlantAndEquipment", "유형자산", "250000000"),
        ("BS", "TradeAndOtherCurrentPayables", "매입채무", "50000000"),
        ("CF", "CashFlowsFromUsedInOperatingActivities", "영업활동현금흐름", "30000000"),
        ("CF", "CashFlowsFromUsedInInvestingActivities", "투자활동현금흐름", "-10000000"),
        ("CF", "CashFlowsFromUsedInFinancingActivities", "재무활동현금흐름", "-5000000"),
    ]
    rows = [
        {
            **common,
            "sj_div": statement,
            "account_id": accountId,
            "account_nm": accountName,
            "thstrm_amount": amount,
        }
        for statement, accountId, accountName, amount in accounts
    ]
    rows.append(
        {
            **common,
            "reprt_nm": "1분기",
            "sj_div": "IS",
            "account_id": "Revenue",
            "account_nm": "매출액",
            "thstrm_amount": "9999999999",
        }
    )
    return pl.DataFrame(rows)


def test_latest_financial_axes_use_same_company_period(tmp_path: Path) -> None:
    """현금흐름, 품질, 유동성, 효율성이 같은 회사 Q4 계정을 사용한다."""

    from dartlab.scan.financial import cashflow, efficiency, liquidity, quality

    path = tmp_path / "finance.parquet"
    _financeRows().write_parquet(path)

    cash = cashflow._scanFromMerged(path).row(0, named=True)
    earningsQuality = quality._scanFromMerged(path).row(0, named=True)
    liquid = liquidity._scanFromMerged(path).row(0, named=True)
    efficient = efficiency._scanFromMerged(path).row(0, named=True)

    assert cash == {
        "stockCode": "A",
        "ocf": 30000000,
        "icf": -10000000,
        "finCf": -5000000,
        "fcf": 20000000,
        "pattern": "성장투자형",
    }
    assert earningsQuality["accrualRatio"] == -0.025
    assert earningsQuality["cfToNi"] == 1.5
    assert earningsQuality["grade"] == "양호"
    assert liquid["currentRatio"] == 200.0
    assert liquid["quickRatio"] == 100.0
    assert liquid["grade"] == "우수"
    assert efficient["assetTurnover"] == 2.5
    assert efficient["invTurnover"] == 5.0
    assert efficient["ccc"] == 110.0
    assert efficient["grade"] == "양호"


def test_dividend_trend_joins_company_selected_year(monkeypatch: pytest.MonkeyPatch) -> None:
    """시장 기준연도에 없는 회사도 자기 최신연도의 수익률과 성향을 붙인다."""

    import dartlab.scan.dividendTrend as dividendTrend

    raw = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "B", "B", "B"],
            "year": ["2025", "2025", "2025", "2024", "2024", "2024"],
            "quarter": ["4분기"] * 6,
            "se": [
                "주당 현금배당금(원)",
                "현금배당수익률(%)",
                "(연결)현금배당성향(%)",
                "주당 현금배당금(원)",
                "현금배당수익률(%)",
                "(연결)현금배당성향(%)",
            ],
            "thstrm": ["100", "2.5", "30", "50", "1.5", "25"],
            "frmtrm": ["80", None, None, "40", None, None],
            "lwfr": ["60", None, None, "30", None, None],
            "stock_knd": ["보통주", "보통주", None, "보통주", "보통주", None],
        }
    )
    monkeypatch.setattr(dividendTrend, "scanParquets", lambda *_args, **_kwargs: raw)

    result = dividendTrend.scanDividendTrend(verbose=False)
    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}

    assert rows["A"]["yieldCurrent"] == 2.5
    assert rows["A"]["payoutRatio"] == 30.0
    assert rows["B"]["yieldCurrent"] == 1.5
    assert rows["B"]["payoutRatio"] == 25.0
    assert rows["B"]["pattern"] == "연속증가"
