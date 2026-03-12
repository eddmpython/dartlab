"""EDGAR docs sections 수평화 파이프라인.

source-native item/title을 유지한 form-native topic x period 뷰를 만든다.
topic namespace는 `form_type::topicId`를 사용한다.
"""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectEdgarReport
from dartlab.engines.edgar.docs.sections.mapper import mapSectionTitle
from dartlab.engines.edgar.docs.sections.views import sortPeriods, sortTopics


def _rowsToTopicRows(df: pl.DataFrame) -> list[dict[str, object]]:
    merged: dict[str, list[str]] = {}
    orderMap: dict[str, int] = {}

    for row in df.sort("section_order").iter_rows(named=True):
        formType = str(row.get("form_type") or "")
        rawTitle = str(row.get("section_title") or "")
        text = str(row.get("section_content") or "")
        if not rawTitle or not text:
            continue

        topic = mapSectionTitle(formType, rawTitle)
        if topic not in merged:
            merged[topic] = []
            orderMap[topic] = int(row.get("section_order") or 0)
        merged[topic].append(text)

    rows: list[dict[str, object]] = []
    for topic, texts in merged.items():
        rows.append(
            {
                "topic": topic,
                "text": "\n".join(texts),
                "orderSeq": orderMap[topic],
            }
        )
    rows.sort(key=lambda row: (int(row["orderSeq"]), str(row["topic"])))
    return rows


def sections(stockCode: str, *, sinceYear: int | None = None) -> pl.DataFrame | None:
    df = loadData(stockCode, category="edgarDocs", sinceYear=sinceYear)
    if "period_key" not in df.columns:
        return None

    periods = sorted(
        [period for period in df["period_key"].drop_nulls().unique().to_list() if period],
        reverse=False,
    )
    periods = sortPeriods(periods)
    if not periods:
        return None

    topicMap: dict[str, dict[str, str]] = {}
    topicOrder: dict[str, int] = {}
    for period in periods:
        report = selectEdgarReport(df, period)
        if report is None or report.is_empty():
            continue
        for row in _rowsToTopicRows(report):
            topic = str(row["topic"])
            text = str(row["text"])
            orderSeq = int(row["orderSeq"])
            if topic not in topicMap:
                topicMap[topic] = {}
                topicOrder[topic] = orderSeq
            topicMap[topic][period] = text

    if not topicMap:
        return None

    rows: list[dict[str, str | None]] = []
    for topic in sortTopics(list(topicMap.keys()), topicOrder):
        row: dict[str, str | None] = {"topic": topic}
        for period in periods:
            row[period] = topicMap[topic].get(period)
        rows.append(row)
    return pl.DataFrame(rows)
