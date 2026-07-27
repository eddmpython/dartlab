"""Analyst 엔진 데이터 타입 — 종합 분석 결과."""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.core.utils.fmt import fmtPrice


@dataclass
class ValuationMethod:
    """개별 밸류에이션 방법론 결과."""

    name: str = ""  # "dcf", "consensus", "peer_multiple", "relative"
    value: float = 0.0  # 산출 목표가
    weight: float = 0.0  # 가중치 (0~1)
    confidence: float = 0.0  # 신뢰도 (0~1)
    reasoning: str = ""  # 산출 근거
    currency: str = "KRW"

    def __repr__(self) -> str:
        return f"{self.name}: {fmtPrice(self.value, self.currency)} (가중치={self.weight:.0%}, 신뢰도={self.confidence:.0%})"


# 투자 의견 매핑
_OPINION_MAP = {
    "strong_buy": "강력매수",
    "buy": "매수",
    "hold": "중립",
    "sell": "매도",
    "strong_sell": "강력매도",
}


def _classifyOpinion(upside: float) -> str:
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

    stockCode: str = ""
    companyName: str = ""
    target_price: float = 0.0  # 가중평균 목표가
    currentPrice: float = 0.0
    upside: float = 0.0  # (target - current) / current
    opinion: str = ""  # "강력매수" | "매수" | "중립" | "매도" | "강력매도"
    methods: list[ValuationMethod] = field(default_factory=list)
    confidence: float = 0.0  # 종합 신뢰도 (0~1)
    reasoning: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generated_at: str = ""
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = [f"[애널리스트 리포트 — {self.companyName or self.stockCode}]"]
        lines.append(f"  종합 목표가: {fmtPrice(self.target_price, self.currency)}")
        lines.append(f"  현재가: {fmtPrice(self.currentPrice, self.currency)}")
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


# 상승여력 구간을 투자의견 라벨로 바꾸는 기준. 세 곳(bankDFV, sotp, _dFVCalcs)이 이 표를
# 글자까지 똑같이 복사해 갖고 있었다. 사용자에게 그대로 보이는 판정이라 한 곳에서만 정한다.
# 셋 중 하나만 임계값을 옮기면 같은 회사가 화면마다 다른 의견을 받는다.
_OPINION_BREAKPOINTS: tuple[tuple[float, str], ...] = (
    (30.0, "강력매수"),
    (10.0, "매수"),
    (-10.0, "보유"),
    (-30.0, "매도"),
)


def opinionFromUpside(upside: float | None) -> str:
    """상승여력을 투자의견 라벨로 바꾼다.

    Args:
        upside: 적정가 대비 상승여력 (%). ``None`` 이면 판단하지 않는다.

    Returns:
        ``"강력매수"`` · ``"매수"`` · ``"보유"`` · ``"매도"`` · ``"강력매도"`` ·
        ``"판단 불가"`` 중 하나.

    Raises:
        없음.

    Example:
        ``opinionFromUpside(35.0)`` 은 ``"강력매수"``.
    """
    if upside is None:
        return "판단 불가"
    for cutoff, label in _OPINION_BREAKPOINTS:
        if upside > cutoff:
            return label
    return "강력매도"
