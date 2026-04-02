"""analysis 엔진 구조 단위 테스트.

_AXIS_REGISTRY, _GROUPS, _ALIASES, _resolveAxis, Analysis 가이드 테스트.
데이터 로드 없음, Company 객체 없음, mock 전용.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


# ── _AXIS_REGISTRY ──


def test_registry_has_core_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    expected = {"수익구조", "수익성", "성장성", "안정성", "효율성", "종합평가"}
    assert expected.issubset(set(_AXIS_REGISTRY.keys()))


def test_registry_has_advanced_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    expected = {"이익품질", "비용구조", "자본배분", "투자효율", "재무정합성"}
    assert expected.issubset(set(_AXIS_REGISTRY.keys()))


def test_registry_has_valuation_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    assert "가치평가" in _AXIS_REGISTRY


def test_registry_has_governance_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    assert "지배구조" in _AXIS_REGISTRY
    assert "공시변화" in _AXIS_REGISTRY
    assert "비교분석" in _AXIS_REGISTRY


def test_registry_has_forecast_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    assert "매출전망" in _AXIS_REGISTRY
    assert "예측신호" in _AXIS_REGISTRY


def test_registry_entries_have_required_fields():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    for key, entry in _AXIS_REGISTRY.items():
        assert entry.section, f"{key}: section 누락"
        assert entry.partId, f"{key}: partId 누락"
        assert entry.description, f"{key}: description 누락"
        assert entry.example, f"{key}: example 누락"


def test_registry_entries_have_calcs():
    from dartlab.analysis.financial import _AXIS_REGISTRY

    for key, entry in _AXIS_REGISTRY.items():
        assert len(entry.calcs) > 0, f"{key}: calcs 비어있음"


# ── _GROUPS ──


def test_groups_has_financial():
    from dartlab.analysis.financial import _GROUPS

    assert "financial" in _GROUPS
    assert "수익성" in _GROUPS["financial"]
    assert "안정성" in _GROUPS["financial"]


def test_groups_has_valuation():
    from dartlab.analysis.financial import _GROUPS

    assert "valuation" in _GROUPS
    assert "가치평가" in _GROUPS["valuation"]


def test_groups_has_governance():
    from dartlab.analysis.financial import _GROUPS

    assert "governance" in _GROUPS
    assert "지배구조" in _GROUPS["governance"]


def test_groups_has_forecast():
    from dartlab.analysis.financial import _GROUPS

    assert "forecast" in _GROUPS
    assert "매출전망" in _GROUPS["forecast"]


def test_groups_has_macro():
    from dartlab.analysis.financial import _GROUPS

    assert "macro" in _GROUPS


def test_groups_axes_exist_in_registry():
    """그룹에 등록된 모든 축이 레지스트리에 존재해야 한다."""
    from dartlab.analysis.financial import _AXIS_REGISTRY, _GROUPS

    for group, axes in _GROUPS.items():
        for axis in axes:
            assert axis in _AXIS_REGISTRY, f"그룹 '{group}'의 축 '{axis}'가 레지스트리에 없음"


# ── _ALIASES ──


def test_aliases_english_to_korean():
    from dartlab.analysis.financial import _ALIASES

    assert _ALIASES["profitability"] == "수익성"
    assert _ALIASES["growth"] == "성장성"
    assert _ALIASES["stability"] == "안정성"
    assert _ALIASES["efficiency"] == "효율성"
    assert _ALIASES["cashflow"] == "현금흐름"


def test_aliases_group_korean():
    from dartlab.analysis.financial import _ALIASES

    assert _ALIASES["재무"] == "financial"
    assert _ALIASES["가치"] == "valuation"


def test_aliases_resolve_to_valid_axis_or_group():
    """alias의 값이 레지스트리 축이거나 그룹이어야 한다."""
    from dartlab.analysis.financial import _ALIASES, _AXIS_REGISTRY, _GROUPS

    for alias, target in _ALIASES.items():
        assert target in _AXIS_REGISTRY or target in _GROUPS, (
            f"alias '{alias}' -> '{target}'가 레지스트리에도 그룹에도 없음"
        )


# ── _resolveAxis ──


def test_resolve_axis_korean():
    from dartlab.analysis.financial import _resolveAxis

    assert _resolveAxis("수익성") == "수익성"
    assert _resolveAxis("안정성") == "안정성"


def test_resolve_axis_english():
    from dartlab.analysis.financial import _resolveAxis

    assert _resolveAxis("profitability") == "수익성"
    assert _resolveAxis("growth") == "성장성"


def test_resolve_axis_case_insensitive():
    from dartlab.analysis.financial import _resolveAxis

    assert _resolveAxis("Profitability") == "수익성"
    assert _resolveAxis("GROWTH") == "성장성"


def test_resolve_axis_unknown_raises():
    from dartlab.analysis.financial import _resolveAxis

    with pytest.raises(ValueError, match="알 수 없는 분석 축"):
        _resolveAxis("존재하지않는축")


def test_resolve_axis_unknown_shows_available():
    from dartlab.analysis.financial import _resolveAxis

    with pytest.raises(ValueError, match="가용 축"):
        _resolveAxis("xxx")


# ── Analysis guide ──


def test_analysis_guide_returns_dataframe():
    import polars as pl

    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a()
    assert isinstance(result, pl.DataFrame)
    assert len(result) > 0


def test_analysis_guide_has_columns():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a()
    cols = set(result.columns)
    assert {"축", "설명"}.issubset(cols)


def test_analysis_guide_has_all_registry_axes():
    from dartlab.analysis.financial import _AXIS_REGISTRY, Analysis

    a = Analysis()
    result = a()
    guide_axes = set(result["축"].to_list())
    for key in _AXIS_REGISTRY:
        assert key in guide_axes, f"가이드에 '{key}' 축 누락"


# ── Analysis group guide ──


def test_analysis_group_guide_financial():
    import polars as pl

    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a("financial")
    assert isinstance(result, pl.DataFrame)
    assert len(result) > 0


def test_analysis_group_guide_columns():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a("financial")
    cols = set(result.columns)
    assert {"축", "파트", "설명"} == cols


def test_analysis_group_guide_valuation():
    import polars as pl

    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a("valuation")
    assert isinstance(result, pl.DataFrame)
    axes = result["축"].to_list()
    assert "가치평가" in axes


def test_analysis_group_guide_korean_alias():
    import polars as pl

    from dartlab.analysis.financial import Analysis

    a = Analysis()
    result = a("재무")
    assert isinstance(result, pl.DataFrame)
    assert len(result) > 0


# ── _GroupAccessor ──


def test_group_accessor_via_attribute():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    accessor = a.financial
    assert accessor is not None
    assert repr(accessor).startswith("Analysis.financial")


def test_group_accessor_repr():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    r = repr(a.financial)
    assert "financial" in r
    assert "수익성" in r


def test_group_accessor_valuation():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    accessor = a.valuation
    assert repr(accessor).startswith("Analysis.valuation")


def test_group_accessor_unknown_raises():
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    with pytest.raises(AttributeError):
        _ = a.nonexistent_group


def test_group_accessor_axis_attribute():
    """analysis.financial.profitability 패턴 — callable을 반환해야 한다."""
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    fn = a.financial.profitability
    assert callable(fn)


def test_group_accessor_wrong_group_axis_raises():
    """financial 그룹에서 valuation 축 접근 시 AttributeError."""
    from dartlab.analysis.financial import Analysis

    a = Analysis()
    with pytest.raises(AttributeError, match="속하지 않습니다"):
        _ = a.financial.valuation
