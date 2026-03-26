"""급여 성장률 vs 매출 성장률 — 인건비 부담 분석."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.market._helpers import (
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


def scan_revenue_growth() -> dict[str, float]:
    """finance IS 2개 완전연도 → {종목코드: 매출성장률(%)}.

    불완전 연도(2025+)는 제외.
    """
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    result: dict[str, float] = {}
    for pf in parquet_files:
        code = pf.stem
        try:
            is_df = (
                pl.scan_parquet(str(pf))
                .filter(
                    pl.col("sj_div").is_in(["IS", "CIS"])
                    & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
                )
                .collect()
            )
        except (pl.exceptions.PolarsError, OSError):
            continue
        if is_df.is_empty() or "account_id" not in is_df.columns:
            continue
        if is_df.is_empty():
            continue
        cfs = is_df.filter(pl.col("fs_nm").str.contains("연결"))
        target = cfs if not cfs.is_empty() else is_df

        rev_rows = target.filter(
            pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS))
        )
        if rev_rows.is_empty():
            rev_rows = target.filter(pl.col("account_nm").str.contains("매출"))
            if rev_rows.is_empty():
                continue

        complete_years = sorted(
            [y for y in rev_rows["bsns_year"].unique().to_list() if y <= "2024"],
            reverse=True,
        )
        if len(complete_years) < 2:
            continue

        new_rev = None
        for row in rev_rows.filter(pl.col("bsns_year") == complete_years[0]).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if new_rev is None or val > new_rev:
                    new_rev = val

        old_rev = None
        for row in rev_rows.filter(pl.col("bsns_year") == complete_years[1]).iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                if old_rev is None or val > old_rev:
                    old_rev = val

        if new_rev and old_rev and old_rev > 0:
            result[code] = round((new_rev - old_rev) / old_rev * 100, 1)

    return result


def compute_salary_vs_revenue(
    sal_map: dict[str, dict] | None = None,
    rev_map: dict[str, float] | None = None,
) -> pl.DataFrame:
    """급여성장률 vs 매출성장률 → DataFrame.

    컬럼: 종목코드, 급여성장률, 매출성장률, 인건비부담, 급여>매출
    """
    if sal_map is None:
        sal_map = scan_salary_growth()
    if rev_map is None:
        rev_map = scan_revenue_growth()

    rows = []
    for code in sal_map:
        if code not in rev_map:
            continue
        sg = sal_map[code]["급여성장률"]
        rg = rev_map[code]
        burden = sg - rg
        rows.append(
            {
                "종목코드": code,
                "급여성장률": sg,
                "매출성장률": rg,
                "인건비부담": round(burden, 1),
                "급여>매출": burden > 0,
            }
        )
    return pl.DataFrame(rows)
