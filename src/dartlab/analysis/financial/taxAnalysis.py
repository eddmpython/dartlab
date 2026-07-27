"""세금 분석 — 유효세율, 세금 현금화, 이연법인세 시계열.

세금 부담의 실체와 미래 세금 리스크를 시계열로 추적한다.
"""

from __future__ import annotations

from dartlab.core.utils.safe import get as _get

_getF = _getF2 = _getF3 = _getF4 = _get

from dartlab.core.memory import memoizedCalc
from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

_MAX_YEARS = 8


from dartlab.core.utils.calc import safePct as _pct  # noqa: E402

# ── 유효세율 ──


@memoizedCalc
def calcEffectiveTaxRate(company, *, basePeriod: str | None = None) -> dict | None:
    """유효세율 시계열 — 법인세비용/세전이익.

    Capabilities:
        - 연도별 유효세율 + 법정세율 (KR 24%) gap 시계열 + Q4 4 분기 합산 fallback.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history (preTaxIncome/taxExpense/effectiveTaxRate/
        statutoryRate/taxGap) 행 리스트. 데이터 부재 시 None.

    Guide:
        법정세율 24% (KR 대기업 근사). taxGap > 0 = 세금혜택 미적용, < 0 =
        세금 절약 효과.

    When:
        세금 부담 시계열 진단·세전 이익 대비 세금 효율 평가 시.

    How:
        IS rawNormalized 매핑 → annualSumFlow (Q4 fallback) → 비율 계산.

    Requires:
        IS (법인세비용/법인세차감전순이익) 시계열.

    Raises:
        없음.

    Example:
        >>> calcEffectiveTaxRate(Company("005930"))
        {"history": [{"period": "...", "effectiveTaxRate": 22.5, ...}]}

    SeeAlso:
        - ``calcTaxCashConversion``: 현금 납부 비교
        - ``calcDeferredTax``: 이연 잔액

    AIContext:
        AI 답변에서 유효세율·세금 효율 한 줄 인용 시.
    """
    accounts = ["법인세비용", "법인세차감전순이익", "세전이익"]
    isResult = company.select("IS", accounts)
    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    taxRow = isData.get("법인세비용", {})
    ptRow = isData.get("법인세차감전순이익", isData.get("세전이익", {}))

    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None
    # 법정세율 (한국 기준, 2023~)
    statutoryRate = 24.0  # 과세표준 구간에 따라 다르나 대기업 근사

    # Phase 15 A1: Q4 함정 제거 — Q4 fallback 컬럼은 annualSumFlow 로 4분기 합산
    from dartlab.core.utils.flow import annualSumFlow

    allPeriods = set(isPeriods)
    history = []
    for col in yCols:
        ptIncome = annualSumFlow(ptRow, col, allPeriods, withFallback=True) or 0
        taxExpense = annualSumFlow(taxRow, col, allPeriods, withFallback=True) or 0

        effectiveTaxRate = None
        taxGap = None
        if ptIncome > 0:
            effectiveTaxRate = abs(taxExpense) / ptIncome * 100
            taxGap = effectiveTaxRate - statutoryRate

        history.append(
            {
                "period": col,
                "preTaxIncome": ptIncome,
                "taxExpense": taxExpense,
                "effectiveTaxRate": effectiveTaxRate,
                "statutoryRate": statutoryRate,
                "taxGap": taxGap,
            }
        )

    return {"history": history} if history else None


# ── 세금 현금화 ──


