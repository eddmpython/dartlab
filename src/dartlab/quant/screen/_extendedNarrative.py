"""quant/screen/extended 서사 + 전략 8 함수 분리.

quant/screen/extended.py 의 story 6막 서사 소비 함수들을 분리.
identity 보존을 위해 extended.py 가 본 모듈에서 re-export 한다.

함수 (analysis calc 패턴):
- calcTrendData — 추세 카테고리 + verdict
- calcRiskData — ATR + 베타 + 변동성
- calcSignalData — 최근 20일 매수/매도 신호
- calcStrategyData — 스타일별 Sharpe + 진입
- calcCrosscheckData — analysis 등급 vs 기술적 판단
- calcQuantConclusionData — 5축 방향 집계
- calcStrategySnapshot — 8 스타일 백테스트 + 진입 진단
- calcActionableTargets — 진입/청산 가격 목표
"""

from __future__ import annotations

import numpy as np

from dartlab.core.memory import memoizedCalc as _memoized_calc
from dartlab.core.polarsUtil import isEmptyDf
from dartlab.quant.screen._extendedCache import _fetchOhlcv


def _calls():
    """Lazy import — 순환 회피."""
    from dartlab.quant.screen.extended import (
        calcFundamentalDivergence,
        calcMarketRisk,
        calcTechnicalSignals,
        calcTechnicalVerdict,
    )

    return calcTechnicalVerdict, calcTechnicalSignals, calcMarketRisk, calcFundamentalDivergence


@_memoized_calc
def calcTrendData(company) -> dict | None:
    """추세 데이터 — MA 정배열 + ADX. 서사는 review가 생성.

    Capabilities:
        - ``calcTechnicalVerdict`` 의 trend 카테고리 dict + 전체 verdict 동시 반환
        - story 6 막 trend 블록 입력

    Args:
        company: Company 객체 (stockCode 보유).

    Returns:
        dict | None — ``{data, verdict}``. verdict 부재 시 None.

    Guide:
        story extended view 의 trend block. 메모이즈 적용.

    When:
        Story 추세 블록 + AI MA 정배열 답변.

    How:
        ``_calls()`` lazy import → ``calcTechnicalVerdict`` → trend dict 추출.

    Requires:
        company.stockCode + OHLCV fetch 가능.

    Raises:
        없음 — verdict None 시 None 반환.

    Example:
        >>> calcTrendData(company)["data"]["label"]
        '정배열'

    See Also:
        - calcRiskData / calcSignalData : 자매 calc
        - extended.calcTechnicalVerdict : 원본 verdict

    AIContext:
        story 6 막 추세 박스 + AI "현재 추세" 답변에 trend label 인용.
    """
    calcTechnicalVerdict, *_ = _calls()
    verdict = calcTechnicalVerdict(company)
    if verdict is None:
        return None
    return {"data": verdict.get("categories", {}).get("trend"), "verdict": verdict}


@_memoized_calc
def calcRiskData(company) -> dict | None:
    """리스크 데이터 — ATR + 베타 + 변동성.

    Capabilities:
        - ``calcMarketRisk`` (ATR/베타/연환산 변동성) + 기술적 verdict 통합
        - story 6 막 risk 박스 + 진입 시점 손실 폭 인용 근거

    Args:
        company: Company 객체.

    Returns:
        dict | None — ``{data: risk, verdict}``.

    Guide:
        ATR ↑ + β ↑ → 변동성 큰 종목. 손절 폭 동적 조정 권장.

    When:
        Story risk 블록 + AI 변동성 답변.

    How:
        ``calcMarketRisk`` + ``calcTechnicalVerdict`` 동시 호출 → dict 결합.

    Requires:
        OHLCV fetch + 시장 벤치마크 데이터.

    Raises:
        없음.

    Example:
        >>> calcRiskData(company)["data"]["beta"]
        1.18

    See Also:
        - calcTrendData / calcSignalData : 자매 calc
        - extended.calcMarketRisk : 원본 risk

    AIContext:
        ATR / 베타 / 변동성을 인용한 "변동성 위험" 답변.
    """
    calcTechnicalVerdict, _, calcMarketRisk, _ = _calls()
    verdict = calcTechnicalVerdict(company)
    risk = calcMarketRisk(company)
    return {"data": risk, "verdict": verdict}


