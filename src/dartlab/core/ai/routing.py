from __future__ import annotations

AI_ROLES: tuple[str, ...] = ("analysis", "summary", "coding", "ui_control")
DEFAULT_ROLE = "analysis"


def normalize_role(role: str | None) -> str | None:
    if role is None:
        return None
    normalized = role.strip().lower()
    return normalized if normalized in AI_ROLES else None
