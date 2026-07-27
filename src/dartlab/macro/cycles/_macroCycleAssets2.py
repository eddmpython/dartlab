"""macroCycle 자산 해석 — FX/시장평가/실질금리 (assets2).

_macroCycleAssets.py 680 줄 분할. interpretFxDrivers (124) + marketLevelValuation
(104) + realRateRegime (113) 약 344 줄. _macroCycleAssets.py 의 facade (gold ·
VIX · copperGold) 책임 유지.

BC: macroCycle 모듈에서 3 함수 모두 import 가능 (re-export 체인).
"""

from __future__ import annotations

import math

from dartlab.macro.cycles._macroCycleStats import _normCdf
from dartlab.macro.cycles._macroCycleTypes import (
    FxDrivers,
    MarketValuation,
    RealRateRegimeResult,
)


def interpretFxDrivers(
    fxChangePct: float,
    rateDiffChange: float | None = None,
    tradeBalanceYoy: float | None = None,
    vix: float | None = None,
) -> FxDrivers:
    """USDKRW 환율 변동 3 요인 분해 — 한미 금리차 + 무역수지 + 위험선호.

    Capabilities:
        Mundell-Fleming 모델 + Carry trade 이론 → 환율 변동의 3 학술 드라이버
        분해: (1) 한미 금리차 (확대 = 자본유출 = 원화약세), (2) 무역수지
        (흑자 확대 = 달러유입 = 원화강세), (3) VIX (상승 = EM 위험회피 =
        원화약세). 각 요인 정량 평가 + 다수결 dominant.

    Args:
        fxChangePct: USDKRW 변화율 (%, 양수=원화약세).
        rateDiffChange: 한미 금리차 변화 (%p, 양수=미국 금리 상대 상승).
        tradeBalanceYoy: 무역수지 YoY 변화 (%, 양수=흑자 확대).
        vix: VIX 수준.

    Returns:
        FxDrivers dataclass:
            - ``fxChangePct`` (float): 입력 echo
            - ``rateDiffEffect``/``tradeEffect``/``vixEffect`` (str): 각 효과
            - ``dominant`` (str): 지배 요인
            - ``description`` (str): 한국어 해석

    Raises:
        없음.

    Example:
        >>> r = interpretFxDrivers(fxChangePct=2.5, rateDiffChange=0.3,
        ...                        tradeBalanceYoy=-15, vix=22)
        >>> r.dominant
        '금리차'  # 미국 금리 우위 → 자본유출 압력

    Guide:
        rateDiffChange > 0.2 = 미국 금리 상대 우위 → 원화약세. tradeBalanceYoy
        < -10% = 무역흑자 축소 → 원화약세. VIX > 25 = EM 위험회피. 3 요인
        합산해 다수 일치 시 dominant.

    SeeAlso:
        - ``interpretGoldDrivers``: 금 3 요인 (달러와 cross-check)
        - ``rateOutlook``: 금리 방향 전망

    When:
        ``macro("cycle", "fx")``. AI 답변 USDKRW 변동 원인 분해 시.

    How:
        3 요인 임계 분기 → 원화강세/약세/중립 → fxChangePct 방향과 일치 요인 → dominant.

    Requires:
        없음 — 4 입력 모두 옵션. fxChangePct 만 필수.

    AIContext:
        dominant + 3 효과 함께 인용. fxChangePct 절대값 큰 (>5%) 변동은 단일
        요인이 아닌 복합 충격 — "기타" dominant 표시. KR 회사 분석 시 환율
        영향 (수출 비중) 함께 노출.

    LLM Specifications:
        AntiPatterns:
            - 금리차만 보고 환율 단정 — 무역수지 (KR 핵심) + VIX 함께.
            - fxChangePct 절대값 인용 — 추세 (3 개월 평균) 권장.
        OutputSchema:
            FxDrivers ``{fxChangePct, rateDiffEffect, tradeEffect, vixEffect,
            dominant, description}``.
        Prerequisites:
            USDKRW 변화율 (필수) + 3 보조 지표 (옵션).
        Freshness:
            환율 일, 무역수지 월, VIX 일, 금리차 일.
        Dataflow:
            3 요인 룰 → 원화강세/약세/중립 → 다수결 dominant → 한국어 합성.
        TargetMarkets: KR (USDKRW). 다른 EM 통화도 응용 가능.
    """
    # 1) 금리차 요인
    if rateDiffChange is not None and rateDiffChange > 0.2:
        rd_effect = "원화약세"
    elif rateDiffChange is not None and rateDiffChange < -0.2:
        rd_effect = "원화강세"
    else:
        rd_effect = "중립"

    # 2) 무역수지 요인
    if tradeBalanceYoy is not None and tradeBalanceYoy > 10:
        trade_effect = "원화강세"
    elif tradeBalanceYoy is not None and tradeBalanceYoy < -10:
        trade_effect = "원화약세"
    else:
        trade_effect = "중립"

    # 3) 위험선호도 요인 (VIX 기반)
    if vix is not None and vix > 25:
        risk_effect = "원화약세"
    elif vix is not None and vix < 15:
        risk_effect = "원화강세"
    else:
        risk_effect = "중립"

    # 지배적 요인 판별
    effects = {"금리차": rd_effect, "무역수지": trade_effect, "위험선호도": risk_effect}
    # fx_change_pct가 양수(약세)인데 어느 요인이 약세 방향인지
    fx_direction = "원화약세" if fxChangePct > 0 else "원화강세"
    matching = [name for name, eff in effects.items() if eff == fx_direction and eff != "중립"]
    if matching:
        dominant = matching[0]  # 일치하는 첫 요인
    elif any(v != "중립" for v in effects.values()):
        dominant = next(name for name, eff in effects.items() if eff != "중립")
    else:
        dominant = "미확인"

    # 금리차-환율 방향 불일치 감지
    divergence = None
    if rateDiffChange is not None and abs(fxChangePct) > 2:
        rd_implied = "원화약세" if rateDiffChange > 0.2 else ("원화강세" if rateDiffChange < -0.2 else "중립")
        if rd_implied != "중립" and rd_implied != fx_direction:
            divergence = f"금리차는 {rd_implied} 방향이나 환율은 {fx_direction} → 비금리 요인(무역수지, 자본유입) 지배"

    return FxDrivers(
        rateDiffEffect=rd_effect,
        tradeEffect=trade_effect,
        riskEffect=risk_effect,
        dominant=dominant,
        divergence=divergence,
    )


