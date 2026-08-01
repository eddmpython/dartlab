"""고정 룰 CPCV 경로 구조와 공개 의미 회귀 테스트."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from dartlab.quant.strategy.backtest import BacktestResult, vectorBacktest
from dartlab.quant.strategy.metrics import dsr
from dartlab.quant.strategy.rule import Rule

pytestmark = pytest.mark.unit


def _alternatingRule(n: int) -> Rule:
    entry = np.zeros(n, dtype=np.bool_)
    exit_ = np.zeros(n, dtype=np.bool_)
    entry[::40] = True
    exit_[20::40] = True
    return Rule(entry_expr=entry, exit_expr=exit_)


def test_fixed_rule_cpcv_builds_complete_paths_without_claiming_oos():
    """N=6, k=2는 15개 split과 전체 시간축 5개 path를 만든다."""
    from dartlab.quant.strategy._backtestAdvanced import cpcv

    n = 180
    close = 100.0 * np.exp(np.cumsum(np.sin(np.arange(n) / 9.0) * 0.002))
    dates = [date(2025, 1, 1) + timedelta(days=idx) for idx in range(n)]
    result = cpcv(
        close,
        _alternatingRule(n),
        dates=dates,
        nSplits=6,
        nTest=2,
        feeBps=0.0,
        slipBps=0.0,
    )

    assert result.status == "ok"
    assert result.oos is False
    assert result.validation is result.cpcv
    assert result.period == (dates[0], dates[-1])
    assert result.cpcv["mode"] == "fixed_rule_path_stress"
    assert result.cpcv["train_used"] is False
    assert result.cpcv["embargo_effective"] is False
    assert result.cpcv["n_folds"] == 15
    assert result.cpcv["n_paths"] == 5
    assert result.cpcv["path_observations"] == n
    assert len(result.cpcv["path_assignments"]) == 30

    assignments = result.cpcv["path_assignments"]
    assert {(item["group"], item["path"]) for item in assignments} == {
        (group, path) for group in range(6) for path in range(5)
    }
    assert len({(item["fold"], item["group"]) for item in assignments}) == 30


def test_fixed_rule_cpcv_preserves_one_full_timeline_execution_ledger():
    """CPCV가 비연속 test 조각을 이어 붙이지 않고 원 백테스트 원장과 일치한다."""
    from dartlab.quant.strategy._backtestAdvanced import cpcv

    close = np.concatenate(
        [
            np.linspace(100.0, 130.0, 60),
            np.linspace(80.0, 110.0, 60),
            np.linspace(150.0, 120.0, 60),
        ]
    )
    open_ = close * (1.0 + np.sin(np.arange(len(close))) * 0.001)
    rule = _alternatingRule(len(close))

    expected = vectorBacktest(close, rule, open_=open_, feeBps=15.0, slipBps=5.0)
    result = cpcv(close, rule, open_=open_, feeBps=15.0, slipBps=5.0)

    np.testing.assert_array_equal(result.returns, expected.returns)
    np.testing.assert_array_equal(result.equity, expected.equity)
    np.testing.assert_array_equal(result.positions, expected.positions)
    assert result.trades is not None
    assert expected.trades is not None
    assert result.trades.equals(expected.trades)
    assert result.turnover == pytest.approx(expected.turnover)
    assert result.cpcv["ledger_available"] is True
    assert result.cpcv["summary_kind"] == "identical_full_timeline_paths"
    assert result.cpcv["path_sharpes"] == pytest.approx([expected.sharpe] * 5)
    assert result.cpcv["path_mdds"] == pytest.approx([expected.mdd] * 5)


def test_cpcv_path_failure_is_not_relabelled_as_zero_sharpe(monkeypatch):
    """계산 실패 path는 정상 무수익 Sharpe 0과 구분해 전체를 fail closed한다."""
    from dartlab.quant.strategy import _backtestAdvanced as advanced

    n = 180
    close = np.arange(1.0, n + 1.0)
    rule = _alternatingRule(n)
    calls = 0

    def _pathBacktest(*_args, **_kwargs):
        nonlocal calls
        path = calls
        calls += 1
        if path == 2:
            return BacktestResult(status="error", reason="fixture failure")
        returns = np.zeros(n)
        return BacktestResult(
            equity=np.ones(n),
            returns=returns,
            positions=np.zeros(n),
            sharpe=0.0,
        )

    monkeypatch.setattr(advanced, "_vectorBacktest", _pathBacktest)

    result = advanced.cpcv(close, rule)

    assert result.status == "error"
    assert result.reason == "1 cpcv paths failed"
    assert result.cpcv["valid_paths"] == 4
    assert result.cpcv["failed_paths"] == [{"path": 2, "reason": "fixture failure"}]


def test_cpcv_dsr_uses_explicit_trials_not_fold_or_path_count():
    """같은 원장과 탐색 횟수의 DSR은 split/path 개수에 따라 바뀌지 않는다."""
    from dartlab.quant.strategy._backtestAdvanced import cpcv

    n = 240
    close = 100.0 * np.exp(np.cumsum(0.001 + np.sin(np.arange(n) / 8.0) * 0.004))
    rule = _alternatingRule(n)

    six_groups = cpcv(close, rule, nSplits=6, nTest=2, nTrials=3, feeBps=0.0, slipBps=0.0)
    five_groups = cpcv(close, rule, nSplits=5, nTest=2, nTrials=3, feeBps=0.0, slipBps=0.0)

    assert six_groups.status == five_groups.status == "ok"
    np.testing.assert_array_equal(six_groups.returns, five_groups.returns)
    assert six_groups.dsr == pytest.approx(five_groups.dsr)
    assert six_groups.dsr == pytest.approx(dsr(six_groups.sharpe, six_groups.returns, nTrials=3))
    assert six_groups.cpcv["n_trials"] == five_groups.cpcv["n_trials"] == 3
    assert six_groups.cpcv["n_paths"] == 5
    assert five_groups.cpcv["n_paths"] == 4


def test_public_backtest_forwards_cpcv_dates_and_trial_count(monkeypatch):
    """공개 축이 기간 원장과 실제 탐색 횟수를 CPCV core까지 전달한다."""
    from dartlab.quant.screen import axStrategy

    n = 80
    dates = [date(2025, 1, 1) + timedelta(days=idx) for idx in range(n)]
    close = np.linspace(100.0, 120.0, n)
    arrays = {"close": close, "open": close, "high": close, "low": close, "date": dates}
    captured = {}

    def _capture(_close, _rule, **kwargs):
        captured.update(kwargs)
        return BacktestResult()

    monkeypatch.setattr(axStrategy, "_arrays", lambda stockCode, start=None: arrays)
    monkeypatch.setattr(axStrategy, "cpcv_fn", _capture)

    axStrategy.runBacktest("TEST", style=_alternatingRule(n), cpcv=True, nTrials=7)

    assert captured["dates"] == dates
    assert captured["nTrials"] == 7


@pytest.mark.parametrize(
    ("n", "n_splits", "n_test", "n_trials"),
    [
        (29, 6, 2, 1),
        (60, 1, 1, 1),
        (60, 6, 0, 1),
        (60, 6, 6, 1),
        (60, 6, 2, 0),
    ],
)
def test_cpcv_rejects_invalid_path_contract(n, n_splits, n_test, n_trials):
    """완전한 path 또는 DSR 계약을 만들 수 없는 입력은 error다."""
    from dartlab.quant.strategy._backtestAdvanced import cpcv

    close = np.arange(1.0, n + 1.0)
    result = cpcv(
        close,
        _alternatingRule(n),
        nSplits=n_splits,
        nTest=n_test,
        nTrials=n_trials,
    )

    assert result.status == "error"
    assert result.oos is False
    assert result.reason.startswith("invalid fixed-rule cpcv input")
