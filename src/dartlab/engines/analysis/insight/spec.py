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
        "description": "부채비율, 유동비율 + 부실 예측 모델 (O-Score, Z''-Score)",
        "metrics": ["debt_ratio", "current_ratio", "interest_coverage", "ohlson_o_score", "altman_zpp_score"],
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
    "trend_deterioration",
    "ccc_deterioration",
]


DISTRESS_MODELS = {
    "ohlsonOScore": {
        "label": "Ohlson O-Score",
        "description": "9변수 로지스틱 부도 확률 (1980). 금융업 포함 범용.",
    },
    "altmanZppScore": {
        "label": "Altman Z''-Score",
        "description": "비제조업/신흥시장 변형 (1995). 금융업 적용 가능.",
    },
    "springateSScore": {
        "label": "Springate S-Score",
        "description": "Z-Score 캐나다 변형 4변수 (1978). S < 0.862 부실.",
    },
    "zmijewskiXScore": {
        "label": "Zmijewski X-Score",
        "description": "3변수 프로빗 모델 (1984). X > 0 부실. 금융업 왜곡 주의.",
    },
    "mertonD2D": {
        "label": "Merton D2D",
        "description": "구조 모형 부도 거리 (1974). 주가변동성+부채 기반. Moody's KMV 글로벌 표준.",
    },
}

DISTRESS_SCORECARD = {
    "axes": [
        {"name": "정량 분석", "weight": "0.30 (Merton 있을 때) / 0.40 (없을 때)", "models": ["ohlsonOScore", "altmanZppScore", "altmanZScore"]},
        {"name": "시장 기반", "weight": "0.20 (Merton 있을 때) / 0 (없을 때)", "models": ["mertonD2D"]},
        {"name": "이익 품질", "weight": "0.15 (Merton 있을 때) / 0.20 (없을 때)", "models": ["beneishMScore", "sloanAccrual", "piotroskiFScore"]},
        {"name": "추세 분석", "weight": "0.25 (Merton 있을 때) / 0.30 (없을 때)", "source": "anomaly (trendDeterioration, cccDeterioration)"},
        {"name": "감사 위험", "weight": 0.10, "source": "anomaly (audit, governance)"},
    ],
    "creditGrade": "AAA~D (S&P PD 매핑, 10단계)",
    "cashRunway": "현금 소진 예상 개월 수 + 유동성 경보",
    "riskFactors": "anomaly + ratios + Merton D2D에서 구조화된 위험 요인 자동 추출",
    "levels": ["safe (<15)", "watch (<30)", "warning (<50)", "danger (<70)", "critical (>=70)"],
}


def buildSpec() -> dict:
    """insight 엔진 스펙 반환."""
    return {
        "name": "insight",
        "description": "기업 분석 등급 (7영역 A~F) + 이상치 탐지 + 부실 예측 + 프로파일 분류",
        "summary": {
            "areas": list(AREAS.keys()),
            "grading": "A~F (6단계, 점수 기반)",
            "anomaly": f"룰 기반 {len(ANOMALY_DETECTORS)}개 탐지기",
            "distress": f"5축 부실 예측 스코어카드 ({len(DISTRESS_MODELS)}개 모델, Merton D2D 포함) + 신용등급 + 유동성 경보",
            "profile": "classifyProfile (수비형/공격형/성장형/가치형 등)",
        },
        "detail": {area: meta for area, meta in AREAS.items()},
        "anomalyDetectors": ANOMALY_DETECTORS,
        "distressModels": DISTRESS_MODELS,
        "distressScorecard": DISTRESS_SCORECARD,
    }
