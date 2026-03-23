"""채널 런타임 API 테스트."""

from __future__ import annotations

import asyncio

import pytest

starlette = pytest.importorskip("starlette", reason="starlette not installed (optional [ai] dependency)")
from starlette.testclient import TestClient  # noqa: E402

from dartlab.server import app  # noqa: E402
from dartlab.server.services.channel_runtime import channel_runtime  # noqa: E402

pytestmark = pytest.mark.unit


class _FakeAdapter:
    def __init__(self):
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        await self._stop_event.wait()

    async def stop(self) -> None:
        self._stop_event.set()

    async def send_text(self, channel_id: str, text: str) -> None:  # pragma: no cover - contract only
        return None


@pytest.fixture()
def client():
    channel_runtime.shutdown_all()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    channel_runtime.shutdown_all()


def test_status_includes_channels(client):
    resp = client.get("/api/status", params={"probe": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert "channels" in data
    assert "telegram" in data["channels"]
    assert "slack" in data["channels"]
    assert "discord" in data["channels"]


def test_channel_start_and_stop(client, monkeypatch):
    monkeypatch.setattr("dartlab.channel.adapters.create_adapter", lambda platform, **kwargs: _FakeAdapter())

    start = client.post("/api/channels/telegram/start", json={"token": "fake-token"})
    assert start.status_code == 200
    assert start.json()["error"] is None

    status = client.get("/api/status", params={"probe": 0}).json()
    assert status["channels"]["telegram"]["running"] is True

    stop = client.post("/api/channels/telegram/stop")
    assert stop.status_code == 200

    status = client.get("/api/status", params={"probe": 0}).json()
    assert status["channels"]["telegram"]["running"] is False


def test_channel_start_validates_required_fields(client):
    resp = client.post("/api/channels/slack/start", json={"botToken": "xoxb-only"})
    assert resp.status_code == 400
    assert "app token" in resp.json()["detail"]
