"""Report parquet에서 apiType별 DataFrame 추출 + 정제."""

from __future__ import annotations

import polars as pl

from dartlab.core.polarsUtil import isEmptyDf
from dartlab.providers.dart.report.types import (
    API_TYPE_LABELS,
    KEEP_META_COLS,
    META_DROP_COLS,
    PREFERRED_QUARTER,
    QUARTER_MAP,
    STR_OVERRIDE_COLS,
    ReportResult,
)


def extractRaw(
    stockCode: str,
    apiType: str,
    *,
    baseDf: pl.DataFrame | None = None,
) -> pl.DataFrame | None:
    """report parquet 에서 apiType 으로 필터 → null 컬럼 제거 → 정렬 (raw 정제 1 차).

    Capabilities:
        - report category parquet (gather 가 사전 수집) 을 load 하고 ``apiType`` 으로 필터.
        - 전부 null 인 컬럼 + ``META_DROP_COLS`` 자동 제거, ``KEEP_META_COLS`` 보존.
        - ``year`` 컬럼은 ``r"(\\d{4})"`` 정규식으로 4 자리 추출 후 Int32 캐스팅.
        - ``quarter`` 컬럼은 ``QUARTER_MAP`` ("1분기"→1) 으로 변환해 ``quarterNum`` 신설.
        - 결과는 ``["year", "quarterNum"]`` 오름차순 정렬, 숫자 캐스팅은 미수행 (extractClean 이 담당).

    Args:
        stockCode: KR 종목코드 6 자리 (예 "005930"). gather 의 dataLoader 가 이 키로 parquet 경로 매핑.
        apiType: ``API_TYPES`` 28 종 중 1 (예 "dividend"/"employee"/"majorHolder"/"executive"/"auditOpinion").
        baseDf: caller 가 사전 load 한 report parquet (옵션). 동일 stockCode 의 여러 apiType 을
            추출할 때 1 회 load → 재사용 → I/O 절약. None 이면 dataLoader 가 매번 load.

    Returns:
        pl.DataFrame — 정제된 raw 데이터. 데이터 없음 (parquet 결락/필터 결과 empty/year null
        전부) → None. column 은 apiType 마다 상이 (DART API 원본 키), 공통 보존은
        ``year`` (Int32) · ``quarterNum`` (Int32) · ``stockCode`` · ``apiType`` · ``stlm_dt``.

    Example:
        >>> from dartlab.providers.dart.report.extract import extractRaw
        >>> df = extractRaw("005930", "dividend")
        >>> df is None or df.height >= 0
        True

    Guide:
        - "삼성전자 배당 raw 데이터" → ``extractRaw("005930", "dividend")``
        - "여러 apiType 추출 효율화" → ``baseDf = loadData("005930", category="report")`` 1 회 후
          ``for t in ["dividend", "employee", ...]: extractRaw("005930", t, baseDf=baseDf)``
        - 정제·캐스팅 필요 시 ``extractClean`` 또는 ``extractAnnual`` 사용.

    SeeAlso:
        - ``extractClean`` — extractRaw 결과에 ``_castNumeric`` 적용 (Float64 변환).
        - ``extractAnnual`` — 연 1 회 분기 기준 필터 (대표분기 자동/수동).
        - ``extractResult`` — ``ReportResult`` dataclass 래핑.
        - ``dartlab.core.dataLoader.loadData`` — report parquet 의 실제 로더.
        - ``dartlab.providers.dart.report.types.API_TYPES`` — 지원 apiType 목록.

    Requires:
        - polars — DataFrame 입출력 + 정규식 추출.
        - dartlab.core.dataLoader — report category parquet 로딩 (lazy import).
        - dartlab.core.polarsUtil.isEmptyDf — None/empty 통합 검사.

    AIContext:
        Ask Workbench 의 정기보고서 (배당/직원/임원/주주/감사) 질문 시 호출되는 entry. raw
        column 이름이 DART 원본 (예 "thstrm"/"frmtrm"/"se") 이라 사람에게 직접 보여주기엔
        부적합 — caller 가 pivot/result 함수로 가공해서 보여줘야 한다. None 반환 = 데이터 없음
        명시, caller 는 "해당 회사 {apiType} 정보 미수집" fallback.

    LLM Specifications:
        AntiPatterns:
            - apiType 이 ``API_TYPES`` 28 종 밖 (예 "foobar") → 필터 결과 empty → None.
              caller 가 API_TYPES 검증할 의무 없음 (silent skip).
            - parquet 자체 결락 (loadData → None) → 본 함수 None. caller 는 gather 누락
              가능성 의심.
            - year 추출 실패 (4 자리 패턴 미매칭) → 해당 row 자동 drop, 일부만 남을 수 있음.
        OutputSchema:
            - row: apiType × stockCode × year × quarter 조합당 1 (또는 sub-key 별 N — apiType 마다 상이).
            - column: apiType 마다 가변. 공통 보존은 KEEP_META_COLS 5 + ``quarterNum`` 1.
            - 정렬: ``year`` 오름차순 → ``quarterNum`` 오름차순.
        Prerequisites:
            - gather report category 가 stockCode 에 대해 1 회 이상 수집됨.
            - parquet 경로 = ``dataLoader`` 의 report 매핑 (caller 가 직접 path 지정 X).
        Freshness:
            - parquet 데이터 = gather 수집 시점 기준. fresh 책임은 gather (운영자).
            - 본 함수 자체는 외부 API 무호출 → 캐시·rate limit 무관.
        Dataflow:
            - gather (report 수집) → parquet → ``loadData`` → 본 함수 → ``extractClean``/
              ``extractAnnual``/``extractResult``/``pivot*`` 함수들.
        TargetMarkets:
            - KR (DART). EDGAR/EDINET 은 별도 finance/disclosure 파이프라인 — 본 함수 미지원.

    Raises:
        없음.
    """
    from dartlab.core.dataLoader import loadData

    df = baseDf if baseDf is not None else loadData(stockCode, category="report")
    if isEmptyDf(df):
        return None

    sub = df.filter(pl.col("apiType") == apiType)
    if sub.is_empty():
        return None

    dropCols = []
    for c in sub.columns:
        if c in META_DROP_COLS:
            dropCols.append(c)
            continue
        if c in KEEP_META_COLS:
            continue
        if sub[c].null_count() == sub.height:
            dropCols.append(c)

    sub = sub.drop(dropCols)

    sub = sub.with_columns(
        pl.col("year").cast(pl.Utf8).str.extract(r"(\d{4})", 1).cast(pl.Int32, strict=False).alias("year")
    )
    # 일부 apiType 은 사업연도 자리에 "제57기 1분기" 처럼 기수 라벨을 담는다. 네 자리 숫자가
    # 없으니 연도가 null 이 되고 바로 아래 필터가 그 apiType 을 통째로 버렸다. 감사의견이
    # 그래서 93 행을 갖고도 0 행으로 나왔다. 결산일이 그 보고서 기간의 끝이라 연도를 준다.
    if "stlm_dt" in sub.columns:
        sub = sub.with_columns(
            pl.when(pl.col("year").is_null())
            .then(pl.col("stlm_dt").cast(pl.Utf8).str.extract(r"(\d{4})", 1).cast(pl.Int32, strict=False))
            .otherwise(pl.col("year"))
            .alias("year")
        )
    sub = sub.filter(pl.col("year").is_not_null())
    sub = sub.with_columns(pl.col("quarter").replace(QUARTER_MAP).cast(pl.Int32).alias("quarterNum"))

    if "stlm_dt" in sub.columns:
        sub = sub.filter(pl.col("stlm_dt").is_not_null())
    sub = sub.sort(["year", "quarterNum"])

    return sub


