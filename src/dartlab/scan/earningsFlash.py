"""잠정실적 횡단 을 최근 잠정실적 공시(영업(잠정)실적 + 손익구조 변동) 발굴 + 핵심 실적.

scan("ipo") 동형의 라이브 직독 축. allFilings 굽기(일 1회 HF push)에 의존하지 않고
listFilings(거래소공시 I)로 최근 잠정실적 공시를 발굴(``classifyEarningsFlash``)한 뒤,
공시별 본문을 직독해 매출·영업이익·순이익 당기값(원 환산) + 전년동기 증감율을 횡단한다.
시간당 왓처(eval_earnings_flash)의 데이터원이자, 사용자/agent 의 "이번 분기 실적 발표"
류 cross 질문 dispatch 표면.

두 유형 상보: 영업(잠정)실적 공정공시(자발 사전발표) + 매출액/손익구조 변동(의무 수시공시,
자발 안 하는 소형주 서프라이즈). 파싱은 :func:`providers.dart.eventDisclosure.parseEarningsFlash`.
"""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# 발굴 윈도(일). 잠정실적은 시점 이벤트라 짧게(시간당 왓처 lookback 여유). 넓게는 dateFrom.
EARNINGS_WINDOW_DAYS = 2
# deep 본문 fetch 상한 (넓은 dateFrom 방어). 초과분은 로그 후 절단(조용한 절단 금지).
EARNINGS_MAX_DEEP = 300

_OUTPUT_SCHEMA = {
    "corpName": pl.Utf8,
    "corpCode": pl.Utf8,
    "stockCode": pl.Utf8,
    "rcept": pl.Utf8,
    "rceptDt": pl.Utf8,
    "type": pl.Utf8,
    "basis": pl.Utf8,
    "unit": pl.Utf8,
    "revenue": pl.Float64,
    "revenueYoy": pl.Float64,
    "operatingProfit": pl.Float64,
    "operatingProfitYoy": pl.Float64,
    "netProfit": pl.Float64,
    "netProfitYoy": pl.Float64,
    "pretaxProfit": pl.Float64,
    "pretaxProfitYoy": pl.Float64,
    "asOf": pl.Utf8,
}

_ACCOUNT_COLS = ("revenue", "operatingProfit", "netProfit", "pretaxProfit")


def _discover(client, *, dateFrom: str | None, verbose: bool) -> tuple[list[dict], str]:
    """거래소공시(I) + report_nm 패턴 을 잠정실적 공시 meta list 로. 발굴 SSOT.

    Args:
        dateFrom: ``"YYYYMMDD"`` 이상만 (None=최근 EARNINGS_WINDOW_DAYS 일).
        verbose: 진행 라인 로그.

    Returns:
        (metas, asOf). metas 는 classifyEarningsFlash 통과분(type/basis 부착), asOf=발굴 기준일.
    """
    from dartlab.gather.dart.disclosure import listFilings
    from dartlab.providers.dart.eventDisclosure import classifyEarningsFlash

    if client is None:
        from dartlab.core.dartClient import DartClient

        client = DartClient()

    end = date.today()
    start = end - timedelta(days=EARNINGS_WINDOW_DAYS)
    if dateFrom and len(dateFrom) == 8:
        start = date(int(dateFrom[:4]), int(dateFrom[4:6]), int(dateFrom[6:8]))
    asOf = end.strftime("%Y%m%d")
    df = listFilings(client, start=start.strftime("%Y%m%d"), end=asOf, filingType="I", fetchAll=True)
    if df.height == 0:
        return [], asOf
    metas: list[dict] = []
    for r in df.iter_rows(named=True):
        c = classifyEarningsFlash(r.get("report_nm") or "")
        if not c["isFlash"]:
            continue
        metas.append({**r, "_type": c["type"], "_basis": c["basis"]})
    if verbose:
        _log.info("잠정실적 발굴: %s~%s · %d 건", start, end, len(metas))
    return metas, asOf


