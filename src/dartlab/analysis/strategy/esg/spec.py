"""esg 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """esg 엔진 스펙 반환."""
    from dartlab.analysis.strategy.esg.taxonomy import (
        ENVIRONMENT_KEYWORDS,
        GRI_INDEX,
        SOCIAL_KEYWORDS,
        TCFD_CATEGORIES,
        TOPIC_TO_PILLAR,
    )

    e_topics = [t for t, p in TOPIC_TO_PILLAR.items() if p == "E"]
    s_topics = [t for t, p in TOPIC_TO_PILLAR.items() if p == "S"]
    g_topics = [t for t, p in TOPIC_TO_PILLAR.items() if p == "G"]

    return {
        "name": "esg",
        "description": "ESG 공시 분석 — 환경(E), 사회(S), 지배구조(G) 3축 평가",
        "summary": {
            "pillars": 3,
            "topicMappings": len(TOPIC_TO_PILLAR),
            "envKeywordCategories": len(ENVIRONMENT_KEYWORDS),
            "socialKeywordCategories": len(SOCIAL_KEYWORDS),
            "griIndices": len(GRI_INDEX),
            "tcfdCategories": len(TCFD_CATEGORIES),
            "scoring": "E 30% + S 30% + G 40%",
        },
        "detail": {
            "environmentTopics": sorted(e_topics),
            "socialTopics": sorted(s_topics),
            "governanceTopics": sorted(g_topics),
            "griIndices": list(GRI_INDEX.keys()),
            "publicAPI": [
                "Company.esg — ESG 종합 등급 (E/S/G 각 점수 + 등급)",
                "Company.esg.environment — 환경 메트릭",
                "Company.esg.social — 사회 메트릭",
                "Company.esg.governance — 지배구조",
                "Company.esg.timeline — 연도별 진전도",
            ],
        },
    }
