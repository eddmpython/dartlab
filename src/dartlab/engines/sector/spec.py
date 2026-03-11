"""sector 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """sector 엔진 스펙 반환."""
    from dartlab.engines.sector.types import IndustryGroup, Sector

    sectors = [s.value for s in Sector if s != Sector.UNKNOWN]
    groups = [g.value for g in IndustryGroup if g != IndustryGroup.UNKNOWN]

    return {
        "name": "sector",
        "description": "WICS 기반 섹터 분류 (3단계: 수동 오버라이드 → 키워드 → KSIC)",
        "summary": {
            "sectors": len(sectors),
            "industryGroups": len(groups),
            "method": "override → keyword → ksic",
        },
        "detail": {
            "sectors": sectors,
            "industryGroups": groups,
            "classificationSteps": [
                "수동 오버라이드 (대형주 ~100종목)",
                "주요제품 키워드 분석",
                "KSIC(KIND 업종명) 매핑",
            ],
        },
    }