def extractClean(
    stockCode: str,
    apiType: str,
    *,
    baseDf: pl.DataFrame | None = None,
) -> pl.DataFrame | None:
    """extractRaw + ``_castNumeric`` (Utf8 → Float64 변환) 적용한 정제 단계.

    Capabilities:
        - ``extractRaw`` 결과를 받아 숫자형 컬럼 후보 (Utf8) 를 Float64 캐스팅.
        - ``STR_OVERRIDE_COLS`` 의 apiType 별 set 은 변환 제외 (의도적 문자열 유지).
        - "," 제거, ``"-"``/``""`` → null, 변환 성공률 70% 이상이면 채택 (보수적).
        - ``KEEP_META_COLS`` + ``quarterNum`` + apiType override 는 캐스팅 skip.

    Args:
        stockCode: KR 종목코드 6 자리 (예 "005930").
        apiType: ``API_TYPES`` 28 종 중 1.
        baseDf: 사전 load 한 report parquet (옵션, 동일 stockCode 여러 apiType 처리 시 재사용).

    Returns:
        pl.DataFrame — 정제 + 숫자 캐스팅 적용된 데이터. extractRaw 결과 None → None.
        대다수 수치 컬럼 (배당금/직원수/지분율 등) 이 Float64 로 변환됨.

    Example:
        >>> from dartlab.providers.dart.report.extract import extractClean
        >>> df = extractClean("005930", "dividend")
        >>> df is None or df.height >= 0
        True

    Guide:
        - "배당금 합산이나 평균 계산 직전 raw 정제" → ``extractClean("005930", "dividend")``
        - "연 1 회 대표분기 기준 데이터" → ``extractAnnual`` 사용 (본 함수는 모든 분기 반환).
        - "표준화된 dataclass 결과" → ``extractResult`` 사용.

    SeeAlso:
        - ``extractRaw`` — 본 함수의 입력 단계 (캐스팅 전).
        - ``extractAnnual`` — extractClean → 연 1 회 대표분기 필터.
        - ``_castNumeric`` (모듈 private) — 실제 캐스팅 로직.
        - ``dartlab.providers.dart.report.types.STR_OVERRIDE_COLS`` — apiType 별 문자열 유지 규약.

    Requires:
        - polars — DataFrame 변환.
        - dartlab.providers.dart.report.extract.extractRaw — 본 함수의 입력 단계.
        - dartlab.providers.dart.report.types — STR_OVERRIDE_COLS / KEEP_META_COLS 의존.

    AIContext:
        Ask Workbench 가 "배당 추세"/"직원 수 증감" 같은 시계열 수치 비교 토픽 처리 시 호출.
        본 함수가 None 반환 = 해당 apiType 미수집. caller 는 raw column 이름이 한국 약어
        (예 "thstrm"="당기"/"frmtrm"="전기") 임을 인지하고 가공해서 답변해야 한다.

    LLM Specifications:
        AntiPatterns:
            - 70% threshold 미만 → 컬럼이 Utf8 로 남음. caller 는 dtype 검사 후 가공.
            - apiType 의 ``STR_OVERRIDE_COLS`` 정의 누락 → 의도치 않은 캐스팅 가능성. types 추가 시 검토.
            - extractRaw None → 본 함수 None (silent pass-through).
        OutputSchema:
            - row: extractRaw 와 동일 (캐스팅은 dtype 만 변경).
            - column: extractRaw 와 동일. 대다수 수치 컬럼 dtype = Float64 로 변경.
            - 정렬: ``year`` 오름차순 → ``quarterNum`` 오름차순 (extractRaw 보존).
        Prerequisites:
            - extractRaw 의 사전조건 (gather report 수집) 동일 적용.
        Freshness:
            - extractRaw 와 동일 (gather 의존). 본 함수 자체는 무상태 변환.
        Dataflow:
            - extractRaw → 본 함수 → extractAnnual / extractResult / pivot*.
        TargetMarkets:
            - KR (DART). 다른 provider 는 본 함수 무관 — finance/disclosure 별도 파이프.

    Raises:
        없음.
    """
    df = extractRaw(stockCode, apiType, baseDf=baseDf)
    if df is None:
        return None

    overrides = STR_OVERRIDE_COLS.get(apiType, set())
    return _castNumeric(df, overrides)


