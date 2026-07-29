"""scan date, quarter, and fiscal calendar helpers."""

from __future__ import annotations

import polars as pl

# 어떤 해가 "다 찬 해" 인지 가르는 상대 기준. 가장 두꺼운 해 대비 이 비율에 못 미치면
# 아직 보고서가 덜 들어온 해로 본다. 절대 하한(minCount) 만으로는 진행 중인 해를 못 거른다.
_YEAR_COMPLETENESS = 0.8


def findLatestYear(raw: pl.DataFrame, checkCol: str, minCount: int = 500) -> str | None:
    """checkCol 에 유효 데이터가 충분히 찬 가장 최근 연도 반환.

    "충분히" 는 두 조건을 함께 본다. 절대 하한 ``minCount`` 이상이고, 동시에 가장 두꺼운
    해의 80 % 이상이어야 한다. 절대 하한만 보면 아직 진행 중인 해가 이미 끝난 해를 이긴다.
    실측 예로 employee 의 ``jan_salary_am`` 은 2025 년에 2,655 종목인데 2026 년은 1 분기
    보고서뿐이라 1,674 종목이다. 둘 다 500 을 넘어서 옛 규칙은 2026 을 골랐고, 그 해에 아직
    보고서를 안 낸 약 1,000 종목이 단면에서 통째로 빠졌다. 빠진 자리는 값이 없는 것이 아니라
    아예 행이 없어서, 소비자 쪽에서는 "그 회사는 원래 자료가 없다" 와 구분되지 않았다.

    Parameters:
        raw: year 컬럼을 포함한 전종목 데이터.
        checkCol: 유효성 검사 대상 컬럼명.
        minCount: 해당 연도에 필요한 최소 유효 행 수 (절대 하한).

    Returns:
        가장 최근 유효 연도 문자열. 없으면 None.

    Raises:
        KeyError: ``raw`` 에 ``"year"`` 컬럼 또는 ``checkCol`` 컬럼이 없을 때.

    Examples:
        >>> findLatestYear(rawDf, "매출액", minCount=500)
        "2024"

    Guide:
        최신 연도 단면을 만들 때 데이터가 거의 없는 조기 제출 연도를 건너뛴다.

    Capabilities:
        연도별 non-null/non-empty count 계산 후, 절대 하한과 상대 완성도(가장 두꺼운 해의
        80 %) 를 함께 넘는 첫 최신 연도 선택.

    AIContext:
        scan axis 가 횡단 비교용 최신 연도 단면을 고를 때 사용하는 기준.

    When:
        governance/workforce/capital 등 연 단위 단면 분석 직전.

    How:
        연도별 유효 행 카운트 → 최대값 대비 완성도 하한 계산 → years_desc 순회.

    Requires:
        ``raw["year"]`` 컬럼과 ``checkCol`` 컬럼.

    SeeAlso:
        ``pickBestQuarter`` · ``filterLatestPerStock``.
    """
    years_desc = sorted(raw["year"].unique().to_list(), reverse=True)
    # 단면의 넓이는 행수가 아니라 종목수다. 한 종목이 성별·구분별로 여러 행을 내므로 행수로 세면
    # 종목이 더 많은 해가 도리어 얇아 보인다 (employee 실측: 2025 년이 2024 년보다 종목은 많고
    # 행은 적다). stockCode 가 없는 입력만 행수로 물러선다.
    hasCode = "stockCode" in raw.columns
    counts: dict[str, int] = {}
    for y in years_desc:
        valid = raw.filter(
            (pl.col("year") == y)
            & pl.col(checkCol).is_not_null()
            & (pl.col(checkCol) != "-")
            & (pl.col(checkCol) != "")
        )
        counts[y] = valid["stockCode"].n_unique() if hasCode else valid.height
    if not counts:
        return None

    # 절대 하한만 보면 진행 중인 해가 끝난 해를 이긴다. 실측 예: employee 의 jan_salary_am 은
    # 2025 년 2,655 종목인데 2026 년은 1 분기 보고서뿐이라 1,674 종목이다. 둘 다 500 을 넘으므로
    # 옛 규칙은 2026 을 골랐고, 그 해에 아직 안 낸 약 1,000 종목이 단면에서 통째로 빠졌다.
    # 그래서 상대 기준을 함께 본다. 가장 두꺼운 해의 일정 비율에 못 미치면 아직 덜 찬 해로 본다.
    fullest = max(counts.values())
    floor = max(minCount, int(fullest * _YEAR_COMPLETENESS))
    for y in years_desc:
        if counts[y] >= floor:
            return y
    return None


