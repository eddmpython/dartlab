"""event 엔진 스펙 — 코드에서 자동 추출."""

from __future__ import annotations


def buildSpec() -> dict:
    """event 엔진 스펙 반환."""
    return {
        "name": "event",
        "description": "공시 발표일 전후 주가 비정상 수익률(CAR) 분석 — Event Study",
        "summary": {
            "models": ["Market Adjusted"],
            "metrics": ["CAR", "BHAR", "t-stat", "p-value"],
            "defaultWindow": "(-10, +20)",
            "dependency": "yfinance (optional)",
        },
        "detail": {
            "analysisSteps": [
                "filings() → 공시 발표일 목록",
                "yfinance → 종목 + 시장 일별 수익률",
                "Market Adjusted AR = R_stock - R_market",
                "CAR = 누적 비정상 수익률",
                "BHAR = 매수-보유 비정상 수익률",
                "t-test 유의성 검정",
            ],
            "eventTypes": [
                "사업보고서",
                "분기보고서",
                "반기보고서",
                "주요사항보고서",
                "10-K",
                "10-Q",
            ],
            "leakageDetection": "pre_car > 2% → 사전 정보 유출 징후",
            "publicAPI": [
                "Company.eventStudy() — 전체 공시 주가 영향",
                "Company.eventStudy(event_type=) — 유형별 필터",
                "Company.eventStudy(window=EventWindow(-5, 10)) — 커스텀 윈도우",
            ],
        },
    }
