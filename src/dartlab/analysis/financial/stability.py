"""2-3 안정성 분석 -- 부채 구조와 지급 능력을 추적한다.

select()로 BS/IS/CF 원본 계정을 가져와서
부채비율 + 이자보상배율 + 부실 판별을 금액과 함께 보여준다.
레버리지가 늘었는지, 이자를 갚을 수 있는지를 금액으로 파악.
"""

from __future__ import annotations

from dartlab.analysis.financial._helpers import (
    MAX_RATIO_YEARS,
    getRatios,
    toDict,
    toDictBySnakeId,
)
from dartlab.analysis.financial._helpers import (
    annualColsFromPeriods as _annualColsFromPeriods,
)

_MAX_YEARS = MAX_RATIO_YEARS


def _isHoldingOrFinancial(company) -> bool:
    """지주사 또는 금융업 판별."""
    try:
        name = getattr(company, "corpName", "") or ""
        if any(k in name for k in ("지주", "홀딩스", "Holdings")):
            return True
        sector = getattr(company, "sector", None)
        if sector is not None:
            from dartlab.core.sector.types import Sector

            if sector.sector == Sector.FINANCIALS:
                return True
    except (AttributeError, ImportError):
        pass
    return False


def _yoy(cur, prev) -> float | None:
    if cur is None or prev is None or prev == 0:
        return None
    return round((cur - prev) / abs(prev) * 100, 2)


def _pctOf(part, total) -> float | None:
    if part is None or total is None or total == 0:
        return None
    return round(part / total * 100, 2)


# ── 레버리지 구조 시계열 ──


def calcLeverageTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """레버리지 구조 시계열 -- 부채로 얼마나 버티는가.

    BS에서 부채/자본/자산 원본 금액을 가져와서
    부채비율 + 자기자본비율 + 순차입금비율을 금액과 함께 보여준다.
    """
    bsResult = company.select(
        "BS",
        ["부채총계", "자본총계", "자산총계", "현금및현금성자산", "단기차입금", "장기차입금", "사채"],
    )
    parsed = toDict(bsResult)
    if parsed is None:
        return None

    data, periods = parsed
    debt = data.get("부채총계", {})
    equity = data.get("자본총계", {})
    ta = data.get("자산총계", {})
    cash = data.get("현금및현금성자산", {})
    stBorrow = data.get("단기차입금", {})
    ltBorrow = data.get("장기차입금", {})
    bonds = data.get("사채", {})

    yCols = _annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        d = debt.get(col)
        e = equity.get(col)
        a = ta.get(col)
        c = cash.get(col)

        totalBorrowing = (stBorrow.get(col) or 0) + (ltBorrow.get(col) or 0) + (bonds.get(col) or 0)
        netDebt = totalBorrowing - (c or 0) if totalBorrowing > 0 else None

        debtRatio = _pctOf(d, e)
        equityRatio = _pctOf(e, a)
        netDebtRatio = _pctOf(netDebt, e) if netDebt is not None else None

        history.append(
            {
                "period": col,
                "totalDebt": d,
                "totalDebtYoy": _yoy(d, debt.get(prevCol)) if prevCol else None,
                "equity": e,
                "equityYoy": _yoy(e, equity.get(prevCol)) if prevCol else None,
                "totalAssets": a,
                "cash": c,
                "totalBorrowing": totalBorrowing if totalBorrowing > 0 else None,
                "netDebt": netDebt,
                "debtRatio": debtRatio,
                "equityRatio": equityRatio,
                "netDebtRatio": netDebtRatio,
            }
        )

    return {"history": history} if history else None


# ── 이자보상 시계열 ──


