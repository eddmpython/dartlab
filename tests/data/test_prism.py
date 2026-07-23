"""Data Prism mixed query, evidence, lineage, quality, Arrow tests."""

from __future__ import annotations

import polars as pl
import pytest

from dartlab.data import (
    DataQuery,
    DataRequest,
    FactorProjection,
    GraphProjection,
    NarrativeProjection,
    QueryBudget,
    RecordsProjection,
)


def _factorSource() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "종목코드": ["005930", "000660"],
            "종목명": ["삼성전자", "SK하이닉스"],
            "2025": [61.0, 72.0],
        }
    )


def testOneQueryBuildsFactorAndNarrativeViews(monkeypatch):
    import dartlab

    scanCalls = []
    gatherCalls = []

    def fakeScan(axis, target=None, **kwargs):
        scanCalls.append((axis, target, kwargs))
        return _factorSource()

    def fakeGather(axis, target=None, **kwargs):
        gatherCalls.append((axis, target, kwargs))
        return {"risk": {"currency": "환율 상승으로 원가 압력이 커질 수 있다."}}

    monkeypatch.setattr(dartlab, "scan", fakeScan)
    monkeypatch.setattr(dartlab, "gather", fakeGather)
    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=(
                DataRequest(
                    assetId="scan.ratio",
                    requestId="technicalFactor",
                    projection=FactorProjection(measures=("rsi",), unit="score", frequency="D"),
                    measures=("rsi",),
                ),
                DataRequest(
                    assetId="gather.narrative",
                    requestId="filingEvidence",
                    projection=NarrativeProjection(),
                    subjects=("005930",),
                    params={"source": "annual"},
                ),
            )
        ),
    )

    assert result.status == "ok"
    assert scanCalls == [("ratio", "rsi", {})]
    assert gatherCalls == [("narrative", "005930", {"source": "annual"})]
    assert [partition.requestId for partition in result.partitions] == ["technicalFactor", "filingEvidence"]

    factor = result.byRequest("technicalFactor")[0]
    assert factor.projectionKind == "factor"
    assert factor.data["knownAt"].null_count() == factor.data.height
    assert factor.lineage is not None
    assert factor.lineage.datasetId == "scan.ratio"

    narrative = result.byRequest("filingEvidence")[0]
    assert narrative.projectionKind == "narrative"
    assert narrative.data["text"].to_list() == ["환율 상승으로 원가 압력이 커질 수 있다."]
    assert narrative.data["language"].to_list() == ["ko"]
    assert narrative.data["knownAt"].null_count() == narrative.data.height
    assert {assertion.assertionId for assertion in result.qualityAssertions} == {
        "rowBudget",
        "byteBudget",
        "provenanceBound",
        "temporalTruth",
        "contentSealed",
    }

    arrow = result.toArrow()
    assert set(arrow) == {"technicalFactor:measure=rsi", "filingEvidence:subject=005930"}
    assert arrow["technicalFactor:measure=rsi"].num_rows == 2
    assert arrow["filingEvidence:subject=005930"].num_rows == 1

    batches = list(result.iterArrowBatches(maxRows=1, maxBytes=1_000_000))
    assert [key for key, _batch in batches] == [
        "technicalFactor:measure=rsi",
        "technicalFactor:measure=rsi",
        "filingEvidence:subject=005930",
    ]
    assert all(batch.num_rows == 1 for _key, batch in batches)
    with pytest.raises(ValueError, match="한 행"):
        list(result.iterArrowBatches(maxRows=1, maxBytes=1))


def testJsonMappingCanEnterMixedWorkbenchWithoutPythonContractObjects(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _factorSource())
    result = dartlab.data(
        "query",
        query={
            "requests": [
                {
                    "assetId": "scan.ratio",
                    "requestId": "outsideProcess",
                    "projection": {"kind": "factor", "measures": ["roe"], "unit": "percent"},
                    "measures": ["roe"],
                }
            ]
        },
    )

    assert result.status == "ok"
    assert result.partitions[0].requestId == "outsideProcess"
    assert result.partitions[0].data["measureId"].unique().to_list() == ["roe"]


