"""scan 엔진의 글로벌 `latestYear = years[0]` 버그 수정 검증.

2026-04-23 확인: 한 종목이라도 2026 Q1 조기 제출하면 글로벌 latestYear=2026 이 되고
2025 자 데이터만 있는 수천 종목이 전부 탈락하던 현상 수정.
`filterLatestPerStock` 공용 유틸 도입 + profitability · growth per-stock loop 재구성.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _mockFinanceRow(stockCode: str, year: int, accountId: str, accountNm: str, amount: int, sj_div: str = "IS") -> dict:
    return {
        "stockCode": stockCode,
        "bsns_year": year,
        "account_id": accountId,
        "account_nm": accountNm,
        "thstrm_amount": amount,
        "sj_div": sj_div,
        "fs_nm": "연결재무제표",
    }


def test_filterLatestPerStock_keepsEachStocksOwnMaxYear():
    """A 종목은 2026 까지, B 는 2025 까지, C 는 2024 까지만 있을 때 각자 자기 max 만 통과."""
    from dartlab.scan.io.parquet import filterLatestPerStock

    rows = [
        {"stockCode": "A", "bsns_year": 2025, "val": 100},
        {"stockCode": "A", "bsns_year": 2026, "val": 110},  # A max
        {"stockCode": "B", "bsns_year": 2024, "val": 200},
        {"stockCode": "B", "bsns_year": 2025, "val": 220},  # B max
        {"stockCode": "C", "bsns_year": 2022, "val": 300},
        {"stockCode": "C", "bsns_year": 2024, "val": 330},  # C max
    ]
    df = pl.DataFrame(rows)
    result = filterLatestPerStock(df, scCol="stockCode", yearCol="bsns_year").sort("stockCode")
    assert result.height == 3
    years_per_stock = dict(zip(result["stockCode"].to_list(), result["bsns_year"].to_list()))
    assert years_per_stock == {"A": 2026, "B": 2025, "C": 2024}


def test_filterLatestPerStock_emptyReturnsEmpty():
    from dartlab.scan.io.parquet import filterLatestPerStock

    df = pl.DataFrame(schema={"stockCode": pl.Utf8, "bsns_year": pl.Int64})
    result = filterLatestPerStock(df)
    assert result.is_empty()


def test_filterLatestPerStock_missingColumnReturnsAsIs():
    from dartlab.scan.io.parquet import filterLatestPerStock

    df = pl.DataFrame({"other": [1, 2, 3]})
    result = filterLatestPerStock(df)
    assert result.equals(df)


def test_filterLatestPeriodPerStock_selects_latest_quarter_independent_of_row_order():
    from dartlab.scan.io.parquet import filterLatestPeriodPerStock

    frame = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "A"],
            "bsns_year": ["2025"] * 4,
            "reprt_nm": ["1분기", "4분기", "1분기", "4분기"],
            "account_id": ["Revenue", "Revenue", "Equity", "Equity"],
            "thstrm_amount": [100, 400, 50, 200],
        }
    )

    forward = filterLatestPeriodPerStock(frame)
    reverse = filterLatestPeriodPerStock(frame.reverse())

    assert forward["reprt_nm"].unique().to_list() == ["4분기"]
    assert forward.sort("account_id").equals(reverse.sort("account_id"))


def test_filterLatestPeriodPerStockLazy_matches_eager():
    from dartlab.scan.io.parquet import filterLatestPeriodPerStock, filterLatestPeriodPerStockLazy

    frame = pl.DataFrame(
        {
            "stockCode": ["A", "A", "A", "B", "B"],
            "bsns_year": ["2024", "2025", "2025", "2024", "2024"],
            "reprt_nm": ["4분기", "1분기", "4분기", "1분기", "3분기"],
            "value": [1, 2, 3, 4, 5],
        }
    )

    eager = filterLatestPeriodPerStock(frame).sort(["stockCode", "value"])
    lazy = filterLatestPeriodPerStockLazy(frame.lazy()).collect().sort(["stockCode", "value"])

    assert lazy.equals(eager)


def test_computeProfitability_uses_one_deterministic_period():
    from dartlab.scan.financial.profitability import _computeProfitability

    rows = []
    for quarter, revenue, op, net, assets, equity in [
        ("1분기", 10_000_000, 1_000_000, 800_000, 50_000_000, 5_000_000),
        ("4분기", 50_000_000, 10_000_000, 6_000_000, 100_000_000, 40_000_000),
    ]:
        for sj, aid, name, amount in [
            ("IS", "Revenue", "매출액", revenue),
            ("IS", "ProfitLossFromOperatingActivities", "영업이익", op),
            ("IS", "ProfitLoss", "당기순이익", net),
            ("BS", "Assets", "자산총계", assets),
            ("BS", "Equity", "자본총계", equity),
        ]:
            row = _mockFinanceRow("A", 2025, aid, name, amount, sj_div=sj)
            row["reprt_nm"] = quarter
            rows.append(row)

    forward = _computeProfitability(pl.DataFrame(rows), "stockCode")
    reverse = _computeProfitability(pl.DataFrame(list(reversed(rows))), "stockCode")

    assert forward.equals(reverse)
    assert forward.item(0, "opMargin") == 20.0
    assert forward.item(0, "roe") == 15.0


def test_computeGrowth_compares_the_same_quarter_across_years():
    from dartlab.scan.financial.growth import _computeGrowth

    rows = []
    for year, quarter, revenue in [
        (2022, "1분기", 100_000_000),
        (2022, "4분기", 400_000_000),
        (2025, "1분기", 200_000_000),
        (2025, "4분기", 800_000_000),
    ]:
        for aid, name, amount in [
            ("Revenue", "매출액", revenue),
            ("ProfitLossFromOperatingActivities", "영업이익", revenue // 10),
            ("ProfitLoss", "당기순이익", revenue // 12),
        ]:
            row = _mockFinanceRow("A", year, aid, name, amount)
            row["reprt_nm"] = quarter
            rows.append(row)

    forward = _computeGrowth(pl.DataFrame(rows), "stockCode")
    reverse = _computeGrowth(pl.DataFrame(list(reversed(rows))), "stockCode")

    assert forward.equals(reverse)
    assert forward.item(0, "revenue") == 800_000_000
    assert forward.item(0, "revenueCagr") == 26.0


def test_computeProfitability_noLongerDroppedByGlobalLatestYear():
    """엔진 버그: 전 샘플 중 단 1 종목만 2026, 나머지는 2025 자. 결과는 전종목이어야 함 (수정 전엔 1건만 남음)."""
    from dartlab.scan.financial.profitability import _computeProfitability

    rows = []
    # A: 2026 까지 있음 (조기 제출 종목 시뮬)
    for sj, aid, nm, amt in [
        ("IS", "Revenue", "매출액", 1_000_000),
        ("IS", "ProfitLossFromOperatingActivities", "영업이익", 100_000),
        ("IS", "ProfitLoss", "당기순이익", 80_000),
        ("BS", "Assets", "자산총계", 10_000_000),
        ("BS", "Equity", "자본총계", 5_000_000),
    ]:
        rows.append(_mockFinanceRow("A", 2026, aid, nm, amt, sj_div=sj))

    # B · C · D: 2025 까지만 있음 (정상 대다수 종목)
    for code in ["B", "C", "D"]:
        for sj, aid, nm, amt in [
            ("IS", "Revenue", "매출액", 2_000_000),
            ("IS", "ProfitLossFromOperatingActivities", "영업이익", 200_000),
            ("IS", "ProfitLoss", "당기순이익", 160_000),
            ("BS", "Assets", "자산총계", 20_000_000),
            ("BS", "Equity", "자본총계", 10_000_000),
        ]:
            rows.append(_mockFinanceRow(code, 2025, aid, nm, amt, sj_div=sj))

    df = pl.DataFrame(rows)
    result = _computeProfitability(df, "stockCode")

    # 수정 전엔 글로벌 latestYear=2026 → A 만 통과 (1건)
    # 수정 후엔 A=2026, B/C/D=2025 각자 자기 최신 → 4건 전부
    assert result.height == 4, f"expected 4 stocks, got {result.height}: {result}"
    codes = set(result["stockCode"].to_list())
    assert codes == {"A", "B", "C", "D"}


def test_computeProfitability_missingStockCodeReturnsSchemaEmpty():
    """부분 fixture / 불완전 fallback 은 컬럼 누락으로 크래시하지 않고 빈 스키마를 반환."""
    from dartlab.scan.financial.profitability import _computeProfitability

    df = pl.DataFrame(
        {
            "stock_code": ["005930"],
            "bsns_year": [2025],
            "account_id": ["Revenue"],
            "account_nm": ["매출액"],
            "thstrm_amount": [1_000_000],
        }
    )

    result = _computeProfitability(df, "stockCode")

    assert result.is_empty()
    assert result.columns == [
        "stockCode",
        "opMargin",
        "netMargin",
        "roe",
        "roa",
        "grade",
        "nonRecurring",
    ]


def test_scanProfitability_perFileFallbackNormalizesStockCode(tmp_path, monkeypatch):
    """개별 finance parquet 의 legacy `stock_code` 컬럼을 fallback 에서 `stockCode`로 정규화."""
    from dartlab.scan.financial import profitability

    finance_dir = tmp_path / "finance"
    finance_dir.mkdir()
    rows = []
    # 분모(매출·자본)는 1e6 원 materiality floor 위 현실 단위 사용 (floor 이하 = 비율 무의미 → None).
    for sj, aid, nm, amt in [
        ("IS", "Revenue", "매출액", 10_000_000),
        ("IS", "ProfitLossFromOperatingActivities", "영업이익", 1_000_000),
        ("IS", "ProfitLoss", "당기순이익", 800_000),
        ("BS", "Assets", "자산총계", 100_000_000),
        ("BS", "Equity", "자본총계", 50_000_000),
    ]:
        rows.append(_mockFinanceRow("005930", 2025, aid, nm, amt, sj_div=sj))
    df = pl.DataFrame(rows).rename({"stockCode": "stock_code"})
    df.write_parquet(finance_dir / "005930.parquet")

    def fakeDataDir(category: str):
        assert category == "finance"
        return finance_dir

    monkeypatch.setattr("dartlab.core.dataLoader._dataDir", fakeDataDir)

    result = profitability._scanPerFile()

    assert result.height == 1
    assert result.item(0, "stockCode") == "005930"
    assert result.item(0, "opMargin") == 10.0


def test_computeGrowth_perStockYearsNotGlobal():
    """CAGR 계산이 각 종목의 자기 최신·기준 연도 pair 를 쓰는지 검증."""
    from dartlab.scan.financial.growth import _computeGrowth

    rows = []
    # A: 2023, 2026 (4년 gap → baseYear=2023)
    rows.append(_mockFinanceRow("A", 2023, "Revenue", "매출액", 100_000))
    rows.append(_mockFinanceRow("A", 2023, "ProfitLossFromOperatingActivities", "영업이익", 10_000))
    rows.append(_mockFinanceRow("A", 2023, "ProfitLoss", "당기순이익", 8_000))
    rows.append(_mockFinanceRow("A", 2026, "Revenue", "매출액", 200_000))
    rows.append(_mockFinanceRow("A", 2026, "ProfitLossFromOperatingActivities", "영업이익", 22_000))
    rows.append(_mockFinanceRow("A", 2026, "ProfitLoss", "당기순이익", 16_000))

    # B: 2022, 2025 (3년 gap → baseYear=2022)
    rows.append(_mockFinanceRow("B", 2022, "Revenue", "매출액", 500_000))
    rows.append(_mockFinanceRow("B", 2022, "ProfitLossFromOperatingActivities", "영업이익", 50_000))
    rows.append(_mockFinanceRow("B", 2022, "ProfitLoss", "당기순이익", 40_000))
    rows.append(_mockFinanceRow("B", 2025, "Revenue", "매출액", 800_000))
    rows.append(_mockFinanceRow("B", 2025, "ProfitLossFromOperatingActivities", "영업이익", 90_000))
    rows.append(_mockFinanceRow("B", 2025, "ProfitLoss", "당기순이익", 70_000))

    df = pl.DataFrame(rows)
    result = _computeGrowth(df, "stockCode")

    # 수정 전엔 글로벌 latestYear=2026 · baseYear=2023 → B 의 2026 자가 없어 baseSub 비어 결과 0 건
    # 수정 후엔 A/B 각자 자기 연도 pair 로 계산 → 2 건
    assert result.height == 2, f"expected 2 stocks, got {result.height}: {result}"
    codes = set(result["stockCode"].to_list())
    assert codes == {"A", "B"}
    # A 는 nYears=3 (2026-2023), B 는 nYears=3 (2025-2022)
    yrs_per_stock = dict(zip(result["stockCode"].to_list(), result["years"].to_list()))
    assert yrs_per_stock["A"] == 3
    assert yrs_per_stock["B"] == 3


def test_computeGrowth_missingStockCodeReturnsSchemaEmpty():
    """부분 fixture / 불완전 fallback 은 컬럼 누락으로 크래시하지 않고 빈 스키마를 반환."""
    from dartlab.scan.financial.growth import _computeGrowth

    df = pl.DataFrame(
        {
            "stock_code": ["005930"],
            "bsns_year": [2025],
            "account_id": ["Revenue"],
            "account_nm": ["매출액"],
            "thstrm_amount": [1_000_000],
        }
    )

    result = _computeGrowth(df, "stockCode")

    assert result.is_empty()
    assert result.columns == [
        "stockCode",
        "revenue",
        "revenueCagr",
        "opIncomeCagr",
        "netIncomeCagr",
        "years",
        "grade",
        "pattern",
    ]


def test_scanGrowth_perFileFallbackNormalizesStockCode(tmp_path, monkeypatch):
    """개별 finance parquet 의 legacy `stock_code` 컬럼을 fallback 에서 `stockCode`로 정규화."""
    from dartlab.scan.financial import growth

    finance_dir = tmp_path / "finance"
    finance_dir.mkdir()
    rows = [
        _mockFinanceRow("005930", 2022, "Revenue", "매출액", 100_000),
        _mockFinanceRow("005930", 2022, "ProfitLossFromOperatingActivities", "영업이익", 10_000),
        _mockFinanceRow("005930", 2022, "ProfitLoss", "당기순이익", 8_000),
        _mockFinanceRow("005930", 2025, "Revenue", "매출액", 150_000),
        _mockFinanceRow("005930", 2025, "ProfitLossFromOperatingActivities", "영업이익", 20_000),
        _mockFinanceRow("005930", 2025, "ProfitLoss", "당기순이익", 12_000),
    ]
    df = pl.DataFrame(rows).rename({"stockCode": "stock_code"})
    df.write_parquet(finance_dir / "005930.parquet")

    def fakeDataDir(category: str):
        assert category == "finance"
        return finance_dir

    monkeypatch.setattr("dartlab.core.dataLoader._dataDir", fakeDataDir)

    result = growth._scanPerFile()

    assert result.height == 1
    assert result.item(0, "stockCode") == "005930"


def _yearRows(year: str, companies: int, rowsEach: int, value: str = "100") -> list[dict]:
    """한 해에 `companies` 종목이 각각 `rowsEach` 행씩 낸 mock 데이터."""
    return [{"stockCode": f"{i:06d}", "year": year, "val": value} for i in range(companies) for _ in range(rowsEach)]


def test_findLatestYear_skipsYearStillBeingFiled():
    """진행 중인 해가 절대 하한을 넘어도, 이미 끝난 해보다 얇으면 고르지 않는다.

    실측 사고: employee 의 급여 항목이 2025 년 2,655 종목인데 2026 년은 1 분기 보고서뿐이라
    1,674 종목이었다. 둘 다 하한 500 을 넘어서 옛 규칙이 2026 을 골랐고, 그 해에 아직 안 낸
    약 1,000 종목이 단면에서 통째로 빠졌다. 소비자 쪽에서는 값이 없는 것과 회사가 원래
    자료를 안 내는 것이 구분되지 않았다.
    """
    from dartlab.scan.io.parquet import findLatestYear

    raw = pl.DataFrame(_yearRows("2025", 1000, 1) + _yearRows("2026", 600, 1))

    assert findLatestYear(raw, "val", 500) == "2025"


def test_findLatestYear_measuresCompaniesNotRows():
    """단면의 넓이는 행수가 아니라 종목수로 잰다.

    한 종목이 성별·구분별로 여러 행을 내므로 행수로 세면 종목이 더 많은 해가 도리어 얇아
    보인다. 여기서 2025 는 종목이 더 많고(800 대 700) 행은 더 적다(800 대 2100).
    """
    from dartlab.scan.io.parquet import findLatestYear

    raw = pl.DataFrame(_yearRows("2024", 700, 3) + _yearRows("2025", 800, 1))

    assert findLatestYear(raw, "val", 500) == "2025"


def test_findLatestYear_stillHonorsAbsoluteFloor():
    """모든 해가 절대 하한에 못 미치면 None (상대 기준이 하한을 무르게 만들지 않는다)."""
    from dartlab.scan.io.parquet import findLatestYear

    raw = pl.DataFrame(_yearRows("2024", 100, 1) + _yearRows("2025", 90, 1))

    assert findLatestYear(raw, "val", 500) is None