@_memoized_calc
def calcSignalData(company) -> dict | None:
    """수급 신호 데이터 — 최근 20일 매수/매도.

    Capabilities:
        - ``calcTechnicalSignals`` 결과 dict (signalSummary/recent20) 포장
        - story 6 막 signal 박스 입력

    Args:
        company: Company 객체.

    Returns:
        dict | None — ``{data: signals}``.

    Guide:
        bullish/bearish 수 비율로 단기 모멘텀 강도 판단.

    When:
        Story signal 블록 + AI 매수·매도 시점 답변.

    How:
        ``calcTechnicalSignals`` 호출 → ``{"data": signals}`` 직렬화.

    Requires:
        OHLCV fetch 가능.

    Raises:
        없음.

    Example:
        >>> calcSignalData(company)["data"]["signalSummary"]
        {'bullish': 4, 'bearish': 1}

    See Also:
        - calcTrendData : 추세 동행
        - extended.calcTechnicalSignals : 원본

    AIContext:
        "최근 20 일 매수 시그널 N 개" 답변에 signalSummary 인용.
    """
    _, calcTechnicalSignals, *_ = _calls()
    signals = calcTechnicalSignals(company)
    return {"data": signals}


@_memoized_calc
def calcStrategyData(company) -> dict | None:
    """전략 검증 데이터 — 스타일별 Sharpe + 진입.

    Example:
        >>> calcStrategyData(company)

    Requires:
        company 가 stockCode 보유 + OHLCV fetch 가능.

    Raises:
        없음 (실패는 None).
    """
    strategy = calcStrategySnapshot(company)
    return {"data": strategy}


@_memoized_calc
def calcCrosscheckData(company) -> dict | None:
    """교차 검증 데이터 — analysis 등급 vs 기술적 판단.

    Capabilities:
        - analysis 등급 (fundamental) vs technical verdict 불일치 진단
        - 본 함수의 단일 호출자는 story 6 막 crosscheck 박스

    Args:
        company: Company 객체.

    Returns:
        dict | None — ``{data: divergence}``.

    Guide:
        analysis 강세 + technical 약세 = "내재가치 vs 가격 괴리" 시그널.

    When:
        Story crosscheck 박스 + AI fundamental/technical 비교 답변.

    How:
        ``calcFundamentalDivergence`` 호출 → ``{"data": divergence}`` 직렬화.

    Requires:
        analysis Company 평가 + technical OHLCV 동시 가용.

    Raises:
        없음.

    Example:
        >>> calcCrosscheckData(company)["data"]["diagnosis"]
        '내재가치 강세 vs 기술적 약세'

    See Also:
        - calcQuantConclusionData : 5 축 종합
        - extended.calcFundamentalDivergence : 원본

    AIContext:
        "내재가치 vs 가격" 답변 시 diagnosis 인용.
    """
    _, _, _, calcFundamentalDivergence = _calls()
    divergence = calcFundamentalDivergence(company)
    return {"data": divergence}


