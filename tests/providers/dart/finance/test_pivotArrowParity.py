"""Phase B — ``_pivotToSeries`` (DuckDB) vs ``_pivotToSeriesLegacy`` parity.

각 cell 의 값이 ``math.isclose(rel_tol=1e-9)`` 로 일치하는지 검증.
또 snake_id set / sj_div 분류도 동일해야 한다.

ledger / log 출력은 비교 안 함 (parity 외).
"""

from __future__ import annotations

import math

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def _sampleLongDf() -> tuple[pl.DataFrame, list[str]]:
    """priority tie / nonstd_ / period 다중 시나리오를 포함한 sample long frame."""
    rows = [
        # ── BS / 2023-Q1 / 자산총계 ── ifrs-full_assets (priority 1) + dart_AssetsTotal (priority 2)
        # → priority < 로 1 우선
        {
            "sj_div": "BS",
            "account_id": "ifrs-full_Assets",
            "account_nm": "자산총계",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 1000.0,
        },
        {
            "sj_div": "BS",
            "account_id": "dart_AssetsTotal",
            "account_nm": "자산총계",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 999.0,
        },
        # ── IS / 2023-Q1 / 매출 ── ifrs-full_Revenue (top-level priority 0) + ifrs-full_OtherRevenue (1)
        {
            "sj_div": "IS",
            "account_id": "ifrs-full_Revenue",
            "account_nm": "매출",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 500.0,
        },
        {
            "sj_div": "IS",
            "account_id": "ifrs-full_OtherRevenue",
            "account_nm": "매출",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 499.0,
        },
        # ── CIS → IS 정규화 ──
        {
            "sj_div": "CIS",
            "account_id": "ifrs-full_ProfitLoss",
            "account_nm": "당기순이익",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 100.0,
        },
        # ── CF ──
        {
            "sj_div": "CF",
            "account_id": "ifrs-full_CashFlowsFromUsedInOperatingActivities",
            "account_nm": "영업활동현금흐름",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 200.0,
        },
        # ── nonstd fallback ── account_id 빈 + 한글명만
        {
            "sj_div": "BS",
            "account_id": "",
            "account_nm": "회사사내계정X",
            "bsns_year": 2023,
            "reprt_nm": "1분기",
            "_normalized_amount": 50.0,
        },
        # ── 다음 분기 (period 다중) ──
        {
            "sj_div": "BS",
            "account_id": "ifrs-full_Assets",
            "account_nm": "자산총계",
            "bsns_year": 2023,
            "reprt_nm": "2분기",
            "_normalized_amount": 1100.0,
        },
    ]
    df = pl.DataFrame(rows)
    periods = ["2023-Q1", "2023-Q2"]
    return df, periods


def _flattenSeries(series: dict) -> dict:
    """{sjDiv: {snakeId: list}} → {(sjDiv, snakeId, idx): value} 평탄화."""
    out = {}
    for sjDiv, inner in series.items():
        for snakeId, values in inner.items():
            for i, v in enumerate(values):
                out[(sjDiv, snakeId, i)] = v
    return out


def test_pivot_parity_basic() -> None:
    """샘플 long DF 에서 legacy vs new 결과 cell 동일."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries, _pivotToSeriesLegacy

    df, periods = _sampleLongDf()

    legacy = _pivotToSeriesLegacy(df, periods)
    # legacy 본체에 _fillSnakeIdGaps + sortSeries 가 포함 안 됨 (new 가 호출)
    # parity 하려면 동일 post-process 적용.
    from dartlab.core.utils.ordering import sortSeries
    from dartlab.providers.dart.finance.pivot import _fillSnakeIdGaps

    _fillSnakeIdGaps(legacy)
    sortSeries(legacy)

    new = _pivotToSeries(df, periods)

    # sj_div 분류 동일
    assert set(legacy.keys()) == set(new.keys()) == {"BS", "IS", "CF"}

    # snake_id set 동일 (sj_div 별)
    for sjDiv in ("BS", "IS", "CF"):
        assert set(legacy[sjDiv].keys()) == set(new[sjDiv].keys()), (
            f"sj_div={sjDiv} snake_id mismatch: legacy={set(legacy[sjDiv].keys())} vs new={set(new[sjDiv].keys())}"
        )

    # cell 값 동일 (None 도 일치, float 은 rel_tol=1e-9)
    legacyFlat = _flattenSeries(legacy)
    newFlat = _flattenSeries(new)
    assert set(legacyFlat.keys()) == set(newFlat.keys())
    for key, legacyVal in legacyFlat.items():
        newVal = newFlat[key]
        if legacyVal is None:
            assert newVal is None, f"{key}: legacy=None, new={newVal}"
        else:
            assert newVal is not None, f"{key}: legacy={legacyVal}, new=None"
            assert math.isclose(legacyVal, newVal, rel_tol=1e-9), f"{key}: legacy={legacyVal}, new={newVal}"


def test_pivot_priority_top_level_wins() -> None:
    """``ifrs-full_Revenue`` (priority 0) 가 ``ifrs-full_OtherRevenue`` (priority 1) 보다 우선."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries

    df, periods = _sampleLongDf()
    new = _pivotToSeries(df, periods)

    # mapper 매핑 가정 — ifrs-full_Revenue → sales 또는 revenue
    # 그 셀의 값이 500 (priority 0) 이어야 (499 가 아니라)
    # 매핑 결과에 의존하지 않는 검증: priority 0 의 값이 살아남는지만 확인.
    found = False
    for snakeId, values in new["IS"].items():
        if values[0] is not None and math.isclose(values[0], 500.0, rel_tol=1e-9):
            found = True
            break
    assert found, f"priority 0 (Revenue=500) 우선 적용 실패. IS: {new['IS']}"


