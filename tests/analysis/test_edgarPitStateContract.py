"""Owner and compatibility-contract tests for EDGAR point-in-time state compilation."""

from __future__ import annotations

from datetime import date, timedelta

import polars as pl
import pytest

from dartlab.analysis.financial import edgarPitState as owner
from dartlab.simulate import edgarPitState as compatibility


def makeFiling() -> pl.DataFrame:
    """Build one coherent quarterly filing with four standalone flow periods."""

    stock = {
        "CashAndCashEquivalentsAtCarryingValue": 10.0,
        "AccountsReceivableNetCurrent": 20.0,
        "InventoryNet": 5.0,
        "AccountsPayableCurrent": 15.0,
        "PropertyPlantAndEquipmentNet": 30.0,
        "Assets": 100.0,
        "Liabilities": 60.0,
        "StockholdersEquity": 40.0,
        "LongTermDebtCurrent": 8.0,
        "LongTermDebtNoncurrent": 12.0,
    }
    rows = [
        {
            "namespace": "us-gaap",
            "tag": tag,
            "unit": "USD",
            "val": value,
            "form": "10-Q",
            "filed": "2025-01-30",
            "start": None,
            "end": "2024-12-31",
            "accn": "fixed",
        }
        for tag, value in stock.items()
    ]
    fiscalEnd = date(2024, 12, 31)
    for lag in range(3, -1, -1):
        quarterEnd = fiscalEnd - timedelta(days=91 * lag)
        quarterStart = quarterEnd - timedelta(days=89)
        for tag, value in (
            ("RevenueFromContractWithCustomerExcludingAssessedTax", 100.0),
            ("OperatingIncomeLoss", 20.0),
        ):
            rows.append(
                {
                    "namespace": "us-gaap",
                    "tag": tag,
                    "unit": "USD",
                    "val": value,
                    "form": "10-Q",
                    "filed": "2025-01-30",
                    "start": quarterStart.isoformat(),
                    "end": quarterEnd.isoformat(),
                    "accn": "fixed",
                }
            )
    return pl.DataFrame(rows)


def testCompatibilityShimReexportsOwnerObjects() -> None:
    """The legacy module must expose the exact owner-layer objects."""

    names = (
        "CompiledFinancialState",
        "CompiledQuarterlyFinancialState",
        "EdgarStateError",
        "FactEvidence",
        "QuarterFlow",
        "compileEdgarFinancialState",
        "compileEdgarQuarterlyFinancialState",
    )
    for name in names:
        assert getattr(compatibility, name) is getattr(owner, name)


def testOwnerKeepsFixedPointInTimeBehavior() -> None:
    """The owner compiler must preserve the established reduced-state result."""

    compiled = owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250228")
    assert compiled.state.cash == 10.0
    assert compiled.state.debt == 20.0
    assert compiled.state.revenue == 400.0
    assert compiled.state.operatingMargin == pytest.approx(0.2)
    assert compiled.fiscalThrough == "20241231"
    assert compiled.revisionPolicy == "asKnown"


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("filed", "2025-01-30-extra"),
        ("end", "2024-02-31"),
    ),
)
def testOwnerRejectsMalformedAndImpossibleFactDates(column: str, value: str) -> None:
    """PIT selection must not truncate or normalize invalid source dates."""

    facts = makeFiling().with_columns(pl.lit(value).alias(column))
    with pytest.raises(owner.EdgarStateError, match="EDGAR facts contain invalid dates"):
        owner.compileEdgarFinancialState(facts, knowledgeAsOf="20250228")

    with pytest.raises(owner.EdgarStateError, match="invalid date"):
        owner.compileEdgarFinancialState(makeFiling(), knowledgeAsOf="20250231")
