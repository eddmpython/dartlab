"""하방 시나리오 자동 민감도. OPM/매출/금리 shock 시 핵심 지표 변화.

"만약 OPM이 5%p 떨어지면?" "매출이 15% 줄면?" "금리가 2%p 오르면?"
각 shock별로 ROE, FCF 커버리지, 이자보상배율 등 핵심 output을 재계산하여
보고서에 리스크/안전마진을 명시한다.

Returns
-------
dict
    baseCase : dict. 현재 핵심 지표
    shocks : dict. 시나리오별 영향
    criticalAssumptions : list[str]. 핵심 가정 목록
    breakdownPoint : dict | None. 손익분기 한계점
"""

from __future__ import annotations

from dartlab.core.memory import memoizedCalc


# 레버 이름에 이미 나가 있는 긴 줄표 (U+2014). 문자열 내용이 곧 반환 계약이라 바꾸지 않고,
# 소스에는 리터럴을 남기지 않으려 코드포인트로 고정한다 (신규 문구에는 쓰지 않는다).
def _latestAnnualRow(company, topic: str, keys: list[str], *, basePeriod: str | None) -> dict | None:
    """최신 연간 컬럼 1 개에서 요청 계정 원값을 뽑는다.

    IS/BS/CF 세 곳이 "select → toDictBySnakeId → annualColsFromPeriods[0] → 계정 조회"
    라는 같은 절차를 계정명만 바꿔 반복하고 있었다. 원값 그대로 돌려주는 이유는
    float 변환 시점이 축마다 다르기 때문이다 (CF 는 ocf 가 있을 때만 capex 를 변환한다).

    Returns
    -------
    dict | None
        {계정 snakeId: 원값}. 조회 실패 또는 연간 컬럼 부재 시 None.
    """
    from dartlab.core.utils.helpers import annualColsFromPeriods, toDictBySnakeId

    parsed = toDictBySnakeId(company.select(topic, keys))
    if parsed is None:
        return None
    data, periods = parsed
    cols = annualColsFromPeriods(periods, basePeriod=basePeriod, maxYears=1)
    if not cols:
        return None
    col = cols[0]
    return {key: data.get(key, {}).get(col) for key in keys}


def _asFloat(value) -> float | None:
    """None 은 그대로 두고 값만 float 로 승격한다."""
    return float(value) if value is not None else None


def _round1(value) -> float | None:
    """0 과 None 을 함께 None 으로 접는 소수 1 자리 반올림 (표시용 관용구)."""
    return round(value, 1) if value else None


