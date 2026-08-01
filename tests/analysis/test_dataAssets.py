from __future__ import annotations

import pytest

from dartlab.analysis.financial.dataAssets import simulationInputs

pytestmark = pytest.mark.unit


class _Company:
    def __init__(self, value=None, error: Exception | None = None):
        self.value = value
        self.error = error

    def _buildFinanceSeries(self, *, freq: str):
        assert freq == "Q"
        if self.error is not None:
            raise self.error
        return self.value


def testSimulationInputsPropagatesOwnerFailureAndRejectsInvalidPeriod():
    with pytest.raises(AttributeError, match="owner failed"):
        simulationInputs(company=_Company(error=AttributeError("owner failed")))

    with pytest.raises(ValueError, match="형식 오류"):
        simulationInputs(company=_Company(({}, [])), asOf="NOT-A-PERIOD")


@pytest.mark.parametrize("value", (None, ({}, []), ({"income": {}}, [])))
def testSimulationInputsRejectsMissingSeries(value):
    with pytest.raises(ValueError):
        simulationInputs(company=_Company(value))


def testSimulationInputsReturnsCoherentBoundedSeries():
    result = simulationInputs(
        company=_Company(({"income": {"revenue": [1, 2]}}, ["2024-Q3", "2024-Q4"])),
        asOf="2024-Q3",
    )

    assert result == {
        "series": {"income": {"revenue": [1]}},
        "asOf": "2024-Q3",
        "latestAsOf": "2024-Q4",
        "requestedAsOf": "2024-Q3",
    }
