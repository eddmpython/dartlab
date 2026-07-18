"""Universe U1 deterministic ID와 revision-scoped locator 검증."""

from __future__ import annotations

import pytest

from tests._attempts.dartlabUniverse.ids import (
    blogBlockIds,
    dartOrganizationId,
    edgarOrganizationId,
    hfFileIds,
    logicalId,
    normalizePath,
    rowId,
    rowVersionId,
    versionId,
)


def testLogicalAndVersionIdsAreStableAndRevisionSensitive():
    logical = logicalId("concept", ("ifrs-full", "Revenue"))
    assert logical == logicalId("concept", ("ifrs-full", "Revenue"))
    assert versionId(logical, ("revision-a",)) != versionId(logical, ("revision-b",))
    assert dartOrganizationId("00126380") != edgarOrganizationId("00126380")


def testHfPathNormalizationAndTraversalRejection():
    first = hfFileIds("Owner/Repo", "dart\\panel\\005930.parquet", "a" * 40, "b" * 64)
    second = hfFileIds("owner/repo", "dart/panel/005930.parquet", "a" * 40, "b" * 64)
    assert first == second
    assert normalizePath("한글/e\u0301.json") == normalizePath("한글/é.json")
    with pytest.raises(ValueError):
        normalizePath("../secret")


def testBusinessKeyAndRevisionScopedRowsNeverMasqueradeAsSameIdentity():
    fileLogical = logicalId("hf-file", ("repo", "table.parquet"))
    fileVersionA = versionId(fileLogical, ("a" * 40, "1" * 64))
    fileVersionB = versionId(fileLogical, ("b" * 40, "2" * 64))
    stable = rowId(fileLogical, "finance", {"corpCode": "00126380", "year": 2025})
    assert stable == rowId(fileLogical, "finance", {"year": 2025, "corpCode": "00126380"})
    assert rowVersionId(fileVersionA, 0, 7) != rowVersionId(fileVersionB, 0, 7)
    with pytest.raises(ValueError):
        rowId(fileLogical, "finance", None)


def testBlogRewriteKeepsLogicalBlockAndChangesVersion():
    postId = logicalId("blog-post", ("dartlab", "blog/post/index.md"))
    logicalA, versionA = blogBlockIds(postId, ("재무", "매출"), "paragraph-1", "a" * 64)
    logicalB, versionB = blogBlockIds(postId, ("재무", "매출"), "paragraph-1", "b" * 64)
    assert logicalA == logicalB
    assert versionA != versionB


def testGeneratedIdentityCorpusHasNoCollision():
    generated = {logicalId("fixture", (index, f"entity-{index}")) for index in range(20000)}
    assert len(generated) == 20000