def calcCoverageTrend(company, *, basePeriod: str | None = None) -> dict | None:
    """이자보상배율 시계열 -- 이자를 갚을 능력이 있는가.

    IS 영업이익 / 이자비용으로 산출.
    이자비용 소스 우선순위: IS 이자비용 → CF interest_paid → IS 금융비용.
    금융비용은 외환손실·파생상품 등 비이자 항목 포함하여 과대계상 위험.
    """
    isResult = company.select("IS", ["영업이익", "금융비용", "이자비용"])
    parsed = toDict(isResult)
    if parsed is None:
        return None

    data, periods = parsed
    op = data.get("영업이익", {})
    finCost = data.get("금융비용", {})
    intCost = data.get("이자비용", {})

    # CF interest_paid (실제 현금 이자 지급액)
    cfIntPaid: dict = {}
    try:
        cfResult = company.select("CF", ["interest_paid"])
        cfParsed = toDictBySnakeId(cfResult)
        if cfParsed is not None:
            cfData, _ = cfParsed
            cfIntPaid = cfData.get("interest_paid", {})
    except (ValueError, KeyError, AttributeError):
        pass

    yCols = _annualColsFromPeriods(periods, basePeriod, _MAX_YEARS + 1)
    if len(yCols) < 2:
        return None

    history = []
    for i, col in enumerate(yCols[:-1]):
        prevCol = yCols[i + 1] if i + 1 < len(yCols) else None
        o = op.get(col)

        # 이자비용 우선순위: IS 이자비용 → CF interest_paid → IS 금융비용
        intVal = intCost.get(col)
        cfVal = cfIntPaid.get(col)
        finVal = finCost.get(col)

        if intVal:
            interest = intVal
            source = "이자비용"
        elif cfVal:
            interest = abs(cfVal)  # CF는 지출이라 음수일 수 있음
            source = "CF이자지급"
        elif finVal:
            interest = finVal
            source = "금융비용"
        else:
            interest = None
            source = None

        coverage = None
        if o is not None and interest is not None and interest != 0:
            coverage = round(o / abs(interest), 2)

        history.append(
            {
                "period": col,
                "operatingIncome": o,
                "operatingIncomeYoy": _yoy(o, op.get(prevCol)) if prevCol else None,
                "interestExpense": interest,
                "interestExpenseSource": source,
                "interestCoverage": coverage,
            }
        )

    return {"history": history} if history else None


# ── 부실 판별 (Altman Z-Score) ──


