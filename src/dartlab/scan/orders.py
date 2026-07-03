"""신규수주 flow 횡단 — 전 상장사 단일판매·공급계약 → book-to-bill.

scan 21 축은 전부 후행(재무·지배구조·공시변화)이다. 본 축은 *유일한 선행 지표* — 신규수주 flow
(건설·조선·방산·플랜트 향후매출 잠금) 를 횡단한다.

런타임-SSOT: 데이터원 = allFilings 월별 parquet(런타임 SSOT, content_raw 포함). report_nm
"단일판매" 필터로 전 상장사 중 계약 공시한 회사를 발굴 → 본문 직독 파싱(fetch 0) → 집계. 별도
orders.parquet 베이크 *없음* (런타임 직독). 파싱=providers.dart.eventDisclosure, 본 축은 횡단 집계만.

book-to-bill = TTM 신규수주 / 최근매출액(공시 자체 제공 → finance 조인 불요). >1 = 백로그 확대.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

_OUTPUT_SCHEMA = {
    "stockCode": pl.Utf8,
    "corpName": pl.Utf8,
    "ttmOrders": pl.Float64,
    "recentRevenue": pl.Float64,
    "bookToBill": pl.Float64,
    "grade": pl.Utf8,
    "momentum": pl.Float64,
    "momentumLabel": pl.Utf8,
    "topCounterparty": pl.Utf8,
    "topShare": pl.Float64,
    "nContract": pl.Int64,
    "nAmend": pl.Int64,
    "nCancel": pl.Int64,
    "asOf": pl.Utf8,
}


def _toDate(yyyymmdd: str | None) -> date | None:
    s = (yyyymmdd or "").strip()
    if len(s) != 8 or not s.isdigit():
        return None
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def _gradeBookToBill(b2b: float | None) -> str:
    if b2b is None:
        return "해당없음"
    if b2b >= 1.0:
        return "수주확대"
    if b2b >= 0.5:
        return "견조"
    if b2b >= 0.2:
        return "둔화"
    return "약함"


def _gradeMomentum(m: float | None) -> str:
    if m is None:
        return "불연속"
    if m >= 1.2:
        return "가속"
    if m >= 0.8:
        return "유지"
    return "감속"


def _collectUniverse(eventType: str, dateFrom: str | None, verbose: bool) -> tuple[dict[str, list[dict]], str | None]:
    """allFilings 전 일자 순회 → stockCode 별 파싱 row 묶음 + 최신 일자(asOf).

    메모리 안전: ``loadDay`` 일별 순회 + 매칭 row 만 인라인 파싱해 작은 dict 로 축약
    (본문 content_raw 미보유). 2.7GB 를 loadAll 로 적재하지 않는다.
    """
    from dartlab.gather.dart.allFilingsCollector import collectedDates, loadDay
    from dartlab.providers.dart.eventDisclosure import classifyEventReport, parseEventDisclosure

    dates = sorted(collectedDates())
    if dateFrom:
        dates = [d for d in dates if d >= dateFrom]
    if not dates:
        return {}, None

    byCompany: dict[str, list[dict]] = {}
    matched = 0
    for d in dates:
        day = loadDay(d)
        if day is None or day.height == 0:
            continue
        hit = day.filter(pl.col("report_nm").str.contains("단일판매"))
        if hit.height == 0:
            continue
        matched += hit.height
        for rec in hit.iter_rows(named=True):
            kind = classifyEventReport((rec["report_nm"] or "").strip(), eventType)
            body = rec.get("content_raw")
            parsed = parseEventDisclosure(body, eventType) if (kind in ("contract", "amend") and body) else {}
            parsed["kind"] = kind
            parsed["rcept_dt"] = rec.get("rcept_dt")
            parsed["corp_name"] = rec.get("corp_name")  # 알림·리포트 가독(코드만으론 정체 불명)
            code = rec.get("stock_code") or "?"
            byCompany.setdefault(code, []).append(parsed)
        del day, hit
    if verbose:
        _log.info(f"수주 전수수집: {len(dates)}일 · {matched}건 · {len(byCompany)}개사 (asOf={dates[-1]})")
    return byCompany, dates[-1]


def _aggregateCompany(code: str, rows: list[dict], asOf: date) -> dict:
    """한 회사 파싱 row → 횡단 지표 dict (영문 컬럼)."""
    amends = [r for r in rows if r.get("kind") == "amend"]
    cancels = [r for r in rows if r.get("kind") == "cancel"]
    contracts = [r for r in rows if r.get("kind") in ("contract", "amend")]

    # dedup: (계약상대, 수주일) — 정정이 원계약 supersede (latest rcept 유지)
    bestByKey: dict[tuple, dict] = {}
    for r in contracts:
        key = (r.get("counterparty") or "?", r.get("orderDate") or r.get("rcept_dt"))
        prev = bestByKey.get(key)
        if prev is None or (r.get("rcept_dt") or "") > (prev.get("rcept_dt") or ""):
            bestByKey[key] = r
    deduped = list(bestByKey.values())

    def _sumWindow(lo: int, hi: int) -> float:
        total = 0.0
        for r in deduped:
            d = _toDate(r.get("rcept_dt"))
            amt = r.get("contractAmount")
            if d is None or amt is None:
                continue
            if lo <= (asOf - d).days < hi:
                total += float(amt)
        return total

    ttmOrders = _sumWindow(0, 365)
    priorOrders = _sumWindow(365, 730)

    # 최근매출액 — 공시별 보고값 중앙값 (단일 오파싱 robust)
    revs = sorted(float(r["recentRevenue"]) for r in deduped if r.get("recentRevenue"))
    recentRevenue = revs[len(revs) // 2] if revs else None

    bookToBill = (ttmOrders / recentRevenue) if recentRevenue else None
    momentum = (ttmOrders / priorOrders) if priorOrders > 0 else None

    byParty: dict[str, float] = {}
    for r in deduped:
        d = _toDate(r.get("rcept_dt"))
        amt = r.get("contractAmount")
        if d is None or amt is None or (asOf - d).days >= 365:
            continue
        party = r.get("counterparty") or "?"
        byParty[party] = byParty.get(party, 0.0) + float(amt)
    topParty, topAmt = max(byParty.items(), key=lambda kv: kv[1]) if byParty else ("-", 0.0)

    corpName = next((r.get("corp_name") for r in rows if r.get("corp_name")), None)
    return {
        "stockCode": code,
        "corpName": corpName,
        "ttmOrders": ttmOrders,
        "recentRevenue": recentRevenue,
        "bookToBill": round(bookToBill, 4) if bookToBill is not None else None,
        "grade": _gradeBookToBill(bookToBill),
        "momentum": round(momentum, 3) if momentum is not None else None,
        "momentumLabel": _gradeMomentum(momentum),
        "topCounterparty": topParty,
        "topShare": round(topAmt / ttmOrders, 4) if ttmOrders > 0 else None,
        "nContract": len([r for r in rows if r.get("kind") == "contract"]),
        "nAmend": len(amends),
        "nCancel": len(cancels),
    }


def scanOrders(*, eventType: str = "supplyContract", dateFrom: str | None = None, verbose: bool = True) -> pl.DataFrame:
    """전 상장사 신규수주 flow 횡단 — book-to-bill·모멘텀·집중도.

    allFilings(런타임 SSOT) 에서 단일판매·공급계약 공시를 전수 수집·파싱해 회사별 TTM 신규수주,
    book-to-bill(TTM수주/최근매출), 수주 모멘텀(TTM/직전TTM), 계약상대 집중도, 등급을 횡단한다.

    Args:
        eventType: 수시공시 유형 (기본 ``"supplyContract"``).
        dateFrom: ``"YYYYMMDD"`` 이상만 수집 (None=수집 전체분, momentum 위해 2 년 권장).
        verbose: 진행 라인 ``logger.info`` 출력.

    Returns:
        pl.DataFrame
            stockCode : str. 종목코드
            corpName : str. 회사명 (allFilings corp_name, 알림·리포트 가독)
            ttmOrders : float. 최근 365 일 신규수주 합(원)
            recentRevenue : float — 최근매출액(원, 공시 self-report 중앙값)
            bookToBill : float — TTM수주/최근매출. >1 = 백로그 확대
            grade : str — 수주확대/견조/둔화/약함/해당없음
            momentum : float — TTM/직전TTM 수주
            momentumLabel : str — 가속/유지/감속/불연속
            topCounterparty : str — 최대 계약상대
            topShare : float — 최대상대 비중(0~1)
            nContract / nAmend / nCancel : int — 체결/정정/해지 건수
            asOf : str — 데이터 기준일(YYYYMMDD)

    Raises:
        없음 — allFilings 미수집 시 빈 DataFrame.

    Examples:
        >>> import dartlab, polars as pl
        >>> df = dartlab.scan("orders")
        >>> df.filter((pl.col("최근매출액") > 1e11) & (pl.col("등급") == "수주확대")).head()

    Capabilities:
        - allFilings report_nm "단일판매" 필터 → 전 상장사 계약 공시 전수 수집(본문 직독, fetch 0).
        - 정정 supersede·해지 분리 dedup → TTM/직전TTM 합 → book-to-bill·모멘텀·집중도·등급.

    AIContext:
        Agent 가 "수주 늘어나는 회사" / "book-to-bill 높은 조선·건설·방산" 같은 cross-company
        질문 시 dispatch. 후행 재무로는 안 보이는 선행 신호. 단건 계약 상세는 후속으로
        :func:`dartlab.providers.dart.eventDisclosure.parseEventDisclosure`.

    Guide:
        - micro-cap 잡음 주의: ``recentRevenue`` 작은 회사는 book-to-bill 극단치 → 매출·계약건수
          필터 권장(예 ``최근매출액 > 1000억 & 계약건수 >= 3``).
        - 런타임 35 초 내외(allFilings 일별 순회). dateFrom 으로 범위 한정 가능(단 momentum 은 2 년 필요).

    When:
        수주산업(건설/조선/방산/기계/플랜트) watchlist·선행 모멘텀 스크리닝 시.

    How:
        ``allFilingsCollector.loadDay`` 일별 순회 → report_nm 필터 → ``parseEventDisclosure`` 인라인
        파싱 → 회사별 ``_aggregateCompany`` → book-to-bill 내림차순 정렬.

    Requires:
        - 로컬/HF ``allFilings`` 월별 parquet (``allFilingsCollector`` 수집분).
        - ``providers.dart.eventDisclosure`` 파서.

    SeeAlso:
        - :func:`dartlab.providers.dart.eventDisclosure.parseEventDisclosure` — 단건 파서.
        - :func:`dartlab.scan.disclosureRisk.scanDisclosureRisk` — 공시 변화 선행 리스크.

    LLM Specifications:
        AntiPatterns:
            - book-to-bill 상위 그대로 추천 (매출 규모·계약건수 필터 없으면 micro-cap 잡음).
            - momentum 극단치(직전TTM 0 근처)를 추세로 단정.
        OutputSchema:
            - stockCode + corpName + ttmOrders/recentRevenue/bookToBill/grade/momentum/momentumLabel/
              topCounterparty/topShare/nContract/nAmend/nCancel/asOf.
        Prerequisites:
            - allFilings 수집(자동 HF pull). 첫 호출 느릴 수 있음.
        Freshness:
            - allFilings 마지막 수집일(asOf 컬럼).
        Dataflow:
            - scan("orders") → 후보 → Company(stockCode).panel/analysis 후속 검증.
        TargetMarkets:
            - KR (DART/KRX 거래소공시).
    """
    byCompany, lastDate = _collectUniverse(eventType, dateFrom, verbose)
    if not byCompany:
        return pl.DataFrame(schema=_OUTPUT_SCHEMA)

    asOf = _toDate(lastDate) or date.today()
    rows = [_aggregateCompany(code, rs, asOf) for code, rs in byCompany.items() if rs]
    for r in rows:
        r["asOf"] = lastDate
    df = pl.DataFrame(rows, schema_overrides=_OUTPUT_SCHEMA)
    return df.sort("bookToBill", descending=True, nulls_last=True)


__all__ = ["scanOrders"]
