"""EDGAR companyfacts / companyconcept / frames wrapper."""

from __future__ import annotations

from datetime import date
from typing import Any

import polars as pl

from dartlab.providers.edgar.openapi.client import DEFAULT_BASE_URL, EdgarClient

EDGAR_COMPANYFACTS_SCHEMA = {
    "cik": pl.Utf8,
    "entityName": pl.Utf8,
    "namespace": pl.Utf8,
    "tag": pl.Utf8,
    "label": pl.Utf8,
    "unit": pl.Utf8,
    "val": pl.Float64,
    "fy": pl.Int32,
    "fp": pl.Utf8,
    "form": pl.Utf8,
    "filed": pl.Date,
    "frame": pl.Utf8,
    "start": pl.Date,
    "end": pl.Date,
    "accn": pl.Utf8,
}


def getCompanyFactsJson(cik: str, client: EdgarClient | None = None) -> dict[str, Any]:
    """CIK로 SEC companyfacts API를 호출하여 전체 XBRL fact JSON을 반환."""
    api = client or EdgarClient()
    normalized = str(cik).zfill(10)
    return api.getJson(f"{DEFAULT_BASE_URL}/api/xbrl/companyfacts/CIK{normalized}.json")


def getCompanyConceptJson(
    cik: str,
    taxonomy: str,
    tag: str,
    client: EdgarClient | None = None,
) -> dict[str, Any]:
    """특정 회사의 taxonomy/tag 조합에 대한 concept JSON을 반환."""
    api = client or EdgarClient()
    normalized = str(cik).zfill(10)
    return api.getJson(f"{DEFAULT_BASE_URL}/api/xbrl/companyconcept/CIK{normalized}/{taxonomy}/{tag}.json")


def getFrameJson(
    taxonomy: str,
    tag: str,
    unit: str,
    period: str,
    client: EdgarClient | None = None,
) -> dict[str, Any]:
    """특정 기간의 전체 기업 XBRL frame 데이터를 JSON으로 반환."""
    api = client or EdgarClient()
    return api.getJson(f"{DEFAULT_BASE_URL}/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json")


def companyFactsToRows(payload: dict[str, Any]) -> pl.DataFrame:
    """companyfacts JSON을 flat한 행 단위 DataFrame으로 변환."""
    rows: list[dict[str, Any]] = []
    cik = str(payload.get("cik") or "").zfill(10)
    entityName = str(payload.get("entityName") or "")
    facts = payload.get("facts", {})
    if not isinstance(facts, dict):
        return pl.DataFrame()

    for namespace, tags in facts.items():
        if not isinstance(tags, dict):
            continue
        for tag, tagInfo in tags.items():
            if not isinstance(tagInfo, dict):
                continue
            label = str(tagInfo.get("label") or tag)
            units = tagInfo.get("units", {})
            if not isinstance(units, dict):
                continue
            for unit, entries in units.items():
                if not isinstance(entries, list):
                    continue
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    rows.append(
                        {
                            "cik": cik,
                            "entityName": entityName,
                            "namespace": namespace,
                            "tag": tag,
                            "label": label,
                            "unit": str(unit),
                            "val": _asFloat(entry.get("val")),
                            "fy": _asInt(entry.get("fy")),
                            "fp": _asText(entry.get("fp")),
                            "form": _asText(entry.get("form")),
                            "filed": _asDate(entry.get("filed")),
                            "frame": _asText(entry.get("frame")),
                            "start": _asDate(entry.get("start")),
                            "end": _asDate(entry.get("end")),
                            "accn": _asText(entry.get("accn")),
                        }
                    )

    if not rows:
        return pl.DataFrame(schema=EDGAR_COMPANYFACTS_SCHEMA)
    return pl.DataFrame(rows, schema=EDGAR_COMPANYFACTS_SCHEMA)


def _asText(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _asInt(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _asFloat(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _asDate(value: Any) -> date | None:
    text = _asText(value)
    if text is None:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
