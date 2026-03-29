"""잔여이익모델(RIM) 엔진 -- BPS + 초과이익 현가 = 내재가치.

공식:
  RI_t = NI_t - (Equity_{t-1} * CoE)
  Intrinsic = BPS + sum(RI_t / (1+CoE)^t) + TV

CoE 추정: CAPM proxy (무위험이자율 + 프리미엄) 또는 배당수익률 기반.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from dartlab.core.finance.extract import getAnnualValues, getLatest


@dataclass
class RIMResult:
    """잔여이익모델 결과."""

    bps: float
    coe: float  # Cost of Equity (%)
    riHistory: list[dict]  # [{period, ni, equity, ri}, ...]
    intrinsicValue: Optional[float]  # 주당 내재가치
    upside: Optional[float]  # 현재가 대비 (%)
    terminalValue: Optional[float]
    warnings: list[str] = field(default_factory=list)
    currency: str = "KRW"

    DISCLAIMER: str = "본 분석은 투자 참고용이며 투자 권유가 아닙니다."

    def __repr__(self) -> str:
        lines = ["[RIM 밸류에이션]"]
        lines.append(f"  BPS: {self.bps:,.0f}")
        lines.append(f"  자기자본비용(CoE): {self.coe:.1f}%")
        if self.intrinsicValue is not None:
            lines.append(f"  주당 내재가치: {self.intrinsicValue:,.0f}")
        if self.upside is not None:
            lines.append(f"  업사이드: {self.upside:+.1f}%")
        if self.warnings:
            for w in self.warnings:
                lines.append(f"  -- {w}")
        lines.append(f"  * {self.DISCLAIMER}")
        return "\n".join(lines)


def calcResidualIncome(
    series: dict,
    shares: Optional[int] = None,
    currentPrice: Optional[float] = None,
    coe: Optional[float] = None,
    currency: str = "KRW",
    beta: Optional[float] = None,
) -> RIMResult | None:
    """잔여이익모델 -- 자기자본 대비 초과이익의 현재가치.

    Args:
        series: 시계열 dict (finance.timeseries).
        shares: 발행주식수.
        currentPrice: 현재 주가.
        coe: 자기자본비용 (%). None이면 자동 추정.
        currency: 통화.

    Returns:
        RIMResult 또는 데이터 부족 시 None.
    """
    warnings: list[str] = []

    # 연간 순이익
    niVals = getAnnualValues(series, "IS", "net_profit")
    if not niVals:
        niVals = getAnnualValues(series, "IS", "net_income")
    if not niVals or len(niVals) < 2:
        return None

    # 연간 자기자본
    eqVals = getAnnualValues(series, "BS", "total_stockholders_equity")
    if not eqVals:
        eqVals = getAnnualValues(series, "BS", "owners_of_parent_equity")
    if not eqVals or len(eqVals) < 2:
        return None

    # CoE 추정
    if coe is None:
        coe = _estimateCoe(series, warnings, currency=currency, beta=beta)

    coeDecimal = coe / 100

    # 최근 BPS
    latestEquity = getLatest(series, "BS", "total_stockholders_equity")
    if latestEquity is None:
        latestEquity = getLatest(series, "BS", "owners_of_parent_equity")
    if latestEquity is None or latestEquity <= 0:
        return None

    bps = latestEquity / shares if shares and shares > 0 else 0

    # RI 시계열 (최소 2년 필요: equity_{t-1} 사용)
    n = min(len(niVals), len(eqVals))
    riHistory: list[dict] = []
    riValues: list[float] = []

    for i in range(1, n):
        ni = niVals[i]
        prevEq = eqVals[i - 1]
        if ni is None or prevEq is None or prevEq <= 0:
            continue
        ri = ni - prevEq * coeDecimal
        riHistory.append(
            {
                "index": i,
                "ni": ni,
                "equity": prevEq,
                "ri": ri,
            }
        )
        riValues.append(ri)

    if len(riValues) < 1:
        warnings.append("잔여이익 계산 불가 (데이터 부족)")
        return RIMResult(
            bps=bps,
            coe=coe,
            riHistory=riHistory,
            intrinsicValue=None,
            upside=None,
            terminalValue=None,
            warnings=warnings,
            currency=currency,
        )

    # 평균 RI -> 영구가치 추정
    avgRi = sum(riValues) / len(riValues)

    # fade factor(omega) 동적 추정 -- ROE-CoE spread 지속성
    omega = _estimateOmega(niVals, eqVals, coeDecimal, warnings)

    # Terminal Value: RI_T * omega / (1 + CoE - omega)  (CFA 표준)
    denominator = 1 + coeDecimal - omega
    if denominator > 0 and coeDecimal > 0:
        lastRi = riValues[-1]
        tv = lastRi * omega / denominator
    else:
        tv = 0

    # PV of RI history
    pvRi = 0.0
    for idx, ri in enumerate(riValues, 1):
        pvRi += ri / (1 + coeDecimal) ** idx

    # PV of TV
    pvTv = tv / (1 + coeDecimal) ** len(riValues) if len(riValues) > 0 else 0

    # 내재 자기자본 = 현재 자기자본 + PV(RI) + PV(TV)
    intrinsicEquity = latestEquity + pvRi + pvTv

    intrinsicPerShare = None
    upside = None
    if shares and shares > 0:
        intrinsicPerShare = round(intrinsicEquity / shares, 0)
        if currentPrice and currentPrice > 0:
            upside = round((intrinsicPerShare - currentPrice) / currentPrice * 100, 1)

    if len(riValues) < 3:
        warnings.append("RI 데이터 3년 미만 -- 결과 신뢰도 낮음")

    return RIMResult(
        bps=round(bps, 0),
        coe=coe,
        riHistory=riHistory,
        intrinsicValue=intrinsicPerShare,
        upside=upside,
        terminalValue=round(tv, 0) if tv else None,
        warnings=warnings,
        currency=currency,
    )


def _estimateOmega(
    niVals: list,
    eqVals: list,
    coeDecimal: float,
    warnings: list[str],
) -> float:
    """초과이익 지속성(omega) 동적 추정.

    ROE-CoE spread가 안정적이면 omega 높음 (경쟁우위 지속),
    급감 추세면 omega 낮음 (평균 회귀).
    범위: 0.2 ~ 0.8
    """
    n = min(len(niVals), len(eqVals))
    if n < 3:
        return 0.5  # 데이터 부족 시 기본값

    # ROE spread = ROE - CoE (각 연도)
    spreads: list[float] = []
    for i in range(n):
        ni = niVals[i]
        eq = eqVals[i]
        if ni is not None and eq is not None and eq > 0:
            roe = ni / eq
            spreads.append(roe - coeDecimal)

    if len(spreads) < 2:
        return 0.5

    # spread의 자기상관(AR1)으로 persistence 추정
    # AR1 계수 = Cov(x_t, x_{t-1}) / Var(x_{t-1})
    mean = sum(spreads) / len(spreads)
    demeaned = [s - mean for s in spreads]

    cov01 = sum(demeaned[i] * demeaned[i - 1] for i in range(1, len(demeaned)))
    var0 = sum(d * d for d in demeaned[:-1])

    if var0 > 0:
        ar1 = cov01 / var0
    else:
        ar1 = 0.5

    # AR1을 omega 범위로 매핑 (0.2 ~ 0.8)
    omega = max(0.2, min(ar1, 0.8))

    # spread가 전부 음수면 (CoE > ROE) → 초과이익 없음, omega 낮춤
    if all(s < 0 for s in spreads):
        omega = min(omega, 0.3)
        warnings.append("ROE < CoE -- 초과이익 없음, omega 하향")

    return round(omega, 2)


def _estimateCoe(
    series: dict,
    warnings: list[str],
    currency: str = "KRW",
    beta: float | None = None,
) -> float:
    """자기자본비용 추정 -- CAPM (MarketParams 기반).

    CoE = Rf + beta * (ERP + CRP)
    beta 미지정 시 1.0 기본, ROE 기반 가감.
    """
    from dartlab.core.sector.types import getMarketParams

    mkt = getMarketParams(currency)
    b = beta if beta is not None else 1.0
    baseCoe = mkt.ke(b)

    # ROE 기반 미세조정 (beta 미지정 시에만)
    if beta is None:
        niVals = getAnnualValues(series, "IS", "net_profit")
        eqVals = getAnnualValues(series, "BS", "total_stockholders_equity")
        if niVals and eqVals and len(niVals) >= 2 and len(eqVals) >= 2:
            recentNi = niVals[-1]
            recentEq = eqVals[-1]
            if recentNi is not None and recentEq and recentEq > 0:
                roe = recentNi / recentEq * 100
                if roe < 5:
                    baseCoe = min(baseCoe + 2.0, 15.0)
                    warnings.append("ROE 낮음 -- CoE 상향 조정")
                elif roe > 20:
                    baseCoe = max(baseCoe - 1.0, 7.0)

    return baseCoe
