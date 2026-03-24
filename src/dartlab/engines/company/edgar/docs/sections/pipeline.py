"""EDGAR docs sections 수평화 파이프라인.

source-native item/title을 유지한 form-native topic x period 뷰를 만든다.
topic namespace는 `form_type::topicId`를 사용한다.

반환 형식:
    (topic, blockType, blockOrder, textNodeType, textLevel, textPath)(행) × period(열) DataFrame
    ┌───────────────────────────┬───────────┬────────────┬──────────────┬───────────┬──────────┬──────────┐
    │ topic                     │ blockType │ blockOrder │ textNodeType │ textLevel │ textPath │ 2024     │
    ├───────────────────────────┼───────────┼────────────┼──────────────┼───────────┼──────────┼──────────┤
    │ 10-K::item1Business       │ text      │ 0          │ heading      │ 1         │ Products │ Products │
    │ 10-K::item1Business       │ text      │ 1          │ body         │ 0         │ Products │ iPhone…  │
    │ 10-K::item1Business       │ table     │ 2          │ null         │ null      │ null     │ 테이블   │
    └───────────────────────────┴───────────┴────────────┴──────────────┴───────────┴──────────┴──────────┘
"""

from __future__ import annotations

import re

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectEdgarReport
from dartlab.engines.company.edgar.docs.sections.mapper import mapSectionTitle
from dartlab.engines.company.edgar.docs.sections.textStructure import parseTextStructure
from dartlab.engines.company.edgar.docs.sections.views import sortPeriods


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

    periods = sortPeriods(
        [period for period in df["period_key"].drop_nulls().unique().to_list() if period],
        descending=True,
    )
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

    dfRows: list[dict[str, str | int | None]] = []
    blockOrderCounter: dict[str, int] = {}

    allKeys = list(sortedKeys) + sorted(set(topicMap.keys()) - set(topicOrder.keys()))
    for key in allKeys:
        topic, blockType = key
        periodTexts = {p: topicMap[key].get(p) for p in periods}

        if blockType == "table":
            bo = blockOrderCounter.get(topic, 0)
            blockOrderCounter[topic] = bo + 1
            row: dict[str, str | int | None] = {
                "topic": topic,
                "blockType": "table",
                "blockOrder": bo,
                "textNodeType": None,
                "textLevel": None,
                "textPath": None,
            }
            for p in periods:
                row[p] = periodTexts.get(p)
            dfRows.append(row)
            continue

        # text → heading/body 분리
        # 최신 period의 텍스트로 구조를 결정하고, 각 period의 텍스트를 같은 구조로 분배
        refText = None
        for p in periods:
            if periodTexts.get(p):
                refText = periodTexts[p]
                break
        if refText is None:
            continue

        structuredRows = parseTextStructure(refText, topic=topic)
        if not structuredRows:
            bo = blockOrderCounter.get(topic, 0)
            blockOrderCounter[topic] = bo + 1
            row = {
                "topic": topic,
                "blockType": "text",
                "blockOrder": bo,
                "textNodeType": "body",
                "textLevel": 0,
                "textPath": None,
            }
            for p in periods:
                row[p] = periodTexts.get(p)
            dfRows.append(row)
            continue

        # 각 기간의 텍스트도 같은 파서로 분리
        periodStructured: dict[str, list[dict]] = {}
        for p in periods:
            t = periodTexts.get(p)
            if t:
                periodStructured[p] = parseTextStructure(t, topic=topic)

        for rowIdx, sRow in enumerate(structuredRows):
            bo = blockOrderCounter.get(topic, 0)
            blockOrderCounter[topic] = bo + 1
            outRow: dict[str, str | int | None] = {
                "topic": topic,
                "blockType": "text",
                "blockOrder": bo,
                "textNodeType": sRow["textNodeType"],
                "textLevel": sRow["textLevel"],
                "textPath": sRow["textPath"],
            }
            for p in periods:
                pRows = periodStructured.get(p)
                if pRows and rowIdx < len(pRows):
                    outRow[p] = pRows[rowIdx]["text"]
                else:
                    outRow[p] = None
            dfRows.append(outRow)

    # 스키마 명시 — period 컬럼은 Utf8
    schema: dict[str, pl.DataType] = {
        "topic": pl.Utf8,
        "blockType": pl.Utf8,
        "blockOrder": pl.Int64,
        "textNodeType": pl.Utf8,
        "textLevel": pl.Int64,
        "textPath": pl.Utf8,
    }
    for p in periods:
        schema[p] = pl.Utf8
    result = pl.DataFrame(dfRows, schema=schema)

    # 연간(YYYY) → Q4로 통일, 최신 먼저
    renameMap: dict[str, str] = {}
    for col in result.columns:
        if re.fullmatch(r"\d{4}", col):
            q4Label = f"{col}Q4"
            if q4Label not in result.columns:
                renameMap[col] = q4Label
    if renameMap:
        result = result.rename(renameMap)

    return result
