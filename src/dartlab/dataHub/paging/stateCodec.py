"""Owner, resource, composite paging이 공유하는 continuation state 원시 codec.

세 paging lane 은 각자 다른 state 스키마를 쓰지만 그 스키마를 담는 JSON tree 규칙과
문자열, digest 검증은 같다. 이 모듈은 그 공통분만 갖는다. lane 마다 다른 것은 남긴다.
``_validateQueryPayload`` 는 state 스키마 자체가 달라 여기로 올리지 않고, composite lane 의
``_jsonLoad`` 는 canonical 왕복 검사를 같은 자리에서 하므로 ``loadStateJson`` 을 쓰지 않는다.
"""

from __future__ import annotations

import dataclasses
import json
import math
import re
from collections.abc import Mapping, Sequence
from typing import Any

from dartlab.dataHub.continuation import ContinuationError, canonicalJsonBytes

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


def loadStateJson(payload: bytes) -> Any:
    """중복 key 를 거부하며 lane 의 private state JSON 을 복원한다.

    Capabilities:
        UTF-8 디코드, JSON 파싱, 중복 key 거부를 한 묶음으로 처리하고 어느 단계에서
        깨져도 같은 continuation 오류로 올린다.

    Args:
        payload: continuation state 로 받은 raw bytes.

    Returns:
        복원한 JSON 값. 검증은 호출자가 자기 스키마로 이어서 한다.

    Raises:
        ContinuationError: UTF-8 이 아니거나 JSON 이 아니거나 중복 key 가 있을 때.

    Example:
        ``loadStateJson(b'{"version":2}')``

    Guide:
        canonical 왕복 검사가 필요한 lane 은 이 함수 밖에서 따로 한다. 검사 자리가
        lane 마다 달라 여기 넣으면 안 하는 lane 이 조용히 규칙을 얻는다.

    When:
        owner, resource lane 이 private state 나 query payload 를 읽을 때.

    How:
        ``json.loads`` 에 ``rejectDuplicateKeys`` 를 ``object_pairs_hook`` 으로 건다.

    SeeAlso:
        ``rejectDuplicateKeys``.

    Requires:
        payload 는 밖에서 온 바이트로 취급한다. 신뢰하지 않는다.

    AI Context:
        훼손과 정상 부재를 같은 값으로 만들지 않는다.
    """

    try:
        return json.loads(payload.decode("utf-8"), object_pairs_hook=rejectDuplicateKeys)
    except ContinuationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ContinuationError("CONTINUATION_CORRUPT") from None


def queryPayloadBytes(
    assetIds: Sequence[str],
    query: Any,
    *,
    formatVersion: int,
    pageKind: str,
    context: str,
    maxBytes: int,
) -> bytes:
    """lane 의 query identity 를 canonical bytes 로 굽고 state 예산을 지킨다.

    Capabilities:
        version, pageKind, assetIds, query 네 항목을 정해진 순서로 담아 canonical
        bytes 를 만들고 예산 초과를 fail-closed 로 끝낸다.

    Args:
        assetIds: 이 페이지가 묶은 asset ID 목록.
        query: canonical tree 로 펼 query.
        formatVersion: lane 의 state format 버전.
        pageKind: lane 식별자. 다른 lane 의 state 를 잘못 읽는 것을 막는다.
        context: ``strictTree`` 오류 문장에 쓸 lane 이름.
        maxBytes: state 한 벌의 바이트 상한.

    Returns:
        canonical JSON bytes. queryDigest 도 이 bytes 에서 뜬다.

    Raises:
        ContinuationError: 결과가 ``maxBytes`` 를 넘을 때.
        ValueError: query tree 에 유한하지 않은 float 나 cycle 이 있을 때.
        TypeError: strict JSON 으로 표현할 수 없는 값이 있을 때.

    Example:
        ``queryPayloadBytes(ids, query, formatVersion=2, pageKind="owner-subject-fanout",
        context="query", maxBytes=MAX_STATE_BYTES)``

    Guide:
        lane 마다 다른 것은 인자로만 들어온다. 굽는 순서와 예산 검사는 lane 이 못 바꾼다.

    When:
        owner, composite lane 이 continuation 을 발급하거나 이어읽기 요청을 검증할 때.

    How:
        ``strictTree`` 로 query 를 펴고 ``canonicalJsonBytes`` 로 굽는다.

    SeeAlso:
        ``strictTree``, ``dartlab.dataHub.continuation.canonicalJsonBytes``.

    Requires:
        같은 query 는 프로세스가 달라도 같은 bytes 여야 한다.

    AI Context:
        query identity 가 흔들리면 이어읽기가 다른 질문의 페이지를 잇는다.
    """

    payload = canonicalJsonBytes(
        {
            "version": formatVersion,
            "pageKind": pageKind,
            "assetIds": list(assetIds),
            "query": strictTree(query, context=context),
        }
    )
    if len(payload) > maxBytes:
        raise ContinuationError("CONTINUATION_STATE_BUDGET")
    return payload


__all__ = [
    "DIGEST_PATTERN",
    "loadStateJson",
    "queryPayloadBytes",
    "requireDigest",
    "requireOptionalText",
    "requireText",
    "strictTree",
]


def rejectDuplicateKeys(pairs: Any) -> dict[str, Any]:
    """중복 JSON key 를 거부하며 mapping 을 조립한다.

    `json.loads` 의 `object_pairs_hook` 으로만 쓴다. 기본 동작은 뒤 값이 앞 값을 덮어쓰는
    것인데, 이어보기 상태는 밖에서 온 바이트라 그 덮어쓰기가 곧 조작 통로가 된다. 같은 key 가
    두 번 나오면 어느 쪽이 진짜인지 정할 방법이 없으므로 훼손으로 끝낸다.

    네 lane 이 이 여섯 줄을 각자 갖고 있었다. `_jsonLoad` 자체는 canonical 왕복 검사 위치가
    lane 마다 달라 올리지 않지만, 이 안쪽 규칙은 셋이 글자까지 같았다.

    Args:
        pairs: JSON decoder 가 전달한 key 와 value 순서쌍.

    Returns:
        중복 key 가 없는 mapping.

    Raises:
        ContinuationError: 같은 key 가 두 번 나타날 때.

    Example:
        ``json.loads(payload, object_pairs_hook=rejectDuplicateKeys)``
    """
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContinuationError("CONTINUATION_CORRUPT")
        result[key] = value
    return result
