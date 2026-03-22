"""Analyst 엔진 데이터 타입 — 종합 분석 결과."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValuationMethod:
    """개별 밸류에이션 방법론 결과."""

    name: str = ""  # "dcf", "consensus", "peer_multiple", "relative"
    value: float = 0.0  # 산출 목표가
    weight: float = 0.0  # 가중치 (0~1)
    confidence: float = 0.0  # 신뢰도 (0~1)
    reasoning: str = ""  # 산출 근거

    def __repr__(self) -> str:
        return (
            f"{self.name}: {self.value:,.0f}원 "
            f"(가중치={self.weight:.0%}, 신뢰도={self.confidence:.0%})"
        )


# 투자 의견 매핑
_OPINION_MAP = {
    "strong_buy": "강력매수",
    "buy": "매수",
    "hold": "중립",
    "sell": "매도",
    "strong_sell": "강력매도",
}


def _classify_opinion(upside: float) -> str:
    """업사이드 → 투자의견 분류.

    Args:
        upside: (target - current) / current 비율.

    Returns:
        "강력매수" | "매수" | "중립" | "매도" | "강력매도"
    """
    if upside > 0.30:
        return "강력매수"
    if upside > 0.10:
        return "매수"
    if upside > -0.10:
        return "중립"
    if upside > -0.30:
        return "매도"
    return "강력매도"


@dataclass
class AnalystReport:
    """종합 애널리스트 리포트."""

    stock_code: str = ""
    company_name: str = ""
    target_price: float = 0.0  # 가중평균 목표가
    current_price: float = 0.0
    upside: float = 0.0  # (target - current) / current
    opinion: str = ""  # "강력매수" | "매수" | "중립" | "매도" | "강력매도"
    methods: list[ValuationMethod] = field(default_factory=list)
    confidence: float = 0.0  # 종합 신뢰도 (0~1)
    reasoning: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = ""

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [f"[애널리스트 리포트 — {self.company_name or self.stock_code}]"]
        lines.append(f"  종합 목표가: {self.target_price:,.0f}원")
        lines.append(f"  현재가: {self.current_price:,.0f}원")
        lines.append(f"  업사이드: {self.upside:+.1%}")
        lines.append(f"  투자의견: {self.opinion}")
        lines.append(f"  신뢰도: {self.confidence:.0%}")
        lines.append("")
        lines.append("  [밸류에이션 방법론]")
        for m in self.methods:
            lines.append(f"    {m}")
        if self.reasoning:
            lines.append("")
            lines.append("  [판단 근거]")
            for r in self.reasoning:
                lines.append(f"    - {r}")
        if self.warnings:
            lines.append("")
            lines.append("  [주의사항]")
            for w in self.warnings:
                lines.append(f"    ⚠ {w}")
        lines.append(f"\n  {self.DISCLAIMER}")
        return "\n".join(lines)