QUARTER_ORDER = {"2분기": 1, "4분기": 2, "3분기": 3, "1분기": 4}


def pickBestQuarter(df: pl.DataFrame) -> pl.DataFrame:
    """가장 선호하는 분기만 필터 (Q2 > Q4 > Q3 > Q1).

    Parameters:
        df: quarter 컬럼을 포함한 전종목 데이터.

    Returns:
        가장 선호하는 분기 1개만 남긴 DataFrame.

    Raises:
        KeyError: ``df`` 에 ``"quarter"`` 컬럼이 없을 때.

    Examples:
        >>> pickBestQuarter(df)["quarter"].unique().to_list()
        ["2분기"]

    Guide:
        분기 혼합 noise 없이 단면 비교를 만들 때 사용한다.

    Capabilities:
        ``QUARTER_ORDER`` 우선순위로 단일 분기 선택.

    AIContext:
        scan 비재무 axis 가 종목별 단일 분기 단면을 만들 때 사용.

    When:
        분기별 raw report를 횡단 스냅샷으로 축약할 때.

    How:
        unique quarter 정렬 후 첫 분기로 filter.

    Requires:
        ``df["quarter"]`` 컬럼.

    SeeAlso:
        ``findLatestYear`` · ``filterLatestPerStock``.
    """
    quarters = df["quarter"].unique().to_list()
    best = sorted(quarters, key=lambda q: QUARTER_ORDER.get(q, 99))
    return df.filter(pl.col("quarter") == best[0]) if best else df


def parseDateYear(s) -> int | None:
    """날짜 문자열에서 연도 추출.

    Parameters:
        s: 날짜 문자열 (예: ``"2021.06.15"``).

    Returns:
        연도. 파싱 불가면 None.

    Raises:
        없음 — ValueError 는 내부에서 흡수해 None 반환.

    Examples:
        >>> parseDateYear("2021.06.15")
        2021

    Guide:
        raw report row 의 date 컬럼을 연도 단위 비교에 쓰기 위한 helper.

    Capabilities:
        ``.``/``-`` separator 날짜 문자열에서 첫 4자를 연도로 파싱.

    AIContext:
        scan 모듈이 공시일/변동일 계열을 연도 단면으로 정규화할 때 사용.

    When:
        raw report 날짜 문자열을 연도 정수로 변환할 때.

    How:
        문자열 정리 후 separator split, 1990~2030 범위 검사.

    Requires:
        표준 문자열 값.

    SeeAlso:
        ``findLatestYear``.
    """
    if s is None:
        return None
    s = str(s).strip()
    if s in ("", "-"):
        return None
    for sep in (".", "-"):
        if sep in s:
            parts = s.split(sep)
            if parts:
                try:
                    y = int(parts[0])
                    if 1990 <= y <= 2030:
                        return y
                except ValueError:
                    pass
    return None


