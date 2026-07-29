"""DART OpenAPI fetch seam — DI Protocol (정공법 B).

gather 가 모든 DART network fetch 를 전담(ETL Extract). providers 의 build/read
코드가 client·키가 필요하면 본 core seam 으로 접근 — providers↛gather 단방향 유지.
``gather/dart/client.py`` 의 ``DartFetchProvider`` 구현이 import 시점에 register.

``DartApiError`` 는 pure infra 예외라 core 에 정의(공유 식별자) — gather 가 raise,
providers 가 except 한다. 본 모듈의 ``DartClient`` 는 *factory 함수* — 소비자
호출부(``DartClient(...)``)는 그대로 두고 import 경로만 본 모듈로 교체하면 된다.

CredentialProvider/LoaderProvider/DisclosureFetcher 와 동일 패턴.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from dartlab.core.pluginDiscovery import bootstrap


class DartApiError(Exception):
    """OpenDART API 에러 (공유 infra 예외 — gather raise, providers except)."""

    def __init__(self, status: str, message: str):
        self.status = status
        self.message = message
        super().__init__(f"[{status}] {message}")


@runtime_checkable
class DartFetchProvider(Protocol):
    """DART fetch 추상화 — providers build/read 가 client·키를 얻는 seam."""

    def makeClient(
        self,
        apiKey: str | None = None,
        apiKeys: list[str] | None = None,
        requestsPerMinute: int = 580,
    ) -> Any:
        """멀티 키 DART HTTP 클라이언트 인스턴스 생성."""
        ...

    def resolveKeys(self, apiKey: str | None = None, apiKeys: list[str] | None = None) -> list[str]:
        """DART API 키 list resolve (env/.env/파라미터)."""
        ...

    def hasKey(self) -> bool:
        """DART API 키 설정 여부."""
        ...

    def call(self, module: str, func: str, *args: Any, **kwargs: Any) -> Any:
        """gather/dart.<module>.<func> 위임 호출 (fetch orchestration 출력)."""
        ...


_PROVIDER: DartFetchProvider | None = None


def _discover() -> None:
    """root composition이 등록한 DartFetchProvider bootstrap을 실행한다."""
    bootstrap(__name__)


def registerDartFetchProvider(provider: DartFetchProvider) -> None:
    """DartFetchProvider 등록 — gather/dart/client 가 import 시점에 호출."""
    global _PROVIDER
    _PROVIDER = provider


def getDartFetchProvider() -> DartFetchProvider | None:
    """현재 등록된 DartFetchProvider 반환. 미등록이면 None. auto-discovery 트리거."""
    _discover()
    return _PROVIDER


def _provider() -> DartFetchProvider:
    provider = getDartFetchProvider()
    if provider is None:
        raise RuntimeError("DartFetchProvider가 composition root에 등록되지 않았습니다")
    return provider


def DartClient(
    apiKey: str | None = None,
    apiKeys: list[str] | None = None,
    requestsPerMinute: int = 580,
) -> Any:
    """DART OpenAPI 클라이언트 factory — gather DartFetchProvider 위임.

    Requires: ``dartlab.gather.dart.client`` (DartFetchProvider 등록) + DART_API_KEY(S).
    Raises: RuntimeError — DartFetchProvider 미등록. ValueError — 키 부재.
    Example:
        >>> from dartlab.core.dartClient import DartClient  # doctest: +SKIP
        >>> client = DartClient()  # gather DartClient 인스턴스
    """
    return _provider().makeClient(apiKey=apiKey, apiKeys=apiKeys, requestsPerMinute=requestsPerMinute)


def resolveDartKeys(apiKey: str | None = None, apiKeys: list[str] | None = None) -> list[str]:
    """DART API 키 list resolve — gather DartFetchProvider 위임.

    Requires: ``dartlab.gather.dart.keys`` (env DART_API_KEY/DART_API_KEYS + .env).
    Raises: RuntimeError — DartFetchProvider 미등록.
    Example:
        >>> resolveDartKeys()  # doctest: +SKIP
    """
    return _provider().resolveKeys(apiKey=apiKey, apiKeys=apiKeys)


def hasDartApiKey() -> bool:
    """DART API 키 설정 여부 — gather DartFetchProvider 위임.

    Requires: ``dartlab.gather.dart.keys``.
    Raises: RuntimeError — DartFetchProvider 미등록.
    Example:
        >>> hasDartApiKey()  # doctest: +SKIP
    """
    return _provider().hasKey()


# ── gather/dart fetch orchestration 위임 delegate (providers 소비자 호환 seam) ──
# 소비자(providers build/read)는 import 경로만 본 모듈로 교체. 실제 구현은 gather/dart 서브모듈.
# providers↛gather 단방향 유지 — providers 는 core.dartClient 만 import.


def _call(module: str, func: str, *args: Any, **kwargs: Any) -> Any:
    return _provider().call(module, func, *args, **kwargs)


def dartCollector(*args: Any, **kwargs: Any) -> Any:
    """Dart 파사드 인스턴스 생성 — gather/dart 위임. Requires: gather.dart + DART_API_KEY. Raises: ValueError. Example: >>> dartCollector()("005930")  # doctest: +SKIP"""
    return _call("dart", "Dart", *args, **kwargs)


