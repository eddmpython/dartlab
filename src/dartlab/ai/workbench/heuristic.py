"""휴리스틱 흐름 — provider 가 LLM 이 아닐 때 5 패스 노드명을 발행하며 답을 합성.

BRIEF (profile + ReadSkill + ReadCapability + planEvidence) → WORK (EngineCall 루프)
→ COMPOSE (휴리스틱 답안) → GATE (verifyAnswer programmatic) → HARVEST (no-op).

본 모듈은 외부 LLM 의존 없음. targets / intent 의 정적 함수 + workbench tools 만 사용.
engineCall / verifyAnswer 는 registry 등록되어 있지 않고 직접 import — 휴리스틱 path 의
plan 실행 + GATE 검증은 LLM 도구 노출과 무관한 내부 helper 다.

PR-W2 결정 (2026-05-28) — PR-W2-B 유지 + 명문화
-----------------------------------------------
마스터 플랜 cryptic-discovering-kettle.md PR-W2 결정 박힘. *결정 근거는 운영
빈도가 아니라 의존성 분석*. 본 모듈은 ``kernel.ask()`` 의 LLM-less 결정론 path —
``tests/ai/test_ai_research_graph.py:118`` 등 다수 테스트가 본 모듈을 monkeypatch
하여 streaming 결과 검증. 삭제 시 test 인프라 회귀 폭 ≥ 5 파일.

위치: LLM provider 미구성 환경 (테스트 fixture / dartlab stub provider) 에서
``WorkbenchLoop.stream()`` 의 ``streamHeuristic`` 진입점. production 에서는 LLM
provider 항상 활성 → 본 path 활성 빈도 ≈ 0%. 그러나 *결정론 시뮬* 가치 = 테스트
인프라 강행.

회귀 가드: ``feedback_no_graph_regression.md`` — 본체는 ``ai/agent.py`` (chat-native
+ 자율 tool calling). 본 모듈은 *option sub-agent only*. BRIEF/WORK/CRITIQUE 노드
강제는 본 모듈 안 휴리스틱 실험 path 한정 — agent.py 본체로 절대 이식 금지.

측정 (PR-W1 digest):
- ``tests/audit/workbenchUsageDigest.py`` (commit d89a26681) — production trace 1+
  일 누적 후 streamHeuristic 진입 빈도 출력. ≥ 1% 면 본 docstring 의 production
  빈도 라인 갱신 (예: "production 활성 빈도 X.YY% (집계일 YYYY-MM-DD)"). < 1% 면
  *그래도 본 모듈 유지* — 본 결정의 근거는 production 빈도가 아니라 test 인프라
  의존성이라 빈도 표시 라인만 갱신.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any

from dartlab.ai.contracts import Ref, TraceEvent
from dartlab.ai.tools.engineCall import engineCall
from dartlab.ai.tools.readCapability import readCapability
from dartlab.ai.tools.readSkill import readSkill
from dartlab.ai.tools.types import ToolResult
from dartlab.ai.tools.verifyAnswer import verifyAnswer

from .harvest import _wireMemory
from .state import WorkbenchState
from .targets import (
    _buildQuestionProfile,
    _candidateApiRefs,
    _injectStepDependency,
    _planEvidence,
    _requiredEvidence,
    _requiresExecution,
    _skillId,
    _skillRequiresTarget,
)


def streamHeuristic(question: str, *, graphNodes: tuple[str, ...], **kwargs: Any) -> Iterator[TraceEvent]:
    """휴리스틱 path — 5 패스 노드명을 발행하며 답을 합성한다.

    graphNodes 는 loop.GRAPH_NODES — circular import 회피용 인자 주입.
    """
    state = WorkbenchState(
        question=str(question or "").strip(),
        threadId=str(kwargs.get("threadId") or ""),
    )
    activity_count = 0

    # ── BRIEF ──
    yield _node("brief", "질문 profile + skill/capability 후보를 만듭니다.", state)
    activity_count += 1
    state.profile = _buildQuestionProfile(state.question, stockCode=kwargs.get("stockCode"))
    state.intent = str(state.profile.get("taskType") or "research")

    yield _toolStart(state, "ReadSkill", {"query": state.question, "limit": 8})
    skill_result = readSkill(state.question, limit=8, includeBody=True)
    state.selectedSkillRefs = skill_result.refs
    state.refs.extend(skill_result.refs)
    state.toolCalls.append({"pass": "brief", "tool": "ReadSkill", "ok": skill_result.ok})
    yield _toolResult(state, "ReadSkill", skill_result)
    yield TraceEvent("reference", {"refs": [ref.toDict() for ref in skill_result.refs], "query": state.question})

    yield _toolStart(state, "ReadCapability", {"query": state.question, "limit": 10})
    spec_result = readCapability(state.question, limit=10)
    state.apiRefs = spec_result.refs
    state.refs.extend(spec_result.refs)
    state.toolCalls.append({"pass": "brief", "tool": "ReadCapability", "ok": spec_result.ok})
    yield _toolResult(state, "ReadCapability", spec_result)

    # selectedSkillRefs 의 requiredEvidence 통합 → state.requiredEvidence
    for ref in state.selectedSkillRefs:
        payload = ref.payload if isinstance(ref.payload, dict) else {}
        for ev in payload.get("requiredEvidence") or []:
            if ev not in state.requiredEvidence:
                state.requiredEvidence.append(str(ev))

    state.plan = _planEvidence(state)
    yield TraceEvent(
        "plan",
        {
            "profile": state.profile,
            "nodes": list(graphNodes),
            "selectedSkillIds": [_skillId(ref) for ref in state.selectedSkillRefs],
            "candidateApiRefs": _candidateApiRefs(state),
            "requiredEvidence": state.requiredEvidence or _requiredEvidence(state),
        },
    )

    # ── WORK ──
    yield _node("work", "EngineCall 실행 루프.", state)
    activity_count += 1
    results: list[dict[str, Any]] = []
    for index, plan in enumerate(state.plan, start=1):
        plan = _injectStepDependency(plan, results)
        yield _toolStart(state, plan["tool"], plan["args"])
        result = _executePlan(plan)
        state.toolCalls.append({"pass": "work", "tool": plan["tool"], "ok": result.ok, "summary": result.summary})
        state.refs.extend(result.refs)
        results.append({"plan": plan, "result": result})
        yield _toolResult(state, plan["tool"], result)
        if not result.ok:
            state.failure = result.error or "tool_failed"
            break

    if not state.plan and _skillRequiresTarget(state.selectedSkillRefs) and not state.profile.get("targets"):
        state.failure = "company_not_resolved"
    elif not state.plan and _requiresExecution(state):
        state.failure = "missing_tool_plan"

    # ── COMPOSE + GATE ──
    if state.failure is None:
        yield _node("compose", "검증된 근거로 답변을 작성합니다.", state)
        activity_count += 1
        answer = _composeAnswer(state, results)
        state.answerText = answer

        yield _node("gate", "claim ↔ ref 검증.", state)
        activity_count += 1
        verify_result = verifyAnswer(answer, state.refs)
        state.verification = verify_result.data
        state.refs.extend(verify_result.refs)
        yield TraceEvent("verify", {"refId": "verify:answer", "result": verify_result.data})
        if not verify_result.ok:
            state.failure = ",".join(verify_result.data.get("issues") or ["verification_failed"])
    else:
        answer = _failureMessage(state.failure)
        yield _node("gate", "도구 실패로 검증을 중단합니다.", state, status="failed")
        activity_count += 1
        yield TraceEvent("verify", {"refId": "verify:answer", "result": {"ok": False, "issues": [state.failure]}})

    # ── 실패 분기 ──
    if state.failure:
        state.status = "failed"
        failure_text = _failureMessage(state.failure)
        yield _node("gate", failure_text, state, status="failed")
        yield TraceEvent(
            "unable", {"reason": state.failure, "message": failure_text, "refs": [ref.id for ref in state.refs]}
        )
        yield TraceEvent("chunk", {"text": failure_text})
        yield TraceEvent(
            "done",
            {
                "refs": [ref.toDict() for ref in state.refs],
                "artifacts": [],
                "verification": {"ok": False, "issues": [state.failure], "refId": "verify:answer"},
                "responseMeta": {
                    "finalEvent": "unable",
                    "responseStatus": "failed",
                    "failureReason": state.failure,
                    "activityCount": activity_count,
                    "passes": list(graphNodes),
                },
            },
        )
        return

    # ── HARVEST (휴리스틱: LLM 발굴은 no-op, 메모리 wiring 은 실행) ──
    state.status = "done"
    state.answerText = answer
    _wireMemory(state)
    yield TraceEvent("answer", {"text": answer, "evidenceRefs": [ref.id for ref in state.refs]})
    for chunk in _chunks(answer):
        yield TraceEvent("chunk", {"text": chunk})
    yield TraceEvent(
        "done",
        {
            "refs": [ref.toDict() for ref in state.refs],
            "evidence": [ref.toDict() for ref in state.refs if ref.kind != "verifyRef"],
            "claims": list(state.claims),
            "artifacts": _harvestArtifacts(state),
            "verification": {"ok": True, "refId": "verify:answer"},
            "responseMeta": {
                "finalEvent": "answer",
                "responseStatus": "ok",
                "refCount": len(state.refs),
                "activityCount": activity_count,
                "passes": list(graphNodes),
            },
        },
    )


# ── TraceEvent 헬퍼 ──


def _node(node: str, summary: str, state: WorkbenchState, *, status: str = "running") -> TraceEvent:
    return TraceEvent(
        "graph_node", {"node": node, "summary": summary, "status": status, "state": state.public(currentNode=node)}
    )


def _toolStart(state: WorkbenchState, tool: str, args: dict[str, Any]) -> TraceEvent:
    return TraceEvent(
        "tool_start",
        {
            "id": f"{state.runId}:{len(state.toolCalls) + 1}:{tool}",
            "tool": tool,
            "input": args,
            "summary": _toolSummary(tool, args),
        },
    )


def _toolResult(state: WorkbenchState, tool: str, result: ToolResult) -> TraceEvent:
    return TraceEvent(
        "tool_result",
        {
            "id": f"{state.runId}:{len(state.toolCalls)}:{tool}",
            "tool": tool,
            "status": "done" if result.ok else "error",
            "outputSummary": result.summary,
            "evidenceRefs": [ref.id for ref in result.refs],
            "artifacts": [ref.toDict() for ref in result.refs if ref.kind == "artifactRef"],
            "error": result.error,
        },
    )


# ── 실행 / 답변 합성 ──


def _executePlan(plan: dict[str, Any]) -> ToolResult:
    # plan dict 의 tool 필드는 PascalCase 가 정본. legacy snake (engine_call) 도 호환.
    tool = plan["tool"]
    if tool in ("EngineCall", "engine_call"):
        return engineCall(plan["args"].get("plan") or plan["args"])
    if tool == "ForensicsMemo":
        return _forensicsMemo(plan["args"])
    raise ValueError(f"unsupported workbench tool: {tool}")


def _forensicsMemo(args: dict[str, Any]) -> ToolResult:
    target = str(args.get("target") or "").strip()
    if not target:
        return ToolResult(False, "종목을 먼저 특정해야 포렌식 memo를 실행할 수 있습니다.", error="company_not_resolved")
    try:
        import polars as pl

        import dartlab
        from dartlab.synth.evidenceForensics import buildEvidenceForensicsMemo
    except Exception as exc:  # noqa: BLE001
        return ToolResult(False, f"forensics helper import 실패: {type(exc).__name__}", error="import_failed")

    try:
        with _quietForensicsExecution():
            company = dartlab.Company(target)
    except Exception as exc:  # noqa: BLE001
        return ToolResult(False, f"{target} Company 객체 생성 실패: {type(exc).__name__}", error="company_failed")

    statements: dict[str, pl.DataFrame] = {}
    for topic in ("IS", "BS", "CF"):
        table = _safeShow(company, topic, pl=pl)
        if isinstance(table, pl.DataFrame) and table.height:
            statements[topic] = table

    section_texts: dict[str, str] = {}
    for topic in ("businessOverview", "riskFactors", "mdna", "notesDetail"):
        text = _safeTopicText(company, topic)
        if text:
            section_texts[topic] = text[:20000]

    events = _safeDisclosureEvents(company)
    scan_rows = _safeForensicsScanRows(dartlab)
    memo = buildEvidenceForensicsMemo(
        target=target,
        market=str(getattr(company, "market", "KR")),
        companyName=str(getattr(company, "corpName", None) or target),
        statements=statements,
        panelTextRows=section_texts,
        events=events,
        scanRows=scan_rows,
    )
    refs = _forensicsRefs(target, memo)
    return ToolResult(
        True,
        f"{memo['companyName']} L1.5 포렌식 memo 실행",
        refs=refs,
        data={"memo": memo, "markdown": _forensicsMarkdown(memo)},
    )


def _safeShow(company: Any, topic: str, *, pl: Any) -> Any:
    try:
        with _quietForensicsExecution():
            table = company.panel(topic, freq="year")
    except TypeError:
        try:
            with _quietForensicsExecution():
                table = company.panel(topic)
        except Exception:  # noqa: BLE001
            return pl.DataFrame()
    except Exception:  # noqa: BLE001
        return pl.DataFrame()
    return table if isinstance(table, pl.DataFrame) else pl.DataFrame()


def _safeTopicText(company: Any, topic: str) -> str:
    try:
        with _quietForensicsExecution():
            value = company.panel(topic)
    except Exception:  # noqa: BLE001
        return ""
    return "" if value is None else str(value)


def _safeDisclosureEvents(company: Any) -> list[dict[str, Any]]:
    try:
        with _quietForensicsExecution():
            disclosure = company.disclosure()
    except Exception:  # noqa: BLE001
        return []
    if hasattr(disclosure, "head") and hasattr(disclosure, "to_dicts"):
        try:
            with _quietForensicsExecution():
                return list(disclosure.head(20).to_dicts())
        except Exception:  # noqa: BLE001
            return []
    try:
        return [row for row in list(disclosure)[:20] if isinstance(row, dict)]
    except Exception:  # noqa: BLE001
        return []


def _safeForensicsScanRows(dartlab_module: Any) -> list[dict[str, Any]]:
    if os.environ.get("DARTLAB_FORENSICS_SCAN", "0") not in {"1", "true", "True"}:
        return []
    rows: list[dict[str, Any]] = []
    for axis in ("quality", "audit", "disclosureRisk"):
        try:
            with _quietForensicsExecution():
                frame = dartlab_module.scan(axis)
                if not hasattr(frame, "head") or not hasattr(frame, "to_dicts"):
                    continue
                axis_rows = frame.head(3).to_dicts()
        except Exception:  # noqa: BLE001
            continue
        for row in axis_rows:
            if isinstance(row, dict):
                item = dict(row)
                item["axis"] = axis
                rows.append(item)
    return rows


@contextmanager
def _quietForensicsExecution() -> Iterator[None]:
    previous_disable = logging.root.manager.disable
    logging.disable(logging.INFO)
    try:
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            yield
    finally:
        logging.disable(previous_disable)


def _forensicsRefs(target: str, memo: dict[str, Any]) -> list[Ref]:
    as_of = str(memo.get("asOf") or "unknown")
    refs: list[Ref] = []
    for table_name, rows in (memo.get("tables") or {}).items():
        if not isinstance(rows, list):
            continue
        refs.append(
            Ref(
                id=f"table:forensics:{target}:{table_name}:{as_of}",
                kind="tableRef",
                title=f"{memo.get('companyName') or target} {table_name}",
                source="buildEvidenceForensicsMemo",
                payload={"table": table_name, "rows": rows, "period": as_of},
            )
        )
    headline = memo.get("headline") or {}
    for key in ("riskScore", "signalCount", "candidateCount"):
        refs.append(
            Ref(
                id=f"value:forensics:{target}:{key}:{as_of}",
                kind="valueRef",
                title=f"{key} {headline.get(key)}",
                source=f"table:forensics:{target}:deepDive:{as_of}",
                payload={"metric": key, "value": headline.get(key), "period": as_of},
            )
        )
    refs.append(
        Ref(
            id=f"date:forensics:{target}:{as_of}",
            kind="dateRef",
            title="forensics memo 기준시점",
            source=f"table:forensics:{target}:deepDive:{as_of}",
            payload={"period": as_of},
        )
    )
    for source in memo.get("sources") or []:
        if isinstance(source, dict):
            refs.append(
                Ref(
                    id=f"source:forensics:{target}:{source.get('id')}",
                    kind="sourceRef",
                    title=str(source.get("title") or source.get("id") or "source"),
                    source=str(source.get("url") or ""),
                    payload=source,
                )
            )
    return refs


_STATUS_LABELS = {
    "risk": "위험",
    "watch": "관찰",
    "open": "반증 필요",
    "ok": "정상",
    "mapped": "매핑됨",
    "candidate": "후보",
    "missing": "입력 부족",
    "notTriggered": "비발동",
    "usable": "사용 가능",
    "usableWithGaps": "일부 결손",
    "insufficientStatements": "원표 부족",
}

_SIGNAL_LABELS = {
    "revenueCashDivergence": "매출-현금 괴리",
    "workingCapitalPressure": "운전자본 압력",
    "noteRiskSignal": "공시/주석 위험 문구",
    "eventStatementLink": "공시 이벤트-재무제표 연결",
    "crossSectionAnomaly": "횡단면 이상치",
    "allowancePressure": "대손/손상 압력",
    "inventoryWriteDown": "재고평가손 신호",
    "relatedParty": "특수관계자 거래",
    "goingConcern": "계속기업 위험",
    "litigation": "소송/우발부채",
    "derivatives": "파생상품 노출",
    "restatement": "정정/재작성",
    "factoring": "매출채권 유동화",
}

_CLAIM_LABELS = {
    "revenue-to-cash divergence": "매출 증가가 현금 회수로 이어지는지",
    "working-capital pressure": "운전자본이 과도하게 묶이는지",
    "note text risk signal": "공시/주석 문구가 실제 위험 신호인지",
    "event-to-statement linkage": "공시 이벤트가 현재 재무 압력과 연결되는지",
}

_COUNTER_EVIDENCE_LABELS = {
    "large new customer, billing-cycle change, or seasonal receivable pattern": "신규 대형 고객, 청구 주기 변화, 계절적 매출채권 패턴",
    "inventory build for contracted backlog or supplier payment normalization": "수주잔고 대응 재고 축적, 공급업체 결제 정상화",
    "boilerplate-only wording or one-off legal disclosure without financial impact": "상투적 문구, 재무 영향 없는 일회성 법무 공시",
    "event is unrelated to current financial-statement pressure": "해당 이벤트가 현재 재무제표 압력과 무관하다는 근거",
}

_STEP_LABELS = {
    "dataCoverageAudit": "데이터 커버리지",
    "accountTraceLedger": "계정 추적",
    "revenueToCashBridge": "매출-현금 브리지",
    "workingCapitalPressureMap": "운전자본 압력",
    "noteSignalExtractor": "공시/주석 신호",
    "eventToStatementMatcher": "이벤트 매칭",
    "crossSectionAnomalyRank": "횡단면 이상치",
    "falsifierLedger": "반증 ledger",
    "engineCandidateMemo": "엔진 환류 후보",
    "finalDecision": "최종 검산 판정",
}


def _forensicsMarkdown(memo: dict[str, Any]) -> str:
    headline = memo.get("headline") or {}
    tables = memo.get("tables") or {}
    cash = (tables.get("revenueToCashBridge") or [{}])[0]
    wc = (tables.get("workingCapitalPressureMap") or [{}])[0]
    cash_worst_row = _worstRow(tables.get("revenueToCashBridge") or [])
    wc_worst_row = _worstRow(tables.get("workingCapitalPressureMap") or [])
    note_risks = [row for row in tables.get("noteSignalExtractor", []) if row.get("status") in {"watch", "risk"}][:5]
    falsifiers = tables.get("falsifierLedger") or []
    candidates = tables.get("engineCandidateMemo") or []
    deep = tables.get("deepDive") or []
    open_falsifiers = [row for row in falsifiers if row.get("status") == "open"]
    active_candidates = [row for row in candidates if row.get("status") in {"watch", "risk", "open"}]
    missing_steps = [row for row in deep if row.get("status") == "missing"]
    alert_steps = [row for row in deep if row.get("status") in {"watch", "risk", "open"}]
    decision = _forensicsDecision(headline, open_falsifiers, deep)

    lines = [
        f"{memo.get('companyName') or memo.get('target')} L1.5 포렌식 deep dive입니다.",
        "",
        (
            f"판정은 **{decision}**입니다. 기준시점은 {memo.get('asOf')}이고, "
            "L2 분석엔진 없이 Company.panel 원표와 공시/섹션 텍스트만으로 검산했습니다."
        ),
        (
            f"위험 점수는 {headline.get('riskScore')}이고 열린 반증은 {len(open_falsifiers)}개입니다. "
            f"데이터 상태는 {_statusLabel(headline.get('decisionStatus'))}입니다."
        ),
        "",
        "## 왜 이렇게 봤나",
        f"- 매출-현금: {_cashInterpretation(cash, cash_worst_row)}",
        f"- 운전자본: {_workingCapitalInterpretation(wc, wc_worst_row)}",
        f"- 공시 텍스트: {_noteInterpretation(note_risks)}",
        "",
        "## 비어있는 근거",
    ]
    lines.extend(_missingEvidenceLines(missing_steps))

    lines.extend(["", "## 반증 우선순위"])
    lines.extend(_falsifierLines(open_falsifiers, falsifiers))

    lines.extend(["", "## 엔진 환류 후보"])
    lines.extend(_candidateLines(active_candidates, candidates))

    lines.extend(["", "## 다음 확인"])
    lines.extend(_nextCheckLines(open_falsifiers, alert_steps, missing_steps))

    lines.append("")
    lines.append("답변 근거는 tableRef, valueRef, dateRef, sourceRef로 분리해 남겼습니다.")
    return "\n".join(lines)


def _forensicsDecision(
    headline: dict[str, Any],
    open_falsifiers: list[dict[str, Any]],
    deep_rows: list[dict[str, Any]],
) -> str:
    risk_score = _asFloat(headline.get("riskScore")) or 0
    panel_alert = any(row.get("status") in {"watch", "risk"} for row in deep_rows if row.get("step") != "finalDecision")
    if risk_score >= 4 or len(open_falsifiers) >= 3:
        return "위험 신호 우선 검토"
    if risk_score >= 1 or open_falsifiers:
        return "관찰 필요"
    if panel_alert:
        return "최신연도는 안정, 과거 패널 경보는 관찰"
    return "현재 입력 기준 큰 경보 없음"


def _statusLabel(value: Any) -> str:
    return _STATUS_LABELS.get(str(value), str(value or "알 수 없음"))


def _signalLabel(value: Any) -> str:
    return _SIGNAL_LABELS.get(str(value), str(value or "알 수 없음"))


def _claimLabel(value: Any) -> str:
    return _CLAIM_LABELS.get(str(value), str(value or "알 수 없음"))


def _counterEvidenceLabel(value: Any) -> str:
    return _COUNTER_EVIDENCE_LABELS.get(str(value), str(value or "알 수 없음"))


def _stepLabel(value: Any) -> str:
    return _STEP_LABELS.get(str(value), str(value or "알 수 없음"))


def _nextActionLabel(value: Any) -> str:
    text = str(value or "")
    for step, label in _STEP_LABELS.items():
        text = text.replace(step, label)
    return text


def _cashInterpretation(latest: dict[str, Any], worst: dict[str, Any] | None) -> str:
    latest_status = _statusLabel(latest.get("status"))
    latest_gap = _formatPctPoint(latest.get("receivableGrowthMinusRevenueGrowth"))
    cfo_to_net = _formatRatio(latest.get("cfoToNetIncome"))
    worst_part = _periodStatus(worst, latest_period=latest.get("period"))
    if latest.get("status") in {"watch", "risk"}:
        return (
            f"최신연도부터 {latest_status}입니다. 매출채권 증가율이 매출 증가율보다 {latest_gap} 높고, "
            f"CFO/순이익은 {cfo_to_net}입니다. {worst_part}"
        )
    return (
        f"최신연도는 {latest_status}입니다. 매출채권 증가율-매출 증가율은 {latest_gap}, "
        f"CFO/순이익은 {cfo_to_net}이라 최신 구간의 현금 회수 자체는 크게 깨지지 않았습니다. {worst_part}"
    )


def _workingCapitalInterpretation(latest: dict[str, Any], worst: dict[str, Any] | None) -> str:
    latest_status = _statusLabel(latest.get("status"))
    ccc = _formatDays(latest.get("cccDays"))
    inventory_gap = _formatPctPoint(latest.get("inventoryGrowthMinusRevenueGrowth"))
    worst_part = _periodStatus(worst, latest_period=latest.get("period"))
    if latest.get("status") in {"watch", "risk"}:
        return f"최신연도부터 {latest_status}입니다. CCC가 {ccc}이고 재고 gap은 {inventory_gap}입니다. {worst_part}"
    return f"최신연도는 {latest_status}입니다. CCC는 {ccc}, 재고 gap은 {inventory_gap}입니다. {worst_part}"


def _noteInterpretation(note_risks: list[dict[str, Any]]) -> str:
    if not note_risks:
        return "현재 확보한 텍스트 범위에서는 관찰/위험 키워드가 뚜렷하지 않습니다."
    parts = [
        f"{_signalLabel(row.get('signal'))} {_statusLabel(row.get('status'))}(hit {row.get('hitCount')})"
        for row in note_risks
    ]
    return "; ".join(parts)


def _periodStatus(row: dict[str, Any] | None, *, latest_period: Any = None) -> str:
    if not row:
        return "패널 최대 경보는 계산하지 못했습니다."
    period = row.get("period") or "unknown"
    status = _statusLabel(row.get("status"))
    if row.get("status") in {"watch", "risk"}:
        if str(period) == str(latest_period):
            return f"패널 최대 상태도 최신연도 {period}년 {status}입니다."
        return f"다만 패널 안에서는 {period}년에 {status} 구간이 있어 과거 원인을 확인해야 합니다."
    return f"패널 전체에서도 최대 상태는 {period}년 {status}입니다."


def _missingEvidenceLines(missing_steps: list[dict[str, Any]]) -> list[str]:
    if not missing_steps:
        return ["- 필수 원표와 현재 섹션 입력 기준으로 큰 결손은 없습니다."]
    lines: list[str] = []
    for row in missing_steps[:4]:
        step = _stepLabel(row.get("step"))
        if row.get("step") == "crossSectionAnomalyRank":
            lines.append(
                "- 횡단면 이상치는 기본 실행에서 제외했습니다. 필요하면 scan primitive를 켜서 peer/시장 내 위치를 보강해야 합니다."
            )
        elif row.get("step") == "eventToStatementMatcher":
            lines.append(
                "- 이벤트 공시 매칭 입력이 부족합니다. 특정 공시 이벤트와 재무제표 변동을 아직 연결하지 못했습니다."
            )
        else:
            lines.append(f"- {step} 입력이 부족합니다.")
    return lines


def _falsifierLines(open_falsifiers: list[dict[str, Any]], all_falsifiers: list[dict[str, Any]]) -> list[str]:
    if open_falsifiers:
        return [
            (
                f"- {_claimLabel(row.get('claim'))}: 확인할 반증은 "
                f"{_counterEvidenceLabel(row.get('counterEvidenceNeeded'))}입니다."
            )
            for row in open_falsifiers
        ]
    inactive = [row for row in all_falsifiers if row.get("status") == "notTriggered"]
    if inactive:
        return ["- 최신 입력 기준 열린 반증은 없습니다. 비발동 항목은 결론 근거로 쓰지 않고 감시 목록에만 남깁니다."]
    return ["- 반증 ledger가 비어 있습니다. 이 경우 위험 결론을 만들지 않습니다."]


def _candidateLines(active_candidates: list[dict[str, Any]], all_candidates: list[dict[str, Any]]) -> list[str]:
    if active_candidates:
        return [
            f"- {_signalLabel(row.get('signalId'))}: {_statusLabel(row.get('status'))}. 후보 축은 {row.get('recommendedEngineOwner')}입니다."
            for row in active_candidates
        ]
    if all_candidates:
        return ["- 이번 실행에서 바로 엔진화할 강한 후보는 없습니다. 정상/입력 부족 후보는 skill 검산 경로에 남깁니다."]
    return ["- 엔진 후보 memo가 생성되지 않았습니다."]


def _nextCheckLines(
    open_falsifiers: list[dict[str, Any]],
    alert_steps: list[dict[str, Any]],
    missing_steps: list[dict[str, Any]],
) -> list[str]:
    lines: list[str] = []
    if open_falsifiers:
        lines.append("- 열린 반증부터 확인합니다. 반증이 해소되지 않으면 위험 점수를 낮추지 않습니다.")
    if alert_steps:
        evidence_alerts = [
            row
            for row in alert_steps
            if row.get("step") not in {"falsifierLedger", "engineCandidateMemo", "finalDecision"}
        ]
        labels = ", ".join(_stepLabel(row.get("step")) for row in evidence_alerts[:3])
        if not labels:
            labels = ", ".join(_stepLabel(row.get("step")) for row in alert_steps[:3])
        lines.append(f"- 경보가 걸린 단계는 {labels}입니다. 이 단계의 원표 row와 기간별 변화를 먼저 봅니다.")
    if missing_steps:
        lines.append("- 입력 부족 단계는 결론에서 제외하고, 보강 전에는 엔진 후보로 승격하지 않습니다.")
    if not lines:
        lines.append("- 다음 실행에서는 같은 기준으로 분기별 갱신 여부만 확인하면 됩니다.")
    return lines


def _worstRow(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    rank = {"missing": 0, "candidate": 1, "ok": 1, "mapped": 1, "notTriggered": 1, "watch": 2, "open": 2, "risk": 3}
    if not rows:
        return None
    return max(rows, key=lambda row: rank.get(str(row.get("status") or "missing"), 0))


def _worstStatus(rows: list[dict[str, Any]]) -> str:
    rank = {"missing": 0, "candidate": 1, "ok": 1, "mapped": 1, "notTriggered": 1, "watch": 2, "open": 2, "risk": 3}
    if not rows:
        return "missing"
    return max((str(row.get("status") or "missing") for row in rows), key=lambda status: rank.get(status, 0))


def _formatPctPoint(value: Any) -> str:
    number = _asFloat(value)
    return "계산 불가" if number is None else f"{number * 100:.1f}%p"


def _formatRatio(value: Any) -> str:
    number = _asFloat(value)
    return "계산 불가" if number is None else f"{number:.2f}x"


def _formatDays(value: Any) -> str:
    number = _asFloat(value)
    return "계산 불가" if number is None else f"{number:.1f}일"


def _asFloat(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number


def _composeAnswer(state: WorkbenchState, results: list[dict[str, Any]]) -> str:
    tool_results = [item["result"] for item in results if item["result"].ok]
    if len(tool_results) >= 2 and _allStatementResults(tool_results):
        return _composeStatementComparison(tool_results)
    for result in tool_results:
        markdown = result.data.get("markdown")
        if markdown:
            return str(markdown)
    if tool_results:
        return _composeToolSummary(tool_results)
    return _composeReferenceAnswer(state)


def _allStatementResults(results: list[ToolResult]) -> bool:
    return all(isinstance(result.data, dict) and result.data.get("summary", {}).get("statement") for result in results)


def _composeStatementComparison(results: list[ToolResult]) -> str:
    left, right = results[0].data, results[1].data
    left_label = f"{left.get('companyName')}({left.get('stockCode')})"
    right_label = f"{right.get('companyName')}({right.get('stockCode')})"
    left_summary = left.get("summary") or {}
    right_summary = right.get("summary") or {}
    period = left_summary.get("latestPeriod")
    lines = [
        f"{left_label}와 {right_label} 재무상태표를 {period} 기준으로 비교했습니다.",
        "",
        f"| 항목 | {left.get('companyName')} | {right.get('companyName')} |",
        "|---|---:|---:|",
    ]
    left_rows = {row["item"]: row for row in left_summary.get("rows") or []}
    right_rows = {row["item"]: row for row in right_summary.get("rows") or []}
    for label in [label for label in left_rows if label in right_rows][:10]:
        lines.append(f"| {label} | {left_rows[label]['formatted']} | {right_rows[label]['formatted']} |")
    ratio = _assetRatio(left_summary, right_summary)
    if ratio is not None:
        lines.extend(
            [
                "",
                "## 핵심 차이",
                f"- 자산총계는 {left.get('companyName')}가 {right.get('companyName')}의 약 {ratio:.1f}배입니다.",
            ]
        )
    lines.append("")
    lines.append("근거는 각 회사 tableRef, valueRef, dateRef로 분리해 남겼습니다.")
    return "\n".join(lines)


def _assetRatio(left: dict[str, Any], right: dict[str, Any]) -> float | None:
    def find(summary: dict[str, Any]) -> float | None:
        """summary.rows 에서 total_assets 행 값을 float 로 추출 (실패 시 None)."""
        for row in summary.get("rows") or []:
            if row.get("snakeId") == "total_assets":
                try:
                    return float(row.get("value"))
                except (TypeError, ValueError):
                    return None
        return None

    left_value = find(left)
    right_value = find(right)
    if left_value is None or right_value in (None, 0):
        return None
    return left_value / right_value


def _composeToolSummary(results: list[ToolResult]) -> str:
    lines = ["실행 결과를 확인했습니다.", ""]
    for result in results:
        lines.append(f"- {result.summary}")
    lines.append("")
    lines.append("근거 ref를 분리해 남겼습니다.")
    return "\n".join(lines)


def _composeReferenceAnswer(state: WorkbenchState) -> str:
    skill_rows = []
    for ref in state.selectedSkillRefs[:5]:
        payload = ref.payload if isinstance(ref.payload, dict) else {}
        skill_rows.append(
            (payload.get("id") or _skillId(ref), payload.get("title") or ref.title, payload.get("purpose") or "")
        )
    api_rows = []
    for ref in state.apiRefs[:5]:
        payload = ref.payload if isinstance(ref.payload, dict) else {}
        api_rows.append((payload.get("apiRef") or ref.id.removeprefix("api:"), payload.get("summary") or ""))
    lines = ["Skill OS와 generated spec을 기준으로 가능한 실행 경로를 확인했습니다.", ""]
    if skill_rows:
        lines.append("## 관련 skill")
        for skill_id, title, purpose in skill_rows:
            lines.append(f"- {skill_id}: {title} — {purpose}")
        lines.append("")
    if api_rows:
        lines.append("## 호출 가능한 API 후보")
        for apiRef, summary in api_rows:
            lines.append(f"- {apiRef}: {summary}")
        lines.append("")
    lines.append(
        "데이터 실행이 필요한 질문은 target, 기간, 지표를 포함하면 해당 skill/capability로 실행하고 ref 검증까지 진행합니다."
    )
    return "\n".join(lines)


def _failureMessage(reason: str) -> str:
    labels = {
        "company_not_resolved": "종목을 먼저 특정해야 분석할 수 있습니다. 예: `삼성전자 재무상태표 확인`",
        "missing_tool_plan": "선택한 skill과 generated spec으로 실행 계획을 만들지 못했습니다. 관련 skill/capability를 보강해야 합니다.",
        "empty_scan": "스캔 결과가 비어 있어 후보를 만들 수 없습니다. scan 데이터 수집 상태를 먼저 확인해야 합니다.",
        "scan_growth_no_rankable_rows": "성장성 스캔은 실행됐지만 순위를 만들 핵심 지표가 부족합니다.",
    }
    return labels.get(reason, f"답변에 필요한 근거 검증을 통과하지 못했습니다: {reason}")


def _toolSummary(tool: str, args: dict[str, Any]) -> str:
    if tool in ("EngineCall", "engine_call"):
        plan = args.get("plan") or args
        apiRef = plan.get("apiRef") or f"{plan.get('engine')}.{plan.get('method')}"
        target = plan.get("target") or plan.get("axis") or plan.get("path") or ""
        return f"{apiRef} {target}".strip()
    return str(args.get("query") or args.get("target") or tool)


def _harvestArtifacts(state: WorkbenchState) -> list[dict[str, Any]]:
    return [ref.toDict() for ref in state.refs if ref.kind == "artifactRef"]


def _chunks(text: str, *, size: int = 240) -> Iterator[str]:
    for index in range(0, len(text), size):
        yield text[index : index + size]
