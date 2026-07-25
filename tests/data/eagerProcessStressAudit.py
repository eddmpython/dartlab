"""Eager/owner process isolation의 명시적 장시간 stress 감사 helper."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import pytest

from dartlab.data.ownerProcess import runOwnerPage
from dartlab.data.pagingRuntime import ownerProcessArtifactRoot
from tests.data.test_eagerComposite import (
    testMixedInitialSealsGeneralEagerAndResumeTouchesOnlyLocator as _runMixedInitial,
)
from tests.data.test_ownerProcess import _sessionPayload

_OWNER_ATTEMPTS = 50
_MIXED_ATTEMPTS = 20


def testOwnerSpawnFiftyConsecutive() -> None:
    outcomes = tuple(
        runOwnerPage(
            _sessionPayload(),
            publicDeadline=time.perf_counter() + 30,
        )
        for _ in range(_OWNER_ATTEMPTS)
    )
    samples = sorted(sample for outcome in outcomes if (sample := outcome.readySeconds) is not None)
    failures = [
        {
            "cleanupTrace": outcome.cleanupTrace,
            "errorCode": outcome.errorCode,
            "ipcFrameCount": outcome.ipcFrameCount,
            "jobObjectAssigned": outcome.jobObjectAssigned,
            "jobObjectAttempted": outcome.jobObjectAttempted,
            "jobObjectError": outcome.jobObjectError,
            "status": outcome.status,
            "zeroLive": outcome.zeroLive,
        }
        for outcome in outcomes
        if outcome.status != "ok" or not outcome.zeroLive
    ]
    p50 = samples[math.ceil(0.50 * len(samples)) - 1] if samples else None
    p95 = samples[math.ceil(0.95 * len(samples)) - 1] if samples else None
    residue = tuple(ownerProcessArtifactRoot().glob("*.arrow"))
    print(
        json.dumps(
            {
                "attempts": _OWNER_ATTEMPTS,
                "failures": failures,
                "maximumSeconds": max(samples) if samples else None,
                "p50Seconds": p50,
                "p95Seconds": p95,
                "residueCount": len(residue),
                "zeroLiveCount": sum(outcome.zeroLive for outcome in outcomes),
            },
            sort_keys=True,
        )
    )

    assert len(samples) == _OWNER_ATTEMPTS
    assert not failures
    assert not residue


@pytest.mark.parametrize("attempt", range(_MIXED_ATTEMPTS))
def testMixedInitialTwentyConsecutive(
    attempt: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _runMixedInitial(
        tmp_path,
        monkeypatch,
    )
    residue = tuple(ownerProcessArtifactRoot().glob("*.arrow"))
    print(
        json.dumps(
            {
                "attempt": attempt + 1,
                "artifactResidueCount": len(residue),
                "status": "ok",
            },
            sort_keys=True,
        )
    )
    assert not residue
