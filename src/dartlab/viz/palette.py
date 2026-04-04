"""DartLab 컬러 팔레트 — 단일 원천.

Python 측 모든 시각화가 이 모듈에서 색상을 가져온다.
JS 측: ``ui/shared/chart/colors.ts`` (동일 값, 주석으로 교차 참조).
"""

from __future__ import annotations

COLORS: list[str] = [
    "#ea4647",  # primary red
    "#fb923c",  # accent orange
    "#3b82f6",  # blue
    "#22c55e",  # green
    "#8b5cf6",  # purple
    "#06b6d4",  # cyan
    "#f59e0b",  # amber
    "#ec4899",  # pink
]
"""8색 팔레트. 인덱스로 순환 사용: ``COLORS[i % len(COLORS)]``."""