def filterLatestPerStock(target: pl.DataFrame, scCol: str = "stockCode", yearCol: str = "bsns_year") -> pl.DataFrame:
    """종목별 최신 ``bsns_year`` 행만 남긴다.

    Parameters:
        target: scan 대상 DataFrame.
        scCol: 종목코드 컬럼명.
        yearCol: 사업년도 컬럼명.

    Returns:
        각 종목의 자기 최신 연도 행만 남긴 DataFrame.

    Raises:
        없음 — 누락 컬럼 시 입력 그대로 반환.

    Examples:
        >>> latest = filterLatestPerStock(df)
        >>> latest.group_by("stockCode").len()["len"].max()
        1

    Guide:
        글로벌 최신 연도 cut 으로 조기 제출 소수 종목만 남는 회귀를 차단한다.

    Capabilities:
        종목별 group_by max year 후 join/filter/drop.

    AIContext:
        scan financial / governance 등 모든 axis 의 최신 단면 일관성 보장.

    When:
        axis 의 횡단 단면 추출 직전.

    How:
        ``group_by(scCol).agg(max yearCol)`` → join → filter → drop.

    Requires:
        ``scCol`` · ``yearCol`` 컬럼.

    SeeAlso:
        ``findLatestYear`` · ``pickBestQuarter``.
    """
    if target.is_empty() or scCol not in target.columns or yearCol not in target.columns:
        return target
    latest = target.group_by(scCol).agg(pl.col(yearCol).max().alias("_maxYear"))
    return target.join(latest, on=scCol).filter(pl.col(yearCol) == pl.col("_maxYear")).drop("_maxYear")


def filterLatestPerStockLazy(
    target: pl.LazyFrame,
    scCol: str = "stockCode",
    yearCol: str = "bsns_year",
) -> pl.LazyFrame:
    """LazyFrame에서 회사별 최신 연도 필터를 수집 전에 적용한다."""

    columns = set(target.collect_schema().names())
    if scCol not in columns or yearCol not in columns:
        return target
    latest = target.group_by(scCol).agg(pl.col(yearCol).max().alias("_maxYear"))
    return target.join(latest, on=scCol).filter(pl.col(yearCol) == pl.col("_maxYear")).drop("_maxYear")


_FINANCE_PERIOD_RANK = {
    "Q1": 1,
    "1분기": 1,
    "Q2": 2,
    "2분기": 2,
    "Q3": 3,
    "3분기": 3,
    "Q4": 4,
    "4분기": 4,
    "annual": 4,
    "연간": 4,
    "사업보고서": 4,
}


def filterLatestPeriodPerStock(
    target: pl.DataFrame,
    scCol: str = "stockCode",
    yearCol: str = "bsns_year",
    periodCol: str = "reprt_nm",
) -> pl.DataFrame:
    """종목별 최신 연도 안에서 가장 늦은 재무 기간의 행만 남긴다.

    같은 사업연도에 Q1부터 Q4까지 함께 있는 합본에서 행 순서에 따라 서로 다른
    계정값을 고르는 문제를 막는다. 기간 컬럼이 없으면 연도 선택만 적용한다.

    Args:
        target: scan 대상 재무 DataFrame.
        scCol: 종목코드 컬럼명.
        yearCol: 사업연도 컬럼명.
        periodCol: 분기 또는 연간 보고기간 컬럼명.

    Returns:
        회사별 최신 연도와 그 연도의 가장 늦은 기간에 속한 모든 계정 행.
    """

    latest = filterLatestPerStock(target, scCol, yearCol)
    if latest.is_empty() or periodCol not in latest.columns:
        return latest
    ranked = latest.with_columns(
        pl.col(periodCol)
        .cast(pl.Utf8)
        .replace_strict(_FINANCE_PERIOD_RANK, default=0, return_dtype=pl.Int8)
        .alias("_periodRank")
    )
    best = ranked.group_by(scCol).agg(pl.col("_periodRank").max().alias("_bestPeriodRank"))
    return (
        ranked.join(best, on=scCol)
        .filter(pl.col("_periodRank") == pl.col("_bestPeriodRank"))
        .drop("_periodRank", "_bestPeriodRank")
    )