@memoizedCalc
def calcScenarioSensitivity(company, *, basePeriod: str | None = None) -> dict | None:
    """핵심 지표 3-shock 민감도 분석.

    Capabilities:
        - OPM -5pp · 매출 -15% · 금리 +2pp 3 시나리오 결과 산출.

    Guide:
        baseCase + 3 shock 결과 + critical assumption + breakdown point.

    When:
        "악조건이면?" 스트레스 시나리오 질의 진입 시.

    How:
        IS/BS 최신값 추출 → 3 shock 적용 → 지표 재계산.

    Requires:
        IS (sales/op/ni/interest) + BS (equity/liabilities).

    Raises:
        없음 (필수 슬롯 부재 시 None).

    Example:
        >>> calcScenarioSensitivity(c)["shocks"]["opm_minus_5pp"]
        {"opm": ..., "roe": ..., ...}

    See Also:
        - calcImprovementLevers : 호조건 개선 lever
        - calcValuationBand : 멀티플 시나리오

    AIContext:
        AI 답변 "스트레스 테스트 결과" 카드의 핵심 evidence.

    Returns
    -------
    dict | None
        baseCase : dict
            opm : float. 영업이익률 (%)
            roe : float. ROE (%)
            interestCoverage : float. 이자보상배율
            debtRatio : float. 부채비율 (%)
            fcf : float. FCF (원)
        shocks : dict
            opm_minus_5pp : dict. OPM -5%p 시
            revenue_minus_15pct : dict. 매출 -15% 시
            interest_plus_2pp : dict. 금리 +2%p 시
        criticalAssumptions : list[str]
        breakdownPoint : dict | None
    """
    isRow = _latestAnnualRow(
        company,
        "IS",
        [
            "sales",
            "operating_income",
            "net_profit",
            "interest_expense",
            "finance_cost",
        ],
        basePeriod=basePeriod,
    )
    if isRow is None:
        return None

    revenue = _asFloat(isRow["sales"])
    opIncome = _asFloat(isRow["operating_income"])
    ni = _asFloat(isRow["net_profit"])
    # 이자비용 다중 키 fallback
    interest = _asFloat(isRow["interest_expense"]) or _asFloat(isRow["finance_cost"])
    if interest is None and opIncome is not None and ni is not None:
        interest = opIncome - ni  # 조세+이자 합산 근사

    if revenue is None or opIncome is None:
        return None

    opm = opIncome / revenue * 100 if revenue else None

    bsRow = _latestAnnualRow(company, "BS", ["total_equity", "total_liabilities"], basePeriod=basePeriod)
    equity = _asFloat(bsRow["total_equity"]) if bsRow else None
    debtTotal = _asFloat(bsRow["total_liabilities"]) if bsRow else None

    roe = ni / equity * 100 if ni and equity and equity > 0 else None
    debtRatio = debtTotal / equity * 100 if debtTotal and equity and equity > 0 else None
    interestAbs = abs(float(interest)) if interest else 0
    ic = opIncome / interestAbs if interestAbs > 0 else None

    cfRow = _latestAnnualRow(
        company,
        "CF",
        ["operating_cashflow", "purchase_of_property_plant_and_equipment"],
        basePeriod=basePeriod,
    )
    fcf = None
    if cfRow is not None:
        ocf = cfRow["operating_cashflow"]
        capex = cfRow["purchase_of_property_plant_and_equipment"]
        if ocf is not None:
            fcf = float(ocf) - abs(float(capex or 0))

    baseCase = {
        "opm": _round1(opm),
        "roe": _round1(roe),
        "interestCoverage": _round1(ic),
        "debtRatio": _round1(debtRatio),
        "fcf": fcf,
        # 내부 값 (calcImprovementLevers에서 재사용)
        "_revenue": revenue,
        "_op_income": opIncome,
        "_equity": equity,
        "_interest_abs": interestAbs,
        "_cash": None,  # 추후 BS에서 채움
    }

    # 세 shock 은 서로 독립한 규칙이라 각자 자기 게이트를 들고 나간다. 성립하지 않는
    # shock 만 None 으로 빠지고 dict 삽입 순서는 여기서 고정된다.
    shocks = {}
    opmShock = _shockOperatingMargin(revenue, opm, interestAbs, equity)
    if opmShock is not None:
        shocks["opm_minus_5pp"] = opmShock
    revenueShock = _shockRevenue(revenue, opm, interestAbs, equity)
    if revenueShock is not None:
        shocks["revenue_minus_15pct"] = revenueShock
    rateShock = _shockInterestRate(opIncome, interestAbs, debtTotal, equity)
    if rateShock is not None:
        shocks["interest_plus_2pp"] = rateShock

    return {
        "baseCase": baseCase,
        "shocks": shocks,
        "criticalAssumptions": _criticalAssumptions(revenue, opm, ic),
        "breakdownPoint": _breakdownPoint(revenue, opm, interestAbs),
    }


def _shockOperatingMargin(revenue, opm, interestAbs, equity) -> dict | None:
    """Shock 1: OPM -5%p. 성립하지 않으면 None."""
    if opm is None or not revenue:
        return None
    shockedOpm = opm - 5
    shockedOp = revenue * shockedOpm / 100
    shockedNi = shockedOp - interestAbs if interestAbs else shockedOp * 0.75
    shockedRoe = shockedNi / equity * 100 if equity and equity > 0 else None
    shockedIc = shockedOp / interestAbs if interestAbs > 0 else None
    return {
        "opm": round(shockedOpm, 1),
        "roe": _round1(shockedRoe),
        "interestCoverage": _round1(shockedIc),
        "verdict": _verdictOpm(shockedOpm, shockedIc),
    }


