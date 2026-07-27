"""DART build seam — DI Protocol (정공법 B).

gather 가 DART 수집 orchestration(fetch loop)을 전담하되, raw(zip XML)→parquet 변환·
저장(Transform/build)은 ``providers/dart/build`` 책임이다. gather↛providers 단방향을
유지하기 위해 본 core seam 으로 build 함수를 위임한다 — ``providers/dart/build`` 가
import 시점에 ``DartBuildProvider`` 를 register.

소비자(gather 콜렉터)는 호출부를 그대로 두고 import 경로만 본 모듈로 교체한다 —
옛 ``providers.dart.build.saver`` 의 ``writeParquetSorted`` 등을 본 모듈
``dartlab.core.dartBuild`` 에서 동일 이름으로 가져온다.

CredentialProvider/LoaderProvider/DartFetchProvider 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import discoverOnce


@runtime_checkable
class DartBuildProvider(Protocol):
    """DART build 추상화 — gather 수집이 raw→parquet 변환을 위임하는 seam."""

    def parseSectionsByTitle(self, *args: Any, **kwargs: Any) -> Any:
        """zip document.xml → <TITLE> 단위 sections rows."""
        ...

    def splitLargeContent(self, *args: Any, **kwargs: Any) -> Any:
        """큰 content 를 셀 byte 한도로 분할."""
        ...

    def writeParquetSorted(self, *args: Any, **kwargs: Any) -> Any:
        """정렬 + atomic parquet write."""
        ...

    def enrichFinance(self, *args: Any, **kwargs: Any) -> Any:
        """재무 DataFrame 표준 컬럼 보강."""
        ...

    def enrichReport(self, *args: Any, **kwargs: Any) -> Any:
        """보고서 DataFrame 표준 컬럼 보강."""
        ...

    def save(self, *args: Any, **kwargs: Any) -> Any:
        """append + dedup atomic write."""
        ...

    def saveReplacingByKeys(self, *args: Any, **kwargs: Any) -> Any:
        """logical key 기준 replace 증분 write."""
        ...

    def korColumns(self, *args: Any, **kwargs: Any) -> Any:
        """컬럼명을 한글로 rename."""
        ...


_PROVIDER: DartBuildProvider | None = None

_KNOWN_PROVIDER_MODULES: tuple[str, ...] = ("dartlab.providers.dart.build",)


def _discover() -> None:
    """알려진 DartBuildProvider 모듈을 한 번만 lazy import . register 트리거.

    한 번만 도는 규칙은 `core.pluginDiscovery` 가 갖는다. 예전에는 이 열세 줄이
    core 안에 열한 벌 복사돼 있었다.
    """
    discoverOnce(__name__, _KNOWN_PROVIDER_MODULES)


def registerDartBuildProvider(provider: DartBuildProvider) -> None:
    """DartBuildProvider 등록 — providers/dart/build 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getDartBuildProvider() -> DartBuildProvider | None:
    """현재 등록된 DartBuildProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER


def _provider() -> DartBuildProvider:
    provider = getDartBuildProvider()
    if provider is None:
        raise RuntimeError("DartBuildProvider 미등록 — dartlab.providers.dart.build import 실패")
    return provider


def parseSectionsByTitle(*args: Any, **kwargs: Any) -> Any:
    """zip document.xml → sections rows — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build`` (DartBuildProvider 등록).
    Raises: RuntimeError — 미등록.
    Example:
        >>> parseSectionsByTitle(xml)  # doctest: +SKIP
    """
    return _provider().parseSectionsByTitle(*args, **kwargs)


def splitLargeContent(*args: Any, **kwargs: Any) -> Any:
    """content 셀 분할 — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> splitLargeContent(text)  # doctest: +SKIP
    """
    return _provider().splitLargeContent(*args, **kwargs)


def writeParquetSorted(*args: Any, **kwargs: Any) -> Any:
    """정렬 atomic parquet write — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> writeParquetSorted(df, dest)  # doctest: +SKIP
    """
    return _provider().writeParquetSorted(*args, **kwargs)


def enrichFinance(*args: Any, **kwargs: Any) -> Any:
    """재무 컬럼 보강 — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> enrichFinance(df, code, name)  # doctest: +SKIP
    """
    return _provider().enrichFinance(*args, **kwargs)


def enrichReport(*args: Any, **kwargs: Any) -> Any:
    """보고서 컬럼 보강 — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> enrichReport(df, code, corp, t, ep)  # doctest: +SKIP
    """
    return _provider().enrichReport(*args, **kwargs)


def save(*args: Any, **kwargs: Any) -> Any:
    """append+dedup write — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> save(df, path)  # doctest: +SKIP
    """
    return _provider().save(*args, **kwargs)


def saveReplacingByKeys(*args: Any, **kwargs: Any) -> Any:
    """key 기준 replace 증분 write — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> saveReplacingByKeys(df, path, keys)  # doctest: +SKIP
    """
    return _provider().saveReplacingByKeys(*args, **kwargs)


def korColumns(*args: Any, **kwargs: Any) -> Any:
    """한글 컬럼 rename — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build``.
    Raises: RuntimeError — 미등록.
    Example:
        >>> korColumns(df, "finance")  # doctest: +SKIP
    """
    return _provider().korColumns(*args, **kwargs)


def xmlChunkToMixed(*args: Any, **kwargs: Any) -> Any:
    """xml chunk → markdown/HTML mixed string — providers/dart/build 위임.

    Requires: ``dartlab.providers.dart.build`` (panel XML adapter).
    Raises: RuntimeError — 미등록.
    Example:
        >>> xmlChunkToMixed(chunk)  # doctest: +SKIP
    """
    return _provider().xmlChunkToMixed(*args, **kwargs)
