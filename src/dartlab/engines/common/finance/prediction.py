"""Context Signal Fusion — 기업 맥락 신호 → 시나리오 확률 동적 재가중.

dartlab의 insight(7등급), diff(변화율), rank(순위), sector(업종) 엔진에서
맥락 신호를 수집하고, 이를 기반으로 시나리오 확률을 재가중한다.

세상에 없는 이유: 인사이트 등급 + 공시 변화율 + 시장 순위 → 시나리오 확률
재가중은 어떤 오픈소스 도구에도 존재하지 않는다.

외부 의존성 제로 (dartlab 내부 엔진만 optional import).
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ══════════════════════════════════════
# 데이터 구조
# ══════════════════════════════════════


@dataclass
class ContextSignals:
    """기업 맥락 신호 — 시나리오 확률 조정의 근거."""

    # insight 등급 (7개 영역)
    insight_grades: dict[str, str] = field(default_factory=dict)
    # 전체 sections 평균 변화율 (0~100)
    diff_change_rate: float = 0.0
    # 리스크 topic 변화율 (0~100)
    risk_change_rate: float = 0.0
    # 기업 규모 ("Large" | "Mid" | "Small")
    size_class: str = "Mid"
    # 업종 경기민감도 ("high" | "moderate" | "defensive")
    sector_cyclicality: str = "moderate"
    # 성장률 백분위 (0~100, 시장 내 순위)
    growth_rank_pct: float = 50.0
    # 시나리오별 확률 조정치 (결과)
    adjustments: dict[str, float] = field(default_factory=dict)
    # 조정 근거 설명
    reasoning: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        lines = ["[Context Signals — 맥락 신호]"]
        if self.insight_grades:
            grades_str = ", ".join(f"{k}={v}" for k, v in self.insight_grades.items())
            lines.append(f"  인사이트 등급: {grades_str}")
        lines.append(f"  공시 변화율: {self.diff_change_rate:.1f}%")
        lines.append(f"  리스크 변화율: {self.risk_change_rate:.1f}%")
        lines.append(f"  기업 규모: {self.size_class}")
        lines.append(f"  업종 경기민감도: {self.sector_cyclicality}")
        lines.append(f"  성장 순위: 상위 {self.growth_rank_pct:.0f}%")
        if self.adjustments:
            lines.append(f"  확률 조정: {self.adjustments}")
        if self.reasoning:
            lines.append("  조정 근거:")
            for r in self.reasoning:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# ══════════════════════════════════════
# MC 노이즈 설정 — 기업 규모별 σ 차등
# ══════════════════════════════════════


NOISE_CONFIG: dict[str, dict[str, float]] = {
    "growth": {"base_sigma": 1.5, "Small": 1.5, "Mid": 1.0, "Large": 0.8},
    "margin": {"base_sigma": 2.5, "Small": 1.3, "Mid": 1.0, "Large": 0.9},
    "wacc": {"base_sigma": 0.8, "Small": 1.5, "Mid": 1.0, "Large": 0.7},
    "capex": {"base_sigma": 1.0, "Small": 1.2, "Mid": 1.0, "Large": 0.9},
    "tax": {"base_sigma": 1.0, "Small": 1.0, "Mid": 1.0, "Large": 1.0},
}


def get_noise_sigma(variable: str, size_class: str = "Mid") -> float:
    """변수별 × 규모별 noise σ 반환."""
    cfg = NOISE_CONFIG.get(variable, {"base_sigma": 1.0})
    base = cfg["base_sigma"]
    mult = cfg.get(size_class, 1.0)
    return base * mult


# ══════════════════════════════════════
# 신호 수집 (Company 객체에서)
# ══════════════════════════════════════


def collect_signals(company) -> ContextSignals:
    """Company 객체에서 맥락 신호를 수집한다.

    optional import 방식으로, Company 객체가 없어도 기본값 반환.
    AnalysisResult(insights)의 7개 영역 등급을 읽고,
    diff/rank/sector 가용시 추가 수집.
    """
    signals = ContextSignals()

    # 1. insight 등급 수집
    try:
        insights = company.insights
        if insights:
            # AnalysisResult: 개별 영역이 속성으로 존재
            for area_key in ("profitability", "health", "cashflow", "governance", "risk", "opportunity", "performance"):
                area = getattr(insights, area_key, None)
                if area and hasattr(area, "grade"):
                    signals.insight_grades[area_key] = area.grade
    except (AttributeError, TypeError):
        pass

    # 2. diff 변화율 수집
    try:
        diff_result = company.docs.diff()
        if diff_result and hasattr(diff_result, "changeRate"):
            signals.diff_change_rate = diff_result.changeRate or 0.0
        # 리스크 topic 변화율
        if diff_result and hasattr(diff_result, "topicChanges"):
            risk_topics = ["riskFactors", "riskDerivative", "contingentLiabilities"]
            risk_changes = []
            for tc in diff_result.topicChanges:
                if hasattr(tc, "topic") and tc.topic in risk_topics:
                    risk_changes.append(tc.changeRate or 0)
            if risk_changes:
                signals.risk_change_rate = sum(risk_changes) / len(risk_changes)
    except (AttributeError, TypeError):
        pass

    # 3. rank (규모, 성장 순위)
    try:
        rank_info = getattr(company, "rank", None) or getattr(company, "rankInfo", None)
        if rank_info:
            if hasattr(rank_info, "sizeClass"):
                signals.size_class = rank_info.sizeClass or "Mid"
            if hasattr(rank_info, "growthRankPct"):
                signals.growth_rank_pct = rank_info.growthRankPct or 50.0
    except (AttributeError, TypeError):
        pass

    # 4. sector 경기민감도
    try:
        from dartlab.engines.common.finance.simulation import get_elasticity

        sector_key = None
        # sectorInfo dict에서 가져오기
        sector_info = getattr(company, "sectorInfo", None)
        if sector_info and isinstance(sector_info, dict):
            sector_key = sector_info.get("sector")
        # profile.sectorName fallback
        if not sector_key:
            profile = getattr(company, "profile", None)
            if profile and hasattr(profile, "sectorName"):
                sector_key = profile.sectorName
        if sector_key:
            elasticity = get_elasticity(sector_key)
            signals.sector_cyclicality = elasticity.cyclicality_label
    except (ImportError, AttributeError, TypeError):
        pass

    # 신호에서 조정치 계산
    adjustments, reasoning = _compute_adjustments(signals)
    signals.adjustments = adjustments
    signals.reasoning = reasoning

    return signals


# ══════════════════════════════════════
# 확률 재가중
# ══════════════════════════════════════


_ADJUSTMENT_RULES = [
    # (조건 함수, 시나리오 조정 dict, 근거 메시지)
]


def _compute_adjustments(signals: ContextSignals) -> tuple[dict[str, float], list[str]]:
    """맥락 신호 → 확률 조정치 + 근거 계산.

    투명성 원칙: 모든 조정에 reasoning 첨부.
    """
    adj: dict[str, float] = {}
    reasons: list[str] = []

    def _add(scenario: str, delta: float, reason: str) -> None:
        adj[scenario] = adj.get(scenario, 0.0) + delta
        reasons.append(reason)

    grades = signals.insight_grades

    # 규칙 1: 수익성 위험 (profitability D/F → adverse +5%p)
    if grades.get("profitability") in ("D", "F"):
        _add("adverse", 0.05, f"수익성 등급 {grades['profitability']} → 하방 리스크 +5%p")
        _add("baseline", -0.05, f"수익성 약화 → baseline -5%p")

    # 규칙 2: 재무건전성 위험 (health D/F → adverse +5%p)
    if grades.get("health") in ("D", "F"):
        _add("adverse", 0.05, f"건전성 등급 {grades['health']} → 하방 리스크 +5%p")
        _add("baseline", -0.05, f"건전성 약화 → baseline -5%p")

    # 규칙 3: 리스크 급변 (risk_change > 60% → adverse +5%p)
    if signals.risk_change_rate > 60:
        _add("adverse", 0.05, f"리스크 공시 변화율 {signals.risk_change_rate:.0f}% → adverse +5%p")
        _add("baseline", -0.05, "리스크 급변 → baseline -5%p")

    # 규칙 4: 높은 기회 (opportunity A → baseline +5%p)
    if grades.get("opportunity") in ("A",):
        _add("baseline", 0.05, "기회 등급 A → baseline +5%p")
        _add("adverse", -0.03, "긍정 기회 → adverse -3%p")

    # 규칙 5: 경기민감 업종 (high → rate_hike +3%p)
    if signals.sector_cyclicality == "high":
        _add("rate_hike", 0.03, "경기민감 업종 → rate_hike +3%p")
        _add("baseline", -0.03, "경기민감 → baseline -3%p")

    # 규칙 6: 방어적 업종 (defensive → baseline +5%p, adverse -3%p)
    if signals.sector_cyclicality == "defensive":
        _add("baseline", 0.05, "방어적 업종 → baseline +5%p")
        _add("adverse", -0.03, "방어적 → adverse -3%p")

    # 규칙 7: 고성장 상위 20% (baseline +3%p)
    if signals.growth_rank_pct <= 20:
        _add("baseline", 0.03, f"성장 상위 {signals.growth_rank_pct:.0f}% → baseline +3%p")

    # 규칙 8: 현금흐름 위험 (cashflow D/F → adverse +3%p)
    if grades.get("cashflow") in ("D", "F"):
        _add("adverse", 0.03, f"현금흐름 등급 {grades['cashflow']} → adverse +3%p")

    return adj, reasons


def adjust_probabilities(
    base_probs: dict[str, float],
    signals: ContextSignals,
) -> dict[str, float]:
    """기본 확률을 맥락 신호로 재가중한다.

    조정 후 합계 = 1.0 보장 (비례 정규화).
    음수 확률 방지 (하한 1%p).

    Args:
        base_probs: 시나리오별 기본 확률 (예: {"baseline": 0.40, ...}).
        signals: ContextSignals (adjustments 포함).

    Returns:
        재가중된 확률 dict.
    """
    # adjustments가 아직 계산되지 않았으면 자동 계산
    if not signals.adjustments and (signals.insight_grades or signals.risk_change_rate > 0 or signals.sector_cyclicality != "moderate" or signals.growth_rank_pct <= 20):
        adj, reasoning = _compute_adjustments(signals)
        signals.adjustments = adj
        signals.reasoning = reasoning

    result = dict(base_probs)

    for scenario, delta in signals.adjustments.items():
        if scenario in result:
            result[scenario] += delta

    # 하한 1%p (음수 확률 방지)
    for k in result:
        result[k] = max(result[k], 0.01)

    # 합계 정규화 → 1.0
    total = sum(result.values())
    if total > 0:
        result = {k: v / total for k, v in result.items()}

    return result
