"""digest 를 뜨기 직전 값을 결정적 JSON bytes 로 펴는 관대한 직렬화.

``continuation.canonicalJsonBytes`` 는 표현할 수 없는 값을 거부한다. 반대로 universe
snapshot 과 실행 영수증의 ref 는 provider 가 넣어 둔 임의 객체가 섞여 들어와도 ref 자체는
나와야 한다. 그래서 dataclass, mapping, collection 을 펴고 남는 것은 문자열로 떨어뜨린다.

거부하는 직렬화와 떨어뜨리는 직렬화는 서로 대체재가 아니다. continuation identity 처럼
값이 조용히 바뀌면 안 되는 자리에는 이 모듈을 쓰지 않는다.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping
from typing import Any


def digestInputBytes(value: Any) -> bytes:
    """ref digest 입력을 결정적 JSON bytes 로 만든다.

    Args:
        value: JSON 트리. dataclass, mapping, tuple, set 이 섞여 있어도 된다.

    Returns:
        bytes. key 를 정렬하고 공백을 없앤 UTF-8 JSON.

    Raises:
        ValueError: 컨테이너에 순환 참조가 있을 때 (``json`` 이 올린다).

    Example:
        >>> digestInputBytes({"market": "KR", "ids": ("a", "b")})
        b'{"ids":["a","b"],"market":"KR"}'
    """

    def serializeDefault(item: Any) -> Any:
        """JSON encoder 가 직접 처리하지 못한 값을 결정적 표현으로 바꾼다."""

        if dataclasses.is_dataclass(item):
            return {field.name: getattr(item, field.name) for field in dataclasses.fields(item)}
        if isinstance(item, Mapping):
            return dict(item)
        if isinstance(item, (tuple, set, frozenset)):
            return list(item)
        return str(item)

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=serializeDefault,
    ).encode()
