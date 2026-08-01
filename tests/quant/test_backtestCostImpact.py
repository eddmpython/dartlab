"""백테스트 체결, 거래, 수익률, 자산곡선이 하나의 순수익 원장을 쓰는지 검증한다."""

from __future__ import annotations

import numpy as np
import pytest

from dartlab.quant.strategy.backtest import vectorBacktest
from dartlab.quant.strategy.metrics import dsr, mdd, sharpe, sortino
from dartlab.quant.strategy.rule import Rule

pytestmark = pytest.mark.unit


def _setup(n: int = 300) -> tuple[np.ndarray, Rule]:
    """스무 봉마다 진입하고 열 봉 뒤 청산하는 규칙."""

    rng = np.random.default_rng(11)
    close = np.cumprod(1 + rng.normal(0.0002, 0.012, n)) * 10000
    entry = np.zeros(n, dtype=bool)
    exitSignal = np.zeros(n, dtype=bool)
    entry[::20] = True
    exitSignal[10::20] = True
    return close, Rule(entry_expr=entry, exit_expr=exitSignal)


def _run(feeBps: float):
    close, rule = _setup()
    return vectorBacktest(
        close=close,
        rule=rule,
        feeBps=feeBps,
        slipBps=0.0,
        execMode="close",
        nTrials=1,
    )


def _rule(n: int, entries: list[int], exits: list[int], *, stop: dict | None = None) -> Rule:
    entry = np.zeros(n, dtype=bool)
    exitSignal = np.zeros(n, dtype=bool)
    entry[entries] = True
    exitSignal[exits] = True
    return Rule(entry_expr=entry, exit_expr=exitSignal, stop=stop)


def _assertLedgerIdentity(result) -> None:
    assert result.trades is not None
    tradeFactor = float(np.prod(1.0 + result.trades["pnl"].to_numpy()))
    returnFactor = float(np.prod(1.0 + result.returns))
    assert result.equity[-1] == pytest.approx(returnFactor)
    assert result.equity[-1] == pytest.approx(tradeFactor)


def testHigherFeesLowerTheSharpe() -> None:
    """비용을 물린다고 밝혔으면 대표 지표가 그것을 알아야 한다."""

    free = _run(0.0)
    charged = _run(15.0)

    assert charged.sharpe < free.sharpe


def testExtremeFeesDestroyThePerformance() -> None:
    """1000bp 를 물려도 성과가 같다면 비용이 어디에도 닿지 않는 것이다."""

    free = _run(0.0)
    punitive = _run(1000.0)

    assert punitive.sharpe < free.sharpe - 1.0


def testHigherFeesDeepenTheDrawdown() -> None:
    """낙폭도 비용을 반영해야 한다. 자산곡선이 같은 근거에서 나오기 때문이다."""

    free = _run(0.0)
    charged = _run(1000.0)

    assert charged.mdd < free.mdd


def testZeroCostRunIsUnchanged() -> None:
    """비용이 0 이면 예전과 같은 값이어야 한다. 계산 자체를 바꾼 것이 아니다."""

    free = _run(0.0)

    assert free.sharpe == pytest.approx(_run(0.0).sharpe)


def testTradeLevelCostsAreStillRecorded() -> None:
    """거래별 비용 기록은 그대로 남아야 한다. 두 자리가 같은 근거를 쓴다."""

    charged = _run(15.0)

    assert charged.trades is not None
    assert charged.trades.height > 0
    assert charged.trades["cost_bps"].max() > 0


def testConstantPriceRoundTripUsesExactEffectiveFills() -> None:
    """왕복 비용은 두 번 뺄셈이 아니라 실제 매도가를 실제 매수가로 나눈다."""
    n = 40
    close = np.full(n, 100.0)
    result = vectorBacktest(
        close,
        _rule(n, [1], [20]),
        feeBps=1000.0,
        slipBps=0.0,
        execMode="close",
    )

    expected = (1.0 - 0.05) / (1.0 + 0.05)
    assert result.equity[-1] == pytest.approx(expected)
    assert result.trades is not None
    assert result.trades["cost_bps"][0] == pytest.approx(1000.0)
    assert result.turnover == pytest.approx(2.0)
    _assertLedgerIdentity(result)


def testMultipleRoundTripsCompoundFromTheTradeLedger() -> None:
    n = 50
    close = np.full(n, 100.0)
    result = vectorBacktest(
        close,
        _rule(n, [1, 21], [10, 30]),
        feeBps=1000.0,
        slipBps=0.0,
        execMode="close",
    )

    expectedTradeFactor = (1.0 - 0.05) / (1.0 + 0.05)
    assert result.equity[-1] == pytest.approx(expectedTradeFactor**2)
    assert result.turnover == pytest.approx(4.0)
    _assertLedgerIdentity(result)


