"""인력/급여 report 스캔 — employee, executivePayIndividual."""

from __future__ import annotations

from pathlib import Path

import polars as pl

from dartlab.scan.io.parquet import (
    findLatestYear,
    latestDataRows,
    parseNumStr,
    pickBestQuarter,
    preferConsolidatedPerCompany,
    scanParquets,
)


def scanEmployee() -> dict[str, dict]:
    """employee 공시에서 종목별 인력 현황을 추출한다.

    최신 연도 + 최적 분기(Q2) 기준. 급여는 직원수 가중평균.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        employee report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanEmployee
    >>> emp = scanEmployee()
    >>> emp.get("005930", {}).get("직원수")

    Returns
    -------
    dict[str, dict]
        {종목코드: 인력현황}. 각 인력현황 dict 키:

        - 직원수 : int — 전체 직원 수 (명)
        - 평균급여_만원 : float — 직원수 가중평균 연봉 (만원)
        - 남녀격차 : float | None — (남성평균 - 여성평균) / 남성평균 (%)
        - 근속_년 : float | None — 직원수 가중평균 근속연수 (년)
    """
    raw = scanParquets(
        "employee",
        ["stockCode", "year", "quarter", "sexdstn", "sm", "jan_salary_am", "avrg_cnwk_sdytrn"],
    )
    if raw.is_empty():
        return {}

    latest_year = findLatestYear(raw, "jan_salary_am", 500)
    if latest_year is None:
        return {}

    sub = raw.filter(pl.col("year") == latest_year)
    result: dict[str, dict] = {}

    for code, group in sub.group_by("stockCode"):
        code_val = code[0]
        qdf = pickBestQuarter(group)

        total_emp, total_wsum = 0, 0.0
        male_emp, male_wsum = 0, 0.0
        female_emp, female_wsum = 0, 0.0
        tenure_emp, tenure_wsum = 0, 0.0

        for row in qdf.iter_rows(named=True):
            emp = parseNumStr(row.get("sm"))
            sal = parseNumStr(row.get("jan_salary_am"))
            tenure = parseNumStr(row.get("avrg_cnwk_sdytrn"))
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
            # 근속 극단값 cap: 60년 초과는 데이터 파싱 오류
            if avg_tenure is not None and avg_tenure > 60:
                avg_tenure = None
            # 평균급여 극단값 cap: 50억원(50만 만원) 초과는 데이터 오류
            if avg_sal > 500_000:
                avg_sal = None

            if avg_sal is None:
                continue

            result[code_val] = {
                "직원수": total_emp,
                "평균급여_만원": round(avg_sal, 0),
                "남녀격차": gender_gap,
                "근속_년": round(avg_tenure, 1) if avg_tenure else None,
            }

    return result


def scanTotalPayroll() -> dict[str, float]:
    """employee 공시에서 종목별 연간 총급여를 추출한다.

    fyer_salary_totamt 합산 우선, 없으면 sm*jan_salary_am fallback.
    Q4 우선 (연간 누적). Q4 없으면 Q2*2 연환산.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        employee report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanTotalPayroll
    >>> tp = scanTotalPayroll()
    >>> tp.get("005930")

    Returns
    -------
    dict[str, float]
        {종목코드: 연간 총급여(원)}.
    """
    PAYROLL_QUARTER_ORDER = {"4분기": 1, "2분기": 2, "3분기": 3, "1분기": 4}

    raw = scanParquets(
        "employee",
        ["stockCode", "year", "quarter", "sm", "jan_salary_am", "fyer_salary_totamt"],
    )
    if raw.is_empty():
        return {}

    latestYear = findLatestYear(raw, "jan_salary_am", 500)
    if latestYear is None:
        return {}

    sub = raw.filter(pl.col("year") == latestYear)
    result: dict[str, float] = {}

    for code, group in sub.group_by("stockCode"):
        codeVal = code[0]
        quarters = group["quarter"].unique().to_list()
        bestQ = sorted(quarters, key=lambda q: PAYROLL_QUARTER_ORDER.get(q, 99))
        qdf = group.filter(pl.col("quarter") == bestQ[0]) if bestQ else group
        isHalf = bestQ[0] == "2분기" if bestQ else False

        total = 0.0
        usedDirect = False
        for row in qdf.iter_rows(named=True):
            direct = parseNumStr(row.get("fyer_salary_totamt"))
            if direct and direct > 0:
                total += direct
                usedDirect = True
            else:
                emp = parseNumStr(row.get("sm"))
                sal = parseNumStr(row.get("jan_salary_am"))
                if emp and emp > 0 and sal and sal > 0:
                    total += emp * sal

        if total > 0:
            if isHalf and not usedDirect:
                total *= 2
            result[codeVal] = total

    return result


