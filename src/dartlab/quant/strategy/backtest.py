"""Vectorized backtest 엔진 — long-only, next-bar 시가 체결.

numpy/polars 만 사용. vectorbt/zipline/backtrader 의존 0.

처리:
    - entry/exit boolean 시계열 → trades(entry_idx, exit_idx, pnl)
    - 다음 봉 시가 체결, 수수료 15bp, 슬리피지 5bp
    - sizing/stop 은 Rule 에 명시된 경우만 적용
    - position 1/0 (long-only v1)

출력: BacktestResult dataclass — equity/returns/trades/sharpe/sortino/mdd/dsr/.../

walkForward + cpcv 로 OOS Sharpe + DSR + PBO 산출 가능.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import polars as pl

from dartlab.core.polarsUtil import isEmptyDf

from .metrics import (
    dsr,
    expectancy,
    exposure,
    mdd,
    profitFactor,
    sharpe,
    sortino,
    turnover,
    winrate,
)
from .rule import Rule

# 체결/비용 상수
DEFAULT_FEE_BPS = 15.0  # 양방향 합산 (진입 + 청산)
DEFAULT_SLIP_BPS = 5.0
# ADV 비례 슬리피지: 거래량의 X% 이상 진입 시 추가 충격 비용 (bp/% impact)
DEFAULT_IMPACT_BPS_PER_PCT = 2.0
# 갭 임계: open[t+1]/close[t] 가 이 비율 초과 시 갭 위험 알림 (slippage 가중)
GAP_THRESHOLD_PCT = 0.03


@dataclass(frozen=True)
class BacktestResult:
    """백테스트 결과 — equity/trades/metrics + overfitting guards."""

    # 시계열
    equity: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    returns: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    positions: np.ndarray = field(default_factory=lambda: np.array([], dtype=np.float64))
    trades: pl.DataFrame | None = None

    # 표준 메트릭
    sharpe: float = 0.0
    sortino: float = 0.0
    mdd: float = 0.0
    winrate: float = 0.0
    profitFactor: float = 0.0
    expectancy: float = 0.0
    turnover: float = 0.0
    exposure: float = 0.0

    # Overfitting guards
    dsr: float = 0.0
    pbo: float | None = None

    # 메타
    style: str | None = None
    period: tuple[date | None, date | None] = (None, None)
    oos: bool = False
    cpcv: dict | None = None
    scanContext: dict | None = None  # scanBacktest 호출 시 universe 출처 추적

    # NotApplicable sentinel (KR-only style on US)
    status: str = "ok"  # "ok" | "not_applicable" | "error"
    reason: str | None = None

    def __repr__(self) -> str:
        if self.status != "ok":
            return f"BacktestResult(status={self.status!r}, reason={self.reason!r})"
        return (
            f"BacktestResult(style={self.style}, sharpe={self.sharpe:+.2f}, "
            f"mdd={self.mdd * 100:+.1f}%, dsr={self.dsr:.2f}, "
            f"trades={self.trades.height if self.trades is not None else 0}, "
            f"oos={self.oos})"
        )

    @classmethod
    def notApplicable(cls, *, style: str, reason: str) -> "BacktestResult":
        """KR-only 스타일을 US 에서 호출 시 sentinel.

        Example:
            >>> BacktestResult.notApplicable(style="kr_flow", reason="US 미지원")

        Requires:
            style/reason 문자열.

        Raises:
            없음.
        """
        return cls(status="not_applicable", reason=reason, style=style)


# ── 핵심 백테스트 ───────────────────────────────────────────────────────────


def vectorBacktest(
    close: np.ndarray,
    rule: Rule,
    *,
    open_: np.ndarray | None = None,
    high: np.ndarray | None = None,
    low: np.ndarray | None = None,
    volume: np.ndarray | None = None,
    dates: list | None = None,
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
    impactBpsPerPct: float = DEFAULT_IMPACT_BPS_PER_PCT,
    capitalPctOfAdv: float = 0.0,
    style: str | None = None,
    nTrials: int = 1,
    execMode: str = "next_open",
) -> BacktestResult:
    """단일 룰 백테스트 — long-only, 정밀 체결 모델.

    체결 모델 (정밀화 v2):
    - **next_open**: entry[t] True → t+1 시가 체결 (default)
    - **close**: entry[t] True → t 종가 체결 (테스트/sanity)
    - **gap 처리**: open[t+1]/close[t] 변동률 ≥ GAP_THRESHOLD_PCT 면 추가 슬리피지
    - **ADV impact**: capital_pct_of_adv > 0 시 거래량 비율에 비례한 충격 비용
    - **intrabar stop**: stop level 이 [low[t], high[t]] 안에 있으면 stop 가격 정확 체결
    - **last bar 청산**: 열린 포지션은 close[-1] 강제 마감

    Capabilities:
        - long-only 정밀 체결 + 갭 처리 + ADV impact + intrabar stop + last-bar 강제 청산
        - DSR 정정 (multiple trials) + Sharpe/MDD/turnover/exposure 메타

    Args:
        close: 일별 종가.
        rule: Rule 객체 (entry/exit/sizing/stop).
        open_/high/low: 정밀 체결 / 갭 / intrabar stop 용.
        volume: ADV impact 계산.
        dates: period 메타.
        feeBps: 양방향 수수료 (bps).
        slipBps: 기본 슬리피지 (bps).
        impactBpsPerPct: 1% ADV 진입 시 추가 bps.
        capitalPctOfAdv: 진입 자본의 거래량 대비 비율.
        style: 스타일 식별자.
        nTrials: DSR 정정용 시도 횟수.
        execMode: ``"next_open"`` | ``"close"``.

    Returns:
        BacktestResult — sharpe/mdd/dsr/trades/oos/cpcv etc.

    Guide:
        Strategy 백테스트 표준 엔진. exec_mode="next_open" + intrabar stop 으로
        realistic 시뮬레이션. n_trials 명시로 DSR multiple testing 정정.

    When:
        Strategy 평가 + AI 백테스트 결과 답변.

    How:
        next_open/close 체결 분기 → gap/impact 비용 → intrabar stop → equity 시계열.

    Requires:
        close 길이 ≥ 30 + rule 길이 일치.

    Raises:
        없음 — 짧으면 error sentinel.

    Example:
        >>> vectorBacktest(close, rule).sharpe
        1.18

    See Also:
        - walkForward : OOS sliding
        - cpcv : Combinatorial Purged CV

    AIContext:
        "이 룰 백테스트 결과" 답변 시 sharpe + mdd + trades 인용.
    """
    n = len(close)
    if n < 30 or len(rule) != n:
        return BacktestResult(
            status="error",
            reason=f"length mismatch or too short: close={n}, rule={len(rule)}",
            style=style,
        )

    # 체결 가격 선택
    if execMode == "close":
        exec_price = close
    else:
        exec_price = open_ if open_ is not None else close

    base_cost = (feeBps + slipBps) / 1e4 / 2.0  # 한쪽

    # ADV impact (거래량 비례)
    def _impactCost(tIdx: int) -> float:
        """t_idx 봉의 거래량 대비 진입 비율 → impact bps 추가."""
        if volume is None or capitalPctOfAdv <= 0 or tIdx >= len(volume):
            return 0.0
        # capital_pct_of_adv = 우리 진입 자본 / 평균 일거래량 (%)
        return (capitalPctOfAdv * impactBpsPerPct) / 1e4 / 2.0

    # gap 가중 (open[t+1] vs close[t])
    def _gapCost(tIdx: int) -> float:
        if open_ is None or tIdx + 1 >= n:
            return 0.0
        gap_pct = abs(open_[tIdx + 1] - close[tIdx]) / max(close[tIdx], 1e-9)
        if gap_pct >= GAP_THRESHOLD_PCT:
            return gap_pct * 0.5  # 갭의 50% 추가 슬리피지
        return 0.0

    # 포지션 시계열
    pos = np.zeros(n, dtype=np.int8)
    in_pos = False
    entry_idx = -1
    entry_price = 0.0
    trades: list[dict] = []

    # stop 시계열 (옵션)
    stop_series: np.ndarray | None = None
    if rule.stop and high is not None and low is not None:
        stop_series = _buildStopSeries(close, high, low, rule.stop)

    for t in range(n - 1):
        # 청산 조건 체크 (홀딩 중일 때만)
        if in_pos:
            should_exit = bool(rule.exit_expr[t])
            stop_hit_intrabar = False
            stop_price_used = None

            # intrabar stop: 당일 low 가 stop 을 뚫었으면 stop 가격으로 체결
            if (
                stop_series is not None
                and not np.isnan(stop_series[t])
                and low is not None
                and low[t] <= stop_series[t]
            ):
                stop_hit_intrabar = True
                stop_price_used = float(stop_series[t])
                should_exit = True

            if should_exit:
                if stop_hit_intrabar and stop_price_used is not None:
                    # intrabar stop: 정확한 stop 가격 (다음 봉 아님)
                    exit_raw = stop_price_used
                    exit_t = t
                else:
                    # next-bar 시가 체결 (또는 close 모드)
                    exit_raw = exec_price[t + 1] if execMode != "close" else close[t]
                    exit_t = t + 1 if execMode != "close" else t
                cost = base_cost + _impactCost(t) + _gapCost(t)
                exit_price = exit_raw * (1 - cost)
                pnl = (exit_price - entry_price) / entry_price
                trades.append(
                    {
                        "entry_idx": entry_idx,
                        "exit_idx": exit_t,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl": pnl,
                        "bars_held": exit_t - entry_idx,
                        "exit_reason": "stop" if stop_hit_intrabar else "signal",
                        "cost_bps": cost * 1e4 * 2,
                    }
                )
                in_pos = False
                pos[t + 1] = 0
                continue

        # 진입 조건 체크 (현금 상태에서만)
        if not in_pos and bool(rule.entry_expr[t]):
            entry_raw = exec_price[t + 1] if execMode != "close" else close[t]
            cost = base_cost + _impactCost(t) + _gapCost(t)
            entry_price = entry_raw * (1 + cost)
            entry_idx = t + 1 if execMode != "close" else t
            in_pos = True
            pos[t + 1] = 1
        else:
            pos[t + 1] = pos[t]

    # 마지막 봉 청산 (열린 포지션 강제 마감)
    if in_pos:
        cost = base_cost + _impactCost(n - 1)
        exit_price = close[-1] * (1 - cost)
        pnl = (exit_price - entry_price) / entry_price
        trades.append(
            {
                "entry_idx": entry_idx,
                "exit_idx": n - 1,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "pnl": pnl,
                "bars_held": n - 1 - entry_idx,
                "exit_reason": "force_close",
                "cost_bps": cost * 1e4 * 2,
            }
        )

    # 일별 수익률 (포지션 기반). 체결 비용을 진입과 청산 봉에 실어 준다.
    #
    # 예전에는 종가만으로 만들어서 수수료, 슬리피지, 갭, 물량 충격이 하나도 반영되지
    # 않았다. 그 비용은 거래 손익에만 붙었기 때문에, 수수료를 0 에서 1000bp 로 올려도
    # 샤프와 최대낙폭이 글자 하나 바뀌지 않았다. 모듈 docstring 이 "수수료 15bp,
    # 슬리피지 5bp" 를 물린다고 밝히는데 정작 대표 지표가 그것을 모르는 셈이었다.
    daily_ret = np.zeros(n, dtype=np.float64)
    for i in range(1, n):
        if pos[i] == 1:
            daily_ret[i] = (close[i] - close[i - 1]) / close[i - 1]
    for trade in trades:
        # `cost_bps` 는 왕복 기준이라 절반씩 진입 봉과 청산 봉에 나눠 붙인다.
        oneWay = float(trade.get("cost_bps", 0.0)) / 2.0 / 1e4
        for barKey in ("entry_idx", "exit_idx"):
            bar = int(trade.get(barKey, -1))
            if 0 <= bar < n:
                daily_ret[bar] -= oneWay
    equity = np.cumprod(1.0 + daily_ret)

    # trades DataFrame
    trades_df = (
        pl.DataFrame(trades)
        if trades
        else pl.DataFrame(
            schema={
                "entry_idx": pl.Int64,
                "exit_idx": pl.Int64,
                "entry_price": pl.Float64,
                "exit_price": pl.Float64,
                "pnl": pl.Float64,
                "bars_held": pl.Int64,
                "exit_reason": pl.Utf8,
                "cost_bps": pl.Float64,
            }
        )
    )

    pnls = np.array([t["pnl"] for t in trades], dtype=np.float64)

    sh = sharpe(daily_ret)
    so = sortino(daily_ret)
    md = mdd(equity)
    wr = winrate(pnls)
    pf = profitFactor(pnls)
    ex = expectancy(pnls)
    to = turnover(pos.astype(np.float64))
    expo = exposure(pos.astype(np.float64))
    ds = dsr(sh, daily_ret, nTrials=nTrials)

    period = (None, None)
    if dates and len(dates) >= 2:
        period = (dates[0], dates[-1])

    return BacktestResult(
        equity=equity,
        returns=daily_ret,
        positions=pos.astype(np.float64),
        trades=trades_df,
        sharpe=sh,
        sortino=so,
        mdd=md,
        winrate=wr,
        profitFactor=pf,
        expectancy=ex,
        turnover=to,
        exposure=expo,
        dsr=ds,
        style=style,
        period=period,
        oos=False,
    )


def _buildStopSeries(close, high, low, stopSpec) -> np.ndarray:
    """rule.stop dict → 시계열 stop level."""
    method = stopSpec.get("method", "atr")
    kw = stopSpec.get("kwargs", {})
    if method == "atr":
        from dartlab.quant.signal.generator import vAtrTrailingStop

        k = kw.get("k", 3.0)
        period = kw.get("period", 14)
        return vAtrTrailingStop(close, high, low, atrPeriod=period, multiplier=k)
    if method == "fixed_pct":
        pct = kw.get("pct", 0.05)
        return close * (1 - pct)
    return np.full(len(close), np.nan, dtype=np.float64)


# ── Walk-forward + CPCV ─────────────────────────────────────────────────────


# ── walkForward + multiAssetBacktest + cpcv → _backtestAdvanced.py 분리 ──

from dartlab.quant.strategy._backtestAdvanced import (  # noqa: E402, F401
    cpcv,
    multiAssetBacktest,
    walkForward,
)