@_memoized_calc
def calcQuantConclusionData(company) -> dict | None:
    """결론 데이터 — 5축 방향 집계.

    Capabilities:
        - 추세/시그널/전략/divergence 5 축 통합 dict 생성
        - story 6 막 conclusion 박스 입력 (trend_label/bullish/bearish/active_styles/diagnosis)

    Args:
        company: Company 객체.

    Returns:
        dict | None — keys: trend_label/bullish/bearish/active_styles/diagnosis. verdict 부재 시 None.

    Guide:
        story conclusion 의 단일 입력. 5 축이 일관되게 강세 → "다축 합의 강세" 결론.

    When:
        Story conclusion 블록 + AI 종합 답변.

    How:
        verdict + signals + strategySnapshot + divergence 4 함수 호출 → key 추출 → 집계.

    Requires:
        OHLCV + analysis 동시 가용.

    Raises:
        없음 — verdict None 시 None 반환.

    Example:
        >>> calcQuantConclusionData(company)["active_styles"]
        ['trendFollow', 'breakout']

    See Also:
        - calcStrategySnapshot : active_styles 산출
        - extended.calcFundamentalDivergence : diagnosis

    AIContext:
        "다축 종합 강세 N 축" 답변에 active_styles + diagnosis 인용.
    """
    calcTechnicalVerdict, calcTechnicalSignals, _, calcFundamentalDivergence = _calls()
    verdict = calcTechnicalVerdict(company)
    signals = calcTechnicalSignals(company)
    strategy = calcStrategySnapshot(company)
    divergence = calcFundamentalDivergence(company)

    if verdict is None:
        return None

    cats = verdict.get("categories", {})
    trendLabel = cats.get("trend", {}).get("label", "")
    summary = (signals or {}).get("signalSummary", {})
    bullish = summary.get("bullish", 0)
    bearish = summary.get("bearish", 0)
    activeStyles = []
    if strategy:
        for k, v in strategy.items():
            if isinstance(v, dict) and v.get("entry_today") and v.get("status") == "ok":
                activeStyles.append(k)
    diagnosis = (divergence or {}).get("diagnosis", "")
    return {
        "trend_label": trendLabel,
        "bullish": bullish,
        "bearish": bearish,
        "active_styles": activeStyles,
        "diagnosis": diagnosis,
    }


@_memoized_calc
def calcStrategySnapshot(company) -> dict | None:
    """전략별 진입 진단 — 8 검증된 스타일 일괄 백테스트.

    Strategy DSL 의 story 6막 (전망) 통합 진입점. 시총 의존 0.

    Capabilities:
        - 8 STYLE_REGISTRY 스타일 일괄 백테스트 (runStyle) + 오늘 진입 여부 (runEntry) 평가
        - 스타일별 sharpe/mdd/dsr/trades/entry_today/exit_today/stop_level 8 key dict

    Args:
        company: Company 객체 (stockCode 보유).

    Returns:
        dict | None — ``{styleName: {sharpe, mdd, dsr, trades, entry_today, exit_today, stop_level, status, reason}}``.

    Guide:
        story 6 막 전망 박스 + AI 스타일 추천 답변의 핵심 입력. ``entry_today=True`` +
        ``status="ok"`` 인 스타일 = 오늘 진입 가능.

    When:
        Story 전망 + AI 스타일 추천 답변.

    How:
        ``runStyle("all")`` + ``runEntry("all")`` 호출 → STYLE_REGISTRY 순회 → 스타일별 dict.

    Requires:
        OHLCV ≥ 60 일 + stockCode + 2014 년 이후 데이터.

    Raises:
        없음 — 데이터 부족 시 None.

    Example:
        >>> snap = calcStrategySnapshot(company)
        >>> snap["trendFollow"]["entry_today"]
        True

    See Also:
        - axStrategy.runStyle / runEntry : 백테스트 엔진
        - strategy.presets.STYLE_REGISTRY : 스타일 SSOT

    AIContext:
        "오늘 진입 가능 스타일 N 개" 답변에 entry_today=True 스타일 + sharpe 인용.
    """
    ohlcv = _fetchOhlcv(company)
    if isEmptyDf(ohlcv) or len(ohlcv) < 60:
        return None

    from dartlab.quant.screen.axStrategy import runEntry, runStyle
    from dartlab.quant.strategy.presets import STYLE_REGISTRY

    code = getattr(company, "stockCode", None)
    if not code:
        return None

    bt_results = runStyle(code, name="all", start="2014-01-01")
    entry_results = runEntry(code, style="all", start="2014-01-01")

    snap: dict = {}
    for key in STYLE_REGISTRY().keys():
        bt = bt_results.get(key)
        ev = entry_results.get(key)
        if bt is None:
            continue
        snap[key] = {
            "sharpe": float(bt.sharpe),
            "mdd": float(bt.mdd),
            "dsr": float(bt.dsr) if bt.dsr is not None else None,
            "trades": int(bt.trades.height) if bt.trades is not None else 0,
            "entry_today": bool(ev.active) if ev else False,
            "exit_today": bool(ev.exit_today) if ev else False,
            "stop_level": float(ev.stop_level) if ev and ev.stop_level else None,
            "status": bt.status,
            "reason": bt.reason,
        }
    return snap


