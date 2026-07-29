"""성장성 스캔 -- 매출/영업이익/순이익 CAGR + 성장 패턴 분류."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.accounts import aggregateAccountValues
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
    _ensureScanData,
    collectScan,
    filterLatestPeriodPerStock,
    filterLatestPeriodPerStockLazy,
    financeScanPath,
    lazyParquet,
    parquetColumns,
    preferConsolidatedPerCompanyLazy,
)

_GROWTH_SCHEMA = {
    "stockCode": pl.Utf8,
    "revenue": pl.Float64,
    "revenueCagr": pl.Float64,
    "opIncomeCagr": pl.Float64,
    "netIncomeCagr": pl.Float64,
    "years": pl.Int64,
    "grade": pl.Utf8,
    "pattern": pl.Utf8,
}


def _emptyGrowthFrame() -> pl.DataFrame:
    return pl.DataFrame(schema=_GROWTH_SCHEMA)


def _gradeGrowth(revCagr: float | None, opCagr: float | None) -> str:
    """매출·영업이익 CAGR 중 높은 값으로 성장성 등급 분류.

    Parameters
    ----------
    revCagr : float | None
        매출액 연평균 복합성장률 (%).
    opCagr : float | None
        영업이익 연평균 복합성장률 (%).

    Returns
    -------
    grade : str
        성장성 등급. 다음 중 하나:
        - ``"고성장"`` : best >= 20 (%)
        - ``"성장"``   : 10 <= best < 20 (%)
        - ``"정체"``   : 0 <= best < 10 (%)
        - ``"역성장"`` : -10 <= best < 0 (%)
        - ``"급감"``   : best < -10 (%)
    """
    values = [value for value in (revCagr, opCagr) if value is not None]
    if not values:
        return "자료부족"
    best = max(values)
    if best >= 20:
        return "고성장"
    if best >= 10:
        return "성장"
    if best >= 0:
        return "정체"
    if best >= -10:
        return "역성장"
    return "급감"


def _classifyPattern(revCagr: float | None, opCagr: float | None, niCagr: float | None) -> str:
    """매출·영업이익·순이익 CAGR 조합으로 성장 패턴 분류.

    Parameters
    ----------
    revCagr : float | None
        매출액 CAGR (%). None 이면 자료부족으로 취급.
    opCagr : float | None
        영업이익 CAGR (%). None 이면 자료부족으로 취급.
    niCagr : float | None
        순이익 CAGR (%). None 이면 필요한 판정에서 자료부족으로 취급.

    Returns
    -------
    pattern : str
        성장 패턴명. 다음 중 하나:
        - ``"균형성장"``   : 매출·영업·순이익 모두 > 5 %
        - ``"수익개선"``   : 매출 > 5 % 이고 영업이익률이 매출 성장을 상회
        - ``"외형성장"``   : 매출 > 5 % 이나 영업이익 역성장
        - ``"구조조정"``   : 매출 역성장이나 영업이익 흑자 전환
        - ``"전면역성장"`` : 매출·영업이익 모두 < -5 %
        - ``"혼합"``       : 위 패턴에 해당하지 않는 경우
    """
    if revCagr is None or opCagr is None:
        return "자료부족"
    r = revCagr
    o = opCagr
    n = niCagr

    if n is not None and r > 5 and o > 5 and n > 5:
        return "균형성장"
    if r > 5 and o > r:
        return "수익개선"
    if r > 5 and o < 0:
        return "외형성장"
    if r < -5 and o > 0:
        return "구조조정"
    if r < -5 and o < -5:
        return "전면역성장"
    return "혼합" if n is not None else "자료부족"


def scanGrowth(*, verbose: bool = True) -> pl.DataFrame:
    """전종목 성장성 스캔 — 매출/영업이익/순이익 3 년 CAGR + 등급 + 성장 패턴.

    Parameters
    ----------
    verbose : bool, default True
        진행 라인을 ``logger.info`` 로 출력.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        revenueCagr : float | None — 매출 3 년 CAGR (%)
        opIncomeCagr : float | None — 영업이익 3 년 CAGR (%)
        netIncomeCagr : float | None — 순이익 3 년 CAGR (%)
        grade : str — 성장성 등급 (고성장/안정성장/저성장/역성장 등)
        pattern : str — 성장 패턴 (6 종 분류)

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 또는 per-file fallback 실패.

    Examples
    --------
    >>> import dartlab
    >>> df = dartlab.scan("growth")
    >>> df.filter(pl.col("등급") == "고성장").head()

    Capabilities:
        - 전종목 finance.parquet 에서 종목별 매출/영업이익/순이익 3 년 CAGR 계산 → 등급 +
          패턴 분류 (수익개선/외형성장/구조조정/전면역성장/혼합/안정).
        - 매출 + 영업이익 부호 / 크기 조합으로 패턴 6 종 분기.

    AIContext:
        Agent 가 ``dartlab.scan("growth")`` 호출 시 본 함수 dispatch. "고성장 종목" 스크리닝,
        "구조조정 종목" (매출 하락 + 영업이익 상승) watchlist, 성장 패턴 cross-company source.

    Guide:
        - CAGR 3 년 = 최신 fy 와 fy-3 사이. 3 년치 데이터 없는 종목은 None.
        - 패턴 "구조조정" 은 매출 하락에도 영업이익 개선 — 비용 효율화 신호로 인용 가능.

    When:
        대시보드 growth 카드 빌드 시. 성장 패턴 cross-company 분석 시.

    How:
        ``_ensureScanData`` → finance.parquet 합본 있으면 ``_scanFromMerged`` (lazy filter +
        종목별 3 년 wide pivot + CAGR + 등급/패턴 분기). 합본 없으면 ``_scanPerFile`` fallback.

    Requires:
        - 로컬 ``data/dart/scan/finance.parquet`` (``buildFinance`` 산출) 또는
          ``data/dart/finance/{stockCode}.parquet`` (fallback)

    SeeAlso:
        - :func:`dartlab.scan.financial.profitability.scanProfitability` — financial 동료 axis
        - :func:`dartlab.scan.dividendTrend.scanDividendTrend` — 배당 시계열 (별도 axis)
    """
    scanDir = _ensureScanData()
    scanPath = financeScanPath(scanDir)

    if not scanPath.exists():
        return _scanPerFile()

    return _scanFromMerged(scanPath)


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet 에서 전종목 성장성 지표 계산.

    Parameters
    ----------
    scanPath : Path
        ``finance.parquet`` 파일 경로.

    Returns
    -------
    pl.DataFrame
        ``_computeGrowth`` 가 반환하는 DataFrame 과 동일한 스키마.
        컬럼 상세는 ``_computeGrowth`` 독스트링 참조.
        데이터가 없으면 빈 DataFrame.
    """
    scCol = "stockCode"

    allIds = list(_REVENUE_IDS | _OP_IDS | _NI_IDS)
    allNms = list(_REVENUE_NMS | _OP_NMS | _NI_NMS)

    schema = parquetColumns(scanPath)
    source = (
        lazyParquet(scanPath)
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
        .select(
            "stockCode",
            "bsns_year",
            *(["reprt_nm"] if "reprt_nm" in schema else []),
            "sj_div",
            "fs_nm",
            "account_id",
            "account_nm",
            "thstrm_amount",
        )
    )
    source = preferConsolidatedPerCompanyLazy(source, scCol)
    if "reprt_nm" in schema:
        latestPeriods = filterLatestPeriodPerStockLazy(source, scCol).select(scCol, "reprt_nm").unique()
        source = source.join(latestPeriods, on=[scCol, "reprt_nm"], how="inner")
    target = collectScan(source)
    if target.is_empty() or scCol not in target.columns:
        return _emptyGrowthFrame()

    return _computeGrowth(target, scCol)


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 파일을 순회하여 성장성 계산 (fallback).

    ``finance.parquet`` 통합 파일이 없을 때 개별 종목 parquet 을 순회한다.

    Returns
    -------
    pl.DataFrame
        ``_computeGrowth`` 가 반환하는 DataFrame 과 동일한 스키마.
        컬럼 상세는 ``_computeGrowth`` 독스트링 참조.
        데이터가 없으면 빈 DataFrame.
    """
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    allDfs = []
    for pf in parquetFiles:
        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS"])
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
        return _emptyGrowthFrame()

    combined = pl.concat(allDfs, how="diagonal_relaxed")
    scCol = "stockCode"
    return _computeGrowth(combined, scCol)


def _computeGrowth(target: pl.DataFrame, scCol: str) -> pl.DataFrame:
    """종목별 매출·영업이익·순이익 3년 CAGR 을 계산하고 등급·패턴을 부여.

    Parameters
    ----------
    target : pl.DataFrame
        손익계산서(IS/CIS) 행만 포함된 DataFrame.
        필수 컬럼: ``bsns_year``, ``account_id``, ``account_nm``, ``thstrm_amount``.
    scCol : str
        종목코드 컬럼명 (``"stockCode"``).

    Returns
    -------
    pl.DataFrame
        종목별 성장성 지표. 컬럼:

        - stockCode : str — 종목코드
        - revenue : float — 최신 연도 매출액 (원)
        - revenueCagr : float — 매출액 CAGR (%)
        - opIncomeCagr : float — 영업이익 CAGR (%)
        - netIncomeCagr : float — 순이익 CAGR (%)
        - years : int — CAGR 계산 기간 (년)
        - grade : str — 성장성 등급 (고성장/성장/정체/역성장/급감)
        - pattern : str — 성장 패턴 (균형성장/수익개선/외형성장/구조조정/전면역성장/혼합)
    """
    required = {scCol, "bsns_year", "account_id", "account_nm", "thstrm_amount"}
    if target.is_empty() or not required.issubset(set(target.columns)):
        return _emptyGrowthFrame()

    # 최신 기간을 회사별로 한 번만 결정하고 과거에도 같은 분기만 남긴다.
    if "reprt_nm" in target.columns:
        latestPeriods = filterLatestPeriodPerStock(target, scCol).select(scCol, "reprt_nm").unique()
        target = target.join(latestPeriods, on=[scCol, "reprt_nm"], how="inner")

    work = target.with_columns(pl.col("bsns_year").cast(pl.Int32, strict=False).alias("_year"))
    work = work.filter(pl.col("_year").is_not_null())
    values = aggregateAccountValues(
        work,
        [scCol, "_year"],
        {
            "_revenue": (_REVENUE_IDS, _REVENUE_NMS, {"IS", "CIS"}),
            "_operatingIncome": (_OP_IDS, _OP_NMS, {"IS", "CIS"}),
            "_netIncome": (_NI_IDS, _NI_NMS, {"IS", "CIS"}),
        },
    )
    if values.is_empty():
        return _emptyGrowthFrame()

    bounds = values.group_by(scCol).agg(
        pl.col("_year").max().alias("_latestYear"),
        pl.col("_year").min().alias("_oldestYear"),
        pl.len().alias("_yearCount"),
    )
    baseCandidates = (
        values.join(bounds.select(scCol, "_latestYear"), on=scCol)
        .filter(pl.col("_year") <= pl.col("_latestYear") - 3)
        .group_by(scCol)
        .agg(pl.col("_year").max().alias("_threeYearBase"))
    )
    bounds = (
        bounds.join(baseCandidates, on=scCol, how="left")
        .with_columns(pl.coalesce("_threeYearBase", "_oldestYear").alias("_baseYear"))
        .with_columns((pl.col("_latestYear") - pl.col("_baseYear")).alias("years"))
        .filter((pl.col("_yearCount") >= 2) & (pl.col("years") > 0))
    )
    if bounds.is_empty():
        return _emptyGrowthFrame()

    latestValues = values.rename(
        {
            "_year": "_latestYear",
            "_revenue": "_revenueNow",
            "_operatingIncome": "_operatingIncomeNow",
            "_netIncome": "_netIncomeNow",
        }
    )
    baseValues = values.rename(
        {
            "_year": "_baseYear",
            "_revenue": "_revenueOld",
            "_operatingIncome": "_operatingIncomeOld",
            "_netIncome": "_netIncomeOld",
        }
    )
    result = bounds.join(latestValues, on=[scCol, "_latestYear"]).join(baseValues, on=[scCol, "_baseYear"])

    exponent = pl.lit(1.0) / pl.col("years")

    def cagrExpr(old: str, new: str) -> pl.Expr:
        """양수인 시작값과 종료값에만 CAGR 벡터식을 적용한다."""

        valid = (pl.col(old) > 0) & (pl.col(new) > 0)
        return pl.when(valid).then(((pl.col(new) / pl.col(old)).pow(exponent) - 1).mul(100).round(1))

    result = result.with_columns(
        pl.col("_revenueNow").round(0).alias("revenue"),
        cagrExpr("_revenueOld", "_revenueNow").alias("revenueCagr"),
        cagrExpr("_operatingIncomeOld", "_operatingIncomeNow").alias("opIncomeCagr"),
        cagrExpr("_netIncomeOld", "_netIncomeNow").alias("netIncomeCagr"),
    )
    best = pl.max_horizontal("revenueCagr", "opIncomeCagr")
    result = result.with_columns(
        pl.when(best.is_null())
        .then(pl.lit("자료부족"))
        .when(best >= 20)
        .then(pl.lit("고성장"))
        .when(best >= 10)
        .then(pl.lit("성장"))
        .when(best >= 0)
        .then(pl.lit("정체"))
        .when(best >= -10)
        .then(pl.lit("역성장"))
        .otherwise(pl.lit("급감"))
        .alias("grade"),
        pl.when(pl.col("revenueCagr").is_null() | pl.col("opIncomeCagr").is_null())
        .then(pl.lit("자료부족"))
        .when(
            pl.col("netIncomeCagr").is_not_null()
            & (pl.col("revenueCagr") > 5)
            & (pl.col("opIncomeCagr") > 5)
            & (pl.col("netIncomeCagr") > 5)
        )
        .then(pl.lit("균형성장"))
        .when((pl.col("revenueCagr") > 5) & (pl.col("opIncomeCagr") > pl.col("revenueCagr")))
        .then(pl.lit("수익개선"))
        .when((pl.col("revenueCagr") > 5) & (pl.col("opIncomeCagr") < 0))
        .then(pl.lit("외형성장"))
        .when((pl.col("revenueCagr") < -5) & (pl.col("opIncomeCagr") > 0))
        .then(pl.lit("구조조정"))
        .when((pl.col("revenueCagr") < -5) & (pl.col("opIncomeCagr") < -5))
        .then(pl.lit("전면역성장"))
        .when(pl.col("netIncomeCagr").is_not_null())
        .then(pl.lit("혼합"))
        .otherwise(pl.lit("자료부족"))
        .alias("pattern"),
    )
    return (
        result.filter(
            pl.any_horizontal(
                pl.col("revenueCagr").is_not_null(),
                pl.col("opIncomeCagr").is_not_null(),
                pl.col("netIncomeCagr").is_not_null(),
            )
        )
        .select(*_GROWTH_SCHEMA)
        .with_columns(pl.col(name).cast(dtype) for name, dtype in _GROWTH_SCHEMA.items())
        .sort("stockCode")
    )


__all__ = ["scanGrowth"]
