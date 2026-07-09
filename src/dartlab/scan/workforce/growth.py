"""급여 성장률 vs 매출 성장률 — 급여-매출 괴리 분석."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    parseNumStr,
    pickBestQuarter,
    scanParquets,
)


def _weightedAvgSalary(group: pl.DataFrame) -> float | None:
    """직원수 가중평균 급여.

    Parameters
    ----------
    group : pl.DataFrame
        단일 종목의 employee 데이터 (sm, jan_salary_am 컬럼).

    Returns
    -------
    float | None
        가중평균 급여 (만원/연). 유효 데이터 없으면 None.
    """
    total_emp, total_wsum = 0, 0.0
    for row in group.iter_rows(named=True):
        emp = parseNumStr(row.get("sm"))
        sal = parseNumStr(row.get("jan_salary_am"))
        if emp and emp > 0 and sal and sal > 0:
            total_emp += int(emp)
            total_wsum += emp * sal
    if total_emp > 0:
        return total_wsum / total_emp / 10000
    return None


def scanSalaryGrowth() -> dict[str, dict]:
    """employee 2개년도 → {종목코드: {급여성장률, 급여_신, 급여_구}}.

    급여는 만원/연 단위 가중평균.

    Returns
    -------
    dict[str, dict]
        {종목코드: info}. 각 info:
            급여성장률 : float — 신/구 평균급여 증감률 (%)
            급여_신 : float — 최신 연도 평균급여 (만원)
            급여_구 : float — 직전 연도 평균급여 (만원)

    Capabilities:
        - employee 2 개년 가중평균 급여 또는 finance IS 2 개년 매출 비교 → 성장률 dict.
          가중평균 → 분기 노이즈 흡수.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner 또는 ``computeSalaryVsRevenue`` 의 source. AI agent 가
        "급여가 매출보다 빨리 늘어난 회사" 같은 인건비 부담 분석 시 본 함수 결과 사용.

    Guide:
        - 직전 연도 데이터 부족 (직원수 < 500 / 매출 0) 종목은 결과 제외.
        - 클램핑 ±500 % (전기 ~0 인 경우 발생하는 수만% noise 차단).

    When:
        ``scanWorkforce`` 진행 또는 ``computeSalaryVsRevenue`` 호출 시.

    How:
        ``scanParquets`` / ``_ensureScanData`` → 2 개년 데이터 추출 → 가중평균 또는 최대값 →
        성장률 계산 → dict / DataFrame 반환.

    Requires:
        - 로컬 ``data/dart/scan/report/employee.parquet`` 또는 ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`computeSalaryVsRevenue` — 본 두 함수의 결합 비교

    Raises
    ------
    polars.PolarsError
        employee report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.growth import scanSalaryGrowth
    >>> sg = scanSalaryGrowth()
    >>> sg.get("005930", {}).get("급여성장률")
    """
    raw = scanParquets(
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
        sal_new = _weightedAvgSalary(pickBestQuarter(grp_new))
        sal_old = _weightedAvgSalary(pickBestQuarter(grp_old))
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
    """프리빌드 finance.parquet → 종목별 매출성장률.

    Parameters
    ----------
    scanPath : Path
        프리빌드 finance.parquet 경로.

    Returns
    -------
    dict[str, float]
        {종목코드: 매출성장률(%)} — 최신 2개 연도 YoY.
    """
    scCol = "stockCode"

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
            & (pl.col("bsns_year") <= "2024")
            & (pl.col("account_id").is_in(list(REVENUE_IDS)) | pl.col("account_nm").is_in(list(REVENUE_NMS)))
        )
        .collect(engine="streaming")
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
            val = parseNumStr(row.get("thstrm_amount"))
            if val and val > 0:
                if newRev is None or val > newRev:
                    newRev = val

        oldRev = None
        for row in sub.filter(pl.col("bsns_year") == oldYear).iter_rows(named=True):
            val = parseNumStr(row.get("thstrm_amount"))
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
                .collect(engine="streaming")
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
            val = parseNumStr(row.get("thstrm_amount"))
            if val and val > 0:
                if newRev is None or val > newRev:
                    newRev = val

        oldRev = None
        for row in revRows.filter(pl.col("bsns_year") == completeYears[1]).iter_rows(named=True):
            val = parseNumStr(row.get("thstrm_amount"))
            if val and val > 0:
                if oldRev is None or val > oldRev:
                    oldRev = val

        if newRev and oldRev and oldRev > 0:
            result[code] = round((newRev - oldRev) / oldRev * 100, 1)

    return result


def scanRevenueGrowth() -> dict[str, float]:
    """finance IS 2개 완전연도 → {종목코드: 매출성장률(%)}.

    프리빌드 finance.parquet 우선, 없으면 per-file fallback.

    Returns
    -------
    dict[str, float]
        {종목코드: 매출성장률(%)}. 직전 연도 매출 0 이거나 매칭 실패 종목 제외.

    Capabilities:
        - employee 2 개년 가중평균 급여 또는 finance IS 2 개년 매출 비교 → 성장률 dict.
          가중평균 → 분기 노이즈 흡수.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner 또는 ``computeSalaryVsRevenue`` 의 source. AI agent 가
        "급여가 매출보다 빨리 늘어난 회사" 같은 인건비 부담 분석 시 본 함수 결과 사용.

    Guide:
        - 직전 연도 데이터 부족 (직원수 < 500 / 매출 0) 종목은 결과 제외.
        - 클램핑 ±500 % (전기 ~0 인 경우 발생하는 수만% noise 차단).

    When:
        ``scanWorkforce`` 진행 또는 ``computeSalaryVsRevenue`` 호출 시.

    How:
        ``scanParquets`` / ``_ensureScanData`` → 2 개년 데이터 추출 → 가중평균 또는 최대값 →
        성장률 계산 → dict / DataFrame 반환.

    Requires:
        - 로컬 ``data/dart/scan/report/employee.parquet`` 또는 ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`computeSalaryVsRevenue` — 본 두 함수의 결합 비교

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 시 per-file fallback 전환.

    Examples
    --------
    >>> from dartlab.scan.workforce.growth import scanRevenueGrowth
    >>> rg = scanRevenueGrowth()
    >>> rg.get("005930")
    """
    from dartlab.scan.io.parquet import _ensureScanData

    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"
    if scanPath.exists():
        return _scanRevenueGrowthFromMerged(scanPath)
    return _scanRevenueGrowthPerFile()


def computeSalaryVsRevenue(
    salMap: dict[str, dict] | None = None,
    revMap: dict[str, float] | None = None,
) -> pl.DataFrame:
    """급여성장률 vs 매출성장률 → DataFrame.

    Parameters
    ----------
    salMap : dict[str, dict] | None
        ``scanSalaryGrowth`` 결과. None 이면 즉시 호출.
    revMap : dict[str, float] | None
        ``scanRevenueGrowth`` 결과. None 이면 즉시 호출.

    Returns
    -------
    pl.DataFrame
        stockCode : str — 종목코드
        급여성장률 : float — (%)
        매출성장률 : float — (%)
        급여매출괴리 : float — 급여성장률 - 매출성장률 (%p)
        급여>매출 : bool — 급여매출괴리 > 0

    Capabilities:
        - employee 2 개년 가중평균 급여 또는 finance IS 2 개년 매출 비교 → 성장률 dict.
          가중평균 → 분기 노이즈 흡수.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner 또는 ``computeSalaryVsRevenue`` 의 source. AI agent 가
        "급여가 매출보다 빨리 늘어난 회사" 같은 인건비 부담 분석 시 본 함수 결과 사용.

    Guide:
        - 직전 연도 데이터 부족 (직원수 < 500 / 매출 0) 종목은 결과 제외.
        - 클램핑 ±500 % (전기 ~0 인 경우 발생하는 수만% noise 차단).

    When:
        ``scanWorkforce`` 진행 또는 ``computeSalaryVsRevenue`` 호출 시.

    How:
        ``scanParquets`` / ``_ensureScanData`` → 2 개년 데이터 추출 → 가중평균 또는 최대값 →
        성장률 계산 → dict / DataFrame 반환.

    Requires:
        - 로컬 ``data/dart/scan/report/employee.parquet`` 또는 ``data/dart/scan/finance.parquet``

    SeeAlso:
        - :func:`computeSalaryVsRevenue` — 본 두 함수의 결합 비교

    Raises
    ------
    polars.PolarsError
        하위 scan 호출 실패 시 전파.

    Examples
    --------
    >>> from dartlab.scan.workforce.growth import computeSalaryVsRevenue
    >>> df = computeSalaryVsRevenue()
    >>> df.filter(pl.col("급여>매출")).head()
    """
    if salMap is None:
        salMap = scanSalaryGrowth()
    if revMap is None:
        revMap = scanRevenueGrowth()

    _CAP = 500.0  # +-500% 초과 성장률은 의미 없음 (전기 매출 ~0 등)
    rows = []
    for code in salMap:
        if code not in revMap:
            continue
        sg = salMap[code]["급여성장률"]
        rg = revMap[code]
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
