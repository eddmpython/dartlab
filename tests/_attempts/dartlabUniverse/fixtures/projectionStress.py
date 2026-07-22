"""U5 projection stress request가 쓰는 deterministic object scope selector."""

from __future__ import annotations

from ..catalog.models import CatalogState


def projectionScope(catalog: CatalogState, count: int) -> tuple[str, ...]:
    """Kind 대표를 먼저 넣고 남은 object를 ID 순서로 채운다."""
    if count < 1:
        raise ValueError("projection stress count는 1 이상이어야 함")
    firstByKind = {}
    for item in catalog.objects:
        firstByKind.setdefault(item.objectKind, item.objectId)
    selected = list(firstByKind.values())
    selected.extend(item.objectId for item in catalog.objects if item.objectId not in set(selected))
    return tuple(selected[:count])
