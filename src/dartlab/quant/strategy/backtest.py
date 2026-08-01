"""Vectorized backtest 엔진 — long-only, next-bar 시가 체결.

numpy/polars 만 사용. vectorbt/zipline/backtrader 의존 0.

처리:
    - entry/exit boolean 시계열 → trades(entry_idx, exit_idx, pnl)
    - 다음 봉 시가 체결, 수수료 15bp, 슬리피지 5bp
    - sizing/stop 은 Rule 에 명시된 경우만 적용
    - position 1/0 (long-only v1)

출력: BacktestResult dataclass — equity/returns/trades/sharpe/sortino/mdd/dsr/.../

walkForward ruleFactory 경로는 OOS 지표를, 고정 룰 cpcv 경로는 temporal stress를 산출한다.
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
    winrate,
)
from .rule import Rule

# 체결/비용 상수
DEFAULT_FEE_BPS = 15.0  # 양방향 합산 (진입 + 청산)
DEFAULT_SLIP_BPS = 5.0
# ADV 비례 슬리피지: 거래량의 X% 이상 진입 시 추가 충격 비용 (bp/% impact)
DEFAULT_IMPACT_BPS_PER_PCT = 2.0


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
    dsr: float | None = None
    pbo: float | None = None

    # 메타
    style: str | None = None
    period: tuple[date | None, date | None] = (None, None)
    oos: bool = False
    validation: dict | None = None
    cpcv: dict | None = None  # legacy alias for validation/portfolio diagnostics
    scanContext: dict | None = None  # scanBacktest 호출 시 universe 출처 추적

    # NotApplicable sentinel (KR-only style on US)
    status: str = "ok"  # "ok" | "not_applicable" | "error"
    reason: str | None = None

    def __repr__(self) -> str:
        if self.status != "ok":
            return f"BacktestResult(status={self.status!r}, reason={self.reason!r})"
        dsr_text = "n/a" if self.dsr is None else f"{self.dsr:.2f}"
        return (
            f"BacktestResult(style={self.style}, sharpe={self.sharpe:+.2f}, "
            f"mdd={self.mdd * 100:+.1f}%, dsr={dsr_text}, "
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
    nTrials: int | None = None,
    execMode: str = "next_open",
) -> BacktestResult:
    """단일 룰 백테스트 — long-only, 정밀 체결 모델.

    체결 모델 (정밀화 v2):
    - **next_open**: entry[t] True → t+1 시가 체결 (default)
    - **close**: entry[t] True → t 종가 체결 (테스트/sanity)
    - **gap 처리**: next-open 체결가 자체로 전일 종가 대비 갭을 반영
    - **ADV impact**: capital_pct_of_adv > 0 시 거래량 비율에 비례한 충격 비용
    - **intrabar stop**: stop level 이 [low[t], high[t]] 안에 있으면 stop 가격 정확 체결
    - **last bar 청산**: 열린 포지션은 close[-1] 강제 마감

    Capabilities:
        - long-only 정밀 체결 + 실제 갭 체결 + ADV impact + intrabar stop + last-bar 강제 청산
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
        nTrials: DSR 정정용 실제 전략/파라미터 탐색 횟수. None이면 DSR 미산출.
        execMode: ``"next_open"`` | ``"close"``.

    Returns:
        BacktestResult — sharpe/mdd/dsr/trades/oos/cpcv etc.

    Guide:
        Strategy 백테스트 표준 엔진. exec_mode="next_open" + intrabar stop 으로
        realistic 시뮬레이션. n_trials 명시로 DSR multiple testing 정정.

    When:
        Strategy 평가 + AI 백테스트 결과 답변.

    How:
        next_open/close 체결 분기 → 체결별 비용 → intrabar stop → EOD equity 시계열.

    Requires:
        close 길이 ≥ 30 + rule 길이 일치.

    Raises:
        없음 — 짧으면 error sentinel.

    Example:
        >>> vectorBacktest(close, rule).sharpe
        1.18

    See Also:
        - walkForward : OOS sliding
        - cpcv : 고정 룰 CPCV path 구조 temporal stress

    AIContext:
        "이 룰 백테스트 결과" 답변 시 sharpe + mdd + trades 인용.
    """
    n = len(close)
    if n < 30 or len(rule) != n or (nTrials is not None and nTrials < 1):
        return BacktestResult(
            status="error",
            reason=f"invalid backtest input: close={n}, rule={len(rule)}, nTrials={nTrials}",
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

    in_pos = False
    entry_idx = -1
    entry_price = 0.0
    entry_cost = 0.0
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
                    # 시가가 stop 을 관통한 long 포지션은 stop 보다 유리하게 팔 수 없다.
                    exit_raw = min(stop_price_used, float(open_[t])) if open_ is not None else stop_price_used
                    exit_t = t
                else:
                    # next-bar 시가 체결 (또는 close 모드)
                    exit_raw = exec_price[t + 1] if execMode != "close" else close[t]
                    exit_t = t + 1 if execMode != "close" else t
                exit_cost = base_cost + _impactCost(t)
                exit_price = exit_raw * (1 - exit_cost)
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
                        "cost_bps": (entry_cost + exit_cost) * 1e4,
                    }
                )
                in_pos = False
                continue

        # 진입 조건 체크 (현금 상태에서만)
        if not in_pos and bool(rule.entry_expr[t]):
            entry_raw = exec_price[t + 1] if execMode != "close" else close[t]
            entry_cost = base_cost + _impactCost(t)
            entry_price = entry_raw * (1 + entry_cost)
            entry_idx = t + 1 if execMode != "close" else t
            in_pos = True

    # 마지막 봉 청산 (열린 포지션 강제 마감)
    if in_pos:
        exit_cost = base_cost + _impactCost(n - 1)
        exit_price = close[-1] * (1 - exit_cost)
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
                "cost_bps": (entry_cost + exit_cost) * 1e4,
            }
        )

    # 거래별 유효 체결가를 단일 원장으로 삼아 EOD wealth 를 재생한다. 비용을 종가
    # 수익률에서 다시 추정하지 않아 trade pnl, returns, equity 가 같은 복리 항등식을 쓴다.
    daily_ret, equity, pos = _replayTrades(close, trades)

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
    # full-notional long-only 한 번의 왕복은 진입 1 + 청산 1 = 총 회전 2 이다.
    to = float(2 * len(trades))
    expo = exposure(pos.astype(np.float64))
    ds = None if nTrials is None else dsr(sh, daily_ret, nTrials=nTrials)

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


def _replayTrades(close: np.ndarray, trades: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """유효 체결가 원장에서 일별 단순 수익률, EOD equity, EOD position 을 재생한다."""
    n = len(close)
    growth = np.ones(n, dtype=np.float64)
    positions = np.zeros(n, dtype=np.int8)

    for trade in trades:
        entry = int(trade["entry_idx"])
        exit_ = int(trade["exit_idx"])
        entry_price = float(trade["entry_price"])
        exit_price = float(trade["exit_price"])

        if entry == exit_:
            growth[entry] *= exit_price / entry_price
            continue

        growth[entry] *= float(close[entry]) / entry_price
        positions[entry:exit_] = 1
        for bar in range(entry + 1, exit_):
            growth[bar] *= float(close[bar]) / float(close[bar - 1])
        growth[exit_] *= exit_price / float(close[exit_ - 1])

    returns = growth - 1.0
    equity = np.cumprod(growth)
    return returns, equity, positions


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