def _shockRevenue(revenue, opm, interestAbs, equity) -> dict | None:
    """Shock 2: 매출 -15%. 마진율은 유지하고 절대액만 줄인다."""
    if not revenue or opm is None:
        return None
    shockedRev = revenue * 0.85
    shockedOp = shockedRev * opm / 100
    shockedNi = shockedOp - interestAbs if interestAbs else shockedOp * 0.75
    shockedRoe = shockedNi / equity * 100 if equity and equity > 0 else None
    shockedIc = shockedOp / interestAbs if interestAbs > 0 else None
    return {
        "revenue_change": "-15%",
        "opm": round(opm, 1),
        "roe": _round1(shockedRoe),
        "interestCoverage": _round1(shockedIc),
        "verdict": _verdictRev(shockedIc),
    }


def _shockInterestRate(opIncome, interestAbs, debtTotal, equity) -> dict | None:
    """Shock 3: 금리 +2%p. 총부채 전액이 재조달된다고 본 상한 시나리오."""
    if not (interestAbs > 0 and debtTotal and debtTotal > 0):
        return None
    additionalInterest = debtTotal * 0.02
    shockedInterest = interestAbs + additionalInterest
    shockedIc = opIncome / shockedInterest if shockedInterest > 0 else None
    shockedNi = opIncome - shockedInterest
    shockedRoe = shockedNi / equity * 100 if equity and equity > 0 else None
    return {
        "additionalInterest": round(additionalInterest),
        "interestCoverage": _round1(shockedIc),
        "roe": _round1(shockedRoe),
        "verdict": _verdictRate(shockedIc),
    }


def _criticalAssumptions(revenue, opm, ic) -> list[str]:
    """baseCase 가 암묵적으로 깔고 있는 전제를 문장으로 노출한다."""
    assumptions = []
    if opm and opm > 10:
        assumptions.append(f"OPM {opm:.0f}%+ 유지")
    if revenue:
        assumptions.append("매출 성장 > 0")
    if ic and ic > 3:
        assumptions.append("금리 상승 제한적")
    return assumptions


def _breakdownPoint(revenue, opm, interestAbs) -> dict | None:
    """이자비용을 겨우 감당하는 OPM 한계점과 현재 여유폭."""
    if not (revenue and interestAbs > 0):
        return None
    breakevenOpm = interestAbs / revenue * 100
    safety = opm - breakevenOpm if opm else None
    return {
        "metric": "opm",
        "value": round(breakevenOpm, 1),
        "meaning": "이자 비용 감당 한계점",
        "safetyMargin": _round1(safety),
    }


