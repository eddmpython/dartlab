"""질문 유형별 선행 분석 레시피."""

from __future__ import annotations

RECIPES: dict[str, tuple[str, ...]] = {
    "건전성": ("health", "quality", "composite", "redFlags", "audit"),
    "수익성": ("profitability", "quality", "dupont"),
    "성장성": ("growth", "investment", "forecast"),
    "배당": ("dividend", "quality"),
    "리스크": ("risk", "composite", "redFlags", "audit"),
    "투자": ("investment", "growth", "forecast", "valuation", "simulation"),
    "지배구조": ("governance",),
    "종합": ("health", "profitability", "growth", "quality", "dupont", "composite", "redFlags", "forecast", "valuation"),
    "공시": ("redFlags",),
    "사업": ("business",),
    "관계사": ("governance", "redFlags"),
    "자본": ("health", "dividend"),
    "인력": ("business", "governance"),
}


def getRecipe(questionType: str) -> tuple[str, ...]:
    """질문 유형에 대응하는 레시피 step 목록을 반환한다."""
    return RECIPES.get(questionType, ())
