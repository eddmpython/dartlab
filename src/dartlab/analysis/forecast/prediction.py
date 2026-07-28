"""Context Signal Fusion — 기업 맥락 신호 -> 시나리오 확률 동적 재가중."""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# ======================================
# 데이터 구조
# ======================================


@dataclass
class ContextSignals:
    """기업 맥락 신호 — 시나리오 확률 조정의 근거."""

    # insight 등급 (7개 영역)
    insightGrades: dict[str, str] = field(default_factory=dict)
    # 전체 sections 평균 변화율 (0~100)
    diffChangeRate: float = 0.0
    # 리스크 topic 변화율 (0~100)
    riskChangeRate: float = 0.0
    # 기업 규모 ("Large" | "Mid" | "Small")
    sizeClass: str = "Mid"
    # 업종 경기민감도 ("high" | "moderate" | "defensive")
    sectorCyclicality: str = "moderate"
    # 성장률 백분위 (0~100, 시장 내 순위)
    growthRankPct: float = 50.0
    # 공시 정성 신호 (Phase 2)
    disclosureTone: float = 0.0  # -1.0 ~ +1.0
    disclosureChangeIntensity: float = 0.0  # 0.0 ~ 1.0
    disclosureGrowthAdj: float = 0.0  # %p
    disclosureConfidence: str = "low"  # "high" | "medium" | "low"
    # 시나리오별 확률 조정치 (결과)
    adjustments: dict[str, float] = field(default_factory=dict)
    # 조정 근거 설명
    reasoning: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        lines = ["[Context Signals -- 맥락 신호]"]
        if self.insightGrades:
            gradesStr = ", ".join(f"{k}={v}" for k, v in self.insightGrades.items())
            lines.append(f"  인사이트 등급: {gradesStr}")
        lines.append(f"  공시 변화율: {self.diffChangeRate:.1f}%")
        lines.append(f"  리스크 변화율: {self.riskChangeRate:.1f}%")
        lines.append(f"  기업 규모: {self.sizeClass}")
        lines.append(f"  업종 경기민감도: {self.sectorCyclicality}")
        lines.append(f"  성장 순위: 상위 {self.growthRankPct:.0f}%")
        if self.disclosureTone != 0.0:
            lines.append(
                f"  공시 tone: {self.disclosureTone:+.2f} (강도 {self.disclosureChangeIntensity:.2f}, 조정 {self.disclosureGrowthAdj:+.1f}%p, {self.disclosureConfidence})"
            )
        if self.adjustments:
            lines.append(f"  확률 조정: {self.adjustments}")
        if self.reasoning:
            lines.append("  조정 근거:")
            for r in self.reasoning:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# ======================================
# 신호 수집 (Company 객체에서)
# ======================================


