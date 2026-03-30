"""analysis dict -> JSON 변환 (DataFrame/NaN/None 안전 직렬화)."""

from __future__ import annotations

import json
import math
from typing import Any

import polars as pl


def serializeValue(value: Any) -> Any:
    """단일 값을 JSON-safe로 변환한다."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, (int, str, bool)):
        return value
    if isinstance(value, pl.DataFrame):
        return _serializeDataFrame(value)
    if isinstance(value, pl.Series):
        return value.to_list()
    if isinstance(value, dict):
        return {str(k): serializeValue(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializeValue(v) for v in value]
    # dataclass / namedtuple
    if hasattr(value, "__dict__"):
        return {str(k): serializeValue(v) for k, v in value.__dict__.items()}
    return str(value)


def _serializeDataFrame(df: pl.DataFrame) -> list[dict[str, Any]]:
    """Polars DataFrame -> list of dicts."""
    rows = df.to_dicts()
    return [{k: serializeValue(v) for k, v in row.items()} for row in rows]


def toJsonStr(value: Any) -> str:
    """값을 JSON 문자열로 직렬화한다."""
    safe = serializeValue(value)
    return json.dumps(safe, ensure_ascii=False, default=str)


def serializeCalcResult(blockKey: str, result: Any) -> dict[str, Any]:
    """단일 calc 결과를 parquet row용 dict로 변환한다.

    Returns:
        {"blockKey": str, "status": "ok"|"none"|"error", "resultJson": str}
    """
    if result is None:
        return {
            "blockKey": blockKey,
            "status": "none",
            "resultJson": "null",
        }
    try:
        jsonStr = toJsonStr(result)
        return {
            "blockKey": blockKey,
            "status": "ok",
            "resultJson": jsonStr,
        }
    except (TypeError, ValueError, OverflowError) as e:
        return {
            "blockKey": blockKey,
            "status": "error",
            "resultJson": json.dumps({"error": str(e)}, ensure_ascii=False),
        }
