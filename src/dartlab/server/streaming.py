"""SSE 스트리밍 generator — ask 내부 이벤트 → SSE 변환.

[최우선 UX 원칙] 사용자용 진행 요약과 raw evidence 분리

모든 분석 로직은 dartlab.ai.kernel.ask 가 처리.
이 모듈은 이벤트를 SSE dict로 변환하는 thin adapter.

5 패스 흐름 (workbench loop SSOT):
  brief → work → critique → compose → gate → harvest
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import threading
from dataclasses import dataclass

from dartlab.ai.trace import AuditCollector

from .models import AskRequest

log = logging.getLogger(__name__)

# Streaming 안정성 튜닝 (환경변수 override 가능)
#   DARTLAB_STREAM_QUEUE_MAX — async bridge 큐 최대 엔트리 (기본 1024).
#                              64 고정 시 chunk 폭주하면 producer blocking.
#   DARTLAB_STREAM_PUT_TIMEOUT — queue.put 타임아웃(초). 느린 소비자·disconnect 감지.
_DEFAULT_QUEUE_MAX = int(os.environ.get("DARTLAB_STREAM_QUEUE_MAX", "1024"))
_DEFAULT_PUT_TIMEOUT = float(os.environ.get("DARTLAB_STREAM_PUT_TIMEOUT", "30"))

_FAILURE_LABELS = {
    "finalize_answer_failed": "최종 답변 생성 실패",
    "forced_finalize_failed": "최종 답변 생성 실패",
    "forced_finalize_prose_failed": "최종 답변 생성 실패",
    "draft_verification_failed": "초안 검증 실패",
    "prose_without_finalize": "초안 검증 실패",
    "prose_without_finalize_failed": "최종 답변 생성 실패",
    "provider_create_failed": "provider 연결 실패",
    "provider_transport_failed": "provider 연결 실패",
    "provider_unavailable": "provider 연결 실패",
    "tool_failed": "도구 실행 실패",
    "verification_failed": "검산 실패",
    "missing_skill_ref": "근거 skill 부족",
    "unsupported_numeric_claim": "숫자 근거 부족",
    "unsupported_date_claim": "날짜 근거 부족",
    "failed_execution_hidden": "도구 실패 은폐",
    "tool_transcript_released": "내부 실행 로그 노출",
}
_SPINNER_ACTIVITY_TOOLS = {"run_python", "compile_visual"}


@dataclass
class AnalysisStreamError(RuntimeError):
    """ask event error surfaced to server adapters."""

    message: str
    action: str = ""
    detail: str | None = None


async def streamAsk(req: AskRequest):
    """ask 이벤트 → SSE 변환.

    모든 분석 로직은 ask workbench 에 위임. 종목 resolve 는 AI 가 자율 판단.
    """
    kwargs = _buildKwargs(req)
    auditor = AuditCollector(
        question=req.question,
        stockCode_hint=kwargs.get("stockCode"),
        provider=None,
        model=None,
    )
    try:
        async for item in streamAnalysis(req.question, _audit=auditor, **kwargs):
            yield item
    finally:
        auditor.flush()


async def streamAnalysis(question: str = "", *, _audit: AuditCollector | None = None, **kwargs):
    """ask internal events → SSE adapter."""
    from dartlab.ai.kernel import _askEvents

    activity_count = 0
    async for event in _syncGenToAsync(_askEvents, question, **kwargs):
        if _audit is not None:
            _audit.observe(event.kind, event.data)
        activity = _activityFromEvent(event.kind, event.data)
        if activity is not None:
            activity_count += 1
            activity["index"] = activity_count
            yield _sse("activity", activity)
        if event.kind == "done":
            meta = event.data.setdefault("responseMeta", {})
            meta.setdefault("activityCount", activity_count)
            meta.setdefault("responseStatus", _responseStatusFromDone(event.data))
            if meta["responseStatus"] != "ok":
                meta.setdefault("failureReason", _failureReasonFromDone(event.data))
        yield _sse(event.kind, event.data)


async def collectAnalysisText(question: str = "", **kwargs) -> str:
    """ask 실행 후 chunk 텍스트 수집 (non-stream HTTP endpoint 용)."""
    result = await collectAnalysisResult(question, **kwargs)
    return result["answer"]


async def collectAnalysisResult(question: str = "", **kwargs) -> dict:
    """ask 실행 후 답변과 tool CSV 아티팩트를 함께 수집한다."""
    from dartlab.ai.kernel import _askEvents

    auditor = AuditCollector(
        question=question,
        stockCode_hint=kwargs.get("stockCode"),
        provider=None,
        model=None,
    )
    chunks: list[str] = []
    artifacts: list[dict] = []
    evidence: list[dict] = []
    claims: list[dict] = []
    visuals: list[dict] = []
    limits: list[str] = []
    refs: list[dict] = []
    trace: list[dict] = []
    verification: dict = {}
    responseMeta: dict = {}
    activity_count = 0
    try:
        async for event in _syncGenToAsync(_askEvents, question, **kwargs):
            auditor.observe(event.kind, event.data)
            if _activityFromEvent(event.kind, event.data) is not None:
                activity_count += 1
            if event.kind == "chunk":
                chunks.append(event.data.get("text", ""))
            elif event.kind == "tool_result":
                artifacts.extend(event.data.get("artifacts") or [])
            elif event.kind == "artifact":
                artifacts.extend(event.data.get("artifacts") or [])
            elif event.kind == "evidence":
                evidence.append(event.data)
            elif event.kind == "claim":
                claims.append(event.data)
            elif event.kind in {"chart", "visual"}:
                visuals.extend([v for v in event.data.get("visuals") or [] if isinstance(v, dict)])
            elif event.kind == "done":
                evidence = _dedupeById(evidence + [v for v in event.data.get("evidence") or [] if isinstance(v, dict)])
                claims = _dedupeById(claims + [v for v in event.data.get("claims") or [] if isinstance(v, dict)])
                visuals = _dedupeVisuals(visuals + [v for v in event.data.get("visuals") or [] if isinstance(v, dict)])
                limits.extend(str(v) for v in event.data.get("limits") or [])
                refs = _dedupeById([v for v in event.data.get("refs") or [] if isinstance(v, dict)])
                trace = [v for v in event.data.get("trace") or [] if isinstance(v, dict)]
                verification = event.data.get("verification") or {}
                responseMeta = event.data.get("responseMeta") or {}
                responseMeta.setdefault("activityCount", activity_count)
                responseMeta.setdefault("responseStatus", _responseStatusFromDone(event.data))
                if responseMeta["responseStatus"] != "ok":
                    responseMeta.setdefault("failureReason", _failureReasonFromDone(event.data))
            elif event.kind == "error":
                error_code = event.data.get("error", "analysis error")
                if error_code in {"provider_create_failed", "provider_transport_failed", "tool_failed"}:
                    limits.append(f"{error_code}: {event.data.get('detail') or event.data.get('action') or ''}".strip())
                    continue
                raise AnalysisStreamError(
                    error_code,
                    action=event.data.get("action", ""),
                    detail=event.data.get("detail"),
                )
    finally:
        auditor.flush()
    return _sanitizeNanInf(
        {
            "answer": "".join(chunks),
            "artifacts": _dedupeArtifacts(artifacts),
            "evidence": _dedupeById(evidence),
            "claims": _dedupeById(claims),
            "visuals": _dedupeVisuals(visuals),
            "limits": _dedupeStrings(limits),
            "refs": refs,
            "trace": trace,
            "verification": verification,
            "responseMeta": responseMeta,
        }
    )


def _sanitizeNanInf(obj):
    """JSON 호환 — NaN / Inf / -Inf float 을 None 으로 재귀 변환.

    polars/pandas 가 missing 을 NaN 으로 표기하는 경우가 있어 ref payload 안에
    섞여 들어오면 fastapi 의 json.dumps(allow_nan=False) 가 ValueError 발생.
    """
    import math

    if isinstance(obj, dict):
        return {k: _sanitizeNanInf(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitizeNanInf(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_sanitizeNanInf(v) for v in obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


def _buildKwargs(req: AskRequest) -> dict:
    """AskRequest → ask workbench kwargs 변환."""
    kwargs: dict = {
        "include": req.include,
        "exclude": req.exclude,
        "history": [h.model_dump() for h in req.history] if req.history else None,
        "view_context": req.viewContext.model_dump() if req.viewContext else None,
        "report_mode": req.reportMode,
    }

    # req.company / viewContext 종목코드 → AI stockCode 힌트로 전달
    hintCode = req.company
    if not hintCode and req.viewContext and req.viewContext.company:
        vc = req.viewContext.company
        hintCode = vc.stockCode or vc.corpName or vc.company
    if hintCode:
        kwargs["stockCode"] = hintCode

    return kwargs


def _dedupeArtifacts(artifacts: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for artifact in artifacts:
        key = str(artifact.get("url") or artifact.get("id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(artifact)
    return out


def _dedupeById(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = str(item.get("id") or item.get("url") or item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupeVisuals(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for item in items:
        key = _visualDedupeKey(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _visualDedupeKey(item: dict) -> str:
    spec = item.get("spec") if isinstance(item, dict) else None
    if not isinstance(spec, dict):
        return str(item.get("id") or item.get("url") or item)
    series = spec.get("series")
    categories = spec.get("categories")
    if isinstance(series, list) and isinstance(categories, list):
        compact_series = []
        for row in series:
            if not isinstance(row, dict):
                continue
            compact_series.append({"name": row.get("name"), "data": row.get("data")})
        return json.dumps(
            {
                "vizType": spec.get("vizType") or "chart",
                "chartType": spec.get("chartType"),
                "categories": categories,
                "series": compact_series,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    return json.dumps(spec, ensure_ascii=False, sort_keys=True)


def _dedupeStrings(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _sse(event: str, data: dict) -> dict:
    """이벤트 → SSE dict 변환."""
    return {"event": event, "data": json.dumps(_publicSseData(data), ensure_ascii=False)}


def _publicSseData(value):
    if isinstance(value, dict):
        return {key: _publicSseData(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_publicSseData(item) for item in value]
    if isinstance(value, str):
        return (
            value.replace("search_reference", "search reference")
            .replace("read_context", "read context")
            .replace("generated_spec_search", "generated spec search")
            .replace("engine_call", "engine call")
            .replace("run_python", "run python")
            .replace("verify_answer", "verify answer")
        )
    return value


def _activityFromEvent(kind: str, data: dict) -> dict | None:
    """TraceEvent → 사용자용 activity payload.

    채팅 본문은 raw trace를 직접 보지 않고 이 1줄 payload만 렌더한다.
    """
    if kind == "plan":
        skills = data.get("selectedSkillIds") if isinstance(data.get("selectedSkillIds"), list) else []
        target = ", ".join(str(item) for item in skills[:3])
        return _activity(
            "plan", "계획 수립", "done", f"분석 경로를 정했습니다{': ' + target if target else ''}", target
        )
    if kind == "reference":
        if data.get("action"):
            return None
        action = str(data.get("action") or "search reference").replace("_", " ")
        refs = data.get("refs") if isinstance(data.get("refs"), list) else []
        ref = data.get("ref") if isinstance(data.get("ref"), dict) else None
        target = _targetFromReference(data, ref)
        if action == "read context":
            summary = f"read context 실행함{': ' + target if target else ''}"
        else:
            summary = f"search reference 실행함{': ' + target if target else ''} · refs {len(refs)}개"
        return _activity(action, _displayToolName(action), "done", summary, target, refs=_refIds(refs, ref))
    if kind in {"inspect", "execute", "visual"}:
        if data.get("action"):
            return None
        action = str(data.get("action") or ("run_python" if kind == "execute" else kind))
        return _activity(
            action,
            _displayToolName(action),
            "done",
            _summaryForTrace(kind, data),
            _targetFromTrace(kind, data),
            refs=_refsFromTrace(data),
        )
    if kind in {"tool_start", "tool_call"}:
        name = str(data.get("name") or data.get("tool") or "tool")
        if name not in _SPINNER_ACTIVITY_TOOLS:
            return None
        target = _targetFromToolPayload(data)
        return _activity(
            name,
            _displayToolName(name),
            "running",
            f"{_displayToolName(name)} 실행함{': ' + target if target else ''}",
            target,
            activityId=_toolActivityId(data, name),
        )
    if kind == "tool_result":
        name = str(data.get("name") or data.get("tool") or "tool")
        status = "error" if data.get("status") == "error" else "done"
        summary = str(data.get("outputSummary") or data.get("summary") or "")
        target = _targetFromToolPayload(data)
        line = f"{_displayToolName(name)} {'실패' if status == 'error' else '완료'}"
        if summary:
            line += f": {summary}"
        return _activity(
            name,
            _displayToolName(name),
            status,
            line,
            target,
            refs=[str(v) for v in data.get("evidenceRefs") or []],
            error=_errorFromPayload(data) if status == "error" else None,
            activityId=_toolActivityId(data, name),
        )
    if kind == "verify":
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        ok = bool(result.get("ok"))
        issues = result.get("issues") if isinstance(result.get("issues"), list) else []
        summary = "verify 실행함: 숫자/날짜/근거 검증 통과" if ok else f"verify 실패: {_issueCodes(issues)}"
        return _activity(
            "verify",
            "verify",
            "done" if ok else "error",
            summary,
            str(data.get("refId") or ""),
            refs=[str(data.get("refId"))] if data.get("refId") else [],
            error=None if ok else summary,
        )
    if kind == "answer":
        refs = [str(v) for v in data.get("evidenceRefs") or []]
        return _activity(
            "answer", "answer", "done", f"answer 실행함: 근거 refs {len(refs)}개로 답변 작성", "", refs=refs
        )
    if kind == "unable":
        reason = _readableFailure(str(data.get("reason") or "finalize_answer_failed"))
        return _activity("unable", "unable", "error", reason, "", error=reason)
    if kind == "draft_rejected":
        return None
    if kind == "artifact":
        artifacts = data.get("artifacts") if isinstance(data.get("artifacts"), list) else []
        return _activity(
            "artifact",
            "artifact",
            "done",
            f"artifact 생성함: {len(artifacts)}개",
            "",
            artifactRefs=[str(a.get("id") or a.get("url")) for a in artifacts if isinstance(a, dict)],
        )
    if kind == "error":
        reason = _readableFailure(str(data.get("error") or data.get("detail") or "실행 오류"))
        return _activity("error", "error", "error", f"오류 발생: {reason}", str(data.get("action") or ""), error=reason)
    return None


def _activity(
    kind: str,
    displayName: str,
    status: str,
    summary: str,
    target: str = "",
    *,
    refs: list[str] | None = None,
    artifactRefs: list[str] | None = None,
    error: str | None = None,
    activityId: str | None = None,
) -> dict:
    digest = hashlib.sha1(
        json.dumps([kind, summary, target, refs or [], artifactRefs or []], ensure_ascii=False, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()[:12]
    return {
        "id": activityId or f"activity:{kind}:{digest}",
        "kind": kind,
        "displayName": displayName,
        "status": status,
        "summary": summary,
        "target": target,
        "refs": refs or [],
        "artifactRefs": artifactRefs or [],
        "error": error,
    }


def _displayToolName(name: str) -> str:
    return str(name or "tool").replace("_", " ")


def _toolActivityId(data: dict, name: str) -> str:
    call_id = str(data.get("id") or data.get("toolCallId") or "")
    if call_id:
        return f"activity:tool:{call_id}"
    return f"activity:{name}:unknown"


def _readableFailure(value: str) -> str:
    text = str(value or "")
    if not text:
        return "최종 답변 생성 실패"
    for code, label in _FAILURE_LABELS.items():
        text = text.replace(code, label)
    return text


def _targetFromReference(data: dict, ref: dict | None) -> str:
    if ref:
        payload = ref.get("payload") if isinstance(ref.get("payload"), dict) else {}
        return str(payload.get("path") or payload.get("title") or ref.get("id") or "")
    query = data.get("query")
    if isinstance(query, str) and query:
        return f'"{query[:120]}"'
    refs = data.get("refs") if isinstance(data.get("refs"), list) else []
    for item in refs:
        if not isinstance(item, dict):
            continue
        payload = item.get("payload") if isinstance(item.get("payload"), dict) else {}
        title = payload.get("title") or payload.get("skillId") or payload.get("path")
        if title:
            return str(title)
    return ""


def _targetFromTrace(kind: str, data: dict) -> str:
    if kind == "inspect":
        return str(data.get("target") or data.get("datasetId") or "")
    if kind == "execute":
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        return str(data.get("refId") or result.get("id") or "")
    if kind == "visual":
        return str(data.get("refId") or "")
    return ""


def _summaryForTrace(kind: str, data: dict) -> str:
    if kind == "inspect":
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        rows = result.get("rows") or result.get("rowCount") or result.get("row_count")
        latest = result.get("latest") if isinstance(result.get("latest"), dict) else {}
        parts = [
            f"rows {rows}" if rows is not None else "",
            f"latest {latest.get('value')}" if latest.get("value") else "",
        ]
        suffix = " · ".join(part for part in parts if part)
        return f"inspect dataset 실행함{': ' + suffix if suffix else ''}"
    if kind == "execute":
        result = data.get("result") if isinstance(data.get("result"), dict) else {}
        ok = result.get("ok")
        return f"run python 실행함: ok={ok}"
    if kind == "visual":
        return "compile visual 실행함"
    return f"{kind} 실행함"


def _targetFromToolPayload(data: dict) -> str:
    args = data.get("input") or data.get("arguments")
    if not isinstance(args, dict):
        args = {}
    for key in ("query", "path", "target", "source_ref", "sourceRef"):
        value = args.get(key) or data.get(key)
        if value:
            return str(value)[:160]
    code = args.get("code") or data.get("codePreview")
    if isinstance(code, str) and code.strip():
        return code.strip().splitlines()[0][:160]
    return ""


def _refIds(refs: list, ref: dict | None = None) -> list[str]:
    out = [str(item.get("id")) for item in refs if isinstance(item, dict) and item.get("id")]
    if ref and ref.get("id"):
        out.append(str(ref["id"]))
    return _dedupeStrings(out)


def _refsFromTrace(data: dict) -> list[str]:
    out: list[str] = []
    if data.get("refId"):
        out.append(str(data["refId"]))
    for key in ("refs", "derivedRefs"):
        values = data.get(key)
        if isinstance(values, list):
            out.extend(str(item.get("id")) for item in values if isinstance(item, dict) and item.get("id"))
    return _dedupeStrings(out)


def _errorFromPayload(data: dict) -> str:
    if data.get("error"):
        return str(data["error"])
    limits = data.get("limits")
    if isinstance(limits, list) and limits:
        return str(limits[0])
    return str(data.get("summary") or "도구 실행 실패")


def _issueCodes(issues: list) -> str:
    codes = [str(item.get("code") or item.get("message")) for item in issues if isinstance(item, dict)]
    return ", ".join(_readableFailure(code) for code in codes[:4]) if codes else "검산 실패"


def _responseStatusFromDone(data: dict) -> str:
    verification = data.get("verification") if isinstance(data.get("verification"), dict) else {}
    meta = data.get("responseMeta") if isinstance(data.get("responseMeta"), dict) else {}
    final_event = meta.get("finalEvent")
    if verification.get("ok") is True and final_event != "unable":
        return "ok"
    return "failed"


def _failureReasonFromDone(data: dict) -> str:
    verification = data.get("verification") if isinstance(data.get("verification"), dict) else {}
    issues = verification.get("issues") if isinstance(verification.get("issues"), list) else []
    if issues:
        return _issueCodes(issues)
    limits = data.get("limits") if isinstance(data.get("limits"), list) else []
    return _readableFailure(str(limits[0])) if limits else "최종 답변 생성 실패"


async def _syncGenToAsync(genFn, *args, **kwargs):
    """동기 제너레이터 → async 큐 브릿지 (timeout · cancel 대응).

    요청 종료(정상·예외·소비자 break·asyncio cancel 모두) 시 Polars string cache 를
    해제하고 GC 를 촉발한다. `/api/ask` 요청마다 AI tool loop 가 만든
    Company 인스턴스·pivot DataFrame 이 쌓여 네이티브 힙이 비대화하는
    문제 방어 — `pl.disable_string_cache()` 는 100~200MB, `gc.collect()`
    는 Python 참조가 해제된 DataFrame 의 Rust 힙 회수를 촉발한다.
    BoundedCache 의 EMERGENCY 임계를 넘지 못한 중간 누적분을 요청 경계
    에서 정리하는 용도.

    안정성 튜닝:
      - queue maxsize : env `DARTLAB_STREAM_QUEUE_MAX` (기본 1024).
      - put timeout   : env `DARTLAB_STREAM_PUT_TIMEOUT` (기본 30초).
      - consumer cancel 시 `cancelled` Event 로 producer thread 조기 종료.
    """
    import queue as _queue_mod

    sync_queue: _queue_mod.Queue = _queue_mod.Queue(maxsize=_DEFAULT_QUEUE_MAX)
    cancelled = threading.Event()
    _SENTINEL = object()

    def _run():
        try:
            for item in genFn(*args, **kwargs):
                if cancelled.is_set():
                    break
                try:
                    sync_queue.put(item, timeout=_DEFAULT_PUT_TIMEOUT)
                except _queue_mod.Full:
                    log.warning(
                        "stream producer: queue put timeout (%.0fs) — slow consumer or disconnect",
                        _DEFAULT_PUT_TIMEOUT,
                    )
                    break
        except Exception as exc:  # noqa: BLE001
            try:
                sync_queue.put(exc, timeout=_DEFAULT_PUT_TIMEOUT)
            except _queue_mod.Full:
                pass
        finally:
            try:
                sync_queue.put(_SENTINEL, timeout=_DEFAULT_PUT_TIMEOUT)
            except _queue_mod.Full:
                pass

    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, _run)

    try:
        while True:
            item = await asyncio.to_thread(sync_queue.get)
            if item is _SENTINEL:
                break
            if isinstance(item, Exception):
                raise item
            yield item

        await task
    except asyncio.CancelledError:
        # ASGI disconnect 또는 상위 task cancel — producer 조기 종료 신호
        cancelled.set()
        raise
    finally:
        # async generator aclose처럼 CancelledError를 거치지 않는 소비자 이탈도
        # producer가 다음 프레임에서 즉시 멈추도록 보장한다.
        cancelled.set()
        _releaseRuntimeHeap()


def _releaseRuntimeHeap() -> None:
    """요청 종료 시 Polars 네이티브 힙 회수 촉발. 실패해도 조용히 넘어간다."""
    try:
        import polars as pl

        pl.disable_string_cache()
    except (ImportError, AttributeError):
        pass
    try:
        import gc

        gc.collect()
    except Exception:  # noqa: BLE001
        pass
