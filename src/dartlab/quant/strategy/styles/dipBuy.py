"""눌림목매수 (Dip Buy) — 강세장 단기 조정 진입.

[언제 강한가]
규모 있는 상승 추세 + 단기 5~10% 조정 후 반등 시점. Bull regime 에서만 작동.
2020-2021 비트코인 / 나스닥, 2017 코스닥 강세장.

[어떤 종목에 어울리나]
시총 중대형 + 명확한 상승 추세 종목. 사이클 종목은 회피 (조정이 추세 종료일 수 있음).

[진입 조건의 의미]
HMM bull regime + 종가 > EMA50 (장기 추세 유지) + RSI < 40 (단기 과매도).
3중 조건으로 "강세장 일시 조정" 명확히 정의.

[청산 조건]
RSI > 60 (정상 회복). ATR×2 stop.

[주의점]
- regime 이 sideways 로 전환되면 즉시 손절. 이 경우 dip 이 아니라 추세 전환.
- 지지선 깨지면 ATR stop 보다 먼저 청산.

[대표 사례]
- BTFD (Buy the F***ing Dip) — 2009-2021 미국 강세장 표준 전략
- Schwager "Market Wizards" 인터뷰 다수에서 반복 언급

[관련 dartlab 축]
regime.calcRegime, indicators.vrsi, indicators.vema

[복제 + 수정 예시]
    rule = (regime_state == 2) & (close > ema50) & (rsi < 40)
    Rule(rule, rsi > 60).with_stop("atr", k=2.0)
"""

from __future__ import annotations

import numpy as np

from dartlab.quant.regime.hmm import _regimeSeries
from dartlab.quant.strategy.rule import Rule
from dartlab.quant.strategy.signal import Signal
from dartlab.quant.strategy.styles._common import getArrays
from dartlab.synth.indicators import vema, vrsi


def build(company, *, emaPeriod: int = 50, rsiLow: float = 50, rsiHigh: float = 65, atrK: float = 2.0) -> Rule:
    """눌림목매수 룰 빌드.

    [학술 정의] BTFD (Buy The F***ing Dip) — 강세장(bull regime) + 장기 추세 위(EMA50)
    상태에서 단기 momentum 약세(RSI < 50) 진입. 회복(RSI > 65) 시 청산.

    [임계 정정 (Phase 4 R1)] 이전 RSI<40 은 강세장 + EMA50 위 와 물리적으로 양립
    불가능 (bull&above_ema 시 RSI 최소 42.5 ~ 중앙값 59). RSI<50 이 학술적으로 정확.
    RSI 30 oversold 는 추세 종료 의미 — meanReversion 룰의 영역.

    Capabilities:
        - 강세 regime + EMA 위 + RSI < 50 → 진입, RSI > 65 회복 → 청산
        - ATR×2 stop

    Args:
        company: Company 객체.
        emaPeriod: 장기 추세 EMA 기간. 기본 ``50``.
        rsiLow: 진입 RSI 임계. 기본 ``50``.
        rsiHigh: 청산 RSI 임계. 기본 ``65``.
        atrK: ATR stop 배수. 기본 ``2.0``.

    Returns:
        Rule — entry/exit + atr stop.

    Guide:
        강세장 단기 조정 매수. regime 필터 필수 (약세장 BTFD 금지).

    When:
        Bull-market dip + AI 조정 매수 답변.

    How:
        regime + EMA50 + RSI 진입/청산 Signal.

    Requires:
        close ≥ 100 봉.

    Raises:
        없음.

    Example:
        >>> build(company).meta["style"]
        'dipBuy'

    See Also:
        - strategy.styles.trendFollow : 동행
        - regime.hmm : regime 입력

    AIContext:
        "강세장 조정 매수" 답변 시 entry 봉 인용.
    """
    arr = getArrays(company)
    close = arr.get("close")
    if close is None or len(close) < 100:
        n = len(close) if close is not None else 0
        return Rule(
            entry_expr=np.zeros(max(n, 1), dtype=np.bool_),
            exit_expr=np.zeros(max(n, 1), dtype=np.bool_),
            meta={"style": "dipBuy", "error": "insufficient data"},
        )

    rsi = vrsi(close, period=14)
    ema = vema(close, emaPeriod)
    reg = _regimeSeries(close)
    state = reg["state"]

    s = Signal()
    s.add("bull", state == 2)
    s.add("above_ema", (close > ema) & ~np.isnan(ema))
    s.add("rsi_low", (rsi < rsiLow) & ~np.isnan(rsi))
    s.add("rsi_high", (rsi > rsiHigh) & ~np.isnan(rsi))

    return Rule(
        entry_expr=s.bull & s.above_ema & s.rsi_low,
        exit_expr=s.rsi_high,
        meta={"style": "dipBuy"},
    ).withStop("atr", k=atrK, period=14)
