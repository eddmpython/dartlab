"""Walk-forward 시점 정렬, 연속 체결 원장, 검증 의미 회귀 테스트."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from dartlab.quant.strategy.backtest import BacktestResult
from dartlab.quant.strategy.metrics import dsr, mdd, sharpe
from dartlab.quant.strategy.rule import Rule

pytestmark = pytest.mark.unit


def _emptyRule(n: int) -> Rule:
    return Rule(
        entry_expr=np.zeros(n, dtype=np.bool_),
        exit_expr=np.zeros(n, dtype=np.bool_),
    )


def _factoryWithSignals(*, entry_offsets=(), exit_offsets=()):
    def _factory(is_close, oos_len):
        train = len(is_close)
        entry = np.zeros(train + oos_len, dtype=np.bool_)
        exit_ = np.zeros(train + oos_len, dtype=np.bool_)
        entry[train + np.asarray(entry_offsets, dtype=np.int64)] = True
        exit_[train + np.asarray(exit_offsets, dtype=np.int64)] = True
        return Rule(entry_expr=entry, exit_expr=exit_)

    return _factory


def test_factory_first_forecast_executes_at_first_oos_open():
    """train 종료 시 알 수 있는 첫 forecast를 두 번째 OOS 봉까지 늦추지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 140.0, 120)
    open_ = close + 0.25
    result = walkForward(
        close,
        ruleFactory=_factoryWithSignals(entry_offsets=(0,)),
        train=60,
        test=60,
        step=60,
        open_=open_,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert result.oos is True
    assert result.validation is result.cpcv
    assert result.trades is not None
    assert result.trades.height == 1
    assert result.trades["entry_idx"][0] == 0
    assert result.trades["entry_price"][0] == pytest.approx(open_[60])
    assert result.cpcv["evaluation_mode"] == "walk_forward_refit"


def test_factory_last_forecast_can_execute_on_last_oos_open():
    """마지막 horizon 신호도 vectorBacktest의 next-open 규약에서 소실되지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 140.0, 120)
    open_ = close + 0.5
    result = walkForward(
        close,
        ruleFactory=_factoryWithSignals(entry_offsets=(59,)),
        train=60,
        test=60,
        step=60,
        open_=open_,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert result.trades is not None
    assert result.trades.height == 1
    assert result.trades["entry_idx"][0] == 59
    assert result.trades["exit_idx"][0] == 59
    assert result.trades["entry_price"][0] == pytest.approx(open_[-1])


def test_refit_boundary_carries_position_and_cost_ledger():
    """모델 재학습 경계는 암묵적인 강제청산과 재진입을 만들지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 160.0, 180)
    result = walkForward(
        close,
        ruleFactory=_factoryWithSignals(entry_offsets=(0,)),
        train=60,
        test=60,
        step=60,
        feeBps=20.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert result.cpcv["n_folds"] == 2
    assert result.cpcv["refit_count"] == 2
    assert result.trades is not None
    assert result.trades.height == 1
    assert result.turnover == pytest.approx(100.0 / 100.1 + 1.0)
    assert result.trades["entry_idx"][0] == 0
    assert result.trades["exit_idx"][0] == 119
    assert result.trades["cost_bps"][0] == pytest.approx(20.0)


def test_static_rule_is_stress_not_certified_oos_and_keeps_prior_signal():
    """고정 룰은 OOS로 인증하지 않지만 첫 test 시가 체결 신호는 보존한다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    n = 180
    close = np.linspace(100.0, 160.0, n)
    entry = np.zeros(n, dtype=np.bool_)
    exit_ = np.zeros(n, dtype=np.bool_)
    entry[59] = True
    rule = Rule(entry_expr=entry, exit_expr=exit_)

    result = walkForward(close, rule, train=60, test=60, step=60, feeBps=0.0, slipBps=0.0)

    assert result.status == "ok"
    assert result.oos is False
    assert result.cpcv["evaluation_mode"] == "fixed_rule_rolling_stress"
    assert result.cpcv["refit_count"] == 0
    assert result.trades is not None
    assert result.trades.height == 1
    assert result.trades["entry_idx"][0] == 0


def test_walk_forward_returns_period_and_metrics_share_one_oos_ledger():
    """초기 train과 불완전 tail은 기간과 수익률 원장에 섞이지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    n = 205
    close = np.linspace(100.0, 180.0, n)
    dates = [date(2025, 1, 1) + timedelta(days=idx) for idx in range(n)]
    result = walkForward(
        close,
        ruleFactory=_factoryWithSignals(entry_offsets=(0,), exit_offsets=(30,)),
        train=60,
        test=60,
        step=60,
        dates=dates,
        feeBps=0.0,
        slipBps=0.0,
        nTrials=4,
    )

    assert result.status == "ok"
    assert len(result.returns) == len(result.equity) == len(result.positions) == 120
    assert result.period == (dates[60], dates[179])
    assert result.cpcv["oos_start_index"] == 60
    assert result.cpcv["oos_end_index"] == 179
    assert result.cpcv["remainder_observations"] == 25
    assert result.equity[-1] == pytest.approx(float(np.prod(1.0 + result.returns)))
    assert result.sharpe == pytest.approx(sharpe(result.returns))
    assert result.mdd == pytest.approx(mdd(result.equity))
    assert result.dsr == pytest.approx(dsr(result.sharpe, result.returns, nTrials=4))
    assert result.pbo is None
    assert result.cpcv["pbo_reason"] == "single candidate"
    assert result.cpcv["n_trials"] == 4


def test_walk_forward_dsr_is_unavailable_without_trial_provenance():
    """탐색 횟수를 모를 때 fold 수로 DSR을 꾸며내지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 160.0, 180)
    result = walkForward(
        close,
        ruleFactory=_factoryWithSignals(entry_offsets=(0,)),
        train=60,
        test=60,
        step=60,
    )

    assert result.status == "ok"
    assert result.dsr is None
    assert result.cpcv["n_trials"] is None


def test_walk_forward_fails_closed_when_an_is_fold_fails(monkeypatch):
    """부분 fold 성과를 정상 headline으로 승격하지 않는다."""
    from dartlab.quant.strategy import _backtestAdvanced as advanced

    close = np.linspace(100.0, 160.0, 180)
    calls = 0

    def _failSecondFold(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            return BacktestResult(status="error", reason="fixture failure")
        return BacktestResult(
            equity=np.ones(60),
            returns=np.zeros(60),
            positions=np.zeros(60),
        )

    monkeypatch.setattr(advanced, "_vectorBacktest", _failSecondFold)

    result = advanced.walkForward(
        close,
        ruleFactory=_factoryWithSignals(),
        train=60,
        test=60,
        step=60,
    )

    assert result.status == "error"
    assert result.reason == "walk-forward IS fold 1 failed: fixture failure"
    assert result.cpcv["failed_fold"] == 1
    assert result.cpcv["valid_folds"] == 1


@pytest.mark.parametrize(
    ("train", "test", "step", "n_trials"),
    [
        (29, 60, 60, None),
        (60, 29, 29, None),
        (60, 60, 0, None),
        (60, 60, -1, None),
        (60, 60, 30, None),
        (60, 60, 61, None),
        (60, 60, 60, 0),
    ],
)
def test_walk_forward_rejects_invalid_single_path_contract(train, test, step, n_trials):
    """중복, 공백, 무한루프, 짧은 fold 입력은 실행 전에 error다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 160.0, 180)
    result = walkForward(
        close,
        _emptyRule(len(close)),
        train=train,
        test=test,
        step=step,
        nTrials=n_trials,
    )

    assert result.status == "error"
    assert result.reason.startswith("invalid walk-forward input")


