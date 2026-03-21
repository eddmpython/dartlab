"""인력/급여 report 스캔 — employee, executivePayIndividual."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.engines.dart.scan._helpers import (
    find_latest_year,
    parse_num,
    pick_best_quarter,
    scan_parquets,
)


def scan_employee() -> dict[str, dict]:
    """employee → {종목코드: {직원수, 평균급여_만원, 남녀격차%, 근속_년}}.

    최신 연도 + 최적 분기(Q2) 기준.  급여는 가중평균.
    """
    raw = scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sexdstn", "sm", "jan_salary_am", "avrg_cnwk_sdytrn"],
    )
    if raw.is_empty():
        return {}

    latest_year = find_latest_year(raw, "jan_salary_am", 500)
    if latest_year is None:
        return {}

    sub = raw.filter(pl.col("year") == latest_year)
    result: dict[str, dict] = {}

    for code, group in sub.group_by("stockCode"):
        code_val = code[0]
        qdf = pick_best_quarter(group)

        total_emp, total_wsum = 0, 0.0
        male_emp, male_wsum = 0, 0.0
        female_emp, female_wsum = 0, 0.0
        tenure_emp, tenure_wsum = 0, 0.0

        for row in qdf.iter_rows(named=True):
            emp = parse_num(row.get("sm"))
            sal = parse_num(row.get("jan_salary_am"))
            tenure = parse_num(row.get("avrg_cnwk_sdytrn"))
            sex = row.get("sexdstn", "")

            if emp and emp > 0 and sal and sal > 0:
                total_emp += int(emp)
                total_wsum += emp * sal
                if sex and "남" in sex:
                    male_emp += int(emp)
                    male_wsum += emp * sal
                elif sex and "여" in sex:
                    female_emp += int(emp)
                    female_wsum += emp * sal

            if emp and emp > 0 and tenure and tenure > 0:
                tenure_emp += int(emp)
                tenure_wsum += emp * tenure

        if total_emp > 0 and total_wsum / total_emp > 1_000_000:  # 100만원 이상
            avg_sal = total_wsum / total_emp / 10000  # 만원/연
            male_avg = male_wsum / male_emp / 10000 if male_emp > 0 else None
            female_avg = female_wsum / female_emp / 10000 if female_emp > 0 else None
            gender_gap = None
            if male_avg and female_avg and male_avg > 0:
                gender_gap = round((male_avg - female_avg) / male_avg * 100, 1)
            avg_tenure = tenure_wsum / tenure_emp if tenure_emp > 0 else None

            result[code_val] = {
                "직원수": total_emp,
                "평균급여_만원": round(avg_sal, 0),
                "남녀격차": gender_gap,
                "근속_년": round(avg_tenure, 1) if avg_tenure else None,
            }

    return result


def scan_revenue_per_employee() -> dict[str, float]:
    """employee + finance IS → {종목코드: 직원당 매출(억)}."""
    # 직원수
    emp_map = scan_employee()

    # 매출 (finance IS)
    from dartlab.core.dataLoader import _dataDir

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

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    rev_map: dict[str, float] = {}
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
        except (pl.exceptions.ComputeError, pl.exceptions.SchemaError, OSError):
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

        years = sorted(rev_rows["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = rev_rows.filter(pl.col("bsns_year") == years[0])
        for row in latest.iter_rows(named=True):
            val = parse_num(row.get("thstrm_amount"))
            if val and val > 0:
                rev_map[code] = val
                break

    # 결합
    result: dict[str, float] = {}
    for code in emp_map:
        if code in rev_map:
            emp_count = emp_map[code]["직원수"]
            if emp_count > 0:
                result[code] = round(rev_map[code] / emp_count / 1e8, 1)  # 억 단위
    return result


def scan_top_pay() -> dict[str, dict]:
    """executivePayIndividual → {종목코드: {공개인원, 최고보수_억}}.

    5억 이상 의무공개자.  최신 연도 기준.
    """
    raw = scan_parquets(
        "executivePayIndividual",
        ["stockCode", "year", "quarter", "nm", "ofcps", "mendng_totamt"],
    )
    if raw.is_empty():
        return {}

    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    latest_year = None
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        valid = sub.filter(
            pl.col("mendng_totamt").is_not_null() & (pl.col("mendng_totamt") != "-") & (pl.col("mendng_totamt") != "")
        )
        if valid["stockCode"].n_unique() >= 200:
            latest_year = y
            break
    if latest_year is None:
        return {}

    latest = raw.filter(pl.col("year") == latest_year)
    result: dict[str, dict] = {}
    for code, group in latest.group_by("stockCode"):
        code_val = code[0]
        max_pay = 0.0
        count = 0
        for row in group.iter_rows(named=True):
            amt = parse_num(row.get("mendng_totamt"))
            if amt and amt > 0:
                count += 1
                pay_억 = amt / 1e8
                if pay_억 > max_pay:
                    max_pay = pay_억
        if count > 0:
            result[code_val] = {
                "공개인원": count,
                "최고보수_억": round(max_pay, 1),
            }
    return result
