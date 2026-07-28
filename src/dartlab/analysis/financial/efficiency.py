"""2-4 효율성 분석 -- 자산을 얼마나 빨리 돌리는가.

select()로 IS/BS 원본 계정을 가져와서
회전율 + CCC를 금액과 함께 보여준다.
재고가 쌓이는지, 매출채권 회수가 느려지는지를 금액으로 파악.
"""

from __future__ import annotations

from dartlab.analysis.financial._seriesMath import _yoy
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, toDictBySnakeId
from dartlab.core.utils.helpers import annualColsFromPeriods as _annualColsFromPeriods

_MAX_YEARS = MAX_RATIO_YEARS


def _turnover(revenue, balance) -> float | None:
    """회전율 계산 (매출 / 잔액).

    Returns
    -------
    float | None
        회전율 (배). 계산 불가 시 None.
    """
    if revenue is None or balance is None or balance == 0:
        return None
    return round(revenue / balance, 2)


def _days(revenue, balance) -> float | None:
    """회전일수 계산 (잔액 / 매출 × 365).

    Returns
    -------
    float | None
        회전일수 (일). 계산 불가 시 None.
    """
    if revenue is None or balance is None or revenue == 0:
        return None
    return round(balance / revenue * 365, 1)


# ── 자산 회전 ──


