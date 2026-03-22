"""Analyst Calibrator — 외부 데이터로 DCF 시나리오 확률 보정.

컨센서스, 수급, 매크로 데이터를 기반으로
DCF 시나리오 확률을 재가중한다.
"""

from __future__ import annotations

import logging

from dartlab.engines.gather.types import MarketSnapshot

log = logging.getLogger(__name__)


def calibrate_scenarios(
    base_probs: dict[str, float],
    dcf_baseline_price: float,
    market: MarketSnapshot,
) -> tuple[dict[str, float], list[str]]:
    """외부 시장 데이터로 DCF 시나리오 확률 보정.

    Args:
        base_probs: 기존 시나리오 확률 (예: {"baseline": 0.40, ...}).
        dcf_baseline_price: DCF baseline 시나리오 목표가.
        market: MarketSnapshot (컨센서스, 수급 포함).

    Returns:
        (보정된 확률 dict, 보정 근거 list).
    """
    probs = dict(base_probs)
    reasons: list[str] = []

    def _adjust(scenario: str, delta: float, reason: str) -> None:
        if scenario in probs:
            probs[scenario] += delta
            reasons.append(reason)

    # ── 규칙 1: 컨센서스 vs DCF 괴리 ──
    if market.consensus and dcf_baseline_price > 0:
        consensus_price = market.consensus.target_price
        if consensus_price > 0:
            ratio = consensus_price / dcf_baseline_price
            if ratio > 1.5:
                # 컨센서스가 DCF보다 50% 이상 높음 → optimistic ↑
                _adjust(
                    "optimistic",
                    0.05,
                    f"컨센서스({consensus_price:,.0f})가 DCF baseline보다 {ratio:.1f}배 → optimistic +5%p",
                )
                _adjust("baseline", -0.03, "컨센서스 상향 → baseline -3%p")
                _adjust("adverse", -0.02, "컨센서스 상향 → adverse -2%p")
            elif ratio < 0.7:
                # 컨센서스가 DCF보다 30% 이상 낮음 → adverse ↑
                _adjust(
                    "adverse", 0.05, f"컨센서스({consensus_price:,.0f})가 DCF baseline보다 {ratio:.1f}배 → adverse +5%p"
                )
                _adjust("baseline", -0.03, "컨센서스 하향 → baseline -3%p")
                _adjust("optimistic", -0.02, "컨센서스 하향 → optimistic -2%p")

    # ── 규칙 2: 매수 비율 ──
    if market.consensus and market.consensus.analyst_count >= 3:
        buy_ratio = market.consensus.buy_ratio
        if buy_ratio >= 0.8:
            _adjust("baseline", 0.03, f"매수의견 {buy_ratio:.0%} → baseline +3%p")
        elif buy_ratio < 0.3:
            _adjust("adverse", 0.03, f"매수의견 {buy_ratio:.0%} (낮음) → adverse +3%p")
            _adjust("baseline", -0.03, "매수의견 저조 → baseline -3%p")

    # ── 규칙 3: 외국인 순매도 ──
    foreign_net = market.supply_demand.get("foreign_net")
    if foreign_net is not None and foreign_net < -1_000_000:
        _adjust("adverse", 0.03, f"외국인 순매도 {foreign_net:,.0f}주 → adverse +3%p")
        _adjust("baseline", -0.03, "외국인 순매도 → baseline -3%p")
    elif foreign_net is not None and foreign_net > 1_000_000:
        _adjust("baseline", 0.03, f"외국인 순매수 {foreign_net:,.0f}주 → baseline +3%p")

    # ── 규칙 4: 기준금리 (매크로) ──
    base_rate = market.macro.get("base_rate")
    if base_rate is not None:
        if base_rate > 4.0:
            _adjust("rate_hike", 0.05, f"기준금리 {base_rate:.1f}% (고금리) → rate_hike +5%p")
            _adjust("baseline", -0.03, "고금리 → baseline -3%p")
        elif base_rate < 2.0:
            _adjust("rate_hike", -0.03, f"기준금리 {base_rate:.1f}% (저금리) → rate_hike -3%p")
            _adjust("baseline", 0.03, "저금리 → baseline +3%p")

    # ── 정규화 (합계=1.0, 하한 1%p) ──
    for k in probs:
        probs[k] = max(probs[k], 0.01)
    total = sum(probs.values())
    if total > 0:
        probs = {k: v / total for k, v in probs.items()}

    return probs, reasons
