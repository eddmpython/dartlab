"""ESG 표준 매핑 — K-ESG, GRI, TCFD 지표 체계.

sections의 topic을 ESG 3축으로 분류하고,
키워드 매칭으로 관련 메트릭을 추출한다.
"""

from __future__ import annotations

# ── sections topic → ESG pillar 매핑 ──

TOPIC_TO_PILLAR: dict[str, str] = {
    # Environment (E)
    "environmentOverview": "E",
    "environmentPolicy": "E",
    "greenBonds": "E",
    "carbonEmission": "E",
    "energyUsage": "E",
    "wasteManagement": "E",
    "waterUsage": "E",
    # Social (S)
    "employeeOverview": "S",
    "employeeWelfare": "S",
    "industrialAccident": "S",
    "socialContribution": "S",
    "customerSatisfaction": "S",
    "humanRights": "S",
    "supplyChainEthics": "S",
    "laborRelations": "S",
    # Governance (G)
    "boardDiversity": "G",
    "boardOverview": "G",
    "auditOpinion": "G",
    "relatedPartyTransaction": "G",
    "majorShareholder": "G",
    "internalControl": "G",
    "ethicsCompliance": "G",
    "executiveCompensation": "G",
    # EDGAR equivalents
    "10-K::item1ARiskFactors": "G",
    "10-K::item1Business": "G",
    "10-K::item7MDA": "G",
}


# ── 키워드 → 환경 메트릭 매핑 ──

ENVIRONMENT_KEYWORDS: dict[str, list[str]] = {
    "carbonEmission": [
        "탄소배출",
        "온실가스",
        "Scope 1",
        "Scope 2",
        "Scope 3",
        "tCO2",
        "tCO2eq",
        "GHG",
        "carbon emission",
    ],
    "energyUsage": [
        "에너지 사용",
        "전력 소비",
        "재생에너지",
        "신재생",
        "TJ",
        "MWh",
        "energy consumption",
        "renewable",
    ],
    "waterUsage": [
        "용수",
        "물 사용",
        "water consumption",
        "water usage",
    ],
    "wasteManagement": [
        "폐기물",
        "재활용",
        "waste",
        "recycling",
        "recycled",
    ],
}


# ── 사회 메트릭 키워드 ──

SOCIAL_KEYWORDS: dict[str, list[str]] = {
    "industrialAccident": [
        "산재",
        "산업재해",
        "재해율",
        "사망",
        "중대재해",
        "industrial accident",
        "fatality",
    ],
    "genderPay": [
        "남녀",
        "성별",
        "급여격차",
        "gender pay",
        "gender gap",
    ],
    "employeeTurnover": [
        "이직",
        "퇴사",
        "퇴직",
        "turnover",
        "attrition",
    ],
    "training": [
        "교육",
        "연수",
        "training",
        "education hours",
    ],
}


# ── GRI 인덱스 매핑 (주요 지표) ──

GRI_INDEX: dict[str, dict[str, str]] = {
    "GRI 305-1": {"pillar": "E", "metric": "Scope 1 GHG emissions", "unit": "tCO2eq"},
    "GRI 305-2": {"pillar": "E", "metric": "Scope 2 GHG emissions", "unit": "tCO2eq"},
    "GRI 305-3": {"pillar": "E", "metric": "Scope 3 GHG emissions", "unit": "tCO2eq"},
    "GRI 302-1": {"pillar": "E", "metric": "Energy consumption", "unit": "TJ"},
    "GRI 303-3": {"pillar": "E", "metric": "Water withdrawal", "unit": "ML"},
    "GRI 306-3": {"pillar": "E", "metric": "Waste generated", "unit": "tonnes"},
    "GRI 401-1": {"pillar": "S", "metric": "New hires and turnover", "unit": "count"},
    "GRI 403-9": {"pillar": "S", "metric": "Work-related injuries", "unit": "rate"},
    "GRI 404-1": {"pillar": "S", "metric": "Training hours", "unit": "hours/employee"},
    "GRI 405-2": {"pillar": "S", "metric": "Gender pay ratio", "unit": "ratio"},
    "GRI 205-2": {"pillar": "G", "metric": "Anti-corruption training", "unit": "%"},
}


# ── TCFD 권고안 카테고리 ──

TCFD_CATEGORIES: dict[str, list[str]] = {
    "governance": ["기후변화 거버넌스", "climate governance", "board oversight"],
    "strategy": ["기후변화 전략", "climate strategy", "scenario analysis"],
    "riskManagement": ["기후 리스크", "climate risk", "transition risk", "physical risk"],
    "metrics": ["탄소집약도", "carbon intensity", "emission target", "감축 목표"],
}
