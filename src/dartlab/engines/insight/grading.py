"""7영역 인사이트 등급 분석.

영역: performance, profitability, health, cashflow, governance, risk, opportunity
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from dartlab.engines.common.finance.extract import getAnnualValues, getLatest
from dartlab.engines.common.finance.ratios import RatioResult
from dartlab.engines.insight.benchmark import getBenchmark, sectorAdjustment
from dartlab.engines.insight.detector import detectIncompleteYear
from dartlab.engines.insight.types import Flag, InsightResult
from dartlab.engines.sector.types import Sector

if TYPE_CHECKING:
    from dartlab.engines.dart.company import Company


def _scoreToGrade(score: int, maxScore: int) -> str:
    ratio = score / maxScore if maxScore > 0 else 0
    if ratio >= 0.8:
        return "A"
    if ratio >= 0.5:
        return "B"
    if ratio >= 0.2:
        return "C"
    if ratio >= 0:
        return "D"
    return "F"


def _getGrowthYoY(annualVals: list[Optional[float]]) -> Optional[float]:
    valid = [(i, v) for i, v in enumerate(annualVals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    if prev and prev != 0:
        return ((curr - prev) / abs(prev)) * 100
    return None


def _getVolatility(qVals: list[Optional[float]]) -> Optional[float]:
    recent = [v for v in qVals[-4:] if v is not None]
    if len(recent) < 2:
        return None
    changes = []
    for i in range(len(recent) - 1):
        if recent[i] != 0:
            changes.append(abs((recent[i + 1] - recent[i]) / recent[i]) * 100)
    return max(changes) if changes else None


def analyzePerformance(
    aSeries: dict,
    aYears: list[str],
    qSeries: dict,
    qPeriods: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """실적 성장성 분석."""
    lastYear, qCount = detectIncompleteYear(qPeriods)
    incomplete = qCount < 4

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")

    if incomplete and len(aYears) > 1:
        useRevVals = revVals[:-1]
        useOpVals = opVals[:-1]
        correctionNote = f"(불완전연도 {lastYear} {qCount}Q 제외)"
    else:
        useRevVals = revVals
        useOpVals = opVals
        correctionNote = ""

    if isFinancial and not any(v is not None for v in useRevVals):
        useRevVals = useOpVals
        revLabel = "영업이익"
    else:
        revLabel = "매출"

    revGrowth = _getGrowthYoY(useRevVals)
    opGrowth = _getGrowthYoY(useOpVals)

    qRevVals = qSeries.get("IS", {}).get("sales", [])
    if isFinancial and not any(v is not None for v in qRevVals):
        qRevVals = qSeries.get("IS", {}).get("operating_profit", [])
    revVolatility = _getVolatility(qRevVals)
    qOpVals = qSeries.get("IS", {}).get("operating_profit", [])
    opVolatility = _getVolatility(qOpVals)

    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    if correctionNote:
        details.append(correctionNote)

    if revGrowth is not None:
        if revGrowth > 20:
            details.append(f"{revLabel} 고성장 (+{revGrowth:.1f}%)")
            opps.append(Flag("strong", "growth", f"{revLabel} {revGrowth:.1f}% 성장"))
            score += 3
        elif revGrowth > 10:
            details.append(f"{revLabel} 성장세 양호 (+{revGrowth:.1f}%)")
            score += 2
        elif revGrowth > 0:
            details.append(f"{revLabel} 소폭 성장 (+{revGrowth:.1f}%)")
            score += 1
        elif revGrowth > -10:
            details.append(f"{revLabel} 소폭 감소 ({revGrowth:.1f}%)")
        else:
            details.append(f"{revLabel} 급감 ({revGrowth:.1f}%)")
            risks.append(Flag("danger", "finance", f"{revLabel} {revGrowth:.1f}% 급감"))
            score -= 2

    if opGrowth is not None and not isFinancial:
        if opGrowth > 50:
            details.append(f"영업이익 급증 (+{opGrowth:.1f}%)")
            opps.append(Flag("strong", "growth", f"영업이익 {opGrowth:.1f}% 급증"))
            score += 3
        elif opGrowth > 15:
            details.append(f"영업이익 증가 (+{opGrowth:.1f}%)")
            score += 2
        elif opGrowth < -30:
            details.append(f"영업이익 급감 ({opGrowth:.1f}%)")
            risks.append(Flag("danger", "finance", f"영업이익 {opGrowth:.1f}% 급감"))
            score -= 2
        elif opGrowth < -10:
            details.append(f"영업이익 감소 ({opGrowth:.1f}%)")
            risks.append(Flag("warning", "finance", f"영업이익 {opGrowth:.1f}% 감소"))
            score -= 1

    if revVolatility is not None and revVolatility > 30:
        details.append(f"{revLabel} 변동성 높음 (분기 최대 {revVolatility:.1f}%)")
        risks.append(Flag("warning", "finance", f"{revLabel} 변동성 {revVolatility:.1f}%"))

    if not isFinancial and opVolatility is not None and opVolatility > 50:
        details.append(f"영업이익 변동성 높음 (분기 최대 {opVolatility:.1f}%)")
        risks.append(Flag("warning", "finance", f"영업이익 변동성 {opVolatility:.1f}%"))

    grade = _scoreToGrade(score, 6)
    if revGrowth is None:
        summary = "실적 데이터 부족"
    elif revGrowth > 20 and opGrowth and opGrowth > 30:
        summary = f"{revLabel}·이익 고성장"
    elif revGrowth > 10 and opGrowth and opGrowth > 10:
        summary = f"{revLabel}·이익 동반 성장"
    elif revGrowth > 0:
        summary = f"{revLabel} 성장세 유지"
    elif revGrowth > -10:
        summary = f"{revLabel} 정체"
    else:
        summary = f"{revLabel} 감소 추세"

    return InsightResult(grade, summary, details, risks, opps)


def analyzeProfitability(
    ratios: RatioResult,
    aSeries: dict,
    isFinancial: bool = False,
    sector: Sector = Sector.UNKNOWN,
) -> InsightResult:
    """수익성 분석."""
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    if isFinancial:
        return _analyzeProfitabilityFinancial(aSeries, details, risks, opps)

    om = ratios.operatingMargin
    nm = ratios.netMargin
    roe = ratios.roe
    roa = ratios.roa

    if om is not None:
        if om > 20:
            details.append(f"영업이익률 우수 ({om:.1f}%)")
            opps.append(Flag("strong", "finance", f"영업이익률 {om:.1f}%"))
            score += 3
        elif om > 10:
            details.append(f"영업이익률 양호 ({om:.1f}%)")
            score += 2
        elif om > 5:
            details.append(f"영업이익률 보통 ({om:.1f}%)")
            score += 1
        elif om < 0:
            details.append(f"영업적자 ({om:.1f}%)")
            risks.append(Flag("danger", "finance", f"영업이익률 {om:.1f}% — 적자"))
            score -= 2
        else:
            details.append(f"영업이익률 저조 ({om:.1f}%)")
            score -= 1

    if om is not None and nm is not None and om != 0:
        gap = nm - om
        gapRatio = (gap / abs(om)) * 100
        if abs(gapRatio) > 50:
            if gap > 0:
                details.append(f"영업외수익 발생 (순이익률 {nm:.1f}% > 영업이익률 {om:.1f}%)")
                risks.append(Flag("warning", "finance", "본업 외 수익에 의존"))
            else:
                details.append(f"영업외비용 발생 (순이익률 {nm:.1f}% < 영업이익률 {om:.1f}%)")
                risks.append(Flag("warning", "finance", "영업외비용 확인 필요"))
        elif abs(gap) < 2 and nm > 0:
            details.append("영업이익≈순이익 — 본업 중심 수익구조")
            opps.append(Flag("positive", "finance", "건전한 수익구조"))

    if roe is not None:
        if roe > 20:
            details.append(f"ROE 우수 ({roe:.1f}%)")
            opps.append(Flag("strong", "finance", f"ROE {roe:.1f}%"))
            score += 2
        elif roe > 10:
            details.append(f"ROE 양호 ({roe:.1f}%)")
            score += 1
        elif roe < 5:
            details.append(f"ROE 저조 ({roe:.1f}%)")

    if roe is not None and roa is not None and roa > 0:
        leverage = roe / roa
        if leverage > 4:
            details.append(f"높은 레버리지로 ROE 달성 (ROE/ROA={leverage:.1f}x)")
            risks.append(Flag("warning", "finance", f"ROE/ROA {leverage:.1f}x — 부채 활용 높음"))
        elif leverage < 1.5 and roe > 15:
            details.append("낮은 레버리지로 고ROE — 진성 수익성")
            opps.append(Flag("strong", "finance", f"레버리지 {leverage:.1f}x로 ROE {roe:.1f}%"))

    bm = getBenchmark(sector)
    omAdj = sectorAdjustment(om, bm.omMedian, bm.omQ1, bm.omQ3)
    roeAdj = sectorAdjustment(roe, bm.roeMedian, bm.roeQ1, bm.roeQ3)
    adj = omAdj + roeAdj
    if adj != 0:
        score += adj
        direction = "상향" if adj > 0 else "하향"
        details.append(f"[섹터 보정 {direction}: {sector.value} 대비 OM{'↑' if omAdj > 0 else '↓' if omAdj < 0 else '→'} ROE{'↑' if roeAdj > 0 else '↓' if roeAdj < 0 else '→'}]")

    grade = _scoreToGrade(score, 5)
    summary = "수익성 " + ("우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요")
    return InsightResult(grade, summary, details, risks, opps)


def _analyzeProfitabilityFinancial(
    aSeries: dict,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> InsightResult:
    """금융업 전용 수익성 분석 (ROE/ROA/CIR)."""
    details.append("[금융업 수익성 기준 적용]")
    score = 0
    netIncome = getLatest(aSeries, "IS", "net_profit")
    totalAssets = getLatest(aSeries, "BS", "total_assets")
    totalEquity = getLatest(aSeries, "BS", "owners_of_parent_equity") or getLatest(aSeries, "BS", "total_stockholders_equity")
    opIncome = getLatest(aSeries, "IS", "operating_profit")
    opExpense = getLatest(aSeries, "IS", "operating_expense")

    roe = (netIncome / totalEquity) * 100 if netIncome and totalEquity and totalEquity > 0 else None
    roa = (netIncome / totalAssets) * 100 if netIncome and totalAssets and totalAssets > 0 else None
    cir = (opExpense / (opExpense + opIncome)) * 100 if opExpense is not None and opIncome and opIncome > 0 else None

    if roe is not None:
        if roe > 10:
            details.append(f"ROE 우수 ({roe:.1f}%)")
            opps.append(Flag("strong", "finance", f"금융업 ROE {roe:.1f}%"))
            score += 3
        elif roe > 8:
            details.append(f"ROE 양호 ({roe:.1f}%)")
            score += 2
        elif roe > 5:
            details.append(f"ROE 보통 ({roe:.1f}%)")
            score += 1
        else:
            details.append(f"ROE 저조 ({roe:.1f}%)")
            risks.append(Flag("warning", "finance", f"금융업 ROE {roe:.1f}%"))

    if roa is not None:
        if roa > 0.7:
            details.append(f"ROA 양호 ({roa:.2f}%)")
            score += 1
        elif roa > 0.4:
            details.append(f"ROA 보통 ({roa:.2f}%)")
        elif roa > 0:
            details.append(f"ROA 저조 ({roa:.2f}%)")
        else:
            details.append(f"ROA 적자 ({roa:.2f}%)")
            risks.append(Flag("danger", "finance", f"금융업 ROA {roa:.2f}%"))
            score -= 2

    if cir is not None:
        if cir < 50:
            details.append(f"CIR {cir:.1f}% — 효율적 운영")
            opps.append(Flag("positive", "finance", f"CIR {cir:.1f}%"))
            score += 1
        elif cir < 60:
            details.append(f"CIR {cir:.1f}% — 보통")
        else:
            details.append(f"CIR {cir:.1f}% — 비효율")
            risks.append(Flag("warning", "finance", f"CIR {cir:.1f}%"))

    grade = _scoreToGrade(score, 5)
    summary = "금융업 수익성 " + ("우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요")
    return InsightResult(grade, summary, details, risks, opps)


def analyzeHealth(ratios: RatioResult, isFinancial: bool = False) -> InsightResult:
    """재무건전성 분석."""
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    dr = ratios.debtRatio
    cr = ratios.currentRatio

    if isFinancial:
        details.append("[금융업 기준 적용]")
        if dr is not None:
            if dr < 1000:
                details.append(f"부채비율 {dr:.0f}% — 금융업 양호")
                opps.append(Flag("positive", "finance", f"금융업 부채비율 {dr:.0f}%"))
                score += 3
            elif dr < 1500:
                details.append(f"부채비율 {dr:.0f}% — 금융업 보통")
                score += 1
            elif dr < 2000:
                details.append(f"부채비율 {dr:.0f}% — 금융업 다소 높음")
            else:
                details.append(f"부채비율 {dr:.0f}% — 금융업 과다")
                risks.append(Flag("warning", "finance", f"금융업 부채비율 {dr:.0f}%"))
                score -= 1
    else:
        if dr is not None:
            if dr < 50:
                details.append(f"부채비율 매우 양호 ({dr:.0f}%)")
                opps.append(Flag("strong", "finance", f"부채비율 {dr:.0f}%"))
                score += 3
            elif dr < 100:
                details.append(f"부채비율 양호 ({dr:.0f}%)")
                opps.append(Flag("positive", "finance", f"부채비율 {dr:.0f}%"))
                score += 2
            elif dr < 150:
                details.append(f"부채비율 보통 ({dr:.0f}%)")
                score += 1
            elif dr < 200:
                details.append(f"부채비율 다소 높음 ({dr:.0f}%)")
            else:
                details.append(f"부채비율 과다 ({dr:.0f}%)")
                risks.append(Flag("warning", "finance", f"부채비율 {dr:.0f}%"))
                score -= 1

        if cr is not None:
            if cr > 200:
                details.append(f"유동성 매우 충분 ({cr:.0f}%)")
                opps.append(Flag("positive", "finance", f"유동비율 {cr:.0f}%"))
                score += 2
            elif cr > 150:
                details.append(f"유동성 충분 ({cr:.0f}%)")
                score += 1
            elif cr > 100:
                details.append(f"유동성 보통 ({cr:.0f}%)")
            elif cr < 100:
                details.append(f"유동성 부족 ({cr:.0f}%)")
                risks.append(Flag("warning", "finance", f"유동비율 {cr:.0f}%"))
                score -= 1

    grade = _scoreToGrade(score, 5)
    label = "금융업 재무건전성" if isFinancial else "재무건전성"
    summary = f"{label} " + ("우수" if score >= 4 else "안정" if score >= 2 else "보통" if score >= 0 else "주의 필요")
    return InsightResult(grade, summary, details, risks, opps)


def analyzeCashflow(
    ratios: RatioResult,
    aSeries: dict,
    isFinancial: bool = False,
) -> InsightResult:
    """현금흐름 분석."""
    if isFinancial:
        return _analyzeCashflowFinancial(aSeries)

    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    opCF = ratios.operatingCashflowTTM
    fcf = ratios.fcf
    revenue = ratios.revenueTTM

    if opCF is not None:
        if opCF > 0:
            details.append("영업활동 현금 창출 양호")
            score += 2
        else:
            details.append("영업활동 현금 적자")
            risks.append(Flag("danger", "finance", "영업CF 적자"))
            score -= 2

    if fcf is not None:
        if fcf > 0:
            if revenue and revenue > 0:
                fcfMargin = (fcf / revenue) * 100
                if fcfMargin > 15:
                    details.append(f"FCF 마진 우수 ({fcfMargin:.1f}%)")
                    opps.append(Flag("strong", "cashflow", f"FCF 마진 {fcfMargin:.1f}%"))
                    score += 3
                elif fcfMargin > 5:
                    details.append(f"FCF 마진 양호 ({fcfMargin:.1f}%)")
                    opps.append(Flag("positive", "cashflow", f"FCF 마진 {fcfMargin:.1f}%"))
                    score += 2
                else:
                    details.append(f"FCF 양호, 마진 저조 ({fcfMargin:.1f}%)")
                    score += 1
            else:
                details.append("FCF 양호")
                score += 1
        elif opCF and opCF > 0:
            details.append("FCF 적자 — 투자 확대 중")
            opps.append(Flag("positive", "growth", "적극 투자 (영업CF 양호)"))
        else:
            details.append("FCF 적자 — 현금 부족")
            risks.append(Flag("warning", "finance", "FCF + 영업CF 부진"))
            score -= 1

    cfVals = getAnnualValues(aSeries, "CF", "operating_cashflow")
    validCf = [v for v in cfVals if v is not None]
    if len(validCf) >= 2:
        improving = validCf[-1] > validCf[-2]
        if improving and validCf[-1] > 0:
            details.append("영업CF 개선 추세")
            score += 1
        elif not improving and validCf[-1] < validCf[-2]:
            details.append("영업CF 악화 추세")

    grade = _scoreToGrade(score, 6)
    summary = "현금흐름 " + ("우수" if score >= 5 else "양호" if score >= 2 else "보통" if score >= 0 else "주의")
    return InsightResult(grade, summary, details, risks, opps)


def _analyzeCashflowFinancial(aSeries: dict) -> InsightResult:
    """금융업 전용 현금흐름 분석."""
    details: list[str] = ["[금융업 현금흐름]"]
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0

    opCF = getLatest(aSeries, "CF", "operating_cashflow")
    dividendsPaid = getLatest(aSeries, "CF", "dividends_paid")
    netIncome = getLatest(aSeries, "IS", "net_profit")

    if opCF is not None:
        details.append(f"영업CF: {opCF / 1e8:,.0f}억")

    if dividendsPaid is not None and dividendsPaid > 0:
        details.append(f"배당 지급: {dividendsPaid / 1e8:,.0f}억")
        opps.append(Flag("positive", "shareholder", f"배당 지급 {dividendsPaid / 1e8:,.0f}억"))
        score += 1

    if netIncome is not None and netIncome > 0:
        details.append(f"순이익 {netIncome / 1e8:,.0f}억")
        score += 2

    grade = _scoreToGrade(score, 3)
    summary = "금융업 현금흐름 " + ("양호" if score >= 2 else "보통" if score >= 0 else "주의")
    return InsightResult(grade, summary, details, risks, opps)


def analyzeGovernance(company: Company | None) -> InsightResult:
    """지배구조 분석."""
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    maxScore = 0

    if company is None or company.report is None:
        return InsightResult("N", "정기보고서 데이터 없음")

    rpt = company.report

    major = rpt.majorHolder
    if major is not None and major.totalShareRatio:
        maxScore += 3
        latest = None
        for v in reversed(major.totalShareRatio):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if latest > 50:
                details.append(f"최대주주 지분 {latest:.1f}% — 지배력 안정")
                opps.append(Flag("positive", "governance", f"최대주주 {latest:.1f}%"))
                score += 3
            elif latest > 30:
                details.append(f"최대주주 지분 {latest:.1f}% — 적정 수준")
                score += 2
            elif latest > 20:
                details.append(f"최대주주 지분 {latest:.1f}%")
                score += 1
            else:
                details.append(f"최대주주 지분 {latest:.1f}% — 경영권 분산")
                risks.append(Flag("warning", "governance", f"최대주주 {latest:.1f}%"))

    audit = rpt.audit
    if audit is not None and audit.opinions:
        maxScore += 2
        latest = None
        for v in reversed(audit.opinions):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if "적정" in str(latest):
                details.append("감사의견: 적정")
                score += 2
            else:
                details.append(f"감사의견: {latest}")
                risks.append(Flag("danger", "audit", f"감사의견 비적정: {latest}"))
                score -= 2

    div = rpt.dividend
    if div is not None and div.dps:
        maxScore += 3
        recentDps = [d for d in div.dps[-3:] if d is not None]
        if recentDps and all(d > 0 for d in recentDps):
            if len(recentDps) >= 3:
                details.append(f"3년 연속 배당 (DPS: {recentDps[-1]:,.0f}원)")
                opps.append(Flag("positive", "shareholder", "안정적 배당"))
                score += 3
            else:
                details.append(f"배당 실시 (DPS: {recentDps[-1]:,.0f}원)")
                score += 2
        elif recentDps and recentDps[-1] > 0:
            details.append(f"배당 재개 (DPS: {recentDps[-1]:,.0f}원)")
            score += 1
        else:
            details.append("무배당")
            risks.append(Flag("warning", "shareholder", "무배당"))

    if maxScore == 0:
        return InsightResult("N", "지배구조 데이터 없음")

    grade = _scoreToGrade(score, maxScore)
    summary = "지배구조 " + (
        "우수" if grade == "A" else
        "안정" if grade == "B" else
        "보통" if grade == "C" else
        "주의" if grade == "D" else "위험"
    )
    return InsightResult(grade, summary, details, risks, opps)


def analyzeRiskSummary(insights: dict[str, InsightResult]) -> InsightResult:
    """리스크 종합 분석."""
    allRisks: list[Flag] = []
    for key in ["performance", "profitability", "health", "cashflow", "governance"]:
        if key in insights:
            allRisks.extend(insights[key].risks)

    if not allRisks:
        return InsightResult("A", "특별한 리스크 없음", ["주요 재무지표 양호"])

    dangerCount = sum(1 for r in allRisks if r.level == "danger")
    warningCount = sum(1 for r in allRisks if r.level == "warning")

    if dangerCount >= 2:
        grade = "F"
        summary = f"중대 리스크 {dangerCount}건"
    elif dangerCount == 1:
        grade = "D"
        summary = f"리스크 경고 (위험 {dangerCount}, 주의 {warningCount})"
    elif warningCount > 3:
        grade = "D"
        summary = f"다수 주의 ({warningCount}건)"
    elif warningCount > 1:
        grade = "C"
        summary = f"일부 주의 ({warningCount}건)"
    else:
        grade = "B"
        summary = "경미한 주의 사항"

    return InsightResult(grade, summary, [r.text for r in allRisks], allRisks)


def analyzeOpportunitySummary(insights: dict[str, InsightResult]) -> InsightResult:
    """기회 종합 분석."""
    allOpps: list[Flag] = []
    for key in ["performance", "profitability", "health", "cashflow", "governance"]:
        if key in insights:
            allOpps.extend(insights[key].opportunities)

    if not allOpps:
        return InsightResult("D", "특별한 투자 기회 없음")

    strongCount = sum(1 for o in allOpps if o.level == "strong")
    positiveCount = sum(1 for o in allOpps if o.level == "positive")
    total = strongCount + positiveCount

    if strongCount >= 3 and total >= 5:
        grade = "A"
        summary = f"투자 매력 높음 ({strongCount}강점, {positiveCount}긍정)"
    elif strongCount >= 2:
        grade = "B"
        summary = f"투자 매력 있음 ({strongCount}강점)"
    elif strongCount >= 1 or positiveCount >= 3:
        grade = "C"
        summary = f"일부 긍정 ({strongCount}강점, {positiveCount}긍정)"
    elif positiveCount >= 1:
        grade = "D"
        summary = f"긍정 요소 미약 ({positiveCount}건)"
    else:
        grade = "F"
        summary = "투자 매력 없음"

    return InsightResult(grade, summary, [o.text for o in allOpps], opportunities=allOpps)