def calcImprovementLevers(company, *, basePeriod: str | None = None) -> dict | None:
    """개선 레버 시뮬레이션. 각 레버별 영향도 계산 + 우선순위.

    "진단"이 아니라 "처방". 이 회사가 어떻게 하면 좋아지는가.
    scenarioSensitivity의 baseCase 재사용 + 상방 시나리오 5종 계산.

    Capabilities:
        - 매출원가/판관비/회전율 등 lever 별 효과 정렬.

    Guide:
        difficulty (easy/medium/hard) + timeframe + effect 합성.

    When:
        "어떻게 좋아질 수 있나?" 처방 의도 진입 시.

    How:
        scenarioSensitivity baseCase 재사용 → 5 lever 시뮬레이션 → 정렬.

    Requires:
        calcScenarioSensitivity 가 baseCase 반환해야 동작.

    Raises:
        없음 (base 부재 시 None).

    Example:
        >>> calcImprovementLevers(c)["topLever"]
        "cogs_reduction_3pp"

    See Also:
        - calcScenarioSensitivity : 하방 시나리오 페어
        - calcMarginWaterfall : 비용 분해

    AIContext:
        AI 답변 "개선 처방" 코너의 우선순위 정렬에 직접 사용.

    Returns
    -------
    dict | None
        baseCase : dict. 현재 핵심 지표
        levers : list[dict]. 개선 레버 (영향도 순 정렬)
            name : str. 레버 이름
            driver : str. 레버 키
            impact : dict. 개선 후 지표
            difficulty : str. easy/medium/hard
            timeframe : str
        topLever : str. 가장 효과 큰 레버 driver
    """
    ss = calcScenarioSensitivity(company, basePeriod=basePeriod)
    if not ss:
        return None

    base = ss.get("baseCase", {})
    if not base:
        return None

    revenue = base.get("_revenue")
    opIncome = base.get("_op_income")
    equity = base.get("_equity")
    interestAbs = base.get("_interest_abs", 0)
    fcf = base.get("fcf")
    opm = base.get("opm")
    roe = base.get("roe")

    # baseCase에 내부 값이 없으면 포기 (company.select 추가 호출 금지. 메모리 압박 방어)
    if revenue is None:
        return None

    if not revenue or revenue <= 0:
        return None

    # 상시 레버 4 종. 레버 1·2 는 마진 개선폭과 라벨만 다른 같은 계산이라 한 빌더로 합쳤다.
    levers = []
    for lever in (
        _marginCostLever(
            revenue,
            opIncome,
            opm,
            fcf,
            equity,
            interestAbs,
            deltaPp=3,
            name="매출원가 3%p 절감",
            driver="cogs_reduction_3pp",
            difficulty="medium",
            period="1-2년",
        ),
        _marginCostLever(
            revenue,
            opIncome,
            opm,
            fcf,
            equity,
            interestAbs,
            deltaPp=2,
            name="판관비 2%p 절감",
            driver="sga_reduction_2pp",
            difficulty="easy",
            period="6개월-1년",
        ),
        _revenueGrowthLever(revenue, opm, equity, interestAbs),
        _debtReductionLever(revenue, opIncome, interestAbs),
    ):
        if lever is not None:
            levers.append(lever)

    # ── 기업유형별 특수 레버 (storyTemplate 연동) ──
    situational = _situationalLevers(company, base, revenue, opIncome, opm, fcf, equity, interestAbs)
    levers.extend(situational)

    # 영향도 순 정렬
    levers.sort(key=lambda x: x.get("effect_score", 0), reverse=True)
    for lv in levers:
        lv.pop("effect_score", None)

    # 기업유형 라벨
    templateName = None
    try:
        from dartlab.analysis.financial.companyType import detectTemplate

        templateName = detectTemplate(company)
    except (ImportError, AttributeError):
        pass

    return {
        "baseCase": base,
        "levers": levers,
        "topLever": levers[0]["driver"] if levers else None,
        "companyType": templateName,
    }


def _marginCostLever(
    revenue,
    opIncome,
    opm,
    fcf,
    equity,
    interestAbs,
    *,
    deltaPp: int,
    name: str,
    driver: str,
    difficulty: str,
    period: str,
) -> dict | None:
    """비용 절감형 레버 (매출원가·판관비 공통). 개선폭과 라벨만 인자로 갈린다."""
    if opm is None:
        return None
    improvedOpm = opm + deltaPp
    improvedOp = revenue * improvedOpm / 100
    improvedNi = improvedOp - interestAbs if interestAbs else improvedOp * 0.75
    improvedRoe = improvedNi / equity * 100 if equity and equity > 0 else None
    fcfChange = ((improvedOp - opIncome) / abs(fcf) * 100) if fcf and fcf != 0 else None
    return {
        "name": name,
        "driver": driver,
        "impact": {
            "opm": round(improvedOpm, 1),
            "roe": _round1(improvedRoe),
            "fcf_change_pct": round(fcfChange, 0) if fcfChange else None,
        },
        "difficulty": difficulty,
        "timeframe": period,
        "effect_score": abs(fcfChange) if fcfChange else 0,
    }


def _revenueGrowthLever(revenue, opm, equity, interestAbs) -> dict | None:
    """레버 3: 매출 10% 성장. 고정비는 그대로 두고 변동비만 비례 증가시킨다."""
    if opm is None or not revenue:
        return None
    grownRev = revenue * 1.10
    # 고정비 부분은 불변 → 변동비만 증가
    variableCost = revenue * (1 - opm / 100)
    grownOp = grownRev - variableCost * 1.10  # 변동비 비례 증가
    grownOpm = grownOp / grownRev * 100
    grownNi = grownOp - interestAbs if interestAbs else grownOp * 0.75
    grownRoe = grownNi / equity * 100 if equity and equity > 0 else None
    return {
        "name": "매출 10% 성장",
        "driver": "revenue_growth_10pct",
        "impact": {
            "opm": round(grownOpm, 1),
            "roe": _round1(grownRoe),
        },
        "difficulty": "hard",
        "timeframe": "2-3년",
        "effect_score": abs(grownOpm - opm) if opm else 0,
    }


