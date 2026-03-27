"""분석 스킬 — 프롬프트 기반 워크플로우 가이드.

도구를 지정하지 않고 분석 목표만 선언한다.
LLM이 현재 가용한 도구 중에서 자율 선택.
"""

from dartlab.ai.skills.registry import Skill, matchSkill

__all__ = ["Skill", "matchSkill"]
