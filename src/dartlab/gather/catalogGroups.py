"""매크로 카탈로그의 그룹 이름을 시리즈 ID 목록으로 해소.

ECOS 와 FRED 는 각자 정적 카탈로그를 들고 "물가", "rates" 같은 그룹 이름을 시리즈 ID
목록으로 바꿔 준다. 이름을 못 찾았을 때 무엇을 하느냐(빈 목록을 흘리지 않고 가용 그룹을
붙여 ``ValueError`` 로 끝낸다)가 두 facade 에서 글자까지 같았다. 그 규칙만 여기 둔다.
"""

from __future__ import annotations

from typing import Any


def resolveGroupIds(catalog: Any, name: str) -> list[str]:
    """그룹 이름을 시리즈 ID 목록으로 풀고, 없으면 가용 그룹을 붙여 끝낸다.

    Capabilities:
        카탈로그 조회 한 번과 미등록 그룹의 fail-closed 처리를 묶는다.

    AIContext:
        매크로 facade 의 ``group`` 축이 실제 fetch 를 걸기 직전에 부른다. 빈 목록을
        그대로 fetch 에 넘기면 "그룹이 없다" 와 "그룹은 있는데 값이 없다" 가 같은 빈
        DataFrame 이 되어 구분되지 않는다. 그래서 여기서 끊는다.

    Guide:
        오류 문장에 가용 그룹 목록을 그대로 붙이므로 호출자가 따로 안내를 만들지 않는다.

    When:
        ``Ecos.group`` , ``Fred.group`` 처럼 그룹 단위 일괄 조회를 할 때.

    How:
        ``catalog.getGroupIds(name)`` 를 부르고 비면 ``catalog.getGroups()`` 로
        안내 문장을 만들어 ``ValueError`` 를 올린다.

    Requires:
        ``getGroupIds`` 와 ``getGroups`` 를 가진 정적 카탈로그 모듈. 네트워크 호출 없음.

    Args:
        catalog: 그룹 카탈로그 모듈 (``gather.ecos.catalog`` 또는 ``gather.fred.catalog``).
            ``getGroupIds(name) -> list[str]`` 과 ``getGroups() -> list[str]`` 둘을 갖춰야 한다.
        name: 찾을 그룹 이름.

    Returns:
        비어 있지 않은 시리즈 ID 목록.

    Raises:
        ValueError: 그룹이 카탈로그에 없을 때. 문장에 가용 그룹 전체가 들어간다.

    Example:
        >>> from dartlab.gather.fred import catalog
        >>> ids = resolveGroupIds(catalog, "rates")
        >>> bool(ids)
        True

    SeeAlso:
        ``dartlab.gather.ecos.facade.Ecos.group`` . 한국 매크로 그룹.
        ``dartlab.gather.fred.facade.Fred.group`` . 미국 매크로 그룹.
    """
    ids = catalog.getGroupIds(name)
    if not ids:
        available = ", ".join(catalog.getGroups())
        raise ValueError(f"그룹 '{name}'을 찾을 수 없습니다. 사용 가능: {available}")
    return ids