def _debtReductionLever(revenue, opIncome, interestAbs) -> dict | None:
    """레버 4: 부채 30% 감축. 이자비용 절감액을 매출 대비 비율로 점수화한다."""
    if not (interestAbs > 0 and opIncome):
        return None
    reducedInterest = interestAbs * 0.70
    improvedIc = opIncome / reducedInterest if reducedInterest > 0 else None
    saved = interestAbs - reducedInterest
    return {
        "name": "부채 30% 감축",
        "driver": "debt_reduction_30pct",
        "impact": {
            "interestCoverage": _round1(improvedIc),
            "interestSaved": round(saved),
        },
        "difficulty": "medium",
        "timeframe": "2-3년",
        "effect_score": saved / revenue * 100 if revenue else 0,
    }


def _situationalLevers(company, base, revenue, opIncome, opm, fcf, equity, interestAbs) -> list[dict]:
    """기업 상태별 특수 레버 5 종.

    다섯 규칙은 서로 의존이 없어 각자 자기 게이트를 들고 dict 또는 None 을 낸다.
    현금 소진·재투자 두 규칙만 `company.select` 를 타므로 평가 순서는 그대로 지킨다.
    """
    candidates = (
        _breakevenLever(revenue, opIncome, opm, interestAbs),
        _dividendExpansionLever(base, fcf, equity),
        _cashRunwayLever(company, base, opm, fcf),
        _cycleDefenseLever(revenue, opm, interestAbs),
        _reinvestmentLever(company, revenue, opm, equity),
    )
    return [lever for lever in candidates if lever is not None]


def _breakevenLever(revenue, opIncome, opm, interestAbs) -> dict | None:
    """적자 기업: 흑자 전환에 필요한 매출 수준."""
    # NaN 마진에서 원본과 같이 빠지도록 부등호를 뒤집지 않고 통째로 부정한다.
    if not (opm is not None and opm < 0 and revenue):
        return None
    breakevenRev = interestAbs / 0.05 if interestAbs > 0 else abs(opIncome) / 0.10  # OPM 5% 가정
    growthNeeded = (breakevenRev - revenue) / revenue * 100 if revenue > 0 else None
    return {
        "name": f"흑자 전환. 매출 {growthNeeded:+.0f}% 필요 (OPM 5% 가정)" if growthNeeded else "흑자 전환 경로",
        "driver": "breakeven_revenue",
        "impact": {
            "breakeven_revenue": round(breakevenRev),
            "required_growth": _round1(growthNeeded),
        },
        "difficulty": "hard",
        "timeframe": "2-3년",
        "effect_score": 100,  # 적자 기업에게 최우선
    }


def _dividendExpansionLever(base, fcf, equity) -> dict | None:
    """현금부자: 배당 확대 시 ROE 변화 (Penman FLEV 효과)."""
    debtRatio = base.get("debtRatio")
    if not (debtRatio is not None and debtRatio < 50 and fcf and fcf > 0 and equity and equity > 0):
        return None
    # FLEV 마이너스 = 순현금. 배당성향 20%p 확대분만큼 자본이 줄어 ROE 분모가 작아진다.
    dividendIncrease = fcf * 0.20
    reducedEquity = equity - dividendIncrease
    ni = base.get("roe", 0) / 100 * equity if base.get("roe") else None
    newRoe = ni / reducedEquity * 100 if ni and reducedEquity > 0 else None
    if not (newRoe and base.get("roe")):
        return None
    return {
        "name": f"배당 확대 (FCF의 20%) → ROE {base['roe']:.1f}% → {newRoe:.1f}%",
        "driver": "dividend_expansion",
        "impact": {"roe": round(newRoe, 1), "dividendIncrease": round(dividendIncrease)},
        "difficulty": "easy",
        "timeframe": "즉시 가능",
        "effect_score": abs(newRoe - base["roe"]),
    }


