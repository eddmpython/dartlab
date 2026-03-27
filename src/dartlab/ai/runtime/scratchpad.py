"""도구 결과 누적/정리 엔진 — dexter scratchpad 패턴.

에이전트 루프에서 도구 호출 결과를 구조적으로 관리한다:
- 도구별 호출 횟수 추적 + 중복 방지
- 토큰 예산 초과 시 오래된 결과 압축
- LLM에 전달할 정리된 컨텍스트 생성
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Entry:
    """단일 도구 호출 결과."""

    toolName: str
    args: dict[str, Any]
    result: str
    tokenEstimate: int
    order: int


@dataclass
class Scratchpad:
    """에이전트 루프 도구 결과 누적/정리."""

    entries: list[_Entry] = field(default_factory=list)
    callCounts: dict[str, int] = field(default_factory=dict)
    _order: int = field(default=0, repr=False)
    tokenBudget: int = 8000

    # ── 핵심 API ──────────────────────────────────────

    def addEntry(self, toolName: str, args: dict[str, Any], result: str) -> None:
        """도구 결과 추가 (pruning 자동 적용)."""
        from dartlab.ai.context.pruning import pruneToolResult

        pruned = pruneToolResult(toolName, result)
        tokens = _estimateTokens(pruned)
        self._order += 1
        self.entries.append(_Entry(toolName, args, pruned, tokens, self._order))
        self.callCounts[toolName] = self.callCounts.get(toolName, 0) + 1
        self.pruneIfNeeded()

    def isDuplicateExceeded(self, toolName: str, maxCalls: int = 3) -> bool:
        """같은 도구가 maxCalls 이상 호출됐는지."""
        return self.callCounts.get(toolName, 0) >= maxCalls

    def pruneIfNeeded(self) -> None:
        """토큰 예산 초과 시 오래된 결과를 1줄 요약으로 압축."""
        while self._totalTokens() > self.tokenBudget and len(self.entries) > 1:
            oldest = self.entries[0]
            summary = _summarizeLine(oldest.toolName, oldest.result)
            oldest.result = summary
            oldest.tokenEstimate = _estimateTokens(summary)

            # 요약해도 여전히 초과면 제거
            if self._totalTokens() > self.tokenBudget:
                self.entries.pop(0)

    def toContext(self) -> str:
        """누적 결과를 마크다운으로 변환."""
        if not self.entries:
            return ""
        parts: list[str] = []
        for e in self.entries:
            argsStr = ", ".join(f"{k}={v}" for k, v in e.args.items()) if e.args else ""
            parts.append(f"### {e.toolName}({argsStr})\n{e.result}")
        return "\n\n".join(parts)

    def getUsageSummary(self) -> str:
        """현재 도구 호출 현황 텍스트."""
        if not self.callCounts:
            return ""
        lines = [f"- {name}: {count}회" for name, count in self.callCounts.items()]
        total = self._totalTokens()
        lines.append(f"- 컨텍스트: ~{total} 토큰 / {self.tokenBudget} 예산")
        return "**도구 사용 현황:**\n" + "\n".join(lines)

    def getDuplicateWarning(self, toolName: str) -> str | None:
        """중복 초과 시 LLM에 전달할 경고 메시지."""
        if not self.isDuplicateExceeded(toolName):
            return None
        count = self.callCounts.get(toolName, 0)
        return (
            f"⚠️ {toolName}을 이미 {count}회 호출했습니다. "
            f"같은 도구를 반복 호출하지 말고, 수집된 데이터로 답변을 종합하세요."
        )

    # ── 내부 ──────────────────────────────────────────

    def _totalTokens(self) -> int:
        return sum(e.tokenEstimate for e in self.entries)


def _estimateTokens(text: str) -> int:
    """간이 토큰 추정 — 한글 2자=1토큰, 영문 4자=1토큰 근사."""
    if not text:
        return 0
    korean = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    other = len(text) - korean
    return korean // 2 + other // 4 + 1


def _summarizeLine(toolName: str, result: str) -> str:
    """도구 결과를 1줄 요약으로 압축."""
    # 첫 줄 또는 첫 100자 + 줄 수 정보
    lines = result.strip().split("\n")
    firstLine = lines[0][:100] if lines else ""
    if len(lines) > 1:
        return f"[요약] {firstLine}... ({len(lines)}줄, {toolName})"
    return f"[요약] {firstLine}"
