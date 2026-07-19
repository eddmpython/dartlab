"""Universe U3 C2 pinned 무결성과 live freshness 분리 계약을 검증한다."""

from dataclasses import dataclass

import pytest

from tests._attempts.dartlabUniverse.u3C2 import (
    PinnedRevisionValidationError,
    SourceFreshnessMonitor,
    assertPinnedHfRevisions,
    probeHfHeadAdvances,
)


@dataclass(frozen=True)
class _Repository:
    repoId: str
    revision: str


class _Api:
    def __init__(self, *, token, currentRevisions, pinnedRevisions=None):
        self.token = token
        self.currentRevisions = currentRevisions
        self.pinnedRevisions = pinnedRevisions or currentRevisions

    def repo_info(self, repoId, *, revision=None, repo_type, files_metadata):
        assert repo_type == "dataset"
        assert files_metadata is False
        revisions = self.pinnedRevisions if revision is not None else self.currentRevisions
        return type("Info", (), {"sha": revisions[repoId]})()


def testPinnedRevisionRemainsValidWhenHeadAdvancesWithoutExposingToken():
    repositories = (_Repository("fixture/data", "a" * 40),)

    def stableFactory(*, token):
        return _Api(token=token, currentRevisions={"fixture/data": "a" * 40})

    assertPinnedHfRevisions(repositories, token="secret", apiFactory=stableFactory)

    def advancedFactory(*, token):
        return _Api(
            token=token,
            currentRevisions={"fixture/data": "b" * 40},
            pinnedRevisions={"fixture/data": "a" * 40},
        )

    assertPinnedHfRevisions(repositories, token="secret", apiFactory=advancedFactory)
    advances = probeHfHeadAdvances(repositories, token="secret", apiFactory=advancedFactory)
    assert advances == (f"HF head advanced: fixture/data snapshot={'a' * 40} current={'b' * 40}",)

    def mismatchedFactory(*, token):
        return _Api(
            token=token,
            currentRevisions={"fixture/data": "b" * 40},
            pinnedRevisions={"fixture/data": "c" * 40},
        )

    with pytest.raises(PinnedRevisionValidationError, match="pinned revision mismatch") as captured:
        assertPinnedHfRevisions(repositories, token="secret", apiFactory=mismatchedFactory)
    assert "secret" not in str(captured.value)


def testSourceFreshnessMonitorRecordsAdvanceWithoutInvalidatingPinnedWork():
    calls = 0

    def probe():
        nonlocal calls
        calls += 1
        return () if calls == 1 else ("fixture snapshot=a current=b",)

    monitor = SourceFreshnessMonitor(probe)

    assert monitor.check()
    assert not monitor.check()
    assert not monitor.check()
    assert monitor.headAdvanced
    assert monitor.checkCount == 3
    assert monitor.advanceEvents == ["fixture snapshot=a current=b"]


def testSourceFreshnessMonitorClassifiesProbeFailureWithoutLeakingDetail():
    def probe():
        raise RuntimeError("secret transport detail")

    monitor = SourceFreshnessMonitor(probe)

    assert not monitor.check()
    assert not monitor.headAdvanced
    assert monitor.advanceEvents == []
    assert monitor.probeFailureCodes == ["RuntimeError"]
