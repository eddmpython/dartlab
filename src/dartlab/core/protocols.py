"""3-provider 동일 surface Protocol SSOT — DART · EDGAR · EDINET 구조적 타이핑.

Capabilities:
    - 3 regulator (한국 DART · 미국 SEC EDGAR · 일본 EDINET) 의 `Company` / docs / finance / filings
      구현체가 만족해야 하는 Protocol contract 단일 출처.
    - `runtime_checkable` 데코레이터로 `isinstance(co, CompanyProtocol)` 런타임 검증 지원.
    - 새 regulator 추가 = 본 모듈의 Protocol 5 종 (`CompanyProtocol` · `DocsProvider` ·
      `FinanceProvider` · `FilingsProvider` · `MemorySafeProvider`) drop-in 구현.

Args:
    (module-level, no callable signature)

Returns:
    Protocol 정의 5 + 보조 dataclass 5 (`FilingResult` · `Section` · `Account` · `Filing` ·
    `StatementsResult`) + L2 analysis 의존성 추상 Protocol 4 (`FinanceDataAccessor` 등).

Example:
    >>> from dartlab.core.protocols import CompanyProtocol
    >>> from dartlab.providers.dart import Company
    >>> isinstance(Company("005930"), CompanyProtocol)
    True

Guide:
    - Company facade 구현 시 본 모듈을 import 해 isinstance 검증 동행.
    - 새 메서드 추가 시 본 모듈에 시그니처 명시 → 3 provider 동시 구현.
    - 메서드 신설 PR 은 `tests/test_providerContract.py` baseline 갱신 동행.

SeeAlso:
    - `operation.architecture` § "Provider Protocol 동일 surface (3-provider mirror)"
    - `operation.code` § "11 룰" 룰 1 (Protocol 동일 surface)
    - `runtime.providerProtocol` § 새 provider 추가 절차

Requires:
    polars (StatementsResult.statements 타입). 다른 외부 의존성 0.

AIContext:
    LLM 이 `isinstance(co, CompanyProtocol)` 로 capability 추론 후 method dispatch.
    Protocol 시그니처는 `inspect.signature()` 로 introspect 가능.

LLM Specifications:
    AntiPatterns:
        - 본 Protocol 을 우회한 duck-typing (`hasattr` 직접 사용) 금지 — `isinstance` 강제.
        - Protocol 시그니처 변경 시 3 provider 동시 갱신 의무 (P-PR0 후 strict).
    OutputSchema:
        Protocol class (5) + dataclass (5) — 모두 `@runtime_checkable` 또는 `@dataclass(frozen=True)`.
    Prerequisites:
        Python 3.12+ (`Protocol` + `runtime_checkable`).
    Freshness:
        Protocol 정의는 P-PR 트랙 동안만 변경. 본 모듈 시그니처 stable 가정.
    Dataflow:
        provider (`providers.{dart,edgar,edinet}.company`) → 본 Protocol → caller (story / AI agent).
    TargetMarkets:
        한국 (DART) · 미국 (EDGAR) · 일본 (EDINET). 신규 regulator 는 본 Protocol 구현으로 추가.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

import polars as pl

# ── P-트랙 룰 1+8+10+11: provider 메서드 반환 dataclass SSOT ──


@dataclass(frozen=True)
class FilingResult:
    """공시 1 건 read 결과."""

    stockCode: str
    period: str
    title: str
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Section:
    """공시 본문 1 섹션."""

    stockCode: str
    period: str
    sectionTitle: str
    sectionOrder: int
    content: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class Account:
    """재무 계정 1 라인."""

    accountId: str
    label: str
    sjDiv: str  # BS/IS/CF/CIS/SCE
    value: float | None = None


@dataclass(frozen=True)
class Filing:
    """공시 메타 1 건 (검색용)."""

    stockCode: str
    rceptNo: str
    title: str
    submittedAt: str
    formType: str | None = None


@dataclass(frozen=True)
class StatementsResult:
    """재무제표 정규화 결과."""

    stockCode: str
    period: str
    kind: str  # annual / Q1 / Q2 / Q3
    statements: pl.DataFrame
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class RawProviderCompanyProtocol(Protocol):
    """L1 provider Company raw surface.

    DART/EDGAR provider 가 직접 소유해야 하는 안정 표면이다. 공시·재무·프로필
    원자료 조회와 lifecycle 만 포함한다. analysis/credit/quant/macro/story/ask
    같은 상위 엔진 편의 진입점은 public facade debt 로 분리 추적한다.
    """

    corpName: str
    market: str
    currency: str

    def __enter__(self) -> "CompanyProtocol":
        """context manager 진입 — Company 그대로 반환.

        Example:
            with Company("005930") as c:
                c.panel("IS").head()

        Returns:
            self.

        Raises:
            RuntimeError: 같은 Company context에 중첩 진입할 때.
        """
        ...

    def __exit__(self, _excType: Any, _excVal: Any, _excTb: Any) -> None:
        """context manager 종료 — cache evict + Python GC + RSS 관측.

        룰 11 만족. provider가 소유한 cache 수명주기를 종료한다.

        Args:
            _excType: 예외 type (정상 종료 시 None).
            _excVal: 예외 인스턴스. 정리 실패와 함께 보존한다.
            _excTb: traceback.

        Raises:
            BaseExceptionGroup: 본문 예외와 정리 실패가 함께 발생했을 때.
            Exception: tripwire 정지 또는 cache 정리가 실패했을 때.
        """
        ...

    @property
    def index(self) -> pl.DataFrame:
        """회사 데이터 구조 인덱스."""
        ...

    @property
    def topics(self) -> pl.DataFrame:
        """사용 가능한 topic 목록."""
        ...

    # Plan v10 P0/P1: c.BS / c.IS / c.CF / c.CIS / c.ratios / c.SCE property 제거.
    # 공개 show 은퇴 → 사용자 진입점은 c.panel(key, freq=, scope=) / c.select(...) 만 (api-contract).

    @property
    def panel(self) -> Any:
        """공시 수평화 단일 표면 — c.panel(key)/c.panel("IS")/c.panel.search(...). show 대체."""
        ...

    def select(
        self,
        topic: str,
        indList: str | list[str] | None = None,
        colList: str | list[str] | None = None,
    ) -> Any:  # SelectResult | None
        """topic 데이터에서 행/열을 선택."""
        ...

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """topic 출처 추적 (docs/finance/report)."""
        ...

    def diff(
        self,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간간 텍스트 변화 감지."""
        ...

    def filings(self) -> pl.DataFrame | None:
        """공시 문서 목록."""
        ...

    def disclosure(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int = 365,
        type: str | None = None,
        keyword: str | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame:
        """실시간 공시 검색."""
        ...

    def liveFilings(
        self,
        start: str | None = None,
        end: str | None = None,
        *,
        days: int | None = None,
        limit: int = 20,
        keyword: str | None = None,
        forms: list[str] | tuple[str, ...] | None = None,
        finalOnly: bool = False,
    ) -> pl.DataFrame:
        """실시간 공시 목록 (OpenAPI)."""
        ...

    def readFiling(
        self,
        filing: Any,
        *,
        maxChars: int | None = None,
    ) -> dict[str, Any]:
        """공시 원문 읽기."""
        ...

    def view(self, *, port: int = 8400) -> None:
        """웹 뷰어 실행."""
        ...


@runtime_checkable
class CompanyProtocol(RawProviderCompanyProtocol, Protocol):
    """현재 공개 Company 공통 인터페이스.

    DART Company와 EDGAR Company 모두 이 Protocol을 만족한다.
    P-트랙 룰 11: context manager + cleanup 의무.

    Notes:
        0.10 전환 중에는 provider Company 가 public facade 편의 메서드까지 함께
        제공한다. 신규 L1 구현은 RawProviderCompanyProtocol 을 먼저 만족하고,
        상위 엔진 편의 메서드는 PublicCompanyFacadeProtocol 으로 분리하는 방향을
        따른다.
    """

    def quant(
        self,
        metric: str | None = None,
        **kwargs: Any,
    ) -> dict | pl.DataFrame | None:
        """기술적 분석 (25개 지표 + 종합 판단)."""
        ...

    def ask(
        self,
        question: str,
        *,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
        provider: str | None = None,
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> str | Any:
        """LLM에게 기업 분석 질문."""
        ...


@runtime_checkable
class PublicCompanyFacadeProtocol(CompanyProtocol, Protocol):
    """사용자 공개 Company facade surface.

    `dartlab.Company(...)` 와 provider Company 의 공개 호출 표면을 보존하기 위한
    Protocol 이다. 내부 의존 debt 는 Guard baseline 으로 추적하되, 사용자 호출 방식
    (`c.panel(...)`, `c.select(...)`, `c.analysis(...)` 등) 은 이 Protocol 을 기준으로
    깨지지 않게 유지한다.
    """

    @property
    def analysis(self) -> Any:
        """재무 분석 dual access facade."""
        ...

    @property
    def credit(self) -> Any:
        """신용 분석 dual access facade."""
        ...

    @property
    def story(self) -> Any:
        """story 조합기 dual access facade."""
        ...

    def macro(self, axis: Any = None, target: Any = None, **kwargs: Any) -> Any:
        """macro 엔진 facade."""
        ...

    def network(self, view: str | None = None, *, hops: int = 1) -> Any:
        """network scan facade."""
        ...

    def governance(self, view: str | None = None) -> pl.DataFrame | None:
        """governance scan facade."""
        ...

    def workforce(self, view: str | None = None) -> pl.DataFrame | None:
        """workforce scan facade."""
        ...

    def capital(self, view: str | None = None) -> pl.DataFrame | None:
        """capital scan facade."""
        ...

    def debt(self, view: str | None = None) -> pl.DataFrame | None:
        """debt scan facade."""
        ...


@runtime_checkable
class DocsProtocol(Protocol):
    """docs namespace 공통 인터페이스."""

    @property
    def sections(self) -> pl.DataFrame | None:
        """pure docs 수평화 sections."""
        ...

    def filings(self) -> pl.DataFrame | None:
        """공시 문서 목록."""
        ...


@runtime_checkable
class FinanceProtocol(Protocol):
    """[INTERNAL] finance namespace — 사용자 진입점 아님.

    Plan v10 P3a: 사용자는 ``c.panel("IS", freq=, scope=)`` 만 사용한다.
    이 protocol 은 내부 backend interface 로만 의미.
    """

    pass


@runtime_checkable
class ProfileProtocol(Protocol):
    """profile namespace 공통 인터페이스."""

    @property
    def sections(self) -> pl.DataFrame | None:
        """merged canonical company table."""
        ...

    def trace(self, topic: str, period: str | None = None) -> dict[str, Any] | None:
        """topic 출처 추적."""
        ...


# ── F3: L2 분석엔진 데이터 의존성 추상화 (구현은 L1 gather, L1.5 scan) ──


@runtime_checkable
class FinanceDataAccessor(Protocol):
    """analysis 엔진의 재무·가격·매크로 fetch 추상.

    구현체는 gather/accessors.DefaultFinanceAccessor (gather 호출),
    또는 테스트의 mock. caller (story/Company) 가 인스턴스를 L2 에 전달한다.
    """

    def fetchPriceSnapshot(
        self, stockCode: str, *, market: str = "KR", start: str | None = None, end: str | None = None
    ) -> pl.DataFrame | None:
        """OHLCV 스냅샷 fetch."""
        ...

    def fetchMacroSeries(self, seriesId: str, *, source: str = "fred", start: str | None = None) -> pl.DataFrame | None:
        """단일 macro 시계열 fetch."""
        ...

    def fetchExogenousAxes(self, stockCode: str) -> list[tuple[str, str]]:
        """종목별 매크로 축 매핑 (seriesId, label) 리스트."""
        ...

    def fetchAlignedMacro(self, stockCode: str, periods: list[str]) -> pl.DataFrame | None:
        """period 기준 정렬된 매크로 패널."""
        ...

    def lookupCompany(self, stockCode: str) -> "CompanyProtocol | None":
        """종목코드 → CompanyProtocol 인스턴스."""
        ...


@runtime_checkable
class QuantDataAccessor(Protocol):
    """quant 엔진의 OHLCV·factor·indicator fetch 추상."""

    def fetchOhlcv(self, stockCode: str, *, market: str = "KR", start: str | None = None) -> pl.DataFrame | None:
        """단일 종목 OHLCV."""
        ...

    def fetchBenchmarkOhlcv(
        self, stockCode: str, *, market: str = "KR", benchmark: str | None = None
    ) -> tuple[pl.DataFrame | None, dict | None]:
        """벤치마크 OHLCV + meta."""
        ...

    def fetchUniverseBulk(self, stockCodes: list[str], *, columns: list[str]) -> pl.DataFrame | None:
        """다종목 bulk 패널."""
        ...

    def fetchTechnicalIndicators(self, stockCode: str, indicators: list[str]) -> dict[str, pl.DataFrame]:
        """지표 번들."""
        ...


@runtime_checkable
class IndustryDataAccessor(Protocol):
    """industry 엔진의 listing·scan parquet fetch 추상."""

    def fetchListing(self, *, market: str = "KR") -> pl.DataFrame | None:
        """전종목 listing snapshot."""
        ...

    def fetchScanProfitability(self) -> pl.DataFrame | None:
        """scan profitability parquet."""
        ...

    def fetchScanFinanceParquet(self, name: str = "finance") -> pl.DataFrame | None:
        """scan finance parquet (또는 변형)."""
        ...


@runtime_checkable
class MacroDataProvider(Protocol):
    """macro 엔진의 gather·cycle 추상."""

    def getDefaultGather(self) -> Any:
        """현재 기본 GatherEntry 인스턴스."""
        ...

    def applyAsOf(self, dataFrame: pl.DataFrame, asOf: str) -> pl.DataFrame:
        """as-of 필터링."""
        ...

    def fetchSeriesLatest(self, seriesId: str) -> float | None:
        """seriesId 의 최신 값."""
        ...

    def fetchSeriesYoy(self, seriesId: str) -> float | None:
        """seriesId 의 YoY 변화율."""
        ...


# ── P-트랙 룰 1: 3-provider 동일 surface 강제 Protocol ──


@runtime_checkable
class DocsProvider(Protocol):
    """3-provider (dart/edgar/edinet) 공통 docs (공시 본문) 표면.

    룰 1 (Protocol 동일 surface) 강제. 새 regulator 추가 = 이 Protocol 구현 drop-in.

    구현체 시그니처는 동일해야 한다 — `test_providerContract.py` 가 introspect.
    """

    def fetchFiling(self, stockCode: str, *, period: str) -> FilingResult | None:
        """단일 공시 본문 fetch.

        Args:
            stockCode: 종목코드 (DART 6자리 / EDGAR ticker / EDINET 4자리).
            period: 보고기간 (예 "2024" annual / "2024Q1").

        Returns:
            FilingResult 또는 데이터 없으면 None.

        Raises:
            ValueError: stockCode 형식 오류.
            OSError: 외부 데이터 접근 실패.
        """
        ...

    def listSections(self, stockCode: str, *, period: str) -> list[Section]:
        """단일 회사의 섹션 list (full materialize).

        Args:
            stockCode: 종목코드.
            period: 보고기간.

        Returns:
            Section 리스트 (빈 list 가능).

        Raises:
            OSError: 데이터 접근 실패.
        """
        ...

    def iterSections(self, stockCode: str, *, period: str) -> Iterator[Section]:
        """단일 회사 섹션 streaming iterator (룰 10 — limit pair).

        Args:
            stockCode: 종목코드.
            period: 보고기간.

        Yields:
            Section.

        Raises:
            OSError: 데이터 접근 실패.
        """
        ...


@runtime_checkable
class FinanceProvider(Protocol):
    """3-provider 공통 finance (XBRL/재무제표) 표면."""

    def fetchStatements(
        self,
        stockCode: str,
        *,
        period: str,
        kind: str = "annual",
        limit: int = 100,
    ) -> StatementsResult | None:
        """재무제표 정규화 패널 fetch.

        Args:
            stockCode: 종목코드.
            period: 보고기간.
            kind: annual / Q1 / Q2 / Q3.
            limit: 반환 row 상한 (룰 8 강제).

        Returns:
            StatementsResult 또는 None.

        Raises:
            ValueError: kind 미지원 값.
            OSError: 데이터 접근 실패.
        """
        ...

    def listAccounts(self, stockCode: str) -> list[Account]:
        """전 계정 list.

        Args:
            stockCode: 종목코드.

        Returns:
            Account 리스트.

        Raises:
            OSError: 데이터 접근 실패.
        """
        ...

    def iterAccounts(self, stockCode: str) -> Iterator[Account]:
        """계정 streaming iterator.

        Args:
            stockCode: 종목코드.

        Yields:
            Account.

        Raises:
            OSError: 데이터 접근 실패.
        """
        ...


@runtime_checkable
class FilingsProvider(Protocol):
    """3-provider 공통 filings (공시 검색) 표면."""

    def search(self, query: str, *, market: str | None = None, limit: int = 20) -> list[Filing]:
        """공시 검색 (메타).

        Args:
            query: 검색어.
            market: KR/US/JP 필터.
            limit: 결과 상한 (룰 8 강제).

        Returns:
            Filing 리스트.

        Raises:
            ValueError: query 빈 문자열.
            OSError: 데이터 접근 실패.
        """
        ...

    def iterSearch(self, query: str, *, market: str | None = None) -> Iterator[Filing]:
        """검색 결과 streaming.

        Args:
            query: 검색어.
            market: 시장 필터.

        Yields:
            Filing.

        Raises:
            ValueError: query 빈 문자열.
        """
        ...


@runtime_checkable
class MemorySafeProvider(Protocol):
    """공통 — 모든 provider 가 만족해야 하는 메모리-safe surface (룰 11)."""

    def cleanupCache(self) -> int:
        """provider 소유 cache evict + Python 순환 참조 회수.

        Returns:
            evict 된 entry 수.

        Raises:
            Exception: cache clear 또는 Python GC가 낸 예외를 그대로 전달한다.
        """
        ...

    def memorySnapshot(self) -> dict[str, int]:
        """캐시 크기 + RSS 등 메모리 상태 snapshot.

        Returns:
            keys: "cacheSize" (entry count), "rssMb" (현 RSS MB).

        Raises:
            없음.
        """
        ...
