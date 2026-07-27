"""2-1 수익성 분석 -- 이익의 흐름을 추적한다.

select()로 IS/BS 원본 계정을 가져와서
금액 + 비율 + YoY 변동을 시계열로 보여준다.
"""

from __future__ import annotations

from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get

from typing import Any

from dartlab.analysis.financial.accountSums import sumBorrowings
from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import MAX_RATIO_YEARS, annualColsFromPeriods, toDictBySnakeId

_MAX_YEARS = MAX_RATIO_YEARS


def _yoy(cur, prev) -> float | None:
    """전기대비 증감률 계산.

    Returns
    -------
    float | None
        YoY 변화율 (%). 계산 불가 시 None.
    """
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


from dartlab.core.utils.calc import safePct as _pctOf  # noqa: E402

# ── 이익 구조 시계열 ──


def _isFinancialSector(company) -> bool:
    """금융업(은행/보험/증권) 판별."""
    try:
        sector = getattr(company, "sector", None)
        if sector is not None:
            from dartlab.frame.sector import Sector

            if sector.sector == Sector.FINANCIALS:
                return True
    except (AttributeError, ImportError):
        pass
    return False


@memoizedCalc
def calcMarginTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """이익 구조 시계열 — 매출 → 매출원가 → 매출총이익 → 판관비 → 영업이익 → 순이익.

    Capabilities:
        IS 의 5 마진 단계 (매출 → COGS → GP → SG&A → OP → NI) 시계열을 산출.
        일반/금융업 분기 (금융업은 이자수익 + 금융이익). YoY 변화율 함께
        제공해 마진 압박/개선 추세 식별.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 13 키 dict (revenue, cogs,
              grossProfit/Margin, sga, operatingIncome/Margin, netIncome/Margin
              + 각 YoY)
            - ``displayHints`` (dict): UI 표시 메타 (core 컬럼 + 한국어 라벨)

    Raises:
        없음.

    Example:
        >>> r = calcMarginTrend(Company("005930"))
        >>> r["history"][0]["operatingMargin"], r["history"][0]["grossMargin"]
        (12.5, 35.0)

    Guide:
        마진 추세 (3 년) 가 progressive 개선/악화면 신호 강함. Operating
        margin 안정 (변동 ±2%p) + Net margin 변동 큼 = 영업외 손익 영향
        (한국 회사 흔함). 금융업은 NIM (Net Interest Margin) 별도 분석.

    When:
        "이익 구조가 어떻게 변했나?" 마진 추세 비교가 필요할 때.

    How:
        company.select("IS", [..]) → 5 단계 추출 → YoY 계산 → history dict.

    SeeAlso:
        - ``analyzeProfitability``: 정성 분석 (본 함수 결과 사용)
        - ``calcReturnTrend``: ROE/ROA/ROIC 시계열
        - ``calcMarginWaterfall``: COGS/SG&A 비중 변화 분해

    Requires:
        IS 시계열 (매출/매출원가/판관비/영업이익/당기순이익) ≥ 2 년.

    AIContext:
        history list 의 첫 dict 가 최신 (latest), [1] = 전년. YoY 변화 분석시
        주의 — 일회성 영업외 (자산매각 등) 가 netMargin 만 영향. 마진 5
        단계 함께 보면 영업 구조 + 영업외 영향 분리 가능.

    LLM Specifications:
        AntiPatterns:
            - 매출액 (revenue) 만 보고 성장 단정 — 영업이익 동반 확인 필수.
            - 금융업 (은행/보험) 에 일반 마진 적용 — isFinancial 자동 분기
              되지만 결과 dict 의 cogs/sga 가 0 일 수 있음.
        OutputSchema:
            ``{history: list[dict], displayHints: dict}``.
        Prerequisites:
            IS 시계열 + 일반/금융업 분기 표준 계정.
        Freshness:
            최신 분기 + 5 년 시계열 (annualColsFromPeriods).
        Dataflow:
            IS → 5 마진 단계 추출 → YoY 계산 → displayHints 메타 합성.
        TargetMarkets: KR (DART 표준), US (EDGAR — 일부 표준 계정 매핑 필요).
    """
    isFinancial = _isFinancialSector(company)

    if isFinancial:
        isResult = company.select("IS", ["이자수익", "금융이익", "영업이익", "당기순이익"])
    else:
        isResult = company.select(
            "IS", ["매출액", "매출원가", "매출총이익", "판매비와관리비", "영업이익", "당기순이익"]
        )

    parsed = toDictBySnakeId(isResult)
    if parsed is None:
        return None

    data, periods = parsed

    if isFinancial:
        # 금융업: 금융이익을 revenue 대체 (이자수익은 일부일 뿐)
        rev = data.get("금융이익", {}) or data.get("이자수익", {})
        op = data.get("영업이익", {})
        ni = data.get("당기순이익", {})
        finIncome = data.get("이자수익", {})
    else:
        rev = data.get("매출액", {})
        op = data.get("영업이익", {})
        ni = data.get("당기순이익", {})

    cogs = data.get("매출원가", {}) if not isFinancial else {}
    gp = data.get("매출총이익", {}) if not isFinancial else {}
    sga = data.get("판매비와관리비", {}) if not isFinancial else {}

    yCols = annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None
    history = []
    for i, col in enumerate(yCols):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        r = rev.get(col)
        if r is None or r == 0:
            continue

        _op = op.get(col)
        _ni = ni.get(col)
        _opPrev = op.get(prevCol) if prevCol else None
        _niPrev = ni.get(prevCol) if prevCol else None
        _rPrev = rev.get(prevCol) if prevCol else None

        row: dict = {
            "period": col,
            "revenue": r,
            "revenueYoy": _yoy(r, _rPrev) if prevCol else None,
            "operatingIncome": _op,
            "operatingMargin": _pctOf(_op, r),
            "operatingIncomeYoy": _yoy(_op, _opPrev) if prevCol else None,
            "netIncome": _ni,
            "netMargin": _pctOf(_ni, r),
            "netIncomeYoy": _yoy(_ni, _niPrev) if prevCol else None,
        }

        if isFinancial:
            row["revenueLabel"] = "금융이익"
            row["financialIncome"] = finIncome.get(col)
        else:
            row["cogs"] = cogs.get(col)
            row["grossProfit"] = gp.get(col)
            row["grossMargin"] = _pctOf(gp.get(col), r)
            row["sga"] = sga.get(col)

        history.append(row)

    if not history:
        return None
    result: dict[str, Any] = {"history": history}
    if isFinancial:
        result["isFinancial"] = True

    # Phase 7 G24: 영업마진 변화 driver 분해 — 각 history entry 에 drivers 주입
    # 이전기 대비 원가율/판관비/환율 driver 자동 분해 (McKinsey + Damodaran Ch.11)
    if not isFinancial:
        try:
            from dartlab.analysis.financial.attribution import decomposeMarginChange

            for i in range(len(history) - 1):
                cur = history[i]
                prev = history[i + 1]
                revT = cur.get("revenue")
                rev_t1 = prev.get("revenue")
                cogsT = cur.get("cogs")
                cogs_t1 = prev.get("cogs")
                sgaT = cur.get("sga")
                sga_t1 = prev.get("sga")
                if all(isinstance(v, (int, float)) for v in (revT, rev_t1, cogsT, cogs_t1, sgaT, sga_t1)):
                    attribution = decomposeMarginChange(
                        revenueT=revT,
                        revenueT1=rev_t1,
                        cogsT=cogsT,
                        cogsT1=cogs_t1,
                        sgaT=sgaT,
                        sgaT1=sga_t1,
                    )
                    cur["drivers"] = attribution.get("drivers") or []
                    cur["driversExplained"] = attribution.get("explainedPct")
        except (ImportError, AttributeError, TypeError, ValueError):
            pass

    # Phase 8 A5: turningPoints 헬퍼 1줄
    from dartlab.synth.turningPoint import injectTurningPoints

    result["turningPoints"] = injectTurningPoints(history, seriesKey="operatingMargin", minDeltaPct=25.0)

    # R22-2: AI 가 표 만들 때 핵심 컬럼을 빠뜨리지 않도록 명시.
    result["displayHints"] = {
        "core": ["period", "revenue", "operatingMargin", "netMargin", "grossMargin"],
        "note": "수익성 응답 시 operatingMargin/netMargin/grossMargin 컬럼을 표에 반드시 포함",
    }
    # Phase 15 C1: _showKey 힌트 — AI 가 자율적으로 `panel("IS")` 재검증 호출 가능
    result["_showKey"] = "IS"
    result["_showFields"] = ["매출액", "영업이익", "당기순이익"]
    return result


