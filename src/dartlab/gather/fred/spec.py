"""FRED 엔진 AI 스펙 메타데이터."""

from __future__ import annotations

from . import catalog as _catalog


def buildSpec() -> dict:
    """AI spec 수집기용 FRED 엔진 스펙."""
    groups = {}
    for name in _catalog.get_groups():
        entries = _catalog.get_group(name)
        groups[name] = {
            "count": len(entries),
            "series": [{"id": e.id, "label": e.label} for e in entries],
        }

    return {
        "name": "fred",
        "label": "FRED 경제지표",
        "description": "미국 연방준비은행 경제 데이터 (800,000+ 시계열)",
        "tier": "beta",
        "capabilities": [
            "시계열 조회 (series)",
            "키워드 검색 (search)",
            "복수 시리즈 비교 (compare)",
            "YoY/MoM 변화율",
            "이동평균 (movingAverage)",
            "상관분석 (correlation)",
            "선행/후행 분석 (leadLag)",
            "주요 지표 카탈로그 (7개 그룹)",
        ],
        "catalog_groups": groups,
        "total_catalog_series": len(_catalog.get_all_ids()),
        "tools": [
            {"name": "fred_series", "description": "FRED 시계열 조회 + 변환"},
            {"name": "fred_search", "description": "FRED 시리즈 키워드 검색"},
            {"name": "fred_compare", "description": "복수 시계열 비교"},
            {"name": "fred_catalog", "description": "주요 경제지표 카탈로그"},
            {"name": "fred_correlation", "description": "시계열 상관분석 + 선행/후행"},
        ],
    }
