"""Kill tests for EDGAR filing-vintage state compilation."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from dartlab.analysis.financial.stepProjection import FinancialParameters
from dartlab.simulate.edgarPitState import (
    EdgarStateError,
    compileEdgarFinancialState,
    compileEdgarQuarterlyFinancialState,
)
from dartlab.simulate.financialWorld import (
    FinancialWorldInputs,
    buildFinancialPath,
    buildFinancialStrategy,
    runFinancialStrategies,
)


def _filing(accn: str, filed: str, fiscalEnd: str, scale: float = 1.0) -> pl.DataFrame:
    stock = {
        "CashAndCashEquivalentsAtCarryingValue": 10.0,
        "AccountsReceivableNetCurrent": 20.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 15.0,
        "PropertyPlantAndEquipmentGross": 80.0,
        "PropertyPlantAndEquipmentNet": 30.0,
        "Assets": 100.0,
        "Liabilities": 60.0,
        "StockholdersEquity": 40.0,
        "LongTermDebtCurrent": 8.0,
        "LongTermDebtNoncurrent": 12.0,
        "LongTermDebt": 20.0,
    }
    rows = [
        {
            "namespace": "us-gaap",
            "tag": tag,
            "unit": "USD",
            "val": value * scale,
            "form": "10-Q",
            "filed": filed,
            "start": None,
            "end": fiscalEnd,
            "accn": accn,
        }
        for tag, value in stock.items()
    ]
    end = date.fromisoformat(fiscalEnd)
    for lag in range(3, -1, -1):
        qEnd = end - timedelta(days=91 * lag)
        qStart = qEnd - timedelta(days=89)
        for tag, value in (
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 100.0),
            ("OperatingIncomeLoss", 20.0),
        ):
            rows.append(
                {
                    "namespace": "us-gaap",
                    "tag": tag,
                    "unit": "USD",
                    "val": value * scale,
                    "form": "10-Q",
                    "filed": filed,
                    "start": qStart.isoformat(),
                    "end": qEnd.isoformat(),
                    "accn": accn,
                }
            )
    return pl.DataFrame(rows)


def _annualWithNineMonthFlow() -> pl.DataFrame:
    filing = _filing("annual", "2025-01-30", "2024-12-31")
    flow = filing.filter(pl.col("start").is_not_null()).sort("end")
    q4End = flow["end"].max()
    q1Start = flow["start"].min()
    q3End = flow.filter(pl.col("end") < q4End)["end"].max()
    base = filing.filter(pl.col("start").is_null() | (pl.col("end") < q4End))
    annualRows = pl.DataFrame(
        [
            {
                "namespace": "us-gaap",
                "tag": tag,
                "unit": "USD",
                "val": value,
                "form": "10-K",
                "filed": "2025-01-30",
                "start": q1Start,
                "end": "2024-12-31",
                "accn": "annual",
            }
            for tag, value in (
                ("RevenueFromContractWithCustomerExcludingAssessedTax", 430.0),
                ("OperatingIncomeLoss", 86.0),
            )
        ]
    )
    nineMonthRows = pl.DataFrame(
        [
            {
                "namespace": "us-gaap",
                "tag": tag,
                "unit": "USD",
                "val": value,
                "form": "10-Q",
                "filed": "2024-10-30",
                "start": q1Start,
                "end": q3End,
                "accn": "nine-month",
            }
            for tag, value in (
                ("RevenueFromContractWithCustomerExcludingAssessedTax", 300.0),
                ("OperatingIncomeLoss", 60.0),
            )
        ]
    )
    return pl.concat([base, annualRows, nineMonthRows])


def test_cutoff_selects_original_then_amendment_and_future_append_is_invariant() -> None:
    original = _filing("original", "2025-01-30", "2024-12-31")
    amendment = _filing("amendment", "2025-03-15", "2024-12-31", scale=1.1)
    before = compileEdgarFinancialState(original, knowledgeAsOf="20250228")
    withFuture = compileEdgarFinancialState(pl.concat([original, amendment]), knowledgeAsOf="20250228")
    after = compileEdgarFinancialState(pl.concat([original, amendment]), knowledgeAsOf="20250401")
    assert before.stateHash == withFuture.stateHash
    assert before.state.cash == 10.0
    assert after.state.cash == pytest.approx(11.0)
    assert after.stateHash != before.stateHash


def test_net_ppe_wins_and_debt_components_do_not_double_count_reported_total() -> None:
    state = compileEdgarFinancialState(_filing("a", "2025-01-30", "2024-12-31"), knowledgeAsOf="20250228")
    assert state.state.ppe == 30.0
    assert state.state.debt == 20.0
    debt = next(item for item in state.evidence if item.conceptId == "totalDebt")
    assert debt.status == "derived"
    assert "reported total excluded" in debt.derivation


def test_commercial_paper_is_added_to_term_debt_without_using_reported_total_twice() -> None:
    filing = pl.concat(
        [
            _filing("a", "2025-01-30", "2024-12-31"),
            pl.DataFrame(
                [
                    {
                        "namespace": "us-gaap",
                        "tag": "CommercialPaper",
                        "unit": "USD",
                        "val": 3.0,
                        "form": "10-Q",
                        "filed": "2025-01-30",
                        "start": None,
                        "end": "2024-12-31",
                        "accn": "a",
                    }
                ]
            ),
        ]
    )
    state = compileEdgarFinancialState(filing, knowledgeAsOf="20250228")
    assert state.state.debt == 23.0
    debt = next(item for item in state.evidence if item.conceptId == "totalDebt")
    assert "CommercialPaper" in debt.tag


def test_q4_residual_prefers_nine_month_flow_and_ignores_later_revision() -> None:
    facts = _annualWithNineMonthFlow()
    compiled = compileEdgarQuarterlyFinancialState(facts, knowledgeAsOf="20250228")
    latest = compiled.quarters[-1]
    assert latest.revenue.value == 130.0
    assert latest.operatingProfit.value == 26.0
    assert latest.revenue.derivation == "annual minus nine-month year-to-date flow"
    assert compiled.state.revenue == 130.0
    assert compiled.ttmRevenue == 430.0

    revision = facts.filter(pl.col("accn") == "nine-month").with_columns(
        pl.lit("2025-03-01").alias("filed"),
        pl.lit("nine-month-revised").alias("accn"),
        (pl.col("val") + 50.0).alias("val"),
    )
    afterRevision = compileEdgarQuarterlyFinancialState(
        pl.concat([facts, revision]),
        knowledgeAsOf="20250401",
    )
    revisedLatest = afterRevision.quarters[-1]
    assert revisedLatest.revenue.value == latest.revenue.value
    assert revisedLatest.revenue.derivationInputs == latest.revenue.derivationInputs


def test_explicit_fiscal_through_selects_requested_complete_vintage() -> None:
    old = _filing("old", "2025-01-30", "2024-12-31")
    new = _filing("new", "2025-04-30", "2025-03-31", scale=2.0)
    compiled = compileEdgarFinancialState(
        pl.concat([old, new]),
        knowledgeAsOf="20250501",
        fiscalThrough="20241231",
    )
    assert compiled.fiscalThrough == "20241231"
    assert compiled.state.revenue == 400.0
    assert {item.accession for item in compiled.evidence if item.kind == "stock"} == {"old"}


def test_all_stock_accounts_share_one_accession_and_exact_fiscal_end() -> None:
    filing = _filing("a", "2025-01-30", "2024-12-31")
    newer = _filing("b", "2025-04-30", "2025-03-31").filter(
        pl.col("start").is_null() & (pl.col("tag") != "InventoryNet")
    )
    state = compileEdgarFinancialState(pl.concat([filing, newer]), knowledgeAsOf="20250501")
    stock = [item for item in state.evidence if item.kind == "stock"]
    assert state.fiscalThrough == "20241231"
    assert {item.accession for item in stock} == {"a"}
    assert {item.fiscalEnd for item in stock} == {"20241231"}
    assert "latestIncompleteFiling:20250331" in state.warnings


def test_unit_conflict_and_balance_failure_block() -> None:
    filing = _filing("a", "2025-01-30", "2024-12-31")
    conflict = pl.concat(
        [
            filing,
            filing.filter(pl.col("tag") == "Assets").with_columns(pl.lit("EUR").alias("unit")),
        ]
    )
    with pytest.raises(EdgarStateError, match="unit conflict"):
        compileEdgarFinancialState(conflict, knowledgeAsOf="20250228")
    broken = filing.with_columns(
        pl.when(pl.col("tag") == "StockholdersEquity").then(pl.lit(41.0)).otherwise(pl.col("val")).alias("val")
    )
    with pytest.raises(EdgarStateError, match="balance identity"):
        compileEdgarFinancialState(broken, knowledgeAsOf="20250228")


def test_reduced_financial_state_closes_without_stale_or_zero_fill() -> None:
    compiled = compileEdgarFinancialState(_filing("a", "2025-01-30", "2024-12-31"), knowledgeAsOf="20250228")
    state = compiled.state
    identity = (
        state.cash
        + state.receivables
        + state.inventories
        + state.ppe
        + state.otherNetAssets
        - state.payables
        - state.debt
    )
    assert identity == pytest.approx(state.equity)
    assert state.revenue == 400.0
    assert state.latentDemandRevenue == 400.0
    assert state.operatingMargin == pytest.approx(0.2)
    assert compiled.revisionPolicy == "asKnown"


def test_real_aapl_has_distinct_filing_vintage_states_when_store_is_installed() -> None:
    path = Path("data/edgar/finance/0000320193.parquet")
    if not path.exists():
        pytest.skip("AAPL companyfacts store is not installed")
    facts = pl.read_parquet(path)
    old = compileEdgarFinancialState(facts, knowledgeAsOf="20250201")
    current = compileEdgarFinancialState(facts, knowledgeAsOf="20260713")
    currentQuarter = compileEdgarQuarterlyFinancialState(facts, knowledgeAsOf="20260713")
    assert old.fiscalThrough == "20241228"
    assert current.fiscalThrough == "20260328"
    assert old.stateHash != current.stateHash
    assert old.state.revenue < current.state.revenue
    assert current.state.debt == 84_711_000_000.0
    assert currentQuarter.state.revenue == 111_184_000_000.0
    assert currentQuarter.ttmRevenue == 451_442_000_000.0
    assert currentQuarter.state.operatingMargin * currentQuarter.state.revenue == 35_885_000_000.0
    stock = [item for item in current.evidence if item.kind == "stock"]
    assert len({item.accession for item in stock}) == 1
    assert next(item for item in stock if item.conceptId == "netPpe").tag == "PropertyPlantAndEquipmentNet"

    state = current.state
    inputs = FinancialWorldInputs(
        state=state,
        parameters=FinancialParameters(
            taxRate=0.20,
            depreciationRate=0.10,
            receivablesRatio=state.receivables / state.revenue,
            payablesRatio=state.payables / state.revenue,
            revenuePerPpe=state.revenue * 1.10 / state.ppe,
            dividendPayout=0.20,
        ),
        asOf=current.knowledgeAsOf,
        refs=(f"edgarState:{current.stateHash}",),
        warnings=("explicitTransitionParameters",),
    )
    paths = (
        buildFinancialPath(
            "base",
            demandGrowth=(0.03, 0.03),
            marginChange=(0.0, 0.0),
            debtRate=(0.04, 0.04),
        ),
        buildFinancialPath(
            "stress",
            demandGrowth=(-0.10, -0.05),
            marginChange=(-0.02, -0.01),
            debtRate=(0.06, 0.06),
        ),
    )
    baseline = buildFinancialStrategy(
        "preserve",
        capexRatio=(0.08, 0.08),
        inventoryRatio=(state.inventories / state.revenue,) * 2,
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
        isBaseline=True,
    )
    conserve = buildFinancialStrategy(
        "conserve",
        capexRatio=(0.04, 0.04),
        inventoryRatio=(state.inventories / state.revenue,) * 2,
        borrow=(0.0, 0.0),
        repay=(0.0, 0.0),
    )
    run = runFinancialStrategies(
        inputs,
        paths,
        (baseline, conserve),
        debtLimit=state.debt * 1.5,
        maxFinancing=state.debt,
    )
    assert run.decisionStatus == "conditionalOnly"
    assert run.recommendation is None
    assert "explicitTransitionParameters" in run.warnings
    assert len(run.dataVintageHash) == 64
    assert all(abs(step.after["identityResidualRatio"]) < 1e-10 for trace in run.traces for step in trace.steps)
