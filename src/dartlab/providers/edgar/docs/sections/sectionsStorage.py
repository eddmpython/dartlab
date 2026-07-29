"""EDGAR sections artifact SSOT read — period-sharded parquet.

본 모듈은 plan ``delegated-prancing-tower`` 의 PR-E1 산출물이다. EDGAR
EDGAR 내부 docs wide / D.1 분석의 전환기 read 진입점.
빌더 (PR-E2) 가 emit 하는 ``data/edgar/sections/{ticker}/{period}.parquet`` 를
mmap + columnar projection + lazy pivot 으로 read.

저장 양식 (period-sharded long format)::

    data/edgar/sections/{ticker}/{period}.parquet
    schema:
      topic            string    ─ "10-K::item1Business" 등 form_type::itemId
      blockType        string    ─ "text" | "table" | "heading"
      blockOrder       int32
      textNodeType     string
      textLevel        int8
      textPath         string
      period           string    ─ "2024Q4" / "2024Q1" 등
      content_raw      string    ─ iXBRL HTML chunk (viewer/table_struct SSOT)
      content_plain    string    ─ markdown (분석/show SSOT)
      accession_no     string    ─ SEC filing accession (freshness diff 키)
      filing_date      date
      form_type        string
      period_key       string
      filing_url       string
      cik              string
    data/edgar/sections/{ticker}/_index.parquet  ─ 분기 list + filing meta (small)

DART sectionsStorage 와 동일 API. EDGAR 특화 차이:
- path: ``edgar/sections`` (DART KR 본문은 ``dart/panel`` artifact)
- valueColumn 기본: ``content_plain`` (EDGAR markdown 이 SSOT analytic surface).
- ``loadSectionsIndex`` 신규 — accession_no 기반 freshness diff 가 ``_index.parquet`` 만 scan.
"""

from __future__ import annotations

import logging
from pathlib import Path

import polars as pl

import dartlab.config as _cfg

_log = logging.getLogger(__name__)

_SECTIONS_REL = "edgar/sections"


class SectionsArtifactFetchError(RuntimeError):
    """EDGAR sections 원격 artifact 조달 실패."""

    def __init__(self, ticker: str, cause: BaseException) -> None:
        self.ticker = ticker.upper()
        super().__init__(
            f"EDGAR sections artifact fetch 실패: ticker={self.ticker}, error={type(cause).__name__}: {cause}"
        )


class SectionsArtifactReadError(RuntimeError):
    """EDGAR sections 로컬 artifact 읽기 실패."""

    def __init__(self, ticker: str, operation: str, cause: BaseException) -> None:
        self.ticker = ticker.upper()
        self.operation = operation
        super().__init__(
            f"EDGAR sections artifact {operation} 실패: ticker={self.ticker}, error={type(cause).__name__}: {cause}"
        )


class SectionsSchemaError(ValueError):
    """EDGAR sections artifact schema 또는 pivot 계약 위반."""


def sectionsDir(ticker: str) -> Path:
    """ticker 별 sections artifact 디렉터리 path.

    Args:
        ticker: US ticker (대소문자 무관, 내부 ``upper()`` 정규화).

    Returns:
        ``data/edgar/sections/{TICKER}/`` Path. 미생성 (builder 호출 시 자동 mkdir).

    Raises:
        없음.

    Example:
        >>> sectionsDir("AAPL").name
        'AAPL'
    """
    return Path(_cfg.dataDir) / _SECTIONS_REL / ticker.upper()


def sectionsPath(ticker: str, period: str) -> Path:
    """단일 period parquet path.

    Args:
        ticker: US ticker.
        period: ``"2024Q4"`` / ``"2024Q1"`` / ``"2024Q2"`` / ``"2024Q3"`` 양식.

    Returns:
        period 별 parquet 파일 path.

    Raises:
        없음.

    Example:
        >>> sectionsPath("AAPL", "2024Q4").name
        '2024Q4.parquet'
    """
    return sectionsDir(ticker) / f"{period}.parquet"


def indexPath(ticker: str) -> Path:
    """``_index.parquet`` path — 분기 list + filing meta.

    Args:
        ticker: US ticker.

    Returns:
        ``data/edgar/sections/{TICKER}/_index.parquet`` Path.

    Raises:
        없음.

    Example:
        >>> indexPath("AAPL").name
        '_index.parquet'
    """
    return sectionsDir(ticker) / "_index.parquet"


def listAvailablePeriods(ticker: str, *, limit: int | None = None) -> list[str]:
    """저장된 period 목록 (newer first). 디렉터리 미생성 시 빈 list.

    Args:
        ticker: US ticker.
        limit: 반환할 최근(newer-first) period 최대 개수. None = 전체.

    Returns:
        period 문자열 list. 정렬: 연도 desc, 분기 desc. limit 지정 시 최근 limit 개만.

    Raises:
        없음.

    Example:
        >>> listAvailablePeriods("AAPL")  # doctest: +SKIP
        ['2024Q4', '2024Q3', '2024Q2', '2024Q1', '2023Q4', ...]
    """
    d = sectionsDir(ticker)
    if not d.exists():
        return []
    periods = [p.stem for p in d.glob("*.parquet") if not p.stem.startswith("_")]
    ordered = sorted(periods, key=_periodSortKey, reverse=True)
    return ordered[:limit] if limit is not None else ordered


