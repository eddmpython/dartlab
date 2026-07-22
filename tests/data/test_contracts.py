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
