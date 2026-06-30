"""Polygon (Massive) grouped-daily — 하루치 전 US 종목 OHLCV 1콜 (by-day 벌크).

gov ``fetchGovBydd`` (하루치 전종목)의 US 대칭. per-ticker(``yahooChart``) 6437콜 대신 **by-day 1콜**로
그날 전 US 시장 OHLCV 를 받는다 — 일별 sync 의 증분 source. 운영자 cron 이 어제 date 1콜로 전종목 증분.

Polygon.io 가 2025-10-30 Massive 로 리브랜딩(같은 회사·API 무변, ``api.polygon.io`` 유지). 무료티어
5콜/분·2년 이력(일증분엔 무관 — 오늘 1봉만 받음). ``adjusted=true`` = 수정주가(Yahoo adjclose 와 일치 실측).
"""

from __future__ import annotations

import httpx
import polars as pl

_GROUPED_URL = "https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date}"


def fetchGroupedDaily(date, *, apiKey: str, client: httpx.Client | None = None, timeout: float = 30.0) -> pl.DataFrame:
    """하루치 전 US 종목 OHLCV raw fetch (Polygon grouped-daily 1콜).

    Capabilities: 그날 전 US 시장(~12000종목) OHLCV raw — 일별 sync 증분 source (by-day 벌크 1콜).
    AIContext: edgarPrices daily 가 어제 date 1콜로 전종목 증분 수집 (per-ticker 6437콜 회피).
    Guide: 운영자 cron(edgarPrices daily)만 호출 → edgar/prices/recent tail 갱신.
    When: 매일 장마감 후 어제 date 1콜.
    How: grouped-daily GET → results[T,o,h,l,c,v] → ticker/date/OHLCV DataFrame.
    Requires: 인터넷 + Polygon(Massive) API 키.
    SeeAlso: gov.govApi.fetchGovBydd (KR 대칭) · domains.yahooChart.fetchHistory (per-ticker 백필).

    Args:
        date: 기준일 'YYYYMMDD' 또는 'YYYY-MM-DD'.
        apiKey: Polygon/Massive API 키 (명시 필수 — 도메인은 env 미참조, 호출자가 주입).
        client: 재사용 ``httpx.Client`` (선택, 다일 루프 시 1개 공유).
        timeout: 요청 타임아웃(초).

    Returns:
        pl.DataFrame: ticker(SEC 대시 convention)·date(YYYYMMDD)·open·high·low·close·volume.
        클래스주는 Polygon 점(BRK.B)을 SEC 대시(BRK-B)로 정규화. 휴장/미확정일은 빈 DataFrame.

    Raises:
        ValueError: apiKey 빈 문자열.
        httpx.HTTPStatusError: Polygon 4xx/5xx (단 404 = 빈 DataFrame).

    Example:
        >>> df = fetchGroupedDaily("20260622", apiKey=key)  # ~12000행
    """
    if not apiKey:
        raise ValueError("apiKey 필수 — Polygon(Massive) 키")
    ymd = str(date).replace("-", "").strip()
    iso = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:8]}"
    url = _GROUPED_URL.format(date=iso)
    params = {"adjusted": "true", "apiKey": apiKey}
    own = client is None
    cli = client or httpx.Client(timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = cli.get(url, params=params)
        if resp.status_code == 404:
            return pl.DataFrame()
        resp.raise_for_status()
        data = resp.json()
    finally:
        if own:
            cli.close()
    if data.get("status") not in ("OK", "DELAYED"):
        return pl.DataFrame()
    out: list[dict] = []
    for x in data.get("results", []):
        ticker = x.get("T")
        close = x.get("c")
        if not ticker or close is None:
            continue
        out.append(
            {
                # Polygon 클래스주 구분자는 점(BRK.B), dartlab 유니버스(SEC company_tickers)는 대시(BRK-B).
                # SEC convention 으로 정규화해 valuation·finance·runtime resolveMarket 와 키 일치(BRK-B 등 가격 매칭).
                # 워런트/유닛(.WS·.U)도 대시화되나 상장 common 유니버스 밖이라 listedOnly 필터에서 자연 제외.
                "ticker": str(ticker).upper().replace(".", "-"),
                "date": ymd,
                "open": x.get("o"),
                "high": x.get("h"),
                "low": x.get("l"),
                "close": close,
                "volume": int(round(float(x.get("v") or 0))),
            }
        )
    return pl.DataFrame(out) if out else pl.DataFrame()
