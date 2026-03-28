"""Discord 채널 어댑터 — Gateway + Slash Command.

사용:
    dartlab share --discord $BOT_TOKEN
"""

from __future__ import annotations

import logging

from dartlab.channel.adapters.base import ChannelAdapter

logger = logging.getLogger(__name__)


class DiscordAdapter(ChannelAdapter):
    """discord.py 기반 Discord 어댑터."""

    name = "discord"
    max_message_length = 2000

    def __init__(self, token: str):
        self._token = token
        self._bot = None

    async def start(self) -> None:
        """Discord 봇을 시작하고 이벤트 리스너 등록."""
        try:
            import discord
            from discord import app_commands
            from discord.ext import commands
        except ImportError as exc:
            raise RuntimeError("Discord 어댑터를 사용하려면:\n  uv pip install discord.py") from exc

        intents = discord.Intents.default()
        intents.message_content = True
        bot = commands.Bot(command_prefix="!", intents=intents)
        self._bot = bot
        adapter = self

        @bot.event
        async def on_ready():
            logger.info("Discord 봇 준비 완료: %s", bot.user)
            try:
                synced = await bot.tree.sync()
                logger.info("Slash commands 동기화: %d개", len(synced))
            except discord.HTTPException:
                logger.warning("Slash commands 동기화 실패")

        @bot.tree.command(name="ask", description="DartLab 기업 분석")
        @app_commands.describe(query="종목명 + 질문 (예: 삼성전자 배당 분석)")
        async def ask_cmd(interaction: discord.Interaction, query: str):
            await interaction.response.defer()
            channel_id = str(interaction.channel_id)

            # handle_ask가 send_text를 호출하므로, followup으로 대체
            adapter._interaction = interaction
            adapter._followup_sent = False
            await adapter.handle_ask(channel_id, query)

        @bot.event
        async def on_message(message: discord.Message):
            if message.author == bot.user:
                return
            # DM이거나 봇이 멘션된 경우
            is_dm = message.guild is None
            is_mentioned = bot.user in message.mentions if bot.user else False
            if not is_dm and not is_mentioned:
                return

            text = message.content
            # 멘션 제거
            if bot.user:
                text = text.replace(f"<@{bot.user.id}>", "").strip()

            adapter._interaction = None
            adapter._channel_obj = message.channel
            await adapter.handle_ask(str(message.channel.id), text)

        logger.info("Discord 봇 시작")
        await bot.start(self._token)

    async def stop(self) -> None:
        """Discord 봇 연결 종료."""
        if self._bot:
            await self._bot.close()

    async def send_text(self, channel_id: str, text: str) -> None:
        """Discord 채널에 텍스트 메시지 전송."""
        # slash command의 경우 followup 사용
        interaction = getattr(self, "_interaction", None)
        if interaction is not None:
            if not getattr(self, "_followup_sent", False):
                await interaction.followup.send(text)
                self._followup_sent = True
            else:
                await interaction.followup.send(text)
            return

        # 일반 메시지의 경우
        channel = getattr(self, "_channel_obj", None)
        if channel:
            await channel.send(text)
        elif self._bot:
            ch = self._bot.get_channel(int(channel_id))
            if ch:
                await ch.send(text)


def create(*, token: str, **kwargs) -> DiscordAdapter:
    """DiscordAdapter 팩토리."""
    return DiscordAdapter(token)
