"""EDGAR panel mapper 파사드 회귀.

`panel/mapper.py` 는 DART 의 `panel.mapper` 와 같은 깊이에 이름을 맞추려고 둔 재export
파사드다. 구현은 `panel/build/mapper.py` 가 소유하고 그쪽 회귀는 형제 폴더에 있다.
여기서 지키는 것은 파사드가 구현과 어긋나지 않는다는 것 하나다. 재export 는 본문에서
쓰이지 않아 자동 도구가 미사용 import 로 오판하기 쉽고, 실제로 이 저장소에서 그렇게
걷혀 나간 적이 있다.
"""

from __future__ import annotations

import dartlab.providers.edgar.panel.build.mapper as implementation
import dartlab.providers.edgar.panel.mapper as facade


def test_facade_exports_exactly_what_all_declares() -> None:
    """`__all__` 에 적은 이름이 전부 실재해야 한다. 하나라도 걷히면 소비자가 깨진다."""

    missing = [name for name in facade.__all__ if not hasattr(facade, name)]
    assert missing == []


def test_facade_names_are_the_same_objects_as_the_implementation() -> None:
    """파사드는 복사본이 아니라 같은 객체를 가리켜야 한다."""

    for name in facade.__all__:
        assert getattr(facade, name) is getattr(implementation, name), name


def test_facade_holds_no_logic_of_its_own() -> None:
    """구현이 파사드로 새어 나오면 두 곳이 서로 다른 진실을 갖게 된다."""

    owned = {
        name
        for name, value in vars(facade).items()
        if not name.startswith("__") and getattr(value, "__module__", None) == facade.__name__
    }
    assert owned == set()
