"""현금흐름 패턴 분류 — OCF/ICF/FCF + 라이프사이클 패턴."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import _ensureScanData, parse_num

# ── 영업활동CF ──

OCF_IDS = {
    "CashFlowsFromUsedInOperatingActivities",
    "CashFlowsFromOperatingActivities",
    "cashFlowsFromUsedInOperatingActivities",
    "ifrs-full_CashFlowsFromUsedInOperatingActivities",
    "OperatingCashFlows",
    "CashFromOperations",
}
OCF_NMS = {"영업활동현금흐름", "영업활동으로인한현금흐름", "영업활동현금흐름합계"}

# ── 투자활동CF ──

ICF_IDS = {
    "CashFlowsFromUsedInInvestingActivities",
    "CashFlowsFromInvestingActivities",
    "cashFlowsFromUsedInInvestingActivities",
    "ifrs-full_CashFlowsFromUsedInInvestingActivities",
    "InvestingCashFlows",
    "CashFromInvesting",
}
ICF_NMS = {"투자활동현금흐름", "투자활동으로인한현금흐름", "투자활동현금흐름합계"}

# ── 재무활동CF ──

FINCF_IDS = {
    "CashFlowsFromUsedInFinancingActivities",
    "CashFlowsFromFinancingActivities",
    "cashFlowsFromUsedInFinancingActivities",
    "ifrs-full_CashFlowsFromUsedInFinancingActivities",
    "FinancingCashFlows",
    "CashFromFinancing",
}
FINCF_NMS = {"재무활동현금흐름", "재무활동으로인한현금흐름", "재무활동현금흐름합계"}


# ── CF 패턴 분류 ──

_PATTERNS = {
    ("P", "N", "N"): "성장투자형",  # OCF+, ICF-, FINCF- → 자체CF로 투자+상환
    ("P", "N", "P"): "공격성장형",  # OCF+, ICF-, FINCF+ → 차입까지 동원해서 투자
    ("P", "P", "N"): "구조재편형",  # OCF+, ICF+, FINCF- → 자산매각+부채상환
    ("P", "P", "P"): "현금축적형",  # OCF+, ICF+, FINCF+ → 모든 채널에서 현금 유입
    ("N", "N", "P"): "외부의존형",  # OCF-, ICF-, FINCF+ → 차입으로 버팀
    ("N", "P", "N"): "축소정리형",  # OCF-, ICF+, FINCF- → 자산매각으로 부채상환
    ("N", "P", "P"): "위기대응형",  # OCF-, ICF+, FINCF+ → 자산매각+차입
    ("N", "N", "N"): "현금위기형",  # OCF-, ICF-, FINCF- → 모든 채널 유출
}


def _classifyPattern(ocf: float, icf: float, finCf: float) -> str:
    """OCF/ICF/FINCF 부호 조합 → 패턴 라벨."""
    key = (
        "P" if ocf >= 0 else "N",
        "P" if icf >= 0 else "N",
        "P" if finCf >= 0 else "N",
    )
    return _PATTERNS.get(key, "미분류")


def _scanFromMerged(scanPath: Path) -> pl.DataFrame:
    """프리빌드 finance.parquet → 종목별 CF 패턴."""
    scCol = "stockCode" if "stockCode" in pl.scan_parquet(str(scanPath)).collect_schema().names() else "stock_code"

    allIds = list(OCF_IDS | ICF_IDS | FINCF_IDS)
    allNms = list(OCF_NMS | ICF_NMS | FINCF_NMS)

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["CF"])
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
        ocf, icf, finCf = None, None, None
        for row in sub.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parse_num(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OCF_IDS or anm in OCF_NMS) and ocf is None:
                ocf = val
            elif (aid in ICF_IDS or anm in ICF_NMS) and icf is None:
                icf = val
            elif (aid in FINCF_IDS or anm in FINCF_NMS) and finCf is None:
                finCf = val

        if ocf is None:
            continue

        fcf = ocf + (icf or 0)
        rows.append(
            {
                "stockCode": code,
                "ocf": round(ocf),
                "icf": round(icf) if icf is not None else None,
                "finCf": round(finCf) if finCf is not None else None,
                "fcf": round(fcf),
                "pattern": _classifyPattern(ocf, icf or 0, finCf or 0),
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
            cfDf = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["CF"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if cfDf.is_empty() or "account_id" not in cfDf.columns:
            continue
        cfs = cfDf.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else cfDf

        years = sorted(target["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = target.filter(pl.col("bsns_year") == years[0])

        ocf, icf, finCf = None, None, None
        for row in latest.iter_rows(named=True):
            aid = row.get("account_id", "")
            anm = row.get("account_nm", "")
            val = parse_num(row.get("thstrm_amount"))
            if val is None:
                continue
            if (aid in OCF_IDS or anm in OCF_NMS) and ocf is None:
                ocf = val
            elif (aid in ICF_IDS or anm in ICF_NMS) and icf is None:
                icf = val
            elif (aid in FINCF_IDS or anm in FINCF_NMS) and finCf is None:
                finCf = val

        if ocf is None:
            continue

        fcf = ocf + (icf or 0)
        rows.append(
            {
                "stockCode": code,
                "ocf": round(ocf),
                "icf": round(icf) if icf is not None else None,
                "finCf": round(finCf) if finCf is not None else None,
                "fcf": round(fcf),
                "pattern": _classifyPattern(ocf, icf or 0, finCf or 0),
            }
        )

    return pl.DataFrame(rows) if rows else pl.DataFrame()


def scanCashflow() -> pl.DataFrame:
    """종목별 OCF/ICF/FCF + 현금흐름 패턴 분류.

    프리빌드 finance.parquet 우선, 없으면 per-file fallback.
    """
    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    if scanPath.exists():
        return _scanFromMerged(scanPath)
    return _scanPerFile()