def scanRevenuePerEmployee() -> dict[str, float]:
    """employee + finance IS에서 종목별 직원당 매출을 산출한다.

    scan/finance.parquet 프리빌드가 있으면 단일 파일에서 매출 추출,
    없으면 종목별 parquet 순회 fallback.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        scan finance.parquet 손상 시 per-file fallback 전환.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanRevenuePerEmployee
    >>> rpe = scanRevenuePerEmployee()
    >>> rpe.get("005930")

    Returns
    -------
    dict[str, float]
        {종목코드: 직원당 매출(억)}.
    """
    emp_map = scanEmployee()

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

    from dartlab.scan.io.parquet import _ensureScanData

    scanDir = _ensureScanData()
    scanPath = scanDir / "finance.parquet"

    if scanPath.exists():
        try:
            revMap = _revenueFromMerged(scanPath, REVENUE_IDS, REVENUE_NMS)
        except (pl.exceptions.PolarsError, OSError):
            revMap = _revenueFallback(REVENUE_IDS, REVENUE_NMS)
    else:
        revMap = _revenueFallback(REVENUE_IDS, REVENUE_NMS)

    result: dict[str, float] = {}
    for code in emp_map:
        if code in revMap:
            emp_count = emp_map[code]["직원수"]
            if emp_count > 0:
                result[code] = round(revMap[code] / emp_count / 1e8, 1)
    return result


def _revenueFromMerged(scanPath: Path, revIds: set[str], revNms: set[str]) -> dict[str, float]:
    """합산 finance parquet에서 종목별 매출을 추출한다.

    연결재무제표 우선, 없으면 개별재무제표. 종목별 최신 연도 기준.
    1차 매칭 실패 시 account_nm에 "매출" 포함 행으로 fallback.

    Parameters
    ----------
    scanPath : Path
        scan/finance.parquet 파일 경로.
    revIds : set[str]
        매출 account_id 후보 집합.
    revNms : set[str]
        매출 account_nm 후보 집합.

    Returns
    -------
    dict[str, float]
        {종목코드: 매출액(원)}.
    """
    scCol = "stockCode"

    target = (
        pl.scan_parquet(str(scanPath))
        .filter(
            pl.col("sj_div").is_in(["IS", "CIS"])
            & (pl.col("fs_nm").str.contains("연결") | pl.col("fs_nm").str.contains("재무제표"))
        )
        .collect(engine="streaming")
    )
    if target.is_empty() or "account_id" not in target.columns:
        return {}

    # 회사별 연결 우선. 유니버스 전체로 한 번에 좁히면 별도만 내는 회사가
    # 다른 회사 때문에 사라진다.
    target = preferConsolidatedPerCompany(target, scCol)

    # 종목별 최신 연도
    latestYear = target.group_by(scCol).agg(pl.col("bsns_year").max().alias("_maxYear"))
    target = target.join(latestYear, on=scCol).filter(pl.col("bsns_year") == pl.col("_maxYear")).drop("_maxYear")

    matched = target.filter(pl.col("account_id").is_in(list(revIds)) | pl.col("account_nm").is_in(list(revNms)))

    revMap: dict[str, float] = {}
    for row in matched.iter_rows(named=True):
        code = row.get(scCol, "")
        val = parseNumStr(row.get("thstrm_amount"))
        if code and val and val > 0 and code not in revMap:
            revMap[code] = val

    # 1차 매칭 실패 종목은 "매출" 포함 fallback
    matchedCodes = set(revMap.keys())
    allCodes = set(target[scCol].unique().to_list())
    missingCodes = allCodes - matchedCodes
    if missingCodes:
        fallbackRows = target.filter(
            pl.col(scCol).is_in(list(missingCodes)) & pl.col("account_nm").str.contains("매출")
        )
        for row in fallbackRows.iter_rows(named=True):
            code = row.get(scCol, "")
            val = parseNumStr(row.get("thstrm_amount"))
            if code and val and val > 0 and code not in revMap:
                revMap[code] = val

    return revMap


