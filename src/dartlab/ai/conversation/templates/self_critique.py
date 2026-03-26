"""Self-Critique 프롬프트 + Guided Generation 스키마."""

from __future__ import annotations

from typing import Any

# ══════════════════════════════════════
# Self-Critique (2-pass 응답 검토)
# ══════════════════════════════════════

SELF_CRITIQUE_PROMPT = """당신은 재무분석 응답의 품질 검토자입니다.
아래 응답을 다음 기준으로 검토하세요.

## 검토 기준
1. **데이터 정합성**: 인용된 수치가 제공된 데이터와 일치하는가?
2. **테이블 사용**: 수치 2개 이상이면 마크다운 테이블을 사용했는가?
3. **해석 제공**: 숫자만 나열하지 않고 "왜?"와 "그래서?"를 설명했는가?
4. **출처 명시**: 수치 인용 시 테이블명과 연도를 표기했는가?
5. **결론 존재**: 명확한 판단과 근거 요약이 있는가?

## 응답 형식
문제가 없으면 "PASS"만 출력하세요.
문제가 있으면 아래 형식으로 수정 제안을 출력하세요:

ISSUES:
- [기준번호] 구체적 문제 설명

REVISED:
(수정된 전체 응답)
"""

# ══════════════════════════════════════
# Guided Generation — JSON 구조 강제 (Ollama)
# ══════════════════════════════════════

GUIDED_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "핵심 요약 1~2문장",
        },
        "metrics": {
            "type": "array",
            "description": "분석 지표 3~8개",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "지표명"},
                    "value": {"type": "string", "description": "값 (예: 45.2%)"},
                    "year": {"type": "string", "description": "연도"},
                    "trend": {"type": "string", "description": "한 단어: 개선/악화/유지/급등/급락"},
                    "assessment": {"type": "string", "description": "한 단어: 양호/주의/위험/우수"},
                },
                "required": ["name", "value", "year", "trend", "assessment"],
            },
        },
        "positives": {
            "type": "array",
            "description": "긍정 신호 1~3개",
            "items": {"type": "string"},
        },
        "risks": {
            "type": "array",
            "description": "리스크 0~3개",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "severity": {"type": "string", "description": "낮음/보통/높음"},
                },
                "required": ["description", "severity"],
            },
        },
        "grade": {
            "type": "string",
            "description": "종합 등급 (A+/A/B+/B/B-/C/D/F 또는 양호/보통/주의/위험)",
        },
        "conclusion": {
            "type": "string",
            "description": "결론 2~3문장, 근거 요약 포함",
        },
    },
    "required": ["summary", "metrics", "positives", "risks", "grade", "conclusion"],
}

# ══════════════════════════════════════
# 응답 메타데이터 추출 패턴
# ══════════════════════════════════════

SIGNAL_KEYWORDS = {
    "positive": ["양호", "우수", "안정", "개선", "성장", "흑자", "증가"],
    "negative": ["위험", "주의", "악화", "하락", "적자", "감소", "취약"],
}
