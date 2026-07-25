"""목록 조회 단일 진입점 — `dartlab.listing(kind, ...)`.

dartlab의 카탈로그성 API들("뭐가 있는지 본다")을 한 함수의 `kind` 인자로 통합한다.
원문 검색("내용 안에서 찾는다")은 별도 엔진 `dartlab.search()`를 사용한다.

지원 kind:
    companies (기본) — 전체 상장법인 (KR/US)
    filings        — 기업별 공시 메타 목록 (DART/EDGAR 자동 분기)
    topics         — 기업별 토픽 목록

상세: src/dartlab/gather/LISTING.md
"""

from __future__ import annotations

import polars as pl

_ALIAS = {
    "기업": "companies",
    "종목": "companies",
    "company": "companies",
    "공시": "filings",
    "filing": "filings",
    "토픽": "topics",
    "topic": "topics",
    "법인": "dartlist",
    "dart": "dartlist",
    "all": "all",
}

_SUPPORTED = ("companies", "filings", "topics", "dartlist", "all")


def listing(
    kind: str = "companies",
    *,
    corp: str | None = None,
    market: str | None = None,
    **kw,
) -> pl.DataFrame:
    """목록 조회 단일 진입점.

    Args:
        kind: 조회 종류. "companies"(기본), "filings", "topics", "dartlist".
            한글 alias 지원: "기업", "공시", "토픽", "법인", "dart".
        corp: 종목코드 또는 ticker. filings/topics에 필수.
        market: "KR" 또는 "US". companies에서만 사용.

    Returns
    -------
    pl.DataFrame
        kind="companies" (기본):
            market="KR" 또는 생략:
            종목코드 : str — 6자리 종목코드
            종목명 : str — 회사명
            시장 : str — 유가/코스닥/코넥스
            업종 : str — 업종명
            market="US":
            종목코드 : str — 미국 ticker
            회사명 : str — SEC 등록 회사명
            시장구분 : str — 거래소
            cik : str — 10자리 SEC 식별번호
        kind="filings":
            id : str — 공시 접수번호
            date : str — 접수일
            title : str — 공시 제목
            url : str — 공시 URL
        kind="topics":
            topic : str — topic 이름
            source : str — 데이터 출처 (docs/finance/report)
            periods : str — 사용 가능 기간
        kind="dartlist":
            corp_code : str — DART 법인코드 (8자리)
            corp_name : str — 법인명
            stock_code : str | None — 종목코드 (비상장이면 None)

    Raises:
        ValueError: 지원하지 않는 kind, 또는 필수 인자 누락.

    Example::

        import dartlab
        import polars as pl

        dartlab.listing()                              # 전 종목 (기존 호환)
        dartlab.listing("dartlist")                    # DART 전체 법인 (비상장 포함, corp_code)
        us = dartlab.listing(market="US")              # EDGAR 종목 + 공개 CIK 열
        us.filter(pl.col("종목코드") == "AAPL").select("종목코드", "회사명", "cik")
        dartlab.listing("filings", corp="005930")      # DART 공시 메타
        dartlab.listing("filings", corp="AAPL")        # EDGAR 공시 메타
        dartlab.listing("topics", corp="005930")       # 토픽 목록
    """
    kind = _ALIAS.get(kind, kind)
    if kind == "companies":
        return _companies(market=market)
    if kind == "filings":
        if not corp:
            raise ValueError("listing('filings') requires corp=")
        return _filings(corp)
    if kind == "topics":
        if not corp:
            raise ValueError("listing('topics') requires corp=")
        return _topics(corp)
    if kind == "dartlist":
        return _dartlist()
    if kind == "all":
        return _companies(market=market)
    raise ValueError(f"unknown kind: {kind!r} — supported: {', '.join(_SUPPORTED)}")


def _dartlist() -> pl.DataFrame:
    """OpenDART 전체 법인 목록 (상장+비상장, corp_code 8자리 포함)."""
    from dartlab.gather.krx.listing import getDartList

    return getDartList()


def _companies(market: str | None = None) -> pl.DataFrame:
    """전체 상장법인 목록 — 기존 dartlab.listing() 동작과 동일."""
    if market and market.upper() == "US":
        try:
            from dartlab.providers.edgar.company import Company as _US

            return _US.listing()
        except (ImportError, AttributeError, NotImplementedError) as e:
            raise NotImplementedError("US listing은 아직 지원되지 않습니다") from e
    from dartlab.providers.dart.company import Company as _DartEngineCompany

    return _DartEngineCompany.listing()


def _filings(corp: str) -> pl.DataFrame:
    """기업별 공시 메타. DART/EDGAR 자동 분기 + 공통 컬럼 정규화."""
    from dartlab.company import Company

    c = Company(corp)
    df = c.filings()
    if df is None:
        return pl.DataFrame(schema={"id": pl.Utf8, "date": pl.Utf8, "url": pl.Utf8})
    return _normalizeFilings(df, c)


def _normalizeFilings(df: pl.DataFrame, company) -> pl.DataFrame:
    """DART/EDGAR filings DataFrame을 공통 컬럼(id/date/period/reportType/url)으로 통일.

    원본 컬럼은 보존(드롭하지 않는다).
    """
    cols = df.columns

    # DART: rceptNo / rceptDate / reportType / dartUrl / year
    if "rceptNo" in cols:
        normalized = df.with_columns(
            pl.col("rceptNo").alias("id"),
            pl.col("rceptDate").alias("date"),
            pl.col("year").alias("period"),
            pl.col("dartUrl").alias("url"),
        )
        front = ["id", "date", "period", "reportType", "url"]
        rest = [c for c in normalized.columns if c not in front]
        return normalized.select([*front, *rest])

    # EDGAR: accession_no / filed_date / form_type / period_key
    if "accession_no" in cols:
        cik = getattr(company, "cik", None)
        if cik is not None:
            url_expr = (
                pl.lit("https://www.sec.gov/Archives/edgar/data/")
                .add(pl.lit(str(cik)))
                .add(pl.lit("/"))
                .add(pl.col("accession_no").str.replace_all("-", ""))
                .add(pl.lit("/"))
                .add(pl.col("accession_no"))
                .add(pl.lit("-index.htm"))
                .alias("url")
            )
        else:
            url_expr = pl.lit(None, dtype=pl.Utf8).alias("url")
        normalized = df.with_columns(
            pl.col("accession_no").alias("id"),
            pl.col("filed_date").alias("date"),
            pl.col("period_key").alias("period"),
            pl.col("form_type").alias("reportType"),
            url_expr,
        )
        front = ["id", "date", "period", "reportType", "url"]
        rest = [c for c in normalized.columns if c not in front]
        return normalized.select([*front, *rest])

    # 알 수 없는 스키마 — 원본 그대로
    return df


def _topics(corp: str) -> pl.DataFrame:
    """기업별 토픽 목록. dict → DataFrame(topic, summary)."""
    from dartlab.company import Company

    c = Company(corp)
    summaries = c.topicSummaries() or {}
    if not summaries:
        return pl.DataFrame(schema={"topic": pl.Utf8, "summary": pl.Utf8})
    return pl.DataFrame({"topic": list(summaries.keys()), "summary": list(summaries.values())})
