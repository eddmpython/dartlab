"""DI registry — F3 Protocol DIP 의 인스턴스 lookup.

L2 엔진은 `getXxxAccessor()` 로 default 인스턴스를 받거나, 테스트는
`setXxxAccessor(mock)` 으로 override. module-level singleton.

정공법 B (Protocol DIP) + C (호출 inversion) 의 결합:
- Protocol = core.protocols (이번 phase 추가)
- impl = gather.accessors / gather.macroProvider (gather 측 default)
- caller (story/Company/CLI/test) 가 setter 로 mock 주입 가능
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from dartlab.core.logger import getLogger
from dartlab.core.pluginDiscovery import bootstrap, resetBootstrapState

_log = getLogger(__name__)

if TYPE_CHECKING:
    from dartlab.core.protocols import (  # noqa: F401
        FinanceDataAccessor,
        IndustryDataAccessor,
        MacroDataProvider,
        QuantDataAccessor,
    )

__all__ = [
    "FinanceDataAccessor",
    "QuantDataAccessor",
    "IndustryDataAccessor",
    "MacroDataProvider",
    "getFinanceAccessor",
    "setFinanceAccessor",
    "getQuantAccessor",
    "setQuantAccessor",
    "getIndustryAccessor",
    "setIndustryAccessor",
    "getMacroProvider",
    "setMacroProvider",
    "getCapabilityCatalog",
    "setCapabilityCatalogProvider",
]


_financeAccessor: "FinanceDataAccessor | None" = None
_quantAccessor: "QuantDataAccessor | None" = None
_industryAccessor: "IndustryDataAccessor | None" = None
_macroProvider: "MacroDataProvider | None" = None
_capabilityCatalogProvider: Callable[[], dict[str, Any]] | None = None
_FINANCE_BOOTSTRAP = f"{__name__}:finance"
_QUANT_BOOTSTRAP = f"{__name__}:quant"
_INDUSTRY_BOOTSTRAP = f"{__name__}:industry"
_MACRO_BOOTSTRAP = f"{__name__}:macro"


def getFinanceAccessor() -> "FinanceDataAccessor":
    """현재 finance accessor — 미설정 시 default 생성.

    Capabilities:
        FinanceDataAccessor 구현체를 lazy singleton으로 제공한다.
    AIContext:
        L2 엔진이 gather 구현체를 직접 import하지 않고 finance data surface에 접근하게 한다.
    Guide:
        테스트나 대체 provider는 ``setFinanceAccessor``로 주입한다.
    When:
        analysis/scan/story 등 상위 엔진이 재무 데이터 accessor가 필요할 때.
    How:
        저장된 override가 없으면 composition bootstrap에 기본 구현 주입을 요청한다.
    Args:
        None.
    Returns:
        ``FinanceDataAccessor`` 구현체.
    Requires:
        root composition에 finance accessor bootstrap이 등록되어야 한다.
    Raises:
        기본 구현 import 또는 생성 예외를 전파한다.
    Example:
        >>> getFinanceAccessor() is not None
        True
    SeeAlso:
        ``setFinanceAccessor``.
    """
    global _financeAccessor
    if _financeAccessor is None:
        bootstrap(_FINANCE_BOOTSTRAP)
    if _financeAccessor is None:
        raise RuntimeError("FinanceDataAccessor가 composition root에 등록되지 않았습니다")
    return _financeAccessor


def setFinanceAccessor(impl: "FinanceDataAccessor | None") -> None:
    """finance accessor override (테스트). None 전달 시 default 로 reset.

    Capabilities:
        FinanceDataAccessor singleton slot을 명시적으로 교체하거나 초기화한다.
    AIContext:
        테스트와 대체 runtime이 core protocol을 통해 의존성을 주입하게 한다.
    Guide:
        테스트 종료 시 ``None``으로 되돌려 다음 호출이 default를 다시 만들게 한다.
    When:
        단위 테스트나 실험 provider가 기본 accessor를 대체할 때.
    How:
        module-level ``_financeAccessor`` 값을 설정한다.
    Args:
        impl: 주입할 accessor 또는 reset용 ``None``.
    Returns:
        ``None``.
    Requires:
        impl이 FinanceDataAccessor surface를 만족해야 한다.
    Raises:
        없음.
    Example:
        >>> setFinanceAccessor(None)
    SeeAlso:
        ``getFinanceAccessor``.
    """
    global _financeAccessor
    if impl is None:
        resetBootstrapState(_FINANCE_BOOTSTRAP)
    _financeAccessor = impl


def getQuantAccessor() -> "QuantDataAccessor":
    """현재 quant accessor.

    Capabilities:
        QuantDataAccessor 구현체를 lazy singleton으로 제공한다.
    AIContext:
        quant 관련 호출이 gather 구현체를 직접 참조하지 않게 하는 DIP 경계다.
    Guide:
        테스트 override는 ``setQuantAccessor``를 사용한다.
    When:
        quant/analysis 기능이 시장 데이터 accessor가 필요할 때.
    How:
        저장된 override가 없으면 composition bootstrap에 기본 구현 주입을 요청한다.
    Args:
        None.
    Returns:
        ``QuantDataAccessor`` 구현체.
    Requires:
        root composition에 quant accessor bootstrap이 등록되어야 한다.
    Raises:
        기본 구현 import 또는 생성 예외를 전파한다.
    Example:
        >>> getQuantAccessor() is not None
        True
    SeeAlso:
        ``setQuantAccessor``.
    """
    global _quantAccessor
    if _quantAccessor is None:
        bootstrap(_QUANT_BOOTSTRAP)
    if _quantAccessor is None:
        raise RuntimeError("QuantDataAccessor가 composition root에 등록되지 않았습니다")
    return _quantAccessor


def setQuantAccessor(impl: "QuantDataAccessor | None") -> None:
    """quant accessor override.

    Capabilities:
        QuantDataAccessor singleton slot을 교체하거나 초기화한다.
    AIContext:
        테스트가 외부 가격/팩터 의존성을 mock으로 대체하게 한다.
    Guide:
        테스트 후 ``None`` reset을 권장한다.
    When:
        quant accessor를 테스트 double이나 대체 구현으로 바꿀 때.
    How:
        module-level ``_quantAccessor`` 값을 설정한다.
    Args:
        impl: 주입할 accessor 또는 reset용 ``None``.
    Returns:
        ``None``.
    Requires:
        impl이 QuantDataAccessor surface를 만족해야 한다.
    Raises:
        없음.
    Example:
        >>> setQuantAccessor(None)
    SeeAlso:
        ``getQuantAccessor``.
    """
    global _quantAccessor
    if impl is None:
        resetBootstrapState(_QUANT_BOOTSTRAP)
    _quantAccessor = impl


def getIndustryAccessor() -> "IndustryDataAccessor":
    """현재 industry accessor.

    Capabilities:
        IndustryDataAccessor 구현체를 lazy singleton으로 제공한다.
    AIContext:
        industry 비교 엔진이 gather 구현체를 직접 import하지 않게 한다.
    Guide:
        테스트 override는 ``setIndustryAccessor``를 사용한다.
    When:
        산업/피어 데이터 접근이 필요할 때.
    How:
        저장된 override가 없으면 composition bootstrap에 기본 구현 주입을 요청한다.
    Args:
        None.
    Returns:
        ``IndustryDataAccessor`` 구현체.
    Requires:
        root composition에 industry accessor bootstrap이 등록되어야 한다.
    Raises:
        기본 구현 import 또는 생성 예외를 전파한다.
    Example:
        >>> getIndustryAccessor() is not None
        True
    SeeAlso:
        ``setIndustryAccessor``.
    """
    global _industryAccessor
    if _industryAccessor is None:
        bootstrap(_INDUSTRY_BOOTSTRAP)
    if _industryAccessor is None:
        raise RuntimeError("IndustryDataAccessor가 composition root에 등록되지 않았습니다")
    return _industryAccessor


def setIndustryAccessor(impl: "IndustryDataAccessor | None") -> None:
    """industry accessor override.

    Capabilities:
        IndustryDataAccessor singleton slot을 교체하거나 초기화한다.
    AIContext:
        산업 비교 테스트가 외부 데이터 의존성을 mock으로 대체하게 한다.
    Guide:
        테스트 후 ``None`` reset을 권장한다.
    When:
        industry accessor를 테스트 double이나 대체 구현으로 바꿀 때.
    How:
        module-level ``_industryAccessor`` 값을 설정한다.
    Args:
        impl: 주입할 accessor 또는 reset용 ``None``.
    Returns:
        ``None``.
    Requires:
        impl이 IndustryDataAccessor surface를 만족해야 한다.
    Raises:
        없음.
    Example:
        >>> setIndustryAccessor(None)
    SeeAlso:
        ``getIndustryAccessor``.
    """
    global _industryAccessor
    if impl is None:
        resetBootstrapState(_INDUSTRY_BOOTSTRAP)
    _industryAccessor = impl


def getMacroProvider() -> "MacroDataProvider":
    """현재 macro provider.

    Capabilities:
        MacroDataProvider 구현체를 lazy singleton으로 제공한다.
    AIContext:
        macro 엔진이 gather macro provider 구현을 직접 import하지 않게 한다.
    Guide:
        테스트 override는 ``setMacroProvider``를 사용한다.
    When:
        거시경제 시계열이나 지표 provider가 필요할 때.
    How:
        저장된 override가 없으면 composition bootstrap에 기본 구현 주입을 요청한다.
    Args:
        None.
    Returns:
        ``MacroDataProvider`` 구현체.
    Requires:
        root composition에 macro provider bootstrap이 등록되어야 한다.
    Raises:
        기본 구현 import 또는 생성 예외를 전파한다.
    Example:
        >>> getMacroProvider() is not None
        True
    SeeAlso:
        ``setMacroProvider``.
    """
    global _macroProvider
    if _macroProvider is None:
        bootstrap(_MACRO_BOOTSTRAP)
    if _macroProvider is None:
        raise RuntimeError("MacroDataProvider가 composition root에 등록되지 않았습니다")
    return _macroProvider


def setMacroProvider(impl: "MacroDataProvider | None") -> None:
    """macro provider override.

    Capabilities:
        MacroDataProvider singleton slot을 교체하거나 초기화한다.
    AIContext:
        macro 테스트가 외부 API/provider 의존성을 mock으로 대체하게 한다.
    Guide:
        테스트 후 ``None`` reset을 권장한다.
    When:
        macro provider를 테스트 double이나 대체 구현으로 바꿀 때.
    How:
        module-level ``_macroProvider`` 값을 설정한다.
    Args:
        impl: 주입할 provider 또는 reset용 ``None``.
    Returns:
        ``None``.
    Requires:
        impl이 MacroDataProvider surface를 만족해야 한다.
    Raises:
        없음.
    Example:
        >>> setMacroProvider(None)
    SeeAlso:
        ``getMacroProvider``.
    """
    global _macroProvider
    if impl is None:
        resetBootstrapState(_MACRO_BOOTSTRAP)
    _macroProvider = impl


def getCapabilityCatalog() -> "dict[str, Any]":
    """capability 카탈로그(docstring 라이브 빌드) lazy 조회 — core L0 의 DI 슬롯.

    Capabilities:
        등록된 capability catalog provider 결과를 반환한다.
    AIContext:
        core 메시징(suggest)이 reference 계층을 import 하지 않고 capability 안내를 만들게 한다.
    Guide:
        호출부는 provider 미등록 또는 빈 dict(카탈로그 미가용)를 graceful 하게 처리한다.
    When:
        메시징/안내 레이어가 함수별 capability 요약이 필요할 때.
    How:
        ``setCapabilityCatalogProvider`` 로 등록된 callable 을 호출한다.
    Args:
        None.
    Returns:
        ``dict[str, Any]`` capability 카탈로그. import 불가 시 빈 dict.
    Requires:
        카탈로그 provider 는 dict 반환 callable 이어야 한다.
    Raises:
        없음 — provider 미등록/실패는 빈 dict 로 흡수.
    Example:
        >>> isinstance(getCapabilityCatalog(), dict)
        True
    SeeAlso:
        ``setCapabilityCatalogProvider``.
    """
    if _capabilityCatalogProvider is None:
        return {}
    try:
        return _capabilityCatalogProvider()
    except Exception as exc:
        _log.warning("capability 카탈로그 provider 실패로 빈 카탈로그 반환: %s: %s", type(exc).__name__, exc)
        return {}


def setCapabilityCatalogProvider(provider: Callable[[], dict[str, Any]] | None) -> None:
    """capability catalog provider 등록.

    reference 계층이 자체 초기화 시 등록하고, core 는 등록된 callable 만 호출한다.
    """
    global _capabilityCatalogProvider
    _capabilityCatalogProvider = provider
