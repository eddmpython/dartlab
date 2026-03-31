"""이익의 질 (Earnings Quality) -- Accrual Ratio 기반 전종목 스캔."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import _ensureScanData, parse_num

# ── 순이익 ──

NI_IDS = {
    "ProfitLoss",
    "ProfitLossAttributableToOwnersOfParent",
    "ifrs-full_ProfitLoss",
    "ifrs-full_ProfitLossAttributableToOwnersOfParent",
    "NetIncomeLoss",
    "dart_ProfitLoss",
}
NI_NMS = {"당기순이익", "당기순이익(손실)", "지배기업소유주지분순이익"}

# ── 영업활동CF ──

OCF_IDS = {
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromOperatingActivities",
    "cashFlowsFromUsedInOperatingActivities",
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
}
OCF_NMS = {"영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동현금흐름합계"}

# ── 총자산 ──

TA_IDS = {
    "Assets",
    "ifrs-full_Assets",
    "TotalAssets",
}
TA_NMS = {"자산총계"}


# ── 등급 분류 ──


def _gradeQuality(accrualRatio: float) -> str:
    """accrual ratio → 등급."""
    if accrualRatio <= -0.05:
        return "우수"  # CF가 이익보다 훨씬 큼
    if accrualRatio <= 0.05:
        return "양호"  # 이익과 CF가 비슷
    if accrualRatio <= 0.15:
        return "보통"  # 약간의 accrual
    if accrualRatio <= 0.25:
        return "주의"  # accrual 비중 높음
    return "위험"  # 이익 대부분이 accrual


def _extractVal(sub: pl.DataFrame, ids: set, nms: set, amtCol: str = "thstrm_amount") -> float | None:
    """DataFrame에서 특정 계정의 값 추출."""
    for row in sub.iter_rows(named=True):
        aid = row.get("account_id", "")
        anm = row.get("account_nm", "")
        if aid in ids or anm in nms:
            val = parse_num(row.get(amtCol))
            if val is not None:
                return val
    return None


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet → 종목별 이익의 질."""
    schema = pl.scan_parquet(str(scanPath)).collect_schema().names()
    scCol = "stockCode" if "stockCode" in schema else "stock_code"

    allIds = list(NI_IDS | OCF_IDS | TA_IDS)
    allNms = list(NI_NMS | OCF_NMS | TA_NMS)

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS", "CF", "BS"])
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

    # 종목별 최신 연도
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    rows: list[dict] = []
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)

        # IS/CIS에서 순이익
        isSub = sub.filter(pl.col("sj_div").is_in(["IS", "CIS"]))
        ni = _extractVal(isSub, NI_IDS, NI_NMS)

        # CF에서 영업CF
        cfSub = sub.filter(pl.col("sj_div") == "CF")
        ocf = _extractVal(cfSub, OCF_IDS, OCF_NMS)

        # BS에서 총자산
        bsSub = sub.filter(pl.col("sj_div") == "BS")
        ta = _extractVal(bsSub, TA_IDS, TA_NMS)

        if ni is None or ocf is None or ta is None or ta == 0:
            continue

        accrualRatio = (ni - ocf) / abs(ta)
        cfToNi = ocf / ni if ni != 0 else None
        # cfToNi 극단값 cap: ±20 초과는 의미 없음 (분모 극소)
        if cfToNi is not None and abs(cfToNi) > 20:
            cfToNi = None

        rows.append(
            {
                "stockCode": code,
                "netIncome": round(ni),
                "operatingCf": round(ocf),
                "totalAssets": round(ta),
                "accrualRatio": round(accrualRatio, 4),
                "cfToNi": round(cfToNi, 4) if cfToNi is not None else None,
                "grade": _gradeQuality(accrualRatio),
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
                    pl.col("sj_div").is_in(["IS", "CIS", "CF", "BS"])
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

        isSub = latest.filter(pl.col("sj_div").is_in(["IS", "CIS"]))
        ni = _extractVal(isSub, NI_IDS, NI_NMS)

        cfSub = latest.filter(pl.col("sj_div") == "CF")
        ocf = _extractVal(cfSub, OCF_IDS, OCF_NMS)

        bsSub = latest.filter(pl.col("sj_div") == "BS")
        ta = _extractVal(bsSub, TA_IDS, TA_NMS)

        if ni is None or ocf is None or ta is None or ta == 0:
            continue

        accrualRatio = (ni - ocf) / abs(ta)
        cfToNi = ocf / ni if ni != 0 else None
        # cfToNi 극단값 cap: ±20 초과는 의미 없음 (분모 극소)
        if cfToNi is not None and abs(cfToNi) > 20:
            cfToNi = None

        rows.append(
            {
                "stockCode": code,
                "netIncome": round(ni),
                "operatingCf": round(ocf),
                "totalAssets": round(ta),
                "accrualRatio": round(accrualRatio, 4),
                "cfToNi": round(cfToNi, 4) if cfToNi is not None else None,
                "grade": _gradeQuality(accrualRatio),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanQuality() -> pl.DataFrame:
    """전종목 이익의 질 스캔 -- Accrual Ratio + CF/NI 비율 + 등급."""
    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
