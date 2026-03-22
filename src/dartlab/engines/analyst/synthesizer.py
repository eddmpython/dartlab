"""Analyst Synthesizer — 복수 밸류에이션 가중평균 합성.

DCF + 컨센서스 + 피어 멀티플 + 상대가치 → 가중평균 목표가.
데이터 미가용 시 가용 방법 간 비례 재배분.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from ..gather.types import MarketSnapshot
from .types import AnalystReport, ValuationMethod, _classify_opinion

log = logging.getLogger(__name__)

# 기본 가중치 (모든 데이터 가용 시)
DEFAULT_WEIGHTS: dict[str, float] = {
    "dcf": 0.30,
    "consensus": 0.35,
    "peer_multiple": 0.20,
    "relative": 0.15,
}


def synthesize(
    *,
    dcf_target: float | None = None,
    dcf_confidence: float = 0.5,
    market: MarketSnapshot | None = None,
    company_financials: dict | None = None,
    shares: int = 0,
    current_price: float = 0.0,
    company_name: str = "",
    stock_code: str = "",
    custom_weights: dict[str, float] | None = None,
) -> AnalystReport:
    """복수 밸류에이션 → 가중평균 목표가 + 종합 의견.

    Args:
        dcf_target: DCF 가중 목표가 (engines/common/finance/pricetarget).
        dcf_confidence: DCF 신뢰도 (0~1).
        market: MarketSnapshot (engines/market/collector).
        company_financials: {"eps": float, "bps": float, "ebitda": float, ...}
        shares: 발행주식수.
        current_price: 현재 주가.
        company_name: 회사명.
        stock_code: 종목코드.
        custom_weights: 사용자 정의 가중치 (기본값 덮어쓰기).

    Returns:
        AnalystReport.
    """
    methods: list[ValuationMethod] = []
    reasoning: list[str] = []
    warnings: list[str] = []
    weights = dict(custom_weights or DEFAULT_WEIGHTS)

    # ── 1. DCF 밸류에이션 ──
    if dcf_target and dcf_target > 0:
        methods.append(ValuationMethod(
            name="dcf",
            value=dcf_target,
            weight=weights.get("dcf", 0.30),
            confidence=dcf_confidence,
            reasoning="자체 DCF 엔진 (MC 시뮬레이션 + 시나리오 가중)",
        ))
    else:
        # DCF 미가용 → 가중치 재배분
        removed = weights.pop("dcf", 0)
        if removed > 0:
            _redistribute(weights, removed)
            warnings.append("DCF 결과 미가용 — 가중치 재배분")

    # ── 2. 컨센서스 밸류에이션 ──
    consensus_target = _extract_consensus(market, weights, methods, reasoning, warnings)

    # ── 3. 피어 멀티플 밸류에이션 ──
    _extract_peer_multiple(market, company_financials, shares, weights, methods, reasoning, warnings)

    # ── 4. 상대가치 (역사적 밴드) ──
    _extract_relative(market, company_financials, weights, methods, reasoning, warnings)

    # ── 가중평균 계산 ──
    if not methods:
        warnings.append("사용 가능한 밸류에이션 방법이 없습니다")
        return AnalystReport(
            stock_code=stock_code,
            company_name=company_name,
            current_price=current_price,
            warnings=warnings,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    # 가중치 정규화
    total_weight = sum(m.weight for m in methods)
    if total_weight > 0:
        for m in methods:
            m.weight = m.weight / total_weight

    # 가중평균 목표가
    target_price = sum(m.value * m.weight for m in methods)

    # 종합 신뢰도 = 가중평균 신뢰도
    confidence = sum(m.confidence * m.weight for m in methods)

    # 업사이드
    upside = 0.0
    if current_price > 0:
        upside = (target_price - current_price) / current_price

    # 투자의견
    opinion = _classify_opinion(upside)

    # DCF-컨센서스 괴리 체크
    if dcf_target and consensus_target and dcf_target > 0 and consensus_target > 0:
        gap = abs(dcf_target - consensus_target) / max(dcf_target, consensus_target)
        if gap > 0.5:
            reasoning.append(
                f"DCF({dcf_target:,.0f})와 컨센서스({consensus_target:,.0f}) "
                f"괴리 {gap:.0%} — DCF 가중치 하향 적용"
            )
            # DCF 가중치 ×0.7 재조정
            for m in methods:
                if m.name == "dcf":
                    m.weight *= 0.7
            # 재정규화
            total_weight = sum(m.weight for m in methods)
            if total_weight > 0:
                for m in methods:
                    m.weight /= total_weight
            target_price = sum(m.value * m.weight for m in methods)
            if current_price > 0:
                upside = (target_price - current_price) / current_price
            opinion = _classify_opinion(upside)

    # 판단 근거 생성
    reasoning.append(
        f"종합 목표가 {target_price:,.0f}원 "
        f"= {' + '.join(f'{m.name}({m.value:,.0f}×{m.weight:.0%})' for m in methods)}"
    )

    return AnalystReport(
        stock_code=stock_code,
        company_name=company_name,
        target_price=target_price,
        current_price=current_price,
        upside=upside,
        opinion=opinion,
        methods=methods,
        confidence=confidence,
        reasoning=reasoning,
        warnings=warnings,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ══════════════════════════════════════
# 내부 헬퍼
# ══════════════════════════════════════


def _redistribute(weights: dict[str, float], removed: float) -> None:
    """제거된 가중치를 나머지에 비례 배분."""
    total = sum(weights.values())
    if total <= 0:
        return
    for k in weights:
        weights[k] += removed * (weights[k] / total)


def _extract_consensus(
    market: MarketSnapshot | None,
    weights: dict[str, float],
    methods: list[ValuationMethod],
    reasoning: list[str],
    warnings: list[str],
) -> float | None:
    """컨센서스 목표가 추출."""
    if not market or not market.consensus:
        removed = weights.pop("consensus", 0)
        if removed > 0:
            _redistribute(weights, removed)
            warnings.append("컨센서스 데이터 미가용 — 가중치 재배분")
        return None

    c = market.consensus
    confidence = 0.7  # 기본 신뢰도

    # 애널리스트 수에 따른 신뢰도 조정
    if c.analyst_count >= 10:
        confidence = 0.85
    elif c.analyst_count >= 5:
        confidence = 0.75
    elif c.analyst_count < 3:
        confidence = 0.5
        # 소수 애널리스트 → 가중치 ×0.5
        w = weights.get("consensus", 0)
        weights["consensus"] = w * 0.5
        removed = w * 0.5
        _redistribute({k: v for k, v in weights.items() if k != "consensus"}, removed)
        warnings.append(f"애널리스트 {c.analyst_count}명 — 컨센서스 신뢰도 낮음")

    methods.append(ValuationMethod(
        name="consensus",
        value=c.target_price,
        weight=weights.get("consensus", 0.35),
        confidence=confidence,
        reasoning=f"시장 컨센서스 (애널리스트 {c.analyst_count}명, 매수비율 {c.buy_ratio:.0%})",
    ))
    reasoning.append(
        f"컨센서스 목표가 {c.target_price:,.0f}원 "
        f"(범위: {c.low:,.0f}~{c.high:,.0f}, {c.analyst_count}명)"
    )
    return c.target_price


def _extract_peer_multiple(
    market: MarketSnapshot | None,
    financials: dict | None,
    shares: int,
    weights: dict[str, float],
    methods: list[ValuationMethod],
    reasoning: list[str],
    warnings: list[str],
) -> None:
    """피어 멀티플 → 상대가치 목표가."""
    # MVP에서는 업종 PER만 사용 (Phase 2에서 글로벌 피어 추가)
    if not market or not financials or shares <= 0:
        removed = weights.pop("peer_multiple", 0)
        if removed > 0:
            _redistribute(weights, removed)
        return

    sector_per = market.multiples.get("sector_per")
    eps = financials.get("eps")

    if not sector_per or not eps or eps <= 0:
        removed = weights.pop("peer_multiple", 0)
        if removed > 0:
            _redistribute(weights, removed)
            warnings.append("피어 멀티플 계산 불가 (업종 PER 또는 EPS 없음)")
        return

    peer_target = sector_per * eps
    methods.append(ValuationMethod(
        name="peer_multiple",
        value=peer_target,
        weight=weights.get("peer_multiple", 0.20),
        confidence=0.6,
        reasoning=f"업종 PER({sector_per:.1f}) × EPS({eps:,.0f})",
    ))
    reasoning.append(f"피어 멀티플 목표가 {peer_target:,.0f}원 (업종PER {sector_per:.1f}×EPS {eps:,.0f})")


def _extract_relative(
    market: MarketSnapshot | None,
    financials: dict | None,
    weights: dict[str, float],
    methods: list[ValuationMethod],
    reasoning: list[str],
    warnings: list[str],
) -> None:
    """상대가치 — 52주 밴드 + PBR 역사 기반."""
    if not market or not market.price_range_52w:
        removed = weights.pop("relative", 0)
        if removed > 0:
            _redistribute(weights, removed)
        return

    low_52w, high_52w = market.price_range_52w
    if low_52w <= 0 or high_52w <= 0:
        removed = weights.pop("relative", 0)
        if removed > 0:
            _redistribute(weights, removed)
        return

    # 52주 중간값을 상대가치 기준
    # PBR이 있으면 PBR 기반 보정
    midpoint = (low_52w + high_52w) / 2

    bps = (financials or {}).get("bps")
    current_pbr = market.multiples.get("pbr")
    if bps and current_pbr and bps > 0:
        # 적정 PBR = 현재 PBR의 ±20% 밴드 중간
        fair_pbr = current_pbr * 1.0  # 현재 PBR 유지 가정
        pbr_target = bps * fair_pbr
        # 52주 중간값과 PBR 기반 평균
        relative_target = (midpoint + pbr_target) / 2
        reasoning_text = f"52주 중간({midpoint:,.0f}) + PBR({fair_pbr:.2f}×BPS {bps:,.0f}) 평균"
    else:
        relative_target = midpoint
        reasoning_text = f"52주 범위 중간값 ({low_52w:,.0f}~{high_52w:,.0f})"

    methods.append(ValuationMethod(
        name="relative",
        value=relative_target,
        weight=weights.get("relative", 0.15),
        confidence=0.5,
        reasoning=reasoning_text,
    ))
    reasoning.append(f"상대가치 목표가 {relative_target:,.0f}원 ({reasoning_text})")
