"""EDGAR 공시 문서 저장소 엔진.

현재 단계는 저장 규약, 로더 연동, sections horizontal view까지 포함한다.
개별 disclosure 파서는 experiments/055_edgarDocs, 057_edgarSectionMap 결과를 바탕으로 순차 흡수한다.

NOTE: fetchEdgarDocs/downloadListedEdgarDocs(SEC HTML fetch)는 gather/edgar/docs 로 이관 —
lazy ``__getattr__`` re-export(providers↛gather module-level 회피). sections(build)는 providers.
"""

from __future__ import annotations

from dartlab.core.pluginDiscovery import lazyAttribute
from dartlab.providers.edgar.docs.sections import sections

# NOTE: fetchEdgarDocs/downloadListedEdgarDocs 는 아래 ``__getattr__`` 로 런타임 lazy 재노출
# (``_LAZY`` 문자열 importlib) — providers↛gather 단방향 유지 위해 static import 는 두지 않는다.

__all__ = ["fetchEdgarDocs", "downloadListedEdgarDocs", "sections"]

_LAZY = {
    "fetchEdgarDocs": "dartlab.gather.edgar.docs.fetch",
    "downloadListedEdgarDocs": "dartlab.gather.edgar.docs.fetch",
}


def __getattr__(name: str):
    """lazy re-export — SEC docs fetch 를 접근 시점에만 gather 에서 import."""
    return lazyAttribute(__name__, _LAZY, name)
