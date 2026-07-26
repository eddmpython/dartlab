"""panel spine 조회. identity 로 정부 문서 순서를 O(1) 로 찾는다.

원래 `spine/__init__.py` 본문에 있었다. `__init__` 은 재export 파사드여야 하고 로직은
형제 모듈이 소유한다. 생성물인 `spineData.py` 와 조회 코드가 한 폴더에 나란히 서는
모양이 되어 어느 쪽이 사람이 고치는 파일인지도 분명해진다.
"""

from __future__ import annotations

from .spineData import SPINE_ROWS

# identity → (spineOrder, parentKey, chapterRank). module-level 1회 (누적 0).
SPINE: dict[str, tuple[int, str | None, int]] = {
    ident: (spineOrder, parentKey, chapterRank) for ident, spineOrder, parentKey, chapterRank in SPINE_ROWS
}


def spineOrderOf(identity: str) -> int | None:
    """identity → 정부 문서 표시순서 (미등재 None).

    Args:
        identity: rowIdentity 결과 (canonicalKey 또는 NARR::chapter␟section).

    Returns:
        spineOrder(int) 또는 None (spine 미등재).

    Raises:
        없음.

    Example:
        >>> spineOrderOf("__nonexistent__") is None
        True

    SeeAlso:
        - ``chapterRankOf`` — 챕터 대순서.
        - ``read.readWide`` — 본 lookup 으로 wide 정렬.

    Requires:
        - 없음 (module-level dict).

    Capabilities:
        - 한 행 identity 의 정부 서식 순서를 O(1) 조회.

    Guide:
        - readWide 가 일괄 map. 직접 호출 가능.

    AIContext:
        - 순수 dict get — 부작용 0.

    LLM Specifications:
        AntiPatterns:
            - 미등재에 임의 order 부여 금지 — None(read 가 말미 처리).
        OutputSchema:
            - ``int | None``.
        Prerequisites:
            - SPINE dict.
        Freshness:
            - spineData 재생성 반영.
        Dataflow:
            - identity → SPINE → spineOrder.
        TargetMarkets:
            - KR + US 공통.
    """
    entry = SPINE.get(identity)
    return entry[0] if entry else None


def chapterRankOf(identity: str) -> int | None:
    """identity → 챕터 대순서 rank (미등재 None).

    Args:
        identity: rowIdentity 결과.

    Returns:
        chapterRank(int) 또는 None (spine 미등재).

    Raises:
        없음.

    Example:
        >>> chapterRankOf("__nonexistent__") is None
        True

    SeeAlso:
        - ``spineOrderOf`` — 문서 표시순서.
        - ``read.readWide`` — (chapterRank, spineOrder) 정렬.

    Requires:
        - 없음.

    Capabilities:
        - 챕터(I~XII) 대순서를 O(1) 조회 — 같은 챕터 내 spineOrder 세부 정렬.

    Guide:
        - readWide 가 1차 정렬키로 사용. 직접 호출 가능.

    AIContext:
        - 순수 dict get.

    LLM Specifications:
        AntiPatterns:
            - 미등재에 임의 rank 부여 금지 — None.
        OutputSchema:
            - ``int | None``.
        Prerequisites:
            - SPINE dict.
        Freshness:
            - spineData 재생성 반영.
        Dataflow:
            - identity → SPINE → chapterRank.
        TargetMarkets:
            - KR + US 공통.
    """
    entry = SPINE.get(identity)
    return entry[2] if entry else None


__all__ = ["SPINE", "chapterRankOf", "spineOrderOf"]
