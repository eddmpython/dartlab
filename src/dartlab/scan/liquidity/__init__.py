"""유동성 스캔 -- 유동비율 + 당좌비율 + 등급."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import _ensureScanData, extractAccount, parse_num

# ── 유동자산 ──

CA_IDS = {
    "CurrentAssets",
    "currentAssets",
    "ifrs-full_CurrentAssets",
    "dart_CurrentAssets",
}
CA_NMS = {"유동자산", "유동자산 합계"}

# ── 유동부채 ──

CL_IDS = {
    "CurrentLiabilities",
    "currentLiabilities",
    "ifrs-full_CurrentLiabilities",
    "dart_CurrentLiabilities",
}
CL_NMS = {"유동부채", "유동부채 합계"}

# ── 재고자산 ──

INV_IDS = {
    "Inventories",
    "inventories",
    "ifrs-full_Inventories",
    "dart_Inventories",
}
INV_NMS = {"재고자산"}


def _gradeLiquidity(currentRatio: float) -> str:
    """유동비율 → 등급."""
    if currentRatio >= 200:
        return "우수"
    if currentRatio >= 150:
        return "양호"
    if currentRatio >= 100:
        return "보통"
    if currentRatio >= 50:
        return "주의"
    return "위험"


_extractVal = extractAccount  # backward compat alias


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet → 종목별 유동성."""
    schema = pl.scan_parquet(str(scanPath)).collect_schema().names()
    scCol = "stockCode" if "stockCode" in schema else "stock_code"

    allIds = list(CA_IDS | CL_IDS | INV_IDS)
    allNms = list(CA_NMS | CL_NMS | INV_NMS)

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            (pl.col("sj_div") == "BS")
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("account_id").is_in(allIds) | pl.col("account_nm").is_in(allNms))
        )
        .collect()
    )
    if target.is_empty():
        return pl.DataFrame()

    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)

        ca = _extractVal(sub, CA_IDS, CA_NMS)
        cl = _extractVal(sub, CL_IDS, CL_NMS)
        inv = _extractVal(sub, INV_IDS, INV_NMS)

        if ca is None or cl is None or cl == 0:
            continue

        currentRatio = ca / cl * 100
        quickAssets = ca - (inv or 0)
        quickRatio = quickAssets / cl * 100 if cl > 0 else None

        rows.append(
            {
                "stockCode": code,
                "currentAssets": round(ca),
                "currentLiabilities": round(cl),
                "inventories": round(inv) if inv is not None else None,
                "currentRatio": round(currentRatio, 1),
                "quickRatio": round(quickRatio, 1) if quickRatio is not None else None,
                "grade": _gradeLiquidity(currentRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def _scanPerFile() -> pl.DataFrame:
    """종목별 finance parquet 순회 fallback."""
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    rows: list[dict] = []
    for pf in parquetFiles:
        code = pf.stem
        try:
            df = (
                pl.scan_parquet(str(pf))
                .filter(
                    (pl.col("sj_div") == "BS")
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if df.is_empty() or "account_id" not in df.columns:
            continue

        cfs = df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else df

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        ca = _extractVal(latest, CA_IDS, CA_NMS)
        cl = _extractVal(latest, CL_IDS, CL_NMS)
        inv = _extractVal(latest, INV_IDS, INV_NMS)

        if ca is None or cl is None or cl == 0:
            continue

        currentRatio = ca / cl * 100
        quickAssets = ca - (inv or 0)
        quickRatio = quickAssets / cl * 100 if cl > 0 else None

        rows.append(
            {
                "stockCode": code,
                "currentAssets": round(ca),
                "currentLiabilities": round(cl),
                "inventories": round(inv) if inv is not None else None,
                "currentRatio": round(currentRatio, 1),
                "quickRatio": round(quickRatio, 1) if quickRatio is not None else None,
                "grade": _gradeLiquidity(currentRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanLiquidity() -> pl.DataFrame:
    """전종목 유동성 스캔 -- 유동비율 + 당좌비율 + 등급."""
    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
