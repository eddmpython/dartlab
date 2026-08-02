from __future__ import annotations

import hashlib
import json
import math
import re as _re
from dataclasses import dataclass
from datetime import date, datetime
from itertools import islice
from typing import Any

from fastapi import Request, Response

HANDLED_API_ERRORS = (
    AttributeError,
    FileNotFoundError,
    ImportError,
    KeyError,
    OSError,
    PermissionError,
    RuntimeError,
    TimeoutError,
    TypeError,
    ValueError,
)

_PATH_PATTERN = _re.compile(
    r"(?:[A-Za-z]:\\|/(?:home|Users|tmp|var|usr|etc|root)/)[\w\\/.~\- ]+",
)
_CREDENTIAL_PATTERN = _re.compile(
    r"(api[_-]?key|token|secret|password|authorization|bearer)[\s:=]+\S+",
    _re.IGNORECASE,
)

_SERIALIZE_ITEM_CAP = 500
_SERIALIZE_DEPTH_CAP = 16
_SERIALIZE_NODE_CAP = 10_000
_SERIALIZE_STRING_BYTES = 32_768
_SERIALIZE_PAYLOAD_BYTES = 1_048_576


@dataclass
class _SerializeState:
    nodes: int = 0
    blocked: bool = False
    reasons: set[str] | None = None
    activeIds: set[int] | None = None

    def __post_init__(self) -> None:
        self.reasons = set()
        self.activeIds = set()

    def mark(self, reason: str, *, blocked: bool = False) -> None:
        """응답 제한 사유와 차단 여부를 누적한다."""
        assert self.reasons is not None
        self.reasons.add(reason)
        self.blocked = self.blocked or blocked


def _safeString(value: str, state: _SerializeState) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= _SERIALIZE_STRING_BYTES:
        return value
    state.mark("maxStringBytes")
    return encoded[:_SERIALIZE_STRING_BYTES].decode("utf-8", errors="ignore")


def _budgetValue(value: Any, state: _SerializeState, depth: int = 0) -> Any:  # noqa: C901, PLR0911
    state.nodes += 1
    if state.nodes > _SERIALIZE_NODE_CAP:
        state.mark("maxNodes")
        return {"status": "partial", "reason": "maxNodes"}
    if depth > _SERIALIZE_DEPTH_CAP:
        state.mark("maxDepth")
        return {"status": "partial", "reason": "maxDepth"}
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, str):
        return _safeString(value, state)
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    activeIds = state.activeIds
    assert activeIds is not None
    objectId = id(value)
    if objectId in activeIds:
        state.mark("cyclicPayload", blocked=True)
        return {"status": "blocked", "reason": "cyclicPayload"}
    activeIds.add(objectId)
    try:
        if isinstance(value, dict):
            entries = list(islice(value.items(), _SERIALIZE_ITEM_CAP + 1))
            result = {
                _safeString(str(key), state): _budgetValue(item, state, depth + 1)
                for key, item in entries[:_SERIALIZE_ITEM_CAP]
            }
            if len(entries) > _SERIALIZE_ITEM_CAP:
                state.mark("maxItems")
                result["_dartlabTruncated"] = {"status": "partial", "reason": "maxItems"}
            return result
        if isinstance(value, (list, tuple, set, frozenset)):
            items = list(islice(value, _SERIALIZE_ITEM_CAP + 1))
            if isinstance(value, (set, frozenset)):
                items.sort(key=str)
            result = [_budgetValue(item, state, depth + 1) for item in items[:_SERIALIZE_ITEM_CAP]]
            if len(items) > _SERIALIZE_ITEM_CAP:
                state.mark("maxItems")
                result.append({"status": "partial", "reason": "maxItems"})
            return result
        itemFn = getattr(value, "item", None)
        if callable(itemFn):
            return _budgetValue(itemFn(), state, depth + 1)
        return _safeString(str(value), state)
    finally:
        activeIds.remove(objectId)


def _serializationMeta(state: _SerializeState) -> dict[str, Any]:
    reasons = sorted(state.reasons or ())
    return {
        "status": "blocked" if state.blocked else "partial" if reasons else "complete",
        "truncated": bool(reasons),
        "reasons": reasons,
        "nodes": state.nodes,
        "nodeLimit": _SERIALIZE_NODE_CAP,
        "byteLimit": _SERIALIZE_PAYLOAD_BYTES,
    }