def test_walk_forward_rejects_ambiguous_rule_source():
    """rule과 factory의 조용한 우선순위는 허용하지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    close = np.linspace(100.0, 160.0, 180)
    both = walkForward(
        close,
        _emptyRule(len(close)),
        ruleFactory=_factoryWithSignals(),
        train=60,
        test=60,
        step=60,
    )
    neither = walkForward(close, train=60, test=60, step=60)

    assert both.status == neither.status == "error"
    assert "정확히 하나" in both.reason
    assert "정확히 하나" in neither.reason


def test_public_walkforward_uses_same_start_for_prices_and_style(monkeypatch):
    """공개 축의 가격 기간과 style Rule 형성 기간이 어긋나지 않는다."""
    from dartlab.quant.screen import axStrategy

    n = 180
    close = np.linspace(100.0, 160.0, n)
    arrays = {"close": close, "open": close, "high": close, "low": close}
    calls = []

    def _arrays(stock_code, start=None):
        calls.append(("arrays", stock_code, start))
        return arrays

    def _build(style, stock_code, start=None):
        calls.append(("style", stock_code, start))
        return _emptyRule(n).withMeta(style=style)

    monkeypatch.setattr(axStrategy, "_arrays", _arrays)
    monkeypatch.setattr(axStrategy, "_buildRuleFromStyle", _build)

    result = axStrategy.runWalkforward(
        "TEST",
        style="trendFollow",
        start="2020-01-01",
        train=60,
        test=60,
        step=60,
    )

    assert result.status == "ok"
    assert result.oos is False
    assert calls == [
        ("arrays", "TEST", "2020-01-01"),
        ("style", "TEST", "2020-01-01"),
    ]


def test_fixed_fractional_sizing_survives_the_single_walk_forward_execution_path():
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    n = 180
    close = np.linspace(100.0, 150.0, n)
    entries = np.zeros(n, dtype=np.bool_)
    exits = np.zeros(n, dtype=np.bool_)
    entries[59] = True
    exits[150] = True
    rule = Rule(
        entries,
        exits,
        sizing={"method": "fixed", "kwargs": {"weight": 0.5}},
    )

    result = walkForward(
        close,
        rule,
        train=60,
        test=30,
        step=30,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert result.trades["size"][0] == pytest.approx(0.5)
    assert 0.0 < result.averageExposure < result.exposure


def test_data_dependent_entry_sizing_is_rejected_when_walk_forward_drops_formation_history():
    from dartlab.quant.strategy._backtestAdvanced import walkForward

    n = 180
    close = np.linspace(100.0, 150.0, n)
    entries = np.zeros(n, dtype=np.bool_)
    exits = np.zeros(n, dtype=np.bool_)
    entries[70] = True
    exits[100] = True
    rule = Rule(
        entries,
        exits,
        sizing={
            "method": "vol_target_at_entry",
            "kwargs": {"window": 60, "minPeriods": 30, "targetVol": 0.1},
        },
    )

    result = walkForward(close, rule, train=60, test=30, step=30)

    assert result.status == "error"
    assert "formation history" in (result.reason or "")
