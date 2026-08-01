"""quant/strategy/backtest.py 고급 백테스트 분리 — walkForward · multiAsset · cpcv.

backtest.py 773 줄 분할. walkForward (206) + multiAssetBacktest (146) + cpcv (74)
약 426 줄. backtest.py 의 facade (BacktestResult dataclass + vectorBacktest 단일
백테스트 + _buildStopSeries) 책임 유지.

BC: strategy.backtest 모듈에서 3 함수 모두 import 가능 (re-export).
순환 import 회피: vectorBacktest · _buildStopSeries · BacktestResult 는 함수 내부 lazy import.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import numpy as np
import polars as pl

from dartlab.core.polarsUtil import isEmptyDf

if TYPE_CHECKING:
    from dartlab.quant.strategy.backtest import BacktestResult

from .metrics import (
    cpcvSplits,
    dsr,
    mdd,
    pbo,
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
) -> "BacktestResult":
    """Walk-forward OOS 백테스트.

    Sliding window 로 train(IS) → test(OOS) 반복. test 구간 수익률만 누적해서
    OOS Sharpe/MDD/DSR 계산. PBO 는 segments 비교로 산출.

    Capabilities:
        - 슬라이딩 train/test/step → OOS 누적 수익률 + segment 별 sharpe → PBO
        - 정적 Rule 또는 dynamic ruleFactory (IS fit + OOS predict) 지원

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

    Returns:
        BacktestResult — ``oos=True``, ``pbo`` 채워짐.

    Guide:
        Lopez de Prado AFML 표준. train=252 (1 년) + test=63 (1 분기) + step=63 (분기 회전).
        PBO ≥ 0.5 = 과적합 의심.

    When:
        OOS 견고성 검정 + AI 과적합 답변.

    How:
        for start in range(0, n-train-test, step): IS fit (정적 또는 factory) → OOS
        backtest → 수익률 누적 → BacktestResult 합성.

    Requires:
        close 길이 ≥ train + test.

    Raises:
        없음.

    See Also:
        - vectorBacktest : in-sample
        - cpcv : Combinatorial Purged CV
        - strategy.metrics.pbo : 산출

    AIContext:
        "OOS 검정 결과" 답변 시 OOS sharpe + pbo + segments 인용.

    Notes
    -----
    rule_factory 사용 예 (forecast 모델 OOS 검증):

    >>> def factory(is_close, oos_len):
    ...     # IS 에서 forecast 모델 fit, 다음 oos_len 일 entry/exit 예측
    ...     fcst = forecast_model.fit(is_close).predict(oos_len)
    ...     entry = np.zeros(len(is_close) + oos_len, dtype=bool)
    ...     entry[len(is_close):] = fcst > threshold  # OOS 만 entry
    ...     exit_ = np.zeros_like(entry)
    ...     return Rule(entry_expr=entry, exit_expr=exit_)
    ...
    >>> walkForward(close, rule=None, rule_factory=factory, train=252, test=63)
    """
    if rule is None and ruleFactory is None:
        return _BacktestResult(
            status="error",
            reason="rule 또는 rule_factory 중 하나 필수",
            style=style,
            oos=True,
        )

    n = len(close)
    if n < train + test:
        return _BacktestResult(
            status="error",
            reason=f"insufficient data for walk-forward: n={n}, need {train + test}",
            style=style,
            oos=True,
        )

    is_sharpes: list[float] = []
    oos_sharpes: list[float] = []
    oos_returns_all: list[np.ndarray] = []
    refit_count = 0

    start = 0
    while start + train + test <= n:
        is_end = start + train
        oos_end = is_end + test
        isClose = close[start:is_end]
        oos_close = close[is_end:oos_end]

        if ruleFactory is not None:
            # IS 마다 재학습 — Rule length 는 train+test 이어야 함 (IS+OOS 일관)
            try:
                fold_rule = ruleFactory(isClose, test)
            except Exception as exc:  # noqa: BLE001
                return _BacktestResult(
                    status="error",
                    reason=f"rule_factory 호출 실패 (fold start={start}): {type(exc).__name__}: {exc}",
                    style=style,
                    oos=True,
                )
            if not isinstance(fold_rule, Rule) or len(fold_rule) != train + test:
                return _BacktestResult(
                    status="error",
                    reason=f"rule_factory 반환 Rule length 가 train+test ({train + test}) 와 불일치",
                    style=style,
                    oos=True,
                )
            refit_count += 1
            is_rule = Rule(
                entry_expr=fold_rule.entry_expr[:train],
                exit_expr=fold_rule.exit_expr[:train],
                sizing=fold_rule.sizing,
                stop=fold_rule.stop,
                meta=fold_rule.meta,
            )
            oos_rule = Rule(
                entry_expr=fold_rule.entry_expr[train:],
                exit_expr=fold_rule.exit_expr[train:],
                sizing=fold_rule.sizing,
                stop=fold_rule.stop,
                meta=fold_rule.meta,
            )
        else:
            # 정적 rule 슬라이스 (기존 동작)
            is_rule = Rule(
                entry_expr=rule.entry_expr[start:is_end],
                exit_expr=rule.exit_expr[start:is_end],
                sizing=rule.sizing,
                stop=rule.stop,
                meta=rule.meta,
            )
            oos_rule = Rule(
                entry_expr=rule.entry_expr[is_end:oos_end],
                exit_expr=rule.exit_expr[is_end:oos_end],
                sizing=rule.sizing,
                stop=rule.stop,
                meta=rule.meta,
            )

        is_bt = _vectorBacktest(
            isClose,
            is_rule,
            open_=open_[start:is_end] if open_ is not None else None,
            high=high[start:is_end] if high is not None else None,
            low=low[start:is_end] if low is not None else None,
            feeBps=feeBps,
            slipBps=slipBps,
        )
        is_sharpes.append(is_bt.sharpe)

        oos_bt = _vectorBacktest(
            oos_close,
            oos_rule,
            open_=open_[is_end:oos_end] if open_ is not None else None,
            high=high[is_end:oos_end] if high is not None else None,
            low=low[is_end:oos_end] if low is not None else None,
            feeBps=feeBps,
            slipBps=slipBps,
        )
        oos_sharpes.append(oos_bt.sharpe)
        oos_returns_all.append(oos_bt.returns)

        start += step

    if not oos_returns_all:
        return _BacktestResult(
            status="error",
            reason="no walk-forward folds",
            style=style,
            oos=True,
        )

    aggregated_returns = np.concatenate(oos_returns_all)
    equity = np.cumprod(1.0 + aggregated_returns)

    sh = sharpe(aggregated_returns)
    so = sortino(aggregated_returns)
    md = mdd(equity)
    ds = dsr(sh, aggregated_returns, nTrials=len(oos_sharpes))

    # PBO: IS 가 [trial=1, segment=k], OOS 도 동일.
    # rule_factory path 에서는 IS region 이 보통 학습용 (entry/exit 모두 False) 이라
    # IS sharpe = 0 → IS vs OOS 비교 무의미 → PBO 1.0 은 가짜. None 으로 표시.
    if refit_count > 0:
        pbo_val = None
    else:
        is_mat = np.array([is_sharpes])
        oos_mat = np.array([oos_sharpes])
        pbo_val = pbo(is_mat, oos_mat)

    period = (None, None)
    if dates and len(dates) >= 2:
        period = (dates[0], dates[-1])

    return _BacktestResult(
        equity=equity,
        returns=aggregated_returns,
        positions=np.array([], dtype=np.float64),
        trades=None,
        sharpe=sh,
        sortino=so,
        mdd=md,
        dsr=ds,
        pbo=pbo_val,
        style=style,
        period=period,
        oos=True,
        cpcv={
            "is_sharpes": is_sharpes,
            "oos_sharpes": oos_sharpes,
            "n_folds": len(oos_sharpes),
            "refit_count": refit_count,
        },
    )


def multiAssetBacktest(
    stockCodes: list[str],
    ruleBuilder,
    *,
    weighting: str = "equal",
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
    style: str | None = None,
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
    ds = dsr(sh, portfolio_ret, nTrials=n_assets)

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
    style: str | None = None,
    feeBps: float = DEFAULT_FEE_BPS,
    slipBps: float = DEFAULT_SLIP_BPS,
) -> "BacktestResult":
    """Combinatorial Purged Cross-Validation 백테스트 (Lopez AFML).

    n_splits 개 그룹 → n_test 개 조합 모두 test. 각 조합의 OOS Sharpe 평균 + DSR.

    Capabilities:
        - C(nSplits, nTest) 모든 조합 → 각 fold OOS sharpe → 평균 + DSR
        - embargo 로 train/test 경계 purge → look-ahead bias 회피

    Args:
        close: 가격 시계열.
        rule: Rule 객체.
        nSplits: 분할 수. 기본 ``6``.
        nTest: test 그룹 수. 기본 ``2``.
        embargo: test 양 끝 purge 관측치. 기본 ``5``.
        open_/high/low: 보조 OHLC.
        style: 메타.
        feeBps: 왕복 수수료 bps.
        slipBps: 왕복 슬리피지 bps.

    Returns:
        BacktestResult — ``oos=True``, ``cpcv`` 메타 채워짐.

    Guide:
        Lopez de Prado AFML Ch.7. walkForward 보다 더 많은 OOS 조합 → 안정적 DSR.
        nSplits=6, nTest=2 → 15 조합.

    When:
        과적합 검정 강건성 + AI DSR 답변.

    How:
        ``cpcvSplits`` 로 모든 (train, test) 조합 생성 → fold 별 OOS backtest → sharpe 평균.

    Requires:
        close 충분히 길어야 (fold ≥ 6).

    Raises:
        없음 — 조합 0 시 error sentinel.

    See Also:
        - walkForward : sliding window
        - strategy.metrics.cpcvSplits : split 생성

    Example:
        >>> r = cpcv(close, rule, nSplits=6, nTest=2)
        >>> r.cpcv["fold_count"]
        15

    AIContext:
        "CPCV 견고성" 답변 시 fold 별 sharpe + DSR 인용.
    """
    n = len(close)
    fold_sharpes: list[float] = []
    fold_returns: list[np.ndarray] = []

    for train_idx, test_idx in cpcvSplits(n, nSplits, nTest, embargo):
        if len(test_idx) < 30:
            continue
        sub_close = close[test_idx]
        sub_rule = Rule(
            entry_expr=rule.entry_expr[test_idx],
            exit_expr=rule.exit_expr[test_idx],
            sizing=rule.sizing,
            stop=rule.stop,
            meta=rule.meta,
        )
        sub_bt = _vectorBacktest(
            sub_close,
            sub_rule,
            open_=open_[test_idx] if open_ is not None else None,
            high=high[test_idx] if high is not None else None,
            low=low[test_idx] if low is not None else None,
            feeBps=feeBps,
            slipBps=slipBps,
        )
        fold_sharpes.append(sub_bt.sharpe)
        fold_returns.append(sub_bt.returns)

    if not fold_returns:
        return _BacktestResult(status="error", reason="no cpcv folds", style=style, oos=True)

    aggregated = np.concatenate(fold_returns)
    equity = np.cumprod(1.0 + aggregated)
    sh = sharpe(aggregated)
    md = mdd(equity)
    ds = dsr(sh, aggregated, nTrials=len(fold_sharpes))

    return _BacktestResult(
        equity=equity,
        returns=aggregated,
        positions=np.array([], dtype=np.float64),
        trades=None,
        sharpe=sh,
        sortino=sortino(aggregated),
        mdd=md,
        dsr=ds,
        style=style,
        oos=True,
        cpcv={"fold_sharpes": fold_sharpes, "n_folds": len(fold_sharpes), "n_splits": nSplits, "n_test": nTest},
    )


# 0.10 BC 깸 — snake_case alias 제거.