# ── ROE 분해 (듀퐁 5요소) ──


@memoizedCalc
def calcReturnTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """ROE 5 요소 듀퐁 분해 시계열 — 수익을 어떻게 만드는가.

    Capabilities:
        ROE = 세금부담 × 이자부담 × 영업마진 × 자산회전 × 레버리지 5 요소
        분해 (Penman 듀퐁) + ROE/ROA 절대값. IS/BS 원본 계정에서 직접 산출.
        ROE 변화를 5 요인 중 어디에서 왔는지 attribution.

    Args:
        company: Company 객체.
        basePeriod: 기준 기간. None 시 최신.

    Returns:
        dict | None:
            - ``history`` (list[dict]): 연도별 11 키 (period + netIncome +
              equity + totalAssets + roe + roa + 5 듀퐁 요소).

    Raises:
        없음.

    Example:
        >>> r = calcReturnTrend(Company("005930"))
        >>> r["history"][0]["roe"], r["history"][0]["leverage"]
        (15.0, 2.1)

    Guide:
        ROE 동일 (15%) 이라도 (영업마진 10% × 자산회전 1.5 × 레버리지 1.0)
        vs (영업마진 5% × 자산회전 1.5 × 레버리지 2.0) 는 질이 다르다 —
        후자는 레버리지 의존. 듀퐁 attribution 으로 ROE 변화 원인 추적.

    When:
        "ROE 가 어디서 왔나?" 듀퐁 분해 의도 진입 시.

    How:
        IS+BS 추출 → 듀퐁 5 요소 산식 → history list 반환.

    SeeAlso:
        - ``calcMarginTrend``: 5 마진 단계 시계열
        - ``calcPenmanDecomposition``: Penman RNOA + 재무레버리지 분해
        - ``calcRoicTree``: ROIC = NOPAT/InvestedCapital
        - Damodaran "Investment Valuation" Ch.5

    Requires:
        IS (매출/영업이익/법인세차감전순이익/당기순이익) + BS (자산총계/자본총계).

    AIContext:
        ROE 단년도 + 5 요소 분해 함께. ROE 상승 원인이 영업마진 (질) vs
        레버리지 (위험) 인지 명시. KR 대기업 평균 ROE ~ 10%, US S&P500 ~ 17%.

    LLM Specifications:
        AntiPatterns:
            - ROE 단독 인용 — 듀퐁 5 요소 분해로 질 분리 필요.
            - 금융업에 일반 듀퐁 적용 — NIM/리스크가중자산이익률 별도.
        OutputSchema:
            ``{history: list[dict 11키]}``.
        Prerequisites:
            IS + BS 시계열 ≥ 2 년.
        Freshness:
            분기 + 시계열.
        Dataflow:
            IS → 매출/영업이익/PBT/NI → BS → 자산/자본 → 듀퐁 5 요소 =
            (NI/PBT) × (PBT/OP) × (OP/Rev) × (Rev/TA) × (TA/Eq).
        TargetMarkets: KR (DART), US (EDGAR — 듀퐁 원형 최적).
    """
    isResult = company.select("IS", ["매출액", "영업이익", "법인세차감전순이익", "당기순이익"])
    bsResult = company.select("BS", ["자산총계", "자본총계"])

    isParsed = toDictBySnakeId(isResult)
    bsParsed = toDictBySnakeId(bsResult)
    if isParsed is None or bsParsed is None:
        return None

    isData, isPeriods = isParsed
    bsData, _ = bsParsed

    rev = isData.get("매출액", {})
    opIncome = isData.get("영업이익", {})
    pbt = isData.get("법인세차감전순이익", {})
    niRow = isData.get("당기순이익", {})
    ta = bsData.get("자산총계", {})
    eq = bsData.get("자본총계", {})

    yCols = annualColsFromPeriods(isPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None
    history = []
    for col in yCols:
        r = rev.get(col)
        o = opIncome.get(col)
        p = pbt.get(col)
        n = niRow.get(col)
        a = ta.get(col)
        e = eq.get(col)

        roe = _pctOf(n, e)
        roa = _pctOf(n, a)

        # 듀퐁 5요소 (원본에서 직접)
        taxBurden = round(n / p, 4) if n is not None and p is not None and p != 0 else None
        interestBurden = round(p / o, 4) if p is not None and o is not None and o != 0 else None
        operatingMargin = _pctOf(o, r)
        assetTurnover = round(r / a, 4) if r is not None and a is not None and a != 0 else None
        leverage = round(a / e, 4) if a is not None and e is not None and e != 0 else None

        history.append(
            {
                "period": col,
                "netIncome": n,
                "equity": e,
                "totalAssets": a,
                "roe": roe,
                "roa": roa,
                "taxBurden": taxBurden,
                "interestBurden": interestBurden,
                "operatingMargin": operatingMargin,
                "assetTurnover": assetTurnover,
                "leverage": leverage,
            }
        )

    return {"history": history} if history else None


# ── 마진 워터폴 ──


# ── 플래그 ──


def _marginGapFlags(latest: dict, isFinancial: bool, flags: list[str]) -> None:
    """순이익률과 영업이익률 괴리, 그리고 영업이익률 절대 크기 경고.

    Parameters
    ----------
    latest : dict
        calcMarginTrend history 최신 항목.
    isFinancial : bool
        금융업 여부. 임계와 문구가 달라진다.
    flags : list[str]
        경고 누적. 제자리 변경.
    """
    nm = latest.get("netMargin")
    om = latest.get("operatingMargin")
    if nm is not None and om is not None and om > 0:
        ratio = nm / om
        if isFinancial:
            # 금융업: 금융이익은 순이자+수수료(매출총이익 성격)이므로
            # 영업이익 > 금융이익은 구조적으로 정상.
            # 순이익률이 영업이익률보다 훨씬 낮은 것은 금융비용/충당금 때문.
            if ratio > 3.0:
                flags.append(f"순이익률({nm:.1f}%)이 영업이익률({om:.1f}%)의 {ratio:.1f}배. 비영업이익 확인 필요")
        elif ratio > 2.0:
            flags.append(f"순이익률({nm:.1f}%)이 영업이익률({om:.1f}%)의 {ratio:.1f}배. 대규모 비영업이익 존재")
        elif 0 < ratio < 0.3:
            flags.append(f"순이익률이 영업이익률의 {ratio:.1f}배. 대규모 비영업손실")

    if om is not None and abs(om) > 100:
        if isFinancial:
            flags.append(
                f"금융업 IS 구조: 금융이익 대비 영업이익률 {om:.1f}% (금융이익=순금융수익, 수수료·보험 등 별도 합산)"
            )
        else:
            # 지주사(로열티/지분법 수입 위주)는 영업이익률 100%+ 정상.
            # "데이터 이상"이라고 하면 사용자에게 불필요한 공포 유발.
            flags.append(f"영업이익률 {om:.1f}%. 매출 대비 영업이익이 크다 (지주사·로열티·지분법이익 구조일 수 있음)")


def _returnTrendFlags(h: dict, isFinancial: bool, flags: list[str]) -> None:
    """ROE/ROA/레버리지 조합 경고.

    Parameters
    ----------
    h : dict
        calcReturnTrend history 최신 항목.
    isFinancial : bool
        금융업 여부. 레버리지 임계가 달라진다.
    flags : list[str]
        경고 누적. 제자리 변경.
    """
    roe = h.get("roe")
    roa = h.get("roa")
    lev = h.get("leverage")
    if roe is None or roa is None or lev is None:
        return
    if isFinancial:
        # 금융업은 레버리지 10x+ 가 정상 (은행 자기자본비율 약 8%)
        if roe > 8:
            flags.append(f"양호한 ROE ({roe:.1f}%, 금융업 기준)")
        return
    if lev > 3:
        flags.append(f"ROE의 레버리지 의존도 높음 (자산/자본 = {lev:.1f}배)")
    if roe > 15 and roa > 5 and lev < 2:
        flags.append(f"진성 고수익 (ROE {roe:.1f}%, 낮은 레버리지)")


@memoizedCalc
def calcProfitabilityFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """수익성 경고/기회 플래그.

    Capabilities:
        - 영업이익률 추세 + 듀퐁 요소 극단값 검출.

    Guide:
        3 기 연속 하락 · 적자 · 레버리지 의존 등 텍스트 경고 묶음.

    When:
        "수익성 위험 신호 있나?" 의도 또는 요약 카드 생성 시.

    How:
        calcMarginTrend / calcReturnTrend 결과 소비 → 임계 비교.

    Requires:
        marginTrend · returnTrend 가 동작 가능해야 함.

    Raises:
        없음 (데이터 부재 시 빈 리스트).

    Example:
        >>> calcProfitabilityFlags(c)
        ["영업이익률 3기 연속 하락 (4.2%)", ...]

    See Also:
        - calcMarginTrend : 마진 시계열
        - calcReturnTrend : 듀퐁 분해

    AIContext:
        AI 답변 "수익성 한 줄 평가" 코너의 경고 문구로 직접 사용.

    Returns
    -------
    list[str]
        경고/기회 메시지 리스트. 빈 리스트이면 이상 없음.
    """
    flags: list[str] = []
    isFinancial = _isFinancialSector(company)

    trend = calcMarginTrend(company, basePeriod=basePeriod)
    if trend and len(trend["history"]) >= 3:
        hist = trend["history"]
        # 영업이익률 3기 연속 하락
        oms = [h.get("operatingMargin") for h in hist[:3]]
        if all(v is not None for v in oms) and oms[0] < oms[1] < oms[2]:
            flags.append(f"영업이익률 3기 연속 하락 ({oms[0]:.1f}%)")
        if oms[0] is not None and oms[0] < 0:
            flags.append(f"영업적자 ({oms[0]:.1f}%)")

    # 마진 괴리 감지. 순이익률 vs 영업이익률
    if trend and trend["history"]:
        _marginGapFlags(trend["history"][0], isFinancial, flags)

    if isFinancial:
        flags.append("금융업: ROE·ROA가 핵심 수익성 지표 (마진 분석은 참고용)")

    ret = calcReturnTrend(company, basePeriod=basePeriod)
    if ret and ret["history"]:
        _returnTrendFlags(ret["history"][0], isFinancial, flags)

    return flags


# ── Penman RNOA + FLEV/SPREAD 분해 ──


# ── McKinsey ROIC Tree ──


# 분리된 깊이 분석 (BC re-export)
from dartlab.analysis.financial._profitabilityDeep import (  # noqa: E402, F401
    calcMarginWaterfall,
    calcPenmanDecomposition,
    calcRoicTree,
)
