"""Product search result schema helpers."""

from __future__ import annotations

import json
from typing import Any

import polars as pl

from dartlab.providers.dart.search.coerce import _asBool

PRODUCT_RESULT_COLUMNS: tuple[str, ...] = (
    "source",
    "sourceRef",
    "dataAsOf",
    "snippet",
    "answerable",
    "notAnswerableReason",
    "fieldCards",
)

# 계약 컬럼이 실어 나르는 dtype. 아래 normalizeSearchResult 가 원본 스키마 위에 덮어쓴다.
_CONTRACT_DTYPES: dict[str, Any] = {
    "source": pl.Utf8,
    "sourceRef": pl.Utf8,
    "dataAsOf": pl.Utf8,
    "snippet": pl.Utf8,
    "answerable": pl.Boolean,
    "notAnswerableReason": pl.Utf8,
    "fieldCards": pl.Utf8,
}


def normalizeSearchResult(df: pl.DataFrame) -> pl.DataFrame:
    """Ensure search rows expose the product result contract.

    Args:
        df: Search result DataFrame.

    Returns:
        pl.DataFrame: Result rows with sourceRef/dataAsOf/snippet/answerable fields.

    Raises:
        None.

    Example:
        >>> normalizeSearchResult(pl.DataFrame())  # doctest: +ELLIPSIS
        shape: (0, 0)
        ...
    """
    if df is None or df.height == 0 or "info" in df.columns:
        return df
    rows = []
    for row in df.iter_rows(named=True):
        out = dict(row)
        source = str(out.get("source") or _inferSource(out))
        sourceRef = str(out.get("sourceRef") or _makeSourceRef(source, out))
        dataAsOf = str(
            out.get("dataAsOf") or out.get("sourceDataAsOf") or out.get("rcept_dt") or _dateFromRcept(out) or ""
        )
        snippet = str(out.get("snippet") or out.get("text") or out.get("section_content") or out.get("title") or "")
        out["source"] = source
        out["sourceRef"] = sourceRef
        out["dataAsOf"] = dataAsOf
        out["snippet"] = snippet[:500]
        out["answerable"] = _asBool(out.get("answerable"), default=True)
        out["notAnswerableReason"] = str(out.get("notAnswerableReason") or "")
        out["fieldCards"] = str(out.get("fieldCards") or _fieldCardsJson(out))
        rows.append(out)
    # dtype 은 추론에 맡기지 않고 원본 df 스키마를 물려준다.
    # 추론(기본 infer_schema_length=100)은 앞 100 행만 보므로, 앞이 전부 null 이고
    # 뒤에 값이 오는 컬럼(뉴스 문서만 채우는 docKey, 공시만 채우는 deleted 등)에서
    # Null 로 확정한 뒤 실제 값을 못 받아 ComputeError 로 검색 전체가 죽었다.
    # 원본 df 는 이미 올바른 dtype 을 들고 있으니 그것이 truth 다.
    schema = {**df.schema, **_CONTRACT_DTYPES}
    return pl.DataFrame(rows, schema=schema)


def _inferSource(row: dict[str, Any]) -> str:
    rcept = str(row.get("rcept_no") or "")
    if rcept.startswith("news:"):
        return "news"
    if "-" in rcept and not rcept.isdigit():
        return "edgar-panel"
    return "allFilings"


def _makeSourceRef(source: str, row: dict[str, Any]) -> str:
    rcept = str(row.get("rcept_no") or "")
    section = int(row.get("section_order") or 0)
    if source == "news":
        return rcept if rcept.startswith("news:") else f"news:{rcept}"
    if source == "edgar-panel":
        return f"edgar:panel:{rcept}#section={section}"
    if source == "panel":
        return f"dart:panel:{rcept}#section={section}"
    if source == "allFilings":
        return f"dart:allFilings:{rcept}#section={section}"
    if source:
        return f"{source}:{rcept}#section={section}"
    return rcept


def _dateFromRcept(row: dict[str, Any]) -> str:
    rcept = str(row.get("rcept_no") or "")
    if len(rcept) >= 8 and rcept[:8].isdigit():
        return rcept[:8]
    return ""


def _fieldCardsJson(row: dict[str, Any]) -> str:
    from dartlab.providers.dart.search.evidencePack import buildFieldCards

    cards = buildFieldCards(row)
    return json.dumps(cards, ensure_ascii=False, separators=(",", ":"))
