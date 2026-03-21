"""히스토리 압축/빌드 — server 의존성 없는 순수 로직.

server/chat.py의 build_history_messages(), compress_history()에서 추출.
경량 타입(types.py) 기반.
"""

from __future__ import annotations

from ..types import HistoryItem

_MAX_HISTORY_TURNS = 10
_MAX_HISTORY_CHARS = 12000
_MAX_HISTORY_MESSAGE_CHARS = 1800
_COMPRESS_TURN_THRESHOLD = 5


def _compress_history_text(text: str) -> str:
    """길어진 과거 대화를 앞뒤 핵심만 남기도록 압축."""
    if len(text) <= _MAX_HISTORY_MESSAGE_CHARS:
        return text
    head = int(_MAX_HISTORY_MESSAGE_CHARS * 0.65)
    tail = _MAX_HISTORY_MESSAGE_CHARS - head
    return text[:head].rstrip() + "\n...\n" + text[-tail:].lstrip()


def build_history_messages(history: list[HistoryItem] | None) -> list[dict[str, str]]:
    """히스토리를 LLM messages 포맷으로 변환. 최근 N턴만 유지."""
    if not history:
        return []
    trimmed = history[-(_MAX_HISTORY_TURNS * 2) :]
    prepared: list[dict[str, str]] = []
    for h in trimmed:
        role = h.role if h.role in ("user", "assistant") else "user"
        text = h.text.strip()
        if not text:
            continue
        if role == "assistant" and h.meta:
            summary_parts: list[str] = []
            if h.meta.company or h.meta.stockCode:
                company_text = h.meta.company or "?"
                if h.meta.stockCode:
                    company_text += f" ({h.meta.stockCode})"
                summary_parts.append(company_text)
            if h.meta.market:
                summary_parts.append(f"시장: {h.meta.market}")
            if h.meta.topicLabel or h.meta.topic:
                summary_parts.append(f"주제: {h.meta.topicLabel or h.meta.topic}")
            if h.meta.dialogueMode:
                summary_parts.append(f"모드: {h.meta.dialogueMode}")
            if h.meta.userGoal:
                summary_parts.append(f"목표: {h.meta.userGoal}")
            if h.meta.modules:
                summary_parts.append(f"모듈: {', '.join(h.meta.modules)}")
            if h.meta.questionTypes:
                summary_parts.append(f"유형: {', '.join(h.meta.questionTypes)}")
            if summary_parts:
                text = f"[이전 대화 상태: {' | '.join(summary_parts)}]\n{text}"
        prepared.append({"role": role, "content": _compress_history_text(text)})

    total = 0
    selected: list[dict[str, str]] = []
    for item in reversed(prepared):
        content_len = len(item["content"])
        if selected and total + content_len > _MAX_HISTORY_CHARS:
            break
        selected.append(item)
        total += content_len
    return list(reversed(selected))


def compress_history(history: list[HistoryItem] | None) -> list[HistoryItem] | None:
    """멀티턴 히스토리 압축: 오래된 턴을 구조화된 요약으로 대체.

    5턴(10 메시지) 이상이면 가장 오래된 턴들을 1개 요약 메시지로 교체.
    최근 4턴(8 메시지)은 원본 유지.
    """
    if not history or len(history) <= _COMPRESS_TURN_THRESHOLD * 2:
        return history

    keep_count = 8
    old_messages = history[:-keep_count]
    recent_messages = history[-keep_count:]

    companies_mentioned: set[str] = set()
    topics_discussed: list[str] = []
    qa_pairs: list[str] = []

    for msg in old_messages:
        text = msg.text.strip()
        if not text:
            continue

        if msg.meta:
            if msg.meta.company:
                companies_mentioned.add(msg.meta.company)
            if msg.meta.topicLabel:
                topics_discussed.append(msg.meta.topicLabel)

        if msg.role == "user":
            brief = text[:80] + "..." if len(text) > 80 else text
            qa_pairs.append(f"- Q: {brief}")
        elif msg.role == "assistant":
            sentences = text.split(".")
            brief = ".".join(sentences[:2]).strip()
            if brief and not brief.endswith("."):
                brief += "."
            if len(brief) > 150:
                brief = brief[:150] + "..."
            if brief:
                qa_pairs.append(f"  A: {brief}")

    if not qa_pairs:
        return history

    summary_lines = ["[이전 대화 요약]"]
    if companies_mentioned:
        summary_lines.append(f"관심 기업: {', '.join(sorted(companies_mentioned))}")
    if topics_discussed:
        unique_topics = list(dict.fromkeys(topics_discussed))[:5]
        summary_lines.append(f"분석 주제: {', '.join(unique_topics)}")
    summary_lines.append("")
    summary_lines.extend(qa_pairs[-8:])

    summary_text = "\n".join(summary_lines)
    summary_msg = HistoryItem(role="assistant", text=summary_text)
    return [summary_msg, *recent_messages]
