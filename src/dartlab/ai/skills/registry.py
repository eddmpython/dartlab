"""스킬 레지스트리 — 분석 목표 기반 워크플로우 매칭.

Skill은 도구를 지정하지 않는다.
분석 목표(analysisGoals)와 종합 가이드(synthesisGuide)만 선언하고,
LLM이 현재 가용한 도구 중에서 자율 선택한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Skill:
    """분석 워크플로우 정의."""

    id: str
    name: str
    triggerKeywords: tuple[str, ...]
    analysisGoals: tuple[str, ...]
    synthesisGuide: str
    checkpoints: tuple[str, ...] = field(default_factory=tuple)

    def toPrompt(self) -> str:
        """시스템 프롬프트에 주입할 자연어 가이드."""
        goals = "\n".join(f"  {i + 1}. {g}" for i, g in enumerate(self.analysisGoals))
        checks = ""
        if self.checkpoints:
            checks = "\n**자체 검증:**\n" + "\n".join(f"  - {c}" for c in self.checkpoints)
        return f"## 분석 스킬: {self.name}\n\n**분석 목표:**\n{goals}\n\n**종합 프레임:** {self.synthesisGuide}{checks}"


def matchSkill(
    question: str,
    questionType: str | None = None,
) -> Skill | None:
    """질문에 가장 적합한 스킬 매칭."""
    from dartlab.ai.skills.catalog import SKILLS

    # 1차: questionType으로 직접 매칭
    if questionType:
        for skill in SKILLS:
            if questionType in skill.triggerKeywords:
                return skill

    # 2차: 질문 텍스트 키워드 매칭
    if not question:
        return None

    bestSkill: Skill | None = None
    bestScore = 0
    for skill in SKILLS:
        score = sum(1 for kw in skill.triggerKeywords if kw in question)
        if score > bestScore:
            bestScore = score
            bestSkill = skill

    return bestSkill if bestScore > 0 else None
