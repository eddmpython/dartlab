"""메시징 채널 어댑터 추상 클래스 + 공통 분석 로직."""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


def _chunk_text(text: str, max_len: int) -> list[str]:
    """텍스트를 max_len 이하 청크로 분할한다.

    문단(\\n\\n) → 줄(\\n) → 강제 분할 순으로 시도.
    """
    if len(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_len:
            chunks.append(remaining)
            break

        # 문단 경계에서 분할 시도
        cut = remaining.rfind("\n\n", 0, max_len)
        if cut > 0:
            chunks.append(remaining[:cut])
            remaining = remaining[cut + 2 :]
            continue

        # 줄 경계에서 분할 시도
        cut = remaining.rfind("\n", 0, max_len)
        if cut > 0:
            chunks.append(remaining[:cut])
            remaining = remaining[cut + 1 :]
            continue

        # 강제 분할
        chunks.append(remaining[:max_len])
        remaining = remaining[max_len:]

    return chunks


class ChannelAdapter(ABC):
    """메시징 채널 어댑터 추상 클래스."""

    name: str = "base"
    max_message_length: int = 4000

    @abstractmethod
    async def start(self) -> None:
        """어댑터를 시작한다 (blocking)."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """어댑터를 정리한다."""
        ...

    @abstractmethod
    async def send_text(self, channel_id: str, text: str) -> None:
        """텍스트 메시지를 전송한다."""
        ...

    async def handle_ask(self, channel_id: str, user_text: str) -> None:
        """사용자 메시지를 분석하고 응답을 전송한다.

        모든 어댑터가 공유하는 핵심 로직:
        1. AI에 질문 전달 (종목은 AI가 자율 판단)
        2. 응답 청킹 + 전송
        """
        user_text = user_text.strip()
        if not user_text:
            await self.send_text(channel_id, "질문을 입력해주세요. 예: 삼성전자 재무분석")
            return

        question = user_text
        await self.send_text(channel_id, "분석 중...")

        # AI 분석 실행 (blocking → asyncio.to_thread)
        try:
            answer = await asyncio.to_thread(self._run_analysis, None, question)
        except Exception as exc:  # noqa: BLE001
            logger.exception("분석 실패: %s", exc)
            await self.send_text(channel_id, f"분석 중 오류가 발생했습니다: {exc}")
            return

        # 응답 청킹 + 전송
        chunks = _chunk_text(answer, self.max_message_length)
        for chunk in chunks:
            await self.send_text(channel_id, chunk)

    @staticmethod
    def _run_analysis(company, question: str) -> str:
        """AI 분석을 실행하고 텍스트를 반환한다 (동기)."""
        from dartlab.ai.runtime.standalone import ask

        return ask(question, company=company, stream=False)
