"""dataHub/identity/digestInput.py . ref digest 입력 직렬화 규칙."""

from __future__ import annotations

import dataclasses

import pytest

from dartlab.dataHub.identity.digestInput import digestInputBytes

pytestmark = pytest.mark.unit


@dataclasses.dataclass(frozen=True)
class _Point:
    """테스트용 dataclass."""

    x: int
    y: int


def test_sortsKeysAndDropsWhitespace() -> None:
    """key 정렬과 공백 제거로 같은 내용은 같은 bytes 가 된다."""
    assert digestInputBytes({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_flattensDataclassAndCollections() -> None:
    """dataclass, tuple, set 은 펴서 담는다."""
    assert digestInputBytes(_Point(1, 2)) == b'{"x":1,"y":2}'
    assert digestInputBytes({"ids": ("a", "b")}) == b'{"ids":["a","b"]}'


def test_keepsNonAsciiAsIs() -> None:
    """한글은 이스케이프하지 않는다."""
    assert digestInputBytes({"market": "한국"}) == '{"market":"한국"}'.encode()


def test_fallsBackToStringForUnknownTypes() -> None:
    """모르는 값은 거부하지 않고 문자열로 떨어뜨린다."""
    assert digestInputBytes({"v": object.__repr__}) != b""


def test_bothCallersShareOneSerializer() -> None:
    """universe snapshot 과 실행 영수증이 같은 함수 객체를 본다."""
    from dartlab.dataHub import execution, executionSupport
    from dartlab.dataHub.catalog import universe

    assert universe.digestInputBytes is digestInputBytes
    assert executionSupport.digestInputBytes is digestInputBytes
    assert execution.digestInputBytes is digestInputBytes
