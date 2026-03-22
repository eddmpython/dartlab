"""supply 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """supply 엔진 스펙 반환."""
    return {
        "name": "supply",
        "description": "공시 기반 공급망 분석 — 고객/공급사 관계 추출 + 리스크 스코어링",
        "summary": {
            "extractionMethod": "규칙 기반 키워드 + 기업명 패턴 매칭",
            "riskFactors": 4,
            "linkTypes": ["customer", "supplier", "related_party"],
        },
        "detail": {
            "sourceTopics": [
                "segments (부문정보)",
                "rawMaterial (원재료)",
                "relatedPartyTransaction (관계자거래)",
                "majorContract (주요 계약)",
                "salesByProduct/salesByRegion",
                "10-K::item1Business (EDGAR)",
            ],
            "riskFactors": [
                "고객 집중도 (HHI) — 단일 의존 vs 분산",
                "공급사 집중도 — 대체 가능성",
                "관계자거래 비중 — 공정성 리스크",
                "정보 투명도 — 공시 충분성",
            ],
            "publicAPI": [
                "Company.supply — 공급망 분석 결과",
                "Company.supply.customers — 주요 고객",
                "Company.supply.suppliers — 주요 공급사",
                "Company.supply.riskScore — 리스크 점수",
            ],
        },
    }
