"""DartLab 공용 색상 토큰 — L0 단일 원천.

차트 spec을 만드는 frame/synth와 이를 표현하는 viz가 같은 의미 색상을 사용한다.
렌더러 구현이나 Plotly 의존성 없이 문자열·typing만 가진 순수 primitive다.
"""

from __future__ import annotations

from typing import Literal, TypedDict

COLORS: list[str] = [
    "#0ea5e9",
    "#f59e0b",
    "#f43f5e",
    "#10b981",
    "#8b5cf6",
    "#f97316",
    "#06b6d4",
    "#d946ef",
    "#84cc16",
    "#71717a",
]
"""Tailwind 500 categorical 10 — sky/amber/rose/emerald/violet/orange/cyan/fuchsia/lime/zinc."""

Intent = Literal["primary", "positive", "negative", "neutral", "accent"]

INTENT_MAP: dict[Intent, str] = {
    "primary": COLORS[0],
    "positive": COLORS[3],
    "negative": COLORS[2],
    "accent": COLORS[1],
    "neutral": COLORS[9],
}

Tone = Literal["light", "dark"]


class ToneColors(TypedDict):
    """light/dark 차트 프레임 색상."""

    axis: str
    grid: str
    background: str
    foreground: str


TONE_MAP: dict[Tone, ToneColors] = {
    "light": {
        "axis": "#52525b",
        "grid": "#e4e4e7",
        "background": "#ffffff",
        "foreground": "#18181b",
    },
    "dark": {
        "axis": "#a1a1aa",
        "grid": "#3f3f46",
        "background": "#09090b",
        "foreground": "#fafafa",
    },
}


def resolveColor(
    *,
    color: str | None = None,
    intent: Intent | None = None,
    key: str | None = None,
    override: dict[str, str] | None = None,
) -> str:
    """명시 override, color, intent, 기본색 순서로 series 색상을 결정한다."""
    if override:
        if key and key in override:
            return override[key]
        if intent and intent in override:
            return override[intent]
    if color:
        return color
    if intent:
        return INTENT_MAP.get(intent, COLORS[0])
    return COLORS[0]


__all__ = [
    "COLORS",
    "INTENT_MAP",
    "TONE_MAP",
    "Intent",
    "Tone",
    "ToneColors",
    "resolveColor",
]
