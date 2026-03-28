"""도구 결과 누적/정리 엔진 — dexter scratchpad 패턴.

에이전트 루프에서 도구 호출 결과를 구조적으로 관리한다:
- 도구별 호출 횟수 추적 + 중복 방지 (soft warning + hard block)
- 동일 인자 호출은 캐시 반환으로 즉시 차단
- 토큰 예산 초과 시 계층적 pruning (필드 제거 → 배열 축소 → 요약 → 삭제)
- LLM에 전달할 정리된 컨텍스트 생성
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

# ── 도구 카테고리별 최대 호출 횟수 ──────────────────
# data 도구: 여러 종목/모듈을 각각 조회해야 하므로 넉넉하게
# analysis 도구: 파생 계산이므로 적게
# meta 도구: 시스템 정보 조회는 1-2회면 충분
_CATEGORY_MAX_CALLS: dict[str, int] = {
    "data": 5,
    "analysis": 3,
    "meta": 2,
}

# 도구 → 카테고리 매핑
_TOOL_CATEGORY: dict[str, str] = {
    # data: 원본 데이터 조회
    "finance": "data",
    "explore": "data",
    "scan": "data",
    "gather": "data",
    "openapi": "data",
    "research": "data",
    # analysis: 파생 계산
    "analysis": "analysis",
    "review": "analysis",
    "chart": "analysis",
    # meta: 시스템/스펙 조회
    "system": "meta",
    # legacy compatibility
    "market": "data",
    "analyze": "analysis",
}

_DEFAULT_MAX_CALLS = 3


def _toolCategory(toolName: str) -> str:
    return _TOOL_CATEGORY.get(toolName, "data")


def _maxCallsFor(toolName: str) -> int:
    cat = _toolCategory(toolName)
    return _CATEGORY_MAX_CALLS.get(cat, _DEFAULT_MAX_CALLS)


def _argsHash(args: dict[str, Any]) -> str:
    """인자 dict의 결정적 해시 (동일 인자 호출 감지용)."""
    normalized = json.dumps(args, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


@dataclass
class _Entry:
    """단일 도구 호출 결과."""

    toolName: str
    args: dict[str, Any]
    argsHash: str
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
    # (toolName, argsHash) → result 캐시 (동일 인자 즉시 반환)
    _resultCache: dict[tuple[str, str], str] = field(default_factory=dict)
    # 카테고리별 최대 호출 오버라이드 (비교 분석 등 확장 필요 시)
    maxCallOverrides: dict[str, int] | None = None

    # ── 핵심 API ──────────────────────────────────────

    def _maxCallsForTool(self, toolName: str) -> int:
        """카테고리별 최대 호출 수 (인스턴스 오버라이드 우선)."""
        if self.maxCallOverrides:
            cat = _toolCategory(toolName)
            if cat in self.maxCallOverrides:
                return self.maxCallOverrides[cat]
        return _maxCallsFor(toolName)

    def addEntry(self, toolName: str, args: dict[str, Any], result: str) -> None:
        """도구 결과 추가 (pruning 자동 적용)."""
        from dartlab.ai.context.pruning import pruneToolResult

        pruned = pruneToolResult(toolName, result)
        tokens = _estimateTokens(pruned)
        aHash = _argsHash(args)
        self._order += 1
        self.entries.append(_Entry(toolName, args, aHash, pruned, tokens, self._order))
        self.callCounts[toolName] = self.callCounts.get(toolName, 0) + 1
        self._resultCache[(toolName, aHash)] = pruned
        self.pruneIfNeeded()

    def checkDuplicate(self, toolName: str, args: dict[str, Any]) -> tuple[str, str | None]:
        """중복 호출 검사. 3가지 결과:

        Returns:
            ("ok", None) — 호출 허용
            ("cached", cachedResult) — 동일 인자 재호출, 캐시 결과 반환
            ("blocked", warningMsg) — 카테고리 한도 초과, 차단
        """
        aHash = _argsHash(args)

        # 1. 완전 동일 호출 → 캐시 반환
        cached = self._resultCache.get((toolName, aHash))
        if cached is not None:
            return ("cached", f"[캐시] 동일한 호출({toolName})의 이전 결과를 재사용합니다:\n{cached}")

        # 2. 카테고리별 한도 초과 → hard block
        maxCalls = self._maxCallsForTool(toolName)
        count = self.callCounts.get(toolName, 0)
        if count >= maxCalls:
            return (
                "blocked",
                f"[차단] {toolName}을 이미 {count}회 호출했습니다 (한도: {maxCalls}회). "
                f"추가 호출이 차단되었습니다. 수집된 데이터로 최종 답변을 작성하세요.",
            )

        return ("ok", None)

    def isDuplicateExceeded(self, toolName: str, maxCalls: int = 3) -> bool:
        """같은 도구가 maxCalls 이상 호출됐는지 (하위호환)."""
        return self.callCounts.get(toolName, 0) >= maxCalls

    def pruneIfNeeded(self) -> None:
        """토큰 예산 초과 시 계층적 pruning.

        Level 1: 배열 길이 축소 (JSON 배열 10개까지)
        Level 2: 오래된 결과 1줄 요약
        Level 3: 가장 오래된 항목 삭제
        """
        # Level 1: 배열 축소
        if self._totalTokens() > self.tokenBudget:
            for entry in self.entries:
                shrunk = _shrinkArrays(entry.result, maxItems=10)
                if shrunk != entry.result:
                    entry.result = shrunk
                    entry.tokenEstimate = _estimateTokens(shrunk)

        # Level 2 + 3: 요약 → 삭제 (오래된 순)
        while self._totalTokens() > self.tokenBudget and len(self.entries) > 1:
            oldest = self.entries[0]
            summary = _summarizeLine(oldest.toolName, oldest.result)
            oldest.result = summary
            oldest.tokenEstimate = _estimateTokens(summary)

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
        """중복 초과 시 LLM에 전달할 경고 메시지 (하위호환)."""
        if not self.isDuplicateExceeded(toolName, maxCalls=_maxCallsFor(toolName)):
            return None
        count = self.callCounts.get(toolName, 0)
        return (
            f"[차단] {toolName}을 이미 {count}회 호출했습니다. "
            f"같은 도구를 반복 호출하지 말고, 수집된 데이터로 답변을 종합하세요."
        )

    # ── 내부 ──────────────────────────────────────────

    def _totalTokens(self) -> int:
        return sum(e.tokenEstimate for e in self.entries)


def _estimateTokens(text: str) -> int:
    """토큰 추정 — tiktoken 가능하면 사용, 아니면 보수적 근사.

    한글은 실제로 1자 ~ 1.5토큰, 영문 4자 ~ 1토큰.
    기존 근사(한글 2자=1토큰)는 과소 추정이었으므로 보수적으로 조정.
    """
    if not text:
        return 0

    # tiktoken이 있으면 정확한 계산
    try:
        import tiktoken

        enc = tiktoken.encoding_for_model("gpt-4o")
        return len(enc.encode(text))
    except (ImportError, KeyError):
        pass

    # fallback: 보수적 근사
    korean = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    other = len(text) - korean
    # 한글: ~1.3토큰/자, 영문: ~0.25토큰/자 (4자=1토큰)
    return int(korean * 1.3) + other // 4 + 1


def _summarizeLine(toolName: str, result: str) -> str:
    """도구 결과를 1줄 요약으로 압축."""
    lines = result.strip().split("\n")
    firstLine = lines[0][:100] if lines else ""
    if len(lines) > 1:
        return f"[요약] {firstLine}... ({len(lines)}줄, {toolName})"
    return f"[요약] {firstLine}"


def _shrinkArrays(text: str, maxItems: int = 10) -> str:
    """JSON 텍스트 내 배열을 maxItems까지 축소."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text

    shrunk = _shrinkValue(data, maxItems)
    return json.dumps(shrunk, ensure_ascii=False, indent=2, default=str)


def _shrinkValue(value: Any, maxItems: int) -> Any:
    """재귀적으로 배열 길이 축소."""
    if isinstance(value, dict):
        return {k: _shrinkValue(v, maxItems) for k, v in value.items()}
    if isinstance(value, list):
        if len(value) > maxItems:
            kept = [_shrinkValue(item, maxItems) for item in value[:maxItems]]
            kept.append({"_truncated": f"{len(value) - maxItems}개 항목 생략"})
            return kept
        return [_shrinkValue(item, maxItems) for item in value]
    return value
