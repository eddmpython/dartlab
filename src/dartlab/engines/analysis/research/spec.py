"""research 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations

QUANT_MODELS = {
    "piotroski": {
        "label": "Piotroski F-Score",
        "description": "9개 바이너리 시그널 (수익4 + 건전3 + 효율2)",
        "range": "0-9",
    },
    "magicFormula": {
        "label": "Magic Formula",
        "description": "Greenblatt ROIC + Earnings Yield",
    },
    "qmj": {
        "label": "Quality Minus Junk",
        "description": "AQR 4-pillar (수익성, 성장, 안전, 배당)",
    },
    "lynchFairValue": {
        "label": "Lynch Fair Value",
        "description": "EPS CAGR × EPS, PEG ratio",
    },
    "buffettOwnerEarnings": {
        "label": "Buffett Owner Earnings",
        "description": "OCF - 유지보수 CAPEX",
    },
    "dupont": {
        "label": "DuPont 3-Factor",
        "description": "순이익률 × 자산회전율 × 레버리지",
    },
}

REPORT_SECTIONS = [
    "executive",
    "thesis",
    "overview",
    "sectorKpis",
    "financial",
    "earningsQuality",
    "quantScores",
    "marketData",
    "forecast",
    "insightDetails",
    "valuationAnalysis",
    "riskAnalysis",
    "peerAnalysis",
    "narrativeAnalysis",
]


def buildSpec() -> dict:
    """research 엔진 스펙."""
    return {
        "name": "research",
        "description": "종합 기업분석 리포트 — 종목코드 하나로 equity research 생성",
        "summary": {
            "sections": len(REPORT_SECTIONS),
            "quantModels": len(QUANT_MODELS),
            "method": "dartlab.research('005930') 또는 c.research()",
        },
        "detail": {
            "sections": REPORT_SECTIONS,
            "quantModels": QUANT_MODELS,
            "dataSources": [
                "finance (BS/IS/CF/ratios/timeseries)",
                "insight (10영역 등급 + 상세 + distress + anomalies)",
                "analyst (DCF/DDM/상대가치 밸류에이션)",
                "gather (주가/컨센서스/수급/거시)",
                "sector (WICS 분류 + 섹터 배수)",
                "esg (ESG 공시 분석)",
                "forecast (자체 매출 예측)",
            ],
        },
    }