def extractAnnual(
    stockCode: str,
    apiType: str,
    quarterNum: int | None = None,
    *,
    baseDf: pl.DataFrame | None = None,
) -> pl.DataFrame | None:
    """연 1 회 대표분기 기준 시계열 추출 (apiType 별 PREFERRED_QUARTER 자동 적용).

    Capabilities:
        - ``extractClean`` 결과를 받아 ``quarterNum == quarterNum`` 으로 필터.
        - quarterNum 미지정 → ``PREFERRED_QUARTER`` 매핑 lookup (배당/감사=Q4 사업보고서,
          직원/임원/주주=Q2 반기보고서 기준 등).
        - Q2 결과 empty → Q4 fallback, Q4 empty → Q2 fallback (보수적 1 단 재시도).
        - 양쪽 모두 empty → None.

    Args:
        stockCode: KR 종목코드 6 자리.
        apiType: ``API_TYPES`` 28 종 중 1.
        quarterNum: 1~4 분기 번호. None 이면 ``PREFERRED_QUARTER`` 적용.
        baseDf: 사전 load 한 report parquet (옵션).

    Returns:
        pl.DataFrame — 연 1 회 (대표분기) 시계열. 사전조건 (extractClean) 결과 None 이나
        대표분기 + fallback 양쪽 empty → None.

    Example:
        >>> from dartlab.providers.dart.report.extract import extractAnnual
        >>> df = extractAnnual("005930", "dividend")  # 기본 Q4 사업보고서
        >>> df is None or df.height >= 0
        True

    Guide:
        - "배당 연간 시계열" → ``extractAnnual("005930", "dividend")`` (Q4 자동).
        - "직원수 매년 6월 기준" → ``extractAnnual("005930", "employee")`` (Q2 자동).
        - "특정 분기 강제" → ``quarterNum=3`` 명시.

    SeeAlso:
        - ``extractClean`` — 본 함수의 입력 단계 (분기 필터 전).
        - ``extractResult`` — 본 함수 결과를 ``ReportResult`` dataclass 로 래핑.
        - ``pivotDividend`` / ``pivotEmployee`` / ``pivotMajorHolder`` / ``pivotAudit`` —
          본 함수 결과를 토픽별 와이드 시계열로 변환.
        - ``PREFERRED_QUARTER`` (types) — apiType 별 기본 분기 매핑.

    Requires:
        - polars — 분기 필터.
        - dartlab.providers.dart.report.extract.extractClean — 본 함수의 입력.
        - dartlab.providers.dart.report.types.PREFERRED_QUARTER — 기본 분기 lookup.

    AIContext:
        "삼성전자 배당 추세" 류 질문에서 가장 빈번하게 호출되는 경로. caller (pivot 함수)
        가 이 결과를 받아 와이드 변환 후 사람에게 제시. None 반환 시 caller 는 "최근 보고서
        미수집" 으로 답변. 분기 fallback 로직 덕분에 Q2/Q4 혼재 데이터에 robust.

    LLM Specifications:
        AntiPatterns:
            - 대표분기 데이터만 있는 회사 (예 분기보고 면제) → fallback 으로도 빈 결과 가능 → None.
            - quarterNum=1 또는 3 명시 시 fallback 미동작 (의도적 — Q2/Q4 만 fallback pair).
        OutputSchema:
            - row: 1 stockCode × 1 apiType × N 년 = N rows (대표분기 1 개 per year).
            - column: extractClean 와 동일.
            - 정렬: ``year`` 오름차순 (extractClean 보존).
        Prerequisites:
            - extractClean 의 사전조건 동일.
            - apiType 이 ``PREFERRED_QUARTER`` 에 정의 안 됨 → default 2 (Q2) 적용.
        Freshness:
            - gather 수집 시점 의존. 본 함수 자체는 무상태.
        Dataflow:
            - extractRaw → extractClean → 본 함수 → extractResult / pivot*.
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    df = extractClean(stockCode, apiType, baseDf=baseDf)
    if df is None:
        return None

    if quarterNum is None:
        quarterNum = PREFERRED_QUARTER.get(apiType, 2)

    annual = df.filter(pl.col("quarterNum") == quarterNum)

    if annual.is_empty() and quarterNum == 2:
        annual = df.filter(pl.col("quarterNum") == 4)
    elif annual.is_empty() and quarterNum == 4:
        annual = df.filter(pl.col("quarterNum") == 2)

    if annual.is_empty():
        return None

    return annual


def extractResult(
    stockCode: str,
    apiType: str,
    quarterNum: int | None = None,
    *,
    baseDf: pl.DataFrame | None = None,
) -> ReportResult | None:
    """apiType 별 ``ReportResult`` dataclass 로 래핑한 표준화 결과.

    Capabilities:
        - ``extractAnnual`` 결과를 ``ReportResult`` (apiType + label 한국어 + df + years + nYears) 로 패키징.
        - label = ``API_TYPE_LABELS`` lookup ("dividend"→"배당" 등). 미정의 시 apiType 그대로.
        - years = df 의 ``year`` 컬럼 unique 오름차순 list[int].
        - extractAnnual None → 본 함수 None (silent pass).

    Args:
        stockCode: KR 종목코드 6 자리.
        apiType: ``API_TYPES`` 28 종 중 1.
        quarterNum: 기준 분기 (1~4) 또는 None (``PREFERRED_QUARTER`` 자동).
        baseDf: 사전 load 한 report parquet (옵션).

    Returns:
        ``ReportResult`` dataclass — ``apiType`` (str) · ``label`` (한국어 str) · ``df``
        (pl.DataFrame) · ``years`` (list[int]) · ``nYears`` (int). 데이터 없음 → None.

    Example:
        >>> from dartlab.providers.dart.report.extract import extractResult
        >>> r = extractResult("005930", "dividend")
        >>> r is None or r.nYears >= 0
        True

    Guide:
        - "여러 apiType 결과 일관 포맷으로 수집" → 본 함수 반복 호출 → dict[apiType, ReportResult].
        - "토픽별 와이드 시계열" → pivot 함수 사용 (본 함수보다 의미 컬럼 명시적).
        - "JSON 직렬화" → ``r.df.to_dicts() + {"apiType", "label", "years"}``.

    SeeAlso:
        - ``extractAnnual`` — 본 함수의 입력 단계.
        - ``ReportResult`` dataclass — 본 함수의 반환 타입.
        - ``API_TYPE_LABELS`` (types) — 한국어 라벨 매핑.
        - ``pivotDividend`` / ``pivotEmployee`` / ... — 토픽별 의미 시계열 (와이드).

    Requires:
        - polars — DataFrame.
        - dartlab.providers.dart.report.extract.extractAnnual — 본 함수의 입력.
        - dartlab.providers.dart.report.types — ``ReportResult`` + ``API_TYPE_LABELS``.

    AIContext:
        Workbench 가 "이 회사 정기보고서 어떤 항목이 있냐" 류 메타 질문 처리 시, 28 apiType
        에 대해 본 함수를 일괄 호출 후 ``nYears > 0`` 만 추려 카탈로그 제시. label 이 한국어
        라 사람에게 그대로 노출 가능. None apiType 은 미수집 표식.

    LLM Specifications:
        AntiPatterns:
            - 라벨 누락 (API_TYPE_LABELS 의 28 종 외 apiType) → label = apiType 원본. caller 가
              사람에게 표시 시 영문 라벨 노출됨.
            - df 가 empty 가 아니지만 ``year`` 컬럼 null 전부 → years=[], nYears=0. caller 는
              빈 시계열로 취급.
        OutputSchema:
            - row: 1 dataclass instance. ``df.height`` = N 년.
            - 필드: 5 종 (apiType/label/df/years/nYears).
        Prerequisites:
            - extractAnnual 의 사전조건 동일.
        Freshness:
            - gather 의존. 본 함수 무상태.
        Dataflow:
            - extractAnnual → 본 함수. pivot 함수와는 병렬 옵션 (caller 가 선택).
        TargetMarkets:
            - KR (DART) 한정.

    Raises:
        없음.
    """
    df = extractAnnual(stockCode, apiType, quarterNum, baseDf=baseDf)
    if df is None:
        return None

    years = sorted(df["year"].unique().to_list())

    return ReportResult(
        apiType=apiType,
        label=API_TYPE_LABELS.get(apiType, apiType),
        df=df,
        years=years,
        nYears=len(years),
    )


def _castNumeric(
    df: pl.DataFrame,
    strOverrides: set[str] | None = None,
) -> pl.DataFrame:
    """문자열 컬럼 중 숫자 변환 가능한 것을 Float64로 변환."""
    if strOverrides is None:
        strOverrides = set()

    skip = KEEP_META_COLS | {"quarterNum"} | strOverrides

    for c in df.columns:
        if c in skip:
            continue
        if df[c].dtype != pl.Utf8:
            continue

        stripped = df[c].str.strip_chars().str.replace_all(",", "")
        cleanedSeries = (
            stripped.to_frame("_v")
            .select(
                pl.when((pl.col("_v") == "-") | (pl.col("_v") == ""))
                .then(pl.lit(None))
                .otherwise(pl.col("_v"))
                .alias("_v")
            )
            .to_series()
        )

        numSeries = cleanedSeries.cast(pl.Float64, strict=False)
        nonNullOriginal = cleanedSeries.drop_nulls().len()
        nonNullConverted = numSeries.drop_nulls().len()

        if nonNullOriginal > 0 and nonNullConverted / nonNullOriginal >= 0.7:
            df = df.with_columns(numSeries.alias(c))

    return df
