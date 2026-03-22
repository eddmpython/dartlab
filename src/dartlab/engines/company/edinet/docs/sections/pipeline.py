"""EDINET sections 수평화 파이프라인.

docs parquet → section 매핑 → topic × period 수평화.
DART/EDGAR sections pipeline과 동일한 패턴.
"""

from __future__ import annotations

from typing import Any

import polars as pl

from dartlab.engines.company.edinet.docs.sections.mapper import (
    mapSectionTitle,
    normalizeSectionTitle,
)


def buildSections(docsDf: pl.DataFrame) -> pl.DataFrame:
    """docs parquet → sections DataFrame 변환.

    Args:
        docsDf: docs parquet (edinet_code, element_id, label, context_id, text).

    Returns:
        sections DataFrame (topic, period, text, ...).
    """
    if docsDf.is_empty():
        return pl.DataFrame(
            schema={
                "topic": pl.Utf8,
                "period": pl.Utf8,
                "text": pl.Utf8,
                "sourceLabel": pl.Utf8,
                "elementId": pl.Utf8,
            }
        )

    rows: list[dict[str, Any]] = []

    for row in docsDf.iter_rows(named=True):
        label = row.get("label", "")
        topicId = mapSectionTitle(label)
        if topicId is None:
            topicId = normalizeSectionTitle(label)

        # context_id에서 period 추출
        # EDINET context 형식: CurrentYearDuration, Prior1YearDuration 등
        contextId = row.get("context_id", "")
        period = _parsePeriod(contextId)

        rows.append(
            {
                "topic": topicId,
                "period": period,
                "text": row.get("text", ""),
                "sourceLabel": label,
                "elementId": row.get("element_id", ""),
            }
        )

    return pl.DataFrame(rows)


def _parsePeriod(contextId: str) -> str:
    """EDINET context ID → period 문자열.

    EDINET context 패턴:
    - CurrentYearDuration → 당기
    - Prior1YearDuration → 전기
    - CurrentYearInstant → 당기말
    - Prior1YearInstant → 전기말
    - CurrentQuarter1Duration → 1Q
    """
    if not contextId:
        return ""

    ctx = contextId.lower()

    if "currentyear" in ctx:
        if "instant" in ctx:
            return "currentEnd"
        return "current"
    if "prior1year" in ctx:
        if "instant" in ctx:
            return "prior1End"
        return "prior1"
    if "prior2year" in ctx:
        if "instant" in ctx:
            return "prior2End"
        return "prior2"

    # 분기 패턴
    if "currentquarter" in ctx:
        return "currentQ"
    if "prior1quarter" in ctx:
        return "prior1Q"

    return contextId
