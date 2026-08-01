"""브라우저 서빙용 async 데이터 라우터 (browser-as-server SSOT).

브라우저의 공개 HTTP 경계는 DartLab 계약 결과를 구조적으로 보존한다. CPython 서버에서는
동기 엔진 호출을 worker thread로 넘기고, thread가 없는 Pyodide에서는 같은 커널에서 직접
실행한다. 응답 직렬화는 행, 깊이, 항목, 문자열, 전체 byte 예산을 적용한다.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import sys
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from itertools import islice
from typing import Any, Callable, cast

_ROW_CAP = 500
_ITEM_CAP = 500
_STRING_BYTE_CAP = 32_768
_PAYLOAD_BYTE_CAP = 1_048_576
_NODE_CAP = 10_000
_DEPTH_CAP = 16
_REF_CAP = 256
_CODE_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,32}$")
_BLOCKED_STATUSES = {"blocked", "error", "failed", "rejected"}
_PARTIAL_STATUSES = {
    "partial",
    "missing",
    "unsupported",
    "empty",
    "unavailable",
    "retrospectiveOnly",
    "documented",
}


class BrowserInputError(ValueError):
    """브라우저 API 입력이 공개 계약의 크기나 문자 규칙을 위반했다."""


class BrowserPayloadError(RuntimeError):
    """공개 응답을 안전한 예산 안에서 직렬화할 수 없다."""


@dataclass
class _BudgetState:
    nodes: int = 0
    truncated: bool = False
    reasons: set[str] | None = None
    activeIds: set[int] | None = None

    def __post_init__(self) -> None:
        self.reasons = set()
        self.activeIds = set()

    def mark(self, reason: str) -> None:
        """브라우저 응답의 잘림 사유를 누적한다."""
        self.truncated = True
        assert self.reasons is not None
        self.reasons.add(reason)


def _threadOffloadAvailable() -> bool:
    return sys.platform not in {"emscripten", "wasi"}


async def _runSync(call: Callable[[], Any]) -> Any:
    """CPython에서는 동기 계산을 offload하고 Pyodide에서는 현재 커널에서 실행한다."""
    if _threadOffloadAvailable():
        return await asyncio.to_thread(call)
    return call()


def _boundedText(value: str, name: str, *, maxLength: int = 128) -> str:
    text = value.strip()
    if not text:
        raise BrowserInputError(f"{name}은 비어 있을 수 없습니다.")
    if len(text) > maxLength:
        raise BrowserInputError(f"{name}은 최대 {maxLength}자입니다.")
    if any(ord(char) < 32 for char in text):
        raise BrowserInputError(f"{name}에 제어 문자를 사용할 수 없습니다.")
    return text


def _boundedCode(code: str) -> str:
    text = code.strip()
    if not _CODE_PATTERN.fullmatch(text):
        raise BrowserInputError("code는 영문, 숫자, 점, 밑줄, 하이픈으로 된 1~32자 식별자여야 합니다.")
    return text


def _boundedFields(raw: str) -> list[str]:
    if len(raw.encode("utf-8")) > 4096:
        raise BrowserInputError("fields는 최대 4096바이트입니다.")
    names = [_boundedText(value, "field") for value in raw.split(",") if value.strip()]
    if not names:
        raise BrowserInputError("fields에 하나 이상의 이름이 필요합니다.")
    if len(names) > 64:
        raise BrowserInputError("fields는 최대 64개입니다.")
    return names


def _boundedString(value: str, state: _BudgetState) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= _STRING_BYTE_CAP:
        return value
    state.mark("maxStringBytes")
    return encoded[:_STRING_BYTE_CAP].decode("utf-8", errors="ignore")


def _frameJsonValue(obj: Any, state: _BudgetState, depth: int) -> dict[str, Any]:
    columns = obj.columns
    rowCount = int(obj.height or 0)
    preview = obj.head(_ROW_CAP) if rowCount > _ROW_CAP else obj
    rows = _jsonValue(preview.to_dicts(), state, depth + 1)
    if rowCount > _ROW_CAP:
        state.mark("maxRows")
    return {
        "columns": [_boundedString(str(column), state) for column in islice(columns, _ITEM_CAP)],
        "shape": list(getattr(obj, "shape", (len(rows), len(columns)))),
        "rows": rows,
        "totalRows": rowCount,
        "truncated": rowCount > _ROW_CAP,
    }


def _dataclassJsonValue(obj: Any, state: _BudgetState, depth: int) -> dict[str, Any]:
    objectFields = fields(obj)
    values = {field.name: _jsonValue(getattr(obj, field.name), state, depth + 1) for field in objectFields[:_ITEM_CAP]}
    if len(objectFields) > _ITEM_CAP:
        state.mark("maxItems")
        values["_dartlabTruncated"] = {"status": "partial", "reason": "maxItems"}
    return values


def _mappingJsonValue(obj: dict[Any, Any], state: _BudgetState, depth: int) -> dict[str, Any]:
    values = {}
    entries = list(islice(obj.items(), _ITEM_CAP + 1))
    for key, value in entries[:_ITEM_CAP]:
        safeKey = _boundedString(str(key), state)
        values[safeKey] = _jsonValue(value, state, depth + 1)
    if len(entries) > _ITEM_CAP:
        state.mark("maxItems")
        values["_dartlabTruncated"] = {"status": "partial", "reason": "maxItems"}
    return values


def _sequenceJsonValue(
    obj: list[Any] | tuple[Any, ...] | set[Any] | frozenset[Any], state: _BudgetState, depth: int
) -> list[Any]:
    source = list(islice(obj, _ITEM_CAP + 1))
    if isinstance(obj, set | frozenset):
        source.sort(key=str)
    values = [_jsonValue(value, state, depth + 1) for value in source[:_ITEM_CAP]]
    if len(source) > _ITEM_CAP:
        state.mark("maxItems")
        values.append({"status": "partial", "reason": "maxItems", "remaining": len(source) - _ITEM_CAP})
    return values


def _jsonValue(obj: Any, state: _BudgetState, depth: int = 0) -> Any:  # noqa: C901, PLR0911
    state.nodes += 1
    if state.nodes > _NODE_CAP:
        state.mark("maxNodes")
        return {"status": "partial", "reason": "maxNodes"}
    if depth > _DEPTH_CAP:
        state.mark("maxDepth")
        return {"status": "partial", "reason": "maxDepth", "type": type(obj).__name__}

    if obj is None or isinstance(obj, (bool, int)):
        return obj
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, str):
        return _boundedString(obj, state)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()

    activeIds = state.activeIds
    assert activeIds is not None
    objectId = id(obj)
    if objectId in activeIds:
        raise BrowserPayloadError("순환 참조가 있는 payload는 공개할 수 없습니다.")
    activeIds.add(objectId)
    try:
        toDicts = getattr(obj, "to_dicts", None)
        columns = getattr(obj, "columns", None)
        if callable(toDicts) and columns is not None:
            return _frameJsonValue(obj, state, depth)

        if is_dataclass(obj) and not isinstance(obj, type):
            return _dataclassJsonValue(obj, state, depth)

        if isinstance(obj, dict):
            return _mappingJsonValue(obj, state, depth)

        if isinstance(obj, (list, tuple, set, frozenset)):
            return _sequenceJsonValue(obj, state, depth)

        df = getattr(obj, "df", None)
        if df is not None and df is not obj:
            return _jsonValue(df, state, depth + 1)

        itemFn = getattr(obj, "item", None)
        if callable(itemFn):
            return _jsonValue(itemFn(), state, depth + 1)

        return {"type": type(obj).__name__, "repr": _boundedString(str(obj), state)}
    finally:
        activeIds.remove(objectId)


def _budgetedJson(obj: Any) -> tuple[Any, dict[str, Any]]:
    state = _BudgetState()
    data = _jsonValue(obj, state)
    byteCount = len(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if byteCount > _PAYLOAD_BYTE_CAP:
        raise BrowserPayloadError(f"응답 payload가 {_PAYLOAD_BYTE_CAP}바이트 예산을 초과했습니다.")
    return data, {
        "status": "partial" if state.truncated else "complete",
        "truncated": state.truncated,
        "reasons": sorted(state.reasons or ()),
        "bytes": byteCount,
        "byteLimit": _PAYLOAD_BYTE_CAP,
        "nodes": state.nodes,
        "nodeLimit": _NODE_CAP,
    }


def _finalizePayloadBytes(payload: Any, serialization: dict[str, Any]) -> None:
    """응답에 포함된 bytes 필드까지 반영한 실제 JSON 크기를 고정한다."""
    serialization["bytes"] = 0
    for _ in range(8):
        byteCount = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if serialization["bytes"] == byteCount:
            break
        serialization["bytes"] = byteCount
    finalBytes = len(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if finalBytes > _PAYLOAD_BYTE_CAP:
        raise BrowserPayloadError(f"응답 payload가 {_PAYLOAD_BYTE_CAP}바이트 예산을 초과했습니다.")


def _publicJson(obj: Any) -> Any:
    data, serialization = _budgetedJson(obj)
    if not serialization["truncated"]:
        return data
    if isinstance(data, dict) and "_dartlabSerialization" not in data:
        result = data | {"_dartlabSerialization": serialization}
    else:
        result = {"data": data, "_dartlabSerialization": serialization}
    _finalizePayloadBytes(result, serialization)
    return result


def _json(obj: Any) -> Any:
    """기존 내부 소비자를 위한 예산 적용 직렬화 호환 이름."""
    return _publicJson(obj)


def _collectNamedValues(obj: Any, names: set[str], *, cap: int = _REF_CAP) -> list[Any]:
    values: list[Any] = []
    stack = [(obj, 0)]
    scanned = 0
    while stack and len(values) < cap and scanned < _NODE_CAP:
        current, depth = stack.pop()
        scanned += 1
        if depth > _DEPTH_CAP:
            continue
        if isinstance(current, dict):
            entries = list(islice(current.items(), _ITEM_CAP))
            for key, value in reversed(entries):
                if key in names:
                    if isinstance(value, (list, tuple)):
                        values.extend(value[: cap - len(values)])
                    elif value is not None:
                        values.append(value)
                if isinstance(value, (dict, list, tuple)):
                    stack.append((value, depth + 1))
        elif isinstance(current, (list, tuple)):
            items = list(islice(current, _ITEM_CAP))
            stack.extend((value, depth + 1) for value in reversed(items))
    return values[:cap]


def _storyStatus(products: dict[str, Any], gaps: list[Any]) -> str:
    statuses = {
        str(product.get("status"))
        for product in products.values()
        if isinstance(product, dict) and product.get("status") is not None
    }
    gapStatuses = {str(gap.get("status") or "partial") for gap in gaps if isinstance(gap, dict)}
    combined = statuses | gapStatuses
    if combined & _BLOCKED_STATUSES:
        return "blocked"
    if gaps or combined & _PARTIAL_STATUSES:
        return "partial"
    if products and statuses and statuses <= {"usable", "ok", "admitted"}:
        return "usable"
    return "unknown"


def _storyEnvelope(result: Any, section: str) -> dict[str, Any]:
    from dartlab.story.lensProducts import publicLensBundle

    bundle = publicLensBundle(getattr(result, "_lensBundle", None)) or {}
    bundleProducts = bundle.get("products")
    products = cast(dict[str, Any], bundleProducts) if isinstance(bundleProducts, dict) else {}
    resultProducts = getattr(result, "lensProducts", None)
    if not products and isinstance(resultProducts, dict):
        products = cast(dict[str, Any], resultProducts)
    gaps = list(getattr(result, "lensGaps", None) or [])
    if isinstance(bundle.get("gaps"), list):
        gaps.extend(bundle["gaps"])

    report = {
        "stockCode": getattr(result, "stockCode", None),
        "corpName": getattr(result, "corpName", None),
        "reportType": getattr(result, "reportType", None),
        "template": getattr(result, "template", None),
        "templates": getattr(result, "templates", None),
        "summaryCard": getattr(result, "summaryCard", None),
        "sections": getattr(result, "sections", None),
        "circulationSummary": getattr(result, "circulationSummary", None),
        "lensGaps": gaps,
        "lensProducts": bundle or {"products": products, "gaps": gaps},
    }
    asOf = _collectNamedValues(report, {"asOf", "dataAsOf", "knowledgeAsOf", "knowledgeBoundary"})
    refs = _collectNamedValues(
        report,
        {"sourceRef", "sourceRefs", "tableRef", "valueRef", "dateRef", "executionRef", "lineageRefs"},
    )
    rawEnvelope = {
        "schemaVersion": "dartlab.browser.story.v1",
        "kind": "story",
        "status": _storyStatus(products, gaps),
        "section": section,
        "asOf": asOf,
        "refs": refs,
        "gaps": gaps,
        "report": report,
    }
    data, serialization = _budgetedJson(rawEnvelope)
    data["serialization"] = serialization
    _finalizePayloadBytes(data, serialization)
    return data


def _errorEnvelope(code: str, message: str, *, retryable: bool = False) -> dict[str, Any]:
    return {
        "schemaVersion": "dartlab.browser.error.v1",
        "kind": "error",
        "status": "blocked",
        "error": {"code": code, "message": message, "retryable": retryable},
    }


def buildBrowserApi():  # noqa: C901, PLR0915
    """브라우저 서빙 FastAPI 앱을 lazy import로 생성한다."""
    from fastapi import FastAPI, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    import dartlab

    app = FastAPI(title="dartlab browser", version=getattr(dartlab, "__version__", "0"))
    companyFactory = cast(Callable[[str], Any], getattr(dartlab, "Company"))
    scanEngine = cast(Callable[[str], Any], getattr(dartlab, "scan"))

    @app.exception_handler(RequestValidationError)
    async def requestValidationError(_: Request, exc: RequestValidationError):
        """요청 스키마 오류를 공개 오류 응답으로 변환한다."""
        details = [{"location": list(error.get("loc", ())), "type": error.get("type")} for error in exc.errors()]
        return JSONResponse(
            status_code=422,
            content=_errorEnvelope("invalid_request", "요청 형식이 올바르지 않습니다.") | {"details": details},
        )

    @app.exception_handler(BrowserInputError)
    async def browserInputError(_: Request, exc: BrowserInputError):
        """브라우저 입력 오류를 공개 오류 응답으로 변환한다."""
        return JSONResponse(status_code=400, content=_errorEnvelope("invalid_input", str(exc)))

    @app.exception_handler(FileNotFoundError)
    async def browserNotFound(_: Request, __: FileNotFoundError):
        """누락된 데이터를 찾을 수 없음 응답으로 변환한다."""
        return JSONResponse(status_code=404, content=_errorEnvelope("not_found", "요청한 데이터를 찾지 못했습니다."))

    @app.exception_handler(TimeoutError)
    async def browserTimeout(_: Request, __: TimeoutError):
        """실행 시간 초과를 재시도 가능한 공개 오류로 변환한다."""
        return JSONResponse(
            status_code=504,
            content=_errorEnvelope("upstream_timeout", "데이터 실행 시간이 초과되었습니다.", retryable=True),
        )

    @app.exception_handler(BrowserPayloadError)
    async def browserPayloadError(_: Request, exc: BrowserPayloadError):
        """직렬화 실패를 공개 오류 응답으로 변환한다."""
        return JSONResponse(status_code=500, content=_errorEnvelope("serialization_failed", str(exc)))

    @app.exception_handler(Exception)
    async def browserInternalError(_: Request, exc: Exception):
        """예상 가능한 내부 예외를 안정된 공개 오류 응답으로 변환한다."""
        if isinstance(exc, (ImportError, MemoryError, OSError, RuntimeError)):
            return JSONResponse(
                status_code=503,
                content=_errorEnvelope(
                    "runtime_unavailable", "브라우저 실행 환경에서 기능을 사용할 수 없습니다.", retryable=True
                ),
            )
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            return JSONResponse(
                status_code=400, content=_errorEnvelope("invalid_input", "요청 인자를 처리할 수 없습니다.")
            )
        return JSONResponse(status_code=500, content=_errorEnvelope("internal_error", "내부 실행 오류가 발생했습니다."))

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "version": getattr(dartlab, "__version__", "0")}

    @app.get("/company/{code}/panel/{topic}")
    async def panel(code: str, topic: str, freq: str | None = None, scope: str | None = None) -> dict:
        safeCode = _boundedCode(code)
        safeTopic = _boundedText(topic, "topic")
        kwargs = {}
        if freq:
            kwargs["freq"] = _boundedText(freq, "freq", maxLength=16)
        if scope:
            kwargs["scope"] = _boundedText(scope, "scope", maxLength=32)
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).panel(safeTopic, **kwargs)))

    @app.get("/company/{code}/select/{topic}")
    async def select(code: str, topic: str, fields: str, freq: str | None = None) -> dict:
        safeCode = _boundedCode(code)
        safeTopic = _boundedText(topic, "topic")
        names = _boundedFields(fields)
        kwargs = {"freq": _boundedText(freq, "freq", maxLength=16)} if freq else {}
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).select(safeTopic, names, **kwargs)))

    @app.get("/company/{code}/analysis/{engine}/{axis}")
    async def analysis(code: str, engine: str, axis: str) -> Any:
        safeCode = _boundedCode(code)
        safeEngine = _boundedText(engine, "engine", maxLength=64)
        safeAxis = _boundedText(axis, "axis")
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).analysis(safeEngine, safeAxis)))

    @app.get("/company/{code}/credit/{axis}")
    async def credit(code: str, axis: str) -> Any:
        safeCode = _boundedCode(code)
        safeAxis = _boundedText(axis, "axis")
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).credit(safeAxis)))

    @app.get("/company/{code}/story/{section}")
    async def story(code: str, section: str) -> Any:
        safeCode = _boundedCode(code)
        safeSection = _boundedText(section, "section")
        return await _runSync(lambda: _storyEnvelope(companyFactory(safeCode).story(safeSection), safeSection))

    @app.get("/company/{code}/industry")
    async def industry(code: str) -> Any:
        safeCode = _boundedCode(code)
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).industry()))

    @app.get("/company/{code}/lenses")
    async def lenses(code: str) -> Any:
        safeCode = _boundedCode(code)

        def _collect():
            from dartlab.story.lensProducts import collectLensProducts, publicLensBundle

            return _publicJson(publicLensBundle(collectLensProducts(companyFactory(safeCode))))

        return await _runSync(_collect)

    @app.get("/company/{code}/trace/{topic}")
    async def trace(code: str, topic: str) -> Any:
        safeCode = _boundedCode(code)
        safeTopic = _boundedText(topic, "topic")
        return await _runSync(lambda: _publicJson(companyFactory(safeCode).trace(safeTopic)))

    @app.get("/scan/{axis}")
    async def scan(axis: str) -> dict:
        safeAxis = _boundedText(axis, "axis")
        return await _runSync(lambda: _publicJson(scanEngine(safeAxis)))

    return app
