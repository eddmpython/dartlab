"""Master API dispatch: dartlab capability registry 의 HTTP face.

dartlab.ai.tools.engineCall 의 dispatch 패턴을 참고하되, **JSON-safe 직렬화 강행**.
dashboard 가 사용할 master entry 는 dataclass / dict / list / DataFrame / Series 모두
구조를 보존해야 한다.

capability 화이트리스트 + private 차단은 capability registry (loadCapabilities) 와
공유한다. engineCall 과 같은 ACL이다.

엔드포인트:
    POST /api/dl/call: capability 호출
    GET  /api/dl/capabilities: 전체 catalogue

Sig:
    POST /api/dl/call {apiRef, target?, args?, kwargs?}

Args:
    apiRef: str. "Company.panel" / "Company.analysis" / "macro.rates" 등
    target: str | None. stockCode 등 1차 식별자
    args: list. positional args
    kwargs: dict. keyword args (axis / topic / period / ...)

Returns:
    {ok, apiRef, target, data}
    data 는 JSON-safe. DataFrame 은 {_type, rowCount, columns, rows} 로 unwrap,
    dict/list 는 재귀 변환, datetime 은 isoformat, NaN 은 null.

Example:
    POST /api/dl/call
    {"apiRef": "Company.analysis", "target": "035720", "kwargs": {"axis": "수익성"}}

Raises:
    HTTPException(400): apiRef 없음 / private API / registry 부재 / target 없음
    HTTPException(500): capability 실행 내부 오류
"""

from __future__ import annotations

import asyncio
import json
import math
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from itertools import islice
from typing import Any

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import dartlab
from dartlab.reference.capability import loadCapabilities

from .common import sanitizeError

CAPABILITIES = loadCapabilities()

router = APIRouter(prefix="/api/dl", tags=["dl"])

_JSON_PREVIEW_ROWS = 200
_JSON_MAX_DEPTH = 16
_JSON_MAX_ITEMS = 500
_JSON_MAX_NODES = 10_000
_JSON_MAX_STRING_BYTES = 32_768
_JSON_MAX_PAYLOAD_BYTES = 1_048_576


class DlCallRequest(BaseModel):
    """Master dispatch payload: apiRef 기반 capability 호출."""

    apiRef: str = Field(..., min_length=1, max_length=256, description="public capability reference")
    target: str | None = Field(None, max_length=128, description="primary identifier")
    args: list[Any] = Field(default_factory=list, max_length=32)
    kwargs: dict[str, Any] = Field(default_factory=dict, max_length=64)


# ── Capability 화이트리스트 (engineCall 과 동일 ACL) ───────────────────


_VIZ_DASHBOARD_PREFIXES = ("viz.dashboard.", "viz.rich.")


def _validateApiRef(apiRef: str) -> tuple[bool, str | None]:
    """capability registry 와 private prefix 로 ACL.

    Returns (allowed, error_code).
    """
    if not apiRef:
        return False, "missing_api_ref"
    if apiRef.startswith("_") or "._" in apiRef or "internal" in apiRef.lower():
        return False, "private_api_blocked"
    if apiRef in CAPABILITIES:
        return True, None
    if any(apiRef.startswith(p) for p in _VIZ_DASHBOARD_PREFIXES):
        return True, None
    return False, "unknown_api_ref"


# ── Dispatch (direct call, JSON-safe 직렬화) ──────────────────────────


# Company 인스턴스 LRU 캐시는 viz.display.finance._cache 로 위임한다. rich / story /
# dashboard / mcp 모두 공유. 매 요청 새 인스턴스 생성 시 collect 결과를 잃어
# cold start 1.8 초 + Polars heap 200~500MB 누적 → BoundedCache 5GB emergency
# flush 무한 루프. 같은 target 은 single instance 재사용 (최대 8 종목).
from dartlab.viz.display.finance._cache import getCompany as _getCompany  # noqa: E402,F401


def _dispatch(apiRef: str, target: str | None, args: list[Any], kwargs: dict[str, Any]) -> Any:
    """capability 를 직접 호출. raw Python 결과 반환 (직렬화 X)."""
    if apiRef.startswith("Company."):
        method = apiRef.split(".", 1)[1]
        if not target:
            raise ValueError("Company API 는 target (stockCode) 가 필요합니다.")
        company = _getCompany(target)
        if not hasattr(company, method):
            raise ValueError(f"공개 Company API 를 찾지 못했습니다: Company.{method}")
        func = getattr(company, method)
        if not callable(func):
            return func  # property / attribute
        return func(*args, **kwargs)

    # dartlab top-level 또는 nested attr (analysis / quant / macro.rates 등)
    parts = apiRef.split(".")
    if parts[0] == "dartlab":
        parts = parts[1:]
    obj: Any = dartlab
    walked: list[str] = []
    for p in parts:
        if not hasattr(obj, p):
            # submodule lazy import. dartlab.viz.dashboard.financial 등
            import importlib

            modPath = ".".join(["dartlab", *walked, p]) if walked else f"dartlab.{p}"
            try:
                obj = importlib.import_module(modPath)
                walked.append(p)
                continue
            except ImportError:
                pass
            raise ValueError(f"공개 API 를 찾지 못했습니다: {apiRef}")
        obj = getattr(obj, p)
        walked.append(p)
    if callable(obj):
        # viz.dashboard.* / viz.rich.*. 첫 positional 은 target (stockCode)
        if target and any(apiRef.startswith(pref) for pref in _VIZ_DASHBOARD_PREFIXES):
            return obj(target, *args, **kwargs)
        return obj(*args, **kwargs)
    return obj


