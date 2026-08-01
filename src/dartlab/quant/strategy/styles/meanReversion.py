"""평균회귀 (Mean Reversion) — 단기 과매도 매수 / 과매수 매도 스타일.

[언제 강한가]
횡보장 + 변동성 정상 구간. 명확한 추세 없는 6~24개월 박스권 국면.
2014-2015 KOSPI, 2018 KOSPI, 2023 KOSDAQ 같은 횡보 환경에서 강함.

[어떤 종목에 어울리나]
유동성 풍부한 대형주 + 변동성 낮은 종목. 사이클 산업 (반등 명확).
실적 안정 + 과매도 후 회복 패턴 잦은 종목.

[진입 조건의 의미]
RSI(14) < 30 (과매도) + 종가 < 볼린저 하단 (이상 하락) + 변동성 정상 (vol < q60).
변동성 폭발 구간(vol > q60) 회피해서 추세 시작점에 진입하지 않음.

[청산 조건]
RSI > 50 (정상 회복). ATR×2 stop 으로 손실 제한.

[주의점]
- 추세 시작점에서 catch falling knife 위험. 변동성 필터 필수.
- 청산 임계 RSI 50 너무 빠르면 win 작아짐 → 60~70 으로 조정 가능.
- 금융위기/코로나 같은 fat tail 에서 큰 손실.

[대표 사례]
- Avellaneda & Lee (2008) "Statistical Arbitrage in the U.S. Equities Market"
- Lo & MacKinlay (1990) — 단기 평균회귀
- Khandani & Lo (2007) — 8월 2007 quant crisis 평균회귀

[관련 dartlab 축]
indicators.vrsi, indicators.vbollinger, volatility (garch_vol)

[복제 + 수정 예시]
    rule = (rsi < 30) & (close < bb_lower) & (vol < vol_q60)
    Rule(rule, rsi > 50).with_stop("atr", k=2.0)
"""

from __future__ import annotations

import numpy as np

from dartlab.quant.risk.volatility import _volatilitySeries
from dartlab.quant.strategy.rule import Rule
from dartlab.quant.strategy.signal import Signal
from dartlab.quant.strategy.styles._common import getArrays, rollingQuantile
from dartlab.synth.indicators import vrsi


def _residualZScore(close: np.ndarray, window: int = 60) -> np.ndarray:
    """log(close) 의 rolling residual z-score — Avellaneda-Lee OU 정상화 form.

    학술 (Avellaneda & Lee 2008):
        log price → 직전 rolling mean 제거 (de-trend) → std 정규화
        z < -s_bo (entry threshold), z > -s_so (exit threshold)
    """
    n = len(close)
    z = np.full(n, np.nan, dtype=np.float64)
    log_p = np.log(np.maximum(close, 1e-9))
    for i in range(window, n):
        win = log_p[i - window : i]
        mu = float(np.mean(win))
        sd = float(np.std(win, ddof=1))
        if sd > 0:
            z[i] = (log_p[i] - mu) / sd
    return z


def build(
    company,
    *,
    zEntry: float = -1.25,
    zExit: float = -0.5,
    zWindow: int = 60,
    rsiConfirm: float = 35,
    atrK: float = 2.0,
) -> Rule:
    """평균회귀 룰 빌드 — Avellaneda-Lee 2008 statistical arbitrage 정의.

    학술 정의:
        z(t) = (log(close[t]) - prior_rolling_mean(60)) / prior_rolling_std(60)
        Entry: z < -1.25 (1.25σ 하방 이탈) + 변동성 정상 + RSI 확인
        Exit:  z > -0.5 (평균 회복 진행)

    원본 Avellaneda-Lee 는 PCA residual 이지만 단일 종목엔 self-residual 사용.
    s_bo = -1.25, s_so = -0.50 은 논문 권장값.

    Capabilities:
        - residual z-score < -1.25 + RSI oversold + 정상 변동성 → 진입
        - z > -0.5 회복 → 청산 + ATR×2 stop

    Args:
        company: Company 객체.
        zEntry: 진입 z-score 임계. 기본 ``-1.25``.
        zExit: 청산 z 임계. 기본 ``-0.5``.
        zWindow: rolling 기간. 기본 ``60``.
        rsiConfirm: RSI 추가 확인 임계. 기본 ``35``.
        atrK: ATR stop 배수. 기본 ``2.0``.

    Returns:
        Rule — entry/exit + atr stop.

    Guide:
        Avellaneda-Lee 2008 statistical arbitrage. 횡보 + low-vol regime 최적.

    When:
        Mean-reversion + AI 평균회귀 답변.

    How:
        z-score + RSI + 직전 252일 vol q70 필터 → entry → recovery exit.

    Requires:
        close ≥ zWindow + 20.

    Raises:
        없음.

    Example:
        >>> build(company).meta["style"]
        'meanReversion'

    See Also:
        - strategy.styles.trendFollow : 반대 스타일
        - strategy.styles.dipBuy : 단기 mean reversion

    AIContext:
        "평균 회귀 매수 기회" 답변 시 entry 마지막 봉 인용.
    """
    arr = getArrays(company)
    close = arr.get("close")
    if close is None or len(close) < zWindow + 20:
        n = len(close) if close is not None else 0
        return Rule(
            entry_expr=np.zeros(max(n, 1), dtype=np.bool_),
            exit_expr=np.zeros(max(n, 1), dtype=np.bool_),
            meta={"style": "meanReversion", "error": "insufficient data"},
        )

    z = _residualZScore(close, window=zWindow)
    rsi = vrsi(close, period=14)
    vol_series = _volatilitySeries(close)
    realized = vol_series["realized_vol"]
    vol_q70 = rollingQuantile(realized, 0.70, window=252, minPeriods=60)

    s = Signal()
    s.add("z_low", (z < zEntry) & ~np.isnan(z))
    s.add("z_recover", (z > zExit) & ~np.isnan(z))
    s.add("rsi_oversold", (rsi < rsiConfirm) & ~np.isnan(rsi))
    s.add("vol_normal", (realized < vol_q70) & ~np.isnan(realized) & ~np.isnan(vol_q70))

    return Rule(
        entry_expr=s.z_low & s.rsi_oversold & s.vol_normal,
        exit_expr=s.z_recover,
        meta={
            "style": "meanReversion",
            "definition": "Avellaneda-Lee_2008",
            "formation": "prior_252d_min_60d",
        },
    ).withStop("atr", k=atrK, period=14)
