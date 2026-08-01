"""저변동방어 (Low Vol Defensive) — 변동성 낮고 낙폭 작은 종목 보유.

[언제 강한가]
약세장 + 횡보장. 변동성 폭발 회피 전략. AQR/MSCI 의 long-term low-vol anomaly
검증 (1968-2020 미국 시장에서 risk-adjusted return 최고 quintile).

[어떤 종목에 어울리나]
유틸리티/필수소비재/통신 같은 defensive 섹터. 사이클 종목 제외.
KOSPI 우량주 대형주 best.

[진입 조건의 의미]
20일 realized vol < 30 percentile (시장 평균보다 안정) + 252일 rolling MDD > -10%
(역사적 낙폭 작음). 두 조건 모두 만족 시 보유 시작.

[청산 조건]
vol > 70 percentile (변동성 폭발) 시 즉시 청산. stop 없음 (홀드 유지).

[주의점]
- 강세장에서 underperform (방어주는 상승률 낮음)
- 청산 임계 (q70) 자주 터지면 너무 빠른 청산 → q80 으로 조정 가능
- 252일 MDD 계산을 위해 최소 1년 데이터 필요

[대표 사례]
- Frazzini & Pedersen (2014) "Betting Against Beta"
- Asness, Frazzini, Pedersen (2019) "Quality Minus Junk"
- MSCI Minimum Volatility Index (1988-)

[관련 dartlab 축]
volatility.calcVolatility (realized_vol), tailrisk.calcTailrisk (rolling_mdd)

[복제 + 수정 예시]
    rule = (vol < q30) & (mdd > -0.10)
    Rule(rule, vol > q70)
"""

from __future__ import annotations

import numpy as np

from dartlab.quant.risk.tailrisk import _tailriskSeries
from dartlab.quant.risk.volatility import _volatilitySeries
from dartlab.quant.strategy.rule import Rule
from dartlab.quant.strategy.signal import Signal
from dartlab.quant.strategy.styles._common import getArrays, rollingQuantile, rollingZScore

_HISTORY_WINDOW = 252 * 5
_MIN_HISTORY = 252
_MIN_CLOSE = 252 + _MIN_HISTORY + 1


def build(
    company,
    *,
    volLowQ: float = 0.40,
    volHighQ: float = 0.70,
    mddZEntry: float = 0.0,
    mddZExit: float = -1.0,
) -> Rule:
    """저변동방어 룰 빌드.

    [학술 정의 정정 (Phase 4 R2)] 원래 plan 의 절대 `mdd_threshold=-0.10` 은
    KR 시장에 물리적으로 도달 불가능 (KOSPI 대형주도 1년 내 거의 항상 10%+ 낙폭).
    Frazzini-Pedersen 2014 BAB 의 cross-section 정의를 단일 종목에 적용 불가.

    대신 self-history z-score: 직전 최대 5년 rolling MDD 분포 vs 현재 시점.
    `mdd_z = (mdd_t - μ) / σ` — z > 0.5 = 평소보다 안정적, z < -0.5 = 평소보다 위험.

    Capabilities:
        - 직전 최대 5년 변동성 < 40 분위 + 자기 history MDD z-score ≥ 0 진입
        - 변동성 > 70 분위 또는 MDD z < -1.0 청산

    Args:
        company: Company 객체.
        volLowQ: 변동성 진입 분위. 기본 ``0.40``.
        volHighQ: 변동성 청산 분위. 기본 ``0.70``.
        mddZEntry: rolling MDD self z 진입. 기본 ``0.0``.
        mddZExit: 청산. 기본 ``-1.0``.

    Returns:
        Rule — entry/exit (stop 없음, vol exit 이 stop 역할).

    Guide:
        Frazzini-Pedersen 2014 BAB self-history z-score 적용. 절대 임계 (mdd<-0.10)
        는 KR 시장에 부적합.

    When:
        Low-vol defensive + AI 방어적 매수 답변.

    How:
        ``_volatilitySeries`` + ``_tailriskSeries`` → 분위 + z-score → Signal.

    Requires:
        close ≥ 505 봉 (252일 MDD + 최소 252개 과거 분포 + 현재 봉).

    Raises:
        없음.

    Example:
        >>> build(company).meta["style"]
        'lowVolDefensive'

    See Also:
        - strategy.styles.meanReversion : 다른 방어형
        - risk.tailrisk : MDD core

    AIContext:
        "지금 방어적 매수 가능" 답변 시 entry 봉 인용.
    """
    arr = getArrays(company)
    close = arr.get("close")
    if close is None or len(close) < _MIN_CLOSE:
        n = len(close) if close is not None else 0
        return Rule(
            entry_expr=np.zeros(max(n, 1), dtype=np.bool_),
            exit_expr=np.zeros(max(n, 1), dtype=np.bool_),
            meta={"style": "lowVolDefensive", "error": "insufficient data"},
        )

    vs = _volatilitySeries(close)
    realized = vs["realized_vol"]
    ts = _tailriskSeries(close)
    mdd_series = ts["rolling_mdd"]

    valid_vol = realized[~np.isnan(realized)]
    valid_mdd = mdd_series[~np.isnan(mdd_series)]
    if len(valid_vol) < 20 or len(valid_mdd) < 20:
        n = len(close)
        return Rule(
            entry_expr=np.zeros(n, dtype=np.bool_),
            exit_expr=np.zeros(n, dtype=np.bool_),
            meta={"style": "lowVolDefensive", "error": "no vol/mdd data"},
        )

    q_low = rollingQuantile(realized, volLowQ, window=_HISTORY_WINDOW, minPeriods=_MIN_HISTORY)
    q_high = rollingQuantile(realized, volHighQ, window=_HISTORY_WINDOW, minPeriods=_MIN_HISTORY)

    # MDD self-history z-score (Phase 4 R2)
    mdd_z = rollingZScore(mdd_series, window=_HISTORY_WINDOW, minPeriods=_MIN_HISTORY)
    formation_ready = np.arange(len(close)) >= _MIN_CLOSE - 1

    s = Signal()
    s.add("vol_low", formation_ready & (realized < q_low) & ~np.isnan(realized) & ~np.isnan(q_low))
    s.add("vol_high", formation_ready & (realized > q_high) & ~np.isnan(realized) & ~np.isnan(q_high))
    s.add("mdd_safer", formation_ready & (mdd_z > mddZEntry) & ~np.isnan(mdd_z))
    s.add("mdd_riskier", formation_ready & (mdd_z < mddZExit) & ~np.isnan(mdd_z))

    return Rule(
        entry_expr=s.vol_low & s.mdd_safer,
        exit_expr=s.vol_high | s.mdd_riskier,
        meta={
            "style": "lowVolDefensive",
            "definition": "BAB_self_zscore",
            "formation": "prior_up_to_5y_min_1y",
        },
    )