def collectSignals(company, *, usePredictionAxis: bool = False) -> ContextSignals:
    """Company 객체에서 맥락 신호를 수집한다.

    usePredictionAxis=True이면 analysis("forecast", "예측신호") 결과를 추가로 소비하여
    공시 tone, 변화 강도, 성장 조정치를 enrichment한다.

    Capabilities:
        - insight 등급·diff 변화율·rank·sector cyclicality 통합 수집
        - 예측신호 축 선택적 enrichment

    Parameters
    ----------
    company : Company
        분석 대상 기업.
    usePredictionAxis : bool
        예측신호 축 결과 추가 소비 여부.

    Returns
    -------
    ContextSignals
        insight 등급, diff 변화율, 사이클 정보 등 맥락 신호.

    Guide:
        adjustProbabilities 진입 전 단계에서 호출해 ContextSignals 를 채운다.

    When:
        시나리오 확률 보정에 필요한 사전 신호 수집이 필요할 때.

    How:
        Company 의 insights·_docs.diff·rank·sectorInfo 를 순차적으로 흡수.

    Requires:
        Company 객체 (insights, _docs, sectorInfo 일부 가능).

    Raises:
        없음. 각 신호 소스 실패는 except 후 skip.

    Example:
        >>> sig = collectSignals(company, usePredictionAxis=True)
        >>> isinstance(sig, ContextSignals)
        True

    See Also:
        - adjustProbabilities : 수집된 신호로 확률 조정
        - ContextSignals : 결과 dataclass

    AIContext:
        AI 답변 시 시나리오 확률 보정 근거를 추적하는 데 인용.
    """
    signals = ContextSignals()

    # 1. insight 등급 수집.
    # 예전에는 `company.insights` 를 읽었다. 그 accessor 는 사라졌는데 아래 except 가
    # AttributeError 를 삼켜서, 등급이 늘 빈 dict 인 채로 조용히 남았다. 그래서 확률 보정
    # 여덟 규칙 중 넷(수익성·건전성·기회·현금흐름)이 한 번도 발동하지 못했다. 지금 살아 있는
    # 산출 경로는 재무 인사이트 파이프라인이고, 그 결과가 같은 영역 등급을 그대로 준다.
    try:
        from dartlab.analysis.financial.insight.pipeline import analyzeFinancial

        result = analyzeFinancial(company.stockCode, company)
        if result is not None:
            wanted = ("profitability", "health", "cashflow", "governance", "risk", "opportunity", "performance")
            grades = result.grades()
            signals.insightGrades = {k: grades[k] for k in wanted if grades.get(k)}
    except (AttributeError, FileNotFoundError, KeyError, RuntimeError, TypeError, ValueError) as exc:
        _log.debug("insight 등급 수집 실패 (%s): %s", getattr(company, "stockCode", "?"), exc)

    # 2. diff 변화율 수집
    try:
        diffResult = company.diff()
        if diffResult and hasattr(diffResult, "changeRate"):
            signals.diffChangeRate = diffResult.changeRate or 0.0
        # 리스크 topic 변화율
        if diffResult and hasattr(diffResult, "topicChanges"):
            riskTopics = ["riskFactors", "riskDerivative", "contingentLiabilities"]
            riskChanges = []
            for tc in diffResult.topicChanges:
                if hasattr(tc, "topic") and tc.topic in riskTopics:
                    riskChanges.append(tc.changeRate or 0)
            if riskChanges:
                signals.riskChangeRate = sum(riskChanges) / len(riskChanges)
    except (AttributeError, TypeError):
        pass

    # 3. rank (규모, 성장 순위)
    try:
        rankInfo = getattr(company, "rank", None)
        if rankInfo:
            if hasattr(rankInfo, "sizeClass"):
                signals.sizeClass = rankInfo.sizeClass or "Mid"
            if hasattr(rankInfo, "growthRankPct"):
                signals.growthRankPct = rankInfo.growthRankPct or 50.0
    except (AttributeError, TypeError):
        pass

    # 4. sector 경기민감도
    #
    # 예전에는 company.sectorInfo 를 보고 없으면 company.profile.sectorName 을 봤다. 두
    # 이름 다 Company 표면에 없어서 업종 키가 늘 None 이었고 경기민감도가 한 번도 채워지지
    # 않았다. 업종 키 해소는 _getSectorKey 가 정본이다.
    try:
        from dartlab.analysis.financial._companyLookup import _getSectorKey
        from dartlab.synth.scenario import getElasticity as get_elasticity

        sectorKey = _getSectorKey(company)
        if sectorKey:
            signals.sectorCyclicality = get_elasticity(sectorKey).cyclicality
    except (ImportError, AttributeError, TypeError) as exc:
        _log.debug("업종 경기민감도 해소 실패: %s", exc)

    # 5. 예측신호 축 enrichment (선택적)
    if usePredictionAxis:
        _enrichFromPredictionAxis(company, signals)

    # 신호에서 조정치 계산
    adjustments, reasoning = _computeAdjustments(signals)
    signals.adjustments = adjustments
    signals.reasoning = reasoning

    return signals


