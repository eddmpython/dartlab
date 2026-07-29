"""수익성 스캔 -- 영업이익률/순이익률/ROE/ROA + 섹터 대비 위치 + 등급."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.accounts import aggregateAccountValues
from dartlab.scan.io.parquet import (
    EQ_IDS as _EQ_IDS,
)
from dartlab.scan.io.parquet import (
    EQ_NMS as _EQ_NMS,
)
from dartlab.scan.io.parquet import (
    NI_IDS as _NI_IDS,
)
from dartlab.scan.io.parquet import (
    NI_NMS as _NI_NMS,
)
from dartlab.scan.io.parquet import (
    OP_IDS as _OP_IDS,
)
from dartlab.scan.io.parquet import (
    OP_NMS as _OP_NMS,
)
from dartlab.scan.io.parquet import (
    REVENUE_IDS as _REVENUE_IDS,
)
from dartlab.scan.io.parquet import (
    REVENUE_NMS as _REVENUE_NMS,
)
from dartlab.scan.io.parquet import (
    TA_IDS as _TA_IDS,
)
from dartlab.scan.io.parquet import (
    TA_NMS as _TA_NMS,
)
from dartlab.scan.io.parquet import (
    _ensureScanData,
    _loadRawFinanceViaDuckDb,
    collectScan,
    filterLatestPeriodPerStock,
    filterLatestPeriodPerStockLazy,
    financeScanPath,
    lazyParquet,
    parquetColumns,
    preferConsolidatedPerCompany,
    preferConsolidatedPerCompanyLazy,
)

_PROFITABILITY_SCHEMA = {
    "stockCode": pl.Utf8,
    "opMargin": pl.Float64,
    "netMargin": pl.Float64,
    "roe": pl.Float64,
    "roa": pl.Float64,
    "grade": pl.Utf8,
    "nonRecurring": pl.Boolean,
}


def _emptyProfitabilityFrame() -> pl.DataFrame:
    return pl.DataFrame(schema=_PROFITABILITY_SCHEMA)


def _gradeProfitability(opMargin: float | None, roe: float | None) -> str:
    """영업이익률·ROE 중 높은 값으로 수익성 등급 분류.

    Parameters
    ----------
    opMargin : float | None
        영업이익률 (%).
    roe : float | None
        자기자본이익률 (%).

    Returns
    -------
    grade : str
        수익성 등급. 다음 중 하나:
        - ``"우수"``   : best >= 20 (%)
        - ``"양호"``   : 10 <= best < 20 (%)
        - ``"보통"``   : 5 <= best < 10 (%)
        - ``"저수익"`` : 0 <= best < 5 (%)
        - ``"적자"``   : best < 0 (%)
    """
    values = [value for value in (opMargin, roe) if value is not None]
    if not values:
        return "자료부족"
    best = max(values)
    if best >= 20:
        return "우수"
    if best >= 10:
        return "양호"
    if best >= 5:
        return "보통"
    if best >= 0:
        return "저수익"
    return "적자"


def scanProfitability(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 수익성 스캔 — 영업이익률/순이익률/ROE/ROA + 등급.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        opMargin : float | None — 영업이익률 (%, 영업이익/매출×100)
        netMargin : float | None — 순이익률 (%, 당기순이익/매출×100)
        roe : float | None — 자기자본이익률 (%, 순이익/자본×100)
        roa : float | None — 총자산이익률 (%, 순이익/자산×100)
        grade : str — 수익성 등급 (우수/양호/보통/주의/적자)

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 또는 per-file fallback 실패.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("profitability")
    >>> df.sort("ROE", descending=True).head()

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 매출/영업이익/순이익/자산/자본 합산 → 4 지표
          (영업이익률/순이익률/ROE/ROA) + 5 단계 등급 (우수/양호/보통/저수익/적자).
        - prebuild 합본 우선, 없으면 종목별 parquet 순회 fallback (``_scanPerFile``).

    AIContext:
        Agent 가 ``dartlab.scan("profitability")`` 호출 시 본 함수 dispatch. "ROE 상위 종목"
        스크리닝, "고마진 회사" 비교, 1 사 수익성 등급 source. financial 7 axis 중 가장 빈번.

    Guide:
        - 등급 기준은 4 지표 중 max(opMargin, roe). 가장 좋은 지표 채택 — 부문별 특수성 흡수.
        - 결산월 환원 후 데이터라 비12월 결산도 캘린더 단면으로 비교 가능.

    When:
        대시보드 profitability 카드 빌드 시. cross-company 수익성 스크리닝 시.

    How:
        ``_ensureScanData`` → ``finance.parquet`` 경로 확인 → 합본 있으면 ``_scanFromMerged``
        lazy filter (연결재무 + 최신 fy) → 종목별 4 지표 계산 + grade 분기. 합본 없으면
        ``_scanPerFile`` fallback.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출) 또는
          ``data/dart/finance/{stockCode}.parquet`` (fallback)
        - REVENUE/OP/NI/TA/EQ public 상수 (``scan.io.parquet``)

    SeeAlso:
        - :func:`dartlab.scan.financial.growth.scanGrowth` · :func:`scanQuality` —
          financial 7 axis 동료
        - :func:`dartlab.scan.builders.kr.core.buildFinance` — source 빌드
        - :func:`dartlab.scan.io.parquet.scanFinanceParquets` — LazyFrame helper
    """
    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)

    if not scanPath.exists():
        return _scanPerFile()

    return _scanFromMerged(scanPath)


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet 에서 전종목 수익성 지표 계산.

    Parameters
    ----------
    scanPath : Path
        ``finance.parquet`` 파일 경로.

    Returns
    -------
    pl.DataFrame
        ``_computeProfitability`` 가 반환하는 DataFrame 과 동일한 스키마.
        컬럼 상세는 ``_computeProfitability`` 독스트링 참조.
        데이터가 없으면 빈 DataFrame.
    """
    schema = parquetColumns(scanPath)
    scCol = "stockCode"
    if scCol not in schema:
        return _emptyProfitabilityFrame()

    allIds = list(_REVENUE_IDS | _OP_IDS | _NI_IDS | _TA_IDS | _EQ_IDS)
    allNms = list(_REVENUE_NMS | _OP_NMS | _NI_NMS | _TA_NMS | _EQ_NMS)

    source = (
        lazyParquet(scanPath)
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS", "BS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
        .select(
            "stockCode",
            "bsns_year",
            "reprt_nm",
            "sj_div",
            "fs_nm",
            "account_id",
            "account_nm",
            "thstrm_amount",
        )
    )
    source = preferConsolidatedPerCompanyLazy(source, scCol)
    target = collectScan(filterLatestPeriodPerStockLazy(source, scCol))
    if target.is_empty() or scCol not in target.columns:
        return _emptyProfitabilityFrame()

    return _computeProfitability(target, scCol)


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 파일을 순회하여 수익성 계산 (fallback).

    ``finance.parquet`` 통합 파일이 없을 때 개별 종목 parquet 을 순회한다.

    Returns
    -------
    pl.DataFrame
        ``_computeProfitability`` 가 반환하는 DataFrame 과 동일한 스키마.
        컬럼 상세는 ``_computeProfitability`` 독스트링 참조.
        데이터가 없으면 빈 DataFrame.
    """
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    scCol = "stockCode"
    allIds = _REVENUE_IDS | _OP_IDS | _NI_IDS | _TA_IDS | _EQ_IDS
    allNms = _REVENUE_NMS | _OP_NMS | _NI_NMS | _TA_NMS | _EQ_NMS

    lz = _loadRawFinanceViaDuckDb(
        financeDir,
        sjDivs=["IS", "CIS", "BS"],
        accountIds=allIds,
        accountNms=allNms,
    )
    if lz is not None:
        try:
            target = lz.filter(pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표")).collect(
                engine="streaming"
            )
        except (pl.exceptions.PolarsError, OSError):
            target = _emptyProfitabilityFrame()
        if not target.is_empty() and scCol in target.columns:
            return _computeProfitability(preferConsolidatedPerCompany(target, scCol), scCol)

    parquetFiles = sorted(financeDir.glob("*.parquet"))

    allDfs = []
    for pf in parquetFiles:
        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS", "BS"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect(engine="streaming")
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.is_empty():
            continue
        if "stockCode" not in df.columns:
            if "stock_code" in df.columns:
                df = df.with_columns(pl.col("stock_code").cast(pl.Utf8).alias("stockCode"))
            else:
                df = df.with_columns(pl.lit(pf.stem).alias("stockCode"))
        cfs = df.filter(pl.col("fs_nm").str.contains("연결"))
        allDfs.append(cfs if not cfs.is_empty() else df)

    if not allDfs:
        return _emptyProfitabilityFrame()

    combined = pl.concat(allDfs, how="diagonal_relaxed")
    return _computeProfitability(combined, scCol)


