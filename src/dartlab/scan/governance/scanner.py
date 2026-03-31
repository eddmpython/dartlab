"""거버넌스 6축 report 스캔."""

from __future__ import annotations

import polars as pl

from dartlab.scan._helpers import (
    find_latest_year,
    parse_num,
    pick_best_quarter,
    scan_parquets,
)


def scan_major_holder_pct() -> dict[str, float]:
    """majorHolder → {종목코드: 최대주주 지분율(%)}."""
    raw = scan_parquets(
        "majorHolder",
        ["stockCode", "year", "quarter", "bsis_posesn_stock_qota_rt"],
    )
    if raw.is_empty():
        return {}

    latest_year = find_latest_year(raw, "bsis_posesn_stock_qota_rt", 1000)
    if latest_year is None:
        return {}

    result: dict[str, float] = {}
    sub = raw.filter(pl.col("year") == latest_year)
    for code, group in sub.group_by("stockCode"):
        vals = []
        for row in group.iter_rows(named=True):
            v = parse_num(row.get("bsis_posesn_stock_qota_rt"))
            if v is not None and 0 <= v <= 100:
                vals.append(v)
        if vals:
            result[code[0]] = max(vals)
    return result


def scan_outside_directors() -> dict[str, dict]:
    """outsideDirector → {종목코드: {사외이사비율, 중도사임, 겸직}}.

    outsideDirector parquet의 drctr_co/otcmp_drctr_co 집계값 사용.
    fallback: executive parquet의 ofcps 문자열 파싱.
    """
    raw = scan_parquets(
        "outsideDirector",
        ["stockCode", "year", "quarter", "drctr_co", "otcmp_drctr_co", "mdstrm_resig", "rlsofc"],
    )

    if not raw.is_empty():
        return _outsideFromDedicated(raw)

    # fallback: executive parquet
    return _outsideFromExecutive()


def _outsideFromDedicated(raw: pl.DataFrame) -> dict[str, dict]:
    """outsideDirector parquet → 사외이사 비율 + 중도사임 + 겸직."""
    latestYear = find_latest_year(raw, "drctr_co", 500)
    if latestYear is None:
        return {}

    sub = raw.filter(pl.col("year") == latestYear)
    result: dict[str, dict] = {}

    for code, group in sub.group_by("stockCode"):
        codeVal = code[0]
        qdf = pick_best_quarter(group)

        totalDirectors = 0
        outsideDirectors = 0
        resignCount = 0
        concurrentCount = 0

        for row in qdf.iter_rows(named=True):
            d = parse_num(row.get("drctr_co"))
            o = parse_num(row.get("otcmp_drctr_co"))
            r = parse_num(row.get("mdstrm_resig"))
            c = parse_num(row.get("rlsofc"))

            if d and d > 0:
                totalDirectors += int(d)
            if o and o > 0:
                outsideDirectors += int(o)
            if r and r > 0:
                resignCount += int(r)
            if c and c > 0:
                concurrentCount += int(c)

        if totalDirectors > 0:
            result[codeVal] = {
                "사외이사비율": outsideDirectors / totalDirectors * 100,
                "중도사임": resignCount,
                "겸직": concurrentCount,
            }

    return result


def _outsideFromExecutive() -> dict[str, dict]:
    """executive parquet fallback → 사외이사 비율만 (중도사임/겸직 없음)."""
    raw = scan_parquets(
        "executive",
        ["stockCode", "year", "quarter", "ofcps"],
    )
    if raw.is_empty():
        return {}

    latestYear = find_latest_year(raw, "ofcps", 1000)
    if latestYear is None:
        return {}

    result: dict[str, dict] = {}
    sub = raw.filter(pl.col("year") == latestYear)
    for code, group in sub.group_by("stockCode"):
        total = group.shape[0]
        outside = sum(1 for row in group.iter_rows(named=True) if row.get("ofcps") and "사외" in row["ofcps"])
        result[code[0]] = {
            "사외이사비율": outside / total * 100 if total > 0 else 0,
            "중도사임": 0,
            "겸직": 0,
        }
    return result


