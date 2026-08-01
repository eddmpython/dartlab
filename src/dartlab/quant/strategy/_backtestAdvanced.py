"""quant/strategy/backtest.py 고급 백테스트 분리 — walkForward · multiAsset · cpcv.

backtest.py 773 줄 분할. walkForward (206) + multiAssetBacktest (146) + cpcv (74)
약 426 줄. backtest.py 의 facade (BacktestResult dataclass + vectorBacktest 단일
백테스트 + _buildStopSeries) 책임 유지.

BC: strategy.backtest 모듈에서 3 함수 모두 import 가능 (re-export).
순환 import 회피: vectorBacktest · _buildStopSeries · BacktestResult 는 함수 내부 lazy import.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from itertools import combinations
from math import comb
from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.quant.strategy.backtest import BacktestResult

from .metrics import (
    cpcvSplits,
    dsr,
    exposure,
    mdd,
    sharpe,
    sortino,
    winrate,
)
from .rule import Rule

# 본 모듈은 backtest.py 의 facade (vectorBacktest · BacktestResult) 를 참조한다.
# 순환 import 회피로 함수 내부 lazy import + annotation 은 string forward ref.

# 체결/비용 상수 — backtest.py SSOT 와 동기 유지 (default 인자에 사용)
DEFAULT_FEE_BPS = 15.0
DEFAULT_SLIP_BPS = 5.0


def _vectorBacktest(*args, **kwargs):
    """lazy proxy → backtest.vectorBacktest (순환 import 회피)."""
    from dartlab.quant.strategy.backtest import vectorBacktest as _vb

    return _vb(*args, **kwargs)


def _BacktestResult(**kwargs):
    """lazy proxy → backtest.BacktestResult (순환 import 회피)."""
    from dartlab.quant.strategy.backtest import BacktestResult as _Br

    return _Br(**kwargs)


def walkForward(
    close: np.ndarray,
    rule: Rule | None = None,
    *,
    train: int = 252,
    test: int = 63,
    step: int = 63,
    open_: np.ndarray | None = None,
    high: np.ndarray | None = None,
    low: np.ndarray | None = None,
    dates: list | None = None,
    style: str | None = None,
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
    ruleFactory=None,
    nTrials: int | None = None,
) -> "BacktestResult":
    """비중복 walk-forward 경로를 하나의 체결 원장으로 검증한다.

    ``ruleFactory`` 경로만 각 train window에서 다시 적합하므로 ``oos=True``다.
    이미 만들어진 고정 ``Rule``은 같은 구간 구조를 쓰는 temporal stress이며
    ``oos=False``다. 두 모드 모두 ``step == test``를 강제하여 모든 OOS 날짜를
    정확히 한 번 사용하고, fold 신호를 연결한 뒤 전체 OOS 구간을 한 번만 체결한다.

    Capabilities:
        - 비중복 train/test 회전과 ruleFactory 재학습 OOS 경로
        - fold 경계 강제청산 없이 단일 positions/trades/비용 원장
        - 고정 Rule은 OOS로 가장하지 않는 rolling stress 모드
        - DSR의 실제 ``nTrials``와 fold 수 분리, 단일 candidate PBO는 None

    Args:
        close: 가격 시계열.
        rule: 정적 Rule. ruleFactory 가 우선.
        train: in-sample window. 기본 ``252``.
        test: out-of-sample window. 기본 ``63``.
        step: 다음 fold 시작 간격. 기본 ``63``.
        open_/high/low: 보조 OHLC.
        dates: 날짜.
        style: 스타일 이름 메타.
        feeBps: 수수료. 기본 5.
        slipBps: 슬리피지. 기본 5.
        ruleFactory: 동적 Rule 생성기.
        nTrials: 실제 전략/파라미터 탐색 횟수. None이면 DSR 미산출.

    Returns:
        BacktestResult. ruleFactory 경로만 ``oos=True``이며 ``pbo=None``.

    Guide:
        Lopez de Prado AFML 표준. train=252 (1 년) + test=63 (1 분기) + step=63 (분기 회전).
        PBO는 여러 candidate의 IS/OOS 순위 행렬이 필요하므로 이 단일 candidate API에서는
        산출하지 않는다.

    When:
        OOS 견고성 검정 + AI 과적합 답변.

    How:
        fold별 IS fit과 OOS 신호 생성 → 신호 시간순 연결 → 전체 OOS 가격축 단일 backtest.

    Requires:
        train/test 각각 30 이상, ``step == test``, close 길이 ≥ train + test.

    Raises:
        없음.

    See Also:
        - vectorBacktest : in-sample
        - cpcv : 고정 룰 CPCV path 구조 temporal stress
        - strategy.metrics.pbo : 다중 candidate 전용 계산

    AIContext:
        ruleFactory 여부, evaluation_mode, OOS 기간, nTrials를 성과와 함께 인용.

    Notes
    -----
    ruleFactory 사용 예 (forecast 모델 OOS 검증):

    >>> def factory(is_close, oos_len):
    ...     # IS 에서 forecast 모델 fit, 다음 oos_len 일 entry/exit 예측
    ...     fcst = forecast_model.fit(is_close).predict(oos_len)
    ...     entry = np.zeros(len(is_close) + oos_len, dtype=bool)
    ...     entry[len(is_close):] = fcst > threshold  # OOS 만 entry
    ...     exit_ = np.zeros_like(entry)
    ...     return Rule(entry_expr=entry, exit_expr=exit_)
    ...
    >>> walkForward(close, rule=None, ruleFactory=factory, train=252, test=63)
    """
    has_rule = rule is not None
    has_factory = ruleFactory is not None
    is_oos = has_factory
    if has_rule == has_factory:
        return _BacktestResult(
            status="error",
            reason="rule 또는 ruleFactory 중 정확히 하나만 필요",
            style=style,
            oos=is_oos,
        )

    close = np.asarray(close, dtype=np.float64)
    n = len(close)
    aligned = [array for array in (open_, high, low) if array is not None]
    invalid = (
        train < 30
        or test < 30
        or step != test
        or n < train + test
        or any(len(array) != n for array in aligned)
        or (dates is not None and len(dates) != n)
        or (rule is not None and len(rule) != n)
        or (nTrials is not None and nTrials < 1)
    )
    if invalid:
        return _BacktestResult(
            status="error",
            reason=(
                "invalid walk-forward input: "
                f"n={n}, train={train}, test={test}, step={step}, "
                f"rule={len(rule) if rule is not None else None}, nTrials={nTrials}"
            ),
            style=style,
            oos=is_oos,
        )

    evaluation_mode = "walk_forward_refit" if has_factory else "fixed_rule_rolling_stress"
    is_sharpes: list[float] = []
    fold_ranges: list[dict[str, int]] = []
    oos_entries: list[np.ndarray] = []
    oos_exits: list[np.ndarray] = []
    refit_count = 0
    path_sizing = None
    path_stop = None
    path_meta = {}

    start = 0
    while start + train + test <= n:
        fold_number = len(fold_ranges)
        is_end = start + train
        oos_end = is_end + test
        is_close = close[start:is_end]

        if ruleFactory is not None:
            try:
                fold_rule = ruleFactory(is_close, test)
            except Exception as exc:  # noqa: BLE001
                return _BacktestResult(
                    status="error",
                    reason=f"ruleFactory failed at fold {fold_number}: {type(exc).__name__}: {exc}",
                    style=style,
                    oos=True,
                    cpcv={
                        "evaluation_mode": evaluation_mode,
                        "failed_fold": fold_number,
                        "fold_start": start,
                        "valid_folds": fold_number,
                    },
                )
            if not isinstance(fold_rule, Rule) or len(fold_rule) != train + test:
                return _BacktestResult(
                    status="error",
                    reason=f"ruleFactory Rule length must equal train+test ({train + test})",
                    style=style,
                    oos=True,
                    cpcv={
                        "evaluation_mode": evaluation_mode,
                        "failed_fold": fold_number,
                        "fold_start": start,
                        "valid_folds": fold_number,
                    },
                )
            refit_count += 1
            is_rule = Rule(
                entry_expr=fold_rule.entry_expr[:train],
                exit_expr=fold_rule.exit_expr[:train],
                sizing=fold_rule.sizing,
                stop=fold_rule.stop,
                meta=fold_rule.meta,
            )
            fold_oos_entry = fold_rule.entry_expr[train:]
            fold_oos_exit = fold_rule.exit_expr[train:]
        else:
            is_rule = Rule(
                entry_expr=rule.entry_expr[start:is_end],
                exit_expr=rule.exit_expr[start:is_end],
                sizing=rule.sizing,
                stop=rule.stop,
                meta=rule.meta,
            )
            fold_oos_entry = rule.entry_expr[is_end - 1 : oos_end - 1]
            fold_oos_exit = rule.exit_expr[is_end - 1 : oos_end - 1]
            fold_rule = rule

        if fold_number == 0:
            path_sizing = fold_rule.sizing
            path_stop = fold_rule.stop
            path_meta = fold_rule.meta
        elif fold_rule.sizing != path_sizing or fold_rule.stop != path_stop:
            return _BacktestResult(
                status="error",
                reason=f"fold {fold_number} changed sizing or stop contract",
                style=style,
                oos=is_oos,
                cpcv={
                    "evaluation_mode": evaluation_mode,
                    "failed_fold": fold_number,
                    "fold_start": start,
                    "valid_folds": fold_number,
                },
            )

        is_result = _vectorBacktest(
            is_close,
            is_rule,
            open_=open_[start:is_end] if open_ is not None else None,
            high=high[start:is_end] if high is not None else None,
            low=low[start:is_end] if low is not None else None,
            feeBps=feeBps,
            slipBps=slipBps,
            nTrials=None,
        )
        if is_result.status != "ok" or len(is_result.returns) != train:
            return _BacktestResult(
                status="error",
                reason=f"walk-forward IS fold {fold_number} failed: {is_result.reason or is_result.status}",
                style=style,
                oos=is_oos,
                cpcv={
                    "evaluation_mode": evaluation_mode,
                    "failed_fold": fold_number,
                    "fold_start": start,
                    "valid_folds": fold_number,
                },
            )

        is_sharpes.append(float(is_result.sharpe))
        oos_entries.append(np.asarray(fold_oos_entry, dtype=np.bool_))
        oos_exits.append(np.asarray(fold_oos_exit, dtype=np.bool_))
        fold_ranges.append(
            {
                "fold": fold_number,
                "train_start": start,
                "train_end": is_end - 1,
                "test_start": is_end,
                "test_end": oos_end - 1,
            }
        )
        start += step

    if not fold_ranges:
        return _BacktestResult(
            status="error",
            reason="no walk-forward folds",
            style=style,
            oos=is_oos,
        )

    oos_start = fold_ranges[0]["test_start"]
    oos_end = fold_ranges[-1]["test_end"] + 1
    execution_start = oos_start - 1
    path_rule = Rule(
        entry_expr=np.concatenate([np.concatenate(oos_entries), np.zeros(1, dtype=np.bool_)]),
        exit_expr=np.concatenate([np.concatenate(oos_exits), np.zeros(1, dtype=np.bool_)]),
        sizing=path_sizing,
        stop=path_stop,
        meta=path_meta,
    )
    path_dates = dates[execution_start:oos_end] if dates is not None else None
    path_result = _vectorBacktest(
        close[execution_start:oos_end],
        path_rule,
        open_=open_[execution_start:oos_end] if open_ is not None else None,
        high=high[execution_start:oos_end] if high is not None else None,
        low=low[execution_start:oos_end] if low is not None else None,
        dates=path_dates,
        feeBps=feeBps,
        slipBps=slipBps,
        style=style,
        nTrials=nTrials,
    )
    expected_returns = len(fold_ranges) * test
    if path_result.status != "ok" or len(path_result.returns) != expected_returns + 1:
        return _BacktestResult(
            status="error",
            reason=f"walk-forward OOS path failed: {path_result.reason or path_result.status}",
            style=style,
            oos=is_oos,
            cpcv={
                "evaluation_mode": evaluation_mode,
                "failed_fold": None,
                "valid_folds": len(fold_ranges),
                "expected_folds": len(fold_ranges),
            },
        )

    oos_returns = path_result.returns[1:]
    oos_equity = np.cumprod(1.0 + oos_returns)
    oos_positions = path_result.positions[1:]
    oos_trades = (
        path_result.trades.with_columns(
            (pl.col("entry_idx") - 1).alias("entry_idx"),
            (pl.col("exit_idx") - 1).alias("exit_idx"),
        )
        if path_result.trades is not None
        else None
    )
    oos_sharpe = sharpe(oos_returns)
    oos_sortino = sortino(oos_returns)
    oos_mdd = mdd(oos_equity)
    oos_dsr = None if nTrials is None else dsr(oos_sharpe, oos_returns, nTrials=nTrials)
    oos_sharpes = [float(sharpe(oos_returns[offset : offset + test])) for offset in range(0, expected_returns, test)]
    remainder = n - oos_end
    period = (None, None)
    if dates is not None:
        period = (dates[oos_start], dates[oos_end - 1])
    validation = {
        "evaluation_mode": evaluation_mode,
        "is_sharpes": is_sharpes,
        "oos_sharpes": oos_sharpes,
        "n_folds": len(fold_ranges),
        "refit_count": refit_count,
        "train": train,
        "test": test,
        "step": step,
        "n_trials": nTrials,
        "oos_start_index": oos_start,
        "oos_end_index": oos_end - 1,
        "initial_train_observations": train,
        "remainder_observations": remainder,
        "fold_ranges": fold_ranges,
        "pbo_reason": "single candidate",
        "ledger_available": True,
        "boundary_policy": "carry",
        "signal_alignment": "signal_for_oos_day_executes_at_same_day_open",
        "failed_fold": None,
    }
    return replace(
        path_result,
        equity=oos_equity,
        returns=oos_returns,
        positions=oos_positions,
        trades=oos_trades,
        sharpe=oos_sharpe,
        sortino=oos_sortino,
        mdd=oos_mdd,
        exposure=exposure(oos_positions),
        dsr=oos_dsr,
        style=style,
        period=period,
        oos=is_oos,
        pbo=None,
        validation=validation,
        cpcv=validation,
    )


def multiAssetBacktest(
    stockCodes: list[str],
    ruleBuilder,
    *,
    weighting: str = "equal",
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
    style: str | None = None,
    nTrials: int | None = None,
) -> "BacktestResult":
    """멀티 종목 포트폴리오 백테스트.

    각 종목별 단일 백테스트 → 일별 수익률 → 가중 결합.

    Capabilities:
        - 종목별 단일 백테스트 → 일별 returns 매트릭스 → 3 가중방식 (equal/inv_vol/risk_parity) 결합
        - 포트 sharpe/mdd/dsr 산출 + 종목별 contribution

    Args:
        stockCodes: 종목 리스트 (예: ``['005930', '000660', ...]``).
        ruleBuilder: ``callable(company) -> Rule`` (스타일 build 함수).
        weighting: ``"equal"`` | ``"inv_vol"`` | ``"risk_parity"``.
        feeBps: 수수료 bps. 기본 5.
        slipBps: 슬리피지 bps. 기본 5.
        style: 메타 스타일명.
        nTrials: 실제 전략/파라미터 탐색 횟수. None이면 DSR 미산출.

    Returns:
        BacktestResult — 가중 결합 결과.

    Guide:
        분산 효과 + correlation diversification 측정. inv_vol/risk_parity 가 equal 보다
        리스크 분산 균등.

    When:
        멀티 종목 포트 평가 + AI 분산 효과 답변.

    How:
        각 종목 단일 backtest → 종목별 returns → weighting 적용 → 포트 returns → 통계.

    Requires:
        stockCodes ≥ 1 + 종목별 OHLCV 가용.

    Raises:
        없음 — 데이터 부족 시 error sentinel.

    See Also:
        - vectorBacktest : 단일 종목
        - portfolio.allocateERC : risk parity weights

    AIContext:
        "다종목 분산 시 성과" 답변 시 포트 sharpe + weights 인용.
    """
    from dataclasses import dataclass

    from dartlab.quant.screen.dataAccess import fetchOhlcv, ohlcvToArrays

    if not stockCodes:
        return _BacktestResult(status="error", reason="empty stock_codes", style=style)
    if nTrials is not None and nTrials < 1:
        return _BacktestResult(status="error", reason=f"invalid nTrials: {nTrials}", style=style)

    @dataclass
    class _Stub:
        stockCode: str

    # 1) 종목별 백테스트
    individual: dict[str, BacktestResult] = {}
    return_series: dict[str, np.ndarray] = {}
    min_len = float("inf")

    for code in stockCodes:
        ohlcv = fetchOhlcv(code)
        if isEmptyDf(ohlcv):
            continue
        arr = ohlcvToArrays(ohlcv)
        if "close" not in arr or len(arr["close"]) < 60:
            continue
        rule = ruleBuilder(_Stub(stockCode=code))
        if hasattr(rule, "status") and rule.status == "not_applicable":
            continue
        if not isinstance(rule, Rule):
            continue
        if len(rule) != len(arr["close"]):
            continue
        bt = _vectorBacktest(
            arr["close"],
            rule,
            open_=arr.get("open"),
            high=arr.get("high"),
            low=arr.get("low"),
            volume=arr.get("volume"),
            feeBps=feeBps,
            slipBps=slipBps,
        )
        if bt.status != "ok":
            continue
        individual[code] = bt
        return_series[code] = bt.returns
        min_len = min(min_len, len(bt.returns))

    if not individual:
        return _BacktestResult(status="error", reason="no valid backtests", style=style)

    # 2) 길이 정렬 (가장 짧은 종목 기준)
    min_len = int(min_len)
    aligned = np.zeros((len(return_series), min_len), dtype=np.float64)
    codes_ordered = list(return_series.keys())
    for i, code in enumerate(codes_ordered):
        r = return_series[code]
        aligned[i] = r[-min_len:]

    # 3) 가중치 계산
    n_assets = len(codes_ordered)
    if weighting == "equal":
        weights = np.full(n_assets, 1.0 / n_assets, dtype=np.float64)
    elif weighting == "inv_vol":
        vols = np.array([np.std(aligned[i]) for i in range(n_assets)])
        inv = 1.0 / np.maximum(vols, 1e-9)
        weights = inv / inv.sum()
    elif weighting == "risk_parity":
        # ERC 단순화: inv vol 기반 (full ERC 는 portfolio.py 호출)
        vols = np.array([np.std(aligned[i]) for i in range(n_assets)])
        inv = 1.0 / np.maximum(vols, 1e-9)
        weights = inv / inv.sum()
    else:
        return _BacktestResult(status="error", reason=f"unknown weighting: {weighting}", style=style)

    # 4) 포트폴리오 일별 수익률
    portfolio_ret = (weights[:, None] * aligned).sum(axis=0)
    equity = np.cumprod(1.0 + portfolio_ret)

    # 5) 메트릭
    sh = sharpe(portfolio_ret)
    so = sortino(portfolio_ret)
    md = mdd(equity)
    ds = None if nTrials is None else dsr(sh, portfolio_ret, nTrials=nTrials)

    # 모든 trades 합산
    all_trades_list = []
    for code, bt in individual.items():
        if bt.trades is not None and bt.trades.height > 0:
            tdf = bt.trades.with_columns(pl.lit(code).alias("stock_code"))
            all_trades_list.append(tdf)
    all_trades = pl.concat(all_trades_list) if all_trades_list else None

    return _BacktestResult(
        equity=equity,
        returns=portfolio_ret,
        positions=np.array([], dtype=np.float64),
        trades=all_trades,
        sharpe=sh,
        sortino=so,
        mdd=md,
        winrate=winrate(
            np.array(
                [
                    t["pnl"]
                    for code in individual
                    for t in (individual[code].trades.to_dicts() if individual[code].trades is not None else [])
                ],
                dtype=np.float64,
            )
        )
        if individual
        else 0.0,
        dsr=ds,
        style=f"{style}_x{n_assets}" if style else f"multi_x{n_assets}",
        oos=False,
        cpcv={
            "n_assets": n_assets,
            "n_trials": nTrials,
            "codes": codes_ordered,
            "weighting": weighting,
            "weights": weights.tolist(),
            "individual_sharpes": {c: float(individual[c].sharpe) for c in codes_ordered},
        },
    )


def cpcv(
    close: np.ndarray,
    rule: Rule,
    *,
    nSplits: int = 6,
    nTest: int = 2,
    embargo: int = 5,
    open_: np.ndarray | None = None,
    high: np.ndarray | None = None,
    low: np.ndarray | None = None,
    dates: list | None = None,
    style: str | None = None,
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
    nTrials: int | None = None,
) -> "BacktestResult":
    """고정 룰의 CPCV 경로 구조를 이용한 조합 스트레스 백테스트.

    이 API는 이미 만들어진 ``Rule``을 받으므로 fold별 재학습을 수행할 수 없다.
    따라서 결과를 OOS CPCV로 가장하지 않고 ``oos=False``인 고정 룰 스트레스
    결과로 반환한다. 모든 CPCV path는 원래 시간축 전체에서 한 번만 체결해
    비연속 test 구간의 가짜 가격 점프, 강제 청산, 중복 복리를 만들지 않는다.

    Capabilities:
        - C(nSplits, nTest) split을 ``C(nSplits-1, nTest-1)``개 path에 배정
        - path마다 모든 시간 group을 정확히 한 번 사용
        - path별 전체 시간축 단일 체결로 포지션과 비용 원장 보존
        - 실패 path는 Sharpe 0으로 대체하지 않고 전체 결과를 error 처리
        - DSR의 ``nTrials``를 fold 수와 분리

    Args:
        close: 가격 시계열.
        rule: 전체 기간에 미리 정의된 고정 Rule 객체.
        nSplits: 분할 수. 기본 ``6``.
        nTest: test 그룹 수. 기본 ``2``.
        embargo: split train 인덱스 기록용 purge 관측치. 고정 룰에는 학습 효과 없음.
        open_/high/low: 보조 OHLC.
        dates: 전체 path의 기간 메타데이터.
        style: 메타.
        feeBps: 왕복 수수료 bps.
        slipBps: 왕복 슬리피지 bps.
        nTrials: DSR의 실제 전략/파라미터 탐색 횟수. None이면 DSR 미산출.

    Returns:
        BacktestResult. 고정 룰이므로 ``oos=False``이며 path 분포는 ``cpcv``에 기록.

    Guide:
        Lopez de Prado AFML Ch.12의 path 배정 구조를 사용한다. 진정한 OOS CPCV는
        각 split의 train으로 모델을 다시 적합하고 서로 다른 test 예측을 만들어야 한다.
        현재 고정 Rule 계약은 그 정보를 받지 않으므로 temporal stress만 제공한다.

    When:
        고정 룰의 시간 group 조합 구조와 체결 원장 강건성 점검.

    How:
        ``cpcvSplits``와 group 조합을 path에 배정한 뒤 path별 전체 시계열을 한 번씩 backtest.

    Requires:
        close 길이 30 이상, Rule과 OHLC 길이 일치, ``1 <= nTest < nSplits``.

    Raises:
        없음. 잘못된 입력과 path 실패는 error sentinel.

    See Also:
        - walkForward : sliding window
        - strategy.metrics.cpcvSplits : split 생성

    Example:
        >>> r = cpcv(close, rule, nSplits=6, nTest=2)
        >>> (r.cpcv["n_folds"], r.cpcv["n_paths"], r.oos)
        (15, 5, False)

    AIContext:
        고정 룰 결과를 OOS 성과로 부르지 말고 path 분포와 ``mode``를 함께 인용.
    """
    close = np.asarray(close, dtype=np.float64)
    n = len(close)
    aligned = [array for array in (open_, high, low) if array is not None]
    if (
        n < 30
        or len(rule) != n
        or any(len(array) != n for array in aligned)
        or nSplits < 2
        or nTest < 1
        or nTest >= nSplits
        or n < nSplits * 2
        or (nTrials is not None and nTrials < 1)
    ):
        return _BacktestResult(
            status="error",
            reason=(
                "invalid fixed-rule cpcv input: "
                f"n={n}, rule={len(rule)}, nSplits={nSplits}, nTest={nTest}, nTrials={nTrials}"
            ),
            style=style,
            oos=False,
        )

    groups = [np.asarray(group, dtype=np.int64) for group in np.array_split(np.arange(n), nSplits)]
    folds = list(cpcvSplits(n, nSplits, nTest, embargo))
    test_combinations = list(combinations(range(nSplits), nTest))
    n_paths = comb(nSplits - 1, nTest - 1)
    if len(folds) != len(test_combinations) or n_paths < 1:
        return _BacktestResult(
            status="error",
            reason="cpcv split/path construction failed",
            style=style,
            oos=False,
        )

    path_entries = np.zeros((n_paths, n), dtype=np.bool_)
    path_exits = np.zeros((n_paths, n), dtype=np.bool_)
    path_coverage = np.zeros((n_paths, n), dtype=np.bool_)
    group_path_counts = np.zeros(nSplits, dtype=np.int64)
    path_assignments: list[dict[str, int]] = []
    train_sizes: list[int] = []

    for fold_number, ((train_idx, test_idx), group_ids) in enumerate(zip(folds, test_combinations)):
        train_sizes.append(len(train_idx))
        expected_test = np.concatenate([groups[group_id] for group_id in group_ids])
        if not np.array_equal(test_idx, expected_test):
            return _BacktestResult(
                status="error",
                reason=f"cpcv fold {fold_number} group mapping mismatch",
                style=style,
                oos=False,
            )
        for group_id in group_ids:
            path_id = int(group_path_counts[group_id])
            if path_id >= n_paths:
                return _BacktestResult(
                    status="error",
                    reason=f"cpcv group {group_id} exceeds path capacity",
                    style=style,
                    oos=False,
                )
            block = groups[group_id]
            path_entries[path_id, block] = rule.entry_expr[block]
            path_exits[path_id, block] = rule.exit_expr[block]
            path_coverage[path_id, block] = True
            path_assignments.append({"fold": fold_number, "group": group_id, "path": path_id})
            group_path_counts[group_id] += 1

    if not np.all(group_path_counts == n_paths) or not np.all(path_coverage):
        return _BacktestResult(
            status="error",
            reason="cpcv paths do not cover every time group exactly once",
            style=style,
            oos=False,
        )

    path_results = []
    failed_paths: list[dict[str, int | str]] = []
    for path_id in range(n_paths):
        path_rule = Rule(
            entry_expr=path_entries[path_id],
            exit_expr=path_exits[path_id],
            sizing=rule.sizing,
            stop=rule.stop,
            meta=rule.meta,
        )
        path_result = _vectorBacktest(
            close,
            path_rule,
            open_=open_,
            high=high,
            low=low,
            dates=dates,
            feeBps=feeBps,
            slipBps=slipBps,
            style=style,
            nTrials=nTrials,
        )
        if path_result.status != "ok" or len(path_result.returns) != n:
            failed_paths.append(
                {
                    "path": path_id,
                    "reason": path_result.reason or f"returns length {len(path_result.returns)}",
                }
            )
            continue
        path_results.append(path_result)

    if failed_paths:
        return _BacktestResult(
            status="error",
            reason=f"{len(failed_paths)} cpcv paths failed",
            style=style,
            oos=False,
            cpcv={
                "mode": "fixed_rule_path_stress",
                "failed_paths": failed_paths,
                "valid_paths": len(path_results),
                "n_paths": n_paths,
                "n_splits": nSplits,
                "n_test": nTest,
            },
        )

    path_sharpes = [float(result.sharpe) for result in path_results]
    path_mdds = [float(result.mdd) for result in path_results]
    path_terminal_equities = [float(result.equity[-1]) for result in path_results]
    representative = path_results[0]
    identical_paths = all(np.array_equal(result.returns, representative.returns) for result in path_results[1:])
    if not identical_paths:
        return _BacktestResult(
            status="error",
            reason="fixed Rule produced non-identical cpcv paths",
            style=style,
            oos=False,
        )

    validation = {
        "mode": "fixed_rule_path_stress",
        "summary_kind": "identical_full_timeline_paths",
        "interpretation": "temporal stress structure, not fold-refit OOS performance",
        "train_used": False,
        "embargo_effective": False,
        "refit_count": 0,
        "n_trials": nTrials,
        "n_folds": len(folds),
        "n_paths": n_paths,
        "n_splits": nSplits,
        "n_test": nTest,
        "path_observations": n,
        "path_sharpes": path_sharpes,
        "path_mdds": path_mdds,
        "path_terminal_equities": path_terminal_equities,
        "median_path_sharpe": float(np.median(path_sharpes)),
        "q10_path_sharpe": float(np.quantile(path_sharpes, 0.10)),
        "q90_path_sharpe": float(np.quantile(path_sharpes, 0.90)),
        "worst_path_mdd": float(min(path_mdds)),
        "path_assignments": path_assignments,
        "train_sizes": train_sizes,
        "failed_paths": [],
        "ledger_available": True,
    }
    return replace(
        representative,
        style=style,
        oos=False,
        validation=validation,
        cpcv=validation,
    )


# 0.10 BC 깸 — snake_case alias 제거.