def _computeProfitability(target: pl.DataFrame, scCol: str) -> pl.DataFrame:
    """최신 연도 기준 종목별 수익성 비율 계산 및 등급 부여.

    Parameters
    ----------
    target : pl.DataFrame
        손익계산서(IS/CIS) + 재무상태표(BS) 행을 포함한 DataFrame.
        필수 컬럼: ``bsns_year``, ``account_id``, ``account_nm``, ``thstrm_amount``.
    scCol : str
        종목코드 컬럼명 (``"stockCode"``).

    Returns
    -------
    pl.DataFrame
        종목별 수익성 지표. 컬럼:

        - stockCode : str — 종목코드
        - opMargin : float — 영업이익률 (%)
        - netMargin : float — 순이익률 (%)
        - roe : float — 자기자본이익률 (%)
        - roa : float — 총자산이익률 (%)
        - grade : str — 수익성 등급 (우수/양호/보통/저수익/적자)
        - nonRecurring : bool — 비경상 이익 의심 여부 (순이익률이 영업이익률 대비 극단적으로 클 때 True)
    """
    required = {scCol, "bsns_year", "account_id", "account_nm", "thstrm_amount"}
    if target.is_empty() or not required.issubset(set(target.columns)):
        return _emptyProfitabilityFrame()

    # 종목별 최신 연도 — 글로벌 max 버그 방지 (2026 Q1 조기 제출 3 종목 때문에
    # 2025 자 2895 종목이 전부 버려지던 현상 수정, 2026-04-23).
    latest = filterLatestPeriodPerStock(target, scCol)
    if latest.is_empty():
        return _emptyProfitabilityFrame()

    values = aggregateAccountValues(
        latest,
        [scCol],
        {
            "_revenue": (_REVENUE_IDS, _REVENUE_NMS, {"IS", "CIS"}),
            "_operatingIncome": (_OP_IDS, _OP_NMS, {"IS", "CIS"}),
            "_netIncome": (_NI_IDS, _NI_NMS, {"IS", "CIS"}),
            "_assets": (_TA_IDS, _TA_NMS, {"BS"}),
            "_equity": (_EQ_IDS, _EQ_NMS, {"BS"}),
        },
    )
    if values.is_empty():
        return _emptyProfitabilityFrame()

    validRevenue = pl.col("_revenue") > 1e6
    validEquity = pl.col("_equity") > 1e6
    validAssets = pl.col("_assets") > 1e6
    result = values.with_columns(
        pl.when(validRevenue & pl.col("_operatingIncome").is_not_null())
        .then((pl.col("_operatingIncome") / pl.col("_revenue") * 100).round(1))
        .alias("opMargin"),
        pl.when(validRevenue & pl.col("_netIncome").is_not_null())
        .then((pl.col("_netIncome") / pl.col("_revenue") * 100).round(1))
        .alias("netMargin"),
        pl.when(validEquity & pl.col("_netIncome").is_not_null())
        .then((pl.col("_netIncome") / pl.col("_equity") * 100).round(1))
        .alias("roe"),
        pl.when(validAssets & pl.col("_netIncome").is_not_null())
        .then((pl.col("_netIncome") / pl.col("_assets") * 100).round(1))
        .alias("roa"),
    ).with_columns(
        pl.when(pl.col("opMargin").abs() > 100)
        .then(None)
        .otherwise(pl.col("opMargin"))
        .cast(pl.Float64)
        .alias("opMargin")
    )
    best = pl.max_horizontal("opMargin", "roe")
    result = (
        result.with_columns(
            pl.when(best.is_null())
            .then(pl.lit("자료부족"))
            .when(best >= 20)
            .then(pl.lit("우수"))
            .when(best >= 10)
            .then(pl.lit("양호"))
            .when(best >= 5)
            .then(pl.lit("보통"))
            .when(best >= 0)
            .then(pl.lit("저수익"))
            .otherwise(pl.lit("적자"))
            .alias("grade"),
            (
                pl.col("netMargin").is_not_null()
                & pl.col("opMargin").is_not_null()
                & (pl.col("netMargin").abs() > pl.col("opMargin").abs() * 3)
                & (pl.col("netMargin").abs() > 50)
            ).alias("nonRecurring"),
        )
        .filter(
            pl.any_horizontal(
                pl.col("opMargin").is_not_null(),
                pl.col("netMargin").is_not_null(),
                pl.col("roe").is_not_null(),
                pl.col("roa").is_not_null(),
            )
        )
        .select(*_PROFITABILITY_SCHEMA)
        .with_columns(pl.col(name).cast(dtype) for name, dtype in _PROFITABILITY_SCHEMA.items())
        .sort("stockCode")
    )
    return result


__all__ = ["scanProfitability"]
