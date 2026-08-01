from __future__ import annotations

import math

import polars as pl
import pytest

from dartlab.ai.tools.engineCall import _resultToRefs
from dartlab.dataHub.contracts import AssetRef, Coverage, DataPartition, DataResult
from dartlab.simulate.run import SimulationResult

pytestmark = pytest.mark.unit


def _product(engine: str = "analysis") -> dict:
    return {
        "schemaVersion": 1,
        "identity": {"target": "005930", "market": "KR", "engine": engine, "axis": "대표", "version": "1"},
        "time": {
            "asOf": "2026-07-18",
            "dataAsOf": "2025-12-31",
            "period": "2025",
            "knowledgeBoundary": "2026-07-18",
        },
        "status": "usable",
        "conclusion": {"label": "현금창출력 양호", "summary": "영업현금흐름 근거가 확인됩니다."},
        "confidence": {"level": "high", "score": 90.0, "method": "coverage"},
        "drivers": [],
        "evidence": [
            {
                "id": "evidence:cashflow",
                "kind": "value",
                "sourceRef": "table:005930:CF:2025",
                "status": "observed",
            }
        ],
        "assumptions": [],
        "gaps": [{"id": "missing.price", "status": "missing", "reason": "가격 기준점 없음"}],
        "scenarios": [],
        "falsifiers": [],
        "payload": {},
    }


def test_result_to_refs_emits_lens_value_and_date_refs() -> None:
    result = _resultToRefs("Company.analysis", {"product": _product()}, target="005930")
    kinds = [ref.kind for ref in result.refs]

    assert kinds == ["executionRef", "valueRef", "dateRef"]
    value = next(ref for ref in result.refs if ref.kind == "valueRef")
    date = next(ref for ref in result.refs if ref.kind == "dateRef")
    assert value.payload["label"] == "현금창출력 양호"
    assert value.payload["confidence"] == 90.0
    assert value.payload["gaps"][0]["id"] == "missing.price"
    assert value.payload["evidenceRefs"] == ["evidence:cashflow"]
    assert value.payload["provenance"] == ["table:005930:CF:2025"]
    assert date.payload["dataAsOf"] == "2025-12-31"
    execution = next(ref for ref in result.refs if ref.kind == "executionRef")
    assert "result" not in execution.payload


def test_dataclass_result_is_structured_and_surfaces_nested_lens_products() -> None:
    simulation = SimulationResult(
        scenarioName="baseline",
        horizon=3,
        revenuePath=(1.0, 2.0, 3.0),
        marginPath=(10.0, 10.0, 10.0),
        fcfPath=(0.1, 0.2, 0.3),
        proformaYears=3,
        terminalRevenue=3.0,
        dcfPerShare=100.0,
        enterpriseValue=1000.0,
        nodes={},
        asOf="2025-Q4",
        latestAsOf="2025-Q4",
        requestedAsOf="2025-Q4",
        lensProducts={"analysis": _product()},
    )

    result = _resultToRefs("Company.simulate", simulation, target="005930")

    assert isinstance(result.data["result"], dict)
    assert result.data["result"]["scenarioName"] == "baseline"
    assert {ref.kind for ref in result.refs} == {"executionRef", "valueRef", "dateRef"}


def test_data_result_keeps_bounded_polars_structure_and_continuation() -> None:
    values = [float(index) for index in range(25)]
    values[:3] = [math.nan, math.inf, -math.inf]
    asset = AssetRef("scan.ratio", "asset:v1")
    table = DataPartition(
        asset=asset,
        projectionKind="factor",
        data=pl.DataFrame({"entityId": [f"KR:{index:06d}" for index in range(25)], "value": values}),
        schema=(("entityId", "String"), ("value", "Float64")),
        rowCount=25,
        truncated=False,
        selector=(("measure", "roe"),),
        temporalStatus="LATEST_ONLY",
        lineageRefs=("source", "receipt"),
        requestId="factor",
    )
    series = DataPartition(
        asset=asset,
        projectionKind="native",
        data={"scores": pl.Series("scores", [1.0, math.nan, math.inf])},
        schema=(("scores", "Float64"),),
        rowCount=3,
        truncated=False,
        selector=(),
        temporalStatus="LATEST_ONLY",
        lineageRefs=("source", "receipt"),
        requestId="series",
    )
    dataResult = DataResult(
        status="partial",
        partitions=(table, series),
        assets=(asset,),
        snapshotId="data-snapshot:v1",
        contractHash="a" * 64,
        coverage=Coverage(1, 1, 2, 0),
        gaps=(),
        lineageRefs=("source",),
        executionReceipts=("receipt",),
        continuation="opaque-next-page",
    )

    result = _resultToRefs("data", dataResult)
    payload = result.data["result"]
    tablePayload = payload["partitions"][0]
    framePayload = tablePayload["data"]
    seriesPayload = payload["partitions"][1]["data"]["scores"]

    assert payload["continuation"] == "opaque-next-page"
    assert tablePayload["truncated"] is False
    assert framePayload["_type"] == "DataFrame"
    assert framePayload["rowCount"] == 25
    assert framePayload["previewRowCount"] == 20
    assert framePayload["previewTruncated"] is True
    assert [row["value"] for row in framePayload["rows"][:3]] == [None, None, None]
    assert seriesPayload == {
        "_type": "Series",
        "name": "scores",
        "dtype": "Float64",
        "length": 3,
        "previewLength": 3,
        "values": [1.0, None, None],
        "previewTruncated": False,
    }
