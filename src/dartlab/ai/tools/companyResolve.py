"""Shared Company resolution helper for ai/tools/ callers.

`peerCompareN`, `scenarioOverlay` 등이 같은 11-line 사본을 박고 있었음 —
target 문자열 → `dartlab.Company(target)` 시도 → 예외 시 None.

`engineCall._resolveCompany` 는 `resolveFromText` fallback + `_quietExecutionNoise` context
까지 포함한 풍부 변형이라 본 SSOT 미사용 (의도). cli `ask._resolveCompany` 도 args 파싱이
달라 별개.
"""

from __future__ import annotations

from typing import Any


def resolveCompanyOrNone(target: str) -> Any | None:
    """target 문자열로 Company 생성 시도. 빈 입력·import 실패·생성 예외는 None."""
    if not target:
        return None
    try:
        from dartlab.company import Company
    except ImportError:
        return None
    try:
        return Company(target)
    except Exception:
        return None