def _revenueFallback(revIds: set[str], revNms: set[str]) -> dict[str, float]:
    """종목별 finance parquet 파일을 순회하여 매출을 추출한다 (fallback).

    합산 finance.parquet이 없거나 읽기 실패 시 사용.
    각 종목 parquet에서 연결재무제표 우선, 최신 연도 기준.

    Parameters
    ----------
    revIds : set[str]
        매출 account_id 후보 집합.
    revNms : set[str]
        매출 account_nm 후보 집합.

    Returns
    -------
    dict[str, float]
        {종목코드: 매출액(원)}.
    """
    from dartlab.core.dataLoader import _dataDir

    finance_dir = Path(_dataDir("finance"))
    parquet_files = sorted(finance_dir.glob("*.parquet"))

    revMap: dict[str, float] = {}
    for pf in parquet_files:
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

        rev_rows = target.filter(pl.col("account_id").is_in(list(revIds)) | pl.col("account_nm").is_in(list(revNms)))
        if rev_rows.is_empty():
            rev_rows = target.filter(pl.col("account_nm").str.contains("매출"))
        if rev_rows.is_empty():
            continue

        years = sorted(rev_rows["bsns_year"].unique().to_list(), reverse=True)
        if not years:
            continue
        latest = rev_rows.filter(pl.col("bsns_year") == years[0])
        for row in latest.iter_rows(named=True):
            val = parseNumStr(row.get("thstrm_amount"))
            if val and val > 0:
                revMap[code] = val
                break
    return revMap


