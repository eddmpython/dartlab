"""재무제표 계정 정렬 및 들여쓰기 레벨.

sortOrder.json(K-IFRS 기준)을 로드하여 모든 시장(KR/US/CN/JP)에서
동일한 계정 표시 순서와 들여쓰기를 제공한다.

snakeId 기준이므로 DART/EDGAR 매퍼의 mapToDart 결과와 직접 호환.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
_DATA_PATH = Path(__file__).parent / "sortOrder.json"
_sortOrderData: dict[str, dict] | None = None
_sortOrderLock = threading.Lock()


def _ensureLoaded() -> dict[str, dict]:
    global _sortOrderData
    if _sortOrderData is not None:
        return _sortOrderData
    with _sortOrderLock:
        if _sortOrderData is not None:
            return _sortOrderData
        with open(_DATA_PATH, encoding="utf-8") as f:
            _sortOrderData = json.load(f)
    return _sortOrderData


def sortOrder(sjDiv: str) -> dict[str, int]:
    """sj_div별 snakeId → 표시 순서.

    sortOrder.json의 sortOrder 값으로 정렬.
    CIS는 IS 정렬을 공유.

    Args:
        sjDiv: "BS", "IS", "CIS", "CF"

    Returns:
        {snakeId: 순서번호} dict. 순서번호가 작을수록 위에 표시.
    """
    data = _ensureLoaded()
    stmtKey = "IS" if sjDiv in ("IS", "CIS") else sjDiv
    stmtData = data.get(stmtKey, {})
    if not stmtData:
        return {}

    sortedItems = sorted(
        stmtData.items(),
        key=lambda kv: kv[1].get("sortOrder", 9999),
    )
    return {sid: i for i, (sid, _) in enumerate(sortedItems)}


def levelMap(sjDiv: str) -> dict[str, int]:
    """sj_div별 snakeId → 들여쓰기 레벨 (1=대분류, 2=중분류, 3=세분류).

    Args:
        sjDiv: "BS", "IS", "CIS", "CF"

    Returns:
        {snakeId: level} dict.
    """
    data = _ensureLoaded()
    stmtKey = "IS" if sjDiv in ("IS", "CIS") else sjDiv
    stmtData = data.get(stmtKey, {})
    return {sid: meta.get("level", 1) for sid, meta in stmtData.items()}


def sortSeries(
    series: dict[str, dict[str, list]],
) -> None:
    """시계열 dict를 표준 순서로 in-place 정렬.

    Args:
        series: {"BS": {snakeId: [...]}, "IS": {...}, "CF": {...}}
    """
    for sjDiv in list(series.keys()):
        order = sortOrder(sjDiv)
        if not order:
            continue
        maxOrd = len(order)
        sortedItems = sorted(
            series[sjDiv].items(),
            key=lambda kv: order.get(kv[0], maxOrd),
        )
        series[sjDiv] = dict(sortedItems)
