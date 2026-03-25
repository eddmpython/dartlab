"""투자논거 합성 — insight 수치 기반 bull/bear/catalyst 생성."""

from __future__ import annotations

from dartlab.engines.analysis.research.types import (
    EarningsQuality,
    ExecutiveSummary,
    ForecastData,
    InsightDetail,
    InvestmentThesis,
    NarrativeAnalysis,
    QuantScores,
    RiskSection,
    ValuationSection,
)


def synthesizeThesis(
    executive: ExecutiveSummary,
    *,
    insightDetails: list[InsightDetail] | None = None,
    valuationAnalysis: ValuationSection | None = None,
    riskAnalysis: RiskSection | None = None,
    quantScores: QuantScores | None = None,
    earningsQuality: EarningsQuality | None = None,
    forecastData: ForecastData | None = None,
    narrativeAnalysis: NarrativeAnalysis | None = None,
) -> InvestmentThesis:
    """분석 결과를 종합하여 bull/bear case 생성."""
    bull: list[str] = []
    bear: list[str] = []
    catalysts: list[str] = []
    monitoring: list[str] = []

    # ── insight details 기반 (구체적 수치) ──
    if insightDetails:
        _addInsightBullBear(insightDetails, bull, bear, catalysts, monitoring)

    # ── valuation 기반 ──
    if valuationAnalysis:
        _addValuationBullBear(valuationAnalysis, executive, bull, bear, catalysts)

    # ── risk 기반 ──
    if riskAnalysis:
        _addRiskBear(riskAnalysis, bear, monitoring)

    # ── forecast 기반 ──
    if forecastData:
        _addForecastBullBear(forecastData, bull, catalysts)

    # ── Piotroski / Lynch (fallback — insight 없을 때 보조) ──
    if quantScores:
        _addQuantBullBear(quantScores, bull, bear, monitoring)

    # ── earnings quality ──
    if earningsQuality:
        if earningsQuality.assessment == "high":
            bull.append("현금흐름 기반 이익의 질 양호")
        elif earningsQuality.assessment in ("low", "questionable"):
            bear.append(f"이익의 질 {earningsQuality.assessment} — 발생주의 비중 과다 주의")

    # ── upside (기본) ──
    if executive.upside is not None:
        if executive.upside > 0.15:
            bull.append(f"컨센서스 대비 상승여력 {executive.upside:+.1%}")
        elif executive.upside < -0.15:
            bear.append(f"컨센서스 대비 고평가 {executive.upside:+.1%}")

    # ── narrative 교차분석 결과 병합 (v3) ──
    if narrativeAnalysis and narrativeAnalysis.paragraphs:
        _mergeNarrative(narrativeAnalysis, bull, bear, catalysts)

    # ── deduplicate & limit ──
    bull = _dedupe(bull)[:7]
    bear = _dedupe(bear)[:7]
    catalysts = _dedupe(catalysts)[:5]
    monitoring = _dedupe(monitoring)[:5]

    # ── confidence ──
    totalSignals = len(bull) + len(bear)
    confidence = 0.5
    if totalSignals > 0:
        bullRatio = len(bull) / totalSignals
        confidence = 0.3 + abs(bullRatio - 0.5) * 1.4  # 0.3~1.0

    # ── summary narrative (v3: 교차분석 기반) ──
    if narrativeAnalysis and narrativeAnalysis.paragraphs:
        narrative = _buildNarrativeFromAnalysis(narrativeAnalysis, valuationAnalysis)
    else:
        narrative = _buildNarrative(executive, bull, bear, valuationAnalysis)

    return InvestmentThesis(
        bullCase=bull,
        bearCase=bear,
        catalysts=catalysts,
        monitoringPoints=monitoring,
        confidence=round(min(confidence, 1.0), 2),
        summaryNarrative=narrative,
    )


