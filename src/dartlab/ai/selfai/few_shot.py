"""Few-Shot 주입기 — 질문에 맞는 스킬을 검색하여 프롬프트에 동적 주입.

core.py의 _buildSystemPromptParts()에서 동적 프롬프트 부분에
유사 질문의 성공 코드 예시를 삽입하여 LLM의 도구 선택 정확도를 높인다.
"""

from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# few-shot 블록 최대 크기 (프롬프트 토큰 절약)
_MAX_CHARS = 1500


def getFewShots(question: str, *, limit: int = 2) -> str:
    """질문에 맞는 스킬을 검색하여 few-shot 프롬프트 블록 생성.

    Args:
        question: 사용자 질문
        limit: 주입할 최대 예시 수

    Returns:
        프롬프트에 주입할 few-shot 블록 (빈 문자열이면 해당 없음)
    """
    try:
        from dartlab.ai.selfai.skill_library import search
    except ImportError:
        return ""

    skills = search(question, limit=limit)
    if not skills:
        return ""

    parts = ["\n\n## 유사 질문 성공 예시 (자동 검색)\n"]

    total_chars = 0
    for skill in skills:
        tools = json.loads(skill.tools_used) if skill.tools_used else []
        tools_str = ", ".join(tools) if tools else "?"

        block = (
            f"\n### Q: {skill.question}\n"
            f"도구: {tools_str}\n"
            f"```python\n{skill.code_template}\n```\n"
        )

        if total_chars + len(block) > _MAX_CHARS:
            break

        parts.append(block)
        total_chars += len(block)

    if len(parts) <= 1:
        return ""

    return "".join(parts)


def recordSkillFromExecution(
    question: str,
    code: str,
    result: str,
    is_error: bool,
) -> None:
    """코드 실행 성공 시 스킬을 자동 저장.

    core.py에서 코드 실행 후 호출하여 성공 패턴을 자동 축적.
    에러인 경우는 저장하지 않는다.
    """
    if is_error:
        return

    # 너무 짧은 결과는 의미 없음 (빈 출력 등)
    if len(result.strip()) < 50:
        return

    try:
        from dartlab.ai.selfai.skill_library import save

        save(question=question, code=code)
    except ImportError:
        pass
