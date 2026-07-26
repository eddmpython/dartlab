from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from dartlab.dataHub.contracts import Coverage, DataResult
from dartlab.dataHub.controlPlane.auth import DataHubAuthPolicy
from dartlab.dataHub.controlPlane.httpApi import buildDataHubRouter
from dartlab.dataHub.controlPlane.ledger import DataHubJobLedger
from dartlab.dataHub.remote import AsyncDataHubClient, DataHubClient
from dartlab.dataHub.transport import decodeDataResult, encodeDataResult
from dartlab.dataHub.workerPlane import DataHubWorker

pytestmark = pytest.mark.unit

CLIENT_TOKEN = "c" * 64
WORKER_TOKEN = "w" * 64
DIGEST = "1" * 64


def result() -> DataResult:
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
        materializationReceipt={
            "generationKey": "2" * 64,
            "terminalRootDigest": "3" * 64,
            "pins": {
                "assetDigest": "4" * 64,
                "sourceDigest": "5" * 64,
                "queryDigest": "6" * 64,
                "universeDigest": "7" * 64,
                "contractDigest": "8" * 64,
                "schemaDigest": "9" * 64,
            },
        },
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
            queryRunner=lambda *_args, **_kwargs: result(),
        )
        try:
            job = client.query(
                {"requests": [{"assetId": "resource.finance"}]},
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
    assert restored.materializationReceipt == result().materializationReceipt


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