def filterLatestPeriodPerStockLazy(
    target: pl.LazyFrame,
    scCol: str = "stockCode",
    yearCol: str = "bsns_year",
    periodCol: str = "reprt_nm",
) -> pl.LazyFrame:
    """회사별 최신 연도와 기간을 LazyFrame 수집 전에 결정한다."""

    latest = filterLatestPerStockLazy(target, scCol, yearCol)
    columns = set(latest.collect_schema().names())
    if periodCol not in columns:
        return latest
    ranked = latest.with_columns(
        pl.col(periodCol)
        .cast(pl.Utf8)
        .replace_strict(_FINANCE_PERIOD_RANK, default=0, return_dtype=pl.Int8)
        .alias("_periodRank")
    )
    best = ranked.group_by(scCol).agg(pl.col("_periodRank").max().alias("_bestPeriodRank"))
    return (
        ranked.join(best, on=scCol)
        .filter(pl.col("_periodRank") == pl.col("_bestPeriodRank"))
        .drop("_periodRank", "_bestPeriodRank")
    )


def _calendarizeWithFmMap(df: pl.DataFrame) -> pl.DataFrame:
    """raw 합본 DataFrame 에 결산월 SSOT 기반 캘린더 환원 적용.

    Parameters:
        df: ``stockCode`` · ``bsns_year`` · ``reprt_nm`` 컬럼을 가진 raw 합본.

    Returns:
        ``bsns_year`` · ``reprt_nm`` 이 캘린더 기준으로 환원된 DataFrame.

    Raises:
        없음 — 결산월 map 이 없으면 입력을 그대로 반환한다.

    Examples:
        >>> out = _calendarizeWithFmMap(df)

    Guide:
        raw glob fallback path 가 prebuild ``finance.parquet`` 과 같은 period 스키마를 갖도록 보장.

    Capabilities:
        결산월 map join 후 사업연도/보고서명을 캘린더 분기로 벡터 변환.

    AIContext:
        비12월 결산 회사가 raw fallback 에서 다른 연도/분기로 비교되는 오류를 방지한다.

    When:
        prebuild finance parquet 이 없어서 raw finance glob 을 DuckDB 로 읽은 뒤.

    How:
        ``_fiscalMonthMap`` + ``_FISCAL_Q_MAP`` 기반 polars expression 적용.

    Requires:
        ``dartlab.scan.builders.kr.fiscal`` 의 결산월 SSOT.

    SeeAlso:
        ``_loadRawFinanceViaDuckDb``.
    """
    from dartlab.scan.builders.kr.fiscal import _FISCAL_Q_MAP, _fiscalMonthMap

    fmMap = _fiscalMonthMap()
    if not fmMap:
        return df

    fmDf = pl.DataFrame(
        {"stockCode": list(fmMap.keys()), "_fm": list(fmMap.values())},
        schema={"stockCode": pl.Utf8, "_fm": pl.Int32},
    )
    df = df.join(fmDf, on="stockCode", how="left").with_columns(pl.col("_fm").fill_null(12))

    bsnsInt = pl.col("bsns_year").cast(pl.Int32, strict=False)
    fq = pl.col("reprt_nm").replace_strict(_FISCAL_Q_MAP, default=None, return_dtype=pl.Int32)
    endMonth = ((pl.col("_fm") + fq * 3 - 1) % 12) + 1
    calQ = ((endMonth - 1) // 3) + 1
    calYear = pl.when(endMonth > pl.col("_fm")).then(bsnsInt - 1).otherwise(bsnsInt)
    newBsns = (
        pl.when(fq.is_not_null() & bsnsInt.is_not_null()).then(calYear.cast(pl.Utf8)).otherwise(pl.col("bsns_year"))
    )
    newRept = (
        pl.when(fq.is_not_null() & bsnsInt.is_not_null())
        .then(calQ.cast(pl.Utf8) + pl.lit("분기"))
        .otherwise(pl.col("reprt_nm"))
    )
    return df.with_columns(newBsns.alias("bsns_year"), newRept.alias("reprt_nm")).drop("_fm")