def test_pivot_cis_collapses_to_is() -> None:
    """``CIS`` row 는 ``IS`` 로 정규화."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries

    df, periods = _sampleLongDf()
    new = _pivotToSeries(df, periods)

    # CIS 키 없어야 함
    assert "CIS" not in new
    # ProfitLoss 가 IS 에 들어가 있어야 (100 값)
    found = False
    for snakeId, values in new["IS"].items():
        if values[0] is not None and math.isclose(values[0], 100.0, rel_tol=1e-9):
            found = True
            break
    assert found, "CIS → IS 정규화 실패"


def test_pivot_nonstd_fallback() -> None:
    """account_id 비어있고 account_nm 만 있는 row 는 nonstd_ 접두로 살아남음."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries

    df, periods = _sampleLongDf()
    new = _pivotToSeries(df, periods)

    nonstdKeys = [k for k in new["BS"] if k.startswith("nonstd_")]
    assert nonstdKeys, f"nonstd_ fallback 미발생: BS={list(new['BS'].keys())}"
    # 값 검증 — 50.0
    matched = False
    for k in nonstdKeys:
        if new["BS"][k][0] is not None and math.isclose(new["BS"][k][0], 50.0, rel_tol=1e-9):
            matched = True
            break
    assert matched


def test_pivot_empty_input() -> None:
    """빈 DataFrame → 빈 series dict (3 sj_div 키만 존재)."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries

    df = pl.DataFrame(
        {
            "sj_div": [],
            "account_id": [],
            "account_nm": [],
            "bsns_year": [],
            "reprt_nm": [],
            "_normalized_amount": [],
        },
        schema={
            "sj_div": pl.Utf8,
            "account_id": pl.Utf8,
            "account_nm": pl.Utf8,
            "bsns_year": pl.Int64,
            "reprt_nm": pl.Utf8,
            "_normalized_amount": pl.Float64,
        },
    )
    periods = ["2023-Q1"]
    new = _pivotToSeries(df, periods)
    assert new["BS"] == {}
    assert new["IS"] == {}
    assert new["CF"] == {}


@pytest.mark.parametrize(
    "rows",
    [
        [
            {
                "sj_div": "BS",
                "account_id": "ifrs-full_Assets",
                "account_nm": "자산총계",
                "bsns_year": 2024,
                "reprt_nm": "1분기",
                "_normalized_amount": None,
            },
            {
                "sj_div": "BS",
                "account_id": "dart_AssetsTotal",
                "account_nm": "자산총계",
                "bsns_year": 2024,
                "reprt_nm": "1분기",
                "_normalized_amount": 900.0,
            },
        ],
        [
            {
                "sj_div": "BS",
                "account_id": "ifrs-full_Assets",
                "account_nm": "자산총계",
                "bsns_year": 2024,
                "reprt_nm": "1분기",
                "_normalized_amount": None,
            },
            {
                "sj_div": "BS",
                "account_id": "ifrs-full_Assets",
                "account_nm": "자산총계",
                "bsns_year": 2024,
                "reprt_nm": "1분기",
                "_normalized_amount": 800.0,
            },
        ],
    ],
)
def test_pivot_prefers_real_value_over_null_before_priority(rows: list[dict]) -> None:
    """legacy처럼 우선순위가 높은 null보다 실제 값을 보존한다."""
    from dartlab.providers.dart.finance.pivot import _pivotToSeries, _pivotToSeriesLegacy

    frame = pl.DataFrame(rows, infer_schema_length=None)
    periods = ["2024-Q1"]

    assert _pivotToSeries(frame, periods) == _pivotToSeriesLegacy(frame, periods)
