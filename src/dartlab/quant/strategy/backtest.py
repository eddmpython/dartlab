"""Vectorized backtest 엔진 — long-only, next-bar 시가 체결.

numpy/polars 만 사용. vectorbt/zipline/backtrader 의존 0.

처리:
    - entry/exit boolean 시계열 → trades(entry_idx, exit_idx, pnl)
    - 다음 봉 시가 체결, 수수료 15bp, 슬리피지 5bp
    - sizing/stop 은 Rule 에 명시된 경우만 적용
    - position 은 현금 포함 포트폴리오의 실제 long exposure

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
    exposure: float = 0.0  # time in market: |position| > 0 인 관측 비율
    averageExposure: float = 0.0  # 실제 평균 gross capital exposure

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
      (open 미제공 시 합성·sanity 용도로 close를 명시적 fallback)
    - **close**: entry[t] True → t 종가 체결 (테스트/sanity)
    - **gap 처리**: next-open 체결가 자체로 전일 종가 대비 갭을 반영
    - **ADV impact**: capital_pct_of_adv > 0 시 거래량 비율에 비례한 충격 비용
    - **intrabar stop**: stop level 이 [low[t], high[t]] 안에 있으면 stop 가격 정확 체결
    - **last bar 청산**: 열린 포지션은 close[-1] 강제 마감

    Capabilities:
        - long-only 정밀 체결 + 실제 갭 체결 + ADV impact + intrabar stop + last-bar 강제 청산
        - equal/fixed/Kelly/신호시점 vol-target 고정 size의 cash + units 자기금융 원장
        - DSR 정정 (multiple trials) + Sharpe/MDD/turnover/exposure 메타

    Args:
        close: 일별 종가.
        rule: Rule 객체. sizing은 equal, fixed, kelly, vol_target_at_entry,
            risk_budget_at_entry를 지원한다. 동적 vol_target은 지원하지 않는다.
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
        close 길이 ≥ 30, Rule·OHLCV·dates 길이와 값, 비용, 체결 모드가 유효해야 한다.

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
    try:
        close = np.asarray(close, dtype=np.float64)
    except (TypeError, ValueError):
        return BacktestResult(status="error", reason="invalid close: numeric series required", style=style)
    if close.ndim != 1 or len(close) < 30 or not np.all(np.isfinite(close)) or np.any(close <= 0):
        return BacktestResult(status="error", reason="invalid close: finite positive 1D series required", style=style)

    n = len(close)
    valid_trials = nTrials is None or (isinstance(nTrials, int) and not isinstance(nTrials, bool) and nTrials >= 1)
    rule_length = len(rule) if isinstance(rule, Rule) else None
    if not isinstance(rule, Rule) or rule_length != n or not valid_trials:
        return BacktestResult(
            status="error",
            reason=f"invalid backtest input: close={n}, rule={rule_length}, nTrials={nTrials}",
            style=style,
        )

    normalized: dict[str, np.ndarray | None] = {}
    for name, raw in (("open_", open_), ("high", high), ("low", low), ("volume", volume)):
        if raw is None:
            normalized[name] = None
            continue
        try:
            values = np.asarray(raw, dtype=np.float64)
        except (TypeError, ValueError):
            return BacktestResult(status="error", reason=f"invalid {name}: numeric series required", style=style)
        valid_values = np.all(np.isfinite(values)) and (np.all(values >= 0) if name == "volume" else np.all(values > 0))
        if values.ndim != 1 or len(values) != n or not valid_values:
            return BacktestResult(
                status="error",
                reason=f"invalid {name}: expected {n} finite {'nonnegative' if name == 'volume' else 'positive'} values",
                style=style,
            )
        normalized[name] = values
    open_ = normalized["open_"]
    high = normalized["high"]
    low = normalized["low"]
    volume = normalized["volume"]

    def _materiallyBelow(upper: np.ndarray, lower: np.ndarray) -> np.ndarray:
        return (upper < lower) & ~np.isclose(upper, lower, rtol=1e-4, atol=1e-8)

    def _materiallyAbove(lower: np.ndarray, upper: np.ndarray) -> np.ndarray:
        return (lower > upper) & ~np.isclose(lower, upper, rtol=1e-4, atol=1e-8)

    if high is not None and (
        np.any(_materiallyBelow(high, close)) or (open_ is not None and np.any(_materiallyBelow(high, open_)))
    ):
        return BacktestResult(status="error", reason="invalid OHLC: high below open/close", style=style)
    if low is not None and (
        np.any(_materiallyAbove(low, close)) or (open_ is not None and np.any(_materiallyAbove(low, open_)))
    ):
        return BacktestResult(status="error", reason="invalid OHLC: low above open/close", style=style)
    if high is not None and low is not None and np.any(high < low):
        return BacktestResult(status="error", reason="invalid OHLC: high below low", style=style)
    if dates is not None:
        if len(dates) != n:
            return BacktestResult(status="error", reason=f"invalid dates: expected {n} values", style=style)
        dateKeys: list[tuple[str, object] | None] = []
        for value in dates:
            if isinstance(value, date):
                dateKeys.append(("date", value.isoformat()))
            elif isinstance(value, np.datetime64):
                dateKeys.append(("date", np.datetime_as_string(value)))
            elif isinstance(value, str):
                dateKeys.append(("text", value))
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(value):
                dateKeys.append(("number", float(value)))
            else:
                dateKeys.append(None)
        sameKind = bool(dateKeys) and all(key is not None and key[0] == dateKeys[0][0] for key in dateKeys)
        strictly_increasing = bool(sameKind and all(dateKeys[idx][1] < dateKeys[idx + 1][1] for idx in range(n - 1)))
        if not strictly_increasing:
            return BacktestResult(status="error", reason="invalid dates: strict ascending order required", style=style)
    try:
        costs = np.asarray([feeBps, slipBps, impactBpsPerPct, capitalPctOfAdv], dtype=np.float64)
    except (TypeError, ValueError):
        return BacktestResult(status="error", reason="invalid cost inputs: numeric values required", style=style)
    if not np.all(np.isfinite(costs)) or np.any(costs < 0):
        return BacktestResult(
            status="error", reason="invalid cost inputs: finite nonnegative values required", style=style
        )
    if execMode not in {"next_open", "close"}:
        return BacktestResult(status="error", reason=f"invalid execMode: {execMode}", style=style)
    if rule.stop and (high is None or low is None):
        return BacktestResult(status="error", reason="stop contract requires high and low series", style=style)

    sizing_series, sizing_error = _buildSizingSeries(close, rule.sizing)
    if sizing_error is not None:
        return BacktestResult(status="error", reason=sizing_error, style=style)
    max_one_side_cost = (
        (feeBps + slipBps + capitalPctOfAdv * float(np.max(sizing_series)) * impactBpsPerPct) / 1e4 / 2.0
    )
    if max_one_side_cost >= 1.0:
        return BacktestResult(
            status="error", reason="invalid cost inputs: one-side cost must stay below 100%", style=style
        )

    # 체결 가격 선택
    if execMode == "close":
        exec_price = close
    else:
        exec_price = open_ if open_ is not None else close

    base_cost = (feeBps + slipBps) / 1e4 / 2.0  # 한쪽

    # ADV impact (거래량 비례)
    def _impactCost(size: float) -> float:
        """명시한 ADV 대비 전액 주문 비율을 실제 position size로 축소한다."""
        if capitalPctOfAdv <= 0:
            return 0.0
        return (capitalPctOfAdv * size * impactBpsPerPct) / 1e4 / 2.0

    def _exitExposure(rawPrice: float) -> float:
        """진입 후 가격 drift를 반영한 청산 직전 gross exposure."""
        gross_asset = entry_size * rawPrice / entry_price
        equity_before_exit = (1.0 - entry_size) + gross_asset
        return gross_asset / equity_before_exit if equity_before_exit > 0 else entry_size

    in_pos = False
    entry_idx = -1
    entry_raw_price = 0.0
    entry_price = 0.0
    entry_cost = 0.0
    entry_size = 0.0
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
                exit_cost = base_cost + _impactCost(_exitExposure(float(exit_raw)))
                exit_price = exit_raw * (1 - exit_cost)
                asset_pnl = (exit_price - entry_price) / entry_price
                pnl = entry_size * asset_pnl
                trades.append(
                    {
                        "entry_idx": entry_idx,
                        "exit_idx": exit_t,
                        "entry_date": str(dates[entry_idx]) if dates is not None else None,
                        "exit_date": str(dates[exit_t]) if dates is not None else None,
                        "entry_raw": entry_raw_price,
                        "exit_raw": exit_raw,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "size": entry_size,
                        "asset_pnl": asset_pnl,
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
            signal_size = float(sizing_series[t])
            if signal_size <= 0:
                continue
            entry_raw = exec_price[t + 1] if execMode != "close" else close[t]
            entry_cost = base_cost + _impactCost(signal_size)
            entry_raw_price = float(entry_raw)
            entry_price = entry_raw * (1 + entry_cost)
            entry_idx = t + 1 if execMode != "close" else t
            entry_size = signal_size
            in_pos = True

    # 마지막 봉 청산 (열린 포지션 강제 마감)
    if in_pos:
        exit_raw = float(close[-1])
        exit_cost = base_cost + _impactCost(_exitExposure(exit_raw))
        exit_price = exit_raw * (1 - exit_cost)
        asset_pnl = (exit_price - entry_price) / entry_price
        pnl = entry_size * asset_pnl
        trades.append(
            {
                "entry_idx": entry_idx,
                "exit_idx": n - 1,
                "entry_date": str(dates[entry_idx]) if dates is not None else None,
                "exit_date": str(dates[n - 1]) if dates is not None else None,
                "entry_raw": entry_raw_price,
                "exit_raw": exit_raw,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "size": entry_size,
                "asset_pnl": asset_pnl,
                "pnl": pnl,
                "bars_held": n - 1 - entry_idx,
                "exit_reason": "force_close",
                "cost_bps": (entry_cost + exit_cost) * 1e4,
            }
        )

    # 거래별 유효 체결가를 단일 원장으로 삼아 EOD wealth 를 재생한다. 비용을 종가
    # 수익률에서 다시 추정하지 않아 trade pnl, returns, equity 가 같은 복리 항등식을 쓴다.
    daily_ret, equity, pos, to = _replayTrades(close, trades)
    if not np.all(np.isfinite(equity)) or np.any(equity <= 0):
        return BacktestResult(status="error", reason="portfolio equity depleted under sizing leverage", style=style)

    # trades DataFrame
    trades_df = (
        pl.DataFrame(trades)
        if trades
        else pl.DataFrame(
            schema={
                "entry_idx": pl.Int64,
                "exit_idx": pl.Int64,
                "entry_date": pl.Utf8,
                "exit_date": pl.Utf8,
                "entry_raw": pl.Float64,
                "exit_raw": pl.Float64,
                "entry_price": pl.Float64,
                "exit_price": pl.Float64,
                "size": pl.Float64,
                "asset_pnl": pl.Float64,
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
    expo = exposure(pos.astype(np.float64))
    average_exposure = float(np.mean(np.abs(pos))) if len(pos) else 0.0
    ds = None if nTrials is None else dsr(sh, daily_ret, nTrials=nTrials)

    period = (None, None)
    if dates is not None and len(dates) >= 2:
        period = (dates[0], dates[-1])
    sizing_method = str((rule.sizing or {}).get("method", "equal"))
    validation = {
        "execution_mode_requested": execMode,
        "execution_mode_effective": "close_fallback" if execMode == "next_open" and open_ is None else execMode,
        "open_fallback": execMode == "next_open" and open_ is None,
        "sizing_method": sizing_method,
        "sizing_semantics": "fixed_at_entry",
        "impact_model": "explicit_adv_ratio_scaled_by_trade_exposure",
    }

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
        averageExposure=average_exposure,
        dsr=ds,
        style=style,
        period=period,
        oos=False,
        validation=validation,
    )


def _replayTrades(close: np.ndarray, trades: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """유효 체결가와 진입 size에서 현금·수량·EOD wealth 원장을 재생한다."""
    n = len(close)
    equity = np.ones(n, dtype=np.float64)
    positions = np.zeros(n, dtype=np.float64)
    last_exit = -1
    turnover = 0.0

    for trade in trades:
        entry = int(trade["entry_idx"])
        exit_ = int(trade["exit_idx"])
        entry_price = float(trade["entry_price"])
        exit_price = float(trade["exit_price"])
        entry_raw = float(trade.get("entry_raw", entry_price))
        exit_raw = float(trade.get("exit_raw", exit_price))
        size = float(trade.get("size", 1.0))
        previous_capital = float(equity[last_exit]) if last_exit >= 0 else 1.0
        if entry > last_exit + 1:
            equity[last_exit + 1 : entry] = previous_capital
        capital = float(equity[entry - 1]) if entry > 0 else 1.0
        units = capital * size / entry_price
        turnover += abs(units * entry_raw) / capital

        if entry == exit_:
            equity[entry] = capital * (1.0 + size * (exit_price / entry_price - 1.0))
            pre_exit_equity = capital * (1.0 - size) + units * exit_raw
            turnover += abs(units * exit_raw) / pre_exit_equity
            last_exit = exit_
            continue

        cash = capital * (1.0 - size)
        for bar in range(entry, exit_):
            equity[bar] = cash + units * float(close[bar])
            if equity[bar] != 0:
                positions[bar] = units * float(close[bar]) / equity[bar]
        equity[exit_] = cash + units * exit_price
        pre_exit_equity = cash + units * exit_raw
        turnover += abs(units * exit_raw) / pre_exit_equity
        last_exit = exit_

    if last_exit + 1 < n:
        equity[last_exit + 1 :] = float(equity[last_exit]) if last_exit >= 0 else 1.0
    previous = np.r_[1.0, equity[:-1]]
    returns = equity / previous - 1.0
    return returns, equity, positions, float(turnover)


def _buildSizingSeries(close: np.ndarray, sizingSpec: dict | None) -> tuple[np.ndarray, str | None]:
    """Rule sizing을 signal-close 시점까지의 정보만 쓰는 position size로 정규화한다."""
    sizes = np.ones(len(close), dtype=np.float64)
    if sizingSpec is None:
        return sizes, None
    if not isinstance(sizingSpec, dict):
        return sizes, "invalid sizing contract: dict required"
    method = sizingSpec.get("method")
    kwargs = sizingSpec.get("kwargs", {})
    if not isinstance(method, str) or not isinstance(kwargs, dict):
        return sizes, "invalid sizing contract: method and kwargs required"

    key = method.strip().lower()
    if key == "equal":
        return sizes, None
    if key == "fixed":
        try:
            weight = float(kwargs.get("weight"))
        except (TypeError, ValueError):
            return sizes, "invalid fixed sizing: weight required"
        if not 0.0 <= weight <= 1.0:
            return sizes, "invalid fixed sizing: weight must be between 0 and 1"
        sizes.fill(weight)
        return sizes, None
    if key == "kelly":
        win_prob = kwargs.get("winProb", kwargs.get("p"))
        win_loss = kwargs.get("winLossRatio", kwargs.get("b"))
        fraction = kwargs.get("fraction", kwargs.get("k", 1.0))
        try:
            win_prob = float(win_prob)
            win_loss = float(win_loss)
            fraction = float(fraction)
        except (TypeError, ValueError):
            return sizes, "invalid kelly sizing: winProb and winLossRatio required"
        if not (0.0 < win_prob < 1.0) or win_loss <= 0 or not (0.0 <= fraction <= 1.0):
            return sizes, "invalid kelly sizing parameters"
        full = (win_prob * win_loss - (1.0 - win_prob)) / win_loss
        sizes.fill(max(0.0, min(1.0, full * fraction)))
        return sizes, None

    if key in {"vol_target", "risk_budget"}:
        return sizes, f"unsupported sizing method: {method}; use {method}_at_entry for fixed trade sizing"
    if key not in {"vol_target_at_entry", "risk_budget_at_entry"}:
        return sizes, f"unknown sizing method: {method}"

    target_keys = (
        ("targetVol", "target", "target_vol")
        if key == "vol_target_at_entry"
        else ("riskBudget", "target", "risk_budget")
    )
    target = next((kwargs[name] for name in target_keys if name in kwargs), 0.10)
    window = kwargs.get("window", 60)
    min_periods = kwargs.get("minPeriods", kwargs.get("min_periods", 30))
    max_leverage = kwargs.get("maxLeverage", kwargs.get("max_leverage", 1.0))
    try:
        target = float(target)
        window = int(window)
        min_periods = int(min_periods)
        max_leverage = float(max_leverage)
    except (TypeError, ValueError):
        return sizes, f"invalid {key} sizing parameters"
    if target <= 0 or window < 2 or min_periods < 2 or min_periods > window or not 0 < max_leverage <= 1:
        return sizes, f"invalid {key} sizing: window/minPeriods/target/maxLeverage"

    sizes.fill(0.0)
    for idx in range(1, len(close)):
        start = max(0, idx - window)
        history = close[start : idx + 1]
        history_returns = history[1:] / history[:-1] - 1.0
        if len(history_returns) < min_periods:
            continue
        realized_vol = float(np.std(history_returns, ddof=1) * np.sqrt(252.0))
        if realized_vol > 0 and np.isfinite(realized_vol):
            sizes[idx] = min(max_leverage, target / realized_vol)
    return sizes, None


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
