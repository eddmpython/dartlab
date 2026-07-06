"""신규상장 IPO 횡단 — 최근 증권신고서(지분증권) 발굴 + 6 카테고리 핵심값.

scan 21 축은 전 상장사(corp_cls Y/K)를 본다. 본 축은 *상장 전* 발행사(corp_cls=E)를 본다 —
신규상장 IPO 의 증권신고서(지분증권)를 최근 윈도우에서 발굴해 공모가밴드·청약일·적용 PER·할인율을
횡단한다. orders.py 동형이되 데이터원이 다르다: IPO 는 allFilings(Y/K 한정)에 없으므로 listFilings
(corp_cls=E) 메타 → 발행사별 최신 FULL 신고서만 본문 직독([발행조건확정] CORRECTION doc 제외) →
:func:`dartlab.providers.dart.securitiesRegistration.parseIpoProspectus` 위임.

판별 = ``classifyIpo`` 3 조건(지분증권+E+빈 stock_code). 단건 deep 6 카테고리는 parseIpoProspectus.
본문 content_raw 는 PRIVATE — 본 축은 추출 핵심값만 반환.
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# 발굴 윈도(일). list.json 은 corp_code 없으면 3 개월(~90 일) 제한이라 초과는 무의미(status 100).
# buildIpoReports(베이크 sync) 와 공유하는 SSOT. tests/sync/test_buildIpoReports 가 동치 강제(드리프트 가드).
IPO_WINDOW_DAYS = 85

_OUTPUT_SCHEMA = {
    "corpName": pl.Utf8,
    "corpCode": pl.Utf8,
    "rcept": pl.Utf8,
    "rceptDt": pl.Utf8,
    "isSpac": pl.Boolean,
    "subscription": pl.Utf8,
    "payDate": pl.Utf8,
    "priceBandLow": pl.Float64,
    "priceBandHigh": pl.Float64,
    "offerTotal": pl.Float64,
    "shares": pl.Int64,
    "appliedPer": pl.Float64,
    "perShareValue": pl.Float64,
    "discountLow": pl.Float64,
    "discountHigh": pl.Float64,
    "freeFloatPct": pl.Float64,
    "lockedShares": pl.Float64,
    "chainOk": pl.Boolean,
    "financialsOk": pl.Boolean,
    "floatOk": pl.Boolean,
    "asOf": pl.Utf8,
}


def _discoverIpoIssuers(
    client, *, dateFrom: str | None = None, includeConfirmation: bool = False, verbose: bool = True
) -> tuple[list[dict], str]:
    """corp_cls=E 증권신고서 발굴 → 발행사별 최신 FULL 신고서 (+ 옵션 발행조건확정 conf doc). 발굴/그룹핑 SSOT.

    listFilings(E, C 발행공시) → classifyIpo 필터 → corp_code 그룹핑. scan("ipo")·buildIpoReports(베이크)가
    공유하던 로직의 파이썬 단일 소스(파싱은 buildIpoReport 별도 위임). TS groupIpoFilings(워커)는 크로스런타임
    미러라 별개 유지. client None 이면 내부 지연 생성(mock 검증 편의).

    Args:
        dateFrom: "YYYYMMDD" 이상만 (None=최근 IPO_WINDOW_DAYS 일).
        includeConfirmation: True 면 발행사별 최신 [발행조건확정] doc 을 conf 로 붙임(베이크 확정공모가 병합용).

    Returns:
        (issuers, asOf). issuers = [{"full": meta(+_isSpac), "conf": meta|None}] (FULL 없는 발행사 제외),
        asOf = 발굴 기준일(YYYYMMDD).
    """
    from dartlab.gather.dart.disclosure import listFilings
    from dartlab.providers.dart.securitiesRegistration import classifyIpo

    if client is None:
        from dartlab.core.dartClient import DartClient

        client = DartClient()

    end = date.today()
    start = end - timedelta(days=IPO_WINDOW_DAYS)  # list.json corp_code 없으면 3 개월 제한
    if dateFrom and len(dateFrom) == 8:
        cand = date(int(dateFrom[:4]), int(dateFrom[4:6]), int(dateFrom[6:8]))
        start = max(start, cand)
    asOf = end.strftime("%Y%m%d")
    # filingType="C"(발행공시) index-first. 효력발생안내·non-발행 E 노이즈 제외 (PRD 성능 척추).
    df = listFilings(client, start=start.strftime("%Y%m%d"), end=asOf, corpClass="E", filingType="C", fetchAll=True)
    if df.height == 0:
        return [], asOf

    byCorp: dict[str, dict] = {}
    for r in df.iter_rows(named=True):
        reportNm = r.get("report_nm") or ""
        c = classifyIpo(reportNm, r.get("corp_cls") or "", r.get("stock_code") or "", r.get("corp_name") or "")
        if not c["isIpo"]:
            continue
        slot = byCorp.setdefault(r["corp_code"], {"full": None, "conf": None})
        if "발행조건확정" in reportNm:  # CORRECTION doc(6 섹션 없음). 확정공모가 병합용, FULL 아님.
            if includeConfirmation and (slot["conf"] is None or r["rcept_no"] > slot["conf"]["rcept_no"]):
                slot["conf"] = r
        elif c["kind"] == "prospectus":
            if slot["full"] is None or r["rcept_no"] > slot["full"]["rcept_no"]:
                slot["full"] = {**r, "_isSpac": c["isSpac"]}
    issuers = [v for v in byCorp.values() if v["full"] is not None]
    if verbose:
        _log.info("IPO 발굴: %s~%s · 발행사 %d 곳", start, end, len(issuers))
    return issuers, asOf


def _latestFullProspectuses(client, dateFrom: str | None, verbose: bool) -> tuple[list[dict], str]:
    """발행사별 최신 FULL 신고서 meta list + asOf. _discoverIpoIssuers 위임(scan 은 FULL 만 파싱, conf 불요)."""
    issuers, asOf = _discoverIpoIssuers(client, dateFrom=dateFrom, includeConfirmation=False, verbose=verbose)
    return [it["full"] for it in issuers], asOf


def _parseRow(client, meta: dict, asOf: str) -> dict:
    """발행사 1 곳 → 메타 + (deep) 본문 직독 파싱 핵심값 row."""
    from dartlab.gather.dart.allFilingsCollector import _collectOneRaw
    from dartlab.providers.dart.securitiesRegistration import parseIpoProspectus

    row: dict[str, object] = {
        "corpName": meta.get("corp_name"),
        "corpCode": meta.get("corp_code"),
        "rcept": meta.get("rcept_no"),
        "rceptDt": meta.get("rcept_dt"),
        "isSpac": bool(meta.get("_isSpac")),
        "asOf": asOf,
    }
    content, status = _collectOneRaw(client, meta["rcept_no"])
    if status == "ok" and content:
        p = parseIpoProspectus(content)
        off, val, ids, flt = p["offering"], p["valuation"], p["identities"], p["float"]
        band = off.get("priceBand")
        disc = val.get("discount")
        row.update(
            {
                "subscription": off.get("subscription"),
                "payDate": off.get("payDate"),
                "priceBandLow": band[0] if band else None,
                "priceBandHigh": band[1] if band else None,
                "offerTotal": off.get("offerTotal"),
                "shares": ids.get("sharesRecovered"),
                "appliedPer": val.get("peerMultiple"),
                "perShareValue": val.get("perShareValue"),
                "discountLow": min(disc) if disc else None,
                "discountHigh": max(disc) if disc else None,
                "freeFloatPct": flt.get("freeFloatPct"),
                "lockedShares": flt.get("lockedShares"),
                "chainOk": ids.get("valuationChain"),
                "financialsOk": ids.get("financialsBalance"),
                "floatOk": ids.get("floatBalance"),
            }
        )
    return row


def scanIpo(*, dateFrom: str | None = None, deep: bool = True, verbose: bool = True) -> pl.DataFrame:
    """최근 신규상장 IPO 횡단 — 증권신고서(지분증권) 발굴 + 공모가·청약일·적용 PER·할인율.

    상장 전 발행사(corp_cls=E)의 증권신고서(지분증권)를 최근 윈도우에서 발굴(``classifyIpo`` 3 조건)
    하고, 발행사별 최신 FULL 신고서 본문을 직독해 공모 조건·상대가치 평가 핵심값을 횡단한다.
    ``[발행조건확정]`` CORRECTION doc(6 섹션 없음)는 제외하고 FULL 신고서만 파싱한다.

    Args:
        dateFrom: ``"YYYYMMDD"`` 이상만 (None=최근 85 일, list.json 3 개월 제한). 더 과거는
            윈도우 분할 호출 권장.
        deep: True 면 발행사별 본문 직독해 6 카테고리 핵심값까지 (느림 — 발행사당 fetch 1).
            False 면 메타(회사명·rcept·스팩)만 빠르게.
        verbose: 진행 라인 ``logger.info``.

    Returns:
        pl.DataFrame
            corpName : str — 발행사명
            corpCode : str — DART corp_code
            rcept : str — 최신 FULL 신고서 접수번호 (원문근거 링크)
            rceptDt : str — 접수일 (YYYYMMDD)
            isSpac : bool — 기업인수목적(스팩)
            subscription : str — 청약기일 (deep)
            payDate : str — 납입기일 (deep)
            priceBandLow / priceBandHigh : float — 희망공모가밴드 (deep)
            offerTotal : float — 모집총액(원, deep)
            shares : int — 모집주식수(항등식 복구, deep)
            appliedPer : float — 발행사 적용 비교기업 PER (deep)
            perShareValue : float — 주당 평가가액(원, deep)
            discountLow / discountHigh : float — 평가액 대비 할인율(%, deep)
            freeFloatPct : float — 상장 직후 유통가능비율(%, deep)
            lockedShares : float — 매각제한(보호예수)물량 주식수 (deep)
            chainOk : bool — 밸류 체인 항등식(①×②÷③≈평가액) 통과 (deep)
            financialsOk : bool — 재무 항등식(자산=부채+자본) 통과 (deep)
            floatOk : bool — 유통 항등식(매각제한+유통가능=공모후총발행) 통과 (deep)
            asOf : str — 발굴 기준일(YYYYMMDD)

    Raises:
        없음 — listFilings 0 또는 IPO 0 시 빈 DataFrame.

    Examples:
        >>> import dartlab  # doctest: +SKIP
        >>> df = dartlab.scan("ipo")  # doctest: +SKIP
        >>> df.select(["corpName", "priceBandLow", "appliedPer", "chainOk"])  # doctest: +SKIP

    Capabilities:
        - corp_cls=E 증권신고서(지분증권) 발굴(사람 라벨 0) → 발행사별 최신 FULL 신고서 본문 직독.
        - 공모가밴드·청약/납입일·적용 PER·할인율·평가액 + 내적 항등식 통과 플래그 횡단.

    AIContext:
        Agent 가 "이번달/최근 IPO" / "청약 임박 종목 공모가·밸류" 류 cross 질문 시 dispatch. 단건
        deep 6 카테고리(유통물량·재무3개년·리스크 전체)는 후속으로
        :func:`dartlab.providers.dart.securitiesRegistration.parseIpoProspectus`.

    Guide:
        - 발행사당 본문(60 만~470 만 자) fetch 1 회 — deep=True 는 발행사 수에 비례해 느리다.
          빠른 목록만 필요하면 deep=False.
        - 적용 PER 는 발행사가 *선택한* 비교군 기준 — "고저평가" 단정 말고 비교 좌표로 사용.

    When:
        IPO 청약 캘린더·공모가 밸류 스크리닝 시.

    How:
        ``listFilings(corp_cls=E)`` 메타 → ``classifyIpo`` 필터 → 발행사별 최신 FULL rcept →
        ``_collectOneRaw`` 본문 직독 → ``parseIpoProspectus`` → 핵심값 추출.

    Requires:
        - DART_API_KEYS (listFilings + document.xml). allFilings 불요(라이브 직독).
        - ``providers.dart.securitiesRegistration`` 파서.

    SeeAlso:
        - :func:`dartlab.providers.dart.securitiesRegistration.parseIpoProspectus` — 단건 6 카테고리.
        - :func:`dartlab.providers.dart.securitiesRegistration.classifyIpo` — IPO 판별.
        - :func:`dartlab.scan.orders.scanOrders` — 신규수주 횡단(동형 패턴).

    LLM Specifications:
        AntiPatterns:
            - ``[발행조건확정]`` 을 6 섹션 기대 (CORRECTION doc — FULL 신고서를 봐야).
            - ``chainOk``/``financialsOk`` False 인 발행사 값을 신뢰 (항등식 위반).
            - 적용 PER 를 절대 고/저평가로 단정 (발행사 선택 비교군 기준).
        OutputSchema:
            - corpName/corpCode/rcept/rceptDt/isSpac/subscription/payDate/priceBand*/offerTotal/
              shares/appliedPer/perShareValue/discount*/chainOk/financialsOk/asOf.
        Prerequisites:
            - DART_API_KEYS. 최근 윈도우(기본 85 일).
        Freshness:
            - asOf (발굴 기준일).
        Dataflow:
            - scan("ipo") → 후보 → parseIpoProspectus(단건 deep) → 원문근거 rcept.
        TargetMarkets:
            - KR (DART 증권신고서 지분증권).
    """
    metas, asOf = _latestFullProspectuses(None, dateFrom, verbose)
    if not metas:
        return pl.DataFrame(schema=_OUTPUT_SCHEMA)

    from dartlab.core.dartClient import DartClient

    client = DartClient() if deep else None
    rows = []
    for i, meta in enumerate(metas, start=1):
        if deep:
            if verbose:
                _log.info("  [%d/%d] %s 본문 파싱", i, len(metas), meta.get("corp_name"))
            rows.append(_parseRow(client, meta, asOf))
        else:
            rows.append(
                {
                    "corpName": meta.get("corp_name"),
                    "corpCode": meta.get("corp_code"),
                    "rcept": meta.get("rcept_no"),
                    "rceptDt": meta.get("rcept_dt"),
                    "isSpac": bool(meta.get("_isSpac")),
                    "asOf": asOf,
                }
            )
    df = pl.DataFrame(rows, schema_overrides=_OUTPUT_SCHEMA)
    return df.sort("rceptDt", descending=True)


__all__ = ["scanIpo"]
