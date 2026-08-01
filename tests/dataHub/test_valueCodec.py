from __future__ import annotations

import polars as pl
import pytest

from dartlab.dataHub import DataQuery, QueryBudget
from dartlab.dataHub.transport import decodeDataResult, encodeDataResult

pytestmark = pytest.mark.unit


def testNestedDataFrameUsesWireCodecForBudgetAndRoundTrip(monkeypatch):
    import dartlab
    from dartlab.analysis.financial import dataAssets

    large = pl.DataFrame({"value": list(range(100_000))})
    monkeypatch.setattr(dataAssets, "simulationInputs", lambda **_kwargs: {"frame": large})
    rejected = dartlab.dataHub(
        "query",
        "analysis.simulationInputs",
        query=DataQuery(subjects=("probe",), budget=QueryBudget(maxBytes=1024)),
    )

    assert rejected.status == "failed"
    assert [gap.code for gap in rejected.gaps] == ["PROJECTION_BYTE_BUDGET"]

    small = pl.DataFrame({"value": [1, 2]})
    monkeypatch.setattr(dataAssets, "simulationInputs", lambda **_kwargs: {"frame": small})
    accepted = dartlab.dataHub(
        "query",
        "analysis.simulationInputs",
        query=DataQuery(subjects=("probe",), budget=QueryBudget(maxBytes=1024 * 1024)),
    )
    restored = decodeDataResult(encodeDataResult(accepted))

    assert restored.status == "ok"
    assert isinstance(restored.partitions[0].data["frame"], pl.DataFrame)
    assert restored.partitions[0].data["frame"].equals(small)


def testUnsupportedNestedObjectFailsBeforeWireEncoding(monkeypatch):
    import dartlab
    from dartlab.analysis.financial import dataAssets

    monkeypatch.setattr(dataAssets, "simulationInputs", lambda **_kwargs: {"opaque": object()})
    result = dartlab.dataHub(
        "query",
        "analysis.simulationInputs",
        query=DataQuery(subjects=("probe",)),
    )

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["PROJECTION_VALUE_UNSUPPORTED"]