def _periodSortKey(period: str) -> tuple[int, int]:
    """period → (year, quarter rank) sort key. Q1=1, Q2=2, Q3=3, Q4=4, annual=4."""
    if not period or len(period) < 4 or not period[:4].isdigit():
        return (-1, -1)
    year = int(period[:4])
    if period.endswith("Q1"):
        return (year, 1)
    if period.endswith("Q2"):
        return (year, 2)
    if period.endswith("Q3"):
        return (year, 3)
    if period.endswith("Q4"):
        return (year, 4)
    return (year, 4)


def hasSectionsArtifact(ticker: str) -> bool:
    """artifact 가 1 개 이상 period 존재하면 True.

    Args:
        ticker: US ticker.

    Returns:
        bool — 1 개 이상 period parquet 존재 시 True.

    Raises:
        없음.

    Example:
        >>> hasSectionsArtifact("AAPL")  # doctest: +SKIP
        True
    """
    return bool(listAvailablePeriods(ticker))


_HF_DOWNLOAD_ATTEMPTED: set[str] = set()


def _ensureFromHf(ticker: str) -> bool:
    """artifact 부재 시 HF dataset 에서 lazy 다운로드 — ``edgarSections`` category nested.

    ``huggingface_hub.snapshot_download`` 의 allow_patterns 으로 한 ticker 디렉터리만
    선택 다운로드. 환경변수 ``DARTLAB_NO_HF_DOWNLOAD=1`` 또는 ``edgarSections``
    카테고리 미등록 시 skip.

    Args:
        ticker: US ticker.

    Returns:
        bool — 다운로드 성공 또는 이미 존재 시 True.

    Raises:
        SectionsArtifactFetchError: 원격 요청·인증·설정·저장 실패.
    """
    if hasSectionsArtifact(ticker):
        return True
    import os as _os

    if _os.environ.get("DARTLAB_NO_HF_DOWNLOAD", "").strip() in ("1", "true", "True"):
        return False
    tickerUpper = ticker.upper()
    if tickerUpper in _HF_DOWNLOAD_ATTEMPTED:
        return False

    try:
        from huggingface_hub import snapshot_download

        from dartlab.core.dataConfig import DATA_RELEASES, repoFor
        from dartlab.core.hfRetry import retryHfCall

        if "edgarSections" not in DATA_RELEASES:
            raise KeyError("DATA_RELEASES에 edgarSections category가 없습니다")
        sectionsDirRel = DATA_RELEASES["edgarSections"]["dir"]
        retryHfCall(  # HF read SSOT(core.hfRetry) — 429/503/504 단일 백오프
            snapshot_download,
            repo_id=repoFor("edgarSections"),  # 전용 repo 존중 (HF_REPO 하드코딩 시 전환 후 빈 결과)
            repo_type="dataset",
            allow_patterns=[f"{sectionsDirRel}/{tickerUpper}/*.parquet"],
            local_dir=str(Path(_cfg.dataDir)),
        )
    except Exception as exc:  # noqa: BLE001 — optional dependency와 원격 원인을 typed 경계로 보존
        raise SectionsArtifactFetchError(tickerUpper, exc) from exc

    available = hasSectionsArtifact(tickerUpper)
    if not available:
        _HF_DOWNLOAD_ATTEMPTED.add(tickerUpper)
    return available


def loadSectionsIndex(ticker: str) -> pl.DataFrame | None:
    """``_index.parquet`` read — 분기 list + filing meta (accession_no/filing_date/...).

    EDGAR freshness diff (``_loadLocalAccessionNos``) 가 본 함수 결과의 ``accession_no``
    컬럼만 scan. 옛 docs.parquet 전수 scan 대비 ~수십 배 작음.

    Args:
        ticker: US ticker.

    Returns:
        index DataFrame 또는 None (artifact 부재).

    Raises:
        SectionsArtifactFetchError: 부재 artifact의 원격 조달 실패.
        SectionsArtifactReadError: index parquet 읽기 실패.

    Example:
        >>> df = loadSectionsIndex("AAPL")  # doctest: +SKIP
        >>> df.columns  # doctest: +SKIP
        ['period', 'accession_no', 'filing_date', 'form_type', 'filing_url', 'cik']
    """
    if not hasSectionsArtifact(ticker):
        _ensureFromHf(ticker)
    p = indexPath(ticker)
    if not p.exists():
        return None
    try:
        return pl.read_parquet(str(p))
    except (OSError, pl.exceptions.ComputeError) as exc:
        raise SectionsArtifactReadError(ticker, "index 읽기", exc) from exc


