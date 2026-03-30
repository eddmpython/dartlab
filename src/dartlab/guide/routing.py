"""AI 역할(role) 정의 및 정규화."""

from __future__ import annotations

AI_ROLES: tuple[str, ...] = ("analysis", "summary", "coding", "ui_control")
DEFAULT_ROLE = "analysis"


def normalize_role(role: str | None) -> str | None:
    """role 문자열을 정규화. 알려진 role이면 반환, 아니면 None."""
    if role is None:
        return None
    normalized = role.strip().lower()
    return normalized if normalized in AI_ROLES else None
