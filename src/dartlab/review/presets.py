"""review 프리셋 -- 관점별 섹션 조합."""

from __future__ import annotations

PRESETS: dict[str, dict] = {
    "executive": {
        "sections": ["종합평가", "수익구조", "현금흐름", "가치평가"],
        "detail": False,
        "description": "경영진/투자자용 핵심 요약",
    },
    "audit": {
        "sections": ["이익품질", "재무정합성", "안정성", "지배구조", "공시변화"],
        "detail": True,
        "description": "감사/회계 검토용",
    },
    "credit": {
        "sections": ["안정성", "현금흐름", "자금조달", "효율성"],
        "detail": True,
        "description": "신용분석/여신심사용",
    },
    "growth": {
        "sections": ["수익구조", "성장성", "투자효율", "매출전망"],
        "detail": True,
        "description": "성장성 분석용",
    },
    "valuation": {
        "sections": ["가치평가", "수익성", "성장성", "매출전망"],
        "detail": True,
        "description": "밸류에이션 중심",
    },
}