def scanTopPay() -> dict[str, dict]:
    """executivePayIndividual 공시에서 종목별 고액 보수자 현황을 추출한다.

    5억 이상 의무공개 대상. 최신 연도(유효 종목 200개 이상인 해) 기준.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        executivePayIndividual report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanTopPay
    >>> tp = scanTopPay()
    >>> tp.get("005930", {}).get("최고보수_억")

    Returns
    -------
    dict[str, dict]
        {종목코드: 고액보수 현황}. 각 dict 키:

        - 공개인원 : int — 5억 이상 보수 공개 대상 인원 (명)
        - 최고보수_억 : float — 최고 개인 보수 (억)
    """
    raw = scanParquets(
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
            amt = parseNumStr(row.get("mendng_totamt"))
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


# ── 인건비 효율 지표 (former workforce/efficiency.py, P-S5 absorbed) ──

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

OP_IDS = {
    "dart_OperatingIncomeLoss",
    "ifrs-full_ProfitLossFromOperatingActivities",
    "OperatingIncomeLoss",
}
OP_NMS = {"영업이익", "영업이익(손실)", "영업손익"}


def _revenueMap() -> dict[str, float]:
    """전종목 매출액을 scan/finance parquet에서 추출한다.

    Returns
    -------
    dict[str, float]
        {종목코드: 매출액(원)}. 손익계산서(IS)에서 매출 관련
        account_id/account_nm에 매칭되는 값을 반환한다.
    """
    from dartlab.scan.io.parquet import scanFinanceParquets

    return scanFinanceParquets("IS", REVENUE_IDS, REVENUE_NMS)


def _opIncomeMap() -> dict[str, float]:
    """전종목 영업이익을 scan/finance parquet에서 추출한다.

    Returns
    -------
    dict[str, float]
        {종목코드: 영업이익(원)}. 손익계산서(IS)에서 영업이익 관련
        account_id/account_nm에 매칭되는 값을 반환한다.
    """
    from dartlab.scan.io.parquet import scanFinanceParquets

    return scanFinanceParquets("IS", OP_IDS, OP_NMS)


def scanLaborRatio() -> dict[str, float]:
    """총급여/매출 → {종목코드: 인건비율(%)}.

    인건비율이 높을수록 매출 중 인건비 비중이 크다.

    Returns
    -------
    dict[str, float]
        {종목코드: 인건비율(%)}. 0 < 인건비율 < 500 범위만 반환.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        하위 scan 호출 실패 시 전파.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanLaborRatio
    >>> lr = scanLaborRatio()
    >>> lr.get("005930")
    """
    payrollMap = scanTotalPayroll()
    revMap = _revenueMap()

    result: dict[str, float] = {}
    for code, payroll in payrollMap.items():
        rev = revMap.get(code)
        if rev and rev > 0:
            ratio = payroll / rev * 100
            if 0 < ratio < 500:
                result[code] = round(ratio, 1)
    return result


def scanValueAdded() -> dict[str, float]:
    """(영업이익+총급여)/직원수 → {종목코드: 1인당부가가치(억)}.

    부가가치 = 영업이익 + 인건비.  직원 1명이 만들어내는 가치.

    Returns
    -------
    dict[str, float]
        {종목코드: 1인당부가가치(억)}. 직원수 0 또는 영업이익 None 인 종목 제외.

    Capabilities:
        - 해당 report 카테고리 prebuild parquet → 종목별 인력/급여 단면 추출. 직원수 가중평균
          + 최적 분기 + 임계 검증으로 noise 제거.

    AIContext:
        ``scanWorkforce`` 의 sub-scanner. AI agent 가 인력 효율 / 급여 / 고액 보수 횡단 비교 시
        본 함수 dict 결과를 그대로 사용.

    Guide:
        - 임계 (예: 평균급여 > 100 만원, 직원수 > 0) 미달 row 는 skip — 잘못된 단위 / 분식 데이터
          방어.

    When:
        ``scanWorkforce`` 진행 단계 안에서. 단독 호출은 prototype.

    How:
        ``scanParquets`` lazy → ``findLatestYear`` 단면 → 종목별 group → ``pickBestQuarter``
        선택 → 값 검증 후 dict 적재.

    Requires:
        - 로컬 ``data/dart/scan/report/{apiType}.parquet`` (``buildReport`` 산출)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` — sub-scanner 통합 호출

    Raises
    ------
    polars.PolarsError
        하위 scan 호출 실패 시 전파.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanValueAdded
    >>> va = scanValueAdded()
    >>> va.get("005930")
    """
    payrollMap = scanTotalPayroll()
    opMap = _opIncomeMap()
    empMap = scanEmployee()

    result: dict[str, float] = {}
    for code, payroll in payrollMap.items():
        opIncome = opMap.get(code)
        empInfo = empMap.get(code)
        if opIncome is None or empInfo is None:
            continue
        headcount = empInfo.get("직원수", 0)
        if headcount and headcount > 0:
            valueAdded = (opIncome + payroll) / headcount / 1e8
            result[code] = round(valueAdded, 1)
    return result


def scanHighPay() -> dict[str, dict]:
    """전종목 5억 이상 개인별 보수 스캔 (오너 일가 추출 포착).

    topPay apiType (5억 이상 개인별 보수, 미등기 오너 포함) 에서 종목별 최신 연도 최고
    개인보수와 공시 인원을 뽑는다. 등기임원 한정 :func:`scanTopPay` (executivePayIndividual)
    를 보완해 미등기 오너의 실적 역행 보수 같은 거버넌스 신호를 포착한다.

    Returns
    -------
    dict[str, dict]
        {종목코드: {최고개인보수_억(억), 고액보수인원(명)}}. 공시 없는 종목 제외.

    Capabilities:
        - topPay report 프리빌드에서 종목별 최신연도 최고 mendng_totamt + 인원. scanWorkforce sub-scanner.

    AIContext:
        ``scanWorkforce`` 내부. 오너 보수 추출 / 보수배수(직원평균 대비) 스크리닝 source.

    Guide:
        - mendng_totamt 결측/0 row 제외. 억 단위 환산(1e8).

    When:
        ``scanWorkforce`` 진행 단계 안에서.

    How:
        report parquet 종목별 최신연도 group 후 최고 보수 + 인원 집계.

    Requires:
        - 로컬 ``data/dart/scan/report/topPay.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` (sub-scanner 통합)

    Raises
    ------
    polars.PolarsError
        topPay report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanHighPay
    >>> scanHighPay().get("005930", {}).get("최고개인보수_억")
    """
    raw = scanParquets("topPay", ["stockCode", "year", "nm", "ofcps", "mendng_totamt"])
    if raw.is_empty() or "mendng_totamt" not in raw.columns:
        return {}
    result: dict[str, dict] = {}
    for code, group in raw.group_by("stockCode"):
        codeVal = code[0]
        latest = latestDataRows(group, "mendng_totamt")
        if latest.is_empty():
            continue
        best = 0.0
        cnt = 0
        for row in latest.iter_rows(named=True):
            amt = parseNumStr(row.get("mendng_totamt"))
            if amt and amt > 0:
                cnt += 1
                best = max(best, amt)
        if cnt > 0:
            result[codeVal] = {"최고개인보수_억": round(best / 1e8, 1), "고액보수인원": float(cnt)}
    return result


def scanUnregExecPay() -> dict[str, float]:
    """전종목 미등기임원 1인평균 보수 스캔.

    unregisteredExecutivePay apiType 에서 종목별 최신 연도 미등기임원 1인평균 급여(jan_salary_am)
    를 뽑는다. 등기 이사회 밖에서 실질 지배하는 오너의 보수 노출 신호.

    Returns
    -------
    dict[str, float]
        {종목코드: 미등기임원평균보수_억(억)}. 공시 없는 종목 제외.

    Capabilities:
        - unregisteredExecutivePay 프리빌드에서 종목별 최신연도 1인평균 급여. scanWorkforce sub-scanner.

    AIContext:
        ``scanWorkforce`` 내부. 미등기 임원 보수 노출 스크리닝 source.

    Guide:
        - jan_salary_am 결측/0 제외. 억 단위 환산(1e8).

    When:
        ``scanWorkforce`` 진행 단계 안에서.

    How:
        report parquet 종목별 최신연도 group 후 최대 1인평균 급여 선택.

    Requires:
        - 로컬 ``data/dart/scan/report/unregisteredExecutivePay.parquet`` (``buildReport``)

    SeeAlso:
        - :func:`dartlab.scan.workforce.scanWorkforce` (sub-scanner 통합)

    Raises
    ------
    polars.PolarsError
        unregisteredExecutivePay report parquet 손상 시.

    Examples
    --------
    >>> from dartlab.scan.workforce.scanner import scanUnregExecPay
    >>> scanUnregExecPay().get("005930")
    """
    raw = scanParquets("unregisteredExecutivePay", ["stockCode", "year", "jan_salary_am"])
    if raw.is_empty() or "jan_salary_am" not in raw.columns:
        return {}
    result: dict[str, float] = {}
    for code, group in raw.group_by("stockCode"):
        codeVal = code[0]
        latest = latestDataRows(group, "jan_salary_am")
        if latest.is_empty():
            continue
        best: float | None = None
        for row in latest.iter_rows(named=True):
            val = parseNumStr(row.get("jan_salary_am"))
            if val and val > 0:
                best = val if best is None else max(best, val)
        if best is not None:
            result[codeVal] = round(best / 1e8, 2)
    return result
