"""수익성 스캔 -- 영업이익률/순이익률/ROE/ROA + 섹터 대비 위치 + 등급."""

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

_TA_IDS = {"Assets", "totalAssets", "ifrs-full_Assets", "dart_Assets"}
_TA_NMS = {"자산총계", "자산 총계"}

_EQ_IDS = {
    "Equity",
    "equity",
    "ifrs-full_Equity",
    "EquityAttributableToOwnersOfParent",
    "ifrs-full_EquityAttributableToOwnersOfParent",
}
_EQ_NMS = {"자본총계", "자본 총계", "지배기업 소유주지분"}


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


def _gradeProfitability(opMargin: float | None, roe: float | None) -> str:
    """수익성 등급."""
    best = max(opMargin or -999, roe or -999)
    if best >= 20:
        return "우수"
    if best >= 10:
        return "양호"
    if best >= 5:
        return "보통"
    if best >= 0:
        return "저수익"
    return "적자"


def scanProfitability() -> pl.DataFrame:
    """전종목 수익성 스캔 -- 영업이익률/순이익률/ROE/ROA + 등급."""
    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"

    if not scanPath.exists():
        return _scanPerFile()

    return _scanFromMerged(scanPath)


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet에서 수익성 계산."""
    schema = pl.scan_parquet(str(scanPath)).collect_schema().names()
    scCol = "stockCode" if "stockCode" in schema else "stock_code"

    allIds = list(_REVENUE_IDS | _OP_IDS | _NI_IDS | _TA_IDS | _EQ_IDS)
    allNms = list(_REVENUE_NMS | _OP_NMS | _NI_NMS | _TA_NMS | _EQ_NMS)

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS", "BS"])
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

    return _computeProfitability(target, scCol)


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
                    pl.col("sj_div").is_in(["IS", "CIS", "BS"])
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
    return _computeProfitability(combined, scCol)


def _computeProfitability(target: pl.DataFrame, scCol: str) -> pl.DataFrame:
    """종목별 수익성 비율 계산 (최신 연도)."""
    years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
    if not years:
        return pl.DataFrame()

    latestYear = years[0]
    latest = target.filter(pl.col("bsns_year") == latestYear)

    rows: list[dict] = []
    for code in latest[scCol].unique().to_list():
        sub = latest.filter(pl.col(scCol) == code)

        rev = _extractAccount(sub, _REVENUE_IDS, _REVENUE_NMS)
        op = _extractAccount(sub, _OP_IDS, _OP_NMS)
        ni = _extractAccount(sub, _NI_IDS, _NI_NMS)
        ta = _extractAccount(sub, _TA_IDS, _TA_NMS)
        eq = _extractAccount(sub, _EQ_IDS, _EQ_NMS)

        opMargin = round(op / rev * 100, 1) if rev and rev != 0 and op is not None else None
        netMargin = round(ni / rev * 100, 1) if rev and rev != 0 and ni is not None else None
        roe = round(ni / eq * 100, 1) if eq and eq != 0 and ni is not None else None
        roa = round(ni / ta * 100, 1) if ta and ta != 0 and ni is not None else None

        if opMargin is None and netMargin is None and roe is None and roa is None:
            continue

        # netMargin이 opMargin 대비 극단적으로 크면 비경상 이익 의심
        hasNonRecurring = (
            netMargin is not None
            and opMargin is not None
            and abs(netMargin) > abs(opMargin) * 3
            and abs(netMargin) > 50
        )

        rows.append(
            {
                "stockCode": code,
                "opMargin": opMargin,
                "netMargin": netMargin,
                "roe": roe,
                "roa": roa,
                "grade": _gradeProfitability(opMargin, roe),
                "nonRecurring": hasNonRecurring,
            }
        )

    if not rows:
        return pl.DataFrame()

    schema = {
        "stockCode": pl.Utf8,
        "opMargin": pl.Float64,
        "netMargin": pl.Float64,
        "roe": pl.Float64,
        "roa": pl.Float64,
        "grade": pl.Utf8,
        "nonRecurring": pl.Boolean,
    }
    return pl.DataFrame(rows, schema=schema)


__all__ = ["scanProfitability"]
