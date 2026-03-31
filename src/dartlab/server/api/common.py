from __future__ import annotations

import hashlib
import json
import re as _re
from typing import Any

from fastapi import Request, Response

from dartlab.core.ai import normalize_provider

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


def sanitize_error(exc: BaseException) -> str:
    """에러 메시지에서 파일 경로와 인증 정보를 마스킹한다."""
    msg = _PATH_PATTERN.sub("<path>", str(exc))
    msg = _CREDENTIAL_PATTERN.sub(r"\1=***", msg)
    return msg


def guideDetail(exc: BaseException, *, feature: str | None = None) -> str:
    """sanitize_error + guide 안내 포함. Server API 에러 응답 표준."""
    detail = sanitize_error(exc)
    try:
        from dartlab.guide.integration import inferFeature

        resolvedFeature = feature or inferFeature(exc)  # type: ignore[arg-type]
        from dartlab.guide import guide

        guideMsg = guide.handleError(exc, feature=resolvedFeature)  # type: ignore[arg-type]
        if guideMsg and guideMsg != f"오류: {exc}":
            detail = f"{detail}\n\n{guideMsg}"
    except ImportError:
        pass
    return detail


def normalize_provider_name(provider: str | None) -> str | None:
    """Provider 이름을 정규화한다."""
    return normalize_provider(provider)


def serialize_payload(payload: Any, *, max_rows: int = 200) -> dict[str, Any]:
    """DataFrame/dict/str 등 다양한 페이로드를 JSON 직렬화 가능한 dict로 변환한다."""
    import polars as pl

    if payload is None:
        return {"type": "none", "data": None}

    if isinstance(payload, pl.DataFrame):
        preview = payload.head(max_rows)
        rows = preview.to_dicts()
        for row in rows:
            for key, value in row.items():
                if value is not None and not isinstance(value, (str, int, float, bool)):
                    row[key] = str(value)
        return {
            "type": "table",
            "columns": preview.columns,
            "rows": rows,
            "totalRows": payload.height,
            "truncated": payload.height > max_rows,
        }

    if isinstance(payload, dict):
        return {"type": "dict", "data": payload}

    if isinstance(payload, str):
        return {"type": "text", "data": payload}

    return {"type": "unknown", "data": str(payload)}


def compute_etag(data: Any) -> str:
    """데이터의 MD5 기반 ETag 해시를 계산한다."""
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False).encode()
    return f'"{hashlib.md5(raw, usedforsecurity=False).hexdigest()[:16]}"'


def etag_response(
    request: Request,
    response: Response,
    data: dict[str, Any],
    *,
    max_age: int = 300,
    swr: int = 1800,
) -> dict[str, Any] | Response:
    """ETag/Cache-Control 헤더를 설정하고 304 응답을 처리한다."""
    etag = compute_etag(data)
    cache_control = f"private, max-age={max_age}, stale-while-revalidate={swr}"

    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        return Response(status_code=304, headers={"ETag": etag, "Cache-Control": cache_control})

    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = cache_control

    return data
