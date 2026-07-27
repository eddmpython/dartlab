"""macroCycle 자산 해석 + VIX/Cu/Au/FX/시장평가/실질금리 6 함수.

macro/cycles/macroCycle.py 가 992 줄 god module 이라 자산 해석 도메인 분리.
identity 보존을 위해 macroCycle.py 가 본 모듈에서 re-export 한다.

함수:
- interpretGoldDrivers — 금 3 요인 (달러/실질금리/안전수요)
- classifyVixRegime — VIX 레짐 (calm/normal/elevated/panic)
- copperGoldRatio — 구리/금 비율 → 위험선호
- interpretFxDrivers — 환율 드라이버 (성장/금리/심리)
- marketLevelValuation — Buffett/CAPE/EY-BY 종합 평가
- realRateRegime — 실질금리 4 레짐
"""

from __future__ import annotations

import math

from dartlab.macro.cycles._macroCycleStats import _normCdf
from dartlab.macro.cycles._macroCycleTypes import (
    CopperGoldSignal,
    FxDrivers,
    GoldDrivers,
    MarketValuation,
    RealRateRegimeResult,
    VixRegime,
)

# ══════════════════════════════════════


def interpretGoldDrivers(
    goldYoy: float,
    realRateChange: float,
    dxyChangePct: float,
    vix: float,
) -> GoldDrivers:
    """금 가격 3 요인 분해 — 실질금리 + 달러 + 안전수요 (VIX).

    Capabilities:
        금 가격 변동의 3 가지 학술적 드라이버 분해: (1) 실질금리 (역상관 -
        DFII10), (2) 달러 강세 (역상관 - DXY), (3) 안전수요 (정상관 - VIX).
        각 효과를 정량 추정 + 잔차로 "기타 (geopolitical/central bank)" 추적.

    Args:
        goldYoy: 금 YoY 변화율 (%).
        realRateChange: 실질금리 (DFII10) 변화 (%p, 양수=상승).
        dxyChangePct: 달러 인덱스 변화율 (%, 양수=달러강세).
        vix: VIX 수준 (panic 시 안전수요 증가).

    Returns:
        GoldDrivers dataclass:
            - ``goldYoy`` (float): 입력 echo
            - ``realRateEffect``/``dollarEffect``/``safeHavenEffect`` (str):
              ``"상승압력"``/``"하락압력"``/``"중립"``
            - ``dominant`` (str): 지배 요인 ("실질금리"/"달러"/"안전자산"/"기타")
            - ``description`` (str): 한국어 해석

    Raises:
        없음.

    Example:
        >>> r = interpretGoldDrivers(goldYoy=18, realRateChange=-0.8,
        ...                          dxyChangePct=-3, vix=22)
        >>> r.dominant, r.realRateEffect
        ('실질금리', '상승압력')

    Guide:
        실질금리 < -0.3%p (3 개월) → 금 상승압력 (carry cost 감소). 달러 < -2%
        (3 개월) → 금 상승 (USD 가격 inverse). VIX > 25 → 안전수요 활성.
        3 요인 합산해 다수결로 dominant 선정. 모두 중립이면 "기타".

    SeeAlso:
        - ``classifyVixRegime``: VIX 4 단계
        - ``copperGoldRatio``: 구리/금 비율 (위험선호)
        - ``classifyCycle``: 사이클 종합

    When:
        ``macro("cycle", "gold")``. 금 가격 변동 원인 분해 답변 시.

    How:
        3 요인 각각 임계 분기 → 상승/하락/중립 라벨 → 다수결로 dominant.

    Requires:
        4 입력 모두 필요 (옵션 아님).

    AIContext:
        dominant + 3 효과 모두 인용 (단일 요인만 인용 금지). 학술적 회귀
        실험에서 실질금리 -0.6, 달러 -0.4, VIX +0.2 비중. KR 입력 시 BOK
        실질금리 + WSJ 달러 인덱스 사용.

    LLM Specifications:
        AntiPatterns:
            - VIX 만 보고 금 전망 단정 — 실질금리 + 달러 함께 확인.
            - YoY 1 개월 변화로 추세 단정 — 본 함수는 단일 시점 분해 (1 분기
              3 개월 변화 기준).
        OutputSchema:
            GoldDrivers ``{goldYoy, realRateEffect, dollarEffect,
            safeHavenEffect, dominant, description}``.
        Prerequisites:
            금 가격 + 실질금리 (DFII10) + DXY + VIX 시계열.
        Freshness:
            금 가격 일, 실질금리 일, DXY 일, VIX 일.
        Dataflow:
            3 요인 룰 → 상승/하락/중립 라벨 → 다수결 dominant → 한국어 합성.
        TargetMarkets: Global (FRED + Yahoo Finance + DFII10).
    """
    # 실질금리 역상관: 실질금리 하락 → 금 상승압력
    if realRateChange < -0.3:
        rr = "상승압력"
    elif realRateChange > 0.3:
        rr = "하락압력"
    else:
        rr = "중립"

    # 달러 역상관: 달러 약세 → 금 상승압력
    if dxyChangePct < -2:
        dx = "상승압력"
    elif dxyChangePct > 2:
        dx = "하락압력"
    else:
        dx = "중립"

    # 안전자산 수요: VIX 급등 → 금 상승
    sh = "상승압력" if vix > 25 else "중립"

    # 지배적 요인 판별
    effects = {"실질금리": rr, "달러": dx, "안전자산": sh}
    up_count = sum(1 for v in effects.values() if v == "상승압력")
    down_count = sum(1 for v in effects.values() if v == "하락압력")

    if up_count > down_count:
        dominant = next(k for k, v in effects.items() if v == "상승압력")
    elif down_count > up_count:
        dominant = next(k for k, v in effects.items() if v == "하락압력")
    else:
        dominant = "복합"

    return GoldDrivers(
        realRateEffect=rr,
        dollarEffect=dx,
        safeHavenEffect=sh,
        dominant=dominant,
    )


