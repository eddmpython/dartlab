from __future__ import annotations

import pytest

from dartlab.analysis.financial.stepProjection import (
    FinancialAction,
    FinancialParameters,
    FinancialShock,
    FinancialState,
    FinancialStepError,
    projectFinancialStep,
)


def _state():
    return FinancialState(
        revenue=100.0,
        operatingMargin=0.15,
        cash=20.0,
        debt=30.0,
        receivables=10.0,
        inventories=10.0,
        payables=10.0,
        ppe=50.0,
        otherNetAssets=0.0,
        equity=50.0,
    )


def _params():
    return FinancialParameters(
        taxRate=0.20,
        depreciationRate=0.10,
        receivablesRatio=0.10,
        payablesRatio=0.10,
        revenuePerPpe=2.2,
        dividendPayout=0.20,
    )


def _shock(growth=0.05, margin=0.0, rate=0.05):
    return FinancialShock(growth, margin, rate)


def _action(capex=0.08, inventory=0.10, borrow=0.0, repay=0.0):
    return FinancialAction(capex, inventory, borrow, repay)


def testEveryStepClosesBalanceSheetAndCashBridge():
    state = _state()
    for _ in range(8):
        result = projectFinancialStep(state, _params(), _shock(), _action())
        assert abs(result.identityResidual) < 1e-8
        assert result.state.cash - state.cash == pytest.approx(result.cashChange)
        assert result.state.ppe == pytest.approx(state.ppe + result.capex - result.depreciation)
        state = result.state


def testNoAutomaticBorrowingWhenCashTurnsNegative():
    stressed = FinancialState(**{**_state().__dict__, "cash": 1.0, "equity": 31.0})
    result = projectFinancialStep(stressed, _params(), _shock(growth=-0.90, margin=-0.8), _action(capex=1.0))
    assert result.state.cash < 0
    assert result.state.debt == stressed.debt


def testFinancingActionChangesCashAndDebtBySameAmount():
    base = projectFinancialStep(_state(), _params(), _shock(), _action())
    financed = projectFinancialStep(_state(), _params(), _shock(), _action(borrow=12.0))
    assert financed.state.cash - base.state.cash == pytest.approx(12.0)
    assert financed.state.debt - base.state.debt == pytest.approx(12.0)
    assert financed.state.equity == pytest.approx(base.state.equity)


def testCapexAffectsCapacityOnlyFromNextStep():
    low = projectFinancialStep(_state(), _params(), _shock(growth=0.5), _action(capex=0.0))
    high = projectFinancialStep(_state(), _params(), _shock(growth=0.5), _action(capex=0.3))
    assert low.state.revenue == high.state.revenue
    low2 = projectFinancialStep(low.state, _params(), _shock(growth=0.5), _action(capex=0.0))
    high2 = projectFinancialStep(high.state, _params(), _shock(growth=0.5), _action(capex=0.0))
    assert high2.capacityRevenue > low2.capacityRevenue
    assert high2.state.revenue > low2.state.revenue


def testInventoryPolicyConsumesCashThroughWorkingCapital():
    lean = projectFinancialStep(_state(), _params(), _shock(), _action(inventory=0.05))
    buffer = projectFinancialStep(_state(), _params(), _shock(), _action(inventory=0.25))
    assert buffer.state.inventories > lean.state.inventories
    assert buffer.state.cash < lean.state.cash


def testMissingOrImpossibleValuesFailLoudly():
    with pytest.raises((FinancialStepError, TypeError, ValueError)):
        projectFinancialStep(_state(), _params(), _shock(rate=None), _action())
    broken = FinancialState(**{**_state().__dict__, "equity": 999.0})
    with pytest.raises(FinancialStepError, match="does not close"):
        projectFinancialStep(broken, _params(), _shock(), _action())
