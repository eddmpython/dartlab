from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dartlab.dataHub.contracts import Coverage, DataPartition, DataResult
from dartlab.dataHub.controlPlane.auth import DataHubAuthPolicy
from dartlab.dataHub.controlPlane.httpApi import buildDataHubRouter
from dartlab.dataHub.controlPlane.ledger import DataHubJobLedger
from dartlab.dataHub.controlPlane.policy import MAX_REQUEST_BYTES, MAX_RESULT_WIRE_BYTES
from dartlab.dataHub.controlPlane.resultContract import buildExpectedResultContract
from dartlab.dataHub.entry import _dataQuery
from dartlab.dataHub.identity.contentSeal import contentHash, resultSnapshotId
from dartlab.dataHub.materialization import GenerationPins, MaterializationReceipt, generationKey
from dartlab.dataHub.remote import AsyncDataHubClient, DataHubClient
from dartlab.dataHub.transport import decodeDataResult, encodeDataResult
from dartlab.dataHub.workerPlane import DataHubWorker

pytestmark = pytest.mark.unit

CLIENT_TOKEN = "c" * 64
WORKER_TOKEN = "w" * 64
DIGEST = "1" * 64


def result() -> DataResult:
    pins = GenerationPins(
        assetDigest="4" * 64,
        sourceDigest="5" * 64,
        queryDigest="6" * 64,
        universeDigest="7" * 64,
        contractDigest="8" * 64,
        schemaDigest="9" * 64,
    )
    receipt = MaterializationReceipt(
        generationKey=generationKey(pins),
        terminalRootDigest="3" * 64,
        pins=pins,
    )
    return DataResult(
        status="ok",
        partitions=(),
        assets=(),
        snapshotId="catalog:test",
        contractHash=DIGEST,
        coverage=Coverage(1, 1, 0, 0),
        gaps=(),
        lineageRefs=(),
        executionReceipts=(),
        materializationReceipt=receipt.asTree(),
    )


def boundResult(query) -> DataResult:
    parsed = _dataQuery(query)
    assert parsed is not None
    expected = buildExpectedResultContract(parsed)
    data = {"value": 1}
    partition = DataPartition(
        asset=expected.assets[0],
        projectionKind="native",
        data=data,
        schema=(("value", "int"),),
        rowCount=1,
        truncated=False,
        selector=(),
        temporalStatus="LATEST_ONLY",
        lineageRefs=(),
        requestId="fixture",
        contentHash=contentHash(data),
    )
    snapshot = resultSnapshotId(
        catalogSnapshotId=expected.catalogSnapshotId,
        contractHash=expected.contractHash,
        partitions=(partition,),
        universeSnapshotId=None,
    )
    return DataResult(
        status="ok",
        partitions=(partition,),
        assets=expected.assets,
        snapshotId=expected.catalogSnapshotId,
        contractHash=expected.contractHash,
        coverage=Coverage(expected.requestedAssets, expected.resolvedAssets, 1, 0),
        gaps=(),
        lineageRefs=(),
        executionReceipts=(),
        dataSnapshotId=snapshot,
    )


def app(tmp_path: Path) -> FastAPI:
    application = FastAPI()
    application.include_router(
        buildDataHubRouter(
            ledger=DataHubJobLedger(tmp_path / "control"),
            authPolicy=DataHubAuthPolicy(
                clientToken=CLIENT_TOKEN,
                workerToken=WORKER_TOKEN,
            ),
        )
    )
    return application


def testResultWireRoundTripPreservesReceipt() -> None:
    original = result()
    restored = decodeDataResult(encodeDataResult(original))
    assert restored.status == original.status
    assert restored.contractHash == original.contractHash
    assert restored.materializationReceipt == original.materializationReceipt


def testRemoteClientAndDistributedWorkerCompleteJob(tmp_path: Path) -> None:
    application = app(tmp_path)
    with TestClient(application) as server:
        transport = server._transport
        client = DataHubClient(
            "http://testserver",
            CLIENT_TOKEN,
            transport=transport,
        )
        worker = DataHubWorker(
            "http://testserver",
            WORKER_TOKEN,
            "worker-node-a",
            transport=transport,
            queryRunner=lambda *_args, **kwargs: boundResult(kwargs["query"]),
        )
        try:
            job = client.query(
                {"requests": [{"assetId": "analysis.simulationInputs"}]},
                wait=False,
                idempotencyKey="remote-job",
            )
            outcome = worker.runOnce()
            restored = client.wait(job.jobId, timeoutSeconds=5)
        finally:
            worker.close()
            client.close()

    assert outcome.claimed
    assert outcome.completed
    assert restored.status == "ok"
    assert restored.partitions[0].data == {"value": 1}


@pytest.mark.asyncio
async def testAsyncClientSubmitsAndCancels(tmp_path: Path) -> None:
    application = app(tmp_path)
    transport = httpx.ASGITransport(app=application)
    client = AsyncDataHubClient(
        "http://testserver",
        CLIENT_TOKEN,
        transport=transport,
    )
    try:
        job = await client(
            "query",
            query={"requests": [{"assetId": "resource.finance"}]},
            wait=False,
        )
        cancelled = await client.cancel(job.jobId)
    finally:
        await client.close()
    assert cancelled.state == "cancelled"


