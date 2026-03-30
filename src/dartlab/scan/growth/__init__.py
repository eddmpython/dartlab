"""성장성 스캔 -- 매출/영업이익/순이익 CAGR + 성장 패턴 분류."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import _ensureScanData

# ── 계정 매핑 ──

_REVENUE_IDS = {"Revenue", "revenue", "ifrs-full_Revenue", "dart_Revenue"}
_REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익"}

_OP_IDS = {
    "ProfitLossFromOperatingActivities",
    "operatingIncome",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "dart_OperatingIncomeLoss",
}
_OP_NMS = {"영업이익", "영업이익(손실)"}

_NI_IDS = {
    "ProfitLoss",
    "netIncome",
    "ifrs-full_ProfitLoss",
    "dart_ProfitLoss",
    "ProfitLossAttributableToOwnersOfParent",
}
_NI_NMS = {"당기순이익", "당기순이익(손실)"}


def _parseAmount(val) -> float | None:
    """금액 → float."""
    if val is None:
        return None
    s = str(val).replace(",", "").strip()
    if not s or s == "-":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _extractAccount(sub: pl.DataFrame, ids: set, nms: set) -> float | None:
    """DataFrame에서 특정 계정의 thstrm_amount 추출."""
    for row in sub.iter_rows(named=True):
        aid = row.get("account_id", "")
        anm = row.get("account_nm", "")
        if aid in ids or anm in nms:
            val = _parseAmount(row.get("thstrm_amount"))
            if val is not None:
                return val
    return None


def _cagr(old: float, new: float, years: int) -> float | None:
    """CAGR 계산 (%). new/old가 음수면 None."""
    if old is None or new is None or years <= 0 or old <= 0 or new <= 0:
        return None
    try:
        result = ((new / old) ** (1 / years) - 1) * 100
        if isinstance(result, complex):
            return None
        return round(result, 1)
    except (ZeroDivisionError, ValueError, OverflowError, TypeError):
        return None


def _gradeGrowth(revCagr: float | None, opCagr: float | None) -> str:
    """성장성 등급."""
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
    """성장 패턴 분류."""
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


def scanGrowth() -> pl.DataFrame:
    """전종목 성장성 스캔 -- 3년 CAGR + 등급 + 패턴."""
    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"

    if not scanPath.exists():
        return _scanPerFile()

    return _scanFromMerged(scanPath)


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet에서 성장성 계산."""
    schema = pl.scan_parquet(str(scanPath)).collect_schema().names()
    scCol = "stockCode" if "stockCode" in schema else "stock_code"

    allIds = list(_REVENUE_IDS | _OP_IDS | _NI_IDS)
    allNms = list(_REVENUE_NMS | _OP_NMS | _NI_NMS)

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
        .collect()
    )
    if target.is_empty():
        return pl.DataFrame()

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    # 연도별로 분리하여 CAGR 계산
    return _computeGrowth(target, scCol)


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 순회 fallback."""
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
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.is_empty():
            continue
        cfs = df.filter(pl.col("fs_nm").str.contains("연결"))
        allDfs.append(cfs if not cfs.is_empty() else df)

    if not allDfs:
        return pl.DataFrame()

    combined = pl.concat(allDfs, how="diagonal_relaxed")
    scCol = "stockCode" if "stockCode" in combined.columns else "stock_code"
    return _computeGrowth(combined, scCol)


def _computeGrowth(target: pl.DataFrame, scCol: str) -> pl.DataFrame:
    """종목별 3년 CAGR 계산."""
    years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
    if len(years) < 2:
        return pl.DataFrame()

    latestYear = years[0]
    # 3년 전 연도 찾기, 없으면 가장 오래된 연도
    baseYear = None
    nYears = 0
    for y in years:
        if int(latestYear) - int(y) >= 3:
            baseYear = y
            nYears = int(latestYear) - int(y)
            break
    if baseYear is None:
        baseYear = years[-1]
        nYears = int(latestYear) - int(baseYear)
    if nYears == 0:
        return pl.DataFrame()

    latest = target.filter(pl.col("bsns_year") == latestYear)
    base = target.filter(pl.col("bsns_year") == baseYear)

    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        latSub = latest.filter(pl.col(scCol) == code)
        baseSub = base.filter(pl.col(scCol) == code)

        revNow = _extractAccount(latSub, _REVENUE_IDS, _REVENUE_NMS)
        revOld = _extractAccount(baseSub, _REVENUE_IDS, _REVENUE_NMS)
        opNow = _extractAccount(latSub, _OP_IDS, _OP_NMS)
        opOld = _extractAccount(baseSub, _OP_IDS, _OP_NMS)
        niNow = _extractAccount(latSub, _NI_IDS, _NI_NMS)
        niOld = _extractAccount(baseSub, _NI_IDS, _NI_NMS)

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
        return pl.DataFrame()

    schema = {
        "stockCode": pl.Utf8,
        "revenue": pl.Float64,
        "revenueCagr": pl.Float64,
        "opIncomeCagr": pl.Float64,
        "netIncomeCagr": pl.Float64,
        "years": pl.Int64,
        "grade": pl.Utf8,
        "pattern": pl.Utf8,
    }
    return pl.DataFrame(rows, schema=schema)


__all__ = ["scanGrowth"]
