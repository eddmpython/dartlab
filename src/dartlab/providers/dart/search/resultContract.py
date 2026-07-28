"""Product search result contract audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from dartlab.providers.dart.search.coerce import _ratio

PRODUCT_CONTRACT_FIELDS = ("source", "sourceRef", "dataAsOf", "snippet", "answerable", "fieldCards")


def loadResultRows(path: str | Path) -> list[dict[str, Any]]:
    """Load search result rows from JSON or JSONL.

    Args:
        path: JSON/JSONL path. Supported shapes are a row list, a
            query-to-rows mapping, or a list of ``{"query": ..., "results": [...]}``.

    Returns:
        list[dict[str, Any]]: Flattened result rows.

    Raises:
        OSError: If the file cannot be read.
        ValueError: If the shape is unsupported.

    Example:
        >>> callable(loadResultRows)
        True
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".jsonl":
        data = [json.loads(line) for line in text.splitlines() if line.strip()]
        return flattenResultRows(data)
    data = json.loads(text) if text.strip() else []
    return flattenResultRows(data)


def flattenResultRows(data: Any) -> list[dict[str, Any]]:
    """Flatten supported result JSON shapes into row dictionaries.

    Args:
        data: Parsed JSON payload.

    Returns:
        list[dict[str, Any]]: Result rows.

    Raises:
        ValueError: If ``data`` has an unsupported shape.

    Example:
        >>> flattenResultRows({"q": [{"sourceRef": "x"}]})[0]["sourceRef"]
        'x'
    """
    if isinstance(data, list):
        rows: list[dict[str, Any]] = []
        for item in data:
            if isinstance(item, Mapping) and isinstance(item.get("results"), list):
                query = str(item.get("query") or "")
                for row in item["results"]:
                    out = dict(row)
                    if query and "query" not in out:
                        out["query"] = query
                    rows.append(out)
            elif isinstance(item, Mapping):
                rows.append(dict(item))
        return rows
    if isinstance(data, Mapping):
        rows = data.get("rows") or data.get("results")
        if isinstance(rows, list):
            return flattenResultRows(rows)
        out: list[dict[str, Any]] = []
        for query, resultRows in data.items():
            if not isinstance(resultRows, list):
                continue
            for row in resultRows:
                item = dict(row)
                item.setdefault("query", str(query))
                out.append(item)
        return out
    raise ValueError("unsupported search result shape")


def auditSearchResultRows(
    rows: Iterable[Mapping[str, Any]],
    *,
    minRows: int = 1,
    requireDataAsOf: bool = True,
    requireSnippet: bool = True,
    requireFieldCards: bool = True,
    requireCardEvidence: bool = True,
) -> dict[str, Any]:
    """Audit product search result rows for release-surface contracts.

    Args:
        rows: Result rows to audit.
        minRows: Minimum rows required.
        requireDataAsOf: True requires each row to have ``dataAsOf``.
        requireSnippet: True requires each row to have ``snippet``.
        requireFieldCards: True requires parseable non-empty ``fieldCards``.
        requireCardEvidence: True requires at least one field card with evidence.

    Returns:
        dict[str, Any]: Audit report with invalid rows and blockers.

    Raises:
        None.

    Example:
        >>> auditSearchResultRows([], minRows=0)["valid"]
        True
    """
    normalizedRows = [dict(row) for row in rows]
    invalidRows: list[dict[str, Any]] = []
    for index, row in enumerate(normalizedRows):
        reasons = _invalidReasons(
            row,
            requireDataAsOf=requireDataAsOf,
            requireSnippet=requireSnippet,
            requireFieldCards=requireFieldCards,
            requireCardEvidence=requireCardEvidence,
        )
        if reasons:
            invalidRows.append(
                {
                    "rowIndex": index,
                    "query": str(row.get("query") or ""),
                    "source": str(row.get("source") or ""),
                    "sourceRef": str(row.get("sourceRef") or ""),
                    "reasons": reasons,
                }
            )
    blockers: list[str] = []
    if len(normalizedRows) < minRows:
        blockers.append(f"minRows:{len(normalizedRows)}/{int(minRows)}")
    if invalidRows:
        blockers.append(f"invalidRows:{len(invalidRows)}")
    return {
        "valid": not blockers,
        "totalRows": len(normalizedRows),
        "invalidRows": invalidRows,
        "blockers": blockers,
        "metrics": _metrics(normalizedRows, invalidRows),
    }


def writeResultContractReport(path: str | Path, report: Mapping[str, Any]) -> None:
    """Write a search result contract report.

    Args:
        path: Output JSON path.
        report: Audit report.

    Returns:
        None.

    Raises:
        OSError: If the file cannot be written.

    Example:
        >>> callable(writeResultContractReport)
        True
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _invalidReasons(
    row: Mapping[str, Any],
    *,
    requireDataAsOf: bool,
    requireSnippet: bool,
    requireFieldCards: bool,
    requireCardEvidence: bool,
) -> list[str]:
    reasons: list[str] = []
    if not str(row.get("source") or "").strip():
        reasons.append("missingSource")
    if not str(row.get("sourceRef") or "").strip():
        reasons.append("missingSourceRef")
    if requireDataAsOf and not str(row.get("dataAsOf") or row.get("sourceDataAsOf") or "").strip():
        reasons.append("missingDataAsOf")
    if "answerable" not in row:
        reasons.append("missingAnswerable")
    if requireSnippet and not str(row.get("snippet") or "").strip():
        reasons.append("missingSnippet")
    if requireFieldCards:
        cards, cardError = _fieldCards(row.get("fieldCards"))
        if cardError:
            reasons.append(cardError)
        elif not cards:
            reasons.append("emptyFieldCards")
        else:
            if not any(str(card.get("sourceRef") or "").strip() for card in cards):
                reasons.append("fieldCardsMissingSourceRef")
            if requireCardEvidence and not any(str(card.get("evidence") or "").strip() for card in cards):
                reasons.append("fieldCardsMissingEvidence")
    return reasons


def _fieldCards(raw: Any) -> tuple[list[dict[str, Any]], str]:
    if raw in (None, ""):
        return [], "missingFieldCards"
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return [], "invalidFieldCardsJson"
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        return [], "invalidFieldCardsShape"
    cards = [dict(card) for card in raw if isinstance(card, Mapping)]
    return cards, ""


def _metrics(rows: Sequence[Mapping[str, Any]], invalidRows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    total = len(rows)
    invalid = len(invalidRows)
    validRows = total - invalid
    answerable = sum(1 for row in rows if _isAnswerable(row))
    return {
        "validRate": _ratio(validRows, total),
        "invalidRate": _ratio(invalid, total),
        "answerableRate": _ratio(answerable, total),
    }


def _isAnswerable(row: Mapping[str, Any]) -> bool:
    value = row.get("answerable")
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "n"}
    return bool(value)