def openDart(*args: Any, **kwargs: Any) -> Any:
    """OpenDart 파사드 인스턴스 생성 — gather/dart 위임. Requires: gather.dart + DART_API_KEY. Raises: ValueError. Example: >>> openDart().filings("005930")  # doctest: +SKIP"""
    return _call("dart", "OpenDart", *args, **kwargs)


def dartHtmlToText(*args: Any, **kwargs: Any) -> Any:
    """DART 공시 HTML → text normalize — gather/dart 위임. Requires: gather.dart. Raises: 없음. Example: >>> dartHtmlToText(html)  # doctest: +SKIP"""
    return _call("collector", "_htmlToText", *args, **kwargs)


def collectMissing(*args: Any, **kwargs: Any) -> Any:
    """누락 카테고리 수집 — gather/dart 위임. Requires: gather.dart + 인터넷. Raises: httpx. Example: >>> collectMissing("005930", categories=["finance"])  # doctest: +SKIP"""
    return _call("freshness", "collectMissing", *args, **kwargs)


def checkFreshness(*args: Any, **kwargs: Any) -> Any:
    """수집 신선도 점검 — gather/dart 위임. Requires: gather.dart. Raises: 없음. Example: >>> checkFreshness("005930")  # doctest: +SKIP"""
    return _call("freshness", "checkFreshness", *args, **kwargs)


def collectMetaRange(*args: Any, **kwargs: Any) -> Any:
    """공시 메타(전체목록) 범위 수집 — gather/dart 위임. Requires: gather.dart + 인터넷. Raises: httpx. Example: >>> collectMetaRange("20240101", "20240131")  # doctest: +SKIP"""
    return _call("allFilingsCollector", "collectMetaRange", *args, **kwargs)


def fillContent(*args: Any, **kwargs: Any) -> Any:
    """공시 원문(section_content) 채우기 — gather/dart 위임. Requires: gather.dart + 인터넷. Raises: httpx. Example: >>> fillContent("202401")  # doctest: +SKIP"""
    return _call("allFilingsCollector", "fillContent", *args, **kwargs)


def fillContentAll(*args: Any, **kwargs: Any) -> Any:
    """공시 원문 전체 채우기 — gather/dart 위임. Requires: gather.dart + 인터넷. Raises: httpx. Example: >>> fillContentAll()  # doctest: +SKIP"""
    return _call("allFilingsCollector", "fillContentAll", *args, **kwargs)


def allFilingsDir(*args: Any, **kwargs: Any) -> Any:
    """allFilings 메타 parquet 저장 디렉토리 — gather/dart 위임. Requires: gather.dart. Raises: 없음. Example: >>> allFilingsDir()  # doctest: +SKIP"""
    return _call("allFilingsCollector", "_allFilingsDir", *args, **kwargs)


def allFilingsMetaSuffix(*args: Any, **kwargs: Any) -> Any:
    """allFilings 메타 parquet 파일 suffix(``_meta``) — gather/dart 위임. Requires: gather.dart. Raises: 없음. Example: >>> allFilingsMetaSuffix()  # doctest: +SKIP"""
    return _call("allFilingsCollector", "metaSuffix", *args, **kwargs)


def collectorStats(*args: Any, **kwargs: Any) -> Any:
    """allFilings 수집 통계 — gather/dart 위임. Requires: gather.dart. Raises: 없음. Example: >>> collectorStats()  # doctest: +SKIP"""
    return _call("allFilingsCollector", "stats", *args, **kwargs)
