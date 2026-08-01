"""analysis/valuation/dcf 결과 타입 — 5 dataclass.

analysis/valuation/dcf.py 가 1170 줄 god module 이라 types 분리.
identity 보존을 위해 dcf.py 가 본 모듈에서 re-export 한다.

타입:
- DCFResult — DCF 밸류에이션 결과
- DDMResult — DDM 밸류에이션 결과
- RelativeValuationResult — 상대가치 밸류에이션 결과
- ValuationSummary — 종합 밸류에이션
- SensitivityResult — 민감도 그리드
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.core.utils.fmt import fmtBig, fmtPrice


@dataclass
class DCFResult:
    """DCF 밸류에이션 결과."""

    fcfHistorical: list[Optional[float]]
    fcfProjections: list[float]
    terminalValue: Optional[float]
    enterpriseValue: Optional[float]
    equityValue: Optional[float]
    perShareValue: Optional[float]
    discountRate: float
    growthRateInitial: float
    terminalGrowth: float
    marginOfSafety: Optional[float]
    exitMultipleTv: Optional[float] = None
    exitMultipleEv: Optional[float] = None
    exitMultiplePerShare: Optional[float] = None
    assumptions: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"
    status: str = "usable"
    blockedReason: str | None = None

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = [
            "[DCF 밸류에이션]",
            f"  할인율: {self.discountRate:.1f}%",
            f"  초기 성장률: {self.growthRateInitial:.1f}%",
            f"  영구 성장률: {self.terminalGrowth:.1f}%",
        ]
        if self.enterpriseValue is not None:
            lines.append(f"  기업가치: {fmtBig(self.enterpriseValue, c)}")
        else:
            lines.append("  기업가치: 미산출")
        if self.equityValue is not None:
            lines.append(f"  주주가치: {fmtBig(self.equityValue, c)}")
        if self.perShareValue is not None:
            lines.append(f"  주당 내재가치: {fmtPrice(self.perShareValue, c)}")
        if self.marginOfSafety is not None:
            lines.append(f"  안전마진: {self.marginOfSafety:.1f}%")
        if self.exitMultiplePerShare is not None:
            lines.append(f"  [교차검증] Exit Multiple 주당가치: {fmtPrice(self.exitMultiplePerShare, c)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        if self.blockedReason and self.blockedReason not in self.warnings:
            lines.append(f"  ⚠ {self.blockedReason}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class DDMResult:
    """DDM 밸류에이션 결과."""

    intrinsicValue: Optional[float]
    dividendPerShare: Optional[float]
    dividendYield: Optional[float]
    payoutRatio: Optional[float]
    dividendGrowth: Optional[float]
    modelUsed: str
    discountRate: float
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        if self.modelUsed == "N/A":
            return "[DDM 밸류에이션]\n  적용 불가 (무배당 또는 데이터 부족)"
        c = self.currency
        lines = [
            f"[DDM 밸류에이션 — {self.modelUsed}]",
            f"  할인율: {self.discountRate:.1f}%",
        ]
        if self.dividendPerShare is not None:
            lines.append(f"  주당배당금: {fmtPrice(self.dividendPerShare, c)}")
        if self.dividendGrowth is not None:
            lines.append(f"  배당성장률: {self.dividendGrowth:.1f}%")
        if self.intrinsicValue is not None:
            lines.append(f"  주당 내재가치: {fmtPrice(self.intrinsicValue, c)}")
        if self.payoutRatio is not None:
            lines.append(f"  배당성향: {self.payoutRatio:.1f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class RelativeValuationResult:
    """상대가치 밸류에이션 결과."""

    sectorMultiples: dict[str, float]
    currentMultiples: dict[str, Optional[float]]
    impliedValues: dict[str, Optional[float]]
    premiumDiscount: dict[str, Optional[float]]
    consensusValue: Optional[float]
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[상대가치 밸류에이션]"]
        lines.append("  지표       섹터배수   현재배수   적정가치      할증/할인")
        for key in ["PER", "PBR", "EV/EBITDA", "PSR", "PEG"]:
            sm = self.sectorMultiples.get(key)
            cm = self.currentMultiples.get(key)
            iv = self.impliedValues.get(key)
            pd = self.premiumDiscount.get(key)
            if sm is None and cm is None and iv is None:
                continue
            smS = f"{sm:.1f}" if sm is not None else "-"
            cmS = f"{cm:.1f}" if cm is not None else "-"
            ivS = fmtPrice(iv, self.currency) if iv is not None else "-"
            pdS = f"{pd:+.1f}%" if pd is not None else "-"
            lines.append(f"  {key:<10s} {smS:>8s}  {cmS:>8s}  {ivS:>10s}  {pdS:>10s}")
        if self.consensusValue is not None:
            lines.append(f"  종합 적정가치: {fmtPrice(self.consensusValue, self.currency)}")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  ⚠ {w}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class ValuationSummary:
    """종합 밸류에이션 결과."""

    dcf: Optional[DCFResult]
    ddm: Optional[DDMResult]
    relative: Optional[RelativeValuationResult]
    fairValueRange: Optional[tuple[float, float]]
    currentPrice: Optional[float]
    verdict: str
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        c = self.currency
        lines = ["[종합 밸류에이션]"]
        if self.fairValueRange:
            lo, hi = self.fairValueRange
            lines.append(f"  적정가치 범위: {fmtPrice(lo, c)} ~ {fmtPrice(hi, c)}")
        if self.currentPrice is not None:
            lines.append(f"  현재가: {fmtPrice(self.currentPrice, c)}")
        lines.append(f"  판단: {self.verdict}")
        lines.append(f"  ※ {self.DISCLAIMER}")
        return "\n".join(lines)


@dataclass
class SensitivityResult:
    """DCF 민감도 분석 결과."""

    grid: list[dict]
    baseWacc: float
    baseTerminalGrowth: float
    baseValue: Optional[float]


__all__ = [
    "DCFResult",
    "DDMResult",
    "RelativeValuationResult",
    "SensitivityResult",
    "ValuationSummary",
]
