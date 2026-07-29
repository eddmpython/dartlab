"""EDGAR build/consume seam — DI Protocol (정공법 B).

gather/edgar 가 SEC fetch+save 를 전담하되, ① sections artifact build(emit*) 와
② 저장 후 소비자 smoke-check(sections/buildTimeseries/Company)는 ``providers/edgar``
책임이다. gather↛providers 단방향을 유지하기 위해 본 core seam 으로 위임 —
``providers/edgar/buildSeam`` 이 import 시점에 ``EdgarBuildProvider`` 를 register.

소비자(gather/edgar saver·docs.fetch)는 호출부를 그대로 두고 import 경로만 본 모듈로
교체한다. 실제 구현은 providers/edgar 서브모듈(generic ``call`` 위임).

CredentialProvider/DartBuildProvider/EdgarFetchProvider 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


@runtime_checkable
class EdgarBuildProvider(Protocol):
    """EDGAR build/consume 추상화 — gather 수집이 sections build·소비자 검증을 위임하는 seam."""

    def call(self, module: str, func: str, *args: Any, **kwargs: Any) -> Any:
        """providers/edgar.<module>.<func> 위임 호출 (build/consume 출력)."""
        ...


_PROVIDER: EdgarBuildProvider | None = None


def _discover() -> None:
    """root composition이 등록한 EdgarBuildProvider bootstrap을 실행한다."""
    bootstrap(__name__)


def registerEdgarBuildProvider(provider: EdgarBuildProvider) -> None:
    """EdgarBuildProvider 등록 — providers/edgar/buildSeam 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getEdgarBuildProvider() -> EdgarBuildProvider | None:
    """현재 등록된 EdgarBuildProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER


def _provider() -> EdgarBuildProvider:
    provider = getEdgarBuildProvider()
    if provider is None:
        raise RuntimeError("EdgarBuildProvider가 composition root에 등록되지 않았습니다")
    return provider


def _call(module: str, func: str, *args: Any, **kwargs: Any) -> Any:
    return _provider().call(module, func, *args, **kwargs)


# ── providers/edgar build/consume 위임 delegate (gather 소비자 호환 seam) ──


def emitIndexArtifact(*args: Any, **kwargs: Any) -> Any:
    """sections index artifact emit — providers/edgar 위임. Requires: providers.edgar. Raises: OSError. Example: >>> emitIndexArtifact(ticker, idx)  # doctest: +SKIP"""
    return _call("docs.sections.sectionsBuilder", "emitIndexArtifact", *args, **kwargs)


def emitPeriodArtifacts(*args: Any, **kwargs: Any) -> Any:
    """sections period artifact emit — providers/edgar 위임. Requires: providers.edgar. Raises: OSError. Example: >>> emitPeriodArtifacts(ticker, rows)  # doctest: +SKIP"""
    return _call("docs.sections.sectionsBuilder", "emitPeriodArtifacts", *args, **kwargs)


def buildSectionRowsFromFiling(*args: Any, **kwargs: Any) -> Any:
    """filing → section rows build — providers/edgar 위임. Requires: providers.edgar. Raises: 없음. Example: >>> buildSectionRowsFromFiling(items=..., meta=...)  # doctest: +SKIP"""
    return _call("docs.sections.sectionsBuilder", "buildSectionRowsFromFiling", *args, **kwargs)


def buildPanelTableRowsFromFiling(*args: Any, **kwargs: Any) -> Any:
    """filing → panel table rows build — providers/edgar 위임. Requires: providers.edgar. Raises: 없음. Example: >>> buildPanelTableRowsFromFiling(items=..., meta=...)  # doctest: +SKIP"""
    return _call("docs.sections.sectionsBuilder", "buildSectionRowsFromFiling", *args, **kwargs)


buildpanelTableRowsFromFiling = buildPanelTableRowsFromFiling


def sections(*args: Any, **kwargs: Any) -> Any:
    """ticker → sections horizontal view(소비자 smoke-check) — providers/edgar 위임. Requires: providers.edgar. Raises: 없음. Example: >>> sections("AAPL")  # doctest: +SKIP"""
    return _call("docs.sections.pipeline", "sections", *args, **kwargs)


def buildTimeseries(*args: Any, **kwargs: Any) -> Any:
    """cik → finance timeseries(소비자 smoke-check) — providers/edgar 위임. Requires: providers.edgar. Raises: 없음. Example: >>> buildTimeseries(cik, edgarDir=...)  # doctest: +SKIP"""
    return _call("finance.pivot", "buildTimeseries", *args, **kwargs)


def edgarCompany(*args: Any, **kwargs: Any) -> Any:
    """ticker → providers.edgar.Company(소비자 smoke-check) — providers/edgar 위임. Requires: providers.edgar. Raises: 없음. Example: >>> edgarCompany("AAPL")  # doctest: +SKIP"""
    return _call("company", "Company", *args, **kwargs)