def calcDistressScore(company, *, basePeriod: str | None = None) -> dict | None:
    """Altman Z-Score 시계열 -- 부실 위험은 어디인가.

    BS/IS에서 원본 계정을 가져와 5개 변수를 직접 계산.
    Z = 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    X1 = 운전자본/총자산, X2 = 이익잉여금/총자산, X3 = EBIT/총자산
    X4 = 시가총액/부채총계, X5 = 매출/총자산
    """
    bsResult = company.select(
        "BS",
        ["자산총계", "유동자산", "유동부채", "부채총계", "이익잉여금", "미처분이익잉여금(결손금)"],
    )
    isResult = company.select("IS", ["영업이익", "매출액"])

    bsParsed = toDict(bsResult)
    isParsed = toDict(isResult)
    if bsParsed is None or isParsed is None:
        return None

    bsData, bsPeriods = bsParsed
    isData, _ = isParsed

    taRow = bsData.get("자산총계", {})
    caRow = bsData.get("유동자산", {})
    clRow = bsData.get("유동부채", {})
    tlRow = bsData.get("부채총계", {})
    from dartlab.analysis.financial._helpers import mergeRows

    reRow = mergeRows(bsData.get("이익잉여금"), bsData.get("미처분이익잉여금(결손금)"))
    opRow = isData.get("영업이익", {})
    revRow = isData.get("매출액", {})

    # 시가총액 (X4용) -- ratios에서 가져옴
    ratios = getRatios(company)
    marketCap = ratios.marketCap if ratios else None

    yCols = _annualColsFromPeriods(bsPeriods, basePeriod, _MAX_YEARS)
    if not yCols:
        return None

    history = []
    for col in yCols:
        a = taRow.get(col)
        ca = caRow.get(col)
        cl = clRow.get(col)
        tl = tlRow.get(col)
        re = reRow.get(col)
        ebit = opRow.get(col)
        rev = revRow.get(col)

        if a is None or a == 0:
            continue

        wc = (ca or 0) - (cl or 0)
        x1 = round(wc / a, 4) if a else None
        x2 = round(re / a, 4) if re is not None and a else None
        x3 = round(ebit / a, 4) if ebit is not None and a else None
        x4 = round(marketCap / tl, 4) if marketCap is not None and tl and tl > 0 else None
        x5 = round(rev / a, 4) if rev is not None and a else None

        # X4(시가총액/부채) 없으면 Altman Z'' (비제조업) 대체
        zScore = None
        zModel = None
        if all(v is not None for v in [x1, x2, x3, x4, x5]):
            zScore = round(1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5, 2)
            zModel = "Z-Score"
        elif all(v is not None for v in [x1, x2, x3, x5]):
            # Z'' = 6.56*X1 + 3.26*X2 + 6.72*X3 + 1.05*X5 (book value 기반)
            zScore = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x5, 2)
            zModel = "Z''-Score"

        if zScore is not None:
            safeThreshold = 2.99 if zModel == "Z-Score" else 2.60
            dangerThreshold = 1.81 if zModel == "Z-Score" else 1.10
            if zScore > safeThreshold:
                zone = "안전"
            elif zScore > dangerThreshold:
                zone = "회색"
            else:
                zone = "위험"
        else:
            zone = None

        history.append(
            {
                "period": col,
                "totalAssets": a,
                "workingCapital": wc,
                "retainedEarnings": re,
                "ebit": ebit,
                "revenue": rev,
                "totalDebt": tl,
                "x1_wcTa": x1,
                "x2_reTa": x2,
                "x3_ebitTa": x3,
                "x4_mcapTl": x4,
                "x5_revTa": x5,
                "zScore": zScore,
                "zModel": zModel,
                "zone": zone,
            }
        )

    if not history:
        return None

    latest = history[0]
    return {
        "history": history,
        "latestScore": latest.get("zScore"),
        "zone": latest.get("zone") or "판별 불가",
    }


# ── 부실 앙상블 (기존 유지 -- getRatios 사용) ──


def calcDistressEnsemble(company, *, basePeriod: str | None = None) -> dict | None:
    """4개 부실예측 모델 앙상블 -- 다수결 투표.

    Altman Z-Score, Ohlson O-Score, Springate S-Score, Zmijewski X-Score
    각 모델의 판정(safe/warning/danger)을 집계하여 종합 등급 산출.
    """
    ratios = getRatios(company)
    if ratios is None:
        return None

    models = []

    # Altman Z-Score: >2.99 safe, 1.81~2.99 gray, <1.81 danger
    z = ratios.altmanZScore
    if z is not None:
        if z > 2.99:
            verdict = "safe"
        elif z > 1.81:
            verdict = "warning"
        else:
            verdict = "danger"
        models.append(
            {
                "model": "Altman Z-Score",
                "score": z,
                "verdict": verdict,
                "threshold": "안전 >2.99 / 회색 1.81~2.99 / 위험 <1.81",
            }
        )

    # Altman Z'' (비제조/신흥): >2.60 safe, 1.10~2.60 gray, <1.10 danger
    zpp = ratios.altmanZppScore
    if zpp is not None:
        if zpp > 2.60:
            verdict = "safe"
        elif zpp > 1.10:
            verdict = "warning"
        else:
            verdict = "danger"
        models.append(
            {
                "model": "Altman Z''-Score",
                "score": zpp,
                "verdict": verdict,
                "threshold": "안전 >2.60 / 회색 1.10~2.60 / 위험 <1.10",
            }
        )

    # Ohlson O-Score: P(default) < 10% safe, 10~50% warning, >50% danger
    oProb = ratios.ohlsonProbability
    if oProb is not None:
        if oProb < 10:
            verdict = "safe"
        elif oProb < 50:
            verdict = "warning"
        else:
            verdict = "danger"
        models.append(
            {
                "model": "Ohlson O-Score",
                "score": ratios.ohlsonOScore,
                "probability": oProb,
                "verdict": verdict,
                "threshold": "안전 <10% / 경고 10~50% / 위험 >50%",
            }
        )

    # Springate S-Score: >0.862 safe, else danger
    ss = ratios.springateSScore
    if ss is not None:
        verdict = "safe" if ss > 0.862 else "danger"
        models.append(
            {"model": "Springate S-Score", "score": ss, "verdict": verdict, "threshold": "안전 >0.862 / 위험 <0.862"}
        )

    # Zmijewski X-Score: <0 safe, else danger
    xz = ratios.zmijewskiXScore
    if xz is not None:
        verdict = "safe" if xz < 0 else "danger"
        models.append({"model": "Zmijewski X-Score", "score": xz, "verdict": verdict, "threshold": "안전 <0 / 위험 >0"})

    if not models:
        return None

    # 다수결
    dangerCount = sum(1 for m in models if m["verdict"] == "danger")
    safeCount = sum(1 for m in models if m["verdict"] == "safe")
    total = len(models)

    if dangerCount > total / 2:
        ensemble = "위험"
    elif safeCount > total / 2:
        ensemble = "안전"
    else:
        ensemble = "주의"

    agreement = max(dangerCount, safeCount) / total * 100

    return {
        "models": models,
        "ensemble": ensemble,
        "agreement": round(agreement, 1),
        "dangerCount": dangerCount,
        "safeCount": safeCount,
        "total": total,
    }