# ══════════════════════════════════════
# VIX 구간 판정
# ══════════════════════════════════════


def classifyVixRegime(vix: float) -> VixRegime:
    """VIX (CBOE 변동성지수) → 6 구간 공포 레짐 + 분할매수 신호 강도.

    Capabilities:
        VIX 수준을 역사적 6 구간 (panic/extreme_fear/fear/anxious/normal/
        complacent) 으로 분류하고 분할매수 신호 강도 (0~3) 산출. 역사적
        contrarian 신호 — VIX > 30 진입 시 1~3 개월 후 +10~20% 수익률 관찰.

    Args:
        vix: CBOE VIX 수준 (보통 10~80 범위).

    Returns:
        VixRegime dataclass:
            - ``vix`` (float)
            - ``regime`` (str): 6 구간 enum
            - ``regimeLabel`` (str): 한국어
            - ``dcaSignal`` (int): 분할매수 강도 (0~3)

    Raises:
        없음.

    Example:
        >>> r = classifyVixRegime(vix=35)
        >>> r.regime, r.dcaSignal
        ('extreme_fear', 2)

    Guide:
        역사적 6 구간:
        - >= 40: panic (2008 80, 2020 82 정점) — DCA 신호 3 (max)
        - >= 30: extreme_fear (시장 패닉) — DCA 신호 2
        - >= 25: fear — DCA 신호 1
        - >= 20: anxious (정상 ~ 경계)
        - >= 15: normal (역사 평균 ~19)
        - < 15: complacent (2017 8~10 정점 직전)

        역사적 contrarian: VIX > 30 진입 시 S&P 500 1~3 개월 후 +10~20%
        (1990~2024). 단, panic > 40 진입 후 추가 하락 가능 (2008 GFC 6 개월).

    SeeAlso:
        - ``interpretGoldDrivers``: VIX 안전수요 효과
        - ``classifyCycle``: 사이클 종합 (VIX 입력)
        - ``copperGoldRatio``: 위험선호 (반대 척도)

    When:
        ``macro("cycle", "vix")``. AI 답변 시장 공포 단계 / DCA 신호 시.

    How:
        VIX 임계 6 단계 (40/30/25/20/15/<15) 매핑.

    Requires:
        VIX 일별 (FRED VIXCLS 또는 CBOE).

    AIContext:
        dcaSignal 은 정성적 권고 — 정확한 매수 시점 신호 아님. 사용자에게
        regime + 역사 평균 ("19 vs 현재 22") 함께 노출 권장.

    LLM Specifications:
        AntiPatterns:
            - 단일 시점 VIX 만 보고 매수 신호 단정 — VIX는 mean-reverting,
              상승 추세 (vix_change) 확인 필요 (별도 호출).
            - panic 진입 즉시 매수 — 2008/2020 사례 모두 panic 진입 후
              1~3 개월 추가 하락. 분할매수 (DCA 3 회) 가 안전.
        OutputSchema:
            VixRegime ``{vix, regime, regimeLabel, dcaSignal}``.
        Prerequisites:
            VIX 일 시계열 (FRED).
        Freshness:
            VIX 일 (EOD).
        Dataflow:
            vix → 6 임계 비교 → regime + dcaSignal 매핑.
        TargetMarkets: US (S&P 500 변동성). KR 은 KOSPI 200 변동성 (V-KOSPI).
    """
    if vix >= 40:
        return VixRegime(vix, "panic", "패닉", 3)
    if vix >= 30:
        return VixRegime(vix, "extreme_fear", "극단공포", 2)
    if vix >= 25:
        return VixRegime(vix, "fear", "공포", 1)
    if vix >= 20:
        return VixRegime(vix, "anxious", "불안", 0)
    if vix >= 15:
        return VixRegime(vix, "normal", "정상", 0)
    return VixRegime(vix, "complacent", "낙관", 0)