@memoizedCalc
def calcTaxCashConversion(company, *, basePeriod: str | None = None) -> dict | None:
    """세금 현금화 시계열 — IS 법인세비용 vs CF 법인세납부.

    Capabilities:
        - 연도별 IS 법인세비용 + CF 법인세납부 + 납부/비용 비율 시계열.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history (taxExpense/taxPaid/taxCashRatio) 행 리스트.
        IS 데이터 부재 시 None.

    Guide:
        taxCashRatio > 150% = 과거 이연분 정산 (과대 납부 패턴). 100% 근처
        = 정상.

    When:
        세금 비용의 현금 뒷받침 여부 추적·이연법인세 정산 패턴 확인 시.

    How:
        IS 법인세비용 + CF income_taxes 매핑 → annualSumFlow 합산 → 비율.

    Requires:
        IS 법인세비용 + CF payments_of_income_taxes.

    Raises:
        없음.

    Example:
        >>> calcTaxCashConversion(Company("005930"))
        {"history": [{"period": "...", "taxCashRatio": 95.2, ...}]}

    SeeAlso:
        - ``calcEffectiveTaxRate``: 유효세율 시계열
        - ``calcDeferredTax``: 이연 잔액

    AIContext:
        AI 답변에서 세금 현금화 한 줄 인용 시.
    """
    isResult = company.select("IS", ["법인세비용"])
    cfResult = company.select("CF", ["payments_of_income_taxes"])

    isParsed = toDictBySnakeId(isResult)
    if isParsed is None:
        return None

    isData, isPeriods = isParsed
    taxExpRow = isData.get("법인세비용", {})

    cfParsed = toDictBySnakeId(cfResult)
    cfData = cfParsed[0] if cfParsed else {}
    taxPaidRow = cfData.get("payments_of_income_taxes", {})

    yCols = annualColsFromPeriods(isPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    # Phase 15 A1: Q4 함정 제거 — annualSumFlow 로 4분기 합산 (Q4 fallback 대응)
    from dartlab.core.utils.flow import annualSumFlow

    allIsPeriods = set(isPeriods)
    cfPeriods = cfParsed[1] if cfParsed else []
    allCfPeriods = set(cfPeriods) if cfPeriods else set()

    history = []
    for col in yCols:
        taxExpVal = annualSumFlow(taxExpRow, col, allIsPeriods, withFallback=True) or 0
        taxExpense = abs(taxExpVal)
        taxPaidVal = annualSumFlow(taxPaidRow, col, allCfPeriods, withFallback=True) if taxPaidRow else None
        taxPaid = abs(taxPaidVal) if taxPaidVal is not None else None

        taxCashRatio = None
        if taxPaid is not None and taxExpense > 0:
            taxCashRatio = taxPaid / taxExpense * 100

        history.append(
            {
                "period": col,
                "taxExpense": taxExpense,
                "taxPaid": taxPaid,
                "taxCashRatio": taxCashRatio,
            }
        )

    return {"history": history} if history else None


# ── 이연법인세 ──


@memoizedCalc
def calcDeferredTax(company, *, basePeriod: str | None = None) -> dict | None:
    """이연법인세 시계열 — 이연자산/부채 추세.

    Capabilities:
        - 이연법인세자산/부채/순이연 + 자산 비중 시계열.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        dict | None: history (deferredTaxAsset/Liability/netDeferredTax/
        dtaToTotalAssets) 행 리스트. 데이터 부재 시 None.

    Guide:
        DTA 급증 = 미래 과세소득 가정 검토 필요. dtaToTotalAssets > 5% =
        실현 가능성 진단 필요.

    When:
        이연법인세 잔액 추세·실현 가능성 진단 시.

    How:
        BS 이연 자산/부채/자산총계 매핑 → 잔액 + 비중 시계열.

    Requires:
        BS 이연법인세 자산·부채·자산총계.

    Raises:
        없음.

    Example:
        >>> calcDeferredTax(Company("005930"))
        {"history": [{"period": "...", "netDeferredTax": 12345, ...}]}

    SeeAlso:
        - ``calcEffectiveTaxRate``: 유효세율 시계열
        - ``calcTaxCashConversion``: 현금 납부

    AIContext:
        AI 답변에서 이연법인세 추세 인용 시.
    """
    bsResult = company.select("BS", ["이연법인세자산", "이연법인세부채", "자산총계"])
    bsParsed = toDictBySnakeId(bsResult)
    if bsParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    dtaRow = bsData.get("deferred_tax_assets", {})
    dtlRow = bsData.get("deferred_tax_liabilities", {})
    taRow = bsData.get("assets", {})

    yCols = annualColsFromPeriods(bsPeriods, basePeriod=basePeriod, maxYears=_MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        dta = _get(dtaRow, col)
        dtl = _get(dtlRow, col)
        ta = _get(taRow, col)
        netDt = dta - dtl

        history.append(
            {
                "period": col,
                "deferredTaxAsset": dta,
                "deferredTaxLiability": dtl,
                "netDeferredTax": netDt,
                "dtaToTotalAssets": _pct(dta, ta),
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def _effectiveTaxRateFlags(history: list[dict], flags: list[str]) -> None:
    """유효세율 수준·구조적 혜택·변동성 3 신호.

    Parameters
    ----------
    history : list[dict]
        calcEffectiveTaxRate history (최신 먼저, 비어있지 않음).
    flags : list[str]
        경고 누적. 제자리 변경.
    """
    h0 = history[0]
    rate = h0.get("effectiveTaxRate")
    statutory = h0.get("statutoryRate", 24.0)
    if rate is None:
        return

    if rate < 10:
        flags.append(f"유효세율 {rate:.1f}%. 극저세율 (세금 혜택 또는 이연)")
    elif rate > 35:
        flags.append(f"유효세율 {rate:.1f}%. 고세율 (추가 세금 부담)")

    # 법정세율의 50% 미만이 3기 연속이면 구조적 세금혜택 의존
    if len(history) >= 3:
        lowTaxYears = sum(
            1 for h in history[:3] if h.get("effectiveTaxRate") is not None and h["effectiveTaxRate"] < statutory * 0.5
        )
        if lowTaxYears >= 3:
            flags.append("유효세율 3기 연속 법정세율의 50% 미만. 세금혜택 구조적 의존")

    # 유효세율 변동성
    rates = [h.get("effectiveTaxRate") for h in history[:5] if h.get("effectiveTaxRate") is not None]
    if len(rates) >= 3:
        mean = sum(rates) / len(rates)
        if mean > 0:
            std = (sum((r - mean) ** 2 for r in rates) / len(rates)) ** 0.5
            cv = std / mean
            if cv > 0.5:
                flags.append(f"유효세율 변동계수 {cv:.2f}. 세금 비용 불안정")


def _deferredTaxFlags(hist: list[dict], flags: list[str]) -> None:
    """이연법인세자산 급증·연속 증가 2 신호.

    Parameters
    ----------
    hist : list[dict]
        calcDeferredTax history (최신 먼저, 2 개 이상).
    flags : list[str]
        경고 누적. 제자리 변경.
    """
    dta0 = hist[0].get("deferredTaxAsset")
    dta1 = hist[1].get("deferredTaxAsset")
    if dta0 is not None and dta1 is not None and dta1 > 0 and dta0 / dta1 > 2:
        flags.append(f"이연법인세자산 {dta0 / dta1:.1f}배 급증. 미래 과세소득 가정 검토")

    # 이연법인세자산 3기 연속 증가
    if len(hist) >= 3:
        dtas = [h.get("deferredTaxAsset") for h in hist[:3]]
        if all(v is not None for v in dtas) and dtas[0] > dtas[1] > dtas[2] > 0:
            flags.append("이연법인세자산 3기 연속 증가. 실현 가능성 점검 필요")


@memoizedCalc
def calcTaxFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """세금 관련 경고 신호.

    Capabilities:
        - 극저/고세율, 세금혜택 구조적 의존, 세율 변동성, 세금현금 과대납부,
          이연법인세 급증/연속 증가 등을 한국어 flags 산출.

    Args:
        company: 분석 대상 기업.
        basePeriod: 기준 기간.

    Returns:
        list[str]: 한국어 경고 메시지. 임계 미달 시 빈 리스트.

    Guide:
        임계 — 유효세율 < 10% 또는 > 35%, 법정세율 50% 미만 3 기 연속,
        변동계수 > 0.5, taxCashRatio > 150%, DTA 2x+ 급증.

    When:
        보고서·UI 위험 배너에 세금 관련 경고 한 줄 표시.

    How:
        ``calcEffectiveTaxRate`` + ``calcTaxCashConversion`` + ``calcDeferredTax``
        결과를 임계와 비교 후 한국어 포맷팅.

    Requires:
        하위 3 calc 가용성.

    Raises:
        없음.

    Example:
        >>> calcTaxFlags(Company("005930"))
        ["유효세율 8.1% — 극저세율 ..."]

    SeeAlso:
        - ``calcEffectiveTaxRate``: 본 함수 입력

    AIContext:
        AI 답변에서 세금 리스크 한 줄 인용 시.
    """
    flags = []

    etr = calcEffectiveTaxRate(company, basePeriod=basePeriod)
    if etr and etr["history"]:
        _effectiveTaxRateFlags(etr["history"], flags)

    cashConv = calcTaxCashConversion(company, basePeriod=basePeriod)
    if cashConv and cashConv["history"]:
        h0 = cashConv["history"][0]
        tcr = h0.get("taxCashRatio")
        if tcr is not None and tcr > 150:
            flags.append(f"세금현금비율 {tcr:.0f}%. 법인세 과대 납부 (과거 이연분 정산)")

    deferred = calcDeferredTax(company, basePeriod=basePeriod)
    if deferred and len(deferred["history"]) >= 2:
        _deferredTaxFlags(deferred["history"], flags)

    return flags
