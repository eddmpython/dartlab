"""이상치 탐지 — 11개 룰 기반."""

from __future__ import annotations

import math
from typing import Optional

from dartlab.engines.analysis.insight.types import Anomaly, AuditDataForAnomaly
from dartlab.engines.common.finance.extract import getAnnualValues


def _yoyChange(vals: list[Optional[float]]) -> Optional[float]:
    from dartlab.engines.common.finance.ratios import yoy_pct

    valid = [(i, v) for i, v in enumerate(vals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    return yoy_pct(curr, prev)


def detectEarningsQuality(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """이익 품질 이상치: 영업이익↑ but 영업CF↓ (금융업 제외)."""
    anomalies: list[Anomaly] = []

    if isFinancial:
        return anomalies

    opIncomeVals = getAnnualValues(aSeries, "IS", "operating_profit")
    opCfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")

    opGrowth = _yoyChange(opIncomeVals)
    cfGrowth = _yoyChange(opCfVals)

    if opGrowth is not None and cfGrowth is not None:
        if opGrowth > 10 and cfGrowth < -10:
            anomalies.append(
                Anomaly(
                    "danger",
                    "earningsQuality",
                    f"이익↑(+{opGrowth:.0f}%) but 영업CF↓({cfGrowth:.0f}%) — 이익 품질 의심",
                    opGrowth - cfGrowth,
                )
            )
        elif opGrowth > 0 and cfGrowth < 0 and abs(cfGrowth) > 20:
            anomalies.append(
                Anomaly(
                    "warning",
                    "earningsQuality",
                    f"이익 증가(+{opGrowth:.0f}%) 대비 영업CF 감소({cfGrowth:.0f}%)",
                    opGrowth - cfGrowth,
                )
            )

    netIncomeVals = getAnnualValues(aSeries, "IS", "net_profit")

    latestNi = None
    latestCf = None
    for v in reversed(netIncomeVals):
        if v is not None:
            latestNi = v
            break
    for v in reversed(opCfVals):
        if v is not None:
            latestCf = v
            break

    if latestNi and latestCf and latestNi > 0 and latestCf < 0:
        anomalies.append(
            Anomaly(
                "danger",
                "earningsQuality",
                f"순이익 흑자({latestNi / 1e8:,.0f}억) but 영업CF 적자({latestCf / 1e8:,.0f}억)",
            )
        )

    return anomalies


def detectWorkingCapitalAnomaly(aSeries: dict) -> list[Anomaly]:
    """운전자본 이상치: 매출채권/재고 급증 > 매출 증가."""
    anomalies: list[Anomaly] = []

    arVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")
    if not arVals:
        arVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")
    invVals = getAnnualValues(aSeries, "BS", "inventories")
    revVals = getAnnualValues(aSeries, "IS", "sales")

    arGrowth = _yoyChange(arVals)
    invGrowth = _yoyChange(invVals)
    revGrowth = _yoyChange(revVals)

    if arGrowth is not None and revGrowth is not None:
        if arGrowth > revGrowth + 20 and arGrowth > 30:
            anomalies.append(
                Anomaly(
                    "warning",
                    "workingCapital",
                    f"매출채권 급증(+{arGrowth:.0f}%) > 매출 증가(+{revGrowth:.0f}%) — 수금 지연 가능",
                    arGrowth - revGrowth,
                )
            )

    if invGrowth is not None and revGrowth is not None:
        if invGrowth > revGrowth + 30 and invGrowth > 40:
            anomalies.append(
                Anomaly(
                    "warning",
                    "workingCapital",
                    f"재고자산 급증(+{invGrowth:.0f}%) > 매출 증가(+{revGrowth:.0f}%) — 재고 과잉 가능",
                    invGrowth - revGrowth,
                )
            )
    elif invGrowth is not None and invGrowth > 50:
        anomalies.append(
            Anomaly(
                "info",
                "workingCapital",
                f"재고자산 대폭 증가(+{invGrowth:.0f}%)",
                invGrowth,
            )
        )

    return anomalies


def detectBalanceSheetShift(aSeries: dict) -> list[Anomaly]:
    """BS 구조 급변: 부채/차입금/자본 ±50% 이상."""
    anomalies: list[Anomaly] = []

    checkItems = [
        ("BS", "total_liabilities", "부채총계"),
        ("BS", "shortterm_borrowings", "단기차입금"),
        ("BS", "longterm_borrowings", "장기차입금"),
        ("BS", "debentures", "사채"),
        ("BS", "owners_of_parent_equity", "자본총계"),
    ]

    for sjDiv, snakeId, label in checkItems:
        vals = getAnnualValues(aSeries, sjDiv, snakeId)
        change = _yoyChange(vals)
        if change is not None and abs(change) > 50:
            direction = "급증" if change > 0 else "급감"
            severity = "warning" if abs(change) > 100 else "info"
            anomalies.append(
                Anomaly(
                    severity,
                    "balanceSheetShift",
                    f"{label} {direction} ({change:+.0f}%)",
                    change,
                )
            )

    equityVals = getAnnualValues(aSeries, "BS", "owners_of_parent_equity")
    valid = [v for v in equityVals if v is not None]
    if valid and valid[-1] is not None and valid[-1] < 0:
        anomalies.append(
            Anomaly(
                "danger",
                "balanceSheetShift",
                f"자본잠식 ({valid[-1] / 1e8:,.0f}억)",
                valid[-1],
            )
        )

    return anomalies


def detectCashBurn(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """현금 소진: 현금 급감, 영업CF적자+재무CF양수 (금융업 제외)."""
    anomalies: list[Anomaly] = []

    cashVals = getAnnualValues(aSeries, "BS", "cash_and_cash_equivalents")
    cashChange = _yoyChange(cashVals)

    if cashChange is not None and cashChange < -50:
        anomalies.append(
            Anomaly(
                "warning",
                "cashBurn",
                f"현금성 자산 급감 ({cashChange:.0f}%)",
                cashChange,
            )
        )

    opCfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    finCfVals = getAnnualValues(aSeries, "CF", "cash_flows_from_financing_activities")

    latestOp = None
    latestFin = None
    for v in reversed(opCfVals):
        if v is not None:
            latestOp = v
            break
    for v in reversed(finCfVals):
        if v is not None:
            latestFin = v
            break

    if not isFinancial and latestOp is not None and latestOp < 0 and latestFin is not None and latestFin > 0:
        anomalies.append(
            Anomaly(
                "warning",
                "cashBurn",
                f"영업CF 적자({latestOp / 1e8:,.0f}억) + 재무CF 양수({latestFin / 1e8:,.0f}억) — 차입으로 영업적자 보전",
            )
        )

    return anomalies


def detectMarginDivergence(aSeries: dict) -> list[Anomaly]:
    """마진 급변: 영업이익률 ±5%p, 영업외손익 급변."""
    anomalies: list[Anomaly] = []

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    niVals = getAnnualValues(aSeries, "IS", "net_profit")

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]

    if len(validRev) >= 2 and len(validOp) >= 2:
        prevMargin = (validOp[-2] / validRev[-2] * 100) if validRev[-2] and validRev[-2] != 0 else None
        currMargin = (validOp[-1] / validRev[-1] * 100) if validRev[-1] and validRev[-1] != 0 else None

        if prevMargin is not None and currMargin is not None:
            marginShift = currMargin - prevMargin
            if abs(marginShift) > 5:
                direction = "개선" if marginShift > 0 else "악화"
                severity = "info" if marginShift > 0 else "warning"
                anomalies.append(
                    Anomaly(
                        severity,
                        "marginDivergence",
                        f"영업이익률 {direction} ({prevMargin:.1f}% → {currMargin:.1f}%, {marginShift:+.1f}%p)",
                        marginShift,
                    )
                )

    if len(validOp) >= 2 and len(validNi) >= 2:
        prevGap = validNi[-2] - validOp[-2] if validOp[-2] is not None and validNi[-2] is not None else None
        currGap = validNi[-1] - validOp[-1] if validOp[-1] is not None and validNi[-1] is not None else None

        if prevGap is not None and currGap is not None:
            gapChange = currGap - prevGap
            if abs(gapChange) > 0 and validOp[-1] and validOp[-1] != 0:
                gapRatio = (abs(gapChange) / abs(validOp[-1])) * 100
                if gapRatio > 30:
                    anomalies.append(
                        Anomaly(
                            "warning",
                            "marginDivergence",
                            f"영업외손익 급변 (영업이익 대비 {gapRatio:.0f}% 규모 변동)",
                            gapRatio,
                        )
                    )

    return anomalies


def detectFinancialSectorAnomaly(aSeries: dict, isFinancial: bool) -> list[Anomaly]:
    """금융업 전용 이상치: 부채비율 급변, 순이익 급감."""
    if not isFinancial:
        return []

    anomalies: list[Anomaly] = []

    liabVals = getAnnualValues(aSeries, "BS", "total_liabilities")
    equityVals = getAnnualValues(aSeries, "BS", "owners_of_parent_equity") or getAnnualValues(
        aSeries, "BS", "total_stockholders_equity"
    )

    validLiab = [v for v in liabVals if v is not None]
    validEq = [v for v in equityVals if v is not None]

    if len(validLiab) >= 2 and len(validEq) >= 2:
        prevDr = (validLiab[-2] / validEq[-2] * 100) if validEq[-2] and validEq[-2] > 0 else None
        currDr = (validLiab[-1] / validEq[-1] * 100) if validEq[-1] and validEq[-1] > 0 else None

        if prevDr is not None and currDr is not None:
            drShift = currDr - prevDr
            if abs(drShift) > 100:
                direction = "급증" if drShift > 0 else "급감"
                anomalies.append(
                    Anomaly(
                        "warning",
                        "financialSector",
                        f"금융업 부채비율 {direction} ({prevDr:.0f}% → {currDr:.0f}%, {drShift:+.0f}%p)",
                        drShift,
                    )
                )

    niVals = getAnnualValues(aSeries, "IS", "net_profit")
    niChange = _yoyChange(niVals)
    if niChange is not None and niChange < -30:
        anomalies.append(
            Anomaly(
                "warning",
                "financialSector",
                f"금융업 순이익 급감 ({niChange:.0f}%)",
                niChange,
            )
        )

    return anomalies


def detectTrendDeterioration(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """시계열 악화 패턴 탐지: 연속적자, ICR<1, 부채비율 상승.

    실험 084/006 검증 결과 기반.
    severity: 4기+ danger, 3기 warning, 2기 info.
    """
    anomalies: list[Anomaly] = []

    # 순이익 연속 적자
    niVals = getAnnualValues(aSeries, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(aSeries, "IS", "net_income")
    streak = 0
    for v in reversed(niVals):
        if v is not None and v < 0:
            streak += 1
        else:
            break
    if streak >= 2:
        sev = "danger" if streak >= 4 else "warning" if streak >= 3 else "info"
        anomalies.append(Anomaly(sev, "trendDeterioration", f"순이익 {streak}기 연속 적자", float(streak)))

    # 영업CF 연속 적자
    cfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    streak = 0
    for v in reversed(cfVals):
        if v is not None and v < 0:
            streak += 1
        else:
            break
    if streak >= 2:
        sev = "danger" if streak >= 4 else "warning" if streak >= 3 else "info"
        anomalies.append(Anomaly(sev, "trendDeterioration", f"영업CF {streak}기 연속 적자", float(streak)))

    if isFinancial:
        return anomalies  # ICR, 부채비율 추이는 금융업 구조적 왜곡

    # ICR < 1 연속 (금융업 제외)
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    if not opVals:
        opVals = getAnnualValues(aSeries, "IS", "operating_income")
    fcVals = getAnnualValues(aSeries, "IS", "finance_costs")
    if not fcVals:
        fcVals = getAnnualValues(aSeries, "IS", "interest_expense")

    if opVals and fcVals:
        n = min(len(opVals), len(fcVals))
        streak = 0
        for i in range(n - 1, -1, -1):
            op_v = opVals[i]
            fc_v = fcVals[i]
            if op_v is not None and fc_v is not None and fc_v > 0 and op_v / fc_v < 1:
                streak += 1
            else:
                break
        if streak >= 2:
            sev = "danger" if streak >= 3 else "warning"
            anomalies.append(Anomaly(sev, "trendDeterioration", f"ICR<1 {streak}기 연속", float(streak)))

    # 부채비율 연속 상승 (3기+)
    tlVals = getAnnualValues(aSeries, "BS", "total_liabilities")
    eqVals = getAnnualValues(aSeries, "BS", "owners_of_parent_equity")
    if not eqVals:
        eqVals = getAnnualValues(aSeries, "BS", "total_stockholders_equity")

    if tlVals and eqVals:
        n = min(len(tlVals), len(eqVals))
        drSeries = []
        for i in range(n):
            if tlVals[i] is not None and eqVals[i] is not None and eqVals[i] > 0:
                drSeries.append(tlVals[i] / eqVals[i] * 100)
            else:
                drSeries.append(None)

        streak = 0
        for i in range(len(drSeries) - 1, 0, -1):
            if drSeries[i] is not None and drSeries[i - 1] is not None and drSeries[i] > drSeries[i - 1]:
                streak += 1
            else:
                break
        if streak >= 3:
            sev = "warning" if streak >= 4 else "info"
            anomalies.append(Anomaly(sev, "trendDeterioration", f"부채비율 {streak}기 연속 상승", float(streak)))

    return anomalies


def detectCCCDeterioration(aSeries: dict, isFinancial: bool = False) -> list[Anomaly]:
    """CCC(현금전환주기) 악화 탐지.

    실험 084/007 검증 결과 기반.
    CCC 3기+ 연속 확대 시 운전자본 경색 경고.
    금융업 제외 (DSO/DIO/CCC 비적용).
    """
    if isFinancial:
        return []

    anomalies: list[Anomaly] = []
    revVals = getAnnualValues(aSeries, "IS", "sales")
    if not revVals:
        revVals = getAnnualValues(aSeries, "IS", "revenue")
    recVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")
    invVals = getAnnualValues(aSeries, "BS", "inventories")
    payVals = getAnnualValues(aSeries, "BS", "trade_and_other_payables")
    cogsVals = getAnnualValues(aSeries, "IS", "cost_of_sales")

    n = (
        min(len(revVals), len(recVals), len(invVals), len(payVals))
        if revVals and recVals and invVals and payVals
        else 0
    )
    if n < 3:
        return anomalies

    cccSeries: list[Optional[float]] = []
    for i in range(n):
        rv = revVals[i]
        rc = recVals[i]
        iv = invVals[i]
        pa = payVals[i]
        co = cogsVals[i] if cogsVals and i < len(cogsVals) else rv

        if rv and rv > 0 and rc is not None and iv is not None and pa is not None and co and co > 0:
            dso = rc / rv * 365
            dio = iv / co * 365
            dpo = pa / co * 365
            cccSeries.append(dso + dio - dpo)
        else:
            cccSeries.append(None)

    # 연속 확대 탐지
    streak = 0
    for i in range(len(cccSeries) - 1, 0, -1):
        if cccSeries[i] is not None and cccSeries[i - 1] is not None and cccSeries[i] > cccSeries[i - 1]:
            streak += 1
        else:
            break

    if streak >= 3:
        latest = cccSeries[-1]
        sev = "warning" if streak >= 4 else "info"
        anomalies.append(
            Anomaly(
                sev,
                "cccDeterioration",
                f"CCC {streak}기 연속 확대 (최신 {latest:.0f}일)" if latest else f"CCC {streak}기 연속 확대",
                float(streak),
            )
        )

    return anomalies


# ── Big4 감사법인 목록 ──

_BIG4_KEYWORDS = ["삼일", "PwC", "삼정", "KPMG", "한영", "EY", "안진", "Deloitte"]


def _isBig4(auditor: str | None) -> bool:
    """감사인이 Big4인지 판정."""
    if not auditor:
        return False
    return any(kw in auditor for kw in _BIG4_KEYWORDS)


def detectAuditRedFlags(auditData: AuditDataForAnomaly | None) -> list[Anomaly]:
    """감사 Red Flag 탐지 — PCAOB AS 3101, ISA 570/701/705, SOX 302/404.

    6개 항목: 감사인 교체, 감사보수 급변, 계속기업 불확실성,
    내부통제 취약점, 감사의견 비적정, KAM 급증.
    """
    if auditData is None:
        return []

    anomalies: list[Anomaly] = []

    # 1. 감사인 비정상 교체 (PCAOB AS 3101)
    auditors = auditData.auditors
    if len(auditors) >= 2:
        # 고유 감사인 수 (None 제외)
        unique = [a for a in auditors if a is not None]
        changes = []
        for i in range(1, len(unique)):
            if unique[i] != unique[i - 1]:
                changes.append((i, unique[i - 1], unique[i]))

        if len(changes) >= 3:
            anomalies.append(
                Anomaly(
                    "danger",
                    "audit",
                    f"감사인 {len(changes)}회 교체 (5년 내) — 빈번 교체 Red Flag",
                    float(len(changes)),
                )
            )
        elif len(changes) >= 2:
            anomalies.append(Anomaly("danger", "audit", "감사인 2년 이내 재교체 — Red Flag", float(len(changes))))
        elif len(changes) == 1:
            _, prev, curr = changes[0]
            if _isBig4(prev) and not _isBig4(curr):
                anomalies.append(Anomaly("warning", "audit", f"Big4→비Big4 교체 ({prev} → {curr})", 1.0))

    # 2. 감사보수 급변 (ISA 260, ±30% YoY)
    fees = auditData.fees
    if len(fees) >= 2:
        validFees = [(i, f) for i, f in enumerate(fees) if f is not None and f > 0]
        if len(validFees) >= 2:
            _, prevFee = validFees[-2]
            _, currFee = validFees[-1]
            feeChange = (currFee - prevFee) / prevFee * 100
            if abs(feeChange) > 30:
                direction = "급증" if feeChange > 0 else "급감"
                anomalies.append(Anomaly("warning", "audit", f"감사보수 {direction} ({feeChange:+.0f}%)", feeChange))

    # 3. 계속기업 불확실성 (ISA 570)
    if auditData.hasGoingConcern:
        anomalies.append(Anomaly("danger", "audit", "계속기업 불확실성 — 감사인 보고 (ISA 570)", 1.0))

    # 4. 내부통제 취약점 (SOX 302/404)
    if auditData.hasInternalControlWeakness:
        anomalies.append(Anomaly("danger", "audit", "내부회계관리제도 취약점 보고 (SOX 302/404)", 1.0))

    # 5. 감사의견 비적정 (ISA 705)
    opinions = auditData.opinions
    if opinions:
        latest = None
        for v in reversed(opinions):
            if v is not None:
                latest = v
                break
        if latest is not None and "적정" not in str(latest):
            anomalies.append(Anomaly("danger", "audit", f"감사의견 비적정: {latest} (ISA 705)", 1.0))

    # 6. KAM 급증 (ISA 701)
    kamCounts = auditData.kamCounts
    if len(kamCounts) >= 2:
        validKam = [(i, k) for i, k in enumerate(kamCounts) if k is not None]
        if len(validKam) >= 2:
            _, prevKam = validKam[-2]
            _, currKam = validKam[-1]
            if currKam > prevKam + 2:
                anomalies.append(
                    Anomaly(
                        "info",
                        "audit",
                        f"KAM 급증 ({prevKam}건 → {currKam}건) — 감사인 위험 인식 확대",
                        float(currKam - prevKam),
                    )
                )

    return anomalies


def detectBenfordAnomaly(aSeries: dict) -> list[Anomaly]:
    """Benford's Law 이상치 탐지 — 회계 조작 의심 신호.

    Nigrini (1996), AICPA 공식 감사 절차.
    재무제표 수치의 첫째 유효 자릿수 분포를 Benford 기대 분포와 비교.
    χ² > 15.51 (df=8, p<0.05) → warning, χ² > 20.09 (p<0.01) → danger.
    """
    anomalies: list[Anomaly] = []

    # 모든 IS/BS/CF 값에서 첫째 유효 자릿수 추출
    digits: list[int] = []
    for sjDiv in ("IS", "BS", "CF"):
        section = aSeries.get(sjDiv, {})
        for _key, vals in section.items():
            if not isinstance(vals, list):
                continue
            for v in vals:
                if v is None or not isinstance(v, (int, float)):
                    continue
                if v == 0 or not math.isfinite(v):
                    continue
                # 첫째 유효 자릿수 추출
                absV = abs(v)
                d = int(str(absV).lstrip("0").lstrip(".").lstrip("0")[:1]) if absV != 0 else 0
                if 1 <= d <= 9:
                    digits.append(d)

    # 최소 50개 이상 숫자 필요
    if len(digits) < 50:
        return anomalies

    n = len(digits)
    # Benford 기대 분포: P(d) = log10(1 + 1/d)
    expected = {d: math.log10(1 + 1 / d) for d in range(1, 10)}
    observed = {d: 0 for d in range(1, 10)}
    for d in digits:
        observed[d] += 1

    # χ² 검정
    chi2 = 0.0
    for d in range(1, 10):
        exp_count = expected[d] * n
        obs_count = observed[d]
        if exp_count > 0:
            chi2 += (obs_count - exp_count) ** 2 / exp_count

    # df=8, p<0.01 → 20.09, p<0.05 → 15.51
    if chi2 > 20.09:
        anomalies.append(
            Anomaly(
                "danger",
                "earningsQuality",
                f"Benford's Law 위반 (χ²={chi2:.1f}, p<0.01) — 회계 수치 분포 이상",
                chi2,
            )
        )
    elif chi2 > 15.51:
        anomalies.append(
            Anomaly(
                "warning",
                "earningsQuality",
                f"Benford's Law 이탈 (χ²={chi2:.1f}, p<0.05) — 회계 수치 분포 주의",
                chi2,
            )
        )

    return anomalies


def detectRevenueQuality(aSeries: dict) -> list[Anomaly]:
    """매출 품질 탐지 — Dechow & Dichev (2002).

    OCF/Revenue 비율 추세: 매출이 늘어도 현금이 안 들어오면 의심.
    - OCF/Revenue < 0 (매출 흑자인데 영업CF 적자) → danger
    - OCF/Revenue 3기 연속 하락 → warning
    - 매출채권 증가율 > 매출 증가율 × 1.5 (3기 연속) → warning
    """
    anomalies: list[Anomaly] = []

    revVals = getAnnualValues(aSeries, "IS", "sales")
    cfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    arVals = getAnnualValues(aSeries, "BS", "trade_and_other_receivables")

    # OCF/Revenue 비율 시계열
    n = min(len(revVals), len(cfVals)) if revVals and cfVals else 0
    ocfRevRatios: list[float | None] = []
    for i in range(n):
        rv = revVals[i]
        cf = cfVals[i]
        if rv is not None and cf is not None and rv > 0:
            ocfRevRatios.append(cf / rv)
        else:
            ocfRevRatios.append(None)

    # OCF/Revenue < 0 (최신기, 매출 흑자인데 영업CF 적자)
    if ocfRevRatios:
        latest = None
        for v in reversed(ocfRevRatios):
            if v is not None:
                latest = v
                break
        if latest is not None and latest < 0:
            anomalies.append(
                Anomaly(
                    "danger",
                    "earningsQuality",
                    f"매출 대비 영업CF 적자 (OCF/Revenue={latest:.1%}) — 매출 품질 의심",
                    latest * 100,
                )
            )

    # OCF/Revenue 3기 연속 하락
    validRatios = [r for r in ocfRevRatios if r is not None]
    if len(validRatios) >= 3:
        consecutive_decline = 0
        for i in range(len(validRatios) - 1, 0, -1):
            if validRatios[i] < validRatios[i - 1]:
                consecutive_decline += 1
            else:
                break
        if consecutive_decline >= 3:
            anomalies.append(
                Anomaly(
                    "warning",
                    "earningsQuality",
                    f"OCF/Revenue {consecutive_decline}기 연속 하락 — 매출 품질 악화 추세",
                    float(consecutive_decline),
                )
            )

    # 매출채권 증가율 > 매출 증가율 × 1.5 (3기 연속)
    if arVals and revVals and len(arVals) >= 3 and len(revVals) >= 3:
        n2 = min(len(arVals), len(revVals))
        arGrowths: list[float | None] = []
        revGrowths: list[float | None] = []
        for i in range(1, n2):
            ar_prev, ar_curr = arVals[i - 1], arVals[i]
            rv_prev, rv_curr = revVals[i - 1], revVals[i]
            if ar_prev and ar_prev > 0 and ar_curr is not None:
                arGrowths.append((ar_curr - ar_prev) / ar_prev * 100)
            else:
                arGrowths.append(None)
            if rv_prev and rv_prev > 0 and rv_curr is not None:
                revGrowths.append((rv_curr - rv_prev) / rv_prev * 100)
            else:
                revGrowths.append(None)

        # 최근 3기 매출채권 증가 > 매출 × 1.5
        consecutive_ar = 0
        for i in range(len(arGrowths) - 1, -1, -1):
            ag = arGrowths[i]
            rg = revGrowths[i]
            if ag is not None and rg is not None and rg >= 0 and ag > rg * 1.5 and ag > 10:
                consecutive_ar += 1
            else:
                break
        if consecutive_ar >= 3:
            anomalies.append(
                Anomaly(
                    "warning",
                    "earningsQuality",
                    f"매출채권 증가율 > 매출 증가율×1.5 {consecutive_ar}기 연속 — 수금 품질 의심",
                    float(consecutive_ar),
                )
            )

    return anomalies


def runAnomalyDetection(
    aSeries: dict,
    isFinancial: bool = False,
    *,
    auditData: AuditDataForAnomaly | None = None,
) -> list[Anomaly]:
    """전체 이상치 탐지 실행.

    Args:
        aSeries: 연간 재무 시계열.
        isFinancial: 금융업 여부.
        auditData: 감사 데이터 (None이면 감사 탐지기 스킵, 하위호환).
    """
    anomalies: list[Anomaly] = []
    anomalies.extend(detectEarningsQuality(aSeries, isFinancial))
    anomalies.extend(detectWorkingCapitalAnomaly(aSeries))
    anomalies.extend(detectBalanceSheetShift(aSeries))
    anomalies.extend(detectCashBurn(aSeries, isFinancial))
    anomalies.extend(detectMarginDivergence(aSeries))
    anomalies.extend(detectFinancialSectorAnomaly(aSeries, isFinancial))
    anomalies.extend(detectTrendDeterioration(aSeries, isFinancial))
    anomalies.extend(detectCCCDeterioration(aSeries, isFinancial))
    # 세계적 감사 기법 — Phase 086
    anomalies.extend(detectAuditRedFlags(auditData))
    anomalies.extend(detectBenfordAnomaly(aSeries))
    anomalies.extend(detectRevenueQuality(aSeries))

    anomalies.sort(key=lambda a: {"danger": 0, "warning": 1, "info": 2}.get(a.severity, 3))
    return anomalies
