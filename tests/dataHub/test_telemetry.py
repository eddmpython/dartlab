"""DataHub 실행 진단 side channel tests."""

from __future__ import annotations

import logging

import pytest

from dartlab.dataHub.telemetry import (
    dataHubLogger,
    durationSummary,
    failureCounts,
    recordDuration,
    recordFailure,
    resetTelemetry,
)


@pytest.fixture(autouse=True)
def _clean() -> None:
    resetTelemetry()


def testLoggerNamesStayUnderDataHubNamespace() -> None:
    """모든 DataHub logger 는 한 이름 공간 아래 모인다."""

    assert dataHubLogger("dartlab.dataHub.ownerPagingApi").name == "dartlab.dataHub.ownerPagingApi"
    assert dataHubLogger("dartlab.dataHub.workerPlane.worker").name == "dartlab.dataHub.workerPlane.worker"
    assert dataHubLogger("someOther.module").name == "dartlab.dataHub.module"


def testRecordFailureKeepsTracebackAndCorrelationKeys(caplog: pytest.LogCaptureFixture) -> None:
    """축약 code 를 유지하면서 원인 traceback 과 상관 키를 남긴다."""

    logger = dataHubLogger("dartlab.dataHub.fixture")
    with caplog.at_level(logging.WARNING, logger="dartlab.dataHub"):
        try:
            raise ValueError("owner boundary가 깨졌습니다")
        except ValueError:
            recordFailure(logger, "CONTINUATION_OWNER_FAILED", context={"requestId": "kr", "market": "KR"})

    assert failureCounts() == {"CONTINUATION_OWNER_FAILED": 1}
    record = caplog.records[-1]
    assert "CONTINUATION_OWNER_FAILED" in record.getMessage()
    assert "requestId" in record.getMessage()
    assert record.exc_info is not None
    assert "owner boundary가 깨졌습니다" in caplog.text


def testFailureCountsAccumulatePerCode() -> None:
    """code 별로 누적해 어떤 결손이 지배적인지 즉시 보인다."""

    logger = dataHubLogger("dartlab.dataHub.fixture")
    for code in ("A_FAILED", "A_FAILED", "B_FAILED"):
        try:
            raise RuntimeError("x")
        except RuntimeError:
            recordFailure(logger, code)

    assert failureCounts() == {"A_FAILED": 2, "B_FAILED": 1}


def testRecordDurationCollectsSamplesEvenWhenBodyRaises() -> None:
    """예외가 나도 구간 소요는 기록한다."""

    with recordDuration("ownerPage"):
        pass
    with pytest.raises(RuntimeError):
        with recordDuration("ownerPage"):
            raise RuntimeError("boom")

    summary = durationSummary()
    assert summary["ownerPage"]["count"] == 2.0
    assert summary["ownerPage"]["max"] >= summary["ownerPage"]["p50"]


def testResetTelemetryClearsBothChannels() -> None:
    """재기준 후에는 카운터와 구간 표본이 모두 비어야 한다."""

    logger = dataHubLogger("dartlab.dataHub.fixture")
    try:
        raise RuntimeError("x")
    except RuntimeError:
        recordFailure(logger, "C_FAILED")
    with recordDuration("span"):
        pass

    resetTelemetry()

    assert failureCounts() == {}
    assert durationSummary() == {}


def testLibraryDoesNotAttachHandlers() -> None:
    """호스트가 logging 을 설정하지 않으면 아무것도 출력하지 않는다."""

    assert dataHubLogger("dartlab.dataHub.fixture").handlers == []
    assert logging.getLogger("dartlab.dataHub").handlers == []


def testSwallowedOwnerCauseReachesSideChannelButNotPublicGap(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """삼켜진 원인은 로그로 남고 공개 gap 메시지는 축약을 유지한다."""

    import dartlab
    import dartlab.dataHub.isolation.ownerProcess as ownerProcess

    secretCause = "강제 주입 owner child boundary 파손"
    monkeypatch.setattr(
        ownerProcess,
        "runOwnerPage",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError(secretCause)),
    )
    request = {
        "assetId": "analysis.dartFinancialFeatures",
        "requestId": "kr",
        "universe": {"markets": ["KR"], "membership": "listed"},
        "projection": {"kind": "factor", "measures": ["financial.revenue"]},
        "time": {"knownAt": "20260723"},
    }
    query = {
        "requests": [request],
        "budget": {
            "maxRows": 1000,
            "maxBytes": 8 * 1024 * 1024,
            "timeoutMs": 60_000,
            "maxAssets": 2,
            "maxSubjects": 20_000,
            "maxConcurrency": 1,
        },
    }

    with caplog.at_level(logging.WARNING, logger="dartlab.dataHub"):
        result = dartlab.dataHub("query", query=query)

    assert result.status == "failed"
    assert [gap.code for gap in result.gaps] == ["CONTINUATION_OWNER_FAILED"]
    # 공개 표면은 원인을 노출하지 않는다.
    assert all(secretCause not in gap.message for gap in result.gaps)
    # side channel 에는 원인이 보존된다.
    assert secretCause in caplog.text
    assert failureCounts().get("CONTINUATION_OWNER_FAILED", 0) >= 1
