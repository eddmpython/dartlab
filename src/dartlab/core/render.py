"""Chart HTML renderer protocol and registry."""

from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@runtime_checkable
class ChartHtmlRenderer(Protocol):
    """ChartSpec dict 를 HTML 문자열로 변환하는 renderer protocol."""

    def htmlFromSpec(self, spec: dict) -> str:
        """ChartSpec 를 HTML 문자열로 변환한다.

        Capabilities:
            Renderer implementation이 chart spec을 HTML fragment로 변환하는 계약을 정의한다.
        AIContext:
            core는 spec만 만들고 실제 렌더링은 viz 구현체가 맡는 dependency inversion surface다.
        Guide:
            구현체는 이 메서드만 맞추면 registry에 등록할 수 있다.
        When:
            ``ChartResult.html`` 같은 호출자가 numeric chart를 HTML로 렌더링할 때.
        How:
            구현체가 Plotly 등 backend별 HTML serialization을 수행한다.
        Args:
            spec: ChartSpec-compatible dict.
        Returns:
            HTML 문자열.
        Requires:
            구현체가 필요한 렌더링 backend를 사용할 수 있어야 한다.
        Raises:
            구현체별 렌더링 예외를 전파한다.
        Example:
            >>> hasattr(ChartHtmlRenderer, "htmlFromSpec")
            True
        SeeAlso:
            ``register`` and ``getRenderer``.
        """
        ...


_renderer: ChartHtmlRenderer | None = None


def register(renderer: ChartHtmlRenderer) -> None:
    """차트 렌더러를 등록한다. 후속 등록은 이전 등록을 덮어쓴다.

    Capabilities:
        전역 renderer slot에 ChartHtmlRenderer 구현체를 등록한다.
    AIContext:
        viz 계층이 core에 직접 import되지 않고 renderer만 주입하게 한다.
    Guide:
        패키지 import 시점의 lightweight registration에만 사용한다.
    When:
        ``dartlab.viz``가 Plotly renderer를 활성화할 때.
    How:
        module-level ``_renderer`` slot을 새 구현체로 교체한다.
    Args:
        renderer: ``ChartHtmlRenderer`` 구현체.
    Returns:
        ``None``.
    Requires:
        renderer가 ``htmlFromSpec``을 제공해야 한다.
    Raises:
        없음.
    Example:
        >>> class R:
        ...     def htmlFromSpec(self, spec): return "<div></div>"
        >>> register(R())
    SeeAlso:
        ``getRenderer``.
    """
    global _renderer
    _renderer = renderer


def getRenderer() -> ChartHtmlRenderer | None:
    """등록된 렌더러를 반환한다. 미등록이면 composition bootstrap을 실행한다.

    Capabilities:
        현재 등록된 chart renderer를 조회하고, 없으면 root composition에 초기화를 요청한다.
    AIContext:
        core/chart 호출자가 viz backend 존재 여부를 안전하게 확인하는 단일 진입점이다.
    Guide:
        반환값이 ``None``이면 caller가 markdown/table fallback을 제공해야 한다.
    When:
        chart HTML 렌더링 직전.
    How:
        ``_renderer``가 비어 있으면 ``bootstrap(__name__)``으로 등록을 유도한다.
    Args:
        None.
    Returns:
        등록된 renderer 또는 미등록/미설치 시 ``None``.
    Requires:
        root composition이 renderer bootstrap을 등록해야 한다.
    Raises:
        renderer bootstrap 오류를 원인 그대로 전파한다.
    Example:
        >>> getRenderer() is None or hasattr(getRenderer(), "htmlFromSpec")
        True
    SeeAlso:
        ``register`` and ``ChartHtmlRenderer``.
    """
    if _renderer is None:
        bootstrap(__name__)
    return _renderer


registry = sys.modules[__name__]
protocols = sys.modules[__name__]
sys.modules.setdefault(__name__ + ".registry", registry)
sys.modules.setdefault(__name__ + ".protocols", protocols)

__all__ = ["ChartHtmlRenderer", "getRenderer", "protocols", "register", "registry"]
