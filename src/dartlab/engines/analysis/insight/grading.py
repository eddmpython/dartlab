"""10영역 인사이트 등급 분석.

영역: performance, profitability, health, cashflow, governance, risk, opportunity,
      predictability, uncertainty, coreEarnings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from dartlab.engines.analysis.insight.benchmark import getBenchmark, sectorAdjustment
from dartlab.engines.analysis.insight.detector import detectIncompleteYear
from dartlab.engines.analysis.insight.types import Flag, InsightResult
from dartlab.engines.analysis.sector.types import Sector
from dartlab.engines.common.finance.extract import getAnnualValues, getLatest
from dartlab.engines.common.finance.ratios import RatioResult

if TYPE_CHECKING:
    from dartlab.engines.company.dart.company import Company


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
    from dartlab.engines.common.finance.ratios import yoy_pct

    valid = [(i, v) for i, v in enumerate(annualVals) if v is not None]
    if len(valid) < 2:
        return None
    _, prev = valid[-2]
    _, curr = valid[-1]
    return yoy_pct(curr, prev)


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
    market: str = "KR",
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

    bm = getBenchmark(sector, market)
    omAdj = sectorAdjustment(om, bm.omMedian, bm.omQ1, bm.omQ3)
    roeAdj = sectorAdjustment(roe, bm.roeMedian, bm.roeQ1, bm.roeQ3)
    adj = omAdj + roeAdj
    if adj != 0:
        score += adj
        direction = "상향" if adj > 0 else "하향"
        details.append(
            f"[섹터 보정 {direction}: {sector.value} 대비 OM{'↑' if omAdj > 0 else '↓' if omAdj < 0 else '→'} ROE{'↑' if roeAdj > 0 else '↓' if roeAdj < 0 else '→'}]"
        )

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
    totalEquity = getLatest(aSeries, "BS", "owners_of_parent_equity") or getLatest(
        aSeries, "BS", "total_stockholders_equity"
    )
    opIncome = getLatest(aSeries, "IS", "operating_profit")
    opExpense = getLatest(aSeries, "IS", "operating_expense")

    roe = (netIncome / totalEquity) * 100 if netIncome and totalEquity and totalEquity > 0 else None
    roa = (netIncome / totalAssets) * 100 if netIncome and totalAssets and totalAssets > 0 else None
    cir = (
        (opExpense / (opExpense + opIncome)) * 100
        if opExpense is not None and opIncome is not None and (opExpense + opIncome) != 0
        else None
    )

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
    summary = "금융업 수익성 " + (
        "우수" if score >= 4 else "양호" if score >= 2 else "보통" if score >= 0 else "개선 필요"
    )
    return InsightResult(grade, summary, details, risks, opps)


def analyzeHealth(ratios: RatioResult, isFinancial: bool = False, currency: str = "KRW") -> InsightResult:
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
    elif currency == "USD":
        # US 기업: 자사주매입으로 equity 축소가 일반적, 부채비율 높음이 정상
        if dr is not None:
            if dr < 100:
                details.append(f"부채비율 매우 양호 ({dr:.0f}%)")
                opps.append(Flag("strong", "finance", f"부채비율 {dr:.0f}%"))
                score += 3
            elif dr < 200:
                details.append(f"부채비율 양호 ({dr:.0f}%)")
                opps.append(Flag("positive", "finance", f"부채비율 {dr:.0f}%"))
                score += 2
            elif dr < 400:
                details.append(f"부채비율 보통 ({dr:.0f}%)")
                score += 1
            elif dr < 600:
                details.append(f"부채비율 다소 높음 ({dr:.0f}%)")
            else:
                details.append(f"부채비율 과다 ({dr:.0f}%)")
                risks.append(Flag("warning", "finance", f"부채비율 {dr:.0f}%"))
                score -= 1

        if cr is not None:
            if cr > 150:
                details.append(f"유동성 매우 충분 ({cr:.0f}%)")
                opps.append(Flag("positive", "finance", f"유동비율 {cr:.0f}%"))
                score += 2
            elif cr > 100:
                details.append(f"유동성 충분 ({cr:.0f}%)")
                score += 1
            elif cr > 80:
                details.append(f"유동성 보통 ({cr:.0f}%)")
            else:
                details.append(f"유동성 부족 ({cr:.0f}%)")
                risks.append(Flag("warning", "finance", f"유동비율 {cr:.0f}%"))
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

    # ── 부실 예측 모델 신호 (ratios에서 계산된 값 활용) ──
    # Ohlson O-Score: P(bankruptcy) > 10% → 경고
    if ratios.ohlsonProbability is not None:
        if ratios.ohlsonProbability > 20:
            details.append(f"O-Score 부도확률 {ratios.ohlsonProbability:.1f}% — 고위험")
            risks.append(Flag("danger", "distress", f"O-Score P(부도) {ratios.ohlsonProbability:.1f}%"))
            score -= 2
        elif ratios.ohlsonProbability > 10:
            details.append(f"O-Score 부도확률 {ratios.ohlsonProbability:.1f}% — 주의")
            risks.append(Flag("warning", "distress", f"O-Score P(부도) {ratios.ohlsonProbability:.1f}%"))
            score -= 1

    # Altman Z''-Score (금융업 포함 범용)
    if ratios.altmanZppScore is not None:
        if ratios.altmanZppScore < 1.1:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f} — 부실 영역")
            risks.append(Flag("danger", "distress", f"Z'' {ratios.altmanZppScore:.2f} (부실)"))
            score -= 2
        elif ratios.altmanZppScore < 2.6:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f} — 회색 영역")
            risks.append(Flag("warning", "distress", f"Z'' {ratios.altmanZppScore:.2f} (회색)"))
            score -= 1
        elif ratios.altmanZppScore > 5:
            details.append(f"Z''-Score {ratios.altmanZppScore:.2f} — 안전")
            score += 1

    grade = _scoreToGrade(score, 7)
    label = "금융업 재무건전성" if isFinancial else "재무건전성"
    summary = f"{label} " + ("우수" if score >= 5 else "안정" if score >= 2 else "보통" if score >= 0 else "주의 필요")
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


def _analyzeGovernanceFromSections(company: Company) -> InsightResult:
    """report가 없을 때 sections 기반 governance 분석 (EDGAR 등)."""
    import polars as pl

    docs = getattr(company, "docs", None)
    if docs is None:
        return InsightResult("N", "지배구조 데이터 없음")
    sec = getattr(docs, "sections", None)
    if sec is None or not isinstance(sec, pl.DataFrame) or sec.is_empty():
        return InsightResult("N", "지배구조 데이터 없음")

    # governance 관련 topic 검색 (EDGAR: director, compensation, ownership)
    gov_pattern = "(?i)governance|director|compensation|ownership|security.?owner|executive.?comp"
    gov_topics = sec.filter(pl.col("topic").cast(pl.Utf8).str.contains(gov_pattern))

    if gov_topics.is_empty():
        return InsightResult("N", "지배구조 데이터 없음")

    # 데이터 존재량으로 점수 부여
    n_topics = gov_topics.select("topic").unique().height
    n_blocks = gov_topics.height
    # 메타 컬럼 제외한 기간 컬럼 수
    meta_cols = {"topic", "blockType", "blockOrder", "textNodeType", "textLevel", "textPath", "source", "chapter"}
    period_cols = [c for c in gov_topics.columns if c not in meta_cols]
    n_periods = 0
    for col in period_cols:
        if gov_topics[col].drop_nulls().len() > 0:
            n_periods += 1

    details: list[str] = []
    score = 0
    max_score = 3

    if n_topics >= 3:
        score += 2
        details.append(f"지배구조 관련 {n_topics}개 topic, {n_blocks}개 블록 공시")
    elif n_topics >= 1:
        score += 1
        details.append(f"지배구조 관련 {n_topics}개 topic 공시")

    if n_periods >= 3:
        score += 1
        details.append(f"{n_periods}개 기간 연속 공시 (일관성 양호)")

    grade = _scoreToGrade(score, max_score)
    summary = "지배구조 " + ("양호" if grade in ("A", "B") else "보통" if grade == "C" else "제한적 정보")
    return InsightResult(grade, summary, details)


def analyzeGovernance(company: Company | None) -> InsightResult:
    """지배구조 분석."""
    details: list[str] = []
    risks: list[Flag] = []
    opps: list[Flag] = []
    score = 0
    maxScore = 0

    if company is None:
        return InsightResult("N", "기업 데이터 없음")

    # report namespace가 없으면 sections 기반 fallback (EDGAR 등)
    if not hasattr(company, "report") or company.report is None:
        return _analyzeGovernanceFromSections(company)

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

    # 감사인 안정성 (PCAOB AS 3101) — Big4 + 장기 유지
    _big4_kw = ["삼일", "PwC", "삼정", "KPMG", "한영", "EY", "안진", "Deloitte"]
    if audit is not None and audit.auditors:
        maxScore += 2
        uniqueAuditors = [a for a in audit.auditors if a is not None]
        latestAuditor = uniqueAuditors[-1] if uniqueAuditors else None

        if latestAuditor and any(kw in latestAuditor for kw in _big4_kw):
            # Big4 판정
            changeCount = sum(1 for i in range(1, len(uniqueAuditors)) if uniqueAuditors[i] != uniqueAuditors[i - 1])
            if changeCount == 0 and len(uniqueAuditors) >= 3:
                details.append(f"감사인: {latestAuditor} (Big4, 3년+ 유지)")
                score += 2
            elif changeCount == 0:
                details.append(f"감사인: {latestAuditor} (Big4)")
                score += 1
            else:
                details.append(f"감사인: {latestAuditor} (Big4, {changeCount}회 교체)")
                score += 1
        elif latestAuditor:
            details.append(f"감사인: {latestAuditor} (비Big4)")
            # 빈번 교체 시 감점
            changeCount = sum(1 for i in range(1, len(uniqueAuditors)) if uniqueAuditors[i] != uniqueAuditors[i - 1])
            if changeCount >= 2:
                score -= 1
                risks.append(Flag("warning", "audit", f"감사인 빈번 교체 ({changeCount}회)"))

    # 내부통제 (SOX 302/404)
    try:
        ic = getattr(rpt, "internalControl", None)
        if ic is not None:
            controlDf = getattr(ic, "controlDf", None)
            if controlDf is not None and len(controlDf) > 0:
                maxScore += 2
                latestRow = controlDf.row(-1, named=True)
                hasWeakness = latestRow.get("hasWeakness", False)
                opinion = latestRow.get("opinion", "")
                if hasWeakness:
                    score -= 2
                    details.append(f"내부통제: 취약점 보고 ({opinion})")
                    risks.append(Flag("danger", "governance", "내부통제 취약점"))
                else:
                    score += 2
                    details.append(f"내부통제: {opinion or '적정'}")
    except (AttributeError, IndexError):
        pass

    # 감사위원회 활동
    try:
        auditSys = getattr(rpt, "auditSystem", None)
        if auditSys is not None:
            activity = getattr(auditSys, "activity", None) or []
            if activity:
                maxScore += 1
                score += 1
                details.append(f"감사위원회: {len(activity)}건 활동")
            elif getattr(auditSys, "committee", None):
                maxScore += 1
                details.append("감사위원회: 설치됨 (활동 미확인)")
    except AttributeError:
        pass

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
        "우수"
        if grade == "A"
        else "안정"
        if grade == "B"
        else "보통"
        if grade == "C"
        else "주의"
        if grade == "D"
        else "위험"
    )
    return InsightResult(grade, summary, details, risks, opps)


def analyzeRiskSummary(insights: dict[str, InsightResult]) -> InsightResult:
    """리스크 종합 분석."""
    allRisks: list[Flag] = []
    for key in [
        "performance",
        "profitability",
        "health",
        "cashflow",
        "governance",
        "predictability",
        "uncertainty",
        "coreEarnings",
    ]:
        if key in insights and insights[key] is not None:
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
    for key in [
        "performance",
        "profitability",
        "health",
        "cashflow",
        "governance",
        "predictability",
        "uncertainty",
        "coreEarnings",
    ]:
        if key in insights and insights[key] is not None:
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


def analyzePredictability(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """사업 예측가능성 분석 (0~10점 → A~F)."""
    import statistics

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    niVals = getAnnualValues(aSeries, "IS", "net_profit")

    if isFinancial:
        revVals = opVals

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]

    if len(validRev) < 3:
        return InsightResult("N", "예측가능성 데이터 부족")

    details: list[str] = []
    score = 0.0

    # 매출 CV (낮을수록 예측 가능)
    revMean = statistics.mean(validRev)
    revCv = statistics.stdev(validRev) / abs(revMean) if revMean != 0 else 1.0
    revScore = max(0, 2.5 - revCv * 2.5)
    score += revScore
    details.append(f"매출 CV {revCv:.2f} ({revScore:.1f}/2.5)")

    # 영업이익 CV
    if len(validOp) >= 3:
        opMean = statistics.mean(validOp)
        opCv = statistics.stdev(validOp) / abs(opMean) if opMean != 0 else 1.0
        opScore = max(0, 2.5 - opCv * 2.5)
        score += opScore
        details.append(f"영업이익 CV {opCv:.2f} ({opScore:.1f}/2.5)")

    # 연속 성장 (매출 YoY > 0 횟수)
    growthCount = sum(1 for i in range(1, len(validRev)) if validRev[i] > validRev[i - 1])
    maxGrowth = max(1, len(validRev) - 1)
    growthScore = (growthCount / maxGrowth) * 2.5
    score += growthScore
    details.append(f"연속성장 {growthCount}/{maxGrowth}년 ({growthScore:.1f}/2.5)")

    # 무적자 (순이익 > 0 비율)
    if len(validNi) >= 3:
        profitCount = sum(1 for v in validNi if v > 0)
        profitScore = (profitCount / len(validNi)) * 2.5
        score += profitScore
        details.append(f"흑자 {profitCount}/{len(validNi)}년 ({profitScore:.1f}/2.5)")

    score = min(10, score)
    grade = _predictabilityGrade(score)
    summary = f"예측가능성 {score:.1f}/10 — " + (
        "매우 높음" if score >= 7 else "높음" if score >= 5 else "보통" if score >= 3 else "낮음"
    )
    return InsightResult(grade, summary, details)


def _predictabilityGrade(score: float) -> str:
    """예측가능성 점수 → 등급."""
    if score >= 8:
        return "A"
    if score >= 6:
        return "B"
    if score >= 4:
        return "C"
    if score >= 2:
        return "D"
    return "F"


def analyzeUncertainty(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """불확실성 등급 분석 (Morningstar 방식 5단계)."""
    import statistics

    revVals = getAnnualValues(aSeries, "IS", "sales")
    opVals = getAnnualValues(aSeries, "IS", "operating_profit")

    if isFinancial:
        revVals = opVals

    validRev = [v for v in revVals if v is not None]
    validOp = [v for v in opVals if v is not None]

    if len(validRev) < 5 or len(validOp) < 5:
        return InsightResult("N", "불확실성 데이터 부족")

    details: list[str] = []

    # 매출 CV
    revMean = statistics.mean(validRev)
    revCv = statistics.stdev(validRev) / abs(revMean) if revMean != 0 else 1.0

    # DOL (영업레버리지)
    dolList = []
    minLen = min(len(validRev), len(validOp))
    for i in range(1, minLen):
        if validRev[i - 1] != 0 and validOp[i - 1] != 0:
            sChg = (validRev[i] - validRev[i - 1]) / abs(validRev[i - 1])
            oChg = (validOp[i] - validOp[i - 1]) / abs(validOp[i - 1])
            if abs(sChg) > 0.01:
                dolList.append(abs(oChg / sChg))
    dol = statistics.median(dolList) if dolList else 2.0

    # D/E
    tl = getLatest(aSeries, "BS", "total_liabilities")
    eq = getLatest(aSeries, "BS", "total_stockholders_equity")
    deRatio = tl / eq if tl is not None and eq and eq > 0 else 0.0

    # 영업이익 CV
    opMean = statistics.mean(validOp)
    opCv = statistics.stdev(validOp) / abs(opMean) if opMean != 0 else 1.0

    # 종합 점수 (각 최대 25점)
    revScore = min(25, revCv / 0.5 * 25)
    dolScore = min(25, (dol - 1) / 9 * 25)
    deScore = min(25, deRatio / 3 * 25)
    opScore = min(25, opCv / 1.0 * 25)
    totalScore = revScore + dolScore + deScore + opScore

    if totalScore < 20:
        rating, margin = "Low", "±15%"
    elif totalScore < 35:
        rating, margin = "Medium", "±25%"
    elif totalScore < 50:
        rating, margin = "High", "±35%"
    elif totalScore < 70:
        rating, margin = "Very High", "±45%"
    else:
        rating, margin = "Extreme", "±55%"

    details.append(f"매출CV {revCv:.2f}, DOL {dol:.1f}, D/E {deRatio:.1f}, 영업CV {opCv:.2f}")
    details.append(f"종합 {totalScore:.1f}/100 → {rating} (Fair Value 밴드 {margin})")

    grade = _uncertaintyGrade(rating)
    summary = f"불확실성 {rating} — Fair Value 밴드 {margin}"
    return InsightResult(grade, summary, details)


def _uncertaintyGrade(rating: str) -> str:
    """불확실성 등급 → insight 등급 (낮은 불확실성 = 좋은 등급)."""
    return {"Low": "A", "Medium": "B", "High": "C", "Very High": "D", "Extreme": "F"}.get(rating, "C")


def analyzeCoreEarnings(
    aSeries: dict,
    aYears: list[str],
    isFinancial: bool = False,
) -> InsightResult:
    """핵심이익 품질 분석 (비경상 항목 분리)."""
    import statistics

    opVals = getAnnualValues(aSeries, "IS", "operating_profit")
    niVals = getAnnualValues(aSeries, "IS", "net_profit")
    taxVals = getAnnualValues(aSeries, "IS", "income_taxes")
    pbtVals = getAnnualValues(aSeries, "IS", "profit_before_tax")

    validOp = [v for v in opVals if v is not None]
    validNi = [v for v in niVals if v is not None]
    validTax = [v for v in taxVals if v is not None]
    validPbt = [v for v in pbtVals if v is not None]

    if len(validOp) < 3 or len(validNi) < 3:
        return InsightResult("N", "핵심이익 데이터 부족")

    details: list[str] = []
    score = 0

    # 실효세율 추정
    if validTax and validPbt:
        taxRates = []
        for t, p in zip(validTax, validPbt):
            if p > 0 and t is not None:
                taxRates.append(t / p)
        effectiveTax = statistics.mean(taxRates) if taxRates else 0.22
    else:
        effectiveTax = 0.22

    # Core Earnings = 영업이익 × (1-세율)
    coreVals = [v * (1 - effectiveTax) for v in validOp]

    # CV 비교: Core vs Reported
    coreMean = statistics.mean(coreVals) if coreVals else 0
    reportedMean = statistics.mean(validNi) if validNi else 0
    coreCv = statistics.stdev(coreVals) / abs(coreMean) if coreMean != 0 and len(coreVals) >= 2 else 999
    reportedCv = statistics.stdev(validNi) / abs(reportedMean) if reportedMean != 0 and len(validNi) >= 2 else 999

    details.append(f"Core CV {coreCv:.2f} vs Reported CV {reportedCv:.2f}")

    # CV 개선 여부
    if coreCv < reportedCv:
        improvement = (1 - coreCv / reportedCv) * 100 if reportedCv > 0 else 0
        details.append(f"핵심이익이 변동성 {improvement:.0f}% 개선")
        score += 2
    else:
        details.append("비경상 항목 영향 미미")

    # 핵심이익 안정성 (Core CV 절대 수준)
    if coreCv < 0.2:
        details.append("핵심이익 매우 안정")
        score += 3
    elif coreCv < 0.4:
        details.append("핵심이익 안정")
        score += 2
    elif coreCv < 0.7:
        details.append("핵심이익 보통")
        score += 1
    else:
        details.append("핵심이익 변동 큼")

    # 핵심이익 대비 보고이익 괴리 (최신연도)
    if coreVals and validNi:
        latestCore = coreVals[-1]
        latestReported = validNi[-1]
        if latestCore != 0:
            gap = (latestReported - latestCore) / abs(latestCore) * 100
            if abs(gap) > 30:
                details.append(f"보고이익 vs 핵심이익 괴리 {gap:+.0f}%")
                if gap < -30:
                    score -= 1  # 비경상 손실
            elif abs(gap) < 10:
                details.append("보고이익 ≈ 핵심이익")
                score += 1

    grade = _scoreToGrade(score, 6)
    summary = "이익 품질 " + ("우수" if score >= 5 else "양호" if score >= 3 else "보통" if score >= 1 else "주의")
    return InsightResult(grade, summary, details)


def disclosureGapFlags(
    company: "Company | None",
    healthGrade: str | None = None,
) -> list[Flag]:
    """공시 텍스트 변화 vs 재무 지표 불일치 탐지.

    diff 기반으로 리스크 서술 급증/감소를 감지하고, 재무 건전성 등급과 교차 비교하여
    '서술형 리스크 급증 vs 재무 안정' 또는 '재무 악화 vs 서술형 은폐' 불일치를 찾는다.
    """
    if company is None:
        return []

    try:
        sections = company.docs.sections
        if sections is None or sections.is_empty():
            return []
    except (AttributeError, ValueError):
        return []

    from dartlab.engines.common.docs.diff import sectionsDiff

    try:
        diffResult = sectionsDiff(sections)
    except (ValueError, TypeError):
        return []

    if not diffResult.entries:
        return []

    # 리스크 관련 topic 식별
    riskTopics = {
        "riskManagement",
        "riskFactor",
        "goingConcern",
        "audit",
        "contingentLiability",
        "litigation",
        "internalControl",
    }
    riskChanges = [e for e in diffResult.entries if e.topic in riskTopics and e.status == "changed"]

    flags: list[Flag] = []

    if riskChanges and healthGrade in ("A", "B"):
        topics = ", ".join(sorted({e.topic for e in riskChanges}))
        flags.append(
            Flag(
                level="warning",
                category="disclosure_gap",
                text=f"리스크 서술 변화({topics}) vs 재무 안정({healthGrade}) — 불일치 확인 필요",
            )
        )

    if not riskChanges and healthGrade in ("D", "F"):
        flags.append(
            Flag(
                level="warning",
                category="disclosure_gap",
                text=f"재무 악화({healthGrade}) vs 리스크 서술 무변동 — 공시 충실도 점검 필요",
            )
        )

    return flags
