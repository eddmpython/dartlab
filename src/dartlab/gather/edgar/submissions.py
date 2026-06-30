"""EDGAR submissions wrapper."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

import polars as pl

from dartlab.core.edgarClient import DEFAULT_BASE_URL, SUPPORTED_REGULAR_FORMS, EdgarClient  # noqa: F401  (re-export)


def getSubmissionsJson(cik: str, client: EdgarClient | None = None) -> dict[str, Any]:
    """CIK 로 SEC submissions API 를 호출하여 원본 JSON 을 반환.

    Args:
        cik: SEC CIK 번호.
        client: EdgarClient 인스턴스.

    Returns:
        submissions API 원본 JSON dict.

    Raises:
        EdgarApiError: API 호출 실패.

    Example:
        >>> getSubmissionsJson("0000320193")

    SeeAlso:
        - ``filingsFrame`` — submissions → DataFrame 변환.
        - ``SUPPORTED_REGULAR_FORMS`` — 10-K/10-Q/20-F/40-F.

    Requires:
        - dartlab
        - datetime
        - polars

    Capabilities:
        - SEC submissions API 위임 — 회사 별 정기보고서 + 수시공시 메타 + accession_no list.

    Guide:
        - "SEC 공시 목록 조회" → 본 모듈.

    AIContext:
        internal submissions wrapper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 전체 submissions 그대로 LLM 노출 → 토큰 폭증. form/since 필터.
        OutputSchema:
            - dict (raw JSON) 또는 pl.DataFrame (filings).
        Prerequisites:
            - 인터넷 + SEC EDGAR public API + CIK.
        Freshness:
            - SEC EDGAR 실시간 (분 단위).
        Dataflow:
            - CIK → EdgarClient → submissions API → JSON → 정규화.
        TargetMarkets:
            - US (SEC EDGAR) submissions.
    """
    api = client or EdgarClient()
    normalized = str(cik).zfill(10)
    return api.getJson(f"{DEFAULT_BASE_URL}/submissions/CIK{normalized}.json")


def mergeSubmissionFilings(
    submissions: dict[str, Any],
    *,
    sinceYear: int = 2009,
    client: EdgarClient | None = None,
) -> dict[str, list[Any]]:
    """recent filings 와 추가 파일들을 병합하여 전체 filing 목록을 구성.

    Args:
        submissions: ``getSubmissionsJson`` 결과 dict.
        sinceYear: 시작 연도.
        client: EdgarClient 인스턴스 (추가 페이지 fetch 용).

    Returns:
        병합된 filing column dict (``{form, filingDate, ...}``).

    Raises:
        EdgarApiError: 추가 페이지 fetch 실패.

    Example:
        >>> mergeSubmissionFilings(getSubmissionsJson("0000320193"), sinceYear=2024)

    SeeAlso:
        - ``filingsFrame`` — submissions → DataFrame 변환.
        - ``SUPPORTED_REGULAR_FORMS`` — 10-K/10-Q/20-F/40-F.

    Requires:
        - dartlab
        - datetime
        - polars

    Capabilities:
        - SEC submissions API 위임 — 회사 별 정기보고서 + 수시공시 메타 + accession_no list.

    Guide:
        - "SEC 공시 목록 조회" → 본 모듈.

    AIContext:
        internal submissions wrapper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 전체 submissions 그대로 LLM 노출 → 토큰 폭증. form/since 필터.
        OutputSchema:
            - dict (raw JSON) 또는 pl.DataFrame (filings).
        Prerequisites:
            - 인터넷 + SEC EDGAR public API + CIK.
        Freshness:
            - SEC EDGAR 실시간 (분 단위).
        Dataflow:
            - CIK → EdgarClient → submissions API → JSON → 정규화.
        TargetMarkets:
            - US (SEC EDGAR) submissions.
    """
    recent = submissions.get("filings", {}).get("recent", {})
    merged = {k: list(v) for k, v in recent.items()}
    api = client or EdgarClient()

    for fileInfo in submissions.get("filings", {}).get("files", []):
        filingTo = str(fileInfo.get("filingTo") or "")
        if filingTo and filingTo[:4].isdigit() and int(filingTo[:4]) < sinceYear:
            continue
        name = str(fileInfo.get("name") or "")
        if not name:
            continue
        extra = api.getJson(f"{DEFAULT_BASE_URL}/submissions/{name}")
        for key in merged:
            if key in extra:
                merged[key].extend(extra[key])
    return merged


def _coerceDateBound(value: str | date | datetime | None, *, end: bool) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-12-31" if end else f"{text}-01-01"
    if re.fullmatch(r"\d{4}-\d{2}", text):
        return f"{text}-31" if end else f"{text}-01"
    return text


def findRegularFilings(
    submissions: dict[str, Any],
    *,
    sinceYear: int = 2009,
    forms: list[str] | tuple[str, ...] | None = None,
    since: str | date | datetime | None = None,
    until: str | date | datetime | None = None,
    client: EdgarClient | None = None,
) -> list[dict[str, Any]]:
    """병합된 submissions → 정기보고서 (10-K/10-Q/20-F/40-F) 필터 — EDGAR 공시 검색 본진.

    SEC EDGAR submissions API 응답에서 정기보고서만 필터링 — KR provider 의
    ``searchNgram`` 과 동치 역할 (회사 공시 retrieval). 정기보고서만 ``SUPPORTED_REGULAR_FORMS``
    (10-K / 10-Q / 20-F / 40-F) 매칭. 수시공시 (8-K / DEF 14A) 는 별도 함수.

    필터 단계:
      1. ``mergeSubmissionFilings`` — recent + older paginated 병합 (필요 시 추가 페이지 fetch).
      2. ``SUPPORTED_REGULAR_FORMS`` 매칭 (10-K/10-Q/20-F/40-F).
      3. ``forms`` 사용자 명시 시 추가 set 필터 (예: ``["10-K"]`` 만).
      4. ``filingDate`` 연도 ≥ ``sinceYear`` (default 2009).
      5. ``since`` / ``until`` 일 단위 bound (``YYYYMMDD`` / date / datetime 자동 정규화).
      6. accession_no 별 ``filing_url`` 구성 (``sec.gov/Archives/edgar/data/{CIK}/{accNoDash}/{primaryDoc}``).
      7. ``filing_date`` ASC 정렬 → list.

    Args:
        submissions: ``getSubmissionsJson(cik)`` 결과 dict (raw SEC JSON).
        sinceYear: 시작 연도 (default 2009 — SEC XBRL 의무화 시점).
        forms: form 유형 필터 (예: ``["10-K"]`` / ``["10-Q", "20-F"]``). None 이면
            ``SUPPORTED_REGULAR_FORMS`` (10-K/10-Q/20-F/40-F) 전체.
        since: 시작일 (``"YYYY-MM-DD"`` / ``"YYYYMMDD"`` / date / datetime).
        until: 종료일 (동일 형식).
        client: ``EdgarClient`` 인스턴스 (``mergeSubmissionFilings`` 의 페이지 fetch 에 사용).

    Returns:
        list[dict] — filing dict 리스트 (filing_date ASC 정렬). 각 dict 키:

        - ``cik`` (str 10): CIK zero-padded.
        - ``form`` (str): ``"10-K"`` / ``"10-Q"`` / ``"20-F"`` / ``"40-F"``.
        - ``filing_date`` (str ``YYYY-MM-DD``): 제출일자.
        - ``report_date`` (str|None ``YYYY-MM-DD``): 보고 기준일.
        - ``acceptance_datetime`` (str|None): SEC 접수 datetime.
        - ``accession_no`` (str): ``YYYYMMDD-NN-NNNNNN`` SEC 접수번호.
        - ``primary_document`` (str|None): 메인 문서 파일명.
        - ``primary_doc_description`` (str|None).
        - ``filing_url`` (str): 메인 문서 URL.
        - ``filing_index_url`` (str): ``index.json`` URL (전체 attachment 목록).
        - ``year`` (str ``YYYY``).

    Raises:
        EdgarApiError: ``mergeSubmissionFilings`` 의 paginated fetch 실패 (HTTP 403/404/429).

    Example:
        >>> subs = getSubmissionsJson("0000320193")  # Apple
        >>> filings = findRegularFilings(subs, sinceYear=2024, forms=["10-K"])
        >>> filings[0]["filing_url"]
        'https://www.sec.gov/Archives/edgar/data/0000320193/...'

    SeeAlso:
        - ``getSubmissionsJson`` — 본 함수 input (raw SEC submissions JSON).
        - ``mergeSubmissionFilings`` — recent + older paginated 병합.
        - ``filingsFrame`` — 본 함수 결과 pl.DataFrame 변환.
        - ``SUPPORTED_REGULAR_FORMS`` — 4 form 정의.
        - ``_coerceDateBound`` — date/datetime 정규화 헬퍼.
        - ``providers.dart.search.ngramIndex.searchNgram`` — KR 공시 검색 동치.

    Requires:
        - datetime / date
        - dartlab.core.edgarClient (``EdgarClient``)
        - SEC EDGAR API ``data.sec.gov/submissions/CIK*.json``.

    Capabilities:
        - SEC 정기보고서 검색 — 회사 × form × 기간 3 축 필터.
        - paginated submissions 자동 병합 (``mergeSubmissionFilings``).
        - filing_url / index_url 자동 구성 — 후속 fetch 즉시 가능.
        - filing_date ASC 정렬 — 시계열 분석 입력 schema.

    Guide:
        - "Apple 최근 5 년 10-K" → ``findRegularFilings(subs, sinceYear=2020, forms=["10-K"])``.
        - "10-Q 만 분기별" → ``forms=["10-Q"]``.
        - 결과 ``accession_no`` 로 ``docs.fetch`` / ``sections`` 후속 호출.
        - 다종목 batch → ``filingsFrame`` 으로 pl.DataFrame 변환 후 횡단 비교.

    AIContext:
        Ask Workbench EDGAR filings core — LLM 이 US 회사 공시 retrieval 시 entry.
        결과 → ``c.panel`` / ``c.panel.search`` 후속 호출의 accession_no 공급.

    LLM Specifications:
        AntiPatterns:
            - SEC User-Agent header 미설정 → HTTP 403 (``EdgarClient`` 기본 처리, 환경변수 ``DARTLAB_USER_AGENT`` 권장).
            - 전체 submissions 그대로 LLM context 주입 X — 토큰 폭증. ``forms`` / ``since`` 필터 의무.
            - 본 함수 결과를 raw 로 분석 X — ``filingsFrame`` pl.DataFrame 변환 후 polars 처리.
            - 8-K (수시공시) / DEF 14A (위임장) 호출 시 본 함수 X — ``SUPPORTED_REGULAR_FORMS`` 외 form 은 별도.
            - paginated submissions 의 추가 fetch 실패 시 부분 결과 반환 X — EdgarApiError 전파.
            - ``filing_url`` 은 메인 문서만 — 첨부 (exhibit / xbrl) 는 ``filing_index_url`` 의 index.json 참조.
        OutputSchema:
            - list[dict] — 각 dict ``cik`` / ``form`` / ``filing_date`` / ``report_date``
              / ``acceptance_datetime`` / ``accession_no`` / ``primary_document``
              / ``primary_doc_description`` / ``filing_url`` / ``filing_index_url`` / ``year``.
            - 정렬: filing_date ASC → form ASC → accession_no ASC.
            - 빈 list — 매칭 0 (form/date 필터 너무 좁음 또는 회사 미제출).
        Prerequisites:
            - ``submissions`` dict (``getSubmissionsJson`` 결과).
            - 인터넷 + SEC EDGAR API 접근 (paginated 페이지 fetch 시).
            - User-Agent header (``EdgarClient``).
        Freshness:
            - SEC EDGAR submissions API 실시간 갱신 (제출 후 분 단위 반영).
            - 정기보고서 cadence: 10-K (연 1 회, 회계년도 마감 후 60-90 일) /
              10-Q (분기, 마감 후 45 일) / 20-F (외국 발행자 연 1 회) / 40-F (캐나다 연 1 회).
        Dataflow:
            - submissions (raw JSON) → ``mergeSubmissionFilings`` (recent + older 병합)
            - → ``SUPPORTED_REGULAR_FORMS`` 매칭 + forms 사용자 set 필터
            - → ``sinceYear`` 연도 cut + ``_coerceDateBound`` since/until 일 bound
            - → accession_no → filing_url 구성 (sec.gov/Archives/edgar/data 패턴)
            - → filing_date ASC 정렬 → list[dict].
        TargetMarkets:
            - US (SEC EDGAR) — NYSE/NASDAQ/AMEX/OTC SEC 등록 + 정기보고서 제출 종목.
            - 외국 발행자 (20-F / 40-F) 포함 — 신흥 시장 ADR 분석 가능.
    """
    merged = mergeSubmissionFilings(submissions, sinceYear=sinceYear, client=client)
    reportDates = merged.get("reportDate", [""] * len(merged.get("form", [])))
    acceptanceDates = merged.get("acceptanceDateTime", [""] * len(merged.get("form", [])))
    descriptions = merged.get("primaryDocDescription", [""] * len(merged.get("form", [])))
    formSet = {form.upper() for form in forms} if forms else None
    sinceBound = _coerceDateBound(since, end=False)
    untilBound = _coerceDateBound(until, end=True)
    cik = str(submissions.get("cik") or "").zfill(10)

    rows: list[dict[str, Any]] = []
    for idx, formType in enumerate(merged.get("form", [])):
        formText = str(formType or "")
        if formText not in SUPPORTED_REGULAR_FORMS:
            continue
        if formSet is not None and formText.upper() not in formSet:
            continue

        filingDate = str(merged.get("filingDate", [None])[idx] or "")
        if len(filingDate) < 4 or not filingDate[:4].isdigit():
            continue
        if int(filingDate[:4]) < sinceYear:
            continue
        if sinceBound is not None and filingDate < sinceBound:
            continue
        if untilBound is not None and filingDate > untilBound:
            continue

        accession = str(merged.get("accessionNumber", [None])[idx] or "")
        primaryDocument = str(merged.get("primaryDocument", [None])[idx] or "")
        accessionNoDash = accession.replace("-", "")
        filingDir = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accessionNoDash}"
        rows.append(
            {
                "cik": cik,
                "form": formText,
                "filing_date": filingDate,
                "report_date": reportDates[idx] or None,
                "acceptance_datetime": acceptanceDates[idx] or None,
                "accession_no": accession,
                "primary_document": primaryDocument or None,
                "primary_doc_description": descriptions[idx] or None,
                "filing_url": f"{filingDir}/{primaryDocument}" if primaryDocument else filingDir,
                "filing_index_url": f"{filingDir}/index.json",
                "year": filingDate[:4],
            }
        )

    rows.sort(key=lambda row: (row["filing_date"], row["form"], row["accession_no"]))
    return rows


def findAllFilings(
    submissions: dict[str, Any],
    *,
    sinceYear: int = 2023,
    since: str | date | datetime | None = None,
    until: str | date | datetime | None = None,
) -> list[dict[str, Any]]:
    """submissions 의 ``filings.recent`` 블록에서 **전 form** filing 메타를 뽑는다 (네트워크 0).

    공시 피드(수시공시 8-K·DEF 14A·SC 13·Form 4 등)용 — ``findRegularFilings`` 의 형제지만
    ``SUPPORTED_REGULAR_FORMS`` 게이트가 *없고*, ``mergeSubmissionFilings`` 의 페이지 fetch 도 안 한다
    (recent 블록 ~1000건이 수년치 피드 충분). bulk(submissions.zip) 회사별 처리에서 네트워크 없이 순회하기
    위함. 정기/수시 구분 없이 전부 반환 — 정기 제외는 소비자(런타임 feed)가 form 으로 필터.

    Args:
        submissions: ``getSubmissionsJson`` 또는 submissions.zip 의 회사 JSON dict.
        sinceYear: filingDate 연도 하한 (default 2023 — 피드 윈도).
        since: 시작일 (``YYYY-MM-DD``/``YYYYMMDD``/date/datetime).
        until: 종료일.

    Returns:
        list[dict] — filing_date ASC. 각 dict: ``cik``·``entityName``·``form``·``filing_date``·
        ``accession_no``·``primary_document``·``primary_doc_description``·``filing_url``·``year``.

    Raises:
        없음 — recent 블록 부재/형식오류는 빈 list.

    Example:
        >>> rows = findAllFilings(getSubmissionsJson("0000320193"), sinceYear=2024)  # doctest: +SKIP
        >>> {r["form"] for r in rows} & {"8-K", "10-K"}  # doctest: +SKIP

    Capabilities:
        - recent 블록(네트워크 0)에서 정기/수시 구분 없이 전 form filing 메타를 연도·기간 필터로 추출.
          ``findRegularFilings`` 와 달리 form 게이트·과거 페이지 fetch 없음(피드 윈도 수년치 충분).

    AIContext:
        US 공시 피드(수시 8-K·DEF 14A 등)의 행 생성기. AI 직접 호출 X — sync 워크플로가 bulk 순회 중
        회사별로 본 함수를 불러 recent.parquet 행을 만든다.

    Guide:
        - "US 전 공시(정기+수시)를 네트워크 없이" → 본 함수. 정기만이면 ``findRegularFilings``.
        - 정기 제외(피드 전용)는 소비자가 ``SUPPORTED_REGULAR_FORMS`` 로 필터(여기선 전부 반환).

    When:
        edgarFilingsSync 가 submissions.zip 회사별 JSON 을 순회할 때. 로컬 dev 눈검수 1회.

    How:
        ``filings.recent`` 의 컬럼 병렬 배열(form·filingDate·accessionNumber·...)을 인덱스로 zip,
        sinceYear/since/until 경계로 거른 뒤 SEC Archives URL 을 합성해 dict 행 생성.

    Requires:
        - ``getSubmissionsJson`` 또는 submissions.zip 의 회사 JSON(``filings.recent`` 키)
        - ``_coerceDateBound`` (기간 경계 정규화)

    SeeAlso:
        - :func:`findRegularFilings` — 정기 form 게이트 + 페이지 fetch 형제
        - :func:`dartlab.gather.edgar.bulkSubmissions.iterSubmissionsBulk` — bulk 순회 공급원
    """
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form") or []
    if not forms:
        return []
    filingDates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    primaryDocs = recent.get("primaryDocument", [])
    descriptions = recent.get("primaryDocDescription", [])
    cik = str(submissions.get("cik") or "").zfill(10)
    entityName = str(submissions.get("name") or submissions.get("entityName") or "")
    sinceBound = _coerceDateBound(since, end=False)
    untilBound = _coerceDateBound(until, end=True)

    def _at(arr: list, idx: int) -> str:
        return str(arr[idx]) if idx < len(arr) and arr[idx] is not None else ""

    rows: list[dict[str, Any]] = []
    for idx, formType in enumerate(forms):
        filingDate = _at(filingDates, idx)
        if len(filingDate) < 4 or not filingDate[:4].isdigit() or int(filingDate[:4]) < sinceYear:
            continue
        if sinceBound is not None and filingDate < sinceBound:
            continue
        if untilBound is not None and filingDate > untilBound:
            continue
        accession = _at(accessions, idx)
        primaryDocument = _at(primaryDocs, idx)
        filingDir = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession.replace('-', '')}"
        rows.append(
            {
                "cik": cik,
                "entityName": entityName,
                "form": str(formType or ""),
                "filing_date": filingDate,
                "accession_no": accession,
                "primary_document": primaryDocument or None,
                "primary_doc_description": _at(descriptions, idx) or None,
                "filing_url": f"{filingDir}/{primaryDocument}" if primaryDocument else filingDir,
                "year": filingDate[:4],
            }
        )
    rows.sort(key=lambda row: (row["filing_date"], row["accession_no"]))
    return rows


def filingsFrame(
    submissions: dict[str, Any],
    *,
    ticker: str | None = None,
    title: str | None = None,
    sinceYear: int = 2009,
    forms: list[str] | tuple[str, ...] | None = None,
    since: str | date | datetime | None = None,
    until: str | date | datetime | None = None,
    client: EdgarClient | None = None,
) -> pl.DataFrame:
    """정기보고서 목록을 ticker/title 포함 Polars DataFrame 으로 반환.

    Args:
        submissions: ``getSubmissionsJson`` 결과.
        ticker: ticker 라벨.
        title: 회사명 라벨.
        sinceYear: 시작 연도.
        forms: form 유형 필터.
        since: 시작일.
        until: 종료일.
        client: EdgarClient 인스턴스.

    Returns:
        ``ticker/cik/title/form/filing_date/...`` 컬럼 DataFrame.

    Raises:
        EdgarApiError: 추가 페이지 fetch 실패.

    Example:
        >>> filingsFrame(getSubmissionsJson("0000320193"), ticker="AAPL", title="Apple Inc.")

    SeeAlso:
        - ``filingsFrame`` — submissions → DataFrame 변환.
        - ``SUPPORTED_REGULAR_FORMS`` — 10-K/10-Q/20-F/40-F.

    Requires:
        - dartlab
        - datetime
        - polars

    Capabilities:
        - SEC submissions API 위임 — 회사 별 정기보고서 + 수시공시 메타 + accession_no list.

    Guide:
        - "SEC 공시 목록 조회" → 본 모듈.

    AIContext:
        internal submissions wrapper — AI 직접 호출 X.

    LLM Specifications:
        AntiPatterns:
            - User-Agent 미설정 → 403.
            - 전체 submissions 그대로 LLM 노출 → 토큰 폭증. form/since 필터.
        OutputSchema:
            - dict (raw JSON) 또는 pl.DataFrame (filings).
        Prerequisites:
            - 인터넷 + SEC EDGAR public API + CIK.
        Freshness:
            - SEC EDGAR 실시간 (분 단위).
        Dataflow:
            - CIK → EdgarClient → submissions API → JSON → 정규화.
        TargetMarkets:
            - US (SEC EDGAR) submissions.
    """
    rows = findRegularFilings(
        submissions,
        sinceYear=sinceYear,
        forms=forms,
        since=since,
        until=until,
        client=client,
    )
    if not rows:
        return pl.DataFrame(
            schema={
                "ticker": pl.Utf8,
                "cik": pl.Utf8,
                "title": pl.Utf8,
                "form": pl.Utf8,
                "filing_date": pl.Utf8,
                "report_date": pl.Utf8,
                "accession_no": pl.Utf8,
                "primary_document": pl.Utf8,
                "primary_doc_description": pl.Utf8,
                "filing_url": pl.Utf8,
                "filing_index_url": pl.Utf8,
                "year": pl.Utf8,
            }
        )

    df = pl.DataFrame(rows)
    return df.with_columns(
        [
            pl.lit((ticker or "")).alias("ticker"),
            pl.lit((title or "")).alias("title"),
        ]
    ).select(
        [
            "ticker",
            "cik",
            "title",
            "form",
            "filing_date",
            "report_date",
            "accession_no",
            "primary_document",
            "primary_doc_description",
            "filing_url",
            "filing_index_url",
            "year",
        ]
    )
