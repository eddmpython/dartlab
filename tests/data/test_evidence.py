"""data.evidence module mirror tests."""

from __future__ import annotations

from dartlab.data.contracts import DataAssetDescriptor, DataQuery
from dartlab.data.evidence import narrativeFrame


def testNarrativeFrameHasStableDocumentAndChunkIdentity():
    descriptor = DataAssetDescriptor(
        assetId="gather.narrative",
        assetVersionId="asset:v1",
        owner="gather",
        layer="L1",
        kind="source",
        label="narrative",
        description="narrative",
        sourceRef="python:gather:narrative",
        queryable=True,
    )
    kwargs = {
        "raw": {"risk": ["환율 상승", "수요 둔화"]},
        "descriptor": descriptor,
        "query": DataQuery(),
        "selector": {"subject": "005930"},
        "receiptRef": "data-execution:1",
    }

    first = narrativeFrame(**kwargs)
    second = narrativeFrame(**kwargs)

    assert first.to_dicts() == second.to_dicts()
    assert first["documentId"].n_unique() == 1
    assert first["chunkId"].n_unique() == 2
    assert first["contentHash"].n_unique() == 2
    assert first["knownAt"].null_count() == 2
