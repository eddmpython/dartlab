"""Unified Data Workbench public contract tests."""

from __future__ import annotations

import pytest

from dartlab.data import DataQuery, DataRequest, QueryBudget, TimeContext


def testBudgetRejectsNonPositiveLimits():
    with pytest.raises(ValueError, match="maxRows"):
        QueryBudget(maxRows=0)


def testQueryRejectsSubjectsBeyondBudget():
    with pytest.raises(ValueError, match="subjects"):
        DataQuery(subjects=("a", "b"), budget=QueryBudget(maxSubjects=1))


def testTimeContextKeepsValidAndKnownTimeSeparate():
    context = TimeContext(validAt="2025-12-31", knownAt="2026-02-01")
    assert context.validAt != context.knownAt


def testMixedRequestSubjectsShareOneGlobalBudget():
    with pytest.raises(ValueError, match="request subjects"):
        DataQuery(
            subjects=("a",),
            requests=(DataRequest("scan.ratio", subjects=("b",)),),
            budget=QueryBudget(maxSubjects=1),
        )


def testDuplicateExplicitRequestIdsFailClosed():
    with pytest.raises(ValueError, match="requestId"):
        DataQuery(
            requests=(
                DataRequest("scan.ratio", "same"),
                DataRequest("gather.narrative", "same"),
            )
        )


def testContinuationIsOpaqueAndCannotOverrideStoredQuery():
    token = "dltc1." + "A" * 43
    query = DataQuery(continuation=token)

    assert token not in repr(query)
    with pytest.raises(ValueError, match="덮어쓸"):
        DataQuery(continuation=token, measures=("sales",))
    with pytest.raises(ValueError, match="비었습니다"):
        DataQuery(continuation="")