# ══════════════════════════════════════
# Copper/Gold Ratio (경기 선행)
# ══════════════════════════════════════


def copperGoldRatio(
    copper: float,
    gold: float,
    prevCopper: float | None = None,
    prevGold: float | None = None,
) -> CopperGoldSignal:
    """Copper/Gold Ratio → 위험선호 + 경기 선행 (10Y 국채 수익률과 강한 상관).

    Capabilities:
        구리 (산업수요 = 위험자산) ÷ 금 (안전자산) 비율의 수준 + 변화로
        위험선호 / 안전선호 진단. 학술적 발견: Copper/Gold ratio 와 10Y
        Treasury yield 의 상관 0.75+ (Stanley Druckenmiller).

    Args:
        copper: 구리 가격 ($/ton 또는 ¢/lb).
        gold: 금 가격 ($/oz). 0 이하 시 빈 결과.
        prevCopper: 이전 구리 가격 (옵션). 변화율 계산.
        prevGold: 이전 금 가격 (옵션). 변화율 계산.

    Returns:
        CopperGoldSignal dataclass:
            - ``ratio`` (float): copper/gold
            - ``trend`` (str): ``"rising"``/``"falling"``/``"stable"``
            - ``trendLabel`` (str): 한국어
            - ``implication`` (str): ``"riskOn"``/``"riskOff"``/``"neutral"``
            - ``description`` (str): 한국어 해석

    Raises:
        없음.

    Example:
        >>> r = copperGoldRatio(copper=8500, gold=2000,
        ...                     prevCopper=8000, prevGold=2050)
        >>> r.trend, r.implication
        ('rising', 'riskOn')

    Guide:
        ratio 상승 (>3% 변화) = riskOn (경기 낙관, 채권 매도). ratio 하락
        (<-3%) = riskOff (안전선호, 채권 매수). 10Y Treasury 와 강한 상관
        — copper/gold 상승 시 10Y yield 동반 상승 예측.

    SeeAlso:
        - ``interpretGoldDrivers``: 금 가격 3 요인 분해
        - ``classifyVixRegime``: VIX 공포 (반대 척도)
        - ``classifyCycle``: 사이클 종합

    When:
        ``macro("cycle", "copperGold")``. 채권 yield 예측 / 위험선호 답변 시.

    How:
        ratio = copper / gold → prev 대비 변화율 ±3% 임계 → trend + implication.

    Requires:
        구리/금 가격 (Yahoo Finance HG=F + GC=F).

    AIContext:
        본 비율은 경기 선행 (6 개월) — 단기 (1 개월) 변동성 큼. 분기 평균
        사용 권장. KR 시장에는 직접 적용 어렵고 글로벌 위험선호 proxy.

    LLM Specifications:
        AntiPatterns:
            - ratio 절대값 인용 — 상대 변화율 (vs prev) 가 더 신뢰. 비율
              자체는 단위 일치 의존.
            - 일별 변화 (>3%) 로 trend 판정 — 본 함수는 분기 변화 권장.
        OutputSchema:
            CopperGoldSignal ``{ratio, trend, trendLabel, implication,
            description}``.
        Prerequisites:
            copper/gold 현재 가격 + 이전 가격 (변화율 계산).
        Freshness:
            구리/금 일 (FRED + Yahoo Finance).
        Dataflow:
            ratio = copper / gold → change vs prev → trend 임계 → implication.
        TargetMarkets: Global (FRED + Yahoo). KR 도 적용 가능 (글로벌 risk).
    """
    if gold <= 0:
        return CopperGoldSignal(0, "stable", "판별불가", "neutral", "금 가격 데이터 없음")

    ratio = copper / gold
    prev_ratio = (prevCopper / prevGold) if prevCopper and prevGold and prevGold > 0 else None

    if prev_ratio is not None:
        change_pct = ((ratio - prev_ratio) / prev_ratio) * 100
    else:
        change_pct = 0.0

    if change_pct > 3:
        return CopperGoldSignal(
            round(ratio, 4),
            "rising",
            "상승",
            "expansion",
            f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 산업수요 확대, 경기 낙관",
        )
    elif change_pct < -3:
        return CopperGoldSignal(
            round(ratio, 4),
            "falling",
            "하락",
            "contraction",
            f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 안전자산 선호, 경기 비관",
        )
    else:
        return CopperGoldSignal(
            round(ratio, 4), "stable", "안정", "neutral", f"Cu/Au {ratio:.4f} ({change_pct:+.1f}%) — 안정"
        )


# ══════════════════════════════════════
# 환율 3요인 분해
# ══════════════════════════════════════


# ── interpretFxDrivers + marketLevelValuation + realRateRegime → _macroCycleAssets2.py 분리 ──

from dartlab.macro.cycles._macroCycleAssets2 import (  # noqa: E402, F401
    interpretFxDrivers,
    marketLevelValuation,
    realRateRegime,
)
