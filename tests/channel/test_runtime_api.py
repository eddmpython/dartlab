"""채널 런타임 API 테스트."""

from __future__ import annotations

import asyncio

import pytest

starlette = pytest.importorskip("starlette", reason="starlette not installed (optional [ai] dependency)")
from starlette.testclient import TestClient  # noqa: E402

from dartlab.server import app  # noqa: E402
from dartlab.server.services.channelRuntime import channelRuntime  # noqa: E402
from dartlab.server.services.devChannelRuntime import devChannelRuntime  # noqa: E402

pytestmark = pytest.mark.unit


class _FakeAdapter:
    def __init__(self):
        self._stop_event = asyncio.Event()

    async def start(self) -> None:
        await self._stop_event.wait()

    async def stop(self) -> None:
        self._stop_event.set()

    async def sendText(self, channelId: str, text: str) -> None:  # pragma: no cover - contract only
        return None


class _FakeProcess:
    def __init__(self):
        self._terminated = False

    def poll(self):
        return 0 if self._terminated else None

    def terminate(self):
        self._terminated = True


@pytest.fixture()
def client():
    channelRuntime.shutdownAll()
    devChannelRuntime.shutdown()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    channelRuntime.shutdownAll()
    devChannelRuntime.shutdown()


def test_status_includes_channels(client):
    resp = client.get("/api/status", params={"probe": 0})
    assert resp.status_code == 200
    data = resp.json()
    assert "channels" in data
    assert "telegram" in data["channels"]
    assert "slack" in data["channels"]
    assert "discord" in data["channels"]


def test_channel_start_and_stop(client, monkeypatch):
    monkeypatch.setattr("dartlab.channel.adapters.createAdapter", lambda platform, **kwargs: _FakeAdapter())

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


def test_dev_channel_status_and_start(client, monkeypatch):
    monkeypatch.setattr(
        "dartlab.server.services.devChannelRuntime.setupDevtunnel",
        lambda *, port, autoYes: ("https://dartlab-8400.jpe1.devtunnels.ms/", _FakeProcess()),
    )

    before = client.get("/api/channel")
    assert before.status_code == 200
    assert before.json()["kind"] == "devtunnel"
    assert before.json()["running"] is False

    started = client.post("/api/channel/start")
    assert started.status_code == 200
    body = started.json()
    assert body["running"] is True
    assert body["url"] == "https://dartlab-8400.jpe1.devtunnels.ms/"
    assert body["qrDataUrl"].startswith("data:image/svg+xml;base64,")

    stopped = client.post("/api/channel/stop")
    assert stopped.status_code == 200
    assert stopped.json()["running"] is False


def test_known_platform_returns_spec_key():
    """_knownPlatform 은 요청 문자열이 아니라 CHANNEL_SPECS 의 key 객체를 돌려준다."""
    from dartlab.server.services.channelRuntime import CHANNEL_SPECS, _knownPlatform

    for key in CHANNEL_SPECS:
        requested = "".join(list(key))
        assert _knownPlatform(requested) is key


@pytest.mark.parametrize("platform", ["whatsapp", "Telegram", "telegram ", "", "../telegram"])
def test_known_platform_rejects_unknown(platform):
    """미지원 채널은 기존과 같은 ValueError 메시지로 거부한다."""
    from dartlab.server.services.channelRuntime import _knownPlatform

    with pytest.raises(ValueError, match="지원하지 않는 채널"):
        _knownPlatform(platform)


def test_channel_unknown_platform_returns_400(client):
    """API 경로의 미지원 platform 은 start/stop 모두 400."""
    start = client.post("/api/channels/whatsapp/start", json={"token": "fake-token"})
    assert start.status_code == 400
    assert "지원하지 않는 채널" in start.json()["detail"]

    stop = client.post("/api/channels/whatsapp/stop")
    assert stop.status_code == 400
    assert "지원하지 않는 채널" in stop.json()["detail"]


def test_dev_channel_start_failure_hides_exception_detail(client, monkeypatch, caplog):
    """셋업 예외 문자열은 응답·상태에 싣지 않고 고정 안내만 돌려준다. 상세는 서버 로그에 남는다."""
    import logging

    from dartlab.channel import DevTunnelSetupError
    from dartlab.server.services import devChannelRuntime as devModule

    secretDetail = "devtunnel host 종료됨:\nC:/Users/someone/.dartlab/bin/devtunnel.exe token=abc123"

    def _failingSetup(*, port, autoYes):
        raise DevTunnelSetupError(secretDetail)

    monkeypatch.setattr("dartlab.server.services.devChannelRuntime.setupDevtunnel", _failingSetup)

    with caplog.at_level(logging.WARNING, logger="dartlab.server.services.devChannelRuntime"):
        started = client.post("/api/channel/start")
    assert started.status_code == 200
    body = started.json()
    assert body["running"] is False
    assert body["url"] is None
    assert body["error"] == devModule._START_FAILED_MESSAGE
    assert "token=abc123" not in started.text
    assert ".dartlab/bin" not in started.text

    status = client.get("/api/channel").json()
    assert status["error"] == devModule._START_FAILED_MESSAGE

    overall = client.get("/api/status", params={"probe": 0}).json()
    assert overall["channel"]["error"] == devModule._START_FAILED_MESSAGE

    assert any("token=abc123" in r.getMessage() for r in caplog.records)
