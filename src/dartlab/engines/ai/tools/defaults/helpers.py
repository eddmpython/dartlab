"""도구 카테고리 모듈에서 공유하는 헬퍼 함수."""

from __future__ import annotations

import json
from typing import Any

import polars as pl


def df_to_md(df: pl.DataFrame, max_rows: int = 15) -> str:
    """DataFrame → 마크다운 테이블."""
    if df is None or df.height == 0:
        return "(데이터 없음)"
    from dartlab.engines.ai.context.builder import df_to_markdown

    return df_to_markdown(df, max_rows=max_rows)


def json_to_text(value: Any, max_chars: int = 4000) -> str:
    """dict/list/json 직렬화."""
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n... (truncated)"


def format_tool_value(value: Any, *, max_rows: int = 30, max_chars: int = 4000) -> str:
    """도구 반환값을 문자열로 표준화."""
    if isinstance(value, pl.DataFrame):
        return df_to_md(value, max_rows=max_rows)
    if isinstance(value, (dict, list, tuple)):
        return json_to_text(value, max_chars=max_chars)
    return str(value)


def maybe_int(value: Any) -> int | None:
    """빈 값이면 None, 아니면 int 변환."""
    if value in (None, "", False):
        return None
    return int(value)


def csv_list(value: str | None) -> list[str] | None:
    """쉼표 구분 문자열 → 리스트."""
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def ui_action_json(action: Any) -> str:
    """UiAction → JSON 문자열."""
    return json.dumps(action.to_payload(), ensure_ascii=False)
