"""외부 채널 런타임 관리.

Telegram / Slack / Discord 어댑터를 현재 서버 프로세스 안에서
백그라운드 스레드로 시작/정지하고 상태를 노출한다.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


CHANNEL_SPECS: dict[str, dict[str, Any]] = {
    "telegram": {
        "label": "Telegram",
        "fields": ("token",),
        "description": "BotFather 토큰으로 polling 봇을 연결합니다.",
    },
    "slack": {
        "label": "Slack",
        "fields": ("botToken", "appToken"),
        "description": "Socket Mode용 bot/app token을 사용합니다.",
    },
    "discord": {
        "label": "Discord",
        "fields": ("token",),
        "description": "Gateway + slash command 봇을 연결합니다.",
    },
}


@dataclass
class ChannelSession:
    """개별 채널 어댑터의 실행 상태."""

    platform: str
    adapter: Any
    thread: threading.Thread
    loop: asyncio.AbstractEventLoop | None = None
    running: bool = False
    started_at: float | None = None
    error: str | None = None


class ChannelRuntimeManager:
    """채널 어댑터 백그라운드 실행 관리자."""

    def __init__(self) -> None:
        self._sessions: dict[str, ChannelSession] = {}
        self._lock = threading.Lock()

    def _base_payload(self, platform: str) -> dict[str, Any]:
        spec = CHANNEL_SPECS[platform]
        session = self._sessions.get(platform)
        return {
            "platform": platform,
            "label": spec["label"],
            "fields": list(spec["fields"]),
            "description": spec["description"],
            "running": bool(session and session.running and session.thread.is_alive()),
            "startedAt": session.started_at if session else None,
            "error": session.error if session else None,
        }

    def status(self) -> dict[str, dict[str, Any]]:
        """모든 채널의 현재 상태를 반환한다."""
        return {platform: self._base_payload(platform) for platform in CHANNEL_SPECS}

    def get(self, platform: str) -> dict[str, Any]:
        """특정 채널의 상태를 반환한다."""
        if platform not in CHANNEL_SPECS:
            raise ValueError(f"지원하지 않는 채널: {platform}")
        return self._base_payload(platform)

    def start(self, platform: str, **kwargs) -> dict[str, Any]:
        """채널 어댑터를 백그라운드 스레드로 시작한다."""
        if platform not in CHANNEL_SPECS:
            raise ValueError(f"지원하지 않는 채널: {platform}")

        from dartlab.channel.adapters import create_adapter

        with self._lock:
            existing = self._sessions.get(platform)
            if existing and existing.running and existing.thread.is_alive():
                raise ValueError(f"{CHANNEL_SPECS[platform]['label']} 채널이 이미 실행 중입니다.")

            mapped_kwargs = self._map_kwargs(platform, kwargs)
            adapter = create_adapter(platform, **mapped_kwargs)
            session = ChannelSession(
                platform=platform,
                adapter=adapter,
                thread=threading.Thread(
                    target=self._run_session,
                    args=(platform,),
                    name=f"dartlab-channel-{platform}",
                    daemon=True,
                ),
            )
            self._sessions[platform] = session
            session.thread.start()

        deadline = time.time() + 1.0
        while time.time() < deadline:
            current = self._sessions.get(platform)
            if current is None:
                break
            if current.error or current.running or current.loop is not None:
                break
            time.sleep(0.02)
        return self.get(platform)

    def stop(self, platform: str) -> dict[str, Any]:
        """채널 어댑터를 정지한다."""
        if platform not in CHANNEL_SPECS:
            raise ValueError(f"지원하지 않는 채널: {platform}")

        session = self._sessions.get(platform)
        if session is None:
            return self.get(platform)

        loop = session.loop
        if loop is not None and loop.is_running():
            future = asyncio.run_coroutine_threadsafe(session.adapter.stop(), loop)
            try:
                future.result(timeout=5)
            except Exception as exc:  # noqa: BLE001
                session.error = f"종료 실패: {exc}"
                logger.warning("채널 종료 실패 (%s): %s", platform, exc)

        session.thread.join(timeout=5)
        if session.thread.is_alive() and session.loop is not None and session.loop.is_running():
            session.error = session.error or "종료 시간 초과"
            try:
                session.loop.call_soon_threadsafe(session.loop.stop)
            except RuntimeError:
                pass
            session.thread.join(timeout=1)

        session.running = False
        session.loop = None
        return self.get(platform)

    def shutdown_all(self) -> None:
        """모든 채널 어댑터를 순차 종료한다."""
        for platform in list(CHANNEL_SPECS):
            try:
                self.stop(platform)
            except ValueError:
                continue

    def _run_session(self, platform: str) -> None:
        session = self._sessions[platform]
        loop = asyncio.new_event_loop()
        session.loop = loop
        asyncio.set_event_loop(loop)
        session.running = True
        session.started_at = time.time()
        session.error = None
        try:
            loop.run_until_complete(session.adapter.start())
        except Exception as exc:  # noqa: BLE001
            session.error = str(exc)
            logger.exception("채널 시작 실패 (%s): %s", platform, exc)
        finally:
            session.running = False
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                try:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except RuntimeError:
                    pass
            loop.close()
            session.loop = None

    @staticmethod
    def _map_kwargs(platform: str, payload: dict[str, Any]) -> dict[str, Any]:
        if platform == "slack":
            bot_token = (payload.get("botToken") or "").strip()
            app_token = (payload.get("appToken") or "").strip()
            if not bot_token or not app_token:
                raise ValueError("Slack 연결에는 bot token과 app token이 모두 필요합니다.")
            return {"bot_token": bot_token, "app_token": app_token}

        token = (payload.get("token") or "").strip()
        if not token:
            raise ValueError(f"{CHANNEL_SPECS[platform]['label']} 연결에는 토큰이 필요합니다.")
        return {"token": token}


channel_runtime = ChannelRuntimeManager()
