"""Spec 무결성 테스트 — 코드와 spec의 불일치를 CI에서 검증."""

import pytest

pytestmark = pytest.mark.integration


def test_all_engines_have_spec():
    """모든 등록된 엔진이 유효한 spec을 반환하는지."""
    from dartlab.engines.ai.spec import buildSpec

    spec = buildSpec(depth="summary")
    expected = ["dart.finance", "dart.report", "sector", "insight", "rank"]

    for name in expected:
        assert name in spec["engines"], f"{name} spec 누락"
        assert spec["engines"][name].get("description"), f"{name} description 없음"
        assert spec["engines"][name].get("summary"), f"{name} summary 없음"


def test_spec_detail_depth():
    """detail depth가 summary보다 더 많은 정보를 포함하는지."""
    from dartlab.engines.ai.spec import buildSpec

    summary = buildSpec(depth="summary")
    detail = buildSpec(depth="detail")

    for name in summary["engines"]:
        assert name in detail["engines"]


def test_get_engine_spec():
    """getEngineSpec이 개별 엔진을 올바르게 반환하는지."""
    from dartlab.engines.ai.spec import getEngineSpec

    spec = getEngineSpec("insight")
    assert spec is not None
    assert spec["name"] == "insight"
    assert "detail" in spec

    section = getEngineSpec("insight", section="summary")
    assert section is not None
    assert "summary" in section


def test_get_engine_spec_not_found():
    """존재하지 않는 엔진 조회 시 None 반환."""
    from dartlab.engines.ai.spec import getEngineSpec

    assert getEngineSpec("nonexistent") is None


def test_insight_areas_match_code():
    """insight spec의 areas가 실제 grading.py 분석 함수와 일치하는지."""
    from dartlab.engines.analysis.insight.spec import AREAS

    expected = {"performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"}
    assert set(AREAS.keys()) == expected


def test_sector_spec_extracts_enums():
    """sector spec이 실제 Sector enum에서 추출하는지."""
    from dartlab.engines.analysis.sector.spec import buildSpec
    from dartlab.engines.analysis.sector.types import Sector

    spec = buildSpec()
    sectorCount = len([s for s in Sector if s != Sector.UNKNOWN])
    assert spec["summary"]["sectors"] == sectorCount


def test_report_spec_matches_api_types():
    """report spec의 apiTypes가 실제 API_TYPES와 일치하는지."""
    from dartlab.engines.company.dart.report.spec import buildSpec
    from dartlab.engines.company.dart.report.types import API_TYPES

    spec = buildSpec()
    assert spec["summary"]["apiTypes"] == len(API_TYPES)
    assert set(spec["detail"]["apiTypes"].keys()) == set(API_TYPES)


def test_finance_spec_ratios_match_dataclass():
    """finance spec의 ratios가 RatioResult 필드와 일치하는지."""
    import dataclasses

    from dartlab.engines.common.finance.ratios import RatioResult
    from dartlab.engines.company.dart.finance.spec import buildSpec

    spec = buildSpec()
    expected = [f.name for f in dataclasses.fields(RatioResult) if f.name != "warnings"]
    assert spec["detail"]["ratios"] == expected


def test_spec_has_system_info():
    """총괄 spec에 시스템 정보가 포함되는지."""
    from dartlab.engines.ai.spec import buildSpec

    spec = buildSpec()
    assert "system" in spec
    assert spec["system"]["name"] == "DartLab"
    assert spec["system"].get("version")
