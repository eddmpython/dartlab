"""Phase 4 Production 리프트 테스트.

G11 bounded accessor cache / G12 dFV baseline / G13 override chain /
G14 validateStory + _suggest / G15 buildBlocks preset + scan lazy.
"""

from __future__ import annotations

import pytest

# ── G11 BoundedCache accessor bound ────────────────────


@pytest.mark.unit
def test_boundedCache_accessors_share_bounded_atomic_policy():
    """accessor도 예외 pin 없이 동일한 bounded·atomic cache 계약을 따른다."""
    from dartlab.core.memory import BoundedCache

    cache = BoundedCache(maxEntries=2, memorySampler=lambda: 0.0)
    keys = ("_showAccessor", "_selectAccessor", "_storyAccessor", "_creditAccessor", "_analysisAccessor")
    for key in keys:
        assert cache.getOrCreate(key, lambda key=key: key) == key

    assert cache.keys() == list(keys[-2:])
    assert len(cache) == 2


# ── G14b BlockMap _suggest int 방어 ────────────────────


@pytest.mark.unit
def test_blockMap_suggest_accepts_non_str():
    """_suggest 가 int/float/list 등 비-str 입력도 str 반환."""
    from dartlab.story.catalog import _suggest

    for q in (123, 4.5, ["a"], None):
        result = _suggest(q)
        assert isinstance(result, str), f"{q!r} → {type(result).__name__}"


# ── G14a validateStory tool overrides description ──────


@pytest.mark.integration
def test_validateStory_tool_schema_has_description():
    """validateStory tool 의 overrides 에 Damodaran 키 description 노출."""
    from dartlab.ai.tools import buildTools

    tools = buildTools()
    vs = next((t for t in tools if t.name == "validateStory"), None)
    assert vs, "validateStory tool 미노출"
    desc = vs.parameters.get("properties", {}).get("overrides", {}).get("description", "")
    for key in ("impliedERP", "bottomUpBeta", "lifeCyclePhase", "pSurvival", "countryCode"):
        assert key in desc, f"{key} description 누락"


# ── G12 dFV baseline 보정 ──────────────────────────────


@pytest.mark.integration
@pytest.mark.requires_data
def test_dFV_samsung_within_realistic_range():
    """삼성전자 dFV 140K~230K (현재가 211K 근접, Phase 3 61K → 개선)."""
    from dartlab.analysis.valuation.dFV import calcDFV
    from dartlab.providers.dart.company import Company

    c = Company("005930")
    r = calcDFV(c)
    assert r is not None
    dfv = r["dFV"]
    assert 140_000 < dfv < 230_000, f"dFV {dfv:,} out of realistic range"


@pytest.mark.integration
@pytest.mark.requires_data
def test_dFV_yangyang_live_ledger_is_internally_consistent():
    """삼양식품 라이브 값은 특정 가격이 아니라 실제 DCF 원장 정합성을 지킨다."""
    from dartlab.analysis.valuation.dFV import calcDFV
    from dartlab.providers.dart.company import Company

    c = Company("003230")
    r = calcDFV(c)
    assert r is not None
    ts = r.get("twoStage") or {}
    assumptions = ts.get("assumptions") or {}
    assert r["dFV"] > 0
    assert r["primaryModel"] == "dcf2stage"
    assert ts["wacc"] == r["qualityWACC"]["adjustedWACC"]
    assert assumptions["fcfPeriods"]
    assert assumptions["balancePeriod"]
    assert assumptions["sharesSource"]
    assert ts["pvExplicit"] + ts["pvTerminal"] == pytest.approx(ts["enterpriseValue"])
    assert ts["enterpriseValue"] - ts["netDebt"] == pytest.approx(ts["equityValue"])
    assert ts["equityValue"] / ts["shares"] == pytest.approx(ts["perShare"])
    assert r["allMethods"]["dcf2stage"] == round(ts["perShare"])


# ── G13 override chain 전파 ────────────────────────────


@pytest.mark.integration
@pytest.mark.requires_data
def test_override_chain_country_propagates():
    """countryCode override 주입 시 dFV 경로 변화 (chain 전파 증거)."""
    from dartlab.analysis.valuation.dFV import calcDFV
    from dartlab.providers.dart.company import Company

    c = Company("003230")
    r_base = calcDFV(c)
    r_us = calcDFV(c, overrides={"countryCode": "US"})
    assert r_base is not None
    assert r_us is not None
    # country 전파 시 dFV 변화 (Rf 차이 반영)
    assert r_base["dFV"] != r_us["dFV"], "country override 미전파"


# ── G15a buildBlocks preset ────────────────────────────


@pytest.mark.unit
def test_buildBlocks_preset_constants_exist():
    """_MINIMAL_KEYS / _STANDARD_KEYS 정의 + dFV/lifeCycleStage 포함."""
    from dartlab.story.registry import _MINIMAL_KEYS, _STANDARD_KEYS

    assert "dFV" in _MINIMAL_KEYS
    assert "lifeCycleStage" in _MINIMAL_KEYS
    assert "valuationSins" in _MINIMAL_KEYS
    # standard 는 minimal 상위집합
    assert _MINIMAL_KEYS <= _STANDARD_KEYS


# ── G15b scan lazy ─────────────────────────────────────


@pytest.mark.integration
def test_storyPrecedents_skipIfScanMissing_signature():
    """calcStoryPrecedents 시그니처에 skipIfScanMissing 파라미터 존재."""
    import inspect

    from dartlab.analysis.financial.storyValidation import calcStoryPrecedents

    sig = inspect.signature(calcStoryPrecedents)
    assert "skipIfScanMissing" in sig.parameters
    # 기본값 True (AI timeout 방지)
    param = sig.parameters["skipIfScanMissing"]
    assert param.default is True
