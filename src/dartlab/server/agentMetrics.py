"""Chat-native vs workbench 호출 비율 추적.

memory/engineering.md 7절 의 회귀 방지 metric. agent_gateway 가 mode 결정 시
record() 호출. snapshot() 으로 누적 비율 조회.

룰 (plan Phase H-4):
- chat-native (agent) 비율 70% 이상 → 본체화 성공
- 30% 이하 → graph 강박 회귀 중. 알림.

확장: /api/metrics endpoint 또는 dev panel 에 노출 (별도 작업).
"""

from __future__ import annotations

import threading
from typing import Any

_LOCK = threading.Lock()
_COUNTS: dict[str, int] = {
    "agent": 0,  # runAgent — chat-native + tool calling
    "workbench": 0,  # WorkbenchLoop 5 패스 (LLM)
    "workbench-heuristic": 0,  # WorkbenchLoop 휴리스틱 (LLM 미해결)
}


def record(mode: str) -> None:
    """agent_gateway 의 분기 결과 기록."""
    if not mode:
        return
    with _LOCK:
        _COUNTS[mode] = _COUNTS.get(mode, 0) + 1


def snapshot() -> dict[str, Any]:
    """현재 누적 카운트 + chat-native 비율."""
    with _LOCK:
        counts = dict(_COUNTS)
    total = sum(counts.values())
    chat_ratio = counts.get("agent", 0) / total if total else 0.0
    return {
        "counts": counts,
        "total": total,
        "chat_native_ratio": chat_ratio,
        "regression_warning": total >= 10 and chat_ratio < 0.3,
    }


def reset() -> None:
    """테스트용."""
    with _LOCK:
        for key in _COUNTS:
            _COUNTS[key] = 0


__all__ = ["record", "snapshot", "reset"]