def _enrichFromPredictionAxis(company, signals: ContextSignals) -> None:
    """analysis("forecast", "예측신호") 결과로 ContextSignals를 보강한다."""
    try:
        from dartlab.analysis.financial.predictionSignals import (
            calcDisclosureDelta,
            calcPredictionSynthesis,
        )

        # 공시 변화 신호 → disclosure 필드 enrichment
        disclosure = calcDisclosureDelta(company)
        if disclosure is not None:
            intensity = disclosure["overallChangeRate"] / 100.0
            signals.disclosureChangeIntensity = intensity
            if disclosure["signalDirection"] == "negative":
                signals.disclosureTone = -0.3 * intensity
            elif disclosure["signalDirection"] == "positive":
                signals.disclosureTone = 0.2 * intensity

        # 종합 신호 → 성장 조정치
        synthesis = calcPredictionSynthesis(company)
        if synthesis is not None:
            bias = synthesis["aiContext"]["directionBias"]
            if abs(bias) > 0.2:
                signals.disclosureGrowthAdj = bias * 3.0
                signals.disclosureConfidence = synthesis["confidence"]
    except (ImportError, TypeError, KeyError):
        pass

    # Prediction Space — 6대 축 기반 시나리오 확률 조정
    _enrichFromPredictionSpace(signals)


def _enrichFromPredictionSpace(signals: ContextSignals) -> None:
    """PredictionSpace 6대 축으로 시나리오 확률을 조정한다."""
    try:
        from dartlab.analysis.forecast.predictionSpace import getPredictionSpace

        space = getPredictionSpace()
        if space is None:
            return

        adj = signals.adjustments
        reasons = signals.reasoning

        # 경기축 수축 → adverse 확률 상승
        bc = space.axes.get("businessCycle")
        if bc and bc.level < -0.3:
            delta = min(0.08, abs(bc.level) * 0.1)
            adj["adverse"] = adj.get("adverse", 0.0) + delta
            adj["baseline"] = adj.get("baseline", 0.0) - delta
            reasons.append(f"경기축 수축 (level={bc.level:.2f}) -> adverse +{delta:.0%}p")

        # 금리축 급등 → rate_hike 시나리오
        ir = space.axes.get("interestRate")
        if ir and ir.level > 0.3 and ir.direction == "improving":
            adj["rate_hike"] = adj.get("rate_hike", 0.0) + 0.05
            adj["baseline"] = adj.get("baseline", 0.0) - 0.03
            reasons.append(f"금리축 상승 (level={ir.level:.2f}, {ir.direction}) -> rate_hike +5%p")

        # 환율축 급변 (약세) → 수출기업 유리, 내수기업 불리
        fx = space.axes.get("fxRate")
        if fx and fx.level > 0.3:
            adj["baseline"] = adj.get("baseline", 0.0) + 0.02
            reasons.append(f"환율축 원화약세 (level={fx.level:.2f}) -> 수출기업 baseline +2%p")

        # 심리축 악화 → 소비 위축
        st = space.axes.get("sentiment")
        if st and st.level < -0.3:
            adj["adverse"] = adj.get("adverse", 0.0) + 0.03
            reasons.append(f"심리축 위축 (level={st.level:.2f}) -> adverse +3%p")

    except (ImportError, TypeError):
        pass


# ======================================
# 확률 재가중
# ======================================


_ADJUSTMENT_RULES = [
    # (조건 함수, 시나리오 조정 dict, 근거 메시지)
]


