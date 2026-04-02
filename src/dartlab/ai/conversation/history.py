"""히스토리 압축/빌드 — server 의존성 없는 순수 로직.

server/chat.py의 build_history_messages(), compress_history()에서 추출.
경량 타입(types.py) 기반.
"""

from __future__ import annotations

import re

from ..types import HistoryItem

_MAX_HISTORY_TURNS_DEFAULT = 10
_MAX_HISTORY_CHARS = 12000
_MAX_HISTORY_MESSAGE_CHARS = 1800
_COMPRESS_TURN_THRESHOLD = 5


def _dynamicMaxTurns(historyItems: list[HistoryItem]) -> int:
    """Dynamic history window based on average message length."""
    if not historyItems:
        return _MAX_HISTORY_TURNS_DEFAULT
    avgLen = sum(len(h.text) for h in historyItems) / len(historyItems)
    if avgLen < 200:
        return 15  # short Q&A exchanges: keep more turns
    if avgLen > 1000:
        return 6  # long analysis responses: keep fewer turns
    return _MAX_HISTORY_TURNS_DEFAULT


_METRIC_LINE_RE = re.compile(
    r"^\s*\|.*\|.*\|",  # 마크다운 테이블 행
    re.MULTILINE,
)
_GRADE_RE = re.compile(r"dCR-[A-D][A-D+\-]*|건전도\s*[\d.]+|ROE\s*=?\s*[\d.]+%|영업이익률\s*[\d.]+%")


def _extractKeyLines(text: str) -> str:
    """텍스트에서 핵심 수치 행(테이블, 등급)을 추출. 압축 시 보존용."""
    lines = []
    for match in _GRADE_RE.finditer(text):
        lines.append(match.group())
    # 마크다운 테이블의 헤더+첫 2행만 보존
    tableLines = _METRIC_LINE_RE.findall(text)
    if len(tableLines) >= 3:
        lines.extend(tableLines[:3])
    return " | ".join(lines[:5]) if lines else ""


def _compress_history_text(text: str) -> str:
    """길어진 과거 대화를 앞뒤 핵심만 남기도록 압축.

    문장 경계(마침표, 줄바꿈)를 존중하여 의미 단위로 절단한다.
    핵심 수치(등급, ROE, 테이블)는 압축에서 보존한다.
    """
    if len(text) <= _MAX_HISTORY_MESSAGE_CHARS:
        return text

    # 핵심 수치 추출 (압축 후 끝에 추가)
    keyLines = _extractKeyLines(text)

    head = int(_MAX_HISTORY_MESSAGE_CHARS * 0.6)
    tail = _MAX_HISTORY_MESSAGE_CHARS - head - len(keyLines) - 20

    # 앞부분: head 근처의 마지막 문장 경계
    head_text = text[:head]
    for sep in ("\n", "다. ", ". ", "? ", "! "):
        idx = head_text.rfind(sep)
        if idx > head * 0.5:
            head_text = head_text[: idx + len(sep)]
            break

    # 뒷부분: -tail 근처의 첫 문장 경계
    tail_text = text[-max(tail, 200):]
    for sep in ("\n", "다. ", ". ", "? ", "! "):
        idx = tail_text.find(sep)
        if idx != -1 and idx < len(tail_text) * 0.3:
            tail_text = tail_text[idx + len(sep) :]
            break

    compressed = head_text.rstrip() + "\n...\n" + tail_text.lstrip()
    if keyLines:
        compressed += f"\n[핵심 수치: {keyLines}]"
    return compressed


def build_history_messages(history: list[HistoryItem] | None) -> list[dict[str, str]]:
    """히스토리를 LLM messages 포맷으로 변환. 최근 N턴만 유지."""
    if not history:
        return []
    maxTurns = _dynamicMaxTurns(history)
    trimmed = history[-(maxTurns * 2) :]
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


_CODE_BLOCK_RE = re.compile(r"```[\s\S]*?```")
_TABLE_ROW_RE = re.compile(r"^\|.*\|$", re.MULTILINE)
_ANALYSIS_TAG_RE = re.compile(r"<analysis>[\s\S]*?</analysis>")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _strip_non_essential(text: str) -> str:
    """코드블록, 테이블, analysis 태그를 제거하여 핵심 해석만 남긴다."""
    text = _CODE_BLOCK_RE.sub("", text)
    text = _TABLE_ROW_RE.sub("", text)
    text = _ANALYSIS_TAG_RE.sub("", text)
    text = _BLANK_LINES_RE.sub("\n\n", text)
    return text.strip()


def compress_history(history: list[HistoryItem] | None) -> list[HistoryItem] | None:
    """멀티턴 히스토리 압축: 오래된 턴을 구조화된 요약으로 대체.

    5턴(10 메시지) 이상이면 가장 오래된 턴들을 1개 요약 메시지로 교체.
    최근 4턴(8 메시지)은 원본 유지.

    Claude Code compaction 패턴 흡수:
    - 비핵심 콘텐츠(코드블록/테이블) 제거 후 압축
    - summarizeResponse()로 종합/결론 섹션 추출 시도
    - 압축 후 "이어서 진행" 지시 추가
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
            cleaned = _strip_non_essential(text)
            # summarizeResponse로 종합/결론 섹션 추출 시도
            try:
                from ..memory.summarizer import summarizeResponse

                summary = summarizeResponse(cleaned, maxChars=150)
            except ImportError:
                summary = ""
            if not summary:
                sentences = cleaned.split(".")
                summary = ".".join(sentences[:2]).strip()
                if summary and not summary.endswith("."):
                    summary += "."
                if len(summary) > 150:
                    summary = summary[:150] + "..."
            if summary:
                qa_pairs.append(f"  A: {summary}")

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
    summary_lines.append("")
    summary_lines.append("위 대화를 이어서 진행하라. 이미 논의된 내용을 반복하지 마라.")

    summary_text = "\n".join(summary_lines)
    summary_msg = HistoryItem(role="assistant", text=summary_text)
    return [summary_msg, *recent_messages]
