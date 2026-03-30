"""코드블록 실행 에이전트 + reflection.

CAPABILITIES-Driven 아키텍처에서 LLM은 코드블록을 생성하고,
시스템이 자동 실행 후 결과를 피드백한다.
tool calling은 사용하지 않는다.
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

from dartlab.ai.providers.base import BaseProvider

# ══════════════════════════════════════
# Reflection — 답변 자체 검증
# ══════════════════════════════════════

_REFLECTION_PROMPT = (
    "당신의 이전 답변을 검토하세요. 다음 기준으로 평가하고 개선하세요:\n"
    "1. **수치 근거**: 인용한 모든 수치에 출처(테이블명, 연도)가 있는가?\n"
    "2. **완전성**: 사용자 질문에 완전히 답했는가? 빠진 관점은?\n"
    "3. **근거 없는 주장**: 제공된 데이터로 뒷받침할 수 없는 주장이 있는가?\n\n"
    "문제가 있으면 수정된 답변을 작성하세요. 문제가 없으면 원본 답변을 그대로 반환하세요."
)


def _reflect_on_answer(provider: BaseProvider, messages: list[dict], answer: str) -> str:
    """답변 자체 검증 — 1회 reflection으로 품질 보완."""
    reflect_messages = [
        *messages,
        {"role": "assistant", "content": answer},
        {"role": "user", "content": _REFLECTION_PROMPT},
    ]
    response = provider.complete(reflect_messages)
    return response.answer if response.answer.strip() else answer