def _cashRunwayLever(company, base, opm, fcf) -> dict | None:
    """턴어라운드: FCF 적자 기업의 현금 소진까지 남은 개월."""
    if not (opm is not None and opm > 0 and opm < 5 and fcf is not None):
        return None
    cash = base.get("_cash")
    if cash is None:
        try:
            bsRow = _latestAnnualRow(company, "BS", ["cash_and_cash_equivalents"], basePeriod=None)
            if bsRow is not None:
                cash = float(bsRow["cash_and_cash_equivalents"] or 0)
        except (AttributeError, ValueError, TypeError):
            pass

    if not (cash and cash > 0 and fcf < 0):
        return None
    months = round(cash / abs(fcf) * 12)
    return {
        "name": f"현금 소진까지 약 {months}개월. 구조조정 시급",
        "driver": "cash_runway",
        "impact": {"cashRunwayMonths": months, "currentCash": round(cash)},
        "difficulty": "critical",
        "timeframe": f"{months}개월",
        "effect_score": 200,  # 생존 이슈는 최우선
    }


def _cycleDefenseLever(revenue, opm, interestAbs) -> dict | None:
    """사이클 기업: 이자비용을 감당하는 최소 OPM 과 현재 여유폭."""
    if not (opm is not None and opm > 10 and interestAbs > 0 and revenue):
        return None
    minOpm = interestAbs / revenue * 100  # 이자비용 감당 최소 OPM
    buffer = opm - minOpm
    if not (buffer < 10):
        return None
    return {
        "name": f"다운턴 방어선 OPM {minOpm:.1f}% (현재 대비 -{buffer:.1f}%p 여유)",
        "driver": "cycle_defense_opm",
        "impact": {"minOPM": round(minOpm, 1), "bufferPP": round(buffer, 1)},
        "difficulty": "awareness",
        "timeframe": "사이클 하강 시",
        "effect_score": 50,
    }


def _reinvestmentLever(company, revenue, opm, equity) -> dict | None:
    """고성장 기업: CAPEX/매출 대비 재투자 효율."""
    if not (opm is not None and opm > 15 and revenue):
        return None
    try:
        cfRow = _latestAnnualRow(
            company,
            "CF",
            ["purchase_of_property_plant_and_equipment"],
            basePeriod=None,
        )
        if cfRow is None:
            return None
        capex = abs(float(cfRow["purchase_of_property_plant_and_equipment"] or 0))
        if not (capex > 0):
            return None
        capexToRev = capex / revenue * 100
        roic = opm * (revenue / equity) if equity and equity > 0 else None
        return {
            "name": f"CAPEX/매출 {capexToRev:.1f}%. ROIC 대비 재투자 효율",
            "driver": "reinvestment_efficiency",
            "impact": {
                "capexToRevenue": round(capexToRev, 1),
                "estimatedROIC": _round1(roic),
            },
            "difficulty": "medium",
            "timeframe": "지속",
            "effect_score": 30,
        }
    except (AttributeError, ValueError, TypeError):
        return None


def _verdictOpm(opm: float, ic: float | None) -> str:
    """OPM shock 후 위험 판단문 반환.

    Returns
    -------
    str
        "영업적자 전환" | "이자 감당 위험" | "마진 압박 심각" | "감내 가능".
    """
    if opm < 0:
        return "영업적자 전환"
    if ic is not None and ic < 1.5:
        return "이자 감당 위험"
    if opm < 5:
        return "마진 압박 심각"
    return "감내 가능"


def _verdictRev(ic: float | None) -> str:
    """매출 shock 후 위험 판단문 반환.

    Returns
    -------
    str
        "이자 감당 위험" | "감내 가능".
    """
    if ic is not None and ic < 1.5:
        return "이자 감당 위험"
    return "감내 가능"


def _verdictRate(ic: float | None) -> str:
    """금리 shock 후 위험 판단문 반환.

    Returns
    -------
    str
        "이자 감당 위험" | "여유 축소" | "감내 가능".
    """
    if ic is not None and ic < 1.5:
        return "이자 감당 위험"
    if ic is not None and ic < 3:
        return "여유 축소"
    return "감내 가능"
