"""Owner, resource, composite paging이 공유하는 state codec tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pytest

from dartlab.dataHub.continuation import ContinuationError, canonicalJsonBytes
from dartlab.dataHub.pagingStateCodec import (
    requireDigest,
    requireOptionalText,
    requireText,
    strictTree,
)

_DIGEST = "a" * 64


@dataclass(frozen=True)
class _Nested:
    name: str
    ratio: float


@dataclass(frozen=True)
class _Root:
    label: str
    child: _Nested
    items: tuple[int, ...]


def testStrictTreeConvertsDataclassMappingAndSequence() -> None:
    tree = strictTree(_Root("root", _Nested("child", 0.5), (1, 2)), context="query")

    assert tree == {
        "label": "root",
        "child": {"name": "child", "ratio": 0.5},
        "items": [1, 2],
    }
    assert canonicalJsonBytes(tree)


def testStrictTreeUsesContextInEveryFailureMessage() -> None:
    with pytest.raises(ValueError, match="composite state float"):
        strictTree(float("nan"), context="composite state")
    with pytest.raises(TypeError, match="resource state mapping key"):
        strictTree({1: "x"}, context="resource state")
    with pytest.raises(TypeError, match="query에는 strict JSON"):
        strictTree(object(), context="query")


def testStrictTreeRejectsCyclesInEveryContainerKind() -> None:
    mapping: dict[str, Any] = {}
    mapping["self"] = mapping
    with pytest.raises(ValueError, match="cycle"):
        strictTree(mapping, context="query")

    sequence: list[Any] = []
    sequence.append(sequence)
    with pytest.raises(ValueError, match="cycle"):
        strictTree(sequence, context="query")


def testStrictTreeAllowsRepeatedSiblingWithoutFalseCycle() -> None:
    """같은 객체를 형제로 두 번 참조하는 것은 cycle이 아니다."""

    shared = {"value": 1}
    tree = strictTree({"left": shared, "right": shared}, context="query")

    assert tree == {"left": {"value": 1}, "right": {"value": 1}}


@pytest.mark.parametrize("value", ["", None, 1, True, b"x"])
def testRequireTextRejectsEmptyAndNonText(value: object) -> None:
    with pytest.raises(ContinuationError) as captured:
        requireText(cast(Any, value))
    assert captured.value.code == "CONTINUATION_CORRUPT"


def testRequireOptionalTextKeepsNoneDistinctFromEmpty() -> None:
    assert requireOptionalText(None) is None
    assert requireOptionalText("cursor") == "cursor"
    with pytest.raises(ContinuationError):
        requireOptionalText("")


@pytest.mark.parametrize("value", ["a" * 63, "a" * 65, "A" * 64, "g" * 64, ""])
def testRequireDigestRejectsAnythingButLowercaseHex64(value: str) -> None:
    with pytest.raises(ContinuationError) as captured:
        requireDigest(value)
    assert captured.value.code == "CONTINUATION_CORRUPT"


def testRequireDigestAcceptsCanonicalDigest() -> None:
    assert requireDigest(_DIGEST) == _DIGEST
