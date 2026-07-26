"""Owner, resource, composite paging이 공유하는 continuation state 원시 codec.

세 paging lane 은 각자 다른 state 스키마를 쓰지만 그 스키마를 담는 JSON tree 규칙과
문자열, digest 검증은 같다. 이 모듈은 그 공통분만 갖는다. lane 마다 다른 것은 남긴다.
``_jsonLoad`` 는 canonical 왕복 검사 위치가 lane 마다 다르고 ``_validateQueryPayload`` 는
state 스키마 자체가 달라 여기로 올리지 않는다.
"""

from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Mapping
from typing import Any

from dartlab.dataHub.continuation import ContinuationError

DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def strictTree(value: Any, *, context: str, seen: set[int] | None = None) -> Any:
    """임의 fallback coercion 없이 canonical JSON tree를 만든다.

    Capabilities:
        dataclass, mapping, sequence를 strict JSON 값으로만 변환하고 cycle을 차단한다.

    Args:
        value: 변환할 값.
        context: 오류 문장에 쓸 state 이름. 예 ``"query"``, ``"composite state"``.
        seen: 재귀 cycle 탐지용 식별자 집합.

    Returns:
        str, bool, int, float, None, list, dict 로만 구성한 tree.

    Raises:
        ValueError: 유한하지 않은 float 또는 cycle이 있을 때.
        TypeError: strict JSON으로 표현할 수 없는 값이나 비 str mapping key일 때.

    Example:
        ``strictTree(query, context="query")``.

    Guide:
        continuation state를 직렬화하기 전 단계에서만 사용한다.

    When:
        owner, resource, composite paging state를 canonical bytes로 굽기 직전 호출한다.

    How:
        타입별로 분기하며 컨테이너 진입 전 식별자를 등록하고 이탈 시 해제한다.

    See Also:
        ``dartlab.dataHub.continuation.canonicalJsonBytes``.

    Requires:
        호출자는 lane 별 오류 문장을 구분하기 위해 ``context``를 명시해야 한다.

    AI Context:
        암묵 coercion 은 continuation identity 를 조용히 바꾸므로 허용하지 않는다.
    """

    activeSeen = set() if seen is None else seen
    if value is None or type(value) in {str, bool, int}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{context} float는 유한해야 합니다")
        return value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError(f"{context}에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            return {
                field.name: strictTree(getattr(value, field.name), context=context, seen=activeSeen)
                for field in dataclasses.fields(value)
            }
        finally:
            activeSeen.remove(identity)
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError(f"{context}에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            tree: dict[str, Any] = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise TypeError(f"{context} mapping key는 str이어야 합니다")
                tree[key] = strictTree(item, context=context, seen=activeSeen)
            return tree
        finally:
            activeSeen.remove(identity)
    if isinstance(value, (tuple, list)):
        identity = id(value)
        if identity in activeSeen:
            raise ValueError(f"{context}에 cycle이 있습니다")
        activeSeen.add(identity)
        try:
            return [strictTree(item, context=context, seen=activeSeen) for item in value]
        finally:
            activeSeen.remove(identity)
    raise TypeError(f"{context}에는 strict JSON 값만 허용됩니다")


def requireText(value: Any) -> str:
    """비어 있지 않은 str만 통과시킨다.

    Capabilities:
        continuation state 의 문자열 필드를 fail-closed 로 검증한다.

    Args:
        value: 검증할 값.

    Returns:
        검증된 문자열.

    Raises:
        ContinuationError: str이 아니거나 비었을 때.

    Example:
        ``requireText(root["assetId"])``.

    Guide:
        복원한 private state 필드에만 사용한다.

    When:
        continuation state 를 decode 한 직후 호출한다.

    How:
        타입과 공허 여부를 확인한다.

    See Also:
        ``requireOptionalText``와 ``requireDigest``.

    Requires:
        빈 문자열은 유효한 식별자가 아니다.

    AI Context:
        state corruption 은 일반 입력 오류와 구분해 continuation 오류로 올린다.
    """

    if type(value) is not str or not value:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return value


def requireOptionalText(value: Any) -> str | None:
    """``None``을 허용하되 값이 있으면 비어 있지 않은 str만 통과시킨다.

    Capabilities:
        선택 문자열 필드를 fail-closed 로 검증한다.

    Args:
        value: 검증할 값.

    Returns:
        ``None`` 또는 검증된 문자열.

    Raises:
        ContinuationError: 값이 있으나 유효한 str이 아닐 때.

    Example:
        ``requireOptionalText(root.get("cursor"))``.

    Guide:
        누락과 빈 문자열을 같게 취급하지 않는다.

    When:
        선택 cursor 나 sample 필드를 복원할 때 사용한다.

    How:
        ``None``이면 그대로 반환하고 아니면 ``requireText``에 위임한다.

    See Also:
        ``requireText``.

    Requires:
        호출자는 ``None``과 빈 문자열의 의미 차이를 유지해야 한다.

    AI Context:
        선택 필드를 빈 문자열로 정규화하면 identity 가 달라진다.
    """

    if value is None:
        return None
    return requireText(value)


def requireDigest(value: Any) -> str:
    """64자리 소문자 hex digest만 통과시킨다.

    Capabilities:
        state 안의 digest 필드 형식을 fail-closed 로 고정한다.

    Args:
        value: 검증할 값.

    Returns:
        검증된 digest 문자열.

    Raises:
        ContinuationError: str이 아니거나 digest 형식이 아닐 때.

    Example:
        ``requireDigest(root["contractHash"])``.

    Guide:
        source pin 과 contract hash 복원에 사용한다.

    When:
        continuation state 의 digest 필드를 읽을 때 호출한다.

    How:
        ``requireText`` 통과 후 hex 패턴을 검사한다.

    See Also:
        ``DIGEST_PATTERN``.

    Requires:
        digest 는 SHA-256 hex 소문자여야 한다.

    AI Context:
        형식이 다른 digest 는 다른 pin 이므로 조용히 받아들이지 않는다.
    """

    text = requireText(value)
    if DIGEST_PATTERN.fullmatch(text) is None:
        raise ContinuationError("CONTINUATION_CORRUPT")
    return text


__all__ = [
    "DIGEST_PATTERN",
    "requireDigest",
    "requireOptionalText",
    "requireText",
    "strictTree",
]