def _computeAdjustments(signals: ContextSignals) -> tuple[dict[str, float], list[str]]:
    """맥락 신호 -> 확률 조정치 + 근거 계산."""
    adj: dict[str, float] = {}
    reasons: list[str] = []

    def _add(scenario: str, delta: float, reason: str) -> None:
        """시나리오별 조정값을 누적하고 사유 기록."""
        adj[scenario] = adj.get(scenario, 0.0) + delta
        reasons.append(reason)

    grades = signals.insightGrades

    # 규칙 1: 수익성 위험 (profitability D/F -> adverse +5%p)
    if grades.get("profitability") in ("D", "F"):
        _add("adverse", 0.05, f"수익성 등급 {grades['profitability']} -> 하방 리스크 +5%p")
        _add("baseline", -0.05, "수익성 약화 -> baseline -5%p")

    # 규칙 2: 재무건전성 위험 (health D/F -> adverse +5%p)
    if grades.get("health") in ("D", "F"):
        _add("adverse", 0.05, f"건전성 등급 {grades['health']} -> 하방 리스크 +5%p")
        _add("baseline", -0.05, "건전성 약화 -> baseline -5%p")

    # 규칙 3: 리스크 급변 (riskChangeRate > 60% -> adverse +5%p)
    if signals.riskChangeRate > 60:
        _add("adverse", 0.05, f"리스크 공시 변화율 {signals.riskChangeRate:.0f}% -> adverse +5%p")
        _add("baseline", -0.05, "리스크 급변 -> baseline -5%p")

    # 규칙 4: 높은 기회 (opportunity A -> baseline +5%p)
    if grades.get("opportunity") in ("A",):
        _add("baseline", 0.05, "기회 등급 A -> baseline +5%p")
        _add("adverse", -0.03, "긍정 기회 -> adverse -3%p")

    # 규칙 5: 경기민감 업종 (high -> rate_hike +3%p)
    if signals.sectorCyclicality == "high":
        _add("rate_hike", 0.03, "경기민감 업종 -> rate_hike +3%p")
        _add("baseline", -0.03, "경기민감 -> baseline -3%p")

    # 규칙 6: 방어적 업종 (defensive -> baseline +5%p, adverse -3%p)
    if signals.sectorCyclicality == "defensive":
        _add("baseline", 0.05, "방어적 업종 -> baseline +5%p")
        _add("adverse", -0.03, "방어적 -> adverse -3%p")

    # 규칙 7: 고성장 상위 20% (baseline +3%p)
    if signals.growthRankPct <= 20:
        _add("baseline", 0.03, f"성장 상위 {signals.growthRankPct:.0f}% -> baseline +3%p")

    # 규칙 8: 현금흐름 위험 (cashflow D/F -> adverse +3%p)
    if grades.get("cashflow") in ("D", "F"):
        _add("adverse", 0.03, f"현금흐름 등급 {grades['cashflow']} -> adverse +3%p")

    return adj, reasons


def adjustProbabilities(
    baseProbs: dict[str, float],
    signals: ContextSignals,
) -> dict[str, float]:
    """기본 확률을 맥락 신호로 재가중한다.

    Capabilities:
        - ContextSignals 의 adjustments 를 적용해 시나리오 확률 재가중
        - 음수 방지 하한 + 합계 1.0 정규화

    Parameters
    ----------
    baseProbs : dict[str, float]
        시나리오별 기본 확률.
    signals : ContextSignals
        맥락 신호.

    Returns
    -------
    dict[str, float]
        재가중된 시나리오별 확률 (합계 1.0 정규화).

    Guide:
        collectSignals 결과를 입력으로 받아 _computeAdjustments 자동 호출.

    When:
        기본 확률을 회사 맥락 신호로 보정해야 할 때.

    How:
        signals.adjustments 가 비어 있으면 _computeAdjustments 호출 후 적용.

    Requires:
        ContextSignals (collectSignals 결과 권장).

    Raises:
        없음. 빈 신호는 baseProbs 그대로 반환.

    Example:
        >>> adjustProbabilities({"baseline": 0.5, "adverse": 0.5}, sig)
        {'baseline': ..., 'adverse': ...}

    See Also:
        - collectSignals : 신호 수집
        - calibrateScenarios : 외부 시장 신호로 보정

    AIContext:
        AI 답변 시 "맥락 신호 N 개로 시나리오 확률 X→Y 조정" 인용.
    """
    # adjustments가 아직 계산되지 않았으면 자동 계산
    if not signals.adjustments and (
        signals.insightGrades
        or signals.riskChangeRate > 0
        or signals.sectorCyclicality != "moderate"
        or signals.growthRankPct <= 20
    ):
        adj, reasoning = _computeAdjustments(signals)
        signals.adjustments = adj
        signals.reasoning = reasoning

    result = dict(baseProbs)

    for scenario, delta in signals.adjustments.items():
        if scenario in result:
            result[scenario] += delta

    # 하한 1%p (음수 확률 방지)
    for k in result:
        result[k] = max(result[k], 0.01)

    # 합계 정규화 -> 1.0
    total = sum(result.values())
    if total > 0:
        result = {k: v / total for k, v in result.items()}

    return result
