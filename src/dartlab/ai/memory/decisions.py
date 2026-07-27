"""세션 간 recall / remember.

저장: ~/.dartlab/ai_memory/decisions.jsonl (append-only) — 또는 환경변수
DARTLAB_DECISIONS_PATH 로 redirect (테스트/외부 도구).
검색: 단순 BM25-like — 질문 토큰 매칭 빈도 + target/skill/metric 가중. 임베딩은 P5.1.

API:
- DecisionMemo(question, answer, refs) — 외부 입력 형식 (dataclass 또는 단순 텍스트).
- remember(memo_or_text, *, tags, refs) — DecisionMemo 또는 string 둘 다 받음.
- recall(query, *, k) → list[DecisionMemo] (dict-like access 호환).
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dartlab.core.market import KR_STOCK_CODE_TEXT_RE

_DECISIONS_PATH = Path.home() / ".dartlab" / "ai_memory" / "decisions.jsonl"
_TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9_]+")


@dataclass
class DecisionMemo:
    """외부 API 형식 — question/answer/refs 분리.

    옛 호출자가 row.get('text', '') 등 dict-like 접근하던 호환을 위해 .get() / .__getitem__
    도 동시 지원. 필드 외 키 (text, tags, ts) 는 derived property 또는 자료에 저장된 값에서 노출.
    """

    question: str
    answer: str = ""
    refs: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    ts: str = ""

    @property
    def text(self) -> str:
        """옛 'text' 필드 호환 — question + answer 결합 또는 question 만."""
        if self.answer:
            return f"Q: {self.question}\nA: {self.answer}"
        return self.question

    def get(self, key: str, default: Any = None) -> Any:
        """dict-like 접근 — DecisionMemo 필드 또는 'text' 합성 키."""
        if key == "text":
            return self.text or default
        return getattr(self, key, default)

    def __getitem__(self, key: str) -> Any:
        if key == "text":
            return self.text
        return getattr(self, key)


@dataclass
class _StoredDecision:
    """내부 저장 형식 — JSONL 한 줄."""

    text: str
    tags: list[str] = field(default_factory=list)
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    question: str = ""
    answer: str = ""
    refs: list[str] = field(default_factory=list)


def _resolveDecisionsPath() -> Path:
    """env var 가 있으면 우선 — 테스트/외부 도구 redirect."""
    env_path = os.environ.get("DARTLAB_DECISIONS_PATH")
    if env_path:
        return Path(env_path)
    return _DECISIONS_PATH


def _ensureDir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def remember(
    memoOrText: DecisionMemo | str,
    *,
    tags: list[str] | None = None,
    refs: list[str] | None = None,
) -> None:
    """DecisionMemo 또는 string 받음 (overload)."""
    if isinstance(memoOrText, DecisionMemo):
        memo = memoOrText
        question = memo.question
        answer = memo.answer
        memo_refs = list(memo.refs) + list(refs or [])
        memo_tags = list(memo.tags) + list(tags or [])
        text = memo.text
    else:
        text = str(memoOrText or "").strip()
        if not text:
            return
        question = text
        answer = ""
        memo_refs = list(refs or [])
        memo_tags = list(tags or [])

    if not (question or "").strip():
        return

    path = _resolveDecisionsPath()
    _ensureDir(path)
    row = _StoredDecision(
        text=text or question,
        tags=memo_tags,
        question=question,
        answer=answer,
        refs=memo_refs,
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")


def _tokenize(text: str) -> set[str]:
    return {tok.lower() for tok in _TOKEN_RE.findall(text or "")}


# KRX 단축코드 정본 패턴 (영숫자 코드 0008Z0 포함, 기간 "2026Q1" 오탐 배제).
_STOCK_CODE_RE = KR_STOCK_CODE_TEXT_RE
_RECIPE_TAG_PREFIXES = ("skill:recipes.", "skill:engines.recipe.")
_TARGET_TAG_PREFIX = "target:"
_METRIC_TAG_PREFIX = "metric:"


def _scoreRecall(row: dict, qTokens: set[str], qMeta: dict) -> float:
    """recall 점수 — 토큰 overlap + target/skill category/metric 가중.

    가중치:
    - target:{stockCode} 일치: +0.3
    - skill:recipes.* 태그: +0.2 (recipe 우선 회상)
      기존 memory 호환을 위해 skill:engines.recipe.* 도 동일 처리.
    - metric:{name} 이 query 토큰에 포함: +0.2 (특정 지표 회상)
    """
    text_for_scoring = row.get("text") or row.get("question") or ""
    d_tokens = _tokenize(text_for_scoring)
    if not d_tokens:
        return 0.0
    overlap = len(qTokens & d_tokens)
    base = overlap / (len(qTokens) + 1) if overlap else 0.0
    if base == 0.0:
        return 0.0

    bonus = 0.0
    tags = row.get("tags") or []
    if isinstance(tags, list):
        target_codes = qMeta.get("targets") or set()
        for tag in tags:
            tag_str = str(tag)
            if tag_str.startswith(_TARGET_TAG_PREFIX):
                code = tag_str[len(_TARGET_TAG_PREFIX) :]
                if code in target_codes:
                    bonus += 0.3
                    break
        if any(str(t).startswith(_RECIPE_TAG_PREFIXES) for t in tags):
            bonus += 0.2
        for tag in tags:
            tag_str = str(tag)
            if tag_str.startswith(_METRIC_TAG_PREFIX):
                metric = tag_str[len(_METRIC_TAG_PREFIX) :].lower()
                if metric and any(metric in tok for tok in qTokens):
                    bonus += 0.2
                    break
    return base + bonus


def _extractQueryMeta(query: str) -> dict:
    return {
        "targets": set(_STOCK_CODE_RE.findall(query or "")),
    }


def _rowToMemo(row: dict) -> DecisionMemo:
    """저장 row → DecisionMemo. 옛 형식 (text only) 호환."""
    question = row.get("question") or ""
    answer = row.get("answer") or ""
    if not question:
        # 옛 형식 — 'text' 만 있고 question/answer 분리 안 됨
        text = row.get("text") or ""
        # "Q: ...\nA: ..." 형식이면 분해 시도
        if text.startswith("Q: ") and "\nA:" in text:
            head, _, tail = text.partition("\nA:")
            question = head[3:].strip()
            answer = tail.strip()
        else:
            question = text
    return DecisionMemo(
        question=question,
        answer=answer,
        refs=list(row.get("refs") or []),
        tags=list(row.get("tags") or []),
        ts=str(row.get("ts") or ""),
    )


def recall(query: str, *, k: int = 5) -> list[DecisionMemo]:
    """query 토큰 매칭 점수로 DecisionMemo 상위 k 개 회상 (JSONL 스캔)."""
    path = _resolveDecisionsPath()
    if not path.exists() or not query:
        return []
    qTokens = _tokenize(query)
    qMeta = _extractQueryMeta(query)
    scored: list[tuple[float, dict]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            score = _scoreRecall(row, qTokens, qMeta)
            if score > 0.0:
                scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [_rowToMemo(row) for _, row in scored[: max(1, int(k or 5))]]


def setDecisionsPathForTesting(path: Path) -> None:
    """레거시 호환 — env var 권장."""
    global _DECISIONS_PATH
    _DECISIONS_PATH = path


__all__ = [
    "DecisionMemo",
    "recall",
    "remember",
    "setDecisionsPathForTesting",
]
