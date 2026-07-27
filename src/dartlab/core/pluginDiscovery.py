"""등록 트리거용 플러그인 모듈을 레지스트리마다 한 번씩만 import 한다.

dartlab 은 PEP 562 lazy attribute 라 패키지를 import 해도 하위 provider 모듈이 안 올라온다.
그래서 각 레지스트리는 처음 쓰일 때 자기가 아는 모듈 목록을 명시적으로 import 해서 그 모듈들이
스스로를 등록하게 한다.

이 열세 줄이 core 안에서 열한 벌 복사돼 있었다. 다른 것은 모듈 목록 상수 이름 하나뿐이고
나머지는 글자까지 같았다. 그렇게 두면 셋째 사본을 만들 때 옆에서 복사하게 되고, 한 곳에서
`except ImportError` 를 넓히거나 로그를 붙여도 나머지 열은 그대로 남는다.

키는 호출하는 모듈 이름이다. 레지스트리마다 한 번이라는 뜻을 그대로 담는다.
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Iterable, Mapping
from typing import Any

_log = logging.getLogger(__name__)

_DISCOVERED: set[str] = set()


def discoverOnce(registryKey: str, moduleNames: Iterable[str]) -> None:
    """등록 트리거 모듈을 registryKey 마다 한 번만 import 한다.

    Args:
        registryKey: 레지스트리 식별자. 호출 모듈의 ``__name__`` 을 그대로 쓴다.
        moduleNames: import 할 모듈 경로들. 없는 모듈은 건너뛴다. 선택 의존성이
            빠진 설치에서도 나머지 provider 는 등록돼야 하기 때문이다.

    Returns:
        없음. 부수효과는 모듈 import 뿐이다.

    Raises:
        없음. ``ImportError`` 는 선택 의존성 부재로 보고 넘어간다. 그 밖의 예외는
        모듈 자체가 잘못된 것이므로 그대로 올려 보낸다.

    Example:
        ``discoverOnce(__name__, _KNOWN_PROVIDER_MODULES)``
    """
    if registryKey in _DISCOVERED:
        return
    # 먼저 표시한다. 아래에서 import 하는 모듈이 다시 이 함수를 부르는 경우가 있어서,
    # 나중에 표시하면 같은 목록을 무한히 다시 돈다.
    _DISCOVERED.add(registryKey)
    for modulePath in moduleNames:
        try:
            importlib.import_module(modulePath)
        except ImportError as exc:
            # 없는 선택 의존성은 넘어가되 흔적은 남긴다. 이유를 안 적으면 "그 provider 를
            # 안 쓰기로 했다" 와 "설치가 깨져서 못 올렸다" 가 결과만 봐서는 같아 보인다.
            _log.debug("플러그인 모듈을 못 올려 건너뛴다 (%s: %s)", modulePath, exc)
            continue


def resetDiscovery() -> None:
    """탐색 기록을 지운다. 테스트가 등록 경로를 다시 태울 때만 쓴다."""
    _DISCOVERED.clear()


__all__ = ["discoverOnce", "resetDiscovery"]


def lazyAttribute(moduleName: str, lazyMap: Mapping[str, str], name: str) -> Any:
    """모듈 이름 하나를 접근 시점에 풀어 준다. 파사드의 ``__getattr__`` 전용.

    파사드 `__init__` 이 무거운 하위 모듈을 위에서 import 하면 두 가지가 터진다. 쓰지도
    않을 것을 매번 올려 시작이 느려지고, 파사드와 하위가 서로를 가리킬 때 순환이 된다.
    그래서 이름과 모듈 경로만 표로 들고 있다가 실제로 꺼낼 때 올린다.

    다섯 파사드가 이 다섯 줄을 각자 갖고 있었다. 없는 이름에 무엇을 던지느냐가 특히
    중요하다. `AttributeError` 가 아니면 `hasattr` 과 `getattr(..., default)` 가
    깨지고, 파사드가 없는 속성을 물어본 쪽이 예외로 죽는다.

    Args:
        moduleName: 부르는 모듈의 ``__name__``. 오류 문구에 그대로 들어간다.
        lazyMap: 이름에서 모듈 경로로 가는 표.
        name: 꺼내려는 속성 이름.

    Returns:
        해당 모듈에서 꺼낸 속성.

    Raises:
        AttributeError: 표에 없는 이름일 때. 파이썬이 기대하는 그 예외다.
    """
    modulePath = lazyMap.get(name)
    if modulePath is None:
        raise AttributeError(f"module {moduleName!r} has no attribute {name!r}")
    return getattr(importlib.import_module(modulePath), name)
