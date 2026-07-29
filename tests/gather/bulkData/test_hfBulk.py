"""dartlab.gather.bulkData.hfBulk mirror 슬롯 — smoke import (P-G7.2).

룰 7 (src↔tests 1:1 mirror) 만족용 placeholder. 본격 단위 테스트는 후속.
"""

from __future__ import annotations

import importlib

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_smoke_import() -> None:
    """``dartlab.gather.bulkData.hfBulk`` 모듈 import 가능 — 모듈 구조 회귀 차단."""
    importlib.import_module("dartlab.gather.bulkData.hfBulk")


def _twoCompanyYear(year: int) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "BAS_DD": ["20260102", "20260102", "20260103"],
            "ISU_CD": ["005930", "000660", "035420"],
            "TDD_CLSPRC": [70_000, 200_000, 180_000],
            "ACC_TRDVOL": [100, 200, 300],
        }
    )


def test_loadFiltered_filters_many_codes_and_projects_columns(monkeypatch: pytest.MonkeyPatch) -> None:
    """다종목 필터는 연도 프레임에서 먼저 줄이고 식별자와 요청 컬럼만 반환한다."""
    from dartlab.gather.bulkData import hfBulk

    monkeypatch.setattr(hfBulk, "_loadYear", _twoCompanyYear)

    result = hfBulk.loadFiltered(
        stockCodes=["005930", "000660", "005930"],
        columns=["TDD_CLSPRC"],
        year=2026,
        adjustment="raw",
    )

    assert result.columns == ["ISU_CD", "BAS_DD", "TDD_CLSPRC"]
    assert result["ISU_CD"].to_list() == ["005930", "000660"]


def test_loadFiltered_rejects_ambiguous_or_unknown_bulk_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """모호한 종목 필터와 없는 컬럼을 조용히 무시하지 않는다."""
    from dartlab.gather.bulkData import hfBulk

    monkeypatch.setattr(hfBulk, "_loadYear", _twoCompanyYear)

    with pytest.raises(ValueError, match="동시에"):
        hfBulk.loadFiltered(stockCode="005930", stockCodes=["000660"], year=2026)
    with pytest.raises(ValueError, match="비어"):
        hfBulk.loadFiltered(stockCodes=[], year=2026)
    with pytest.raises(KeyError, match="없는 컬럼"):
        hfBulk.loadFiltered(stockCodes=["005930"], columns=["typo"], year=2026, adjustment="raw")
