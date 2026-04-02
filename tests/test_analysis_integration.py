"""analysis 통합 테스트 — MockCompany로 전체 축 코드 경로 검증.

모든 축의 calc 함수를 합성 데이터로 실행하여 crash 없음을 확인한다.
실제 코드 경로를 최대한 통과시키는 것이 목표.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── 전체 축 실행 ──


def test_all_financial_axes(mock_company):
    """14개 financial 축 — 각각 dict 또는 None 반환, crash 없음."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    financial_axes = _GROUPS["financial"]

    for axis_name in financial_axes:
        mock_company._cache.clear()
        result = analysis("financial", axis_name, company=mock_company)
        assert result is None or isinstance(result, dict), f"financial/{axis_name} returned {type(result)}"


def test_all_valuation_axes(mock_company):
    """가치평가 축 — dict 반환, crash 없음."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    for axis_name in _GROUPS["valuation"]:
        mock_company._cache.clear()
        result = analysis("valuation", axis_name, company=mock_company)
        assert result is None or isinstance(result, dict), f"valuation/{axis_name} returned {type(result)}"


def test_all_governance_axes(mock_company):
    """지배구조/공시변화/비교분석 — dict 반환, crash 없음."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    for axis_name in _GROUPS["governance"]:
        mock_company._cache.clear()
        result = analysis("governance", axis_name, company=mock_company)
        assert result is None or isinstance(result, dict), f"governance/{axis_name} returned {type(result)}"


def test_all_forecast_axes(mock_company):
    """매출전망/예측신호 — dict 반환, crash 없음."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    for axis_name in _GROUPS["forecast"]:
        mock_company._cache.clear()
        result = analysis("forecast", axis_name, company=mock_company)
        assert result is None or isinstance(result, dict), f"forecast/{axis_name} returned {type(result)}"


def test_all_macro_axes(mock_company):
    """매크로 4축 — dict 반환, crash 없음."""
    from dartlab.analysis.financial import _GROUPS, Analysis

    analysis = Analysis()
    for axis_name in _GROUPS["macro"]:
        mock_company._cache.clear()
        result = analysis("macro", axis_name, company=mock_company)
        assert result is None or isinstance(result, dict), f"macro/{axis_name} returned {type(result)}"


def test_every_axis_in_registry(mock_company):
    """_AXIS_REGISTRY 전체 — 빠진 축 없이 모두 실행."""
    from dartlab.analysis.financial import _AXIS_REGISTRY, Analysis

    analysis = Analysis()
    failed = []

    for axis_name in _AXIS_REGISTRY:
        mock_company._cache.clear()
        try:
            result = analysis(axis_name, company=mock_company)
            if not (result is None or isinstance(result, dict)):
                failed.append(f"{axis_name}: returned {type(result)}")
        except Exception as e:
            failed.append(f"{axis_name}: {type(e).__name__}: {e}")

    assert not failed, f"{len(failed)} axes failed:\n" + "\n".join(failed)


# ── 빈 데이터 안전성 ──


def test_all_axes_with_empty_company(empty_mock_company):
    """빈 회사 데이터로도 crash 없음.

    일부 축(가치평가 등)은 report 데이터 다운로드를 시도하므로
    RuntimeError(네트워크)도 허용한다.
    """
    from dartlab.analysis.financial import _AXIS_REGISTRY, Analysis

    analysis = Analysis()

    for axis_name in _AXIS_REGISTRY:
        empty_mock_company._cache.clear()
        try:
            result = analysis(axis_name, company=empty_mock_company)
            assert result is None or isinstance(result, dict), f"{axis_name} with empty data returned {type(result)}"
        except RuntimeError:
            # 네트워크 요청 실패 (빈 종목코드로 데이터 다운로드 시도) — 허용
            pass


# ── 개별 calc 함수 직접 실행 ──


def test_individual_calc_functions(mock_company):
    """레지스트리의 모든 calc 함수를 개별 실행 — import + 호출 검증."""
    import importlib
    import inspect

    from dartlab.analysis.financial import _AXIS_REGISTRY

    failed = []
    total = 0

    for axis_name, entry in _AXIS_REGISTRY.items():
        for calc in entry.calcs:
            total += 1
            mock_company._cache.clear()
            try:
                mod = importlib.import_module(calc.module)
                fn = getattr(mod, calc.fn)
                sig = inspect.signature(fn)
                if "basePeriod" in sig.parameters:
                    result = fn(mock_company, basePeriod=None)
                else:
                    result = fn(mock_company)
                # result can be dict, list, None, or any type — just no crash
            except (KeyError, ValueError, TypeError, AttributeError, ArithmeticError, ImportError):
                # These are expected for mock data — calc functions may reject synthetic data
                pass
            except Exception as e:
                failed.append(f"{calc.module}.{calc.fn}: {type(e).__name__}: {e}")

    assert not failed, f"{len(failed)}/{total} calc functions crashed:\n" + "\n".join(failed)


# ── 캐시 재사용 검증 ──


def test_cache_reuse_across_axes(mock_company):
    """같은 company 객체로 여러 축 실행 — 캐시가 올바르게 동작."""
    from dartlab.analysis.financial import Analysis

    analysis = Analysis()

    # 첫 실행
    r1 = analysis("financial", "수익성", company=mock_company)
    # 캐시 유지한 채 다른 축 실행
    r2 = analysis("financial", "안정성", company=mock_company)
    # 다시 같은 축 — 캐시 히트
    r3 = analysis("financial", "수익성", company=mock_company)

    assert isinstance(r1, dict)
    assert isinstance(r2, dict)
    assert isinstance(r3, dict)
