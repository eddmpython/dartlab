"""EDGAR docs sections 수평화 파이프라인.

source-native item/title을 유지한 form-native topic x period 뷰를 만든다.
topic namespace는 `form_type::topicId`를 사용한다.

반환 형식:
    (topic, blockType)(행) × period(열) DataFrame
    ┌───────────────────────────┬───────────┬──────────┬──────────┐
    │ topic                     │ blockType │ 2024     │ 2023     │
    ├───────────────────────────┼───────────┼──────────┼──────────┤
    │ 10-K::item1Business       │ text      │ 텍스트   │ 텍스트   │
    │ 10-K::item1Business       │ table     │ 테이블   │ null     │
    │ 10-K::item7Mdna           │ text      │ 텍스트   │ 텍스트   │
    └───────────────────────────┴───────────┴──────────┴──────────┘
"""

from __future__ import annotations

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectEdgarReport
from dartlab.engines.edgar.docs.sections.mapper import mapSectionTitle
from dartlab.engines.edgar.docs.sections.views import sortPeriods


def _splitTextTable(content: str) -> tuple[str, str]:
    """content를 텍스트 부분과 테이블 부분으로 분리."""
    text_lines: list[str] = []
    table_lines: list[str] = []
    for line in content.split("\n"):
        if line.strip().startswith("|"):
            table_lines.append(line)
        else:
            text_lines.append(line)
    return "\n".join(text_lines).strip(), "\n".join(table_lines).strip()


def _rowsToTopicRows(df: pl.DataFrame) -> list[dict[str, object]]:
    # key: (topic, blockType)
    merged: dict[tuple[str, str], list[str]] = {}
    orderMap: dict[tuple[str, str], tuple[int, int]] = {}
    idx = 0

    for row in df.sort("section_order").iter_rows(named=True):
        formType = str(row.get("form_type") or "")
        rawTitle = str(row.get("section_title") or "")
        content = str(row.get("section_content") or "")
        if not rawTitle or not content:
            continue

        topic = mapSectionTitle(formType, rawTitle)
        orderSeq = int(row.get("section_order") or 0)

        textPart, tablePart = _splitTextTable(content)
        if textPart:
            key = (topic, "text")
            if key not in merged:
                merged[key] = []
                orderMap[key] = (orderSeq, idx)
                idx += 1
            merged[key].append(textPart)
        if tablePart:
            key = (topic, "table")
            if key not in merged:
                merged[key] = []
                orderMap[key] = (orderSeq, idx)
                idx += 1
            merged[key].append(tablePart)

    rows: list[dict[str, object]] = []
    for (topic, blockType), texts in merged.items():
        seq, subIdx = orderMap[(topic, blockType)]
        blockSort = 0 if blockType == "text" else 1
        rows.append(
            {
                "topic": topic,
                "blockType": blockType,
                "text": "\n".join(texts),
                "orderSeq": seq,
                "blockSort": blockSort,
                "subIdx": subIdx,
            }
        )
    rows.sort(key=lambda r: (int(r["orderSeq"]), int(r["blockSort"]), int(r["subIdx"])))
    return rows


def sections(stockCode: str, *, sinceYear: int | None = None) -> pl.DataFrame | None:
    """전 기간 보고서 섹션 — (topic, blockType) × period DataFrame.

    텍스트와 테이블을 분리하여 같은 topic이라도 text 행과 table 행으로 나뉜다.

    Args:
        stockCode: ticker (예: "AAPL").
        sinceYear: 이 연도 이후만 포함 (optional).

    Returns:
        (topic, blockType)(행) × period(열) DataFrame. 값은 텍스트(str).
        데이터 없으면 None.
    """
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

    # key: (topic, blockType)
    topicMap: dict[tuple[str, str], dict[str, str]] = {}
    topicOrder: dict[tuple[str, str], tuple[int, int, int]] = {}
    for period in periods:
        report = selectEdgarReport(df, period)
        if report is None or report.is_empty():
            continue
        for row in _rowsToTopicRows(report):
            topic = str(row["topic"])
            blockType = str(row["blockType"])
            text = str(row["text"])
            orderSeq = int(row["orderSeq"])
            blockSort = int(row["blockSort"])
            subIdx = int(row["subIdx"])
            key = (topic, blockType)
            if key not in topicMap:
                topicMap[key] = {}
            topicMap[key][period] = text
            if key not in topicOrder:
                topicOrder[key] = (orderSeq, blockSort, subIdx)

    if not topicMap:
        return None

    sortedKeys = sorted(topicOrder.keys(), key=lambda k: topicOrder[k])

    dfRows: list[dict[str, str | None]] = []
    for key in sortedKeys:
        topic, blockType = key
        row: dict[str, str | None] = {"topic": topic, "blockType": blockType}
        for period in periods:
            row[period] = topicMap[key].get(period)
        dfRows.append(row)

    remaining = set(topicMap.keys()) - set(topicOrder.keys())
    for key in sorted(remaining):
        topic, blockType = key
        row: dict[str, str | None] = {"topic": topic, "blockType": blockType}
        for period in periods:
            row[period] = topicMap[key].get(period)
        dfRows.append(row)

    return pl.DataFrame(dfRows)
