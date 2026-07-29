"""EDGAR panel read facade — DART read contract with US defaults.

구조와 정렬 뼈대는 DART ``panel.read`` 와 동일하다. EDGAR facade 는 기본
``marketNs`` 만 ``"us"`` 로 고정해 ``data/edgar/panel/{ticker}.parquet`` 를 읽게 한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.providers.dart.panel.read import (
    absorbAttached,
    alignNotes,
    anchorLatest,
    anchorNarrativeToSpine,
    orderBySpine,
    scopeExpr,
)
from dartlab.providers.dart.panel.read import ensurePanelFromHf as _ensurePanelFromHf
from dartlab.providers.dart.panel.read import readLong as _readLong
from dartlab.providers.dart.panel.read import readWide as _readWide


def _panelCode(code: str, marketNs: str) -> str:
    return code.upper() if marketNs == "us" else code


def ensurePanelFromHf(code: str, marketNs: str = "us") -> bool:
    """panel artifact lazy load — EDGAR 기본 repo(``edgarPanel``) 사용.

    Args:
        code: US ticker.
        marketNs: panel namespace. 기본은 ``"us"``.

    Returns:
        artifact가 준비됐으면 ``True``. 다운로드 비활성 또는 원격 부재면 ``False``.

    Raises:
        ValueError: 지원하지 않는 ``marketNs``.
        PanelArtifactFetchError: 원격 조달 실패.

    Example:
        >>> ensurePanelFromHf("AAPL")  # doctest: +SKIP
    """
    return _ensurePanelFromHf(_panelCode(code, marketNs), marketNs)


def readLong(code: str, *, marketNs: str = "us", periods: list[str] | None = None) -> pl.DataFrame | None:
    """EDGAR panel long read — DART ``readLong`` 계약의 US facade.

    Args:
        code: US ticker. ``marketNs="us"`` 에서는 upper-case 로 정규화한다.
        marketNs: panel namespace. 기본은 ``"us"``.
        periods: 선택 기간 필터.

    Returns:
        long panel DataFrame 또는 artifact 부재 시 None.

    Raises:
        없음 — 하위 DART read facade 의 lazy-load 계약을 그대로 따른다.

    Example:
        >>> readLong("AAPL")  # doctest: +SKIP
    """
    return _readLong(_panelCode(code, marketNs), marketNs=marketNs, periods=periods)


def readWide(
    code: str,
    *,
    marketNs: str = "us",
    periods: list[str] | None = None,
    tag: bool = True,
) -> pl.DataFrame | None:
    """EDGAR panel wide read — DART ``readWide`` 계약의 US facade.

    Args:
        code: US ticker.
        marketNs: panel namespace. 기본은 ``"us"``.
        periods: 선택 기간 필터.
        tag: True 면 tag 컬럼 포함.

    Returns:
        wide panel DataFrame 또는 artifact 부재 시 None.

    Raises:
        없음 — 하위 DART read facade 의 lazy-load 계약을 그대로 따른다.

    Example:
        >>> readWide("AAPL")  # doctest: +SKIP
    """
    return _readWide(_panelCode(code, marketNs), marketNs=marketNs, periods=periods, tag=tag)


__all__ = [
    "absorbAttached",
    "alignNotes",
    "anchorLatest",
    "anchorNarrativeToSpine",
    "ensurePanelFromHf",
    "orderBySpine",
    "readLong",
    "readWide",
    "scopeExpr",
]