def _addInsightBullBear(
    details: list[InsightDetail],
    bull: list[str],
    bear: list[str],
    catalysts: list[str],
    monitoring: list[str],
) -> None:
    """insight 10영역의 구체적 수치를 bull/bear에 직접 사용."""
    # 영역별 중요도 (앞쪽일수록 중요)
    priorityAreas = [
        "performance",
        "profitability",
        "health",
        "cashflow",
        "governance",
        "predictability",
        "uncertainty",
        "coreEarnings",
    ]

    for detail in details:
        if detail.area in ("risk", "opportunity"):
            # risk/opportunity는 종합 플래그이므로 별도 처리
            if detail.area == "opportunity" and detail.grade in ("A", "B"):
                for opp in detail.details[:2]:
                    catalysts.append(opp)
            continue

        if detail.grade in ("A", "B"):
            for d in detail.details[:2]:
                bull.append(d)
            for opp in detail.opportunities[:1]:
                catalysts.append(opp)
        elif detail.grade in ("D", "F"):
            for d in detail.details[:2]:
                # 등급은 D/F인데 detail 텍스트가 긍정적이면 skip
                if _isPositiveText(d):
                    continue
                bear.append(d)
            for r in detail.risks[:1]:
                monitoring.append(r)
        elif detail.grade == "C":
            # C등급은 모니터링만
            for r in detail.risks[:1]:
                monitoring.append(r)


def _addValuationBullBear(
    va: ValuationSection,
    executive: ExecutiveSummary,
    bull: list[str],
    bear: list[str],
    catalysts: list[str],
) -> None:
    """밸류에이션 결과를 bull/bear에 반영."""
    if va.verdict == "저평가":
        if va.fairValueRange:
            lo, hi = va.fairValueRange
            bull.append(f"3가지 밸류에이션 기준 저평가 (적정 {lo:,.0f}~{hi:,.0f}원)")
        if va.dcfMos is not None and va.dcfMos > 20:
            bull.append(f"DCF 안전마진 {va.dcfMos:.0f}%")
        catalysts.append("시장이 내재가치를 반영할 촉매 대기")
    elif va.verdict == "고평가":
        if va.fairValueRange:
            lo, hi = va.fairValueRange
            bear.append(f"3가지 밸류에이션 기준 고평가 (적정 {lo:,.0f}~{hi:,.0f}원)")


def _addRiskBear(
    ra: RiskSection,
    bear: list[str],
    monitoring: list[str],
) -> None:
    """리스크 분석 결과를 bear/monitoring에 반영."""
    if ra.distress:
        d = ra.distress
        if d.level in ("danger", "critical"):
            bear.append(f"부실 위험 {d.level} (신용등급 {d.creditGrade})")
            for rf in d.riskFactors[:2]:
                bear.append(rf)
        elif d.level == "warning":
            monitoring.append(f"부실 주의 (신용 {d.creditGrade}, 종합 {d.overall:.0f}/100)")
        if d.cashRunwayMonths is not None and d.cashRunwayMonths < 18:
            bear.append(f"현금소진 {d.cashRunwayMonths:.0f}개월 이내 예상")

    if ra.anomalies:
        for item in ra.anomalies.items:
            sev = item.get("severity", "")
            text = item.get("text", "")
            if sev in ("critical", "danger"):
                bear.append(f"이상치: {text}")
            elif sev == "warning" and len(monitoring) < 5:
                monitoring.append(text)


def _addForecastBullBear(
    fc: ForecastData,
    bull: list[str],
    catalysts: list[str],
) -> None:
    """예측 데이터를 bull/catalyst에 반영."""
    if fc.selfForecast:
        sf = fc.selfForecast
        gr = sf.get("growthRate")
        method = sf.get("method", "")
        conf = sf.get("confidence", "")
        if gr is not None and gr > 5:
            bull.append(f"자체 매출 예측 +{gr:.1f}% ({method})")
        if gr is not None and gr > 0:
            catalysts.append(f"매출 성장 +{gr:.1f}% 전망 (신뢰도 {conf})")

    if fc.scenarioSummary:
        sc = fc.scenarioSummary
        bullVal = sc.get("bull")
        baseVal = sc.get("base")
        if bullVal and baseVal and bullVal > baseVal:
            catalysts.append(f"시나리오 상방 {bullVal:,.0f}원 (기준 {baseVal:,.0f}원)")