# ══════════════════════════════════════
# 시장 레벨 밸류에이션 (Buffett Indicator)
# ══════════════════════════════════════


def marketLevelValuation(
    totalMarketCap: float,
    gdp: float,
) -> MarketValuation:
    """Buffett Indicator (시총/GDP) → 시장 전체 밸류에이션 5 구간 분류.

    Capabilities:
        Warren Buffett 의 "가장 좋은 단일 시장 척도" — Wilshire 5000 시총
        (WILL5000PRFC) / 명목 GDP. 역사적 범위 (1970~2024) 의 5 구간으로
        분류하여 현 시점 시장 전체 밸류에이션 판정.

    Args:
        totalMarketCap: 전체 시가총액 (Billions $). FRED WILL5000PRFC.
        gdp: 명목 GDP (Billions $). FRED GDP.

    Returns:
        MarketValuation dataclass:
            - ``buffettIndicator`` (float): 시총/GDP 비율 (%)
            - ``zone`` (str): ``"undervalued"``/``"fair"``/``"overvalued"``/
              ``"extreme"``
            - ``zoneLabel`` (str): 한국어
            - ``description`` (str): 한국어 해석

    Raises:
        없음. gdp ≤ 0 시 zero result.

    Example:
        >>> r = marketLevelValuation(totalMarketCap=55000, gdp=27000)
        >>> r.buffettIndicator, r.zone
        (203.7, 'extreme')

    Guide:
        역사적 5 구간 (미국 1970~2024):
        - < 70%: 극단 저평가 (2009 GFC 바닥, 2020 COVID 바닥)
        - 70~100%: 저평가 (장기 평균 1990s)
        - 100~140%: 적정 (현대 평균 2010s)
        - 140~180%: 고평가
        - > 180%: 극단 고평가 (1999 닷컴 정점 150%, 2021 175%)

        본 지표는 시장 전체 — 개별 종목 valuation 과 다름. 글로벌화 (해외
        매출 비중) 증가로 long-run 평균 자체가 상승 추세 (mean reversion 한계).

    SeeAlso:
        - ``classifyCycle``: 매크로 사이클 (밸류에이션과 함께 종합)
        - ``copperGoldRatio``: 위험선호 (다른 시장 척도)
        - Buffett, W. (2001) Fortune Magazine

    When:
        ``macro("cycle", "buffett")``. 시장 전체 valuation 답변 시.

    How:
        ratio = (시총/GDP) × 100 → 5 구간 (70/100/140/180) 분류.

    Requires:
        Wilshire 5000 시가총액 + 명목 GDP (FRED).

    AIContext:
        Buffett Indicator extreme 결과는 시장 전체 신호이지 개별 종목 매도
        신호 아님 — long-run mean reversion 시점 불확실 (1~5 년).
        한국 KOSPI 적용 시 KRX 전체 시총 / 한국 GDP 사용.

    LLM Specifications:
        AntiPatterns:
            - extreme 단계만 보고 "시장 폭락 임박" 단정 — Buffett 본인도
              "정확한 timing 도구 아님" 명시 (2001 Fortune).
            - 글로벌화 증가로 long-run 평균 자체 상승 — 1990 표준을 2024에
              그대로 적용 금지.
        OutputSchema:
            MarketValuation ``{buffettIndicator, zone, zoneLabel, description}``.
        Prerequisites:
            FRED WILL5000PRFC + GDP. 동일 통화 단위 (Billions $).
        Freshness:
            시총 일, GDP 분기 (Bureau of Economic Analysis Q1/Q2/Q3/Q4).
        Dataflow:
            (시총 / GDP) × 100 → 5 구간 임계 분류 → description.
        TargetMarkets: US (WILL5000PRFC + GDP). KR 도 KRX/KOSIS 적용 가능.
    """
    if gdp <= 0:
        return MarketValuation(0, "fair", "판별불가", "GDP 데이터 없음")

    ratio = (totalMarketCap / gdp) * 100

    if ratio < 70:
        zone, label = "deep_value", "극단저평가"
        desc = f"Buffett Indicator {ratio:.0f}% — 시장 극단 저평가 (역사적 바닥 수준)"
    elif ratio < 100:
        zone, label = "undervalued", "저평가"
        desc = f"Buffett Indicator {ratio:.0f}% — 시장 저평가 (장기 평균 하회)"
    elif ratio < 140:
        zone, label = "fair", "적정"
        desc = f"Buffett Indicator {ratio:.0f}% — 시장 적정 수준"
    elif ratio < 180:
        zone, label = "overvalued", "고평가"
        desc = f"Buffett Indicator {ratio:.0f}% — 시장 고평가 (조정 위험 상승)"
    else:
        zone, label = "extreme", "극단고평가"
        desc = f"Buffett Indicator {ratio:.0f}% — 시장 극단 고평가 (버블 경고)"

    return MarketValuation(
        buffettIndicator=round(ratio, 1),
        zone=zone,
        zoneLabel=label,
        description=desc,
    )


