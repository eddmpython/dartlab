"""서버 대화 헬퍼.

AI 로직은 engines/ai/에 있다. 이 모듈은 서버 전용 기능과
기존 public helper surface의 하위호환 re-export를 함께 유지한다.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab import Company
from dartlab.ai.context.snapshot import build_snapshot
from dartlab.ai.conversation.focus import build_diff_context, build_focus_context
from dartlab.ai.conversation.history import build_history_messages
from dartlab.ai.conversation.prompts import build_dynamic_chat_prompt

from .models import HistoryMessage

OLLAMA_MODEL_GUIDE: list[dict[str, str]] = [
    {
        "name": "qwen3",
        "size": "8B",
        "vram": "~6GB",
        "quality": "높음",
        "speed": "보통",
        "note": "한국어 재무분석에 가장 추천",
    },
    {"name": "gemma2", "size": "9B", "vram": "~7GB", "quality": "높음", "speed": "보통", "note": "다국어 성능 우수"},
    {"name": "llama3.2", "size": "3B", "vram": "~3GB", "quality": "보통", "speed": "빠름", "note": "저사양 PC 추천"},
    {"name": "mistral", "size": "7B", "vram": "~5GB", "quality": "보통", "speed": "빠름", "note": "영문 질문에 강함"},
    {"name": "phi4", "size": "14B", "vram": "~10GB", "quality": "매우높음", "speed": "느림", "note": "GPU 12GB+ 추천"},
    {
        "name": "qwen3:14b",
        "size": "14B",
        "vram": "~10GB",
        "quality": "매우높음",
        "speed": "느림",
        "note": "최고 품질, 고사양 PC",
    },
]


def extract_last_stock_code(history: list[HistoryMessage] | None) -> str | None:
    """히스토리에서 가장 최근 분석된 종목코드를 추출."""
    if not history:
        return None
    for h in reversed(history):
        if h.meta and h.meta.stockCode:
            return h.meta.stockCode
    return None


def build_topic_summary_prompt(
    company: Company | Any,
    topic: str,
    *,
    max_text_chars: int = 3000,
) -> tuple[list[dict[str, str]], str] | None:
    """topic 요약을 위한 LLM messages + context를 빌드한다.

    Returns:
        (messages, context_text) 또는 None.
        caller가 LLM.stream(messages)으로 요약을 생성한다.
    """
    from dartlab.ai.conversation.focus import _build_topic_diff_snippet, _stringify_focus_value

    if not hasattr(company, "show"):
        return None

    try:
        overview = company.show(topic)
    except (AttributeError, KeyError, TypeError, ValueError):
        return None
    if not isinstance(overview, pl.DataFrame) or overview.height == 0:
        return None

    corp_name = getattr(company, "corpName", "?")
    stock_code = getattr(company, "stockCode", "?")

    # 블록 데이터 수집
    parts: list[str] = [f"# {corp_name} ({stock_code}) — {topic} 요약 근거"]
    block_col = "block" if "block" in overview.columns else "blockOrder" if "blockOrder" in overview.columns else None
    total_chars = 0
    if block_col:
        for row in overview.iter_rows(named=True):
            block_idx = row.get(block_col)
            if not isinstance(block_idx, int):
                continue
            try:
                block_data = company.show(topic, block_idx)
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
            if block_data is None:
                continue
            block_text = _stringify_focus_value(block_data, max_rows=15, max_chars=1200)
            if total_chars + len(block_text) > max_text_chars:
                break
            parts.append(f"\n## block {block_idx}")
            parts.append(block_text)
            total_chars += len(block_text)

    # diff 정보 추가
    diff_snippet = _build_topic_diff_snippet(company, topic, max_entries=5)
    if diff_snippet:
        parts.append(f"\n{diff_snippet}")

    context_text = "\n".join(parts)

    system = (
        "당신은 한국 기업 공시 분석 전문가입니다. "
        "아래 데이터를 기반으로 이 섹션의 핵심을 3~5문장으로 요약하세요.\n"
        "- 수치가 있으면 반드시 포함\n"
        "- 기간간 변화가 있으면 변화 포인트 언급\n"
        "- 마지막에 한 줄 판단 (긍정/부정/중립)\n"
        "- 질문과 같은 언어로 답변"
    )
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{context_text}\n\n위 데이터를 기반으로 '{topic}' 섹션을 요약해 주세요."},
    ]
    return messages, context_text


def build_topic_summary_question(topic: str) -> str:
    """Topic summary를 core.analyze()에 요청할 때 쓰는 canonical 질문."""
    return (
        f"현재 보고 있는 '{topic}' 섹션만 기준으로 핵심을 3~5문장으로 요약해줘. "
        "수치가 있으면 포함하고, 기간 변화가 있으면 짚어주고, 마지막에 한 줄 판단을 붙여줘."
    )


__all__ = [
    "OLLAMA_MODEL_GUIDE",
    "build_diff_context",
    "build_dynamic_chat_prompt",
    "build_focus_context",
    "build_history_messages",
    "build_snapshot",
    "build_topic_summary_prompt",
    "build_topic_summary_question",
    "extract_last_stock_code",
]
