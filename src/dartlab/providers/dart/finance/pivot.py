"""원본 finance parquet → 분기별 시계열 dict 피벗.

정규화 로직:
1. CFS 우선 선택 (행 단위 중복 제거)
2. IS/CIS/CF 누적 → standalone 변환
3. BS 그대로 (시점 잔액)
4. 분기별 period 컬럼 생성
5. SCE 연도별 매트릭스/시계열 피벗

결과 구조::

    {
        "BS":  {"total_assets": [v1, v2, ...], ...},
        "IS":  {"sales": [...], ...},
        "CF":  {"operating_cashflow": [...], ...},
    }

periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]

SCE 결과 구조::

    matrix[year][cause][detail] = 금액
    series["SCE"]["cause__detail"] = [v2016, v2017, ..., v2024]

snakeId는 standardAccounts.json 기준 그대로 사용.
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any

import polars as pl

from dartlab.core.observability import mapping_ledger
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.core.utils.ordering import sortSeries
from dartlab.core.utils.period import extractYear, formatPeriod, parsePeriod
from dartlab.providers.dart.finance.mapper import AccountMapper

_log = logging.getLogger(__name__)

QUARTER_ORDER = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def _loaderFingerprint(loader: Callable[..., Any]) -> tuple[int, str, str, str, int, int]:
    returnValue = getattr(loader, "return_value", None)
    sideEffect = getattr(loader, "side_effect", None)
    return (
        id(loader),
        getattr(loader, "__module__", ""),
        getattr(loader, "__qualname__", ""),
        repr(loader),
        id(returnValue),
        id(sideEffect),
    )


def _preserveUnmapped(label: str, prefix: str) -> str:
    safe = (
        label.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(",", "_")
    )
    safe = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in safe)
    safe = "_".join(part for part in safe.split("_") if part)
    return f"{prefix}_{safe or 'unknown'}"


# ── 동의어 snakeId 기간별 gap 채우기 ──
# 기업이 기간에 따라 같은 개념을 다른 항목으로 제출하는 경우 대응.
# 예: CJ ENM은 2025Q1까지 "매출액"(→sales), 2025Q2부터 "수익"(→revenue).
_SNAKE_FILL_RULES: list[tuple[str, str, str]] = [
    # (재무제표, primary, fallback) — primary가 null인 기간에 fallback 값 사용
    ("IS", "sales", "revenue"),
    ("IS", "sales", "net_sales"),
    ("BS", "retained_earnings", "unappropriated_retained_earnings_deficit"),
]


def _fillSnakeIdGaps(
    series: dict[str, dict[str, list[float | None]]],
) -> None:
    """동의어 snakeId 간 기간별 null을 채운다 (in-place)."""
    for sjDiv, primary, fallback in _SNAKE_FILL_RULES:
        stmt = series.get(sjDiv)
        if stmt is None:
            continue
        pVals = stmt.get(primary)
        fVals = stmt.get(fallback)
        if pVals is None and fVals is None:
            continue
        if pVals is None:
            # primary 자체가 없으면 fallback을 primary로 승격
            stmt[primary] = list(fVals)
            continue
        if fVals is None:
            continue
        # 둘 다 있으면 primary의 null을 fallback으로 채움
        for i in range(len(pVals)):
            if pVals[i] is None and i < len(fVals) and fVals[i] is not None:
                pVals[i] = fVals[i]


def _loadAndNormalize(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> tuple[pl.DataFrame, list[str]] | None:
    """finance parquet → 정규화된 DataFrame + periods (내부용)."""
    from dartlab.core.dataLoader import loadData

    _FINANCE_COLS = [
        "sj_div",
        "fs_div",
        "account_id",
        "account_nm",
        "bsns_year",
        "reprt_nm",
        "thstrm_amount",
        "thstrm_add_amount",
    ]
    df = loadData(stockCode, category="finance", columns=_FINANCE_COLS)
    return _normalizeFinanceFrame(df, fsDivPref)


def _normalizeFinanceFrame(
    df: pl.DataFrame,
    fsDivPref: str = "CFS",
) -> tuple[pl.DataFrame, list[str]] | None:
    """이미 읽은 DART finance frame을 분기 피벗 직전 형태로 정규화한다."""

    if isEmptyDf(df):
        return None

    if "sj_div" not in df.columns:
        return None

    df = df.filter(pl.col("sj_div").is_in(["BS", "IS", "CIS", "CF"]))
    if df.is_empty():
        return None

    # 2015년 제외 — Q4(사업보고서)만 존재하여 standalone 변환 불가
    df = df.filter(pl.col("bsns_year") != "2015")
    if df.is_empty():
        return None

    df = _applyCfsPriority(df, fsDivPref)
    df = _normalizeQ4(df)

    periods = _buildPeriods(df)
    return df, periods


def buildTimeseries(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    """finance parquet → 분기별 standalone 시계열 — DART 정규화 본진.

    DART 공시 IS/CF 는 **누적 (year-to-date)** 표기 — Q1 = 1Q / Q2 = 1H / Q3 = 9M / Q4 = FY.
    본 함수가 ``thstrm_add_amount`` 차분으로 **분기 standalone** 으로 변환.
    BS 는 시점 잔액 그대로, SCE 는 별도 ``buildSceMatrix`` 가 2-tier pivot.

    캐시: ``@lru_cache(maxsize=8)`` — 종목 × fsDiv 조합 8 LRU. 같은 process 안 반복
    호출 시 1 회만 매핑. 결과는 작은 dict (~수 MB). 무효화 = parquet 갱신 시
    ``clearFinanceCache()`` 또는 server 재기동.

    Args:
        stockCode: 종목코드 (6 자리, 예: ``"005930"``). 정규화 (strip) 후 cache key.
        fsDivPref: ``"CFS"`` (연결재무제표 우선) 또는 ``"OFS"`` (별도). CFS 부재 시
            OFS fallback 자동. 공시 형식 변경 회사는 caller 가 명시 권장.

    Returns:
        tuple — ``(series, periods)`` 또는 None.

        - ``series``: ``{"BS": {snakeId: [값..., None]}, "IS": {...}, "CF": {...}}``.
          값 ``None`` = 해당 분기 미공시. dict 키 = snakeId 정규화 (``"sales"``,
          ``"operating_profit"``, ``"net_income"``, ``"total_assets"`` 등).
        - ``periods``: ``["2019-Q1", "2019-Q2", ..., "2025-Q4"]`` (정렬, 결측 없음).

    Raises:
        없음. 데이터 부재 / parquet 부재 시 None 반환 (예외 X).

    Example:
        >>> series, periods = buildTimeseries("005930")
        >>> series["IS"]["sales"][-1]  # 최신 분기 매출
        ...
    """
    from dartlab.core import dataLoader

    stockCode = str(stockCode).strip()
    fsDivPref = str(fsDivPref).strip() or "CFS"
    loader = dataLoader.loadData
    loaderFingerprint = _loaderFingerprint(loader)
    return _buildTimeseriesCached(stockCode, fsDivPref, loaderFingerprint)


@functools.lru_cache(maxsize=8)
def _buildTimeseriesCached(
    stockCode: str,
    fsDivPref: str,
    loadDataFingerprint: tuple[int, str, str, str, int, int],
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    _ = loadDataFingerprint
    return _buildTimeseriesUncached(stockCode, fsDivPref)


def _buildTimeseriesUncached(
    stockCode: str,
    fsDivPref: str,
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    result = _loadAndNormalize(stockCode, fsDivPref)
    if result is None:
        return None
    df, periods = result
    series = _pivotToSeries(df, periods, stockCode=stockCode)
    return series, periods


def clearFinanceCache() -> None:
    """parquet 갱신 후 cached 결과 폐기 — tests/dev 용.

    Returns:
        None (in-place cache clear).

    Raises:
        없음.

    Example:
        >>> clearFinanceCache()  # parquet 재로드 강제
    """
    _buildTimeseriesCached.cache_clear()


def buildAnnual(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    """finance parquet → 연도별 시계열.

    - IS/CF: 해당 연도 분기별 standalone 합산.
    - BS: 해당 연도 마지막 분기 (Q4 우선) 시점잔액.

    Args:
        stockCode: 종목코드 (예: ``"005930"``).
        fsDivPref: ``"CFS"`` (연결) 또는 ``"OFS"`` (별도).

    Returns:
        ``(series, years)`` 또는 None.

        - ``series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}``
        - ``years = ["2016", "2017", ..., "2024"]``

    Raises:
        없음 (데이터 부재 시 None 반환).

    Example:
        >>> series, years = buildAnnual("005930")
    """
    qResult = buildTimeseries(stockCode, fsDivPref)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult
    return _aggregateAnnual(qSeries, qPeriods)


def buildCumulative(
    stockCode: str,
    fsDivPref: str = "CFS",
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]] | None:
    """finance parquet → 분기별 누적 시계열.

    - IS/CF: 해당 연도 시작부터 누적합 (Q1, Q1+Q2, Q1+Q2+Q3, Q1+Q2+Q3+Q4).
    - BS: 시점잔액 그대로.

    Args:
        stockCode: 종목코드 (예: ``"005930"``).
        fsDivPref: ``"CFS"`` (연결) 또는 ``"OFS"`` (별도).

    Returns:
        ``(series, periods)`` 또는 None.

        - ``series = {"BS": {"snakeId": [값...]}, "IS": {...}, "CF": {...}}``
        - ``periods = ["2016-Q1", "2016-Q2", ..., "2024-Q4"]``

    Raises:
        없음 (데이터 부재 시 None 반환).

    Example:
        >>> series, periods = buildCumulative("005930")
    """
    qResult = buildTimeseries(stockCode, fsDivPref)
    if qResult is None:
        return None

    qSeries, qPeriods = qResult
    return _aggregateCumulative(qSeries, qPeriods)


def _applyCfsPriority(df: pl.DataFrame, pref: str) -> pl.DataFrame:
    """시트(연도×분기×재무제표) 단위 CFS/OFS 선택. pref 우선.

    같은 시트에서 CFS가 1행이라도 있으면 CFS만 사용하고,
    CFS가 없는 시트는 OFS 전체로 폴백한다.
    행 단위 혼합은 합계 불일치를 유발하므로 금지한다.
    """
    if "fs_div" not in df.columns:
        return df

    available = set(df["fs_div"].drop_nulls().unique().to_list())
    if len(available) <= 1:
        return df

    # 시트별(연도, 분기, 재무제표) 소스 결정
    groupCols = ["bsns_year", "reprt_nm", "sj_div"]
    if not all(c in df.columns for c in groupCols):
        return df

    sheetSources = df.group_by(groupCols).agg(pl.col("fs_div").drop_nulls().unique().alias("_sources"))

    def _pickSource(sources: list[str]) -> str:
        """시트별 선택할 fs_div 결정."""
        sourceSet = set(sources)
        if pref in sourceSet:
            return pref
        fallback = "OFS" if pref == "CFS" else "CFS"
        if fallback in sourceSet:
            return fallback
        return sources[0]

    sheetSources = sheetSources.with_columns(
        pl.col("_sources").map_elements(_pickSource, return_dtype=pl.Utf8).alias("_targetFs")
    )

    df = df.join(sheetSources.select(groupCols + ["_targetFs"]), on=groupCols, how="left")
    df = df.filter(pl.col("fs_div") == pl.col("_targetFs"))
    df = df.drop("_targetFs")
    return df


def _normalizeQ4(df: pl.DataFrame) -> pl.DataFrame:
    """IS/CIS/CF 누적값 → standalone(분기 단독) 변환.

    DART 원본 데이터 구조:
    - thstrm_amount: 당기금액 (IS/CIS: 누적, CF: 누적, BS: 시점잔액)
    - thstrm_add_amount: 당기추가금액 (IS/CIS Q4 사업보고서 전용 — 연간 누적)

    Standalone 변환 로직:
    - BS: 시점 잔액이므로 thstrm_amount 그대로
    - CF: Q1은 그대로, Q2~Q4는 전분기 thstrm_amount 차분
    - IS/CIS:
      - Q1: thstrm_amount 그대로 (없으면 thstrm_add_amount fallback)
      - Q2~Q3: thstrm_add_amount - 전분기 thstrm_add_amount
        (thstrm_amount가 null이거나 thstrm_add_amount와 같으면 누적 기반)
      - Q4 특수: thstrm_add_amount가 없으면 thstrm_amount를 Q4 누적으로 간주
        → thstrm_amount - 전분기 thstrm_add_amount로 standalone 추출

    Fallback 경로:
    - thstrm_add_amount null + Q4 IS/CIS → thstrm_amount로 대체 후 차분
    - 전분기 값 null → None (standalone 계산 불가)
    """
    df = df.with_columns(pl.col("reprt_nm").replace(QUARTER_ORDER).cast(pl.Int32).alias("_qOrd"))

    # 문자열 금액 → Float64 변환 (빈 문자열, "-" → null)
    for col in ["thstrm_amount", "thstrm_add_amount"]:
        if col in df.columns:
            df = df.with_columns(
                pl.when(
                    pl.col(col).is_not_null()
                    & (pl.col(col).str.strip_chars() != "")
                    & (pl.col(col).str.strip_chars() != "-")
                )
                .then(pl.col(col).str.strip_chars().str.replace_all(",", "").cast(pl.Float64, strict=False))
                .otherwise(pl.lit(None).cast(pl.Float64))
                .alias(col)
            )
        else:
            df = df.with_columns(pl.lit(None).cast(pl.Float64).alias(col))

    groupKey = ["bsns_year", "sj_div", "account_id"]
    df = df.sort(groupKey + ["_qOrd"])

    df = df.with_columns(
        pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd")
    )  # polars-streaming-unsupported: over

    # Q4 IS/CIS: thstrm_add_amount가 null이면 thstrm_amount를 연간 누적으로 간주
    df = df.with_columns(
        pl.when(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("reprt_nm") == "4분기")
            & pl.col("thstrm_add_amount").is_null()
        )
        .then(pl.col("thstrm_amount"))
        .otherwise(pl.col("thstrm_add_amount"))
        .alias("thstrm_add_amount")
    )

    # prevAdd/prevAmount 재계산 (Q4 fallback 적용 후)
    df = df.with_columns(
        pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd")
    )  # polars-streaming-unsupported: over
    df = df.with_columns(
        pl.col("thstrm_amount").shift(1).over(groupKey).alias("_prevAmount")
    )  # polars-streaming-unsupported: over

    df = df.with_columns(
        # BS: 시점 잔액 그대로
        pl.when(pl.col("sj_div") == "BS")
        .then(pl.col("thstrm_amount"))
        # CF: Q1 그대로, Q2~Q4 전분기 차분
        .when(pl.col("sj_div") == "CF")
        .then(
            pl.when(pl.col("_qOrd") == 1)
            .then(pl.col("thstrm_amount"))
            .when(pl.col("_prevAmount").is_null())
            .then(None)
            .otherwise(pl.col("thstrm_amount") - pl.col("_prevAmount"))
        )
        # IS/CIS Q1: thstrm_amount null이면 thstrm_add_amount fallback
        .when((pl.col("reprt_nm") == "1분기") & pl.col("thstrm_amount").is_null())
        .then(pl.col("thstrm_add_amount"))
        # IS/CIS Q2~Q4: 누적 기반 차분 (thstrm_amount가 null이거나 add와 같으면)
        .when(
            (pl.col("reprt_nm") != "1분기")
            & (pl.col("thstrm_amount").is_null() | (pl.col("thstrm_amount") == pl.col("thstrm_add_amount")))
        )
        .then(
            pl.when(pl.col("_prevAdd").is_null()).then(None).otherwise(pl.col("thstrm_add_amount") - pl.col("_prevAdd"))
        )
        # IS/CIS Q4: thstrm_add_amount null fallback — thstrm_amount에서 차분
        .when((pl.col("reprt_nm") == "4분기") & pl.col("thstrm_add_amount").is_null())
        .then(pl.when(pl.col("_prevAdd").is_null()).then(None).otherwise(pl.col("thstrm_amount") - pl.col("_prevAdd")))
        # 기본: thstrm_amount 사용 (IS/CIS Q1 정상 경로)
        .otherwise(pl.col("thstrm_amount"))
        .alias("_normalized_amount")
    )

    df = df.drop(["_prevAdd", "_prevAmount", "thstrm_add_amount", "_qOrd"])

    return df


def _buildPeriods(df: pl.DataFrame) -> list[str]:
    """분기별 period 리스트 생성."""
    pairs = df.select("bsns_year", "reprt_nm").unique()
    result = []
    for row in pairs.iter_rows(named=True):
        y = row["bsns_year"]
        q = row["reprt_nm"]
        qNum = QUARTER_ORDER.get(q, 0)
        if qNum == 0:
            continue
        result.append((y, qNum, formatPeriod(y, qNum)))

    result.sort(key=lambda x: (x[0], x[1]))
    return [r[2] for r in result]


# IFRS 표준 "상위 집계" 라인 — 해당 snakeId의 총합으로 간주할 수 있는 공식 IFRS 태그.
# 한국 DART 공시에서 매출/원가/이익이 세분화 공시될 때 이 태그가 있으면 총합으로 채택.
# (한미약품: 매출액은 제품매출+상품매출+임가공매출 세분화되지만 ifrs-full_Revenue 14,955억이 공식 총합)
_IFRS_TOP_LEVEL_IDS = frozenset(
    {
        "ifrs-full_revenue",
        "ifrs-full_costofsales",
        "ifrs-full_grossprofit",
        "ifrs-full_profitloss",
        "ifrs-full_profitlossbeforetax",
        "ifrs-full_profitlossfromoperatingactivities",
        "ifrs-full_comprehensiveincome",
        "ifrs-full_othercomprehensiveincome",
        "ifrs-full_assets",
        "ifrs-full_liabilities",
        "ifrs-full_equity",
        "ifrs-full_currentassets",
        "ifrs-full_noncurrentassets",
        "ifrs-full_currentliabilities",
        "ifrs-full_noncurrentliabilities",
    }
)


_NONSTD_PREFIX = "nonstd_"


def _fallbackSnakeId(accountNm: str) -> str | None:
    """미매핑 계정의 fallback snake_id — 데이터 손실 방지.

    DART 의 회사 사내 계정 (account_id = '-표준계정코드 미사용-') 은 표준 mapping 사전에
    없을 수밖에 없다. 무시하면 분석 누락. 한글명을 그대로 키로 살리되 nonstd_ 접두로
    표준 컬럼과 명확히 구분 (LLM/사용자가 비교 분석 시 비표준임을 인식).

    표준화는 별도 — 자주 등장하는 한글명은 accountMappings.json 에 점진 추가.
    """
    clean = (accountNm or "").strip()
    if not clean:
        return None
    # 공백·슬래시·괄호 제거 — 한글은 그대로 (LLM 이 의미 파악 가능).
    for ch in (" ", "\t", "/", "(", ")", "[", "]", ",", "."):
        clean = clean.replace(ch, "_")
    while "__" in clean:
        clean = clean.replace("__", "_")
    clean = clean.strip("_")
    if not clean:
        return None
    return f"{_NONSTD_PREFIX}{clean}"


def _accountIdPriority(accountId: str) -> int:
    """account_id 기반 우선순위. 낮을수록 우선 (덮어쓰기 대상).

    한국 DART 공시에서 같은 기간에 같은 개념(예: '매출액')이 여러 라인으로
    공시되는 경우 (한미약품: ifrs-full_Revenue 총합 + dart_RevenueFromSaleOfGoodsProduct
    서브라인 등)를 해결하기 위한 우선순위.

    - IFRS 상위 집계 라인 (``ifrs-full_Revenue`` 등 화이트리스트): 최우선 (priority 0)
    - 그 외 ``ifrs-full_*`` (예: ``ifrs-full_OtherRevenue``): priority 1
    - ``dart_*``: DART 사내 세분화 라인 → priority 2
    - 그 외 / 빈 값: 최후순위 (priority 3)

    Returns:
            정수 우선순위 (낮을수록 먼저).
    """
    if not accountId:
        return 3
    lower = accountId.lower()
    if lower in _IFRS_TOP_LEVEL_IDS:
        return 0
    if lower.startswith("ifrs-full_") or lower.startswith("ifrs_"):
        return 1
    if lower.startswith("dart_"):
        return 2
    return 3


def _pivotToSeries(
    df: pl.DataFrame,
    periods: list[str],
    stockCode: str | None = None,
) -> dict[str, dict[str, list[float | None]]]:
    """DataFrame → {sjDiv: {snakeId: [값...]}} 피벗.

    Phase B 처방 — DuckDB 기반 PIVOT 으로 위임. Python row dict 누적 0,
    priorityTrack window 함수로 흡수. 결과 dict 는 caller 호환 동일.

    ``stockCode`` 는 ENV ``DARTLAB_MAPPING_LEDGER`` 가 활성일 때
    ledger ndjson 에 함께 기록 (prod 동작 0 영향).

    Legacy (구 Python iter_rows 본체) 는 ``_pivotToSeriesLegacy`` 로 보존 —
    parity test 와 pyodide WASM fallback 에서 사용.
    """
    # pyodide WASM: DuckDB 미가용 → legacy fallback.
    import sys

    if sys.platform == "emscripten":
        return _pivotToSeriesLegacy(df, periods, stockCode)

    from dartlab.providers.dart.finance.pivotArrow import pivotToSeriesArrow

    result = pivotToSeriesArrow(
        df,
        periods,
        accountIdPriority=_accountIdPriority,
        fallbackSnakeId=_fallbackSnakeId,
        ifrsTopLevelIds=_IFRS_TOP_LEVEL_IDS,
        stockCode=stockCode,
    )
    _fillSnakeIdGaps(result)
    sortSeries(result)
    return result


def _pivotToSeriesLegacy(
    df: pl.DataFrame,
    periods: list[str],
    stockCode: str | None = None,
) -> dict[str, dict[str, list[float | None]]]:
    """Phase B 이전의 Python iter_rows 본체 — parity test + pyodide fallback 보존."""
    mapper = AccountMapper.get()
    periodIdx = {p: i for i, p in enumerate(periods)}
    nPeriods = len(periods)

    result: dict[str, dict[str, list[float | None]]] = {
        "BS": {},
        "IS": {},
        "CF": {},
    }
    # (sjDiv, snakeId, idx) → 현재 저장된 값의 우선순위
    priorityTrack: dict[tuple[str, str, int], int] = {}

    totalRows = 0
    unmappedRows = 0
    unmappedAccounts: dict[str, int] = {}
    # ledger 옵트인 — 미매핑 한 건당 (accountId, accountNm, sjDiv) 기준 누적.
    ledgerKeys: dict[tuple[str, str, str], int] = {}

    for row in df.iter_rows(named=True):
        sjDiv = row.get("sj_div", "")
        if sjDiv == "CIS":
            sjDiv = "IS"
        if sjDiv not in result:
            continue

        totalRows += 1
        accountId = row.get("account_id", "") or ""
        accountNm = row.get("account_nm", "") or ""
        snakeId = mapper.map(accountId, accountNm)
        if snakeId is None:
            # fallback — DART 회사 사내 계정 (account_id 표준 X) 도 한글명으로 살린다.
            # nonstd_ 접두로 표준 컬럼과 명시 구분. 데이터 손실 0.
            snakeId = _fallbackSnakeId(accountNm)
            ledgerKey = (accountId, accountNm, sjDiv)
            ledgerKeys[ledgerKey] = ledgerKeys.get(ledgerKey, 0) + 1
            if snakeId is None:
                unmappedRows += 1
                key = f"{accountId}|{accountNm}"
                unmappedAccounts[key] = unmappedAccounts.get(key, 0) + 1
                continue
            # nonstd 도 카운트 — 운영자가 점진 표준화할 후보 식별.
            key = f"{accountId}|{accountNm}"
            unmappedAccounts[key] = unmappedAccounts.get(key, 0) + 1

        amount = row.get("_normalized_amount")

        year = row.get("bsns_year", "")
        reprtNm = row.get("reprt_nm", "")
        qNum = QUARTER_ORDER.get(reprtNm, 0)
        pKey = formatPeriod(year, qNum)

        idx = periodIdx.get(pKey)
        if idx is None:
            continue

        target = result[sjDiv]
        if snakeId not in target:
            target[snakeId] = [None] * nPeriods

        priority = _accountIdPriority(accountId)
        slotKey = (sjDiv, snakeId, idx)
        existingPriority = priorityTrack.get(slotKey)

        if target[snakeId][idx] is None:
            target[snakeId][idx] = amount
            priorityTrack[slotKey] = priority
        elif existingPriority is None or priority < existingPriority:
            # 더 우선순위 높은 account_id 발견 → 덮어쓰기
            target[snakeId][idx] = amount
            priorityTrack[slotKey] = priority

    if unmappedAccounts:
        nonstdRows = sum(unmappedAccounts.values()) - unmappedRows
        _log.info(
            "finance 매핑: %d/%d 행 표준 매핑, %d 행 nonstd_ fallback, %d 행 손실 (%d 고유 비표준 계정)",
            totalRows - unmappedRows - nonstdRows,
            totalRows,
            nonstdRows,
            unmappedRows,
            len(unmappedAccounts),
        )
        # 점진 표준화 후보 — 자주 등장하는 비표준 계정 상위 5 개를 INFO 로 노출.
        # accountMappings.json 에 추가하면 표준 snake_id 로 승격되어 회사간 비교 가능.
        for acct, cnt in sorted(unmappedAccounts.items(), key=lambda x: -x[1])[:5]:
            _log.info("  표준화 후보: %s (%d회)", acct, cnt)

    # ENV gated — ledger append (옵트인). ENV OFF 기본 = no-op.
    if ledgerKeys and mapping_ledger.isEnabled():
        records = [
            {
                "accountId": aId,
                "accountNm": aNm,
                "sjDiv": sj,
                "occurrenceCount": cnt,
            }
            for (aId, aNm, sj), cnt in ledgerKeys.items()
        ]
        try:
            mapping_ledger.append(records, stockCode=stockCode)
        except OSError as exc:  # pragma: no cover - 디스크/권한 실패 시 prod 영향 0
            _log.warning("mapping_ledger append 실패: %s", exc)

    _fillSnakeIdGaps(result)
    sortSeries(result)
    return result


def _aggregateAnnual(
    qSeries: dict[str, dict[str, list[float | None]]],
    qPeriods: list[str],
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]]:
    """분기별 standalone → 연도별 집계.

    Partial year (4 분기 미만) 은 column label 에 분기 수 표시.
    예: 2026 에 Q1 만 있으면 label = "2026Q1" (full year "2026" 와 구분).
    LLM 이 표에서 partial 데이터를 full-year 와 혼동하는 것을 차단.
    """
    yearSet: dict[str, list[int]] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
        yearSet.setdefault(year, []).append(i)

    years = sorted(yearSet.keys())
    nYears = len(years)
    yearIdx = {y: i for i, y in enumerate(years)}

    yearLabels: list[str] = []
    for y in years:
        qIndices = yearSet[y]
        if len(qIndices) >= 4:
            yearLabels.append(y)
        else:
            maxQ = max(parsePeriod(qPeriods[i])[1] for i in qIndices)
            yearLabels.append(f"{y}Q{maxQ}")

    result: dict[str, dict[str, list[float | None]]] = {"BS": {}, "IS": {}, "CF": {}}

    for sjDiv in qSeries:
        for snakeId, vals in qSeries[sjDiv].items():
            annual: list[float | None] = [None] * nYears

            for year, qIndices in yearSet.items():
                yIdx = yearIdx[year]

                if sjDiv == "BS":
                    lastIdx = max(qIndices)
                    annual[yIdx] = vals[lastIdx] if lastIdx < len(vals) else None
                else:
                    qVals = [vals[qi] for qi in qIndices if qi < len(vals) and vals[qi] is not None]
                    annual[yIdx] = sum(qVals) if qVals else None

            result[sjDiv][snakeId] = annual

    return result, yearLabels


def _aggregateCumulative(
    qSeries: dict[str, dict[str, list[float | None]]],
    qPeriods: list[str],
) -> tuple[dict[str, dict[str, list[float | None]]], list[str]]:
    """분기별 standalone → 분기별 누적."""
    yearStarts: dict[str, int] = {}
    for i, p in enumerate(qPeriods):
        year = extractYear(p)
        if year not in yearStarts:
            yearStarts[year] = i

    result: dict[str, dict[str, list[float | None]]] = {"BS": {}, "IS": {}, "CF": {}}
    nPeriods = len(qPeriods)

    for sjDiv in qSeries:
        for snakeId, vals in qSeries[sjDiv].items():
            cum: list[float | None] = [None] * nPeriods

            if sjDiv == "BS":
                cum = list(vals)
            else:
                for i, p in enumerate(qPeriods):
                    year = extractYear(p)
                    startIdx = yearStarts[year]
                    qVals = [vals[j] for j in range(startIdx, i + 1) if j < len(vals) and vals[j] is not None]
                    cum[i] = sum(qVals) if qVals else None

            result[sjDiv][snakeId] = cum

    return result, list(qPeriods)


# ── SCE helper 는 pivotSce.py 로 분리 (규칙 3 LoC).
from dartlab.providers.dart.finance.pivotSce import (  # noqa: E402, F401
    _buildSceMatrixFromDf,
    _sceMatrixToSeries,
    buildSceAnnual,
    buildSceMatrix,
)
