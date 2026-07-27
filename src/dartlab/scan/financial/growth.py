"""성장성 스캔 -- 매출/영업이익/순이익 CAGR + 성장 패턴 분류."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.core.utils.calc import cagr as _cagr  # noqa: E402
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
    extractAccount,
    financeScanPath,
    lazyParquet,
    preferConsolidatedPerCompany,
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
    best = max(revCagr or -999, opCagr or -999)
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
        매출액 CAGR (%). None 이면 0 으로 취급.
    opCagr : float | None
        영업이익 CAGR (%). None 이면 0 으로 취급.
    niCagr : float | None
        순이익 CAGR (%). None 이면 0 으로 취급.

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
    r = revCagr or 0
    o = opCagr or 0
    n = niCagr or 0

    if r > 5 and o > 5 and n > 5:
        return "균형성장"
    if r > 5 and o > r:
        return "수익개선"
    if r > 5 and o < 0:
        return "외형성장"
    if r < -5 and o > 0:
        return "구조조정"
    if r < -5 and o < -5:
        return "전면역성장"
    return "혼합"


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

    target = collectScan(
        lazyParquet(scanPath).filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
    )
    if target.is_empty() or scCol not in target.columns:
        return _emptyGrowthFrame()

    # 연결 우선
    # 회사별 연결 우선. 유니버스 전체로 한 번에 좁히면 별도만 내는 회사가
    # 다른 회사 때문에 사라진다.
    target = preferConsolidatedPerCompany(target, scCol)

    # 연도별로 분리하여 CAGR 계산
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

    # 종목별 최신·기준 연도 (CAGR 은 pair 필요) — 글로벌 years[0] 버그 방지 (2026-04-23).
    # 한 종목의 2026 Q1 조기 제출 때문에 전종목이 2025 로 커트되던 현상 수정.
    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)
        yrs = sorted(sub["bsns_year"].unique().to_list(), reverse=True)
        if len(yrs) < 2:
            continue
        latestYear = yrs[0]
        # 3년 전 연도 찾기, 없으면 가장 오래된 연도
        baseYear = None
        nYears = 0
        for y in yrs:
            if int(latestYear) - int(y) >= 3:
                baseYear = y
                nYears = int(latestYear) - int(y)
                break
        if baseYear is None:
            baseYear = yrs[-1]
            nYears = int(latestYear) - int(baseYear)
        if nYears == 0:
            continue

        latSub = sub.filter(pl.col("bsns_year") == latestYear)
        baseSub = sub.filter(pl.col("bsns_year") == baseYear)

        revNow = extractAccount(latSub, _REVENUE_IDS, _REVENUE_NMS)
        revOld = extractAccount(baseSub, _REVENUE_IDS, _REVENUE_NMS)
        opNow = extractAccount(latSub, _OP_IDS, _OP_NMS)
        opOld = extractAccount(baseSub, _OP_IDS, _OP_NMS)
        niNow = extractAccount(latSub, _NI_IDS, _NI_NMS)
        niOld = extractAccount(baseSub, _NI_IDS, _NI_NMS)

        revCagr = _cagr(revOld, revNow, nYears) if revOld and revOld > 0 else None
        opCagr = _cagr(opOld, opNow, nYears) if opOld and opOld > 0 else None
        niCagr = _cagr(niOld, niNow, nYears) if niOld and niOld > 0 else None

        if revCagr is None and opCagr is None and niCagr is None:
            continue

        rows.append(
            {
                "stockCode": code,
                "revenue": round(revNow) if revNow else None,
                "revenueCagr": revCagr,
                "opIncomeCagr": opCagr,
                "netIncomeCagr": niCagr,
                "years": nYears,
                "grade": _gradeGrowth(revCagr, opCagr),
                "pattern": _classifyPattern(revCagr, opCagr, niCagr),
            }
        )

    if not rows:
        return _emptyGrowthFrame()

    return pl.DataFrame(rows, schema=_GROWTH_SCHEMA)


__all__ = ["scanGrowth"]