@memoizedCalc
def calcTurnoverTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """자산 회전 시계열 — 회전율 4 종 + DSO/DIO/DPO + CCC (현금전환주기).

    Capabilities:
        자산 효율성 4 종 (총자산회전율, 매출채권/재고/매입채무 회전율) 시계열
        + DSO (Days Sales Outstanding) + DIO (Days Inventory Outstanding) +
        DPO (Days Payable Outstanding) + CCC (Cash Conversion Cycle) 산출.
        Damodaran/Penman 의 운전자본 효율성 분석.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 14 키:
                period + revenue + totalAssets + receivables/inventory/payables
                + 4 회전율 + DSO/DIO/DPO + CCC

    Raises:
        없음.

    Example:
        >>> r = calcTurnoverTrend(Company("005930"))
        >>> r["history"][0]["dso"], r["history"][0]["ccc"]
        (45, 30)  # 매출채권 45 일, CCC 30 일

    Guide:
        CCC = DSO + DIO - DPO. CCC 짧음 (< 0 = 마이너스 CCC) = 운전자본
        효율 매우 우수 (Apple/Amazon). CCC 증가 추세 = 운전자본 부담 (재고
        쌓임 또는 매출채권 회수 지연). KR 제조업 평균 CCC ~ 60~90 일.

    When:
        "운전자본 효율 추세?" 운전자본/회전율 의도 진입 시.

    How:
        IS+BS 추출 → 회전율 4 종 → DSO/DIO/DPO/CCC → history dict.

    SeeAlso:
        - ``calcWorkingCapital``: 운전자본 절대값 시계열
        - ``calcAssetStructure``: 자산 영업/비영업 분리
        - ``calcInventoryDivergence``: 재고 신호 (predictionSignals)

    Requires:
        IS (매출/매출원가) + BS (자산/채권/재고/매입채무) ≥ 2 년.

    AIContext:
        CCC 시계열 추세 함께 노출 — 단년도 절대값 < 추세 변화가 더 informative.
        매출채권/재고 YoY 도 함께 (revenue YoY 보다 빠르게 증가 시 운전자본
        부담 신호).

    LLM Specifications:
        AntiPatterns:
            - DSO 단독 인용 — DPO 와 함께 확인 (큰 회사는 supplier 협상력으로
              DPO 늘려 CCC 단축).
            - 단년도 CCC 비교 — 동종 업종 평균 (calcCagrComparison) 필요.
        OutputSchema:
            ``{history: list[dict 14키]}``.
        Prerequisites:
            IS + BS 시계열 + 매출채권/재고/매입채무 표준 계정.
        Freshness:
            최신 분기 + 시계열.
        Dataflow:
            IS → revenue + 매출원가 + BS → AR/Inv/AP → 4 회전율 → DSO/DIO/DPO
            → CCC.
        TargetMarkets: KR (DART 표준 계정), US (EDGAR 동일 표준).
    """
    isResult = company.select("IS", ["매출액", "매출원가"])
    bsResult = company.select(
        "BS", ["자산총계", "매출채권", "매출채권및기타채권", "재고자산", "매입채무", "매입채무및기타채무"]
    )

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("매출액", {})
    cogs = isData.get("매출원가", {})
    ta = bsData.get("자산총계", {})
    ar = bsData.get("매출채권", {}) or bsData.get("매출채권및기타채권", {})
    inv = bsData.get("재고자산", {})
    ap = bsData.get("매입채무", {}) or bsData.get("매입채무및기타채무", {})

    yCols = _annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS + 1)
    if len(yCols) < 2:
        return None
    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        r = rev.get(col)
        c = cogs.get(col)

        arVal = ar.get(col)
        invVal = inv.get(col)
        apVal = ap.get(col)
        taVal = ta.get(col)

        # 회전율
        totalAssetTurnover = _turnover(r, taVal)
        receivablesTurnover = _turnover(r, arVal)
        inventoryTurnover = _turnover(c, invVal)  # COGS 기준

        # CCC 구성 (일수)
        dso = _days(r, arVal)
        dio = _days(c, invVal)
        dpo = _days(c, apVal)
        ccc = round(dso + dio - dpo, 1) if dso is not None and dio is not None and dpo is not None else None

        history.append(
            {
                "period": col,
                "revenue": r,
                "totalAssets": taVal,
                "receivables": arVal,
                "receivablesYoy": _yoy(arVal, ar.get(prevCol)) if prevCol else None,
                "inventory": invVal,
                "inventoryYoy": _yoy(invVal, inv.get(prevCol)) if prevCol else None,
                "payables": apVal,
                "totalAssetTurnover": totalAssetTurnover,
                "receivablesTurnover": receivablesTurnover,
                "inventoryTurnover": inventoryTurnover,
                "dso": dso,
                "dio": dio,
                "dpo": dpo,
                "ccc": ccc,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


@memoizedCalc
def calcEfficiencyFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """효율성 경고/기회 플래그.

    Capabilities:
        - 회전율 하락 · 재고 급증 · CCC 악화 등 경고 텍스트 산출.

    Guide:
        calcTurnoverTrend history 비교로 추세 신호 검출.

    When:
        대시보드 "효율성 신호" 카드 또는 요약 답변 합성 시.

    How:
        turnoverTrend 호출 → 회전율/CCC YoY 비교 → 임계 통과 시 push.

    Requires:
        calcTurnoverTrend 가 history ≥ 2 년 반환.

    Raises:
        없음 (데이터 부재 시 빈 리스트).

    Example:
        >>> calcEfficiencyFlags(c)
        ["총자산회전율 3기 연속 하락 (0.45회)", ...]

    See Also:
        - calcTurnoverTrend : 회전율 시계열 원천
        - calcSummaryFlags : 통합 flags

    AIContext:
        AI 가 "효율성 신호" 코너에서 경고 문장으로 직접 인용.

    Returns
    -------
    list[str]
        경고/기회 플래그 문자열 목록.
    """
    flags: list[str] = []

    trend = calcTurnoverTrend(company, basePeriod=basePeriod)
    if trend is None or len(trend["history"]) < 2:
        return flags

    hist = trend["history"]

    # 총자산회전율 3기 연속 하락
    if len(hist) >= 3:
        tats = [h.get("totalAssetTurnover") for h in hist[:3]]
        if all(v is not None for v in tats) and tats[0] < tats[1] < tats[2]:
            flags.append(f"총자산회전율 3기 연속 하락 ({tats[0]:.2f}회)")

    # 재고 급증 (매출 대비)
    h0, h1 = hist[0], hist[1]
    invYoy = h0.get("inventoryYoy")
    revYoy = h0.get("revenue")
    revPrev = h1.get("revenue")
    if invYoy is not None and revPrev is not None and revPrev > 0:
        _yoy(revYoy, revPrev)
        # 여기서는 이미 계산된 inventoryYoy 사용
        if invYoy is not None and invYoy > 20:
            flags.append(f"재고자산 +{invYoy:.0f}% 급증")

    # CCC
    if len(hist) >= 2:
        ccc0 = hist[0].get("ccc")
        ccc1 = hist[1].get("ccc")
        if ccc0 is not None and ccc1 is not None:
            diff = ccc0 - ccc1
            if diff > 20:
                flags.append(f"CCC {diff:.0f}일 악화 ({ccc0:.0f}일)")
            if ccc0 < 0:
                flags.append(f"CCC {ccc0:.0f}일 -- 운전자본 유리 구조")

    return flags