def scan_pay_ratio() -> dict[str, float]:
    """executivePayAllTotal + employee → {종목코드: pay ratio(배)}."""
    raw_pay = scan_parquets(
        "executivePayAllTotal",
        ["stockCode", "year", "quarter", "nmpr", "jan_avrg_mendng_am"],
    )
    raw_emp = scan_parquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am"],
    )
    if raw_pay.is_empty() or raw_emp.is_empty():
        return {}

    # 임원 평균보수
    pay_map: dict[str, float] = {}
    latest = find_latest_year(raw_pay, "jan_avrg_mendng_am", 500)
    if latest:
        sub = raw_pay.filter(pl.col("year") == latest)
        for code, group in sub.group_by("stockCode"):
            qdf = pick_best_quarter(group)
            wsum, tnmpr = 0.0, 0
            for row in qdf.iter_rows(named=True):
                n = parse_num(row.get("nmpr"))
                p = parse_num(row.get("jan_avrg_mendng_am"))
                if n and n > 0 and p and p > 0:
                    wsum += n * p
                    tnmpr += int(n)
            if tnmpr > 0:
                pay_map[code[0]] = wsum / tnmpr

    # 직원 평균급여
    sal_map: dict[str, float] = {}
    latest = find_latest_year(raw_emp, "jan_salary_am", 500)
    if latest:
        sub = raw_emp.filter(pl.col("year") == latest)
        for code, group in sub.group_by("stockCode"):
            qdf = pick_best_quarter(group)
            wsum, temp = 0.0, 0
            for row in qdf.iter_rows(named=True):
                e = parse_num(row.get("sm"))
                s = parse_num(row.get("jan_salary_am"))
                if e and e > 0 and s and s > 0:
                    wsum += e * s
                    temp += int(e)
            if temp > 0:
                sal_map[code[0]] = wsum / temp

    result: dict[str, float] = {}
    for code in pay_map:
        if code in sal_map and sal_map[code] > 0:
            ratio = pay_map[code] / sal_map[code]
            # pay_ratio 극단값 cap: 500배 초과는 데이터 오류
            if ratio > 500:
                continue
            result[code] = ratio
    return result


def scan_audit_opinion() -> dict[str, str]:
    """auditOpinion → {종목코드: 감사의견 문자열}."""
    raw = scan_parquets(
        "auditOpinion",
        ["stockCode", "year", "quarter", "adt_opinion"],
    )
    if raw.is_empty():
        return {}

    opinion_rank = {"의견거절": 4, "부적정의견": 3, "한정의견": 2, "적정의견": 1}
    result: dict[str, str] = {}
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    for y in years_desc:
        sub = raw.filter(pl.col("year") == y)
        if sub.filter(pl.col("adt_opinion").is_not_null()).shape[0] < 500:
            continue
        for code, group in sub.group_by("stockCode"):
            valid_rows = group.filter(pl.col("adt_opinion").is_not_null())
            if valid_rows.is_empty():
                continue
            worst, worst_op = 0, None
            for row in valid_rows.iter_rows(named=True):
                op = row.get("adt_opinion")
                if op:
                    r = opinion_rank.get(op, 0)
                    if r > worst:
                        worst = r
                        worst_op = op
                    elif worst_op is None:
                        worst_op = op
            if worst_op:
                result[code[0]] = worst_op
        break
    return result


def scan_minority_holder() -> dict[str, float]:
    """minorityHolder → {종목코드: 소액주주 지분율(%)}.

    hold_stock_rate가 높을수록 주주 분산이 양호.
    """
    raw = scan_parquets(
        "minorityHolder",
        ["stockCode", "year", "quarter", "hold_stock_rate"],
    )
    if raw.is_empty():
        return {}

    latestYear = find_latest_year(raw, "hold_stock_rate", 500)
    if latestYear is None:
        return {}

    sub = raw.filter(pl.col("year") == latestYear)
    result: dict[str, float] = {}

    for code, group in sub.group_by("stockCode"):
        codeVal = code[0]
        qdf = pick_best_quarter(group)
        vals = []
        for row in qdf.iter_rows(named=True):
            raw_val = row.get("hold_stock_rate")
            if raw_val is not None:
                cleaned = str(raw_val).strip().rstrip("%")
                v = parse_num(cleaned)
                if v is not None and 0 <= v <= 100:
                    vals.append(v)
        if vals:
            result[codeVal] = max(vals)

    return result
