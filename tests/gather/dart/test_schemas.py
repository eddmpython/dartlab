"""Pandera FinanceSchema와 ReportSchema fixture 및 drift mirror 회귀.

본 SSOT 통합 PR (Phase 2b). Pandera schema가 raw fetch 결과를 데이터 계약
으로 못박는 1 차 방어선. 실 production 데이터 snapshot 전수 통과 + 의도적 drift
(컬럼 삭제) 시 에러 발생 확인.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from dartlab.gather.dart.schemas import FinanceSchema, ReportSchema

pytestmark = pytest.mark.unit

_FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures"

_FINANCE_FIXTURES = [
    "000660.finance.parquet",
    "003550.finance.parquet",
    "005380.finance.parquet",
    "005930.finance.parquet",
    "006400.finance.parquet",
    "017670.finance.parquet",
    "034730.finance.parquet",
    "035720.finance.parquet",
    "055550.finance.parquet",
    "207940.finance.parquet",
]


@pytest.mark.parametrize("filename", _FINANCE_FIXTURES)
def test_FinanceSchema_acceptsFixture(filename: str) -> None:
    """fixture 10 종이 FinanceSchema 통과 . 실 production snapshot 회귀 가드."""
    df = pl.read_parquet(_FIXTURE_DIR / filename)
    FinanceSchema.validate(df, lazy=True)


def test_ReportSchema_acceptsFixture() -> None:
    """report fixture 가 ReportSchema 통과."""
    df = pl.read_parquet(_FIXTURE_DIR / "005930.report.parquet")
    ReportSchema.validate(df, lazy=True)


def test_FinanceSchema_rejectsMissingRequiredColumn() -> None:
    """필수 컬럼 (rcept_no) 누락 시 SchemaError . drift 차단 회귀."""
    import pandera.errors

    df = pl.read_parquet(_FIXTURE_DIR / "005930.finance.parquet")
    dfDropped = df.drop("rcept_no")
    with pytest.raises(pandera.errors.SchemaErrors):
        FinanceSchema.validate(dfDropped, lazy=True)


def test_FinanceSchema_rejectsMissingStockCode() -> None:
    """stock_code 컬럼 누락 시 drift 차단."""
    import pandera.errors

    df = pl.read_parquet(_FIXTURE_DIR / "005930.finance.parquet")
    dfDropped = df.drop("stock_code")
    with pytest.raises(pandera.errors.SchemaErrors):
        FinanceSchema.validate(dfDropped, lazy=True)


def test_maybeValidateFinance_envGateOff_noOp() -> None:
    """DARTLAB_VALIDATE_SCHEMA 미설정 시 _maybeValidateFinance 는 no-op (production default)."""
    import os

    from dartlab.gather.dart.dart import _maybeValidateFinance

    os.environ.pop("DARTLAB_VALIDATE_SCHEMA", None)
    # 잘못된 데이터를 줘도 no-op → 예외 없어야 함.
    bad = pl.DataFrame({"not_a_column": [1, 2, 3]})
    _maybeValidateFinance(bad)  # no raise


def test_maybeValidateFinance_envGateOn_raisesSchemaErrors() -> None:
    """검증 활성화 상태의 깨진 데이터는 SchemaErrors를 호출자에게 전달한다."""
    import os

    import pandera.errors

    from dartlab.gather.dart.dart import _maybeValidateFinance

    os.environ["DARTLAB_VALIDATE_SCHEMA"] = "1"
    try:
        with pytest.raises(pandera.errors.SchemaErrors):
            bad = pl.DataFrame({"not_a_column": ["x"]})
            _maybeValidateFinance(bad)
    finally:
        os.environ.pop("DARTLAB_VALIDATE_SCHEMA", None)


def test_maybeValidateFinance_envGateOn_emptyFrame_noOp() -> None:
    """빈 frame 은 validate 건너뜀 (Dart.finance 가 종종 빈 DataFrame 반환)."""
    import os

    from dartlab.gather.dart.dart import _maybeValidateFinance

    os.environ["DARTLAB_VALIDATE_SCHEMA"] = "1"
    try:
        _maybeValidateFinance(pl.DataFrame())  # no raise
    finally:
        os.environ.pop("DARTLAB_VALIDATE_SCHEMA", None)
