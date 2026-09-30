"""Exact-period cash-flow extraction, revision and missing-data boundaries."""

import polars as pl
import pytest

from dartlab.analysis.financial.edgarPitState import EdgarStateError, compileEdgarPeriodFlows

pytestmark = pytest.mark.unit


def flowRow(value, start, end, filed="2025-07-30", tag="Capex", unit="USD"):
    return {
        "namespace": "us-gaap",
        "tag": tag,
        "unit": unit,
        "val": float(value),
        "form": "10-Q",
        "filed": filed,
        "start": start,
        "end": end,
        "accn": filed,
    }


def readFlows(rows):
    return compileEdgarPeriodFlows(
        pl.DataFrame(rows),
        {"capex": ("Capex", "OldCapex")},
        knowledgeAsOf="20250731",
        fiscalStart="20250401",
        fiscalEnd="20250630",
    )


def testCumulativeFlowsSubtractExactAdjacentPrefix() -> None:
    rows = [flowRow(12, "2025-01-01", "2025-06-30"), flowRow(5, "2025-01-01", "2025-03-31", "2025-04-30")]
    result = readFlows(rows)[0]
    assert result.value == 7 and result.status == "derived"
    assert result.fiscalStart == "20250401" and result.fiscalEnd == "20250630"
    assert len(result.derivationInputs) == 2
    assert readFlows(list(reversed(rows))) == (result,)


def testObservedZeroIsKept() -> None:
    result = readFlows([flowRow(0, "2025-04-01", "2025-06-30")])[0]
    assert result.value == 0 and result.status == "observed"


@pytest.mark.parametrize(
    "prefix",
    [
        flowRow(5, "2025-01-01", "2025-03-30", "2025-04-30"),
        flowRow(5, "2025-01-01", "2025-03-31", "2025-08-01"),
        flowRow(5, "2025-01-01", "2025-03-31", "2025-04-30", tag="OldCapex"),
    ],
)
def testMissingOrIncompatiblePrefixStaysMissing(prefix) -> None:
    assert readFlows([flowRow(12, "2025-01-01", "2025-06-30"), prefix]) == ()


def testLatestRevisionCannotFallBackToOlderStandaloneValue() -> None:
    rows = [
        flowRow(7, "2025-04-01", "2025-06-30", "2025-07-20"),
        flowRow(15, "2025-01-01", "2025-06-30"),
        flowRow(5, "2025-01-01", "2025-03-31", "2025-04-30"),
    ]
    assert readFlows(rows)[0].value == 10
    assert readFlows(rows[:-1]) == ()


def testConflictingLatestValuesAndCurrencyAreRejected() -> None:
    with pytest.raises(EdgarStateError, match="conflicting"):
        readFlows([flowRow(7, "2025-04-01", "2025-06-30"), flowRow(8, "2025-04-01", "2025-06-30")])
    with pytest.raises(EdgarStateError, match="unit conflict"):
        readFlows([flowRow(7, "2025-04-01", "2025-06-30", unit="EUR")])
