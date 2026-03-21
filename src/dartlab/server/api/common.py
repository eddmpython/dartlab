from __future__ import annotations

import hashlib
import re as _re
from typing import Any

import msgpack
import orjson
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


def sanitize_error(exc: BaseException) -> str:
	return _PATH_PATTERN.sub("<path>", str(exc))


def normalize_provider_name(provider: str | None) -> str | None:
	return normalize_provider(provider)


def serialize_payload(payload: Any, *, max_rows: int = 200) -> dict[str, Any]:
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
	raw = orjson.dumps(data, option=orjson.OPT_SORT_KEYS)
	return f'"{hashlib.md5(raw, usedforsecurity=False).hexdigest()[:16]}"'


def etag_response(
	request: Request,
	response: Response,
	data: dict[str, Any],
	*,
	max_age: int = 300,
	swr: int = 1800,
) -> dict[str, Any] | Response:
	etag = compute_etag(data)
	cache_control = f"private, max-age={max_age}, stale-while-revalidate={swr}"

	if_none_match = request.headers.get("if-none-match")
	if if_none_match == etag:
		return Response(status_code=304, headers={"ETag": etag, "Cache-Control": cache_control})

	response.headers["ETag"] = etag
	response.headers["Cache-Control"] = cache_control

	accept = request.headers.get("accept", "")
	if "application/msgpack" in accept:
		packed = msgpack.packb(data, use_bin_type=True)
		return Response(
			content=packed,
			media_type="application/msgpack",
			headers={"ETag": etag, "Cache-Control": cache_control},
		)

	return data
