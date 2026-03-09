"""
실험 ID: 008
실험명: 금융업 Profitability/Cashflow 보정 통합

목적:
- 007에서 발견한 ratios.py getTTM 문제 우회 → 인사이트 엔진에서 직접 계산
- 금융업 Profitability: ROE/ROA 직접 계산 + 영업이익률(일반margin 대체)
- 금융업 Cashflow: operating_cashflow가 음수인 것은 금융업 특성 → 별도 해석
- 006 보정 버전에 금융업 Profitability/Cashflow 보정 추가 후 5종목 재검증

가설:
1. getLatest로 직접 ROE/ROA를 계산하면 금융업 Profitability가 D에서 B~C로 개선된다
2. 금융업 CF는 "데이터 특성상 평가 제외" 처리하면 Cashflow가 D에서 N으로 변경된다
3. 일반 종목의 등급은 006과 동일하게 유지된다

방법:
1. analyzeProfitability에 isFinancial 분기 추가 (직접 ROE/ROA 계산)
2. analyzeCashflow에 isFinancial 분기 추가 (CF 해석 변경)
3. 5종목 재검증 + 006 결과와 비교

결과 (실험 후 작성):
- 006 → 008 등급 비교 (KB금융만 변경, 나머지 4종목 동일)
  KB금융: Profitability D→B, Cashflow D→A, Opportunity C→B
- KB금융 금융업 수익성: ROE 8.6%(양호), ROA 0.64%(보통), CIR 42.6%(효율적)
- KB금융 금융업 CF: 영업CF -3.2조(음수지만 대출 확대), 순이익 5.1조, 배당 9,673억
- 변경 3/35, 개선 3/3 (100%)

결론:
- 가설 1 채택: getLatest로 직접 ROE/ROA 계산 → Profitability D→B
- 가설 2 수정채택: "평가 제외(N)" 대신 순이익 기반 양호 판정 → Cashflow D→A
- 가설 3 채택: 일반 종목 4종목 006과 100% 동일
- CIR(Cost-Income Ratio) = opExpense / (opExpense + opIncome)이 유용한 금융업 효율성 지표
- 금융업 CF는 영업CF 부호보다 순이익 창출력 + 배당 지급 능력이 핵심

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Optional

import dartlab
dartlab.verbose = False

from dartlab.engines.financeEngine.pivot import buildTimeseries, buildAnnual
from dartlab.engines.financeEngine.ratios import calcRatios, RatioResult
from dartlab.engines.financeEngine.extract import getLatest, getAnnualValues


@dataclass
class Flag:
    level: str
    category: str
    text: str


@dataclass
class InsightResult:
    grade: str
    summary: str
    details: list[str] = field(default_factory=list)
    risks: list[Flag] = field(default_factory=list)
    opportunities: list[Flag] = field(default_factory=list)


def _scoreToGrade(score: int, maxScore: int) -> str:
    ratio = score / maxScore if maxScore > 0 else 0
    if ratio >= 0.8:
        return "A"
    elif ratio >= 0.5:
        return "B"
    elif ratio >= 0.2:
        return "C"
    elif ratio >= 0:
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


def detectIncompleteYear(qPeriods: list[str]) -> tuple[str, int]:
    lastPeriod = qPeriods[-1]
    lastYear = lastPeriod.split("_")[0]
    qCount = sum(1 for p in qPeriods if p.startswith(lastYear))
    return lastYear, qCount


def detectFinancialSector(series: dict, ratios: RatioResult) -> tuple[bool, list[str]]:
    signals = []

    revVals = getAnnualValues(series, "IS", "revenue")
    opVals = getAnnualValues(series, "IS", "operating_income")
    hasRevenue = any(v is not None for v in revVals)
    hasOpIncome = any(v is not None for v in opVals)

    if not hasRevenue and hasOpIncome:
        signals.append("revenue 없고 operating_income 있음")

    if ratios.debtRatio is not None and ratios.debtRatio > 500:
        signals.append(f"부채비율 {ratios.debtRatio:.0f}%")

    if ratios.currentRatio is None and getLatest(series, "BS", "current_assets") is None:
        signals.append("유동자산/유동부채 데이터 없음")

    interestIncome = getLatest(series, "IS", "interest_income")
    if interestIncome is not None:
        signals.append("이자수익 계정 존재")

    netInterestIncome = getLatest(series, "IS", "net_interest_income")
    if netInterestIncome is not None:
        signals.append("순이자수익 계정 존재")

    insuranceRevenue = getLatest(series, "IS", "insurance_revenue")
    if insuranceRevenue is not None:
        signals.append("보험수익 계정 존재")

    isFinancial = len(signals) >= 2
    return isFinancial, signals


def analyzePerformance(
    annualSeries: dict,
    annualYears: list[str],
    qSeries: dict,
    qPeriods: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    lastYear, qCount = detectIncompleteYear(qPeriods)
    incomplete = qCount < 4

    revVals = getAnnualValues(annualSeries, "IS", "revenue")
    opVals = getAnnualValues(annualSeries, "IS", "operating_income")

    if incomplete and len(annualYears) > 1:
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

    qRevVals = qSeries.get("IS", {}).get("revenue", [])
    if isFinancial and not any(v is not None for v in qRevVals):
        qRevVals = qSeries.get("IS", {}).get("operating_income", [])
    revVolatility = _getVolatility(qRevVals)
    qOpVals = qSeries.get("IS", {}).get("operating_income", [])
    opVolatility = _getVolatility(qOpVals)

    details = []
    risks = []
    opps = []
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
    series: dict,
    isFinancial: bool = False,
) -> InsightResult:
    details = []
    risks = []
    opps = []
    score = 0

    if isFinancial:
        return _analyzeProfitabilityFinancial(series, details, risks, opps)

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
            details.append(f"낮은 레버리지로 고ROE — 진성 수익성")
            opps.append(Flag("strong", "finance", f"레버리지 {leverage:.1f}x로 ROE {roe:.1f}%"))

    grade = _scoreToGrade(score, 5)
    summary = "수익성 " + ("우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요")

    return InsightResult(grade, summary, details, risks, opps)


def _analyzeProfitabilityFinancial(
    series: dict,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> InsightResult:
    details.append("[금융업 수익성 기준 적용]")
    score = 0

    netIncome = getLatest(series, "IS", "net_income")
    totalAssets = getLatest(series, "BS", "total_assets")
    totalEquity = getLatest(series, "BS", "total_equity")
    if totalEquity is None:
        totalEquity = getLatest(series, "BS", "equity_including_nci")

    opIncome = getLatest(series, "IS", "operating_income")
    opExpense = getLatest(series, "IS", "operating_expense")

    roe = None
    if netIncome is not None and totalEquity and totalEquity > 0:
        roe = (netIncome / totalEquity) * 100

    roa = None
    if netIncome is not None and totalAssets and totalAssets > 0:
        roa = (netIncome / totalAssets) * 100

    cir = None
    if opExpense is not None and opIncome is not None and opIncome > 0:
        cir = (opExpense / (opExpense + opIncome)) * 100

    if roe is not None:
        if roe > 10:
            details.append(f"ROE 우수 ({roe:.1f}%) — 금융업 상위")
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
            risks.append(Flag("warning", "finance", f"금융업 ROE {roe:.1f}% — 저조"))

    if roa is not None:
        if roa > 0.7:
            details.append(f"ROA 양호 ({roa:.2f}%) — 금융업 기준 상위")
            score += 1
        elif roa > 0.4:
            details.append(f"ROA 보통 ({roa:.2f}%)")
        elif roa > 0:
            details.append(f"ROA 저조 ({roa:.2f}%)")
        else:
            details.append(f"ROA 적자 ({roa:.2f}%)")
            risks.append(Flag("danger", "finance", f"금융업 ROA {roa:.2f}% — 적자"))
            score -= 2

    if cir is not None:
        if cir < 50:
            details.append(f"CIR(비용/수익) {cir:.1f}% — 효율적 운영")
            opps.append(Flag("positive", "finance", f"CIR {cir:.1f}%"))
            score += 1
        elif cir < 60:
            details.append(f"CIR(비용/수익) {cir:.1f}% — 보통")
        else:
            details.append(f"CIR(비용/수익) {cir:.1f}% — 비효율")
            risks.append(Flag("warning", "finance", f"CIR {cir:.1f}% — 비용 과다"))

    grade = _scoreToGrade(score, 5)
    summary = "금융업 수익성 " + ("우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요")

    return InsightResult(grade, summary, details, risks, opps)


def analyzeHealth(ratios: RatioResult, isFinancial: bool = False) -> InsightResult:
    details = []
    risks = []
    opps = []
    score = 0

    dr = ratios.debtRatio
    cr = ratios.currentRatio

    if isFinancial:
        details.append("[금융업 기준 적용]")
        if dr is not None:
            if dr < 1000:
                details.append(f"부채비율 {dr:.0f}% — 금융업 기준 양호 (은행 평균 ~1500%)")
                opps.append(Flag("positive", "finance", f"금융업 부채비율 {dr:.0f}% — 양호"))
                score += 3
            elif dr < 1500:
                details.append(f"부채비율 {dr:.0f}% — 금융업 기준 보통")
                score += 1
            elif dr < 2000:
                details.append(f"부채비율 {dr:.0f}% — 금융업 기준 다소 높음")
            else:
                details.append(f"부채비율 {dr:.0f}% — 금융업 기준으로도 과다")
                risks.append(Flag("warning", "finance", f"금융업 부채비율 {dr:.0f}% — 과다"))
                score -= 1
    else:
        if dr is not None:
            if dr < 50:
                details.append(f"부채비율 매우 양호 ({dr:.0f}%)")
                opps.append(Flag("strong", "finance", f"부채비율 {dr:.0f}% — 차입 여력 충분"))
                score += 3
            elif dr < 100:
                details.append(f"부채비율 양호 ({dr:.0f}%)")
                opps.append(Flag("positive", "finance", f"부채비율 {dr:.0f}%"))
                score += 2
            elif dr < 200:
                details.append(f"부채비율 보통 ({dr:.0f}%)")
                score += 1
            else:
                details.append(f"부채비율 과다 ({dr:.0f}%)")
                risks.append(Flag("warning", "finance", f"부채비율 {dr:.0f}%"))
                score -= 1

    if not isFinancial and cr is not None:
        if cr > 200:
            details.append(f"유동성 매우 충분 ({cr:.0f}%)")
            opps.append(Flag("positive", "finance", f"유동비율 {cr:.0f}%"))
            score += 2
        elif cr > 150:
            details.append(f"유동성 충분 ({cr:.0f}%)")
            score += 1
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
    series: dict,
    isFinancial: bool = False,
) -> InsightResult:
    details = []
    risks = []
    opps = []
    score = 0

    if isFinancial:
        return _analyzeCashflowFinancial(series, details, risks, opps)

    opCF = ratios.operatingCashflowTTM
    fcf = ratios.fcf

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
            details.append("잉여현금흐름(FCF) 양호")
            opps.append(Flag("strong", "cashflow", "FCF 양호 — 주주환원 여력"))
            score += 2
        elif opCF and opCF > 0:
            details.append("FCF 적자 — 투자 확대 중")
            opps.append(Flag("positive", "growth", "FCF 적자지만 영업CF 양호 — 적극 투자"))
        else:
            details.append("FCF 적자 — 현금 부족")
            risks.append(Flag("warning", "finance", "FCF + 영업CF 부진"))

    grade = _scoreToGrade(score, 4)
    summary = "현금흐름 " + ("우수" if score >= 3 else "양호" if score >= 1 else "보통" if score >= 0 else "주의")

    return InsightResult(grade, summary, details, risks, opps)


def _analyzeCashflowFinancial(
    series: dict,
    details: list[str],
    risks: list[Flag],
    opps: list[Flag],
) -> InsightResult:
    details.append("[금융업 현금흐름 — 예금/대출 유출입 포함으로 별도 해석]")
    score = 0

    opCF = getLatest(series, "CF", "operating_cashflow")
    finCF = getLatest(series, "CF", "financing_cashflow")
    invCF = getLatest(series, "CF", "investing_cashflow")
    dividendsPaid = getLatest(series, "CF", "dividends_paid")

    hasData = False

    if opCF is not None:
        hasData = True
        details.append(f"영업CF: {opCF/1e8:,.0f}억")
        if opCF < 0:
            details.append("영업CF 음수 — 금융업은 대출 확대/예금 유출로 정상 가능")

    if invCF is not None:
        hasData = True
        details.append(f"투자CF: {invCF/1e8:,.0f}억")

    if finCF is not None:
        hasData = True
        details.append(f"재무CF: {finCF/1e8:,.0f}억")

    if dividendsPaid is not None and dividendsPaid > 0:
        details.append(f"배당 지급: {dividendsPaid/1e8:,.0f}억")
        opps.append(Flag("positive", "shareholder", f"배당 지급 {dividendsPaid/1e8:,.0f}억"))
        score += 1

    netIncome = getLatest(series, "IS", "net_income")
    if netIncome is not None and netIncome > 0:
        details.append(f"순이익 {netIncome/1e8:,.0f}억 — 이익 창출력 있음")
        score += 2

    if not hasData:
        return InsightResult("N", "금융업 현금흐름 데이터 부족")

    grade = _scoreToGrade(score, 3)
    summary = "금융업 현금흐름 " + ("양호" if score >= 2 else "보통" if score >= 0 else "주의")

    return InsightResult(grade, summary, details, risks, opps)


def analyzeGovernance(company) -> InsightResult:
    details = []
    risks = []
    opps = []

    if company.report is None:
        return InsightResult("N", "정기보고서 데이터 없음")

    rpt = company.report

    major = rpt.majorHolder
    if major is not None and major.totalShareRatio:
        latest = None
        for v in reversed(major.totalShareRatio):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if latest > 50:
                details.append(f"최대주주 지분 {latest:.1f}% — 지배력 안정")
                opps.append(Flag("positive", "governance", f"최대주주 {latest:.1f}%"))
            elif latest < 20:
                details.append(f"최대주주 지분 {latest:.1f}% — 경영권 분산")
                risks.append(Flag("warning", "governance", f"최대주주 {latest:.1f}% — 경영권 분쟁 가능"))
            else:
                details.append(f"최대주주 지분 {latest:.1f}%")

    audit = rpt.audit
    if audit is not None and audit.opinions:
        latest = None
        for v in reversed(audit.opinions):
            if v is not None:
                latest = v
                break
        if latest is not None:
            if "적정" in str(latest):
                details.append("감사의견: 적정")
            else:
                details.append(f"감사의견: {latest}")
                risks.append(Flag("danger", "audit", f"감사의견 비적정: {latest}"))

    div = rpt.dividend
    if div is not None and div.dps:
        recentDps = [d for d in div.dps[-3:] if d is not None]
        if recentDps and all(d > 0 for d in recentDps):
            details.append(f"최근 3년 연속 배당 실시 (최근 DPS: {recentDps[-1]:,.0f}원)")
            opps.append(Flag("positive", "shareholder", "안정적 배당 정책"))
        elif recentDps and recentDps[-1] == 0:
            details.append("최근 무배당")
            risks.append(Flag("warning", "shareholder", "무배당"))

    if not details:
        return InsightResult("N", "지배구조 데이터 없음")

    grade = "B" if not risks else "D"
    summary = "지배구조 " + ("안정" if not risks else "주의 필요")

    return InsightResult(grade, summary, details, risks, opps)


def analyzeRiskSummary(insights: dict[str, InsightResult]) -> InsightResult:
    allRisks = []
    for key in ["performance", "profitability", "health", "cashflow", "governance"]:
        if key in insights:
            allRisks.extend(insights[key].risks)

    if not allRisks:
        return InsightResult("A", "특별한 리스크 없음", ["주요 재무지표 양호"])

    dangerCount = sum(1 for r in allRisks if r.level == "danger")
    warningCount = sum(1 for r in allRisks if r.level == "warning")

    if dangerCount > 0:
        grade = "F"
        summary = f"중대 리스크 {dangerCount}건"
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
    allOpps = []
    for key in ["performance", "profitability", "health", "cashflow", "governance"]:
        if key in insights:
            allOpps.extend(insights[key].opportunities)

    if not allOpps:
        return InsightResult("C", "특별한 투자 기회 없음")

    strongCount = sum(1 for o in allOpps if o.level == "strong")
    positiveCount = sum(1 for o in allOpps if o.level == "positive")

    if strongCount >= 3:
        grade = "A"
        summary = f"투자 매력 높음 ({strongCount}개 강점)"
    elif strongCount >= 1:
        grade = "B"
        summary = f"투자 매력 있음 ({strongCount}강점, {positiveCount}긍정)"
    elif positiveCount >= 2:
        grade = "B"
        summary = f"긍정적 요소 다수 ({positiveCount}건)"
    else:
        grade = "C"
        summary = "일부 긍정적 요소"

    return InsightResult(grade, summary, [o.text for o in allOpps], opportunities=allOpps)


def runFullAnalysis(stockCode: str):
    print(f"\n{'=' * 70}")
    print(f"  인사이트 분석: {stockCode}")
    print(f"{'=' * 70}")

    qResult = buildTimeseries(stockCode)
    aResult = buildAnnual(stockCode)

    if qResult is None or aResult is None:
        print("  시계열 데이터 없음")
        return None

    qSeries, qPeriods = qResult
    aSeries, aYears = aResult

    ratios = calcRatios(aSeries)
    company = dartlab.Company(stockCode)

    isFinancial, financialSignals = detectFinancialSector(aSeries, ratios)
    if isFinancial:
        print(f"  [금융업 감지] 신호 {len(financialSignals)}개: {', '.join(financialSignals)}")

    insights = {}
    insights["performance"] = analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial)
    insights["profitability"] = analyzeProfitability(ratios, aSeries, isFinancial)
    insights["health"] = analyzeHealth(ratios, isFinancial)
    insights["cashflow"] = analyzeCashflow(ratios, aSeries, isFinancial)
    insights["governance"] = analyzeGovernance(company)
    insights["risk"] = analyzeRiskSummary(insights)
    insights["opportunity"] = analyzeOpportunitySummary(insights)

    for name, result in insights.items():
        print(f"\n  [{name.upper()}] {result.grade} — {result.summary}")
        for d in result.details:
            print(f"    · {d}")
        for r in result.risks:
            icon = "!!" if r.level == "danger" else "!"
            print(f"    {icon} RISK: {r.text}")
        for o in result.opportunities:
            icon = "★" if o.level == "strong" else "☆"
            print(f"    {icon} OPP: {o.text}")

    return insights


STOCKS = {
    "005930": "삼성전자",
    "005380": "현대자동차",
    "105560": "KB금융",
    "035720": "카카오",
    "373220": "LG에너지솔루션",
}

BEFORE_GRADES_006 = {
    "005930": {"performance": "A", "profitability": "B", "health": "A", "cashflow": "A", "governance": "B", "risk": "B", "opportunity": "A"},
    "005380": {"performance": "D", "profitability": "B", "health": "F", "cashflow": "F", "governance": "B", "risk": "F", "opportunity": "B"},
    "105560": {"performance": "D", "profitability": "D", "health": "C", "cashflow": "D", "governance": "D", "risk": "C", "opportunity": "C"},
    "035720": {"performance": "D", "profitability": "D", "health": "C", "cashflow": "A", "governance": "N", "risk": "B", "opportunity": "B"},
    "373220": {"performance": "F", "profitability": "C", "health": "C", "cashflow": "B", "governance": "B", "risk": "F", "opportunity": "B"},
}


if __name__ == "__main__":
    CATEGORIES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]

    results = {}
    for code, name in STOCKS.items():
        print(f"\n{'#' * 70}")
        print(f"  {name} ({code})")
        print(f"{'#' * 70}")
        insights = runFullAnalysis(code)
        if insights:
            results[code] = insights

    print(f"\n\n{'=' * 100}")
    print("  006 → 008 등급 비교 (금융업 Profitability/Cashflow 보정)")
    print(f"{'=' * 100}")

    header = f"  {'종목':<12}"
    for cat in CATEGORIES:
        header += f" {cat[:6]:^11}"
    print(header)
    print(f"  {'-' * 90}")

    gradeOrder = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1, "N": 0, "?": -1}
    changeCount = 0
    improveCount = 0

    for code, name in STOCKS.items():
        if code not in results:
            continue

        before = BEFORE_GRADES_006.get(code, {})
        after = results[code]

        beforeRow = f"  {name:<12}"
        afterRow = f"  {'':12}"
        for cat in CATEGORIES:
            bGrade = before.get(cat, "?")
            aGrade = after[cat].grade if cat in after else "?"
            changed = " *" if bGrade != aGrade else ""
            beforeRow += f" {'006:' + bGrade:^11}"
            afterRow += f" {'008:' + aGrade + changed:^11}"
            if bGrade != aGrade:
                changeCount += 1
                if gradeOrder.get(aGrade, -1) > gradeOrder.get(bGrade, -1):
                    improveCount += 1

        print(beforeRow)
        print(afterRow)
        print()

    totalCells = len([c for c in STOCKS if c in results]) * len(CATEGORIES)
    print(f"  변경된 등급: {changeCount}/{totalCells}")
    print(f"  개선된 등급: {improveCount}/{changeCount if changeCount else 1}")
