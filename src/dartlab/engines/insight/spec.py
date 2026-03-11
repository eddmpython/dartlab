"""insight 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations

AREAS = {
    "performance": {
        "label": "실적",
        "description": "매출/영업이익 YoY 성장률 + 분기 변동성",
        "metrics": ["revenue_growth_yoy", "operating_income_growth_yoy", "quarterly_volatility"],
    },
    "profitability": {
        "label": "수익성",
        "description": "영업이익률, 순이익률, ROE, ROA + 섹터 벤치마크 보정",
        "metrics": ["operating_margin", "net_margin", "roe", "roa"],
    },
    "health": {
        "label": "재무건전성",
        "description": "부채비율, 유동비율, 이자보상배율",
        "metrics": ["debt_ratio", "current_ratio", "interest_coverage"],
    },
    "cashflow": {
        "label": "현금흐름",
        "description": "영업CF, FCF, 현금성자산 비중",
        "metrics": ["operating_cf", "fcf", "cash_ratio"],
    },
    "governance": {
        "label": "지배구조",
        "description": "최대주주 지분율, 감사의견, 사외이사 비율, 자기주식",
        "metrics": ["major_holder_pct", "audit_opinion", "outside_director_ratio", "treasury_stock"],
    },
    "risk": {
        "label": "종합 리스크",
        "description": "전 영역 리스크 플래그 종합",
        "metrics": [],
    },
    "opportunity": {
        "label": "종합 기회",
        "description": "전 영역 기회 플래그 종합",
        "metrics": [],
    },
}

ANOMALY_DETECTORS = [
    "earnings_quality",
    "working_capital",
    "balance_sheet_shift",
    "cash_burn",
    "margin_divergence",
    "financial_sector",
]


def buildSpec() -> dict:
    """insight 엔진 스펙 반환."""
    return {
        "name": "insight",
        "description": "기업 분석 등급 (7영역 A~F) + 이상치 탐지 + 프로파일 분류",
        "summary": {
            "areas": list(AREAS.keys()),
            "grading": "A~F (6단계, 점수 기반)",
            "anomaly": f"Z-score 기반 {len(ANOMALY_DETECTORS)}개 탐지기",
            "profile": "classifyProfile (수비형/공격형/성장형/가치형 등)",
        },
        "detail": {area: meta for area, meta in AREAS.items()},
        "anomalyDetectors": ANOMALY_DETECTORS,
    }
