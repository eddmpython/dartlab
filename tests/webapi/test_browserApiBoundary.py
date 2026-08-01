"""브라우저 HTTP 경계의 구조 보존, 비차단 실행, 예산 회귀 테스트."""

from __future__ import annotations

import asyncio
import json
import time
from types import SimpleNamespace

import pytest

from dartlab.webapi import browserApi

pytestmark = pytest.mark.unit


def _storyResult(*, status: str = "partial", gaps: list[dict] | None = None):
    product = {
        "status": status,
        "time": {"asOf": "2026-07-31", "dataAsOf": "2026-06-30"},
        "evidence": [{"sourceRef": "fixture://analysis", "valueRef": "value://revenue"}],
    }
    gapRows = list(gaps or [])
    bundle = {"products": {"analysis": product}, "gaps": gapRows}
    return SimpleNamespace(
        stockCode="005930",
        corpName="삼성전자",
        reportType="full",
        template="general",
        templates=["general"],
        summaryCard=SimpleNamespace(conclusion="근거 제한", strengths=[], warnings=["자료 부족"], grades={}),
        sections=[SimpleNamespace(key="overview", title="개요", summary="요약", blocks=[], threads=[])],
        circulationSummary="",
        lensGaps=gapRows,
        lensProducts={"analysis": product},
        _lensBundle=bundle,
    )


def test_storyEnvelopePreservesStatusGapsAsOfAndRefs(monkeypatch) -> None:
    from dartlab.story import lensProducts

    monkeypatch.setattr(lensProducts, "publicLensBundle", lambda bundle: bundle)
    gaps = [{"status": "blocked", "reason": "입력 결손", "sourceRef": "fixture://gap"}]

    result = browserApi._storyEnvelope(_storyResult(gaps=gaps), "수익구조")

    assert result["schemaVersion"] == "dartlab.browser.story.v1"
    assert result["status"] == "blocked"
    assert result["gaps"][0]["status"] == "blocked"
    assert result["report"]["lensProducts"]["products"]["analysis"]["status"] == "partial"
    assert set(result["asOf"]) >= {"2026-07-31", "2026-06-30"}
    assert "fixture://gap" in result["refs"]
    assert "fixture://analysis" in result["refs"]
    assert "value://revenue" in result["refs"]
    assert result["serialization"]["status"] == "complete"
    assert result["serialization"]["bytes"] == len(
        json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )


def test_storyEnvelopeNeverPromotesPartialToComplete(monkeypatch) -> None:
    from dartlab.story import lensProducts

    monkeypatch.setattr(lensProducts, "publicLensBundle", lambda bundle: bundle)

    result = browserApi._storyEnvelope(_storyResult(status="partial"), "수익구조")

    assert result["status"] == "partial"
    assert result["status"] != "complete"


def test_budgetedJsonMarksStringAndCollectionTruncation() -> None:
    payload = {"text": "가" * 20_000, "items": list(range(browserApi._ITEM_CAP + 5))}

    result = browserApi._publicJson(payload)

    meta = result["_dartlabSerialization"]
    assert meta["status"] == "partial"
    assert set(meta["reasons"]) >= {"maxStringBytes", "maxItems"}
    assert len(result["text"].encode("utf-8")) <= browserApi._STRING_BYTE_CAP
    assert result["items"][-1]["status"] == "partial"
    assert meta["bytes"] == len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def test_budgetedJsonRejectsCycles() -> None:
    payload: dict = {}
    payload["self"] = payload

    with pytest.raises(browserApi.BrowserPayloadError, match="순환 참조"):
        browserApi._publicJson(payload)


def test_runSyncDoesNotBlockCpythonEventLoop(monkeypatch) -> None:
    monkeypatch.setattr(browserApi, "_threadOffloadAvailable", lambda: True)

    async def _scenario() -> float:
        started = time.perf_counter()
        task = asyncio.create_task(browserApi._runSync(lambda: time.sleep(0.2)))
        await asyncio.sleep(0.02)
        elapsed = time.perf_counter() - started
        await task
        return elapsed

    assert asyncio.run(_scenario()) < 0.12


def test_runSyncAvoidsThreadsInPyodide(monkeypatch) -> None:
    monkeypatch.setattr(browserApi, "_threadOffloadAvailable", lambda: False)

    async def _unexpected(*_args, **_kwargs):
        raise AssertionError("Pyodide에서 thread offload를 호출하면 안 됩니다.")

    monkeypatch.setattr(asyncio, "to_thread", _unexpected)
    assert asyncio.run(browserApi._runSync(lambda: 42)) == 42


def test_storyEndpointReturnsStructuredEnvelope(monkeypatch) -> None:
    starlette = pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    import dartlab
    from dartlab.story import lensProducts

    class _Company:
        def __init__(self, code: str):
            self.code = code

        def story(self, section: str):
            assert section == "수익구조"
            return _storyResult(status="partial")

    monkeypatch.setattr(dartlab, "Company", _Company)
    monkeypatch.setattr(lensProducts, "publicLensBundle", lambda bundle: bundle)
    with TestClient(browserApi.buildBrowserApi(), raise_server_exceptions=False) as client:
        response = client.get("/company/005930/story/수익구조")

    assert response.status_code == 200
    body = response.json()
    assert body["kind"] == "story"
    assert body["status"] == "partial"
    assert "report" in body
    assert "text" not in body


def test_browserErrorsUseBlockedTaxonomyWithoutLeakingDetails(monkeypatch) -> None:
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    import dartlab

    class _Company:
        def __init__(self, code: str):
            raise Exception("token=secret123 at /home/user/private.json")

    monkeypatch.setattr(dartlab, "Company", _Company)
    with TestClient(browserApi.buildBrowserApi(), raise_server_exceptions=False) as client:
        response = client.get("/company/005930/industry")

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "blocked"
    assert body["error"]["code"] == "internal_error"
    assert "secret123" not in response.text
    assert "/home/user" not in response.text


def test_browserInputBudgetUsesStructuredError() -> None:
    pytest.importorskip("starlette")
    from starlette.testclient import TestClient

    with TestClient(browserApi.buildBrowserApi(), raise_server_exceptions=False) as client:
        response = client.get(f"/company/{'A' * 33}/industry")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_input"
