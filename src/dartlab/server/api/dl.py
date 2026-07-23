"""Master API dispatch — dartlab capability registry 의 HTTP face.

dartlab.ai.tools.engineCall 의 dispatch 패턴을 참고하되, **JSON-safe 직렬화 강행**.
dashboard 가 사용할 master entry 는 dataclass / dict / list / DataFrame / Series 모두
구조를 보존해야 한다.

capability 화이트리스트 + private 차단은 capability registry (loadCapabilities) 와
공유 — engineCall 과 같은 ACL.

엔드포인트:
    POST /api/dl/call          — capability 호출
    GET  /api/dl/capabilities  — 전체 catalogue

Sig:
    POST /api/dl/call {apiRef, target?, args?, kwargs?}

Args:
    apiRef: str — "Company.panel" / "Company.analysis" / "macro.rates" 등
    target: str | None — stockCode 등 1차 식별자
    args: list — positional args
    kwargs: dict — keyword args (axis / topic / period / ...)

Returns:
    {ok, apiRef, target, data}
    data 는 JSON-safe — DataFrame 은 {_type, rowCount, columns, rows} 로 unwrap,
    dict/list 는 재귀 변환, datetime 은 isoformat, NaN 은 null.

Example:
    POST /api/dl/call
    {"apiRef": "Company.analysis", "target": "035720", "kwargs": {"axis": "수익성"}}

Raises:
    HTTPException(400) — apiRef 없음 / private API / registry 부재 / target 없음
    HTTPException(500) — capability 실행 내부 오류
"""

from __future__ import annotations

import math
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from typing import Any

import polars as pl
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import dartlab
from dartlab.reference.capability import loadCapabilities

CAPABILITIES = loadCapabilities()

router = APIRouter(prefix="/api/dl", tags=["dl"])

_JSON_PREVIEW_ROWS = 200
_JSON_MAX_DEPTH = 50


class DlCallRequest(BaseModel):
    """Master dispatch payload — apiRef 기반 capability 호출."""

    apiRef: str = Field(..., description="public capability reference (e.g. 'Company.panel')")
    target: str | None = Field(None, description="primary identifier (e.g. stockCode '035720')")
    args: list[Any] = Field(default_factory=list)
    kwargs: dict[str, Any] = Field(default_factory=dict)


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


# Company 인스턴스 LRU 캐시는 viz.display.finance._cache 로 위임 — rich / story /
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
            # submodule lazy import — dartlab.viz.dashboard.financial 등
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
        # viz.dashboard.* / viz.rich.* — 첫 positional 은 target (stockCode)
        if target and any(apiRef.startswith(pref) for pref in _VIZ_DASHBOARD_PREFIXES):
            return obj(target, *args, **kwargs)
        return obj(*args, **kwargs)
    return obj


# ── JSON-safe 직렬화 ──────────────────────────────────────────────────


def _toJsonSafe(obj: Any, _depth: int = 0) -> Any:
    """recursively 변환 — DataFrame / dict / list / numpy / datetime → JSON.

    DataFrame과 Series는 실제 크기와 bounded preview를 함께 반환한다. 이 preview 표시는
    DataResult의 query-level ``truncated``와 ``continuation``을 변경하지 않는다.
    NaN / inf 는 null (JSON 호환). 깊이 제한 50.
    """
    if _depth > _JSON_MAX_DEPTH:
        return {"_type": type(obj).__name__, "previewTruncated": True, "reason": "maxDepth"}

    if obj is None or isinstance(obj, (str, bool, int)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, pl.DataFrame):
        preview = obj.head(_JSON_PREVIEW_ROWS)
        return {
            "_type": "DataFrame",
            "rowCount": obj.height,
            "previewRowCount": preview.height,
            "columns": list(obj.columns),
            "schema": [
                {"name": name, "dtype": str(dtype)} for name, dtype in zip(obj.columns, obj.dtypes, strict=True)
            ],
            "rows": [_toJsonSafe(row, _depth + 1) for row in preview.to_dicts()],
            "previewTruncated": obj.height > preview.height,
        }
    if isinstance(obj, pl.Series):
        preview = obj.head(_JSON_PREVIEW_ROWS)
        return {
            "_type": "Series",
            "name": obj.name,
            "dtype": str(obj.dtype),
            "length": obj.len(),
            "previewLength": preview.len(),
            "values": [_toJsonSafe(item, _depth + 1) for item in preview.to_list()],
            "previewTruncated": obj.len() > preview.len(),
        }
    if is_dataclass(obj) and not isinstance(obj, type):
        return {field.name: _toJsonSafe(getattr(obj, field.name), _depth + 1) for field in fields(obj)}
    if isinstance(obj, dict):
        return {str(k): _toJsonSafe(v, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        items = sorted(obj, key=str) if isinstance(obj, (set, frozenset)) else obj
        return [_toJsonSafe(v, _depth + 1) for v in items]
    # numpy 타입 / 기타 — fallback to str
    try:
        # numpy scalars 등
        candidate: Any = obj
        itemFn = getattr(candidate, "item", None)
        if callable(itemFn):
            return _toJsonSafe(itemFn(), _depth + 1)
    except Exception:
        pass
    return str(obj)


# ── HTTP 엔드포인트 ──────────────────────────────────────────────────


@router.post("/call")
async def apiDlCall(req: DlCallRequest) -> dict[str, Any]:
    """Capability dispatch — JSON-safe 직렬화 강행."""
    allowed, errCode = _validateApiRef(req.apiRef)
    if not allowed:
        raise HTTPException(
            status_code=400,
            detail={"error": errCode, "message": f"capability 거부: {req.apiRef} ({errCode})"},
        )

    try:
        raw = _dispatch(req.apiRef, req.target, req.args, req.kwargs)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_request", "message": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "internal", "message": str(e)},
        ) from e

    return {
        "ok": True,
        "apiRef": req.apiRef,
        "target": req.target,
        "data": _toJsonSafe(raw),
    }


@router.get("/capabilities")
async def apiDlCapabilities() -> dict[str, Any]:
    """Capability catalogue — registry 의 모든 public capability 명단."""
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
