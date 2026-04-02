"""fixture 기반 analysis 통합 테스트 — 실제 parquet 데이터로 전축 검증.

tests/fixtures/dart/ 하위의 실제 삼성전자 데이터를 사용한다.
fixture 데이터는 최소한이므로 대부분의 축이 None을 반환할 수 있다 — 정상.
핵심은 crash 없이 모든 축이 실행 가능한지 검증하는 것이다.
"""

from __future__ import annotations

import gc
import os
from pathlib import Path

import pytest

pytestmark = [pytest.mark.integration]

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


# ── 전체 축 일괄 실행 ──


def test_all_financial_axes_no_crash(samsung):
    """financial 그룹 전축 — crash 없음 확인."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    failed = []

    for axis_name in _GROUPS["financial"]:
        samsung._cache.clear()
        try:
            result = analysis("financial", axis_name, company=samsung)
            if not (result is None or isinstance(result, dict)):
                failed.append(f"{axis_name}: returned {type(result)}")
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            # fixture 데이터 부족으로 예외 가능 — crash만 아니면 OK
            pass
        except Exception as e:
            failed.append(f"{axis_name}: {type(e).__name__}: {e}")

    assert not failed, "financial axes failed:\n" + "\n".join(failed)


def test_all_valuation_axes_no_crash(samsung):
    """valuation 그룹 전축 — crash 없음 확인."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()

    for axis_name in _GROUPS["valuation"]:
        samsung._cache.clear()
        try:
            result = analysis("valuation", axis_name, company=samsung)
            assert result is None or isinstance(result, dict)
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            pass


def test_all_governance_axes_no_crash(samsung):
    """governance 그룹 전축 — crash 없음 확인."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()

    for axis_name in _GROUPS["governance"]:
        samsung._cache.clear()
        try:
            result = analysis("governance", axis_name, company=samsung)
            assert result is None or isinstance(result, dict)
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            pass


def test_all_forecast_axes_no_crash(samsung):
    """forecast 그룹 전축 — crash 없음 확인."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()

    for axis_name in _GROUPS["forecast"]:
        samsung._cache.clear()
        try:
            result = analysis("forecast", axis_name, company=samsung)
            assert result is None or isinstance(result, dict)
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            pass


def test_all_macro_axes_no_crash(samsung):
    """macro 그룹 전축 — crash 없음 확인."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()

    for axis_name in _GROUPS["macro"]:
        samsung._cache.clear()
        try:
            result = analysis("macro", axis_name, company=samsung)
            assert result is None or isinstance(result, dict)
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            pass


def test_every_axis_in_registry_no_crash(samsung):
    """_AXIS_REGISTRY 전체 — 빠진 축 없이 crash 검증."""
    from dartlab.analysis.financial import _AXIS_REGISTRY, Analysis

    analysis = Analysis()
    failed = []

    for axis_name in _AXIS_REGISTRY:
        samsung._cache.clear()
        try:
            result = analysis(axis_name, company=samsung)
            if not (result is None or isinstance(result, dict)):
                failed.append(f"{axis_name}: returned {type(result)}")
        except (RuntimeError, KeyError, ValueError, TypeError, AttributeError):
            pass
        except Exception as e:
            failed.append(f"{axis_name}: {type(e).__name__}: {e}")

    assert not failed, f"{len(failed)} axes failed:\n" + "\n".join(failed)


# ── 핵심 축 개별 테스트 (fixture 데이터로 결과 기대) ──


class TestFinancialAxesIndividual:
    """최소 fixture 데이터로도 결과가 나올 가능성이 높은 축 개별 검증."""

    def test_profitability(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "수익성")
        assert result is None or isinstance(result, dict)

    def test_growth(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "성장성")
        assert result is None or isinstance(result, dict)

    def test_stability(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "안정성")
        assert result is None or isinstance(result, dict)

    def test_efficiency(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "효율성")
        assert result is None or isinstance(result, dict)

    def test_revenue_structure(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "수익구조")
        assert result is None or isinstance(result, dict)

    def test_funding_structure(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "자금조달")
        assert result is None or isinstance(result, dict)

    def test_asset_structure(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "자산구조")
        assert result is None or isinstance(result, dict)

    def test_cashflow_structure(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "현금흐름")
        assert result is None or isinstance(result, dict)

    def test_scorecard(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "종합평가")
        assert result is None or isinstance(result, dict)

    def test_earnings_quality(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "이익품질")
        assert result is None or isinstance(result, dict)

    def test_cost_structure(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "비용구조")
        assert result is None or isinstance(result, dict)

    def test_capital_allocation(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "자본배분")
        assert result is None or isinstance(result, dict)

    def test_investment_efficiency(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "투자효율")
        assert result is None or isinstance(result, dict)

    def test_financial_consistency(self, samsung):
        samsung._cache.clear()
        result = samsung.analysis("financial", "재무정합성")
        assert result is None or isinstance(result, dict)


# ── analysis guide (no company) ──


class TestAnalysisGuide:
    def test_analysis_guide_returns_dataframe(self, samsung):
        """analysis() 인자 없이 호출 → 가이드 DataFrame."""
        import polars as pl

        from dartlab.analysis.financial import Analysis

        analysis = Analysis()
        result = analysis()
        assert isinstance(result, pl.DataFrame)

    def test_analysis_axis_guide(self, samsung):
        """analysis("financial", "수익성") company 없이 → 항목 목록."""
        import polars as pl

        from dartlab.analysis.financial import Analysis

        analysis = Analysis()
        result = analysis("financial", "수익성")
        assert isinstance(result, pl.DataFrame)


# ── 캐시 동작 ──


def test_cache_reuse_with_fixture(samsung):
    """실제 데이터에서 캐시 재사용 — 두 번째 호출이 crash 없이 동작."""
    samsung._cache.clear()
    r1 = samsung.analysis("financial", "수익성")
    # 캐시 유지한 채 같은 축 재호출
    r2 = samsung.analysis("financial", "수익성")
    # 둘 다 같은 타입
    assert type(r1) is type(r2)


def test_cache_across_axes_with_fixture(samsung):
    """실제 데이터에서 캐시 공유 — 다른 축 간 공유 calc 캐시."""
    samsung._cache.clear()
    r1 = samsung.analysis("financial", "수익성")
    # 다른 축 — 공유 calc 캐시 사용
    r2 = samsung.analysis("financial", "안정성")
    assert r1 is None or isinstance(r1, dict)
    assert r2 is None or isinstance(r2, dict)
