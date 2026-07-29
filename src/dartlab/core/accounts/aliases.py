"""snakeId alias — DART ↔ EDGAR 동일 개념 통합 (옛 ``labels.SNAKEID_ALIASES``).

``SNAKEID_ALIASES`` 는 SSOT ``layers.snakeAlias`` 에서 로드하되 *module-level 단일
dict 객체* 의 identity 를 보존한다 (5+ 소비처가 ``from ... import SNAKEID_ALIASES``
로 참조하고, EDGAR 측이 ``EDGAR_TO_DART_ALIASES = SNAKEID_ALIASES`` 로 동일 객체를
재-export 하기 때문). ``reset()`` 은 rebind 가 아니라 in-place clear+update 로
identity 를 유지한 채 내용만 갱신한다.
"""

from __future__ import annotations

from dartlab.core.accounts.data import loadAccounts

# module-level 단일 객체 — identity 보존 (소비처가 by-reference import)
SNAKEID_ALIASES: dict[str, str] = {}


def _compileAliasGraph(aliases: dict[str, str]) -> dict[str, str]:
    """alias graph를 terminal canonical로 평탄화하고 순환을 거부한다.

    Args:
        aliases: ``alias -> canonical`` 원본 매핑.

    Returns:
        self edge를 제외하고 모든 target이 terminal인 새 매핑.

    Raises:
        ValueError: 두 개 이상 노드가 순환하거나 빈 key 또는 value가 있을 때.
    """

    compiled: dict[str, str] = {}
    for source in aliases:
        if not source or not aliases[source]:
            raise ValueError("snakeAlias에는 빈 key 또는 value를 둘 수 없습니다.")
        path = [source]
        target = aliases[source]
        while target in aliases and aliases[target] != target:
            if target in path:
                cycle = " -> ".join([*path, target])
                raise ValueError(f"snakeAlias 순환 참조: {cycle}")
            path.append(target)
            target = aliases[target]
        if source != target:
            compiled[source] = target
    return compiled


def _populate() -> None:
    SNAKEID_ALIASES.clear()
    SNAKEID_ALIASES.update(_compileAliasGraph(loadAccounts()["layers"]["snakeAlias"]))


_populate()


def reset() -> None:
    """SNAKEID_ALIASES 내용을 SSOT 에서 in-place 재로드 (identity 보존).

    Args:
        없음.

    Returns:
        None.

    Raises:
        ValueError: SSOT alias graph에 순환이나 빈 key 또는 value가 있을 때.

    Example:
        >>> from dartlab.core.accounts import aliases
        >>> aliases.reset()
    """
    _populate()


def mergeAliasRows(
    rowMap: dict[str, dict],
    *,
    metaCols: set[str] | None = None,
) -> set[str]:
    """SNAKEID_ALIASES 양방향 row 머지 — 단일 진실의 원천 (SSOT).

    같은 개념이 두 snakeId 로 분리된 케이스 (예: ``cash_flows_from_financing_activities``
    ↔ ``financing_cashflow``) 를 한 row 로 in-place 합친다. col 별 not-null 우선.
    canonical row 만 살아남고 alias row 는 제거 대상으로 분류.

    DART pivot (``_financeToDataFrame``) 과 calc 헬퍼 (``toDictBySnakeId``)
    양쪽 모두 이 함수를 호출 — 머지 로직은 이 한 곳에만 존재.

    Args:
        rowMap: ``{snakeId: row_dict}``. row_dict 는 in-place 수정됨.
        metaCols: 머지 대상에서 제외할 메타 컬럼. None 이면
            ``{"snakeId", "항목", "_level", "_sort"}`` default. calc dict 머지에선
            ``set()`` 전달.

    Returns:
        머지된 (= 제거 대상) alias snakeId set.

    Raises:
        없음.

    Example:
        >>> merged = mergeAliasRows({"revenue": {"v": 1}, "sales": {"v": None}}, metaCols=set())
        >>> "revenue" in merged
        True
    """
    if metaCols is None:
        metaCols = {"snakeId", "항목", "_level", "_sort"}
    mergedSnakeIds: set[str] = set()
    for alias, canonical in SNAKEID_ALIASES.items():
        if alias == canonical:
            continue
        aRow = rowMap.get(alias)
        cRow = rowMap.get(canonical)
        if aRow is None or cRow is None:
            continue
        for col, val in aRow.items():
            if col in metaCols:
                continue
            if cRow.get(col) is None and val is not None:
                cRow[col] = val
        mergedSnakeIds.add(alias)
    return mergedSnakeIds
