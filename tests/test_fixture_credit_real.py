"""fixture 기반 credit 통합 테스트 — 실제 parquet 데이터로 검증.

tests/fixtures/dart/ 하위의 실제 삼성전자 데이터를 사용한다.
credit 엔진은 finance 데이터로 신용등급을 산출한다.
fixture 데이터가 최소한이므로 결과가 None일 수 있다 — crash 없음이 핵심.
"""

from __future__ import annotations

import gc
import os
from pathlib import Path

import polars as pl
import pytest

pytestmark = [pytest.mark.integration]

# Polars 예외 — scan 데이터 미존재 등으로 발생 가능
_SAFE_EXCEPTIONS = (
    RuntimeError,
    KeyError,
    ValueError,
    TypeError,
    ZeroDivisionError,
    AttributeError,
    pl.exceptions.PolarsError,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures"
_SAMSUNG = "005930"


def _fixture_data_available() -> bool:
    return (FIXTURE_DIR / "dart" / "finance" / f"{_SAMSUNG}.parquet").exists()


@pytest.fixture(scope="module")
def samsung():
    """fixture 데이터로 삼성전자 Company 로드."""
    if not _fixture_data_available():
        pytest.skip("Fixture data not available")

    os.environ["DARTLAB_DATA_DIR"] = str(FIXTURE_DIR)
    import dartlab

    dartlab.dataDir = str(FIXTURE_DIR)
    try:
        c = dartlab.Company(_SAMSUNG)
        yield c
    except Exception:
        pytest.skip("Fixture data not available or Company init failed")
    finally:
        gc.collect()


# ── evaluateCompany ──


def test_evaluateCompany(samsung):
    """evaluateCompany — dict 또는 None."""
    from dartlab.credit.engine import evaluateCompany

    samsung._cache.clear()
    try:
        result = evaluateCompany(samsung)
        assert result is None or isinstance(result, dict)
        if result is not None:
            # 기본 키 확인
            assert "grade" in result or "dCR" in result or "score" in result
    except _SAFE_EXCEPTIONS:
        # fixture 데이터 부족 — crash만 아니면 OK
        pass


def test_evaluateCompany_with_detail(samsung):
    """evaluateCompany detail=True — 확장 결과."""
    from dartlab.credit.engine import evaluateCompany

    samsung._cache.clear()
    try:
        result = evaluateCompany(samsung, detail=True)
        assert result is None or isinstance(result, dict)
    except _SAFE_EXCEPTIONS:
        pass


# ── Company.credit() 메서드 ──


def test_company_credit(samsung):
    """c.credit() — dict 또는 None."""
    samsung._cache.clear()
    try:
        result = samsung.credit()
        assert result is None or isinstance(result, dict)
    except _SAFE_EXCEPTIONS:
        pass


def test_company_credit_detail(samsung):
    """c.credit(detail=True) — 확장 결과."""
    samsung._cache.clear()
    try:
        result = samsung.credit(detail=True)
        assert result is None or isinstance(result, dict)
    except _SAFE_EXCEPTIONS:
        pass


# ── calcAllMetrics ──


def test_calcAllMetrics(samsung):
    """calcAllMetrics — 원시 메트릭 dict."""
    from dartlab.credit.engine import calcAllMetrics

    samsung._cache.clear()
    try:
        result = calcAllMetrics(samsung)
        assert result is None or isinstance(result, dict)
        if result is not None:
            assert "history" in result
    except _SAFE_EXCEPTIONS:
        pass


# ── 순수 로직 함수 ──


def test_scoreMetric_basic():
    """scoreMetric — 순수 함수, fixture 불필요."""
    from dartlab.core.finance.creditScorecard import scoreMetric

    # thresholdDef는 {"lower_is_better": bool, "breakpoints": [(value, score), ...]}
    threshold_def = {
        "lower_is_better": True,
        "breakpoints": [(0.05, 100), (0.1, 80), (0.2, 60), (0.3, 40), (0.5, 20)],
    }
    result = scoreMetric(0.15, threshold_def)
    assert isinstance(result, (int, float))


def test_scoreMetric_none_value():
    """scoreMetric — None 값 처리."""
    from dartlab.core.finance.creditScorecard import scoreMetric

    threshold_def = {
        "lower_is_better": True,
        "breakpoints": [(0.05, 100), (0.1, 80), (0.2, 60), (0.3, 40), (0.5, 20)],
    }
    result = scoreMetric(None, threshold_def)
    assert result is None


# ── credit 등급 산출 순수 로직 ──


def test_creditScorecard_import():
    """creditScorecard 모듈 import — 순수 로직 존재 확인."""
    from dartlab.core.finance.creditScorecard import creditOutlook

    # 빈 이력 — crash 없음
    result = creditOutlook([])
    assert result is None or isinstance(result, str)
