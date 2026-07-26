"""panel spine 조회 회귀.

`read.readWide` 가 wide 각 행의 identity 로 이 표를 찾아 정부 문서 순서대로 정렬한다.
표가 비거나 미등재를 0 으로 돌려주면 정렬이 조용히 뭉개져 패널 행 순서가 원본과
달라진다. 그 경계를 못 박는다.
"""

from __future__ import annotations

from dartlab.providers.dart.panel.spine import SPINE, chapterRankOf, spineOrderOf
from dartlab.providers.dart.panel.spine.lookup import SPINE as implementationSpine


def testFacadeAndImplementationShareOneTable() -> None:
    """파사드가 표를 복사하면 두 곳이 서로 다른 순서를 갖게 된다."""

    assert SPINE is implementationSpine


def testSpineTableIsNotEmpty() -> None:
    """표가 비면 모든 행이 미등재가 되어 정렬이 통째로 사라진다."""

    assert len(SPINE) > 0


def testEveryEntryCarriesOrderAndChapterRank() -> None:
    """항목은 (순서, 부모, 챕터순위) 셋을 갖춘다. 하나라도 빠지면 조회가 깨진다."""

    for identity, entry in SPINE.items():
        assert isinstance(identity, str) and identity
        spineOrder, parentKey, chapterRank = entry
        assert isinstance(spineOrder, int)
        assert parentKey is None or isinstance(parentKey, str)
        assert isinstance(chapterRank, int)


def testLookupsAgreeWithTheTable() -> None:
    """두 조회 함수는 표에서 각각 첫째와 셋째를 꺼낸다."""

    identity = next(iter(SPINE))
    spineOrder, _parentKey, chapterRank = SPINE[identity]

    assert spineOrderOf(identity) == spineOrder
    assert chapterRankOf(identity) == chapterRank


def testUnregisteredIdentityReturnsNoneNotZero() -> None:
    """미등재를 0 으로 돌려주면 맨 앞으로 끌려 올라가 원본 순서가 뒤집힌다."""

    assert spineOrderOf("__nonexistent__") is None
    assert chapterRankOf("__nonexistent__") is None


def testBlankIdentityIsTreatedAsUnregistered() -> None:
    """빈 identity 도 미등재다. 빈 문자열이 표에 실려 있으면 안 된다."""

    assert spineOrderOf("") is None
    assert chapterRankOf("") is None
