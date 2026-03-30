"""Channel adapters tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit

from dartlab.channel.adapters.base import ChannelAdapter, _chunk_text

# ---------------------------------------------------------------------------
# 청킹 테스트
# ---------------------------------------------------------------------------


class TestChunkText:
    def test_short_text_no_split(self):
        result = _chunk_text("hello world", 100)
        assert result == ["hello world"]

    def test_split_on_paragraph(self):
        text = "first paragraph\n\nsecond paragraph\n\nthird paragraph"
        result = _chunk_text(text, 30)
        assert len(result) >= 2
        assert "first paragraph" in result[0]

    def test_split_on_newline(self):
        text = "line1\nline2\nline3\nline4"
        result = _chunk_text(text, 12)
        assert all(len(chunk) <= 12 for chunk in result)

    def test_force_split(self):
        text = "a" * 100
        result = _chunk_text(text, 30)
        assert all(len(chunk) <= 30 for chunk in result)
        assert "".join(result) == text

    def test_empty_text(self):
        result = _chunk_text("", 100)
        assert result == [""]

    def test_exact_limit(self):
        text = "a" * 50
        result = _chunk_text(text, 50)
        assert result == [text]

    def test_telegram_limit(self):
        text = "x" * 8000
        result = _chunk_text(text, 4096)
        assert all(len(chunk) <= 4096 for chunk in result)

    def test_discord_limit(self):
        text = "x" * 5000
        result = _chunk_text(text, 2000)
        assert all(len(chunk) <= 2000 for chunk in result)


# ---------------------------------------------------------------------------
# 팩토리 테스트
# ---------------------------------------------------------------------------


class TestCreateAdapter:
    def test_unknown_platform_raises(self):
        from dartlab.channel.adapters import create_adapter

        with pytest.raises(ValueError, match="알 수 없는 채널"):
            create_adapter("whatsapp")

    def test_telegram_factory(self):
        with patch("dartlab.channel.adapters.telegram.TelegramAdapter") as mock:
            mock.return_value = MagicMock(spec=ChannelAdapter)
            from dartlab.channel.adapters import create_adapter

            adapter = create_adapter("telegram", token="fake-token")
            assert adapter is not None


# ---------------------------------------------------------------------------
# handle_ask 테스트
# ---------------------------------------------------------------------------


class MockAdapter(ChannelAdapter):
    name = "mock"
    max_message_length = 100

    def __init__(self):
        self.sent: list[tuple[str, str]] = []

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def send_text(self, channel_id: str, text: str) -> None:
        self.sent.append((channel_id, text))


class TestHandleAsk:
    @pytest.mark.asyncio
    async def test_empty_input(self):
        adapter = MockAdapter()
        await adapter.handle_ask("ch1", "")
        assert len(adapter.sent) == 1
        assert "질문을 입력" in adapter.sent[0][1]

    @pytest.mark.asyncio
    async def test_any_question_goes_to_ai(self):
        """종목 없는 질문도 AI에 전달된다 (company=None)."""
        with patch("dartlab.channel.adapters.base.ChannelAdapter._run_analysis", return_value="답변입니다") as mock_run:
            adapter = MockAdapter()
            await adapter.handle_ask("ch1", "blah blah")
            # "분석 중..." + 결과 = 2개 메시지
            assert len(adapter.sent) == 2
            assert "분석 중" in adapter.sent[0][1]
            assert "답변" in adapter.sent[1][1]
            # company=None으로 호출됨
            mock_run.assert_called_once_with(None, "blah blah")

    @pytest.mark.asyncio
    async def test_successful_analysis(self):
        with patch("dartlab.channel.adapters.base.ChannelAdapter._run_analysis", return_value="삼성전자의 배당은..."):
            adapter = MockAdapter()
            await adapter.handle_ask("ch1", "삼성전자 배당 분석")
            # "분석 중..." + 결과 = 2개 메시지
            assert len(adapter.sent) == 2
            assert "분석 중" in adapter.sent[0][1]
            assert "배당은" in adapter.sent[1][1]

    @pytest.mark.asyncio
    async def test_long_response_chunked(self):
        long_text = "x" * 250

        with patch("dartlab.channel.adapters.base.ChannelAdapter._run_analysis", return_value=long_text):
            adapter = MockAdapter()
            await adapter.handle_ask("ch1", "테스트 분석")
            # "분석 중..." + 청크들
            assert len(adapter.sent) >= 3
            # 모든 청크가 max_message_length 이하
            for _, text in adapter.sent[1:]:
                assert len(text) <= 100
