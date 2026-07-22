"""Data Prism attempt의 혼합 projection과 evidence spine 검증."""

from __future__ import annotations

import pytest
from prismPrototype import ViewRequest, compileViews, narrativeChunks


def testMixedViewsInheritAndOverrideWithoutCrossContamination():
    requests = (
        ViewRequest("quant.momentum", "signal", "factor", measures=("rsi",)),
        ViewRequest("gather.sections", "evidence", "narrative", params={"section": "risk"}),
    )

    compiled = compileViews(
        requests,
        subjects=("005930",),
        measures=("roe",),
        params={"language": "ko", "section": "all"},
    )

    assert [item["projection"] for item in compiled] == ["factor", "narrative"]
    assert compiled[0]["subjects"] == ("005930",)
    assert compiled[0]["measures"] == ("rsi",)
    assert compiled[1]["measures"] == ("roe",)
    assert compiled[0]["params"]["section"] == "all"
    assert compiled[1]["params"]["section"] == "risk"


def testDuplicateRequestIdFailsClosed():
    with pytest.raises(ValueError, match="고유"):
        compileViews(
            (
                ViewRequest("quant.momentum", "same", "factor"),
                ViewRequest("gather.sections", "same", "narrative"),
            )
        )


def testNarrativeEvidenceIsDeterministicAndDoesNotInventKnowledgeTime():
    kwargs = {
        "assetId": "gather.sections",
        "revisionId": "v1",
        "sourceRef": "dart:filing:1",
        "evidenceRef": "data-execution:1",
    }
    first = narrativeChunks({"risk": ["환율 상승", "수요 둔화"]}, **kwargs)
    second = narrativeChunks({"risk": ["환율 상승", "수요 둔화"]}, **kwargs)

    assert first == second
    assert len(first) == 2
    assert first[0]["documentId"] == first[1]["documentId"]
    assert first[0]["chunkId"] != first[1]["chunkId"]
    assert first[0]["knownAt"] is None
    assert first[0]["temporalStatus"] == "LATEST_ONLY"
    assert {"assetId", "eventAt", "availableAt", "knownAt", "revisionId", "sourceRef", "evidenceRef"} <= set(first[0])
