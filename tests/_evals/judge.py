"""dartlab 에이전트 출력 6 신호 채점기 — Track 3.

본 SSOT — [tests/POLICY.md](../POLICY.md) §5 Track 3 + [README.md](README.md).

룰 기반 4 신호 (factual_correctness · evidence_citation · tool_use_appropriate ·
format_compliance) 는 외부 호출 없이 무료 채점. 나머지 2 신호 (reasoning_depth ·
no_hallucination) 는 외부 모델 judge — `judgeWithModel()` 옵션, 비용 발생.

룰 기반은 CI Fast 에서 mock 에이전트 출력으로 회귀 가드. 외부 모델 judge 는
운영자 트리거 + nightly 한정.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class EvalCase:
    """eval_set.jsonl 한 줄 = 한 case."""

    id: str
    question: str
    expected_signals: dict[str, Any]
    tags: list[str] = field(default_factory=list)
    baseline_score: float = 0.0


@dataclass
class AgentRun:
    """에이전트 1 회 실행 결과 — runner.runAgent 또는 mock 가 채움."""

    case_id: str
    output_text: str
    tool_calls: list[str] = field(default_factory=list)
    refs: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalScore:
    """한 신호 채점 결과 — 0.0 ~ 1.0."""

    name: str
    score: float
    detail: str = ""


@dataclass
class JudgeResult:
    """case 1 종 6 신호 채점 결과."""

    case_id: str
    signals: list[SignalScore]

    @property
    def aggregate(self) -> float:
        """단순 평균 (보고용 — fail gate 는 개별 신호 임계 사용)."""
        if not self.signals:
            return 0.0
        return sum(s.score for s in self.signals) / len(self.signals)

    def signal(self, name: str) -> SignalScore | None:
        for s in self.signals:
            if s.name == name:
                return s
        return None


def loadEvalSet(path: str | Path) -> list[EvalCase]:
    """eval_set.jsonl 로드."""
    path = Path(path)
    out: list[EvalCase] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        d = json.loads(line)
        out.append(
            EvalCase(
                id=d["id"],
                question=d["question"],
                expected_signals=d["expected_signals"],
                tags=d.get("tags", []),
                baseline_score=d.get("baseline_score", 0.0),
            )
        )
    return out


def scoreFactualCorrectness(case: EvalCase, run: AgentRun) -> SignalScore:
    """기대 키워드가 output 에 등장하는 비율."""
    expected = case.expected_signals.get("factual_correctness") or []
    if not expected:
        return SignalScore("factual_correctness", 1.0, "no expected keywords")
    text = run.output_text
    hits = sum(1 for kw in expected if kw in text)
    score = hits / len(expected)
    return SignalScore("factual_correctness", score, f"{hits}/{len(expected)} hits")


def scoreEvidenceCitation(case: EvalCase, run: AgentRun) -> SignalScore:
    """실제로 반환된 근거 ID가 답변에 인용됐는지 확인한다."""
    required = case.expected_signals.get("evidence_citation", False)
    if not required:
        return SignalScore("evidence_citation", 1.0, "not required")
    cited = [ref for ref in run.refs if re.search(re.escape(ref) + r"(?![\w:])", run.output_text)]
    if cited:
        return SignalScore("evidence_citation", 1.0, f"{len(cited)} returned refs cited")
    return SignalScore("evidence_citation", 0.0, "no returned ref cited")


def scoreToolUseAppropriate(case: EvalCase, run: AgentRun) -> SignalScore:
    """기대 도구가 tool_calls 에 포함됐는지."""
    expected = case.expected_signals.get("tool_use_appropriate") or []
    if not expected:
        # 기대 도구 없음 = 도구 호출도 없어야 함 (예: untrusted 본문)
        if run.tool_calls:
            return SignalScore("tool_use_appropriate", 0.5, f"unexpected tools: {run.tool_calls}")
        return SignalScore("tool_use_appropriate", 1.0, "no tool expected, none called")
    hits = sum(1 for t in expected if any(t.lower() in c.lower() for c in run.tool_calls))
    score = hits / len(expected)
    return SignalScore("tool_use_appropriate", score, f"{hits}/{len(expected)} expected tools called")


def scoreFormatCompliance(case: EvalCase, run: AgentRun) -> SignalScore:
    """기대 포맷 (markdown_with_table / markdown / any) 검증."""
    expected = case.expected_signals.get("format_compliance", "any")
    text = run.output_text
    if expected == "any":
        return SignalScore("format_compliance", 1.0, "no format requirement")
    if expected == "markdown":
        has_md = any(marker in text for marker in ("##", "**", "- ", "1.", "`"))
        return SignalScore("format_compliance", 1.0 if has_md else 0.0, f"markdown markers: {has_md}")
    if expected == "markdown_with_table":
        has_table = "|" in text and "---" in text
        return SignalScore("format_compliance", 1.0 if has_table else 0.0, f"markdown table: {has_table}")
    if expected == "json":
        try:
            json.loads(text)
            return SignalScore("format_compliance", 1.0, "valid json")
        except json.JSONDecodeError:
            return SignalScore("format_compliance", 0.0, "not valid json")
    return SignalScore("format_compliance", 0.5, f"unknown format spec: {expected}")


def scoreNoHallucination(case: EvalCase, run: AgentRun) -> SignalScore:
    """금지 키워드 (forbidden_hallucinations) 가 출력에 없는지 — 룰 기반.

    외부 모델 judge 강화는 judgeWithModel() 옵션 (eval 마커, 운영자 트리거).
    """
    forbidden = case.expected_signals.get("forbidden_hallucinations") or []
    if not forbidden:
        return SignalScore("no_hallucination", 1.0, "no forbidden list")
    hits = [kw for kw in forbidden if kw in run.output_text]
    if hits:
        return SignalScore("no_hallucination", 0.0, f"hallucinated keywords: {hits}")
    return SignalScore("no_hallucination", 1.0, "no forbidden keywords")


def scoreReasoningDepth(case: EvalCase, run: AgentRun) -> SignalScore:
    """추론 깊이 — 룰 기반 근사 (인과 markers 카운트).

    외부 모델 judge 강화는 judgeWithModel() 옵션.
    """
    min_depth = case.expected_signals.get("min_reasoning_depth", 1)
    text = run.output_text
    causal_markers = ["때문에", "왜냐하면", "따라서", "그러므로", "에 의해", "결과적으로", "→"]
    count = sum(text.count(m) for m in causal_markers)
    if count >= min_depth:
        return SignalScore("reasoning_depth", 1.0, f"causal markers: {count} >= {min_depth}")
    if min_depth == 0:
        return SignalScore("reasoning_depth", 1.0, "no min depth required")
    return SignalScore("reasoning_depth", count / max(min_depth, 1), f"causal markers: {count} < {min_depth}")


_RULE_SIGNALS = (
    scoreFactualCorrectness,
    scoreEvidenceCitation,
    scoreToolUseAppropriate,
    scoreFormatCompliance,
    scoreNoHallucination,
    scoreReasoningDepth,
)


def judgeRule(case: EvalCase, run: AgentRun) -> JudgeResult:
    """6 신호 룰 기반 채점 — 외부 호출 0, CI Fast 안전.

    Args:
        case: eval_set.jsonl 한 줄.
        run: 에이전트 실행 결과 (mock 또는 실 호출).
    Returns:
        JudgeResult — 6 SignalScore.
    """
    signals = [fn(case, run) for fn in _RULE_SIGNALS]
    return JudgeResult(case_id=case.id, signals=signals)


def judgeWithModel(case: EvalCase, run: AgentRun, *, model_provider: str = "anthropic") -> JudgeResult:
    """외부 모델 judge 로 reasoning_depth · no_hallucination 강화 — 운영자 트리거.

    환경변수 (OPENAI_API_KEY / ANTHROPIC_API_KEY) 필요. 비용 발생.
    DARTLAB_EVAL_LIVE != "1" 면 룰 기반으로 fallback.
    """
    import os

    if os.environ.get("DARTLAB_EVAL_LIVE") != "1":
        # live 모드 아니면 룰 기반 그대로
        return judgeRule(case, run)

    # 외부 모델 호출 placeholder — 실제 구현은 dartlab.ai.providers 재사용.
    # 본 PR 에는 인프라만, 실 호출은 별도 트리거.
    raise NotImplementedError(
        "judgeWithModel 의 외부 모델 호출은 본 PR 범위 밖. Phase 3 트리거 시 dartlab.ai.providers 재사용해 구현."
    )