# ── JSON-safe 직렬화 ──────────────────────────────────────────────────


@dataclass
class _JsonBudgetState:
    nodes: int = 0
    truncated: bool = False
    reasons: set[str] | None = None
    activeIds: set[int] | None = None

    def __post_init__(self) -> None:
        self.reasons = set()
        self.activeIds = set()

    def mark(self, reason: str) -> None:
        """직렬화 잘림 사유를 누적한다."""
        self.truncated = True
        assert self.reasons is not None
        self.reasons.add(reason)


class _ResponseSerializationError(RuntimeError):
    pass


def _safeString(value: str, state: _JsonBudgetState) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= _JSON_MAX_STRING_BYTES:
        return value
    state.mark("maxStringBytes")
    return encoded[:_JSON_MAX_STRING_BYTES].decode("utf-8", errors="ignore")


def _dataFrameJson(obj: pl.DataFrame, depth: int, state: _JsonBudgetState) -> dict[str, Any]:
    preview = obj.head(_JSON_PREVIEW_ROWS)
    if obj.height > preview.height:
        state.mark("maxRows")
    return {
        "_type": "DataFrame",
        "rowCount": obj.height,
        "previewRowCount": preview.height,
        "columns": [_safeString(str(name), state) for name in obj.columns[:_JSON_MAX_ITEMS]],
        "schema": [
            {"name": _safeString(str(name), state), "dtype": str(dtype)}
            for name, dtype in islice(zip(obj.columns, obj.dtypes, strict=True), _JSON_MAX_ITEMS)
        ],
        "rows": [_toJsonSafe(row, depth + 1, state) for row in preview.to_dicts()],
        "previewTruncated": obj.height > preview.height,
    }


def _seriesJson(obj: pl.Series, depth: int, state: _JsonBudgetState) -> dict[str, Any]:
    preview = obj.head(_JSON_PREVIEW_ROWS)
    if obj.len() > preview.len():
        state.mark("maxRows")
    return {
        "_type": "Series",
        "name": _safeString(str(obj.name), state),
        "dtype": str(obj.dtype),
        "length": obj.len(),
        "previewLength": preview.len(),
        "values": [_toJsonSafe(item, depth + 1, state) for item in preview.to_list()],
        "previewTruncated": obj.len() > preview.len(),
    }


def _mappingJson(obj: dict[Any, Any], depth: int, state: _JsonBudgetState) -> dict[str, Any]:
    values = {
        _safeString(str(key), state): _toJsonSafe(value, depth + 1, state)
        for key, value in islice(obj.items(), _JSON_MAX_ITEMS)
    }
    if len(obj) > _JSON_MAX_ITEMS:
        state.mark("maxItems")
        values["_dartlabTruncated"] = {"status": "partial", "reason": "maxItems"}
    return values


def _sequenceJson(
    obj: list[Any] | tuple[Any, ...] | set[Any] | frozenset[Any], depth: int, state: _JsonBudgetState
) -> list[Any]:
    source = list(islice(obj, _JSON_MAX_ITEMS + 1))
    if isinstance(obj, set | frozenset):
        source.sort(key=str)
    values = [_toJsonSafe(value, depth + 1, state) for value in source[:_JSON_MAX_ITEMS]]
    if len(source) > _JSON_MAX_ITEMS:
        state.mark("maxItems")
        values.append({"status": "partial", "reason": "maxItems"})
    return values


