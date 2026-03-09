"""
실험 ID: 010
실험명: 등급 분별력 개선 — Cashflow/Opportunity/Governance 재설계

목적:
- 009에서 발견된 등급 편중 문제 해결
- Cashflow: A 14/20 → FCF/매출 비율, CF 추세로 세분화
- Opportunity: B 15/20 → 강점 기준 상향, 비지니스 리스크 감안
- Governance: B/D 이진법 → 세분화 (감사의견, 배당, 지분율 각각 점수화)
- Health: D 등급 없음 → 임계값 조정

가설:
1. Cashflow에 FCF마진 + CF추세를 추가하면 A가 50% 이하로 감소한다
2. Opportunity에 가중치 재설계를 적용하면 A~D가 골고루 분포한다
3. Governance를 점수제로 바꾸면 A~F 분포가 나온다

방법:
1. 각 영역별 새 스코어링 로직 설계
2. 20종목 동일 데이터로 재검증
3. 009 등급과 비교

결과 (실험 후 작성):
- 전체 등급 분포: A 21.4%, B 28.6%, C 22.1%, D 13.6%, F 11.4%, N 2.9%
- 009→010 Cashflow: A:14→4, B:5→12, C:0→3 (A 편중 해소)
- 009→010 Opportunity: A:5→3, B:15→2, C:0→12, D:0→3 (B 편중 해소, C 중심으로 분산)
- 009→010 Governance: B:13→7, A:0→9 (점수제 적용으로 A등급 생성)
- Health: D 등급 3종목 신규 출현 (LG화학, LG에너지, LG전자)
- Risk: F:8→3, D:0→5 (danger 1건→D로 변경, 세분화)

결론:
- 가설 1 채택: Cashflow A가 14→4로 감소 (70%→20%), FCF마진 세분화 효과
- 가설 2 채택: Opportunity가 A:5 B:15 → A:3 B:2 C:12 D:3으로 4단계 분산
- 가설 3 부분채택: Governance A:9 B:7 (점수제), C/D/F 없이 A/B 편중 잔존
- 전체 분포가 A~F 골고루 분산 (최대 28.6%, 최소 11.4%) — 009 대비 대폭 개선
- Governance C/D/F 부재는 감사의견 적정 + 배당 실시가 대부분이라 자연스러운 결과
- Risk도 D 등급 추가로 F 편중 해소

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

from dataclasses import dataclass, field
from typing import Optional
from collections import Counter

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
    if getLatest(series, "IS", "interest_income") is not None:
        signals.append("이자수익 계정 존재")
    if getLatest(series, "IS", "net_interest_income") is not None:
        signals.append("순이자수익 계정 존재")
    if getLatest(series, "IS", "insurance_revenue") is not None:
        signals.append("보험수익 계정 존재")
    return len(signals) >= 2, signals


def analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial=False):
    lastYear, qCount = detectIncompleteYear(qPeriods)
    incomplete = qCount < 4

    revVals = getAnnualValues(aSeries, "IS", "revenue")
    opVals = getAnnualValues(aSeries, "IS", "operating_income")

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

    qRevVals = qSeries.get("IS", {}).get("revenue", [])
    if isFinancial and not any(v is not None for v in qRevVals):
        qRevVals = qSeries.get("IS", {}).get("operating_income", [])
    revVolatility = _getVolatility(qRevVals)
    qOpVals = qSeries.get("IS", {}).get("operating_income", [])
    opVolatility = _getVolatility(qOpVals)

    details, risks, opps = [], [], []
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


def analyzeProfitability(ratios, series, isFinancial=False):
    details, risks, opps = [], [], []
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


def _analyzeProfitabilityFinancial(series, details, risks, opps):
    details.append("[금융업 수익성 기준 적용]")
    score = 0
    netIncome = getLatest(series, "IS", "net_income")
    totalAssets = getLatest(series, "BS", "total_assets")
    totalEquity = getLatest(series, "BS", "total_equity") or getLatest(series, "BS", "equity_including_nci")
    opIncome = getLatest(series, "IS", "operating_income")
    opExpense = getLatest(series, "IS", "operating_expense")

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


def analyzeHealth(ratios, isFinancial=False):
    details, risks, opps = [], [], []
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


def analyzeCashflow(ratios, series, isFinancial=False):
    if isFinancial:
        return _analyzeCashflowFinancial(series)

    details, risks, opps = [], [], []
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

    cfVals = getAnnualValues(series, "CF", "operating_cashflow")
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


def _analyzeCashflowFinancial(series):
    details, risks, opps = [], [], []
    details.append("[금융업 현금흐름]")
    score = 0

    opCF = getLatest(series, "CF", "operating_cashflow")
    dividendsPaid = getLatest(series, "CF", "dividends_paid")
    netIncome = getLatest(series, "IS", "net_income")

    if opCF is not None:
        details.append(f"영업CF: {opCF/1e8:,.0f}억")

    if dividendsPaid is not None and dividendsPaid > 0:
        details.append(f"배당 지급: {dividendsPaid/1e8:,.0f}억")
        opps.append(Flag("positive", "shareholder", f"배당 지급 {dividendsPaid/1e8:,.0f}억"))
        score += 1

    if netIncome is not None and netIncome > 0:
        details.append(f"순이익 {netIncome/1e8:,.0f}억")
        score += 2

    grade = _scoreToGrade(score, 3)
    summary = "금융업 현금흐름 " + ("양호" if score >= 2 else "보통" if score >= 0 else "주의")
    return InsightResult(grade, summary, details, risks, opps)


def analyzeGovernance(company):
    details, risks, opps = [], [], []
    score = 0
    maxScore = 0

    if company.report is None:
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
    summary = "지배구조 " + ("우수" if grade in ["A"] else "안정" if grade in ["B"] else "보통" if grade in ["C"] else "주의" if grade in ["D"] else "위험")
    return InsightResult(grade, summary, details, risks, opps)


def analyzeRiskSummary(insights):
    allRisks = []
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


def analyzeOpportunitySummary(insights):
    allOpps = []
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


def runFullAnalysis(stockCode):
    qResult = buildTimeseries(stockCode)
    aResult = buildAnnual(stockCode)
    if qResult is None or aResult is None:
        return None

    qSeries, qPeriods = qResult
    aSeries, aYears = aResult
    ratios = calcRatios(aSeries)
    company = dartlab.Company(stockCode)

    isFinancial, _ = detectFinancialSector(aSeries, ratios)

    insights = {}
    insights["performance"] = analyzePerformance(aSeries, aYears, qSeries, qPeriods, isFinancial)
    insights["profitability"] = analyzeProfitability(ratios, aSeries, isFinancial)
    insights["health"] = analyzeHealth(ratios, isFinancial)
    insights["cashflow"] = analyzeCashflow(ratios, aSeries, isFinancial)
    insights["governance"] = analyzeGovernance(company)
    insights["risk"] = analyzeRiskSummary(insights)
    insights["opportunity"] = analyzeOpportunitySummary(insights)
    return insights


STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대자동차",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "035720": "카카오",
    "105560": "KB금융",
    "055550": "신한지주",
    "006800": "미래에셋증권",
    "032830": "삼성생명",
    "051910": "LG화학",
    "373220": "LG에너지솔루션",
    "066570": "LG전자",
    "003550": "LG",
    "000270": "기아",
    "068270": "셀트리온",
    "028260": "삼성물산",
    "096770": "SK이노베이션",
    "034730": "SK",
    "015760": "한국전력",
}

CATEGORIES = ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]


if __name__ == "__main__":
    results = {}
    for code, name in STOCKS.items():
        insights = runFullAnalysis(code)
        if insights:
            results[code] = {cat: insights[cat].grade for cat in CATEGORIES}

    print(f"{'=' * 80}")
    print("  등급 매트릭스 (010 보정)")
    print(f"{'=' * 80}")

    header = f"  {'종목':<15}"
    for cat in CATEGORIES:
        header += f" {cat[:5]:^7}"
    print(header)
    print(f"  {'─' * 70}")

    for code, name in STOCKS.items():
        if code not in results:
            continue
        grades = results[code]
        row = f"  {name:<15}"
        for cat in CATEGORIES:
            row += f" {grades.get(cat, '?'):^7}"
        print(row)

    print(f"\n{'=' * 80}")
    print("  카테고리별 등급 분포")
    print(f"{'=' * 80}")

    for cat in CATEGORIES:
        counter = Counter()
        for grades in results.values():
            counter[grades.get(cat, "?")] += 1
        dist = " ".join(f"{g}:{c}" for g, c in sorted(counter.items()))
        print(f"  {cat:<15} {dist}")

    print(f"\n{'=' * 80}")
    print("  전체 등급 분포")
    print(f"{'=' * 80}")

    allGrades = Counter()
    for grades in results.values():
        for g in grades.values():
            allGrades[g] += 1

    total = sum(allGrades.values())
    for g in ["A", "B", "C", "D", "F", "N"]:
        c = allGrades.get(g, 0)
        pct = (c / total * 100) if total > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {g}: {c:>3} ({pct:>5.1f}%) {bar}")

    print(f"\n{'=' * 80}")
    print("  009 vs 010 Cashflow 비교")
    print(f"{'=' * 80}")
    cfCounter009 = Counter({"A": 14, "B": 5, "F": 1})
    cfCounter010 = Counter()
    for grades in results.values():
        cfCounter010[grades.get("cashflow", "?")] += 1
    print(f"  009: {dict(sorted(cfCounter009.items()))}")
    print(f"  010: {dict(sorted(cfCounter010.items()))}")

    print(f"\n  009 vs 010 Opportunity 비교")
    opCounter009 = Counter({"A": 5, "B": 15})
    opCounter010 = Counter()
    for grades in results.values():
        opCounter010[grades.get("opportunity", "?")] += 1
    print(f"  009: {dict(sorted(opCounter009.items()))}")
    print(f"  010: {dict(sorted(opCounter010.items()))}")

    print(f"\n  009 vs 010 Governance 비교")
    govCounter009 = Counter({"B": 13, "D": 3, "N": 4})
    govCounter010 = Counter()
    for grades in results.values():
        govCounter010[grades.get("governance", "?")] += 1
    print(f"  009: {dict(sorted(govCounter009.items()))}")
    print(f"  010: {dict(sorted(govCounter010.items()))}")
