"""agent 모듈 테스트 — CAPABILITIES 기반 코드블록 실행."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.ai.runtime.agent import _reflect_on_answer
from dartlab.ai.runtime.core import _extractCodeBlocks
from dartlab.ai.types import ToolResponse

# ══════════════════════════════════════
# 코드블록 추출
# ══════════════════════════════════════


class TestCodeBlockExtraction:
    def test_single_block(self):
        """단일 python 코드블록 추출."""
        text = '분석합니다.\n\n```python\nprint("hello")\n```\n\n결과입니다.'
        blocks = _extractCodeBlocks(text)
        assert len(blocks) == 1
        assert 'print("hello")' in blocks[0]

    def test_multiple_blocks(self):
        """복수 코드블록 추출."""
        text = "```python\na = 1\n```\n설명\n```python\nb = 2\n```"
        blocks = _extractCodeBlocks(text)
        assert len(blocks) == 2

    def test_no_block(self):
        """코드블록 없으면 빈 리스트."""
        text = "코드가 없는 답변입니다."
        blocks = _extractCodeBlocks(text)
        assert len(blocks) == 0

    def test_non_python_block_ignored(self):
        """python이 아닌 코드블록은 무시."""
        text = '```javascript\nconsole.log("hi")\n```'
        blocks = _extractCodeBlocks(text)
        assert len(blocks) == 0


# ══════════════════════════════════════
# Reflection
# ══════════════════════════════════════


class MockProvider:
    """테스트용 mock LLM provider."""

    def __init__(self, answer: str):
        self._answer = answer

    def complete(self, messages):
        return ToolResponse(
            answer=self._answer,
            provider="mock",
            model="mock-1",
            tool_calls=[],
            finish_reason="stop",
        )


class TestReflection:
    def test_reflect_returns_improved(self):
        """reflection이 개선된 답변을 반환."""
        provider = MockProvider("개선된 답변입니다.")
        result = _reflect_on_answer(
            provider,
            [{"role": "user", "content": "질문"}],
            "원본 답변",
        )
        assert result == "개선된 답변입니다."

    def test_reflect_empty_keeps_original(self):
        """reflection이 비어있으면 원본 유지."""
        provider = MockProvider("  ")
        result = _reflect_on_answer(
            provider,
            [{"role": "user", "content": "질문"}],
            "원본 답변",
        )
        assert result == "원본 답변"
