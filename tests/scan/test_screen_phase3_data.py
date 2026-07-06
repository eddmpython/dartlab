"""Phase 3 시계열·상대 define 노드 실 데이터 회귀 (requires_data).

합성 유닛은 ``test_screen_define.py`` 가 결정적으로 커버한다. 여기서는 실
``finance.parquet`` (연간 격자) + ``listing`` 업종으로 ``_loadFieldSeries`` ·
percentile · 업종 join · 데모 스크린이 실제로 종목을 산출하는지 확인한다.
메모리 안전: scanAccount 는 finance.parquet 단일 fast-path (Company 객체 아님).
"""

from __future__ import annotations

import polars as pl
import pytest

import dartlab
import dartlab.scan.builders.kr.report.fields as F

pytestmark = [pytest.mark.requires_data, pytest.mark.heavy]


def test_industry_map_covers_universe():
    imap = F._industryMap()
    assert imap.height > 2000  # 전상장사 업종 매핑
    assert imap["_grp"].n_unique() > 50
    assert set(imap.columns) == {"stockCode", "_grp"}


def test_field_series_yearly_grid():
    series, k = F._loadFieldSeries("finance.account.operating_profit", 3)
    assert k >= 2 and "stockCode" in series.columns
    assert {f"_t{i}" for i in range(k)}.issubset(set(series.columns))
    assert series.height > 1000


def test_percentile_monotonic_with_raw():
    # 백분위는 원 지표의 단조 변환 → 순위 상관 ~1.0.
    df, unit = F._evalRelativeNode("p", {"op": "percentile", "field": "finance.ratio.roe"}, {"_axisCache": {}}, {}, {})
    assert unit == "백분위"
    raw = F._loadFieldValues("finance.ratio.roe", {"_axisCache": {}})
    joined = (
        df.join(raw, on="stockCode", how="inner")
        .drop_nulls()
        .with_columns(pl.col("@p").rank().alias("_rp"), pl.col("finance.ratio.roe").rank().alias("_rr"))
    )
    corr = joined.select(pl.corr("_rp", "_rr"))[0, 0]
    assert corr is not None and corr > 0.99


def test_zscore_centered():
    # 전체 유니버스 z-score 평균 ~0.
    df, _ = F._evalRelativeNode("z", {"op": "zscore", "field": "finance.ratio.debtRatio"}, {"_axisCache": {}}, {}, {})
    mean = df.select(pl.col("@z").mean())[0, 0]
    assert mean is not None and abs(mean) < 0.05


def test_demo_screen_runs():
    out = dartlab.scan("screen", "resilientCompounders")
    assert out.height > 0
    cols = set(out.columns)
    assert "@opMin3y" in cols and "@roeIndPct" in cols  # 시계열·상대 파생 실재
    # 3년 연속 흑자 게이트: min 영업이익 > 0
    assert out.select((pl.col("@opMin3y") > 0).all())[0, 0]