def calcDebtMaturity(company, *, basePeriod: str | None = None) -> dict | None:
    """부채 만기 구조 분석.

    단기/장기 차입금 비율, 차환 리스크 지표.
    """
    bsResult = company.select(
        "BS",
        [
            "단기차입금",
            "장기차입금",
            "사채",
            "차입부채",
            "발행사채",
            "유동금융부채",
            "장기금융부채",
            "유동부채",
            "비유동부채",
            "부채총계",
        ],
    )
    parsed = toDict(bsResult, maxPeriods=5)
    if parsed is None:
        return None

    data, periods = parsed
    # 일반 제조업
    stRow = data.get("단기차입금", {})
    ltRow = data.get("장기차입금", {})
    bondsRow = data.get("사채", {})
    # 금융업
    borrowRow = data.get("차입부채", {})
    issuedBondRow = data.get("발행사채", {})
    # 바이오 등
    curFinRow = data.get("유동금융부채", {})
    ltFinRow = data.get("장기금융부채", {})

    clRow = data.get("유동부채", {})
    nclRow = data.get("비유동부채", {})
    tlRow = data.get("부채총계", {})

    # 연도 컬럼만
    annualPeriods = _annualColsFromPeriods(periods, basePeriod, 5)
    if not annualPeriods:
        return None

    # OCF for 차환능력 평가
    cfResult = company.select("CF", ["영업활동현금흐름"])
    cfParsed = toDict(cfResult, maxPeriods=5) if cfResult else None
    cfData = cfParsed[0] if cfParsed else {}
    ocfRow = cfData.get("영업활동현금흐름", {})

    history = []
    for col in annualPeriods:
        # 차입금: 업종별 계정 대응
        st = stRow.get(col) or 0
        lt = ltRow.get(col) or 0
        bondsVal = bondsRow.get(col) or 0
        totalBorrowing = st + lt + bondsVal

        # 금융업 fallback
        if totalBorrowing == 0:
            borrow = borrowRow.get(col) or 0
            issued = issuedBondRow.get(col) or 0
            totalBorrowing = borrow + issued
            st = borrow  # 금융업 차입부채를 단기로 근사
            lt = issued

        # 바이오 등 fallback
        if totalBorrowing == 0:
            curFin = curFinRow.get(col) or 0
            ltFin = ltFinRow.get(col) or 0
            totalBorrowing = curFin + ltFin
            st = curFin
            lt = ltFin

        cl = clRow.get(col) or 0
        tl = tlRow.get(col) or 0
        ocf = ocfRow.get(col)

        shortTermRatio = round(st / totalBorrowing * 100, 2) if totalBorrowing > 0 else None
        currentToTotal = round(cl / tl * 100, 2) if tl > 0 else None

        # 단기차입금/OCF = 차환능력 (낮을수록 안전)
        refinancingRisk = None
        if ocf is not None and ocf > 0 and st > 0:
            refinancingRisk = round(st / ocf, 2)

        history.append(
            {
                "period": col,
                "shortTermBorrowing": st,
                "longTermBorrowing": lt,
                "bonds": bondsVal,
                "totalBorrowing": totalBorrowing,
                "shortTermRatio": shortTermRatio,
                "currentToTotalDebt": currentToTotal,
                "refinancingRisk": refinancingRisk,
            }
        )

    return {"history": history} if history else None


