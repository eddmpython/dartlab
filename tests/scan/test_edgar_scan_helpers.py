"""EDGAR scan helpers의 batch 호출과 회사별 공통 기간 계약.

회귀 가드 2건:
  1. 계정 수만큼 전체 shard를 다시 읽지 않고 ``scanAccounts``를 한 번 호출한다.
  2. 계정마다 다른 최신 기간을 고르지 않고 회사별 동일한 최신·전기 기간을 쓴다.

monkeypatch 로 scanAccounts 를 합성 대체해 실제 parquet 없이 계약만 검증한다.
"""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_scan_edgar_accounts_batches_and_aligns_company_periods(monkeypatch: pytest.MonkeyPatch) -> None:
    """batch 1회와 회사별 동일 기간을 보장한다."""
    import dartlab.scan.builders.edgar.helpers as h

    calls: list[tuple[list[str], str]] = []
    frames = {
        "sales": pl.DataFrame(
            {
                "stockCode": ["A", "B"],
                "corpName": ["A Inc", "B Inc"],
                "2024": [100.0, None],
                "2023": [90.0, 200.0],
                "2022": [80.0, 180.0],
            }
        ),
        "net_profit": pl.DataFrame(
            {
                "stockCode": ["A", "B", "C"],
                "corpName": ["A Inc", "B Inc", "C Inc"],
                "2023": [9.0, 20.0, 30.0],
                "2022": [8.0, 18.0, 25.0],
            }
        ),
    }

    def fakeScanAccounts(snakeIds: list[str], *, freq: str = "Q") -> dict[str, pl.DataFrame]:
        calls.append((snakeIds, freq))
        return {snakeId: frames[snakeId] for snakeId in snakeIds}

    monkeypatch.setattr(
        "dartlab.providers.edgar.finance.scanAccount.scanAccounts",
        fakeScanAccounts,
    )

    df = h.scanEdgarAccounts(["sales", "net_profit"])

    assert calls == [(["sales", "net_profit"], "Y")]
    rows = {row["stockCode"]: row for row in df.iter_rows(named=True)}
    assert set(rows) == {"A", "B", "C"}
    assert rows["A"]["sales"] == 100.0
    assert rows["A"]["net_profit"] is None
    assert rows["A"]["sales_prev"] == 90.0
    assert rows["A"]["net_profit_prev"] == 9.0
    assert rows["B"]["sales"] == 200.0
    assert rows["B"]["net_profit"] == 20.0
    assert rows["C"]["sales"] is None
    assert rows["C"]["net_profit"] == 30.0


def test_edgar_profitability_rejects_tiny_denominators_and_extreme_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """미소 분모와 비현실적 비율이 상위 수익성 등급을 만들지 못한다."""

    import dartlab.scan.builders.edgar.scan as scanModule

    source = pl.DataFrame(
        {
            "stockCode": ["GOOD", "TINY", "EXTREME"],
            "corpName": ["Good Inc", "Tiny Inc", "Extreme Inc"],
            "sales": [10_000_000.0, 1000.0, 10_000_000.0],
            "sales_prev": [9_000_000.0, 900.0, 9_000_000.0],
            "operating_profit": [2_000_000.0, 500.0, 20_000_000.0],
            "operating_profit_prev": [1_500_000.0, 400.0, 10_000_000.0],
            "net_profit": [1_000_000.0, 400.0, 60_000_000.0],
            "net_profit_prev": [900_000.0, 300.0, 30_000_000.0],
            "total_assets": [20_000_000.0, 5000.0, 50_000_000.0],
            "total_assets_prev": [18_000_000.0, 4500.0, 40_000_000.0],
            "total_stockholders_equity": [5_000_000.0, 2000.0, 2_000_000.0],
            "total_stockholders_equity_prev": [4_000_000.0, 1800.0, 1_500_000.0],
        }
    )
    monkeypatch.setattr(scanModule, "scanEdgarAccounts", lambda *_args, **_kwargs: source)

    result = scanModule._scanProfitability()
    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}

    assert rows["GOOD"]["opMargin"] == 20.0
    assert rows["GOOD"]["roe"] == 20.0
    assert rows["GOOD"]["grade"] == "우수"
    assert rows["TINY"]["opMargin"] is None
    assert rows["TINY"]["roe"] is None
    assert rows["TINY"]["grade"] == "자료부족"
    assert rows["EXTREME"]["opMargin"] is None
    assert rows["EXTREME"]["netMargin"] is None
    assert rows["EXTREME"]["roe"] is None
    assert rows["EXTREME"]["roa"] is None
    assert rows["EXTREME"]["grade"] == "자료부족"


def test_edgar_growth_rejects_tiny_baselines_and_extreme_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """미소 전기값과 극단 YoY를 성장 신호로 분류하지 않는다."""

    import dartlab.scan.builders.edgar.scan as scanModule

    source = pl.DataFrame(
        {
            "stockCode": ["GOOD", "TINY", "EXTREME"],
            "corpName": ["Good Inc", "Tiny Inc", "Extreme Inc"],
            "sales": [10_000_000.0, 100_000.0, 30_000_000.0],
            "sales_prev": [5_000_000.0, 1000.0, 2_000_000.0],
            "operating_profit": [3_000_000.0, 50_000.0, 30_000_000.0],
            "operating_profit_prev": [1_500_000.0, 500.0, 2_000_000.0],
            "net_profit": [2_000_000.0, 40_000.0, 30_000_000.0],
            "net_profit_prev": [1_200_000.0, 400.0, 2_000_000.0],
        }
    )
    monkeypatch.setattr(scanModule, "scanEdgarAccounts", lambda *_args, **_kwargs: source)

    result = scanModule._scanGrowth()
    rows = {row["stockCode"]: row for row in result.iter_rows(named=True)}

    assert rows["GOOD"]["revenueYoy"] == 100.0
    assert rows["GOOD"]["pattern"] == "고성장"
    assert rows["TINY"]["revenueYoy"] is None
    assert rows["TINY"]["opYoy"] is None
    assert rows["TINY"]["niYoy"] is None
    assert rows["TINY"]["pattern"] == "자료부족"
    assert rows["EXTREME"]["revenueYoy"] is None
    assert rows["EXTREME"]["opYoy"] is None
    assert rows["EXTREME"]["niYoy"] is None
    assert rows["EXTREME"]["pattern"] == "자료부족"
