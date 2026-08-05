"""런타임 턴의 결과 원장 전이와 evidence projection을 관리한다."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from dartlab.productOutcome import advanceOutcome, registerOutcomeEvidence, startOutcome

from .answerQuality import evaluateAnswerQuality
from .contracts import AgentEvent

logger = logging.getLogger(__name__)

_GROUNDING_TOOL_NAMES = frozenset(
    {
        "EngineCall",
        "InspectDataset",
        "RunPython",
        "PeerCompareN",
        "DCFValuation",
        "CompileFinancialDashboard",
        "RegressionForecast",
        "SensitivityAnalysis",
        "CreditScorecard",
        "ScenarioCompareN",
        "ScenarioOverlay",
    }
)


@dataclass
class _OutcomeTracker:
    """한 runtime turn의 content-free 결과 전이만 추적한다."""

    outcomeId: str | None
    question: str
    scoped: bool = False
    grounded: bool = False
    answerText: str = ""
    completed: bool = False
    completionSucceeded: bool = False
    failed: bool = False
    registeredRefIds: set[str] = field(default_factory=set)
    registeredRefs: dict[str, dict[str, Any]] = field(default_factory=dict)
    toolNames: dict[str, str] = field(default_factory=dict)
    readSkillCalls: int = 0
    coverageContract: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def start(cls, question: str) -> _OutcomeTracker:
        """결과 원장 오류가 실제 에이전트 턴을 막지 않는 tracker를 만든다."""
        from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

        coverage = coveragePacketForQuestion(question)
        try:
            return cls(startOutcome(feature="ask").outcomeId, question, coverageContract=coverage)
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 시작 기록 실패")
            return cls(None, question, coverageContract=coverage)

    @classmethod
    def resume(
        cls,
        question: str,
        *,
        outcomeId: str,
        refs: list[dict[str, Any]],
        readSkillCalls: int,
    ) -> _OutcomeTracker:
        """같은 native session의 교정 턴이 기존 outcome과 근거를 이어받게 한다."""
        from dartlab.reference.capability.analysisGraph import coveragePacketForQuestion

        registered = {str(ref["id"]): dict(ref) for ref in refs if isinstance(ref, dict) and ref.get("id")}
        return cls(
            outcomeId,
            question,
            scoped=bool(registered),
            grounded=bool(registered),
            registeredRefIds=set(registered),
            registeredRefs=registered,
            readSkillCalls=readSkillCalls,
            coverageContract=coveragePacketForQuestion(question),
        )

    def enrich(self, event: AgentEvent) -> dict[str, Any]:
        """tool 상관관계와 evidence receipt를 반영한 공개 payload를 만든다."""
        payload = dict(event.payload)
        toolId = _toolCallId(payload)
        if event.kind == "toolStarted":
            toolName = _toolName(payload)
            if toolId and toolName:
                self.toolNames[toolId] = toolName
            if toolName:
                payload["nativeName"] = toolName
                payload["canonicalName"] = _canonicalToolName(toolName)
            if toolId:
                payload["toolCallId"] = toolId
        elif event.kind == "toolCompleted":
            self._groundToolResult(payload, toolId=toolId)
        elif event.kind == "turnCompleted":
            payload["runtimeCoverage"] = {
                "readSkillCalls": self.readSkillCalls,
                "contractIds": list(self.coverageContract.get("contractIds") or ()),
                "requiredEvidence": list(self.coverageContract.get("requiredEvidence") or ()),
                "candidateCapabilityRefs": list(self.coverageContract.get("candidateCapabilityRefs") or ()),
            }
        if self.outcomeId:
            payload["outcomeId"] = self.outcomeId
        return payload

    def _groundToolResult(self, payload: dict[str, Any], *, toolId: str) -> None:
        """허용된 grounding tool의 정형 ref만 원장에 등록한다."""
        toolName = _toolName(payload) or self.toolNames.get(toolId, "")
        if toolName:
            payload["toolName"] = toolName
            payload["nativeName"] = toolName
            payload["canonicalName"] = _canonicalToolName(toolName)
        if toolId:
            payload["toolCallId"] = toolId
        if _canonicalToolName(toolName) == "ReadSkill" and not _toolFailed(payload):
            self.readSkillCalls += 1
        refDetails = _evidenceDetails(payload)
        refIds = [str(item["id"]) for item in refDetails]
        if not self._canGround(toolName, refIds, payload):
            return
        try:
            if not self.scoped:
                advanceOutcome(str(self.outcomeId), "scoped")
                self.scoped = True
            if not self.grounded:
                advanceOutcome(str(self.outcomeId), "grounded")
                self.grounded = True
            registerOutcomeEvidence(str(self.outcomeId), refIds)
            self.registeredRefIds.update(refIds)
            self.registeredRefs.update({str(item["id"]): dict(item) for item in refDetails})
            payload["evidenceRefs"] = refIds
            payload["refDetails"] = [{**item, "outcomeId": self.outcomeId} for item in refDetails]
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 근거 기록 실패")

    def _canGround(self, toolName: str, refIds: list[str], payload: dict[str, Any]) -> bool:
        """현재 completion이 실제 DartLab grounding receipt인지 판정한다."""
        canonical = _canonicalToolName(toolName)
        if canonical == "RunPython" and not _runPythonEvidenceHasLineage(_evidenceDetails(payload)):
            return False
        return bool(self.outcomeId and canonical in _GROUNDING_TOOL_NAMES and refIds and not _toolFailed(payload))

    def observe(self, event: AgentEvent) -> None:
        """전달, 완료, 실패 표식만 누적한다."""
        if event.kind == "messageDelta" and event.payload.get("text"):
            self.answerText += str(event.payload["text"])
        elif event.kind == "turnCompleted":
            self.completed = True
            self.completionSucceeded = _turnCompletedSuccessfully(event.payload)
        elif event.kind == "runtimeError":
            self.failed = True

    def finalize(self) -> None:
        """근거와 답변이 모두 완주한 턴만 delivered로 전진시킨다."""
        if not (
            self.outcomeId
            and self.grounded
            and self.answerText.strip()
            and self.completed
            and self.completionSucceeded
            and self.registeredRefIds
            and self._qualityPassed()
            and not self.failed
        ):
            return
        try:
            advanceOutcome(self.outcomeId, "delivered")
        except Exception:  # noqa: BLE001
            logger.exception("product outcome 전달 기록 실패")

    def _qualityPassed(self) -> bool:
        """질문 유형별 evidence와 값 및 시점 binding이 모두 통과했는지 확인한다."""
        report = evaluateAnswerQuality(
            self.question,
            self.answerText,
            list(self.registeredRefs.values()),
            completionSucceeded=self.completed and self.completionSucceeded,
            failed=self.failed,
            readSkillCalls=self.readSkillCalls,
        )
        return report.passed


def _toolCallId(payload: dict[str, Any]) -> str:
    """네이티브 tool event payload에서 상관관계용 호출 ID를 읽는다."""
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    return str(item.get("id") or item.get("toolCallId") or item.get("tool_call_id") or item.get("tool_use_id") or "")


def _toolName(payload: dict[str, Any]) -> str:
    """네이티브 tool event payload에서 가능한 경우 실제 MCP tool 이름을 읽는다."""
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    return str(payload.get("toolName") or item.get("tool") or item.get("name") or item.get("title") or "")


def _canonicalToolName(name: str) -> str:
    """런타임별 MCP prefix 또는 옛 별칭을 canonical 도구 이름으로 바꾼다."""
    value = name.rsplit("__", 1)[-1].rsplit("/", 1)[-1]
    aliases = {
        "engine_call": "EngineCall",
        "inspect_dataset": "InspectDataset",
        "read_skill": "ReadSkill",
        "run_python": "RunPython",
    }
    return aliases.get(value, value)


def _runPythonEvidenceHasLineage(refs: list[dict[str, Any]]) -> bool:
    """RunPython 파생 근거가 canonical upstream ref를 모두 보존했는지 확인한다."""
    derived = [ref for ref in refs if ref.get("kind") in {"tableRef", "valueRef", "dateRef"}]
    if not derived:
        return False
    for ref in derived:
        provenance = ref.get("payload", {}).get("provenance") if isinstance(ref.get("payload"), dict) else None
        if not isinstance(provenance, list) or not any(
            isinstance(item, str)
            and item.startswith(("table:", "doc:", "value:", "date:", "dataset:"))
            and ":local:" not in item
            for item in provenance
        ):
            return False
    return True


def _toolFailed(payload: dict[str, Any]) -> bool:
    """tool completion payload에 명시적인 실패 표식이 있는지 확인한다."""
    item = payload.get("item") if isinstance(payload.get("item"), dict) else payload
    status = str(item.get("status") or "").lower()
    if status in {"failed", "error", "cancelled", "canceled"} or item.get("is_error") is True:
        return True
    # Codex mcpToolCall 은 실패를 별도 `error` 필드로 싣는다.
    if item.get("error"):
        return True
    return _containsFalseOk(item)


def _containsFalseOk(value: Any, *, depth: int = 0) -> bool:
    """제한된 깊이의 tool result에서 `ok: false`를 찾는다."""
    if depth > 6:
        return False
    if isinstance(value, dict):
        if value.get("ok") is False:
            return True
        return any(_containsFalseOk(item, depth=depth + 1) for item in value.values())
    if isinstance(value, list):
        return any(_containsFalseOk(item, depth=depth + 1) for item in value[:200])
    return False


def _turnCompletedSuccessfully(payload: dict[str, Any]) -> bool:
    """runtime별 terminal turn payload가 정상 완료 상태인지 판정한다."""
    turn = payload.get("turn") if isinstance(payload.get("turn"), dict) else {}
    status = str(payload.get("status") or turn.get("status") or payload.get("stopReason") or "completed").lower()
    return status not in {"failed", "error", "interrupted", "cancelled", "canceled", "refused"}


def _evidenceDetails(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """tool 결과 속 정형 evidence ref를 작은 공개 projection으로 변환한다."""
    found: dict[str, dict[str, Any]] = {}

    def visit(value: Any, *, depth: int = 0, inRefs: bool = False) -> None:
        """제한된 깊이와 개수 안에서 evidence ref 후보를 순회한다."""
        if depth > 8 or len(found) >= 100:
            return
        if isinstance(value, str):
            stripped = value.strip()
            if len(stripped) <= 262_144 and stripped[:1] in {"{", "["}:
                try:
                    visit(json.loads(stripped), depth=depth + 1, inRefs=inRefs)
                except (TypeError, ValueError, json.JSONDecodeError):
                    return
            return
        if isinstance(value, list):
            for item in value[:200]:
                visit(item, depth=depth + 1, inRefs=inRefs)
            return
        if not isinstance(value, dict):
            return
        refId = value.get("id")
        kind = str(value.get("kind") or "")
        if isinstance(refId, str) and refId and (inRefs or kind.endswith("Ref")):
            found.setdefault(
                refId,
                {
                    "id": refId,
                    "kind": kind or "evidenceRef",
                    "title": str(value.get("title") or refId)[:500],
                    "source": str(value.get("source") or "")[:1000],
                    "sourceType": str(value.get("sourceType") or "internal")[:100],
                    "payload": _publicEvidencePayload(value.get("payload"), kind=kind),
                },
            )
        for key, item in value.items():
            visit(item, depth=depth + 1, inRefs=inRefs or key in {"refs", "evidence", "refDetails"})

    visit(payload)
    return list(found.values())


def _publicEvidencePayload(value: Any, *, kind: str = "") -> dict[str, Any]:
    """근거 종류별 검증 필드를 bounded projection으로 공개한다."""
    if not isinstance(value, dict):
        return {}
    common = {
        "stockCode",
        "target",
        "period",
        "periods",
        "metric",
        "canonicalMetricId",
        "metrics",
        "value",
        "unit",
        "currency",
        "dataAsOf",
        "asOf",
        "page",
        "apiRef",
        "status",
        "specified",
        "complete",
        "rowCount",
        "statement",
        "sourcePeriods",
        "provenance",
        "sourceRef",
        "key",
        "timeseries",
    }
    byKind = {
        "tableRef": {"rows", "columns", "missingCells", "filter", "formula", "universe", "datasetAsOf"},
        "docRef": {"rceptNo", "filedAt", "section", "sections", "reportType", "excerpt", "fields", "url"},
        "executionRef": {"stockCodes", "targets", "missingCells", "coverage", "gaps", "receipt"},
        "datasetRef": {"columns", "universe", "datasetAsOf", "filter", "formula"},
        "valueRef": {"rank", "basis", "label", "axis", "scenario"},
        "dateRef": {"knowledgeBoundary", "requestedAsOf"},
    }
    allowed = common | byKind.get(kind, set())
    result: dict[str, Any] = {}
    for key in sorted(allowed):
        if key not in value:
            continue
        projected = _boundedEvidenceValue(value[key])
        if projected is not _EVIDENCE_OMIT:
            result[key] = projected
    return result


_EVIDENCE_OMIT = object()


def _boundedEvidenceValue(value: Any, *, depth: int = 0) -> Any:
    """근거 상세 drawer에 필요한 구조를 크기와 깊이 제한 안에서 보존한다."""
    if depth > 4:
        return _EVIDENCE_OMIT
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return value[:2_000]
    if isinstance(value, list | tuple):
        rows = []
        for item in value[:40]:
            projected = _boundedEvidenceValue(item, depth=depth + 1)
            if projected is not _EVIDENCE_OMIT:
                rows.append(projected)
        return rows
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:40]:
            projected = _boundedEvidenceValue(item, depth=depth + 1)
            if projected is not _EVIDENCE_OMIT:
                result[str(key)] = projected
        return result
    return _EVIDENCE_OMIT
