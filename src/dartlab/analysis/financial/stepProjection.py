"""Pure one-period financial projection with explicit financing actions.\n\nThe leaf closes the cash bridge, PPE roll-forward, debt roll-forward, and a\nreduced balance sheet without a cash plug or automatic borrowing. Every input\nis explicit. Scenario orchestration and strategy comparison remain owned by\n``dartlab.simulate``.\n\nLayer: L2 analysis.\n"""

from __future__ import annotations

import math
from dataclasses import dataclass


class FinancialStepError(ValueError):
    """재무 전이 입력이나 회계 폐합 조건이 유효하지 않을 때 발생한다."""

    pass


@dataclass(frozen=True)
class FinancialState:
    """한 기간 시작점의 축소 재무상태를 보존한다."""

    revenue: float
    operatingMargin: float
    cash: float
    debt: float
    receivables: float
    inventories: float
    payables: float
    ppe: float
    otherNetAssets: float
    equity: float


@dataclass(frozen=True)
class FinancialParameters:
    """기간 전이에 사용하는 명시적 재무 비율과 생산능력 계수를 보존한다."""

    taxRate: float
    depreciationRate: float
    receivablesRatio: float
    payablesRatio: float
    revenuePerPpe: float
    dividendPayout: float


@dataclass(frozen=True)
class FinancialShock:
    """해당 기간에 주입할 수요, 마진, 차입금리 조건을 보존한다."""

    demandGrowth: float
    marginDelta: float
    debtRate: float


@dataclass(frozen=True)
class FinancialAction:
    """해당 기간에 실행할 투자, 재고, 차입, 상환 행동을 보존한다."""

    capexRatio: float
    inventoryRatio: float
    borrow: float
    repay: float


@dataclass(frozen=True)
class FinancialStepResult:
    """다음 재무상태와 회계 폐합을 설명하는 기간별 흐름을 반환한다."""

    state: FinancialState
    demandRevenue: float
    capacityRevenue: float
    capacityBound: bool
    operatingProfit: float
    depreciation: float
    capex: float
    interest: float
    tax: float
    netIncome: float
    dividends: float
    deltaNwc: float
    cfo: float
    cashChange: float
    identityResidual: float


def _checkFinite(name: str, value: float) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise FinancialStepError(f"{name} must be finite")
    return number


def _validate(state: FinancialState, params: FinancialParameters, shock: FinancialShock, action: FinancialAction):
    for obj in (state, params, shock, action):
        for name in obj.__dataclass_fields__:
            _checkFinite(name, getattr(obj, name))
    nonnegative = {
        "revenue": state.revenue,
        "debt": state.debt,
        "receivables": state.receivables,
        "inventories": state.inventories,
        "payables": state.payables,
        "ppe": state.ppe,
        "borrow": action.borrow,
        "repay": action.repay,
    }
    if any(value < 0 for value in nonnegative.values()):
        raise FinancialStepError("stock and financing actions must be nonnegative")
    ratios = (
        params.taxRate,
        params.depreciationRate,
        params.receivablesRatio,
        params.payablesRatio,
        params.dividendPayout,
        action.capexRatio,
        action.inventoryRatio,
        shock.debtRate,
    )
    if any(value < 0 or value > 1 for value in ratios):
        raise FinancialStepError("ratios must be in [0, 1]")
    if params.revenuePerPpe <= 0:
        raise FinancialStepError("revenuePerPpe must be positive")
    if action.repay > state.debt + action.borrow:
        raise FinancialStepError("repayment exceeds available debt")
    initialIdentity = (
        state.cash
        + state.receivables
        + state.inventories
        + state.ppe
        + state.otherNetAssets
        - state.payables
        - state.debt
    )
    tolerance = max(1e-8, abs(state.equity) * 1e-10)
    if abs(initialIdentity - state.equity) > tolerance:
        raise FinancialStepError("initial balance sheet does not close")


def projectFinancialStep(
    state: FinancialState,
    params: FinancialParameters,
    shock: FinancialShock,
    action: FinancialAction,
) -> FinancialStepResult:
    """Project one explicit period without a cash plug or automatic borrowing."""

    _validate(state, params, shock, action)
    demandRevenue = max(0.0, state.revenue * (1.0 + shock.demandGrowth))
    capacityRevenue = state.ppe * params.revenuePerPpe
    revenue = min(demandRevenue, capacityRevenue)
    capacityBound = demandRevenue > capacityRevenue + 1e-12

    operatingMargin = state.operatingMargin + shock.marginDelta
    if operatingMargin < -1 or operatingMargin > 1:
        raise FinancialStepError("operating margin leaves physical range")
    operatingProfit = revenue * operatingMargin
    depreciation = min(state.ppe, state.ppe * params.depreciationRate)
    capex = revenue * action.capexRatio
    ppe = state.ppe + capex - depreciation

    receivables = revenue * params.receivablesRatio
    inventories = revenue * action.inventoryRatio
    payables = revenue * params.payablesRatio
    priorNwc = state.receivables + state.inventories - state.payables
    currentNwc = receivables + inventories - payables
    deltaNwc = currentNwc - priorNwc

    interest = state.debt * shock.debtRate
    ebt = operatingProfit - interest
    tax = max(0.0, ebt * params.taxRate)
    netIncome = ebt - tax
    dividends = max(0.0, netIncome * params.dividendPayout)
    cfo = netIncome + depreciation - deltaNwc

    debt = state.debt + action.borrow - action.repay
    cashChange = cfo - capex - dividends + action.borrow - action.repay
    cash = state.cash + cashChange
    equity = state.equity + netIncome - dividends
    identityEquity = cash + receivables + inventories + ppe + state.otherNetAssets - payables - debt
    identityResidual = identityEquity - equity

    nextState = FinancialState(
        revenue=revenue,
        operatingMargin=operatingMargin,
        cash=cash,
        debt=debt,
        receivables=receivables,
        inventories=inventories,
        payables=payables,
        ppe=ppe,
        otherNetAssets=state.otherNetAssets,
        equity=equity,
    )
    return FinancialStepResult(
        state=nextState,
        demandRevenue=demandRevenue,
        capacityRevenue=capacityRevenue,
        capacityBound=capacityBound,
        operatingProfit=operatingProfit,
        depreciation=depreciation,
        capex=capex,
        interest=interest,
        tax=tax,
        netIncome=netIncome,
        dividends=dividends,
        deltaNwc=deltaNwc,
        cfo=cfo,
        cashChange=cashChange,
        identityResidual=identityResidual,
    )