def testNextOpenEntryAndExitGapsBelongToTheActualHoldingPeriod() -> None:
    """진입 전 갭은 먹지 않고, 보유 중 next-open 청산 갭은 빠짐없이 반영한다."""
    n = 40
    close = np.full(n, 200.0)
    close[0] = 100.0
    close[11:] = 50.0
    open_ = close.copy()
    result = vectorBacktest(
        close,
        _rule(n, [0], [10]),
        open_=open_,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.returns[1] == pytest.approx(0.0)
    assert result.returns[11] == pytest.approx(-0.75)
    assert result.equity[-1] == pytest.approx(0.25)
    _assertLedgerIdentity(result)


def testSameBarEntryAndStopUseOneEffectiveFillRatio() -> None:
    n = 40
    close = np.full(n, 100.0)
    open_ = close.copy()
    high = close.copy()
    low = close.copy()
    low[1] = 94.0
    result = vectorBacktest(
        close,
        _rule(n, [0], [], stop={"method": "fixed_pct", "kwargs": {"pct": 0.05}}),
        open_=open_,
        high=high,
        low=low,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.equity[-1] == pytest.approx(0.95)
    assert result.positions.sum() == pytest.approx(0.0)
    assert result.turnover == pytest.approx(2.0)
    _assertLedgerIdentity(result)


def testGapThroughStopUsesTheOpenInsteadOfAnImpossibleStopFill() -> None:
    n = 40
    close = np.full(n, 100.0)
    open_ = close.copy()
    high = close.copy()
    low = close.copy()
    open_[1] = 90.0
    low[1] = 85.0
    result = vectorBacktest(
        close,
        _rule(n, [0], [], stop={"method": "fixed_pct", "kwargs": {"pct": 0.05}}),
        open_=open_,
        high=high,
        low=low,
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )

    assert result.trades is not None
    assert result.trades["exit_price"][0] == pytest.approx(90.0)
    assert result.equity[-1] == pytest.approx(0.9)
    _assertLedgerIdentity(result)


def testForceCloseEndsInCashAndIncludesTheExitTurnover() -> None:
    n = 40
    close = np.linspace(100.0, 120.0, n)
    result = vectorBacktest(
        close,
        _rule(n, [5], []),
        feeBps=0.0,
        slipBps=0.0,
        execMode="close",
    )

    assert result.trades is not None
    assert result.trades["exit_reason"][0] == "force_close"
    assert result.positions[-1] == pytest.approx(0.0)
    assert result.turnover == pytest.approx(2.0)
    _assertLedgerIdentity(result)


def testReportedMetricsAreRecomputedFromTheReturnedNetSeries() -> None:
    result = _run(15.0)

    assert result.sharpe == pytest.approx(sharpe(result.returns))
    assert result.sortino == pytest.approx(sortino(result.returns))
    assert result.mdd == pytest.approx(mdd(result.equity))
    assert result.dsr == pytest.approx(dsr(result.sharpe, result.returns, nTrials=1))
    _assertLedgerIdentity(result)


def testDsrIsUnavailableWithoutSelectionTrialProvenance() -> None:
    """실제 탐색 횟수를 모르면 단일 trial로 가정해 DSR을 만들지 않는다."""
    close, rule = _setup()

    result = vectorBacktest(close, rule, feeBps=0.0, slipBps=0.0)

    assert result.status == "ok"
    assert result.dsr is None


def testPublicBacktestAxisPassesCostAssumptionsToTheCore(monkeypatch) -> None:
    """공개 quant 축의 비용 kwargs 가 내부 기본값에 먹히지 않고 실제 체결까지 도달한다."""
    import dartlab
    from dartlab.quant.screen import axStrategy

    n = 80
    close = np.full(n, 100.0)
    arrays = {
        "close": close,
        "open": close.copy(),
        "high": close.copy(),
        "low": close.copy(),
        "volume": np.full(n, 1_000_000.0),
    }
    monkeypatch.setattr(axStrategy, "_arrays", lambda stockCode, start=None: arrays)
    rule = _rule(n, [1], [60])

    free = dartlab.quant("backtest", "TEST", style=rule, feeBps=0.0, slipBps=0.0)
    charged = dartlab.quant("backtest", "TEST", style=rule, feeBps=1000.0, slipBps=0.0)

    assert free.equity[-1] == pytest.approx(1.0)
    assert charged.equity[-1] == pytest.approx((1.0 - 0.05) / (1.0 + 0.05))


def testEveryPublicStrategyVariantForwardsCostAssumptions(monkeypatch) -> None:
    from dartlab.quant.screen import axStrategy
    from dartlab.quant.strategy.backtest import BacktestResult

    n = 80
    close = np.full(n, 100.0)
    arrays = {"close": close, "open": close, "high": close, "low": close}
    rule = _rule(n, [1], [60])
    calls: list[tuple[str, float, float]] = []

    def _capture(name):
        def _fake(*args, **kwargs):
            calls.append((name, kwargs["feeBps"], kwargs["slipBps"]))
            return BacktestResult()

        return _fake

    monkeypatch.setattr(axStrategy, "_arrays", lambda stockCode, start=None: arrays)
    monkeypatch.setattr(axStrategy, "vectorBacktest", _capture("strategy"))
    axStrategy.runStrategy("TEST", rule=rule, feeBps=71.0, slipBps=9.0)

    monkeypatch.setattr(axStrategy, "walkForward", _capture("walkforward"))
    axStrategy.runWalkforward(
        "TEST",
        rule=rule,
        train=40,
        test=20,
        feeBps=71.0,
        slipBps=9.0,
    )

    monkeypatch.setattr(axStrategy, "cpcv_fn", _capture("cpcv"))
    axStrategy.runBacktest("TEST", style=rule, cpcv=True, feeBps=71.0, slipBps=9.0)

    monkeypatch.setattr(axStrategy, "multiAssetBacktest", _capture("multi"))
    axStrategy.runMultiAsset(["TEST"], style="trendFollow", feeBps=71.0, slipBps=9.0)

    originalRunBacktest = axStrategy.runBacktest
    monkeypatch.setattr(axStrategy, "runBacktest", _capture("style"))
    axStrategy.runStyle("TEST", name="trendFollow", feeBps=71.0, slipBps=9.0)
    monkeypatch.setattr(axStrategy, "runBacktest", originalRunBacktest)

    assert calls == [
        ("strategy", 71.0, 9.0),
        ("walkforward", 71.0, 9.0),
        ("cpcv", 71.0, 9.0),
        ("multi", 71.0, 9.0),
        ("style", 71.0, 9.0),
    ]