def testResultWireRejectsTampering() -> None:
    payload = bytearray(encodeDataResult(result()))
    payload[-2] = ord("0") if payload[-2] != ord("0") else ord("1")
    with pytest.raises(Exception, match="durable state 검증"):
        decodeDataResult(bytes(payload))


def testRoleTokensAreNotInterchangeable(tmp_path: Path) -> None:
    application = app(tmp_path)
    with TestClient(application) as client:
        clientHeaders = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        workerHeaders = {"Authorization": f"Bearer {WORKER_TOKEN}"}
        assert client.post("/api/dataHub/v1/catalog", headers=clientHeaders).status_code == 200
        assert (
            client.post(
                "/api/dataHub/v1/workers/claims",
                headers=clientHeaders,
                json={"workerId": "wrong-role"},
            ).status_code
            == 401
        )
        assert client.post("/api/dataHub/v1/catalog", headers=workerHeaders).status_code == 401


def testWorkerCannotCompleteWithCorruptWirePayload(tmp_path: Path) -> None:
    application = app(tmp_path)
    with TestClient(application) as client:
        clientHeaders = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        workerHeaders = {"Authorization": f"Bearer {WORKER_TOKEN}"}
        job = client.post(
            "/api/dataHub/v1/jobs",
            headers=clientHeaders,
            json={"query": {"requests": [{"assetId": "resource.finance"}]}},
        ).json()
        lease = client.post(
            "/api/dataHub/v1/workers/claims",
            headers=workerHeaders,
            json={"workerId": "worker-corrupt", "leaseSeconds": 60},
        ).json()["lease"]

        response = client.post(
            f"/api/dataHub/v1/workers/jobs/{job['jobId']}/complete",
            params={"leaseEpoch": lease["leaseEpoch"]},
            headers={
                **workerHeaders,
                "X-DataHub-Worker": "worker-corrupt",
            },
            content=b'{"not":"a-data-result"}',
        )

        assert response.status_code == 422
        assert (
            client.get(
                f"/api/dataHub/v1/jobs/{job['jobId']}",
                headers=clientHeaders,
            ).json()["state"]
            == "leased"
        )


def testSubmitRejectsInvalidQueryBeforeQueue(tmp_path: Path) -> None:
    application = app(tmp_path)
    with TestClient(application) as client:
        clientHeaders = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        workerHeaders = {"Authorization": f"Bearer {WORKER_TOKEN}"}
        response = client.post(
            "/api/dataHub/v1/jobs",
            headers=clientHeaders,
            json={"query": {"notAField": 1}},
        )
        claim = client.post(
            "/api/dataHub/v1/workers/claims",
            headers=workerHeaders,
            json={"workerId": "worker-empty"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "DATA_HUB_INVALID"
    assert claim.json() == {"lease": None}


def testRemoteCompletionRejectsResultUnboundToClaimedQuery(tmp_path: Path) -> None:
    application = app(tmp_path)
    with TestClient(application) as client:
        clientHeaders = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
        workerHeaders = {"Authorization": f"Bearer {WORKER_TOKEN}"}
        submitted = client.post(
            "/api/dataHub/v1/jobs",
            headers=clientHeaders,
            json={"query": {"requests": [{"assetId": "analysis.simulationInputs"}]}},
        ).json()
        lease = client.post(
            "/api/dataHub/v1/workers/claims",
            headers=workerHeaders,
            json={"workerId": "worker-cross-job"},
        ).json()["lease"]
        unrelated = boundResult(
            {
                "requests": [{"assetId": "scan.ratio"}],
                "budget": {"maxBytes": 12_517_376},
                "materialization": {"mode": "refresh"},
            }
        )
        response = client.post(
            f"/api/dataHub/v1/workers/jobs/{submitted['jobId']}/complete",
            params={"leaseEpoch": lease["leaseEpoch"]},
            headers={
                **workerHeaders,
                "X-DataHub-Worker": "worker-cross-job",
                "X-DataHub-Request-Digest": lease["job"]["requestDigest"],
            },
            content=encodeDataResult(unrelated),
        )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "DATA_HUB_RESULT_UNBOUND"


def testServerAndCodecRejectOversizedBodyBeforeDecoding(tmp_path: Path) -> None:
    with pytest.raises(Exception) as captured:
        decodeDataResult(b"x" * (MAX_RESULT_WIRE_BYTES + 1))
    assert getattr(captured.value, "code", None) == "DATA_HUB_PAYLOAD_BUDGET"

    application = app(tmp_path)
    with TestClient(application) as client:
        response = client.post(
            "/api/dataHub/v1/jobs",
            headers={"Authorization": f"Bearer {CLIENT_TOKEN}"},
            content=b"x" * (MAX_REQUEST_BYTES + 1),
        )
    assert response.status_code == 413
    assert response.json()["detail"]["code"] == "DATA_HUB_PAYLOAD_BUDGET"


def testRemoteClientsRequireTlsOutsideLoopback() -> None:
    with pytest.raises(ValueError, match="https"):
        DataHubClient("http://example.com", CLIENT_TOKEN)
    with pytest.raises(ValueError, match="https"):
        AsyncDataHubClient("http://example.com", CLIENT_TOKEN)