def _finalizePayloadBytes(result: dict[str, Any], meta: dict[str, Any]) -> int:
    """metadata 자체를 포함한 응답의 실제 JSON byte 크기를 계산한다."""
    meta["bytes"] = 0
    for _ in range(8):
        byteCount = len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        if meta["bytes"] == byteCount:
            return byteCount
        meta["bytes"] = byteCount
    return len(json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))


def _enforceResponseBytes(result: dict[str, Any], state: _SerializeState) -> dict[str, Any]:
    meta = _serializationMeta(state)
    result["serialization"] = meta
    byteCount = _finalizePayloadBytes(result, meta)
    if byteCount <= _SERIALIZE_PAYLOAD_BYTES:
        return result
    return {
        "type": "blocked",
        "status": "blocked",
        "data": None,
        "error": {"code": "response_too_large", "message": "응답 직렬화 예산을 초과했습니다."},
        "serialization": {
            "status": "blocked",
            "truncated": True,
            "reasons": ["maxPayloadBytes"],
            "bytes": byteCount,
            "byteLimit": _SERIALIZE_PAYLOAD_BYTES,
            "nodes": state.nodes,
            "nodeLimit": _SERIALIZE_NODE_CAP,
        },
    }


def sanitizeError(exc: BaseException) -> str:
    """에러 메시지에서 파일 경로와 인증 정보를 마스킹한다."""
    msg = _PATH_PATTERN.sub("<path>", str(exc))
    msg = _CREDENTIAL_PATTERN.sub(r"\1=***", msg)
    return msg


def guideDetail(exc: BaseException, *, feature: str | None = None) -> str:
    """sanitize_error + 친절 안내 포함. Server API 에러 응답 표준."""
    detail = sanitizeError(exc)
    try:
        from dartlab.core.messagingErrors import handleError, inferFeature

        resolvedFeature = feature or inferFeature(exc)  # type: ignore[arg-type]
        guideMsg = handleError(exc, feature=resolvedFeature)  # type: ignore[arg-type]
        if guideMsg and guideMsg != f"오류: {exc}":
            detail = f"{detail}\n\n{guideMsg}"
    except ImportError:
        pass
    return detail


def normalizeProviderName(provider: str | None) -> str | None:
    """호환 provider 입력 중 설치형 runtime ID만 통과시킨다.

    direct-model provider 이름은 더 이상 서버 실행 설정이 아니므로 None으로
    정규화한다. 이 함수는 옛 company summary query 호환에만 남아 있다.
    """
    lowered = str(provider or "").strip().lower()
    return lowered if lowered in {"codex", "claude", "cline"} else None


def serializePayload(payload: Any, *, maxRows: int = 200) -> dict[str, Any]:
    """DataFrame/dict/str 등 다양한 페이로드를 JSON 직렬화 가능한 dict로 변환한다."""
    import polars as pl

    state = _SerializeState()
    if payload is None:
        return _enforceResponseBytes({"type": "none", "data": None}, state)

    if isinstance(payload, pl.DataFrame):
        rowLimit = max(1, min(maxRows, _SERIALIZE_ITEM_CAP))
        preview = payload.head(rowLimit)
        if payload.height > rowLimit:
            state.mark("maxRows")
        rows = _budgetValue(preview.to_dicts(), state)
        return _enforceResponseBytes(
            {
                "type": "table",
                "columns": [_safeString(str(column), state) for column in preview.columns[:_SERIALIZE_ITEM_CAP]],
                "rows": rows,
                "totalRows": payload.height,
                "truncated": payload.height > rowLimit,
            },
            state,
        )

    if isinstance(payload, dict):
        return _enforceResponseBytes({"type": "dict", "data": _budgetValue(payload, state)}, state)

    if isinstance(payload, str):
        return _enforceResponseBytes({"type": "text", "data": _safeString(payload, state)}, state)

    return _enforceResponseBytes({"type": "unknown", "data": _safeString(str(payload), state)}, state)


def computeEtag(data: Any) -> str:
    """데이터의 MD5 기반 ETag 해시를 계산한다."""
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return f'"{hashlib.md5(raw, usedforsecurity=False).hexdigest()[:16]}"'


def etagResponse(
    request: Request,
    response: Response,
    data: dict[str, Any],
    *,
    maxAge: int = 300,
    swr: int = 1800,
) -> dict[str, Any] | Response:
    """ETag/Cache-Control 헤더를 설정하고 304 응답을 처리한다."""
    etag = computeEtag(data)
    cache_control = f"private, max-age={maxAge}, stale-while-revalidate={swr}"

    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": cache_control})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = cache_control

    return data
