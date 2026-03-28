"""Slack 채널 어댑터 — Socket Mode.

사용:
    dartlab share --slack $BOT_TOKEN --slack-app-token $APP_TOKEN
"""

from __future__ import annotations

import asyncio
import inspect
import logging

from dartlab.channel.adapters.base import ChannelAdapter

logger = logging.getLogger(__name__)


class SlackAdapter(ChannelAdapter):
    """slack-bolt 기반 Slack 어댑터 (Socket Mode)."""

    name = "slack"
    max_message_length = 3000

    def __init__(self, bot_token: str, app_token: str):
        self._bot_token = bot_token
        self._app_token = app_token
        self._app = None
        self._client = None
        self._handler = None

    async def start(self) -> None:
        """Slack 봇을 Socket Mode로 시작."""
        try:
            from slack_bolt import App
            from slack_bolt.adapter.socket_mode import SocketModeHandler
        except ImportError as exc:
            raise RuntimeError("Slack 어댑터를 사용하려면:\n  uv pip install slack-bolt") from exc

        app = App(token=self._bot_token)
        self._app = app
        self._client = app.client
        adapter = self

        @app.event("app_mention")
        def on_mention(event, say):
            text = event.get("text", "")
            # @bot 멘션 제거
            import re

            text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()
            channel = event["channel"]

            import asyncio

            asyncio.run(adapter.handle_ask(channel, text))

        @app.event("message")
        def on_dm(event, say):
            # DM에서는 멘션 없이 바로 처리
            if event.get("channel_type") != "im":
                return
            text = event.get("text", "").strip()
            channel = event["channel"]

            import asyncio

            asyncio.run(adapter.handle_ask(channel, text))

        logger.info("Slack 봇 시작 (Socket Mode)")
        handler = SocketModeHandler(app, self._app_token)
        self._handler = handler
        await asyncio.to_thread(handler.start)

    async def stop(self) -> None:
        """Slack 봇 연결 종료."""
        if self._handler is None:
            return
        close = getattr(self._handler, "close", None)
        if callable(close):
            await asyncio.to_thread(close)
            return

        client = getattr(self._handler, "client", None)
        disconnect = getattr(client, "disconnect", None) if client else None
        if callable(disconnect):
            result = disconnect()
            if inspect.isawaitable(result):
                await result

    async def send_text(self, channel_id: str, text: str) -> None:
        """Slack 채널에 텍스트 메시지 전송."""
        if self._client:
            self._client.chat_postMessage(channel=channel_id, text=text)


def create(*, bot_token: str, app_token: str, **kwargs) -> SlackAdapter:
    """SlackAdapter 팩토리."""
    return SlackAdapter(bot_token, app_token)