# ══════════════════════════════════════
# BEI / Real Rate 분해
# ══════════════════════════════════════


def realRateRegime(realRate: float, bei: float) -> RealRateRegimeResult:
    """실질금리 (DFII10) + BEI (10Y break-even) → 금융 환경 4 레짐 분류.

    Capabilities:
        실질금리와 BEI 의 (수준 + 조합) 으로 금융 환경 4 레짐 (긴축/디플레위험/
        리플레이션/골디락스) 분류. macro/cycles/cycle 의 보조 진단으로 사용.

    Args:
        realRate: 10년 실질금리 (DFII10, %).
        bei: 10년 break-even inflation (%).

    Returns:
        RealRateRegimeResult dataclass:
            - ``realRate``/``bei`` (float): 입력 echo
            - ``regime`` (str): ``"tight"``/``"deflation"``/``"reflation"``/
              ``"goldilocks"``
            - ``regimeLabel`` (str): 한국어
            - ``description`` (str): 한국어 해석

    Raises:
        없음.

    Example:
        >>> r = realRateRegime(realRate=2.3, bei=1.8)
        >>> r.regime
        'deflation'

    Guide:
        4 레짐 매트릭스 (수준 기반):
        - 실질 > 2 + BEI < 2 → deflation 위험
        - 실질 > 1.5 + BEI > 2.5 → tight (긴축)
        - 실질 < 0 + BEI > 2.5 → reflation
        - 실질 < 0.5 + BEI ~ 2 → goldilocks

        방향 판별 (전기 대비) 은 호출자 책임 — 본 함수는 수준 분류만.

    SeeAlso:
        - ``classifyCycle``: 사이클 4 국면 (regime 과 결합)
        - ``interpretGoldDrivers``: realRateChange 사용
        - ``rateOutlook``: 금리 방향 전망 (Fed funds 기반)

    Requires:
        실질금리 + BEI 둘 다 필요 (옵션 아님).

    AIContext:
        regime + description 함께 인용. tight regime 시 자산 클래스
        선택 변경 권장 — 채권 우위. goldilocks 는 주식 우위.

    LLM Specifications:
        AntiPatterns:
            - realRate 단독으로 regime 판정 — BEI 동반 분석 필수.
            - 본 함수의 regime 라벨을 미국 Fed funds 와 혼동 (본 함수는 10Y
              실질, Fed funds 는 단기).
        OutputSchema:
            RealRateRegimeResult ``{realRate, bei, regime, regimeLabel,
            description}``.
        Prerequisites:
            FRED DFII10 + T10YIE (10Y BEI).
        Freshness:
            DFII10 일, T10YIE 일.
        Dataflow:
            (realRate, bei) → 4 레짐 임계 분류 → description 합성.
        TargetMarkets: US (FRED DFII10 표준). KR 미적용 (KR BEI 부재).
    """
    if realRate > 2.0 and bei < 2.0:
        return RealRateRegimeResult(
            round(realRate, 2),
            round(bei, 2),
            "deflation",
            "디플레위험",
            f"실질금리 {realRate:.2f}% 높음 + BEI {bei:.2f}% 낮음 — 디플레이션 위험",
        )
    elif realRate > 1.5 and bei > 2.5:
        return RealRateRegimeResult(
            round(realRate, 2),
            round(bei, 2),
            "tightening",
            "긴축",
            f"실질금리 {realRate:.2f}% + BEI {bei:.2f}% 동반 상승 — 금융 긴축",
        )
    elif realRate < 0.5 and bei > 2.5:
        return RealRateRegimeResult(
            round(realRate, 2),
            round(bei, 2),
            "reflation",
            "리플레이션",
            f"실질금리 {realRate:.2f}% 낮음 + BEI {bei:.2f}% 높음 — 리플레이션",
        )
    elif realRate < 1.0 and bei < 2.0:
        return RealRateRegimeResult(
            round(realRate, 2),
            round(bei, 2),
            "goldilocks",
            "골디락스",
            f"실질금리 {realRate:.2f}% + BEI {bei:.2f}% 모두 안정 — 골디락스",
        )
    else:
        return RealRateRegimeResult(
            round(realRate, 2),
            round(bei, 2),
            "neutral",
            "중립",
            f"실질금리 {realRate:.2f}%, BEI {bei:.2f}% — 뚜렷한 방향 없음",
        )


__all__ = [
    "interpretFxDrivers",
    "marketLevelValuation",
    "realRateRegime",
]
