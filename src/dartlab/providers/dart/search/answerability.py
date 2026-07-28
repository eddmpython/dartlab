"""Answerability policy for product search results."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import polars as pl

from dartlab.providers.dart.search.coerce import _isFalse
from dartlab.providers.dart.search.facetPlanner import QueryFacets, facetMismatchReason
from dartlab.providers.dart.search.sourceIntent import SourceIntent, sourceMatchesIntent

_FRESHNESS_MAX_AGE_DAYS: tuple[tuple[str, int], ...] = (
    ("news", 3),
    ("allFilings", 14),
    ("panel", 30),
    ("edgar-panel", 30),
    ("edgarPanel", 30),
)
LOW_CONFIDENCE_SCORE_FLOOR = 0.02


def applyAnswerability(
    df: pl.DataFrame,
    *,
    sourceIntent: SourceIntent | str | None = None,
    facets: QueryFacets | None = None,
    today: str | None = None,
) -> pl.DataFrame:
    """Mark whether result rows have enough evidence for downstream answers.

    Args:
        df: Normalized search result DataFrame.
        sourceIntent: Optional source isolation intent.
        facets: Optional query facets used to reject mismatched rows.
        today: Optional YYYYMMDD clock value for deterministic freshness checks.

    Returns:
        pl.DataFrame: Rows with answerable and notAnswerableReason updated.

    Raises:
        None.

    Example:
        >>> applyAnswerability(pl.DataFrame()).height
        0
    """
    if df is None or df.height == 0 or "info" in df.columns:
        return df
    rows = []
    for row in df.iter_rows(named=True):
        out = dict(row)
        answerable, reason = _rowAnswerability(out, sourceIntent=sourceIntent, facets=facets, today=today)
        out["answerable"] = answerable
        out["notAnswerableReason"] = reason
        rows.append(out)
    return pl.DataFrame(rows)


def markLowConfidenceRows(result: pl.DataFrame, *, minScore: float = LOW_CONFIDENCE_SCORE_FLOOR) -> pl.DataFrame:
    """Mark the whole candidate set unanswerable when every score is below confidence floor.

    Args:
        result: Search result DataFrame after row-level answerability policy.
        minScore: Minimum score that keeps the candidate pool answerable.

    Returns:
        pl.DataFrame: Result rows with low-confidence answerable rows downgraded.

    Raises:
        None.

    Example:
        >>> markLowConfidenceRows(pl.DataFrame()).height
        0
    """
    if result is None or result.height == 0 or "info" in result.columns:
        return result
    if "score" not in result.columns or "answerable" not in result.columns:
        return result
    scores: list[float] = []
    for value in result["score"].to_list():
        try:
            scores.append(float(value))
        except (TypeError, ValueError):
            continue
    if not scores or max(scores) >= float(minScore):
        return result
    rows = []
    for row in result.iter_rows(named=True):
        out = dict(row)
        if out.get("answerable") is True:
            out["answerable"] = False
            out["notAnswerableReason"] = "lowConfidence"
        rows.append(out)
    return pl.DataFrame(rows)


def _rowAnswerability(
    row: dict[str, Any],
    *,
    sourceIntent: SourceIntent | str | None,
    facets: QueryFacets | None,
    today: str | None,
) -> tuple[bool, str]:
    existing = row.get("answerable")
    existingReason = str(row.get("notAnswerableReason") or "")
    if _isFalse(existing):
        return False, existingReason or "notAnswerable"

    if not sourceMatchesIntent(row.get("source"), sourceIntent):
        return False, "sourceIntentMismatch"
    if not _hasUsableSourceRef(row):
        return False, "missingSourceRef"
    if not _hasUsableEvidenceText(row):
        return False, "missingSnippet"
    if not str(row.get("dataAsOf") or row.get("sourceDataAsOf") or row.get("rcept_dt") or "").strip():
        return False, "missingDataAsOf"
    constraintReason = str(row.get("constraintViolationReason") or "").strip()
    if constraintReason:
        return False, constraintReason.split(",", maxsplit=1)[0]
    facetReason = facetMismatchReason(row, facets)
    if facetReason:
        return False, facetReason
    if _isStaleSource(row, facets=facets, today=today):
        return False, "staleSource"
    return True, ""


def _hasUsableSourceRef(row: dict[str, Any]) -> bool:
    ref = str(row.get("sourceRef") or "").strip()
    if not ref:
        return False
    if ref.startswith("news:"):
        return len(ref) > len("news:")
    if ref.startswith("dart:"):
        return ":#section=" not in ref
    if ref.startswith("edgar:"):
        return ":#section=" not in ref
    return True


def _hasUsableEvidenceText(row: dict[str, Any]) -> bool:
    return bool(
        str(
            row.get("snippet")
            or row.get("text")
            or row.get("section_content")
            or row.get("evidenceText")
            or row.get("report_nm")
            or row.get("reportName")
            or row.get("title")
            or row.get("section_title")
            or row.get("sectionTitle")
            or ""
        ).strip()
    )


def _isStaleSource(row: dict[str, Any], *, facets: QueryFacets | None, today: str | None) -> bool:
    if facets is None or not facets.freshnessRequired:
        return False
    rowDate = _parseDate(row.get("dataAsOf") or row.get("sourceDataAsOf") or row.get("rcept_dt") or row.get("date"))
    todayDate = _parseDate(today or datetime.now(timezone.utc).strftime("%Y%m%d"))
    if rowDate is None or todayDate is None:
        return False
    maxAge = _maxAgeDays(row)
    return (todayDate - rowDate).days > maxAge


def _maxAgeDays(row: dict[str, Any]) -> int:
    source = str(row.get("source") or "")
    for prefix, days in _FRESHNESS_MAX_AGE_DAYS:
        if source == prefix or source.startswith(prefix):
            return days
    return 14


def _parseDate(value: Any):
    text = str(value or "").strip()
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 8:
        return None
    try:
        return datetime.strptime(digits[:8], "%Y%m%d").date()
    except ValueError:
        return None
