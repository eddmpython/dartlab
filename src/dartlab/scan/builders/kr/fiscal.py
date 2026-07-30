"""KR scan builder fiscal-month and calendarization helpers."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import polars as pl

from dartlab.scan.builders.kr.common import financeDir
from dartlab.scan.builders.kr.corpProfile import _loadFiscalMonthMap


def _fiscalMonthMap() -> dict[str, int]:
    """종목코드 → 결산월(int) SSOT 매핑 — 전종목 cover.

    Parameters:
        없음.

    Returns:
        {종목코드: 결산월 1-12}. 데이터가 없으면 빈 dict.

    Raises:
        없음 — listing/raw finance 접근 실패는 빈 보강으로 흡수한다.

    Examples:
        >>> fm = _fiscalMonthMap()
        >>> fm.get("005930", 12)
        12

    Guide:
        DART corpProfile, KIND listing, raw finance 사업보고서 접수일 순서로 결산월을 보강한다.

    Capabilities:
        12월 결산도 명시 포함해 calendarization caller 가 identity 처리할 수 있게 한다.

    AIContext:
        finance prebuild 와 raw fallback 의 사업연도/분기 비교 기준을 달력 기준으로 통일한다.

    When:
        buildFinance 또는 raw finance fallback 이 결산월 환원을 수행할 때.

    How:
        corp profile map → listing 결산월 → raw annual filing rcept_no 추정 → fallback 12.

    Requires:
        선택적으로 ``scan/corpProfile.parquet``, KIND listing, raw finance parquet.

    SeeAlso:
        ``_calendarizeFiscalColumns`` · ``_calendarizeWithFmMap``.
    """
    result: dict[str, int] = {}
    result.update(_loadCorpProfileMap())

    try:
        from dartlab.gather.krx.listing import getKindList

        li = getKindList()
        if li is not None and not li.is_empty() and "결산월" in li.columns and "종목코드" in li.columns:
            for code, monthStr in li.select(["종목코드", "결산월"]).iter_rows():
                if code in result or not isinstance(monthStr, str):
                    continue
                try:
                    month = int(monthStr.replace("월", ""))
                except (ValueError, AttributeError):
                    continue
                if 1 <= month <= 12:
                    result[code] = month
    except (ImportError, FileNotFoundError, OSError):
        pass

    finDir = financeDir()
    if finDir.exists():
        for pf in finDir.glob("*.parquet"):
            code = pf.stem
            if code in result:
                continue
            estimated = _estimateFiscalMonthFromAnnualFiling(pf)
            result[code] = estimated if estimated is not None else 12

    return result


def _loadCorpProfileMap() -> dict[str, int]:
    """corpProfile.parquet → stockCode → acc_mt 매핑.

    Parameters:
        없음.

    Returns:
        {stockCode: 결산월 1-12}. 파일 없거나 파싱 실패 시 빈 dict.

    Raises:
        없음 — parquet 읽기 실패는 빈 dict 로 흡수한다.

    Examples:
        >>> _loadCorpProfileMap()
        {}

    Guide:
        DART OpenAPI ``companyInfo()`` 의 ``acc_mt`` 를 prefetch 한 권위 source.

    Capabilities:
        ``acc_mt`` 의 ``"12월"``/``"12"`` 변형을 월 정수로 정규화한다.

    AIContext:
        비12월 결산 회사의 캘린더 환원 정확도를 높이는 1순위 소스.

    When:
        ``_fiscalMonthMap`` 생성 첫 단계.

    How:
        ``scan/corpProfile.parquet`` 의 stockCode/acc_mt 컬럼만 streaming collect.

    Requires:
        선택적 ``data/dart/scan/corpProfile.parquet``.

    SeeAlso:
        ``.github/scripts/meta/buildCorpProfile.py``.
    """
    return _loadFiscalMonthMap()


def _estimateFiscalMonthFromAnnualFiling(pf: Path) -> int | None:
    """raw finance parquet → 사업보고서 접수일 기반 결산월 추정.

    Parameters:
        pf: raw finance parquet 경로.

    Returns:
        추정 결산월 1-12. 사업보고서 row 없거나 파싱 실패 시 None.

    Raises:
        없음 — parquet/schema 읽기 실패는 None 으로 흡수한다.

    Examples:
        >>> _estimateFiscalMonthFromAnnualFiling(Path("005930.parquet"))

    Guide:
        사업보고서 접수월 - 3개월을 결산월로 보고 여러 접수일의 최빈값을 채택한다.

    Capabilities:
        listing/corpProfile 누락 종목의 결산월을 raw finance 에서 보강한다.

    AIContext:
        비12월 결산 환원 누락으로 미래 bsns_year 가 생기는 회귀를 줄인다.

    When:
        ``_fiscalMonthMap`` 이 raw finance 파일을 순회할 때.

    How:
        ``reprt_code == "11011"`` 의 ``rcept_no`` 첫 8자리에서 접수월을 추출한다.

    Requires:
        raw finance parquet 에 ``reprt_code`` · ``rcept_no`` 컬럼.

    SeeAlso:
        ``_fiscalMonthMap``.
    """
    try:
        lz = pl.scan_parquet(str(pf))
        schemaNames = lz.collect_schema().names()
        if "reprt_code" not in schemaNames or "rcept_no" not in schemaNames:
            return None
        annual = lz.filter(pl.col("reprt_code") == "11011").select("rcept_no").unique().collect(engine="streaming")
    except (pl.exceptions.PolarsError, OSError):
        return None

    if annual.is_empty():
        return None

    months: list[int] = []
    for rcn in annual["rcept_no"].to_list():
        if not isinstance(rcn, str) or len(rcn) < 8:
            continue
        try:
            rmonth = int(rcn[4:6])
        except ValueError:
            continue
        if 1 <= rmonth <= 12:
            months.append(((rmonth - 3 - 1) % 12) + 1)

    if not months:
        return None
    return Counter(months).most_common(1)[0][0]


def _toCalendarPeriod(bsnsYear: int, fiscalQ: int, fiscalMonth: int) -> tuple[int, int]:
    """사업연도 분기 → 달력 (연도, 분기) 변환.

    Parameters:
        bsnsYear: 사업연도.
        fiscalQ: 사업연도 분기 1~4.
        fiscalMonth: 결산월 1~12.

    Returns:
        ``(calYear, calQ)``.

    Raises:
        없음.

    Examples:
        >>> _toCalendarPeriod(2026, 1, 3)
        (2025, 2)

    Guide:
        비12월 결산 회사의 사업연도 분기를 달력 분기로 환원한다.

    Capabilities:
        모든 결산월 × 4분기 조합에 대한 순수 수학 변환.

    AIContext:
        횡단 finance scan 에서 서로 다른 결산월 회사를 같은 달력 기간으로 비교하게 한다.

    When:
        테스트/문서 또는 벡터 변환 검증 기준이 필요할 때.

    How:
        fiscal month 에 fiscal quarter end offset 을 더해 endMonth 를 구한다.

    Requires:
        1~12 결산월과 1~4 fiscalQ.

    SeeAlso:
        ``_calendarizeFiscalColumns``.
    """
    endMonth = ((fiscalMonth + fiscalQ * 3 - 1) % 12) + 1
    calQ = ((endMonth - 1) // 3) + 1
    calYear = bsnsYear - 1 if endMonth > fiscalMonth else bsnsYear
    return calYear, calQ


_FISCAL_Q_MAP = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}


def _calendarizeFiscalColumns(df: pl.DataFrame, fiscalMonth: int) -> pl.DataFrame:
    """``bsns_year`` / ``reprt_nm`` 을 캘린더 기준으로 환원.

    Parameters:
        df: ``bsns_year`` · ``reprt_nm`` 컬럼을 가진 raw finance DataFrame.
        fiscalMonth: 결산월 1~12.

    Returns:
        period 컬럼이 캘린더 기준으로 환원된 DataFrame.

    Raises:
        없음 — 변환 불가능한 row 는 원본 값을 보존한다.

    Examples:
        >>> _calendarizeFiscalColumns(df, 12)

    Guide:
        ``_toCalendarPeriod`` 와 같은 수학을 polars expression 으로 적용한다.

    Capabilities:
        12월 결산 identity, 비12월 결산 연도/분기 shift, non-quarter row 보존.

    AIContext:
        finance parquet prebuild 가 달력 기간 기준으로 scan/analysis 에 제공되게 한다.

    When:
        ``buildFinance`` 가 종목별 raw finance 를 합본으로 쓰기 직전.

    How:
        ``reprt_nm`` → fiscalQ map, endMonth/calQ/calYear expression 계산.

    Requires:
        ``bsns_year`` · ``reprt_nm`` 컬럼.

    SeeAlso:
        ``_fiscalMonthMap``.
    """
    bsnsInt = pl.col("bsns_year").cast(pl.Int32, strict=False)
    fq = pl.col("reprt_nm").replace_strict(_FISCAL_Q_MAP, default=None, return_dtype=pl.Int32)
    endMonth = ((fiscalMonth + fq * 3 - 1) % 12) + 1
    calQ = ((endMonth - 1) // 3) + 1
    calYear = pl.when(endMonth > fiscalMonth).then(bsnsInt - 1).otherwise(bsnsInt)
    newBsns = (
        pl.when(fq.is_not_null() & bsnsInt.is_not_null()).then(calYear.cast(pl.Utf8)).otherwise(pl.col("bsns_year"))
    )
    newRept = (
        pl.when(fq.is_not_null() & bsnsInt.is_not_null())
        .then(calQ.cast(pl.Utf8) + pl.lit("분기"))
        .otherwise(pl.col("reprt_nm"))
    )
    return df.with_columns(newBsns.alias("bsns_year"), newRept.alias("reprt_nm"))
