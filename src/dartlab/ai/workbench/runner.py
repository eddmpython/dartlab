"""5 패스 공용 LLM-도구 루프 (옛 WorkbenchProvider / generate() 시스템).

provider.generate(messages, tools) -> ProviderTurn 호출 + tool_calls 실행 + tool_result 메시지 이어붙여 다음 라운드.

안전성:
- tool_result content 가 _MAX_TOOL_RESULT_CHARS 초과면 truncate.
- 누적 messages 가 _MAX_MESSAGES_CHARS 초과면 가장 오래된 tool 메시지부터 trim.
- provider.generate() RateLimitError 면 1 회 retry.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Iterator
from typing import Any

from dartlab.ai.contracts import Ref, TraceEvent
from dartlab.ai.providers import ProviderTurn, WorkbenchProvider
from dartlab.ai.providers.base import RateLimitError
from dartlab.ai.toolAdmission import executeAllowedTool
from dartlab.ai.tools.formatting import EXTERNAL_END, EXTERNAL_START, wrapExternalInResult
from dartlab.ai.tools.registry import _SPECS as TOOL_SPECS
from dartlab.ai.tools.registry import executeTool

from .state import WorkbenchState

_MAX_TOOL_RESULT_CHARS = int(os.environ.get("DARTLAB_TOOL_RESULT_MAX_CHARS", "8000"))
_MAX_MESSAGES_CHARS = int(os.environ.get("DARTLAB_MESSAGES_MAX_CHARS", "120000"))
_RATE_LIMIT_RETRY_DELAY_SEC = float(os.environ.get("DARTLAB_RATE_LIMIT_RETRY_SEC", "2"))


def _boundedToolContent(content: str) -> str:
    """도구 결과를 상한 안에 두고 외부 본문 marker 쌍은 절단 뒤에도 닫는다."""

    if len(content) <= _MAX_TOOL_RESULT_CHARS:
        return content
    suffix = f"\n...(truncated, full {len(content)} chars)"
    if EXTERNAL_START not in content:
        return content[: max(0, _MAX_TOOL_RESULT_CHARS - len(suffix))] + suffix

    prefix = f"{EXTERNAL_START}\n"
    closing = f"\n{EXTERNAL_END}{suffix}"
    body_budget = max(0, _MAX_TOOL_RESULT_CHARS - len(prefix) - len(closing))
    preview = content.replace(EXTERNAL_START, "").replace(EXTERNAL_END, "")[:body_budget]
    return prefix + preview + closing


def runLLMPass(
    state: WorkbenchState,
    provider: WorkbenchProvider,
    *,
    passName: str,
    systemPrompt: str,
    userContext: str,
    allowedTools: list[str],
    maxRounds: int = 6,
    role: str | None = None,
) -> Iterator[TraceEvent]:
    """5 패스 공용 모델-도구 루프.

    role 인자: 사용자 profile 의 role binding 으로 모델 라우팅. 미지정 시 호출자 provider 그대로.
    AI_ROLES = ("analysis", "summary", "coding", "ui_control"). 일반적으로:
    - BRIEF/CRITIQUE/COMPOSE → role="analysis" (deep tier)
    - 비싼 모델 비용 절감 시 BRIEF 만 role="summary" 등 fine-tune 가능
    """
    state.currentPass = passName
    yield TraceEvent(kind="pass_enter", data={"pass": passName})

    if role:
        provider = _resolveProviderForRole(provider, role)

    tool_specs_objs = [TOOL_SPECS[name] for name in allowedTools if name in TOOL_SPECS]
    allowed_tool_names = frozenset(spec.name for spec in tool_specs_objs)
    tools_payload = [_toolToOpenAIFormat(spec) for spec in tool_specs_objs]
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": systemPrompt},
        {"role": "user", "content": userContext},
    ]

    rounds_used = 0
    for round_idx in range(maxRounds):
        rounds_used = round_idx + 1
        _trimMessagesIfNeeded(messages)
        try:
            turn = _generateWithRetry(provider, messages, tools_payload)
        except RateLimitError as exc:
            # rate limit 1회 retry 도 실패 — state.failure 에 명시 + 답변 합성을 loop 가 처리
            state.failure = "rate_limit"
            yield TraceEvent(
                kind="llm_error",
                data={"pass": passName, "round": round_idx, "error": str(exc), "type": "RateLimitError"},
            )
            break
        except Exception as exc:  # noqa: BLE001
            yield TraceEvent(
                kind="llm_error",
                data={"pass": passName, "round": round_idx, "error": str(exc), "type": type(exc).__name__},
            )
            break

        if turn.content:
            yield TraceEvent(
                kind="llm_text",
                data={"pass": passName, "round": round_idx, "text": turn.content},
            )

        for call in turn.toolCalls:
            yield TraceEvent(
                kind="llm_tool_use",
                data={
                    "pass": passName,
                    "round": round_idx,
                    "id": call.id,
                    "name": call.name,
                    "input": call.args,
                },
            )

        # assistant 메시지 추가 (tool_calls 포함)
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": turn.content or ""}
        if turn.toolCalls:
            assistant_msg["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.name, "arguments": json.dumps(c.args, ensure_ascii=False)},
                }
                for c in turn.toolCalls
            ]
        messages.append(assistant_msg)

        if not turn.toolCalls:
            yield TraceEvent(kind="llm_stop", data={"pass": passName, "round": round_idx, "reason": "no_tool_calls"})
            break

        for call in turn.toolCalls:
            tool_start = time.monotonic()
            result = executeAllowedTool(
                executeTool,
                call.name,
                call.args or {},
                allowed_tool_names,
            )
            tool_duration_ms = int((time.monotonic() - tool_start) * 1000)

            state.toolCalls.append(
                {
                    "pass": passName,
                    "tool": call.name,
                    "args": call.args,
                    "ok": result.get("ok"),
                    "durationMs": tool_duration_ms,
                }
            )
            for ref_dict in result.get("refs") or []:
                state.refs.append(_refFromDict(ref_dict))

            yield TraceEvent(
                kind="tool_result",
                data={
                    "pass": passName,
                    "tool": call.name,
                    "ok": result.get("ok"),
                    "summary": result.get("summary"),
                    "refs": [r.get("id") for r in result.get("refs") or []],
                    "error": result.get("error"),
                },
            )
            # 외부 본문 (sourceType=external) 인 ref 의 payload·data 텍스트 필드를
            # [EXTERNAL CONTENT START/END] 마커로 감싼다.
            # 상세: runtime.workbenchEvidenceFlow "외부 본문 처리".
            wrapped = wrapExternalInResult(result)
            content = json.dumps(wrapped, ensure_ascii=False, default=str)
            content = _boundedToolContent(content)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": content,
                }
            )

    yield TraceEvent(kind="pass_exit", data={"pass": passName, "rounds": rounds_used})


def _generateWithRetry(
    provider: WorkbenchProvider, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
) -> ProviderTurn:
    """provider.generate() — RateLimitError 1 회 retry."""
    try:
        return provider.generate(messages, tools)
    except RateLimitError:
        time.sleep(_RATE_LIMIT_RETRY_DELAY_SEC)
        return provider.generate(messages, tools)


def _resolveProviderForRole(currentProvider: WorkbenchProvider, role: str) -> WorkbenchProvider:
    """role 별 별도 모델 binding 으로 provider 재해상.

    Profile 에 role 이 등록되어 있고 모델이 다르면 새 provider 를 생성.
    동일하거나 미등록이면 currentProvider 를 그대로 반환 (롤백 안전).
    """
    try:
        from dartlab.ai.providers import createProvider, getConfig

        current_provider_id = (getattr(currentProvider.config, "provider", None) or "").lower()
        current_model = getattr(currentProvider.config, "model", None)
        new_config = getConfig(role=role, provider=current_provider_id)
        if (new_config.provider or "").lower() == current_provider_id and (new_config.model or "") == (
            current_model or ""
        ):
            return currentProvider
        return createProvider(new_config)
    except Exception:  # noqa: BLE001
        return currentProvider


def _trimMessagesIfNeeded(messages: list[dict[str, Any]]) -> None:
    """누적 messages 가 한도를 넘으면 가장 오래된 tool 메시지부터 trim.

    system / user (첫 두 개) 와 마지막 assistant 는 보존. 그 사이 tool 메시지를 우선 제거.
    """
    total = sum(len(str(m.get("content") or "")) for m in messages)
    if total <= _MAX_MESSAGES_CHARS:
        return
    # 보존 인덱스: 0 (system), 1 (user), 마지막 메시지
    if len(messages) <= 3:
        return
    keep_head = 2
    keep_tail = 1
    middle = messages[keep_head : len(messages) - keep_tail]
    # tool 메시지 우선 제거
    middle_filtered = [m for m in middle if m.get("role") != "tool"]
    new_total = sum(
        len(str(m.get("content") or "")) for m in messages[:keep_head] + middle_filtered + messages[-keep_tail:]
    )
    if new_total <= _MAX_MESSAGES_CHARS:
        messages[keep_head : len(messages) - keep_tail] = middle_filtered
        return
    # tool 제거로도 부족하면 가장 오래된 assistant 부터 truncate
    while middle_filtered and new_total > _MAX_MESSAGES_CHARS:
        middle_filtered.pop(0)
        new_total = sum(
            len(str(m.get("content") or "")) for m in messages[:keep_head] + middle_filtered + messages[-keep_tail:]
        )
    messages[keep_head : len(messages) - keep_tail] = middle_filtered


def _toolToOpenAIFormat(spec: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.inputSchema,
        },
    }


def _refFromDict(d: dict[str, Any]) -> Ref:
    return Ref(
        id=str(d.get("id", "")),
        kind=str(d.get("kind", "")),
        title=str(d.get("title", "")),
        source=str(d.get("source", "")),
        payload=d.get("payload") or {},
    )


def buildContextSummary(state: WorkbenchState) -> str:
    """WorkbenchState → LLM 입력용 멀티라인 컨텍스트 문자열 (질문/skill/refs/recipe)."""
    parts: list[str] = [f"질문: {state.question}"]
    if state.selectedSkillRefs:
        parts.append("선택된 skill: " + ", ".join(r.id for r in state.selectedSkillRefs))
    if state.apiRefs:
        parts.append("후보 API: " + ", ".join(r.id for r in state.apiRefs[:8]))
    if state.requiredEvidence:
        parts.append("requiredEvidence: " + ", ".join(state.requiredEvidence))
    recipe_lines = _formatRecipeSteps(state.selectedSkillRefs)
    if recipe_lines:
        parts.append("선택 recipe 의 단계 (순차 실행):\n" + recipe_lines)
    if state.refs:
        parts.append(f"누적 ref: {len(state.refs)}개")
        by_kind: dict[str, list[Ref]] = {}
        for ref in state.refs:
            by_kind.setdefault(ref.kind, []).append(ref)

        for kind, summarizer, max_count in (
            ("valueRef", _summarizeValueRef, 20),
            ("tableRef", _summarizeTableRef, 5),
            ("dateRef", _summarizeDateRef, 5),
            ("executionRef", _summarizeExecutionRef, 3),
            ("datasetRef", _summarizeDatasetRef, 5),
        ):
            refs_of_kind = by_kind.get(kind)
            if not refs_of_kind:
                continue
            recent = refs_of_kind[-max_count:]
            parts.append(f"## {kind} ({len(refs_of_kind)}개, 최근 {len(recent)}개 노출)")
            parts.extend(f"- {summarizer(r)}" for r in recent)

        handled = {"valueRef", "tableRef", "dateRef", "executionRef", "datasetRef"}
        other_kinds = sorted(set(by_kind) - handled)
        for kind in other_kinds:
            refs_of_kind = by_kind[kind]
            sample = [f"{kind}:{r.id}"[:60] for r in refs_of_kind[-10:]]
            parts.append(f"기타 {kind} ({len(refs_of_kind)}개): " + ", ".join(sample))
    if state.critiques:
        parts.append("CRITIQUE 이슈: " + "; ".join(c.get("text", "") for c in state.critiques[:5]))
    return "\n".join(parts)


def _truncate(text: str, limit: int) -> str:
    text = str(text)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _withRefSuffix(prefix: str, ref: Ref, totalCap: int) -> str:
    """ref id 는 절대 자르지 않고 prefix 만 cap 안에 맞춘다."""
    suffix = f" <{ref.kind}:{ref.id}>"
    max_prefix = max(20, totalCap - len(suffix))
    return _truncate(prefix, max_prefix) + suffix


def _summarizeValueRef(ref: Ref) -> str:
    payload = ref.payload if isinstance(ref.payload, dict) else {}
    item = payload.get("item") or payload.get("key") or ""
    formatted = payload.get("formatted")
    value = payload.get("value")
    period = payload.get("period") or ""
    unit = payload.get("unit") or ""
    value_str = str(formatted) if formatted else (str(value) if value is not None else "?")
    pieces = [str(item) or ref.id, "=", value_str]
    if unit:
        pieces.append(f"({unit})")
    if period:
        pieces.append(f"@{period}")
    prefix = " ".join(p for p in pieces if p)
    return _withRefSuffix(prefix, ref, 100)


def _summarizeTableRef(ref: Ref) -> str:
    payload = ref.payload if isinstance(ref.payload, dict) else {}
    parts: list[str] = []
    label = payload.get("label") or payload.get("statement") or payload.get("axis") or ""
    if label:
        parts.append(str(label))
    period = payload.get("latestPeriod") or payload.get("period")
    if period:
        parts.append(f"@{period}")
    rows = payload.get("rows")
    rowCount = payload.get("rowCount")
    if rowCount is None and isinstance(rows, list):
        rowCount = len(rows)
    if rowCount is not None:
        parts.append(f"rows={rowCount}")
    columns = payload.get("columns")
    if isinstance(columns, list) and columns:
        sample_cols = ", ".join(str(c) for c in columns[:3])
        parts.append(f"cols=[{sample_cols}]")
    base = _withRefSuffix(" ".join(parts), ref, 120)
    # COMPOSE 단계 등에서 LLM 이 행 데이터 인용 가능하도록 처음 N 행 짧게 노출.
    # 보수적: 처음 5 행, 각 행 160 chars cap, 총 1.5KB 이하.
    if isinstance(rows, list) and rows:
        try:
            import json as _json

            sample_rows = rows[:5]
            row_lines = []
            total = 0
            for row in sample_rows:
                if isinstance(row, dict):
                    line = _truncate(_json.dumps(row, ensure_ascii=False, default=str), 160)
                else:
                    line = _truncate(str(row), 160)
                if total + len(line) > 1500:
                    break
                row_lines.append(line)
                total += len(line)
            if row_lines:
                more = f" (+{len(rows) - len(row_lines)} more)" if len(rows) > len(row_lines) else ""
                base += " | rows: " + " ; ".join(row_lines) + more
        except Exception:  # noqa: BLE001 - context 직렬화 실패는 무시
            pass
    return base


def _summarizeDateRef(ref: Ref) -> str:
    payload = ref.payload if isinstance(ref.payload, dict) else {}
    period = payload.get("period") or payload.get("value") or ""
    return _withRefSuffix(str(period), ref, 80)


def _summarizeExecutionRef(ref: Ref) -> str:
    payload = ref.payload if isinstance(ref.payload, dict) else {}
    duration_ms = payload.get("durationMs")
    preview = payload.get("preview") or payload.get("stdout") or payload.get("result") or ""
    snippet = _truncate(str(preview).replace("\n", " "), 180)
    head = f"[{duration_ms}ms]" if duration_ms is not None else ""
    prefix = f"{head} {snippet}".strip()
    return _withRefSuffix(prefix, ref, 250)


def _summarizeDatasetRef(ref: Ref) -> str:
    payload = ref.payload if isinstance(ref.payload, dict) else {}
    target = payload.get("target") or ref.title or ""
    source = payload.get("source") or ""
    rowCount = payload.get("rowCount")
    latest = payload.get("latest")
    parts = [str(target)]
    if source:
        parts.append(f"src={source}")
    if rowCount is not None:
        parts.append(f"rows={rowCount}")
    if latest:
        parts.append(f"latest={latest}")
    return _withRefSuffix(" ".join(parts), ref, 140)


def _formatRecipeSteps(refs: list[Ref]) -> str:
    """selectedSkillRefs 중 recipe ref 의 step list 직렬화.

    형식: "1. {skillId} — {note}\\n2. ...". step 당 60 char truncate, max 8 step.
    """
    for ref in refs:
        payload = ref.payload if isinstance(ref.payload, dict) else {}
        if payload.get("kind") != "recipe" and not payload.get("recipeSteps"):
            continue
        steps = payload.get("recipeSteps") or []
        if not steps:
            from dartlab.skills.registry import _stepsFromRecipeBody

            steps = _stepsFromRecipeBody(str(payload.get("body") or ""))
        if not steps:
            steps = [{"skillId": sid, "note": ""} for sid in payload.get("linkedSkills") or []]
        if not steps:
            continue
        lines: list[str] = []
        for index, step in enumerate(steps[:8], start=1):
            skill_id = str(step.get("skillId") or "")
            note = str(step.get("note") or "")
            entry = f"{index}. {skill_id}"
            if note:
                entry += f" — {note[:60]}"
            lines.append(entry)
        return "\n".join(lines)
    return ""
