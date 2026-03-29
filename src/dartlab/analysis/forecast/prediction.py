"""Context Signal Fusion — 기업 맥락 신호 -> 시나리오 확률 동적 재가중."""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.core.finance.scenario import NOISE_CONFIG, getNoiseSigma

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


def collectSignals(company) -> ContextSignals:
    """Company 객체에서 맥락 신호를 수집한다."""
    signals = ContextSignals()

    # 1. insight 등급 수집
    try:
        insights = company.insights
        if insights:
            for areaKey in ("profitability", "health", "cashflow", "governance", "risk", "opportunity", "performance"):
                area = getattr(insights, areaKey, None)
                if area and hasattr(area, "grade"):
                    signals.insightGrades[areaKey] = area.grade
    except (AttributeError, TypeError):
        pass

    # 2. diff 변화율 수집
    try:
        diffResult = company.docs.diff()
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
        rankInfo = getattr(company, "rank", None) or getattr(company, "rankInfo", None)
        if rankInfo:
            if hasattr(rankInfo, "sizeClass"):
                signals.sizeClass = rankInfo.sizeClass or "Mid"
            if hasattr(rankInfo, "growthRankPct"):
                signals.growthRankPct = rankInfo.growthRankPct or 50.0
    except (AttributeError, TypeError):
        pass

    # 4. sector 경기민감도
    try:
        from dartlab.core.finance.scenario import getElasticity as get_elasticity

        sectorKey = None
        # sectorInfo dict에서 가져오기
        sectorInfo = getattr(company, "sectorInfo", None)
        if sectorInfo and isinstance(sectorInfo, dict):
            sectorKey = sectorInfo.get("sector")
        # profile.sectorName fallback
        if not sectorKey:
            profile = getattr(company, "profile", None)
            if profile and hasattr(profile, "sectorName"):
                sectorKey = profile.sectorName
        if sectorKey:
            elasticity = get_elasticity(sectorKey)
            signals.sectorCyclicality = elasticity.cyclicality
    except (ImportError, AttributeError, TypeError):
        pass

    # 신호에서 조정치 계산
    adjustments, reasoning = _computeAdjustments(signals)
    signals.adjustments = adjustments
    signals.reasoning = reasoning

    return signals


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
    """기본 확률을 맥락 신호로 재가중한다."""
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