def testSameAssetCanExposeTwoIndependentViews(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _factorSource())
    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=(
                DataRequest("scan.ratio", "raw", measures=("roe",)),
                DataRequest(
                    "scan.ratio",
                    "factor",
                    projection=FactorProjection(measures=("roe",), unit="percent"),
                    measures=("roe",),
                ),
            )
        ),
    )

    assert result.status == "ok"
    assert result.byRequest("raw")[0].projectionKind == "native"
    assert result.byRequest("factor")[0].projectionKind == "factor"
    assert len(result.assets) == 1


def testGraphViewKeepsDirectionAndEvidenceWhileArrowSelectsTables(monkeypatch):
    import dartlab

    monkeypatch.setattr(dartlab, "scan", lambda *args, **kwargs: _factorSource())
    monkeypatch.setattr(
        dartlab,
        "industry",
        lambda *args, **kwargs: {
            "nodes": ({"nodeId": "supplier"}, {"nodeId": "buyer"}),
            "edges": ({"sourceId": "supplier", "targetId": "buyer", "predicate": "supplies"},),
        },
    )
    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=(
                DataRequest(
                    "scan.ratio",
                    "factor",
                    projection=FactorProjection(measures=("roe",), unit="percent"),
                    measures=("roe",),
                ),
                DataRequest(
                    "industry.edges",
                    "supplyGraph",
                    projection=GraphProjection(),
                    subjects=("005930",),
                ),
            )
        ),
    )

    graph = result.byRequest("supplyGraph")[0].data
    assert graph["edges"][0]["sourceId"] == "supplier"
    assert graph["edges"][0]["targetId"] == "buyer"
    assert graph["evidence"]["sourceRef"].startswith("python:")
    assert set(result.toArrow()) == {"factor:measure=roe"}


@pytest.mark.parametrize(
    "projection",
    (RecordsProjection(), NarrativeProjection(), FactorProjection(unit="score")),
    ids=("records", "narrative", "factor"),
)
def testEveryEngineAssetPassesUniversalProjectionMatrix(monkeypatch, projection):
    import dartlab

    assets = tuple(
        asset for asset in dartlab.data("catalog").assets if asset.queryable and asset.executorKind == "engineAxis"
    )

    def fakeEngine(owner):
        def execute(axis, *args, **kwargs):
            if isinstance(projection, FactorProjection):
                return pl.DataFrame(
                    {
                        "종목코드": ["005930"],
                        "종목명": ["삼성전자"],
                        "2025": [1.0],
                    }
                )
            return {"text": f"{owner}.{axis}", "value": 1.0}

        return execute

    for owner in {asset.owner for asset in assets}:
        monkeypatch.setattr(dartlab, owner, fakeEngine(owner))
    requests = tuple(
        DataRequest(
            asset.assetId,
            requestId=asset.assetId,
            projection=projection,
            subjects=("probe",) if asset.selectorKind == "subject" else (),
            measures=("probe",) if asset.selectorKind == "measure" else (),
        )
        for asset in assets
    )

    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=requests,
            budget=QueryBudget(maxAssets=len(requests), maxRows=2_000),
            completeness="requireComplete",
        ),
    )

    assert result.status == "ok"
    assert not result.gaps
    assert len(result.partitions) == len(assets) == 146
    assert {partition.projectionKind for partition in result.partitions} == {projection.kind}
    assert len(result.toArrow()) == len(assets)


def testEveryGraphAssetPreservesNodesEdgesAndEvidence(monkeypatch):
    import dartlab

    assets = tuple(
        asset
        for asset in dartlab.data("catalog").assets
        if asset.queryable and asset.owner == "industry" and asset.kind == "graph"
    )
    monkeypatch.setattr(
        dartlab,
        "industry",
        lambda *args, **kwargs: {
            "nodes": ({"nodeId": "source"}, {"nodeId": "target"}),
            "edges": ({"sourceId": "source", "targetId": "target", "predicate": "links"},),
        },
    )
    result = dartlab.data(
        "query",
        query=DataQuery(
            requests=tuple(
                DataRequest(
                    asset.assetId,
                    requestId=asset.assetId,
                    projection=GraphProjection(),
                    subjects=("semiconductor",),
                )
                for asset in assets
            )
        ),
    )

    assert result.status == "ok"
    assert len(result.partitions) == len(assets) == 9
    for partition in result.partitions:
        assert partition.data["edges"][0]["sourceId"] == "source"
        assert partition.data["evidence"]["evidenceRef"].startswith("data-execution:")
