"""scan parquet 로드 + 종목별 추출 (메모리 안전 lazy scan)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl

log = logging.getLogger(__name__)

STOCK_CODE_COLUMNS: tuple[str, ...] = ("stockCode", "종목코드", "stock_code", "corp_code")


def _scanDataRoot() -> Path:
    """data/ 루트 경로."""
    from dartlab.core.dataLoader import _getDataRoot

    return Path(_getDataRoot())


def loadScanParquet(name: str, market: str = "KR") -> "pl.LazyFrame | None":
    """scan 프리빌드 parquet lazy scan 로드.

    Capabilities:
        - dart/scan 또는 edgar/scan 하위 parquet 을 polars LazyFrame 으로 로드
        - report/ 하위 fallback 자동 시도 (finance/changes 외 보조 파일)

    Args:
        name: ``"finance"``, ``"changes"`` 또는 report/ 하위 이름.
        market: ``"KR"`` | ``"US"``.

    Returns:
        pl.LazyFrame | None — 파일 미존재 시 None.

    Guide:
        Quant screen·signal 모듈의 표준 데이터 진입점. lazy scan 으로 메모리 절약 (Polars
        OOM 방지). collect 는 호출자 책임.

    When:
        Quant 횡단면 스크리닝 + 시계열 분석 진입.

    How:
        ``_scanDataRoot`` → market 별 base 경로 → ``name.parquet`` 또는 ``report/name.parquet``.

    Requires:
        ``data/{dart|edgar}/scan/`` 디렉토리 + 대상 parquet 존재.

    Raises:
        없음 — 파일 부재 시 warning 로그 + None.

    Example:
        >>> lf = loadScanParquet("finance", market="KR")
        >>> lf.collect_schema().names()[:3]
        ['stockCode', 'fy', 'sales']

    See Also:
        - loadSharesOutstanding : 발행주식수 LazyFrame
        - loadAllfilingsForStock : 종목별 allFilings
        - fetchOhlcv : OHLCV 시계열

    AIContext:
        Quant cross-sectional 답변 시 finance/changes parquet 로드 → percentile/factor 계산.
    """
    import polars as pl

    root = _scanDataRoot()
    if market == "KR":
        base = root / "dart" / "scan"
    else:
        base = root / "edgar" / "scan"

    path = base / f"{name}.parquet"
    if not path.exists():
        path = base / "report" / f"{name}.parquet"
    if not path.exists():
        log.warning("scan parquet 없음: %s", path)
        return None

    return pl.scan_parquet(path)


def loadSharesOutstanding(market: str = "KR") -> "pl.DataFrame | None":
    """발행주식수 프리빌드 LazyFrame 로드.

    Capabilities:
        - KR: ``data/dart/scan/sharesOutstanding.parquet`` (보통주/우선주 분리)
        - US: ``data/edgar/scan/sharesOutstanding.parquet`` (XBRL dei)
        - scan 카테고리이므로 ``_ensureScanData()`` 가 자동으로 HF 에서 받아온다

    Args:
        market: ``"KR"`` 또는 ``"US"``.

    Returns:
        pl.LazyFrame | None — 파일 부재 시 None.

    Guide:
        Quant valuation factor (PER/PBR) 의 시가총액 계산 필수 입력. finance.parquet 과
        ``stockCode + period_end`` 키로 join.

    When:
        Market cap 기반 factor 계산 + AI 시총 인용 답변.

    How:
        KR: ``_ensureScanData`` → ``sharesOutstanding.parquet``. US: ``_scanDataRoot`` 직접.

    Requires:
        scan parquet 디렉토리 존재 + HF 데이터셋 다운로드 완료.

    Raises:
        없음 — 파일 부재 시 warning + None.

    Example:
        >>> lf = loadSharesOutstanding("KR")
        >>> lf.collect_schema().names()
        ['stockCode', 'period_end', 'common', 'preferred']

    See Also:
        - loadScanParquet : 일반 scan parquet
        - dartlab.scan.io.parquet : HF 동기화

    AIContext:
        시총·PER/PBR 답변 시 발행주식수 × 종가 인용.
    """
    import polars as pl

    if market == "KR":
        import importlib

        _ensureScanData = importlib.import_module("dartlab.scan.io.parquet")._ensureScanData

        scanDir = _ensureScanData()
        path = scanDir / "sharesOutstanding.parquet"
    else:
        root = _scanDataRoot()
        path = root / "edgar" / "scan" / "sharesOutstanding.parquet"

    if not path.exists():
        log.warning("sharesOutstanding parquet 없음: %s", path)
        return None
    return pl.scan_parquet(path)


def loadPanelTextForStock(stockCode: str) -> "pl.DataFrame | None":
    """단일 종목 panel text 로드.

    Capabilities:
        - ``providers.dart.panel.text.panelTextRows`` eager read
        - 종목별 사업보고서 본문 텍스트 (텍스트 alpha 입력)

    Args:
        stockCode: 6 자리 종목코드.

    Returns:
        pl.DataFrame | None — 파일 부재 시 None.

    Guide:
        Quant text alpha (sentiment/toneChange/riskText/governance) 의 본문 입력.

    When:
        Text factor 계산 + AI 공시 본문 기반 답변.

    How:
        ``providers.dart.panel.text.panelTextRows`` → 옛 text-alpha 호환 schema.

    Requires:
        ``data/dart/panel/{stockCode}.parquet`` 존재.

    Raises:
        없음 — 부재 시 warning + None.

    Example:
        >>> df = loadPanelTextForStock("005930")
        >>> df["section"].unique().to_list()[:3]
        ['business', 'risk', 'mdAndA']

    See Also:
        - loadChangesForStock : 변경사항 시계열
        - calcSentiment : 본문 sentiment 추출

    AIContext:
        본문 인용 답변 시 section 별 텍스트 → sentiment/risk 점수 인용.
    """
    import polars as pl

    # plan delegated-prancing-tower PR-E6 — EDGAR ticker 분기.
    # 6 자리 숫자: DART 기존 path. 영문 ticker (US): EDGAR sectionsStorage path.
    if _looksLikeEdgarTicker(stockCode):
        edgarDf = _loadEdgarSectionsAsDocs(stockCode)
        if edgarDf is not None:
            return edgarDf

    # providers.dart.panel.text SSOT(panel 섹션 본문).
    # 옛 text-alpha long schema(year/section_title/section_content) 호환 schema 노출 →
    # 호출자 (sentiment/risk/changes/disclosureDiff 등 D.1 모듈) 0 변경.
    from dartlab.providers.dart.panel.text import panelTextRows

    long = panelTextRows(stockCode)
    if long is None or long.is_empty():
        log.warning("panel 섹션 본문 없음: %s", stockCode)
        return None
    # panel period (예 "2025Q1" / "2025Q4") → year(4 자리) + report_kind 분리,
    # sectionLeaf → section_title, contentRaw → section_content (옛 docs 호환).
    return long.with_columns(
        pl.col("period").str.slice(0, 4).alias("year"),
        pl.col("period").str.slice(4).alias("report_kind"),
        pl.col("sectionLeaf").alias("section_title"),
        pl.col("contentRaw").alias("section_content"),
    )


def _looksLikeEdgarTicker(stockCode: str) -> bool:
    """EDGAR ticker 양식 판별 — 영문 1~5 자.

    DART 6 자리 숫자와 cross-pollination 0 — 6-digit ticker (예 "AAPL45") 면 False.
    EDGAR ticker 의 일부는 dash (BRK.B / BRK-B) 또는 dot 포함 — 본 함수는 단순화 위해
    영문/숫자/dot/dash 만 허용, 길이 1~10.
    """
    from dartlab.core.market import isKrStockCode

    if not stockCode:
        return False
    if isKrStockCode(stockCode):
        return False  # KR stockCode (6자리 숫자 또는 숫자 선두 영숫자, 예 0008Z0)
    return 1 <= len(stockCode) <= 10 and all(c.isalnum() or c in "-." for c in stockCode)


def _loadEdgarSectionsAsDocs(ticker: str) -> "pl.DataFrame | None":
    """EDGAR sections artifact → 옛 docs.parquet 호환 schema 변환.

    D.1 모듈 (sentiment/risk/toneChange/governance/disclosureDiff) 의 호출자 변경 0 —
    같은 columns (year / section_title / section_content) 노출. EDGAR ticker 만 hit.

    Args:
        ticker: 영문 US ticker.

    Returns:
        DataFrame (year/section_title/section_content/period/report_kind) 또는 None.
    """
    import polars as pl

    from dartlab.providers.edgar.docs.sections.sectionsStorage import (
        hasSectionsArtifact as edgarHasArtifact,
    )
    from dartlab.providers.edgar.docs.sections.sectionsStorage import (
        loadSectionsLong as edgarLoadLong,
    )

    tickerUpper = ticker.upper()
    if not edgarHasArtifact(tickerUpper):
        return None
    long = edgarLoadLong(
        tickerUpper,
        columns=["topic", "period", "content_plain", "accession_no", "filing_date", "form_type"],
    )
    if long is None or long.is_empty():
        return None
    try:
        return long.with_columns(
            pl.col("period").str.slice(0, 4).alias("year"),
            pl.col("period").str.slice(4).alias("report_kind"),
            pl.col("content_plain").alias("section_content"),
            pl.col("topic").alias("section_title"),
        )
    except (pl.exceptions.ComputeError, pl.exceptions.SchemaError) as exc:
        log.warning("EDGAR sections → docs 호환 schema 변환 실패 (%s): %s", ticker, exc)
        return None


def loadChangesForStock(stockCode: str) -> "pl.DataFrame | None":
    """changes.parquet에서 단일 종목 필터링.

    Capabilities:
        - ``dart/scan/changes.parquet`` 에서 stockCode 컬럼 자동 탐색 → 단일 종목 추출
        - STOCK_CODE_COLUMNS SSOT 후보 순회

    Args:
        stockCode: 6 자리 종목코드.

    Returns:
        pl.DataFrame | None — 컬럼 모두 매칭 실패 시 None.

    Guide:
        changes.parquet 의 컬럼명 변동성 (snake_case ↔ camelCase ↔ 한글) 대응.
        streaming engine 으로 메모리 안전.

    When:
        종목별 시계열 변동 분석 + AI quarterly change 답변.

    How:
        STOCK_CODE_COLUMNS 후보 순회 → 첫 매칭 컬럼에 ``filter`` → ``collect(streaming)``.

    Requires:
        ``data/dart/scan/changes.parquet`` 존재 + STOCK_CODE_COLUMNS 중 하나 컬럼 존재.

    Raises:
        없음 — 매칭 실패 시 None.

    Example:
        >>> df = loadChangesForStock("005930")
        >>> df.shape[0]
        24

    See Also:
        - loadScanParquet : 일반 scan 진입
        - STOCK_CODE_COLUMNS : 컬럼 후보 SSOT

    AIContext:
        분기 변화 답변 시 columnPos 별 ``change_pct`` 인용.
    """
    import polars as pl

    root = _scanDataRoot()
    path = root / "dart" / "scan" / "changes.parquet"
    if not path.exists():
        return None

    lf = pl.scan_parquet(path)
    for col in STOCK_CODE_COLUMNS:
        try:
            return lf.filter(pl.col(col) == stockCode).collect(engine="streaming")
        except pl.exceptions.ColumnNotFoundError:
            continue
    return None


def stockPercentile(lf, stockCode: str, col: str, stockCol: str = "stockCode", reverse: bool = False) -> float | None:
    """scan lazy frame에서 특정 종목의 컬럼 백분위를 계산.

    Args:
        lf: pl.LazyFrame (scan parquet)
        stockCode: 종목코드
        col: 백분위를 구할 컬럼명
        stockCol: 종목코드 컬럼명
        reverse: True이면 높은 값 = 낮은 백분위 (PBR 등)

    Returns:
        (value, percentile) 또는 (None, None)

    Example:
        >>> stockPercentile(lf, "005930", "roe")
        (0.18, 0.85)

    Requires:
        lf 가 polars LazyFrame + col 존재.

    Raises:
        없음 — 컬럼 누락 시 (None, None).
    """
    import polars as pl

    try:
        schema_names = lf.collect_schema().names()
        actual_stock_col = None
        for c in (stockCol, "종목코드", "stockCode", "corp_code"):
            if c in schema_names:
                actual_stock_col = c
                break
        if actual_stock_col is None or col not in schema_names:
            return None, None

        row = lf.filter(pl.col(actual_stock_col) == stockCode).select(col).collect(engine="streaming")
        if len(row) == 0 or row.item() is None:
            return None, None

        val = float(row.item())

        all_vals = lf.select(col).drop_nulls().collect(engine="streaming").to_series()
        if len(all_vals) == 0:
            return val, None

        if reverse:
            pct = float((all_vals > val).sum() / len(all_vals))
        else:
            pct = float((all_vals < val).sum() / len(all_vals))

        return val, round(pct, 4)
    except (KeyError, ValueError, TypeError):
        return None, None


def loadAllfilingsForStock(stockCode: str, *, lookback: int | None = None) -> "pl.DataFrame | None":
    """allFilings parquet 에서 단일 종목 데이터 로드.

    `data/dart/allFilings/*.parquet` 일자별 전종목 파일에서 stock_code 로 필터.
    polars lazy scan + filter pushdown 으로 메모리 안전 (전체 스캔 가능).

    [Phase 4 R3 fix]
    - 이전: `parquets[-60:]` 슬라이싱으로 60일 한정 → eventDriven 5년 백테스트 막힘
    - 정정: 전체 일자 lazy scan, 컬럼 매칭 `stock_code` (snake_case) 우선
    - lookback_days 명시 시만 최근 N일로 제한 (호출자 책임)

    Capabilities:
        - 일자별 allFilings parquet 전체 lazy scan + stock_code 매칭 컬럼 자동 탐색
        - lookback 명시 시 최근 N 일 슬라이싱, ``diagonal_relaxed`` concat 으로 스키마 변동 흡수

    Args:
        stockCode: 6 자리 종목코드 (예: ``"005930"``).
        lookback: ``None`` = 전체, 숫자 = 최근 N 일.

    Returns:
        pl.DataFrame | None — 매칭 0 건 시 None.

    Guide:
        eventDriven 백테스트의 표준 입력. ``lookback`` 미지정 = 전체 5+ 년 스캔 가능
        (streaming engine 이라 메모리 안전).

    When:
        Event study + AI 공시 시계열 답변.

    How:
        ``allFilings/*.parquet`` glob → ``_meta`` 제외 → lookback 슬라이싱 → 컬럼 매칭 후
        per-file filter + concat.

    Requires:
        ``data/dart/allFilings/`` 존재 + parquet 파일 ≥ 1 개.

    Raises:
        없음 — OSError/ComputeError 는 per-file skip.

    Example:
        >>> df = loadAllfilingsForStock("005930", lookback=252)
        >>> df.shape[0]
        18

    See Also:
        - loadChangesForStock : changes.parquet 단일 종목
        - calcCAR : event study CAR

    AIContext:
        공시 이력 시계열 답변 시 ``filing_date + filing_type`` 인용.
    """
    import polars as pl

    root = _scanDataRoot()
    adir = root / "dart" / "allFilings"
    if not adir.exists():
        return None

    parquets = sorted(adir.glob("*.parquet"))
    parquets = [p for p in parquets if "_meta" not in p.name]
    if not parquets:
        return None

    if lookback is not None and lookback > 0:
        parquets = parquets[-lookback:]

    candidate_cols = ("stock_code", *(c for c in STOCK_CODE_COLUMNS if c != "stock_code"))

    frames: list = []
    for p in parquets:
        try:
            lf = pl.scan_parquet(p)
            schema = lf.collect_schema().names()
            matched_col = next((c for c in candidate_cols if c in schema), None)
            if matched_col is None:
                continue
            filtered = lf.filter(pl.col(matched_col) == stockCode).collect(engine="streaming")
            if len(filtered) > 0:
                frames.append(filtered)
        except (OSError, pl.exceptions.ComputeError):
            continue

    if not frames:
        return None
    return pl.concat(frames, how="diagonal_relaxed")