def _parseRow(client, meta: dict, asOf: str) -> dict:
    """공시 1 건 을 메타 + 본문 직독 실적(원 환산) row 로."""
    from dartlab.gather.dart.allFilingsCollector import _collectOneRaw
    from dartlab.providers.dart.eventDisclosure import parseEarningsFlash

    row: dict[str, object] = {
        "corpName": meta.get("corp_name"),
        "corpCode": meta.get("corp_code"),
        "stockCode": (meta.get("stock_code") or "").strip(),
        "rcept": meta.get("rcept_no"),
        "rceptDt": meta.get("rcept_dt"),
        "type": meta.get("_type"),
        "basis": meta.get("_basis"),
        "asOf": asOf,
    }
    content, status = _collectOneRaw(client, meta["rcept_no"])
    if status == "ok" and content:
        p = parseEarningsFlash(content, meta.get("report_nm") or "")
        row["unit"] = p["unit"]
        won = p["unitWon"]
        for col in _ACCOUNT_COLS:
            acc = p["accounts"].get(col)
            if acc and acc.get("current") is not None:
                row[col] = acc["current"] * won  # 원 환산
                row[f"{col}Yoy"] = acc.get("yoyPct")
    return row


def scanEarningsFlash(*, dateFrom: str | None = None, deep: bool = True, verbose: bool = True) -> pl.DataFrame:
    """최근 잠정실적 횡단 을 영업(잠정)실적 + 손익구조 변동 발굴 + 매출·영업이익·순이익 + 증감율로.

    최근 윈도우의 거래소공시(I)에서 잠정실적 공시를 발굴(``classifyEarningsFlash`` 패턴,
    전망/예고/안내 제외)하고, 공시별 본문을 직독해 계정별 당기 실적(원 환산)과 전년동기
    (손익구조는 직전연도) 증감율을 횡단한다. 값을 대시로만 낸 공시는 해당 계정이 빠진다.

    Args:
        dateFrom: ``"YYYYMMDD"`` 이상만 (None=최근 2 일, 시간당 왓처 lookback). 넓은 시즌
            조회는 이 값을 과거로. list.json corp_code 미지정 3 개월 제한 안쪽만.
        deep: True 면 공시별 본문 직독해 실적 숫자까지 (공시당 fetch 1). False 면 메타
            (회사명·rcept·type·basis)만 빠르게.
        verbose: 진행 라인 로그.

    Returns:
        pl.DataFrame
            corpName : str
            corpCode : str
            stockCode : str
            rcept : str  잠정실적 공시 접수번호(원문근거)
            rceptDt : str  접수일 YYYYMMDD
            type : str  영업잠정실적 / 손익구조변동
            basis : str  연결 / 별도
            unit : str  본문 표 단위 (deep)
            revenue : float  매출액(원, deep)
            revenueYoy : float  매출 전년동기 증감율%(deep)
            operatingProfit / operatingProfitYoy : float  영업이익(원) + 증감율(deep)
            netProfit / netProfitYoy : float  당기순이익(원) + 증감율(deep)
            pretaxProfit / pretaxProfitYoy : float  세전이익(원) + 증감율(deep)
            asOf : str  발굴 기준일

    Raises:
        없음. listFilings 0 또는 매치 0 시 빈 DataFrame.

    Examples:
        >>> import dartlab  # doctest: +SKIP
        >>> df = dartlab.scan("earningsFlash")  # doctest: +SKIP
        >>> df.select(["corpName", "revenue", "operatingProfitYoy"])  # doctest: +SKIP

    Capabilities:
        - 두 잠정실적 유형 발굴(사람 라벨 0) 후 공시별 본문 직독으로 계정 실적 + 증감율 횡단.
        - 표 단위 원 환산 + 음수(영업손실) 부호 보존.

    AIContext:
        Agent 가 "이번 분기/최근 실적 발표" 류 cross 질문 시 dispatch. 시간당 왓처의 데이터원.

    Guide:
        - 공시당 본문 fetch 1 회 (deep). 넓은 dateFrom 은 느리다. 목록만이면 deep=False.
        - 잠정치라 확정치와 다를 수 있음(공시 자체 경고). 대시 계정은 값 부재(0 아님).

    When:
        분기 실적 시즌 모니터링·잠정실적 서프라이즈 스크리닝 시.

    How:
        ``listFilings(filingType="I")`` 메타 후 ``classifyEarningsFlash`` 필터 후 공시별
        ``_collectOneRaw`` 본문 직독 후 ``parseEarningsFlash`` 후 원 환산.

    Requires:
        - DART_API_KEYS (listFilings + document.xml). allFilings 불요(라이브 직독).
        - ``providers.dart.eventDisclosure.parseEarningsFlash`` 파서.

    SeeAlso:
        - :func:`dartlab.providers.dart.eventDisclosure.parseEarningsFlash`. 단건 본문 파싱.
        - :func:`dartlab.scan.ipo.scanIpo`. 라이브 직독 발굴 동형 패턴.

    LLM Specifications:
        AntiPatterns:
            - 대시 계정을 0 실적으로 오해 (해당 계정 컬럼이 null).
            - 잠정치를 확정 실적으로 단정 (정정·확정에서 바뀔 수 있음).
            - deep=True 로 수개월 dateFrom (본문 fetch 폭증, EARNINGS_MAX_DEEP 절단).
        OutputSchema:
            - corpName/corpCode/stockCode/rcept/rceptDt/type/basis/unit/revenue*/
              operatingProfit*/netProfit*/pretaxProfit*/asOf.
        Prerequisites:
            - DART_API_KEYS. 최근 윈도우(기본 2 일).
        Freshness:
            - asOf (발굴 기준일). 공시 분 단위 실시간.
        Dataflow:
            - scan("earningsFlash") 후 후보 후 parseEarningsFlash 후 원문근거 rcept.
        TargetMarkets:
            - KR (DART/KRX 거래소공시 I 잠정실적).
    """
    metas, asOf = _discover(None, dateFrom=dateFrom, verbose=verbose)
    if not metas:
        return pl.DataFrame(schema=_OUTPUT_SCHEMA)

    if deep and len(metas) > EARNINGS_MAX_DEEP:
        _log.warning(
            "잠정실적 %d 건 > 상한 %d, 최신 %d 건만 deep 파싱", len(metas), EARNINGS_MAX_DEEP, EARNINGS_MAX_DEEP
        )
        metas = sorted(metas, key=lambda m: m.get("rcept_no") or "", reverse=True)[:EARNINGS_MAX_DEEP]

    rows: list[dict] = []
    if deep:
        from dartlab.core.dartClient import DartClient

        client = DartClient()
        for i, meta in enumerate(metas, start=1):
            if verbose:
                _log.info("  [%d/%d] %s 본문 파싱", i, len(metas), meta.get("corp_name"))
            rows.append(_parseRow(client, meta, asOf))
    else:
        for meta in metas:
            rows.append(
                {
                    "corpName": meta.get("corp_name"),
                    "corpCode": meta.get("corp_code"),
                    "stockCode": (meta.get("stock_code") or "").strip(),
                    "rcept": meta.get("rcept_no"),
                    "rceptDt": meta.get("rcept_dt"),
                    "type": meta.get("_type"),
                    "basis": meta.get("_basis"),
                    "asOf": asOf,
                }
            )
    df = pl.DataFrame(rows, schema_overrides=_OUTPUT_SCHEMA)
    # rceptDt desc + basis desc(연결 우선) 로 왓처 slug 첫-승 dedup 이 연결을 택하게.
    return df.sort(["rceptDt", "basis"], descending=[True, True])


__all__ = ["scanEarningsFlash"]