def _addQuantBullBear(
    qs: QuantScores,
    bull: list[str],
    bear: list[str],
    monitoring: list[str],
) -> None:
    """정량 스코어 보조 bull/bear."""
    if qs.piotroski:
        f = qs.piotroski
        if f.total >= 7:
            bull.append(f"Piotroski F-Score {f.total}/9 — 펀더멘탈 건전")
        elif f.total <= 3:
            bear.append(f"Piotroski F-Score {f.total}/9 — 펀더멘탈 취약")

    if qs.lynchFairValue:
        lv = qs.lynchFairValue
        if lv.signal == "undervalued" and lv.pegRatio is not None:
            bull.append(f"PEG {lv.pegRatio:.2f} — 성장 대비 저렴")
        elif lv.signal == "overvalued" and lv.pegRatio is not None:
            bear.append(f"PEG {lv.pegRatio:.2f} — 성장 대비 비쌈")

    if qs.dupont:
        dp = qs.dupont
        if dp.driver == "leverage":
            monitoring.append("레버리지가 ROE 주도 — 부채비율 추이 주시")
        elif dp.driver == "margin":
            monitoring.append("순이익률 변동이 ROE 주도 — 마진 추이 주시")


def _buildNarrative(
    executive: ExecutiveSummary,
    bull: list[str],
    bear: list[str],
    va: ValuationSection | None,
) -> str:
    """1-2문장 핵심 투자 요약."""
    name = ""
    parts = []

    nBull = len(bull)
    nBear = len(bear)
    if nBull > nBear * 2:
        parts.append("긍정적 신호가 압도적으로 우세")
    elif nBull > nBear:
        parts.append("긍정적 신호 우세")
    elif nBear > nBull * 2:
        parts.append("부정적 신호가 압도적으로 우세")
    elif nBear > nBull:
        parts.append("부정적 신호 우세")
    else:
        parts.append("긍정/부정 신호 균형")

    if va and va.verdict:
        parts.append(f"밸류에이션 {va.verdict}")

    if executive.opinion:
        parts.append(f"투자의견 {executive.opinion}")

    return " | ".join(parts) + "."


def _isPositiveText(text: str) -> bool:
    """텍스트가 명백히 긍정적 의미인지 판별."""
    positiveKeywords = ["안전", "양호", "우수", "개선", "충분", "안정", "미미"]
    negativeKeywords = ["위험", "부족", "악화", "적자", "과다", "취약"]
    hasPositive = any(kw in text for kw in positiveKeywords)
    hasNegative = any(kw in text for kw in negativeKeywords)
    return hasPositive and not hasNegative


def _dedupe(items: list[str]) -> list[str]:
    """중복 제거 (순서 유지)."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _mergeNarrative(
    na: NarrativeAnalysis,
    bull: list[str],
    bear: list[str],
    catalysts: list[str],
) -> None:
    """narrative 교차분석 결과를 bull/bear/catalysts에 병합."""
    for p in na.paragraphs:
        if p.severity == "positive":
            bull.insert(0, p.body)
        elif p.severity in ("negative", "warning"):
            bear.insert(0, p.body)
    for fi in na.forwardImplications:
        catalysts.append(fi)


def _buildNarrativeFromAnalysis(
    na: NarrativeAnalysis,
    va: ValuationSection | None,
) -> str:
    """교차분석 기반 summaryNarrative 생성."""
    parts: list[str] = []
    positive = [p for p in na.paragraphs if p.severity == "positive"]
    negative = [p for p in na.paragraphs if p.severity in ("negative", "warning")]

    if positive:
        parts.append(_firstSentence(positive[0].body))
    if negative:
        parts.append(_firstSentence(negative[0].body))
    if va and va.verdict:
        parts.append(f"밸류에이션 {va.verdict}")

    return " | ".join(parts) + "." if parts else ""


def _firstSentence(text: str) -> str:
    """본문에서 첫 문장 추출 (숫자 소수점 구분)."""
    # ". " 패턴으로 문장 분리 (소수점 ".1%" 등과 구분)
    import re

    # 마침표 뒤에 공백 또는 문자열 끝
    sentences = re.split(r"\.\s", text, maxsplit=1)
    return sentences[0] if sentences else text


def classifyProfile(grades: dict[str, str], upside: float | None) -> str:
    """투자 프로파일 분류."""
    gradeValues = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
    vals = [gradeValues.get(g, 3) for g in grades.values()]
    avg = sum(vals) / len(vals) if vals else 3

    if avg >= 4.0:
        return "premium"
    if avg >= 3.5:
        return "growth"
    if avg >= 2.5:
        return "stable"
    if avg >= 2.0:
        return "caution"
    return "distress"
