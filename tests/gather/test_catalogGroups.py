"""gather/catalogGroups.py 미러 . 매크로 카탈로그 그룹 해소 규칙."""

from __future__ import annotations

import pytest

from dartlab.gather.catalogGroups import resolveGroupIds

pytestmark = pytest.mark.unit


class _Catalog:
    """테스트용 정적 카탈로그."""

    def __init__(self, groups: dict[str, list[str]]) -> None:
        self._groups = groups

    def getGroupIds(self, name: str) -> list[str]:
        """그룹 이름에 속한 ID 목록."""
        return list(self._groups.get(name, []))

    def getGroups(self) -> list[str]:
        """등록된 그룹 이름 전체."""
        return list(self._groups)


def test_returnsIdsWhenGroupExists() -> None:
    """등록된 그룹은 ID 목록을 그대로 돌려준다."""
    catalog = _Catalog({"rates": ["A", "B"]})
    assert resolveGroupIds(catalog, "rates") == ["A", "B"]


def test_raisesWithAvailableGroups() -> None:
    """없는 그룹은 가용 목록을 붙여 끝낸다. 빈 목록을 흘리지 않는다."""
    catalog = _Catalog({"rates": ["A"], "prices": ["B"]})
    with pytest.raises(ValueError) as excinfo:
        resolveGroupIds(catalog, "없음")
    message = str(excinfo.value)
    assert "없음" in message
    assert "rates, prices" in message


def test_emptyGroupCountsAsMissing() -> None:
    """등록은 됐지만 ID 가 비었으면 없는 것과 같게 끝낸다."""
    catalog = _Catalog({"rates": []})
    with pytest.raises(ValueError):
        resolveGroupIds(catalog, "rates")


def test_bothMacroFacadesShareOneRule() -> None:
    """ECOS 와 FRED facade 가 같은 함수 객체를 본다."""
    from dartlab.gather.ecos import facade as ecosFacade
    from dartlab.gather.fred import facade as fredFacade

    assert ecosFacade.resolveGroupIds is resolveGroupIds
    assert fredFacade.resolveGroupIds is resolveGroupIds
