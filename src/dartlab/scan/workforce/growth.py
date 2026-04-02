"""급여 성장률 vs 매출 성장률 — 급여-매출 괴리 분석."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan._helpers import (
    parse_num,
    pick_best_quarter,
    scan_parquets,
)


def _weighted_avg_salary(group: pl.DataFrame) -> float | None:
    """직원수 가중평균 급여 (만원/연)."""
    total_emp, total_wsum = 0, 0.0
    for row in group.iter_rows(named=True):
        emp = parse_num(row.get("sm"))
        sal = parse_num(row.get("jan_salary_am"))
        if emp and emp > 0 and sal and sal > 0:
            total_emp += int(emp)
            total_wsum += emp * sal
    if total_emp > 0:
        return total_wsum / total_emp / 10000
    return None


def scan_salary_growth() -> dict[str, dict]:
    """employee 2개년도 → {종목코드: {급여성장률, 급여_신, 급여_구}}.

    급여는 만원/연 단위 가중평균.
    """
    raw = scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am"],
    )
    if raw.is_empty():
        return {}

    years = sorted(raw["year"].unique().to_list(), reverse=True)
    valid_years = []
    for y in years:
        sub = raw.filter(pl.col("year") == y)
        ok = sub.filter(pl.col("jan_salary_am").is_not_null() & (pl.col("jan_salary_am") != "-")).shape[0]
        if ok >= 500:
            valid_years.append(y)
            if len(valid_years) == 2:
                break
    if len(valid_years) < 2:
        return {}

    y_new, y_old = valid_years[0], valid_years[1]
    result: dict[str, dict] = {}
    for code in raw["stockCode"].unique().to_list():
        grp_new = raw.filter((pl.col("stockCode") == code) & (pl.col("year") == y_new))
        grp_old = raw.filter((pl.col("stockCode") == code) & (pl.col("year") == y_old))
        if grp_new.is_empty() or grp_old.is_empty():
            continue
        sal_new = _weighted_avg_salary(pick_best_quarter(grp_new))
        sal_old = _weighted_avg_salary(pick_best_quarter(grp_old))
        if sal_new and sal_old and sal_old > 100:
            growth = (sal_new - sal_old) / sal_old * 100
            result[code] = {
                "급여성장률": round(growth, 1),
                "급여_신": round(sal_new, 0),
                "급여_구": round(sal_old, 0),
            }
    return result


REVENUE_IDS = {
    "Revenue",
    "Revenues",
    "revenue",
    "revenues",
    "ifrs-full_Revenue",
    "dart_Revenue",
    "RevenueFromContractsWithCustomers",
}
REVENUE_NMS = {"매출액", "수익(매출액)", "영업수익", "매출", "순영업수익"}


def _scanRevenueGrowthFromMerged(scanPath: Path) -> dict[str, float]:
    """프리빌드 finance.parquet → 종목별 매출성장률."""
    scCol = "stockCode" if "stockCode" in pl.scan_parquet(str(scanPath)).collect_schema().names() else "stock_code"

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("bsns_year") <= "2024")
            & (pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS)))
        )
        .collect()
    )
    if target.is_empty():
        return {}

    # 연결 우선
    cfs = target.filter(pl.col("fs_nm").str.contains("연결"))
    if not cfs.is_empty():
        target = cfs

    result: dict[str, float] = {}
    for code in target[scCol].unique().to_list():
        sub = target.filter(pl.col(scCol) == code)
        years = sorted(sub["bsns_year"].unique().to_list(), reverse=True)
        if len(years) < 2:
            continue

        newYear, oldYear = years[0], years[1]
        newRev = None
        for row in sub.filter(pl.col("bsns_year") == newYear).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if newRev is None or val > newRev:
                    newRev = val

        oldRev = None
        for row in sub.filter(pl.col("bsns_year") == oldYear).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if oldRev is None or val > oldRev:
                    oldRev = val

        if newRev and oldRev and oldRev > 0:
            result[code] = round((newRev - oldRev) / oldRev * 100, 1)

    return result


def _scanRevenueGrowthPerFile() -> dict[str, float]:
    """종목별 finance parquet 순회 fallback."""
    from dartlab.core.dataLoader import _dataDir

    financeDir = Path(_dataDir("finance"))
    parquetFiles = sorted(financeDir.glob("*.parquet"))

    result: dict[str, float] = {}
    for pf in parquetFiles:
        code = pf.stem
        try:
            isDf = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if isDf.is_empty() or "account_id" not in isDf.columns:
            continue
        cfs = isDf.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else isDf

        revRows = target.filter(
            pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS))
        )
        if revRows.is_empty():
            revRows = target.filter(pl.col("account_nm").str.contains("매출"))
            if revRows.is_empty():
                continue

        completeYears = sorted(
            [y for y in revRows["bsns_year"].unique().to_list() if y <= "2024"],
            reverse=True,
        )
        if len(completeYears) < 2:
            continue

        newRev = None
        for row in revRows.filter(pl.col("bsns_year") == completeYears[0]).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if newRev is None or val > newRev:
                    newRev = val

        oldRev = None
        for row in revRows.filter(pl.col("bsns_year") == completeYears[1]).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if oldRev is None or val > oldRev:
                    oldRev = val

        if newRev and oldRev and oldRev > 0:
            result[code] = round((newRev - oldRev) / oldRev * 100, 1)

    return result


def scan_revenue_growth() -> dict[str, float]:
    """finance IS 2개 완전연도 → {종목코드: 매출성장률(%)}.

    프리빌드 finance.parquet 우선, 없으면 per-file fallback.
    """
    from dartlab.scan._helpers import _ensureScanData

    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    if scanPath.exists():
        return _scanRevenueGrowthFromMerged(scanPath)
    return _scanRevenueGrowthPerFile()


def compute_salary_vs_revenue(
    sal_map: dict[str, dict] | None = None,
    rev_map: dict[str, float] | None = None,
) -> pl.DataFrame:
    """급여성장률 vs 매출성장률 → DataFrame.

    컬럼: 종목코드, 급여성장률, 매출성장률, 급여매출괴리, 급여>매출
    """
    if sal_map is None:
        sal_map = scan_salary_growth()
    if rev_map is None:
        rev_map = scan_revenue_growth()

    _CAP = 500.0  # +-500% 초과 성장률은 의미 없음 (전기 매출 ~0 등)
    rows = []
    for code in sal_map:
        if code not in rev_map:
            continue
        sg = sal_map[code]["급여성장률"]
        rg = rev_map[code]
        # 극단값 클램핑 — 전기 매출/급여가 극소일 때 수만% 발생 방지
        sg_c = max(-_CAP, min(_CAP, sg))
        rg_c = max(-_CAP, min(_CAP, rg))
        burden = sg_c - rg_c
        rows.append(
            {
                "stockCode": code,
                "급여성장률": round(sg_c, 1),
                "매출성장률": round(rg_c, 1),
                "급여매출괴리": round(burden, 1),
                "급여>매출": burden > 0,
            }
        )
    return pl.DataFrame(rows)