def _toJsonSafe(obj: Any, _depth: int = 0, _state: _JsonBudgetState | None = None) -> Any:  # noqa: C901, PLR0911
    """재귀 변환: DataFrame / dict / list / numpy / datetime을 JSON으로 만든다.

    DataFrame과 Series는 실제 크기와 bounded preview를 함께 반환한다. 이 preview 표시는
    DataResult의 query-level ``truncated``와 ``continuation``을 변경하지 않는다.
    NaN / inf 는 null로 바꾸고 컬렉션, 문자열, 깊이, 노드 예산을 함께 강제한다.
    """
    state = _state or _JsonBudgetState()
    state.nodes += 1
    if state.nodes > _JSON_MAX_NODES:
        state.mark("maxNodes")
        return {"status": "partial", "reason": "maxNodes"}
    if _depth > _JSON_MAX_DEPTH:
        state.mark("maxDepth")
        return {"_type": type(obj).__name__, "status": "partial", "reason": "maxDepth"}

    if obj is None or isinstance(obj, (bool, int)):
        return obj
    if isinstance(obj, str):
        return _safeString(obj, state)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()

    activeIds = state.activeIds
    assert activeIds is not None
    objectId = id(obj)
    if objectId in activeIds:
        raise _ResponseSerializationError("cyclic_payload")
    activeIds.add(objectId)
    try:
        if isinstance(obj, pl.DataFrame):
            return _dataFrameJson(obj, _depth, state)
        if isinstance(obj, pl.Series):
            return _seriesJson(obj, _depth, state)
        if is_dataclass(obj) and not isinstance(obj, type):
            return {field.name: _toJsonSafe(getattr(obj, field.name), _depth + 1, state) for field in fields(obj)}
        if isinstance(obj, dict):
            return _mappingJson(obj, _depth, state)
        if isinstance(obj, (list, tuple, set, frozenset)):
            return _sequenceJson(obj, _depth, state)
        try:
            candidate: Any = obj
            itemFn = getattr(candidate, "item", None)
            if callable(itemFn):
                return _toJsonSafe(itemFn(), _depth + 1, state)
        except (TypeError, ValueError):
            pass
        return _safeString(str(obj), state)
    finally:
        activeIds.remove(objectId)


def _serializeApiData(raw: Any) -> tuple[Any, dict[str, Any]]:
    state = _JsonBudgetState()
    data = _toJsonSafe(raw, _state=state)
    byteCount = len(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
    if byteCount > _JSON_MAX_PAYLOAD_BYTES:
        raise _ResponseSerializationError("response_too_large")
    return data, {
        "status": "partial" if state.truncated else "complete",
        "truncated": state.truncated,
        "reasons": sorted(state.reasons or ()),
        "bytes": byteCount,
        "byteLimit": _JSON_MAX_PAYLOAD_BYTES,
        "nodes": state.nodes,
        "nodeLimit": _JSON_MAX_NODES,
    }


def _finalizeResponseBytes(response: dict[str, Any], serialization: dict[str, Any]) -> int:
    """serialization metadata까지 포함한 전체 응답의 실제 JSON 크기를 계산한다."""
    serialization["bytes"] = 0
    for _ in range(8):
        byteCount = len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if serialization["bytes"] == byteCount:
            return byteCount
        serialization["bytes"] = byteCount
    return len(json.dumps(response, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


# ── HTTP 엔드포인트 ──────────────────────────────────────────────────


@router.post("/call")
async def apiDlCall(req: DlCallRequest) -> dict[str, Any]:
    """Capability dispatch: JSON-safe 직렬화 강행."""
    allowed, errCode = _validateApiRef(req.apiRef)
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail={"error": errCode, "message": f"capability 거부: {req.apiRef} ({errCode})"},
        )

    try:
        raw = await asyncio.to_thread(_dispatch, req.apiRef, req.target, req.args, req.kwargs)
        data, serialization = await asyncio.to_thread(_serializeApiData, raw)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "status": "blocked", "message": sanitizeError(e)},
        ) from e
    except _ResponseSerializationError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "serialization_failed", "status": "blocked", "message": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "internal", "status": "blocked", "message": sanitizeError(e)},
        ) from e

    resultStatus = str(data.get("status") or "unknown") if isinstance(data, dict) else "unknown"
    if serialization["truncated"] and resultStatus not in {"blocked", "error", "failed", "rejected"}:
        resultStatus = "partial"
    response = {
        "ok": resultStatus not in {"blocked", "error", "failed", "rejected"},
        "status": resultStatus,
        "apiRef": req.apiRef,
        "target": req.target,
        "data": data,
        "serialization": serialization,
    }
    if _finalizeResponseBytes(response, serialization) > _JSON_MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "serialization_failed",
                "status": "blocked",
                "message": "response_too_large",
            },
        )
    return response


@router.get("/capabilities")
async def apiDlCapabilities() -> dict[str, Any]:
    """Capability catalogue: registry 의 모든 public capability 명단."""
    items = []
    for ref, meta in CAPABILITIES.items():
        items.append(
            {
                "apiRef": ref,
                "kind": meta.get("kind", "method") if isinstance(meta, dict) else "method",
                "summary": meta.get("summary", "") if isinstance(meta, dict) else "",
            }
        )
    return {"count": len(items), "items": items}