# ── 플래그 ──


def calcStabilityFlags(company, *, basePeriod: str | None = None) -> list[str]:
    """안정성 경고/기회 플래그."""
    flags: list[str] = []

    # 레버리지
    isFinancial = _isHoldingOrFinancial(company)
    lev = calcLeverageTrend(company, basePeriod=basePeriod)
    if lev and lev["history"]:
        hist = lev["history"]
        h0 = hist[0]
        dr = h0.get("debtRatio")
        if dr is not None:
            if isFinancial:
                # 금융업: 예수부채로 부채비율이 구조적으로 높음. 비금융 기준 적용 불가
                if dr < 1000:
                    flags.append(f"부채비율 {dr:.0f}% -- 금융업 양호")
                elif dr < 1500:
                    flags.append(f"부채비율 {dr:.0f}% -- 금융업 보통")
                else:
                    flags.append(f"부채비율 {dr:.0f}% -- 금융업 과다")
            elif dr > 200:
                flags.append(f"부채비율 {dr:.0f}% -- 재무 위험")
            elif dr < 50:
                flags.append(f"부채비율 {dr:.0f}% -- 매우 안정")

        # 부채 3기 연속 증가
        if len(hist) >= 3:
            debts = [h.get("totalDebt") for h in hist[:3]]
            if all(v is not None for v in debts) and debts[0] > debts[1] > debts[2]:
                yoy = h0.get("totalDebtYoy")
                flags.append(f"부채 3기 연속 증가 (최근 +{yoy:.0f}%)" if yoy else "부채 3기 연속 증가")

    # 이자보상
    cov = calcCoverageTrend(company, basePeriod=basePeriod)
    if cov and cov["history"]:
        h0 = cov["history"][0]
        ic = h0.get("interestCoverage")
        source = h0.get("interestExpenseSource")
        # 순현금 여부 확인 -- 순현금이면 금융비용 기반 저배율은 오진 가능
        isNetCash = False
        if lev and lev["history"]:
            nd = lev["history"][0].get("netDebt")
            if nd is not None and nd < 0:
                isNetCash = True
        # 지주사/금융업: 영업이익 구조적 저수준 (지분법이익이 영업외에 잡힘)
        if ic is not None:
            if isFinancial:
                # 지주사/금융은 영업이익 기반 이자보상배율이 구조적으로 낮음
                if ic < 1:
                    flags.append(f"이자보상배율 {ic:.1f}배 -- 지주/금융 구조상 저수준 (영업외 수익이 이자 커버)")
            elif ic < 1 and not isNetCash:
                flags.append(f"이자보상배율 {ic:.1f}배 -- 이자 지급 불능 위험")
            elif ic < 3 and not (isNetCash and source == "금융비용"):
                flags.append(f"이자보상배율 {ic:.1f}배 -- 이자 부담 과다")

    # Altman Z-Score (제조업 기반 모형 — 금융/지주사는 구조적 왜곡)
    if not isFinancial:
        distress = calcDistressScore(company, basePeriod=basePeriod)
        if distress and distress.get("latestScore") is not None:
            z = distress["latestScore"]
            if z < 1.81:
                flags.append(f"Altman Z-Score {z:.2f} -- 부실 위험 구간")

    return flags
