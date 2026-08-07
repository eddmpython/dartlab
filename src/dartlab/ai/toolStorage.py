"""큰 도구 결과 디스크 persist + preview inject — chat-native loop 의 컨텍스트 압박 방지.

큰 결과 (Polars 10k row, RunPython stdout 등) 를 LLM 메시지에 통째로 넣으면 나머지 추론 공간이
잠식돼 답 품질이 저하된다. 임계 초과 결과는 디스크 저장 + *preview + 파일 경로* 만 LLM 에 inject —
Read 도구로 전체를 다시 읽을 수 있다.

회귀 가드: graph 노드 추가 아님. agent.py 본체에 합치지 않고 단일 책임 모듈로 분리
(memory/engineering.md 7절 패턴 5 — workbench 본체화 금지 정신과 정합).
"""

from __future__ import annotations

import re
from pathlib import Path

MAX_TOOL_RESULT_CHARS: int = 50_000
PREVIEW_CHARS: int = 2_000

_DEFAULT_RESULTS_ROOT = Path.home() / ".dartlab" / "tool-results"
_SAFE_ID_RE = re.compile(r"[^a-zA-Z0-9_-]+")


def _resolveResultsRoot() -> Path:
    """저장 디렉토리. 테스트는 monkeypatch 로 _DEFAULT_RESULTS_ROOT 교체."""
    _DEFAULT_RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    return _DEFAULT_RESULTS_ROOT


def exceedsSizeCap(content: str) -> bool:
    """결과 길이 > MAX_TOOL_RESULT_CHARS 이면 True."""
    return len(content) > MAX_TOOL_RESULT_CHARS


def persistLargeResult(toolName: str, toolCallId: str, content: str) -> tuple[str, str]:
    """결과를 디스크에 저장하고 (preview, filePath) 반환.

    파일은 ~/.dartlab/tool-results/<safe_id>.txt. 디렉토리는 자동 생성.
    safe_id 는 toolCallId 우선, 없으면 toolName, 둘 다 없으면 "result".
    """
    root = _resolveResultsRoot()
    raw = str(toolCallId or toolName or "result")
    safe_id = _SAFE_ID_RE.sub("_", raw) or "result"
    target = root / f"{safe_id}.txt"
    target.write_text(content, encoding="utf-8")
    preview = content[:PREVIEW_CHARS]
    return preview, str(target)


def buildPersistedContent(filePath: str, preview: str, sizeBytes: int) -> str:
    """LLM 에 inject 할 대체 content. Read 도구 안내 포함."""
    size_kb = max(1, round(sizeBytes / 1024))
    return (
        f"[Result persisted to {filePath} ({size_kb} KB)]\n\n"
        f"Preview (first {PREVIEW_CHARS} chars):\n{preview}\n\n"
        f"Use the Read tool to access the full result if needed."
    )


__all__ = [
    "MAX_TOOL_RESULT_CHARS",
    "PREVIEW_CHARS",
    "exceedsSizeCap",
    "persistLargeResult",
    "buildPersistedContent",
]