def loadSectionsLong(
    ticker: str,
    *,
    periods: list[str] | None = None,
    columns: list[str] | None = None,
) -> pl.DataFrame | None:
    """sections artifact long format read — period-sharded glob + columnar projection.

    polars ``scan_parquet([files]).select(columns)`` 로 select 안 한 컬럼은 페이지
    fault 0. 분석 path 가 ``columns=["content_plain"]`` 만 select 시 ``content_raw``
    페이지 fault 0 (콜드 메모리 절감).

    Args:
        ticker: US ticker.
        periods: 특정 period 만 read. None = 전체.
        columns: 특정 컬럼만 select. None = 전체.

    Returns:
        long format DataFrame 또는 None (artifact 부재).

    Raises:
        SectionsArtifactFetchError: 부재 artifact의 원격 조달 실패.
        SectionsArtifactReadError: period parquet 읽기 실패.
        SectionsSchemaError: 요청 projection이 artifact schema와 맞지 않음.

    Example:
        >>> df = loadSectionsLong("AAPL", periods=["2024Q4"], columns=["topic", "content_plain"])  # doctest: +SKIP
    """
    if not hasSectionsArtifact(ticker):
        _ensureFromHf(ticker)
    available = listAvailablePeriods(ticker)
    if not available:
        return None
    targetPeriods = available if periods is None else [p for p in available if p in set(periods)]
    if not targetPeriods:
        return None
    files = [str(sectionsPath(ticker, p)) for p in targetPeriods]
    try:
        scan = pl.scan_parquet(files)
        if columns:
            availableSchema = set(scan.collect_schema().names())
            wantedCols = [c for c in columns if c in availableSchema]
            if not wantedCols:
                raise SectionsSchemaError(
                    f"EDGAR sections {ticker.upper()}: 요청 컬럼이 모두 schema에 없습니다: {columns}"
                )
            scan = scan.select(wantedCols)
        return scan.collect()
    except (OSError, pl.exceptions.ComputeError, pl.exceptions.ShapeError) as exc:
        raise SectionsArtifactReadError(ticker, "long 읽기", exc) from exc


# EDGAR sections schema 의 meta 컬럼 — wide pivot 시 index. DART 와 schema 다름:
# chapter/textPathKey 없음, accession_no/filing_url/form_type 등 EDGAR-only meta 추가.
_MINIMAL_META: tuple[str, ...] = (
    "topic",
    "blockType",
    "blockOrder",
    "textNodeType",
    "textLevel",
    "textPath",
)


def loadSectionsWide(
    ticker: str,
    *,
    periods: list[str] | None = None,
    valueColumn: str = "content_plain",
) -> pl.DataFrame | None:
    """sections artifact wide format read — long → pivot(period).

    ``valueColumn`` 으로 cell 값 종류 선택:
    - ``"content_plain"`` (default) — markdown, 내부 docs 분석 / legacy show
    - ``"content_raw"`` — iXBRL HTML, viewer 전용

    Args:
        ticker: US ticker.
        periods: 특정 period 만 wide 컬럼으로. None = 전체.
        valueColumn: pivot value 컬럼.

    Returns:
        wide format DataFrame 또는 None.

    Raises:
        SectionsArtifactFetchError: 부재 artifact의 원격 조달 실패.
        SectionsArtifactReadError: period parquet 읽기 실패.
        SectionsSchemaError: 필수 컬럼 또는 pivot 계약 위반.

    Example:
        >>> df = loadSectionsWide("AAPL")  # doctest: +SKIP
        >>> df.columns[:6]  # doctest: +SKIP
        ['topic', 'blockType', 'blockOrder', 'textNodeType', 'textLevel', 'textPath']
    """
    selectCols = list(_MINIMAL_META) + ["period", valueColumn]
    long = loadSectionsLong(ticker, periods=periods, columns=selectCols)
    if long is None or long.is_empty():
        return None
    if valueColumn not in long.columns:
        raise SectionsSchemaError(
            f"EDGAR sections {ticker.upper()}: valueColumn {valueColumn!r} 부재 (사용 가능: {long.columns})"
        )
    metaCols = [c for c in long.columns if c not in ("period", valueColumn)]
    if "period" not in long.columns or not metaCols:
        raise SectionsSchemaError(
            f"EDGAR sections {ticker.upper()}: pivot 필수 컬럼이 없습니다 "
            f"(period={'period' in long.columns}, meta={metaCols})"
        )
    try:
        return long.pivot(
            values=valueColumn,
            index=metaCols,
            on="period",
            aggregate_function="first",
        )
    except (pl.exceptions.ComputeError, pl.exceptions.ShapeError) as exc:
        raise SectionsSchemaError(f"EDGAR sections {ticker.upper()}: pivot 실패: {type(exc).__name__}: {exc}") from exc
