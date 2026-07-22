"""U5 spatial projection tests가 공유하는 current-repo fixture request."""

from __future__ import annotations

from .contracts import Visibility
from .fixtures.projectionStress import projectionScope
from .queryTestSupport import QueryRuntimeFixture, buildQueryRuntimeFixture
from .spatial.contracts import ProjectionRequest


def spatialFixture() -> QueryRuntimeFixture:
    return buildQueryRuntimeFixture()


def spatialRequest(
    fixture: QueryRuntimeFixture,
    *,
    count: int = 128,
    activeLens: str = "overview",
    stabilityBaseProjectionId: str | None = None,
    selectedObjectIds: tuple[str, ...] = (),
) -> ProjectionRequest:
    required = tuple(
        sorted(
            {
                item
                for statement in fixture.statements
                for item in (statement.subjectRef, statement.objectRef)
                if item is not None
            }
        )
    )
    scope = tuple(dict.fromkeys((*required, *projectionScope(fixture.catalog, count))))[:count]
    return ProjectionRequest(
        snapshotId=fixture.snapshot.snapshotId,
        projectionVersion="du-projection-fixture-v1",
        objectScope=scope,
        relationScope=(),
        validAt="9999-12-30T00:00:00Z",
        knownAt="9999-12-30T00:00:00Z",
        activeLens=activeLens,
        allowedVisibility=(Visibility.PUBLIC, Visibility.LOCAL, Visibility.PRIVATE, Visibility.RESTRICTED),
        selectedObjectIds=selectedObjectIds,
        stabilityBaseProjectionId=stabilityBaseProjectionId,
        seed=20260722,
    )