def calcActionableTargets(company, *, overrides: dict | None = None) -> dict | None:
    """기술적 관점의 구체적 행동 목표 — 진입/청산 가격.

    Capabilities:
        - 20 일 high/low + Bollinger ±2σ + RSI 14 → 진입/청산 후보 가격 trigger
        - signal 별 (볼린저 하단/RSI 과매도) action/confidence/triggerPrice dict 목록

    Args:
        company: Company 객체.
        overrides: 기본 임계 덮어쓰기. 기본 None.

    Returns:
        dict | None — currentPrice/technicalVerdict/support/resistance/bollingerLower/bollingerUpper/targets.

    Guide:
        AI 답변에 구체적 가격을 인용해야 하는 시점 + story 행동 카드 입력. 신뢰도는
        ``medium``/``high`` 2 단계.

    When:
        Story actionable 카드 + AI "어디서 사야 하나" 답변.

    How:
        OHLCV ≥ 20 → Bollinger lower + RSI → trigger 평가 → 행동 dict 누적.

    Requires:
        OHLCV close ≥ 20 봉.

    Raises:
        없음 — 데이터 부족 시 None.

    Example:
        >>> r = calcActionableTargets(company)
        >>> r["targets"][0]["action"]
        '분할 매수 검토'

    See Also:
        - calcStrategySnapshot : 전략 진입
        - calcRiskData : 손절 보조

    AIContext:
        "지금 매수 적절한가" 답변 시 triggerPrice + action 인용.
    """
    try:
        ohlcv = _fetchOhlcv(company)
    except (AttributeError, ValueError, TypeError):
        return None

    if isEmptyDf(ohlcv):
        return None

    closes = ohlcv["close"].to_list()
    if not closes or len(closes) < 20:
        return None

    current = closes[-1]

    low20 = min(closes[-20:])
    high20 = max(closes[-20:])

    arr = np.array(closes[-20:], dtype=float)
    ma20 = float(np.mean(arr))
    std20 = float(np.std(arr))
    bb_lower = ma20 - 2 * std20
    bb_upper = ma20 + 2 * std20

    targets = []

    if current > bb_lower:
        targets.append(
            {
                "signal": "볼린저 하단 접근",
                "triggerPrice": round(bb_lower),
                "action": "분할 매수 검토",
                "confidence": "medium",
            }
        )

    if len(closes) >= 14:
        gains = [max(0, closes[i] - closes[i - 1]) for i in range(-14, 0)]
        losses = [max(0, closes[i - 1] - closes[i]) for i in range(-14, 0)]
        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14
        rsi = 100 - 100 / (1 + avg_gain / avg_loss) if avg_loss > 0 else 100

        if rsi > 30:
            rsi_target = round(current * 0.90)
            targets.append(
                {
                    "signal": "RSI 과매도 접근",
                    "triggerPrice": rsi_target,
                    "action": "적극 매수 검토",
                    "confidence": "high" if rsi < 40 else "medium",
                }
            )

    calcTechnicalVerdict, *_ = _calls()
    verdict = calcTechnicalVerdict(company)
    tech_label = verdict.get("verdict", "중립") if verdict else "중립"

    return {
        "currentPrice": round(current),
        "technicalVerdict": tech_label,
        "support": round(low20),
        "resistance": round(high20),
        "bollingerLower": round(bb_lower),
        "bollingerUpper": round(bb_upper),
        "targets": targets,
    }


__all__ = [
    "calcActionableTargets",
    "calcCrosscheckData",
    "calcQuantConclusionData",
    "calcRiskData",
    "calcSignalData",
    "calcStrategyData",
    "calcStrategySnapshot",
    "calcTrendData",
]
