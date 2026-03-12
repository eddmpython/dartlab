"""sections 파생 뷰 생성 helpers."""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix
from dartlab.engines.dart.docs.sections.runtime import (
    detailTopicForBlock,
    detailTopicForTopic,
    semanticTopicForBlock,
)

REPORT_KINDS = [
    ("annual", ""),
    ("Q1", "Q1"),
    ("semi", "Q2"),
    ("Q3", "Q3"),
]
RE_MAJOR = re.compile(r"^([가-힣])\.\s*(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")


def periodSortKey(period: str) -> tuple[int, int]:
    value = str(period)
    if "Q" in value:
        return int(value[:4]), int(value[-1])
    return int(value), 4


def sortPeriods(periods: list[str], *, descending: bool = True) -> list[str]:
    return sorted(periods, key=periodSortKey, reverse=descending)


def periodOrderValue(period: str) -> int:
    year, slot = periodSortKey(period)
    return year * 10 + slot


def contentCol(df: pl.DataFrame) -> str:
    if "section_content" in df.columns:
        return "section_content"
    return "content"


def normalizeTitle(title: str) -> str:
    return stripSectionPrefix((title or "").strip())


def isBoilerplateTopic(topic: str) -> bool:
    return topic in {
        "사업보고서",
        "분기보고서",
        "반기보고서",
        "정정신고(보고)",
        "ceoConfirmation",
    }


def isPlaceholderBlock(blockText: str) -> bool:
    text = blockText.strip()
    if not text:
        return False
    phrases = (
        "분기보고서에 기재하지 않습니다",
        "반기보고서에 기재하지 않습니다",
        "반기ㆍ사업보고서에 기재 예정",
        "반기·사업보고서에 기재 예정",
        "기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다",
    )
    return any(phrase in text for phrase in phrases)


def blockPriority(
    blockType: str,
    semanticTopic: str | None,
    detailTopic: str | None,
    isBoilerplate: bool,
    isPlaceholder: bool,
) -> int:
    if isBoilerplate:
        return 0
    if isPlaceholder:
        return 0
    if detailTopic:
        return 5
    if semanticTopic:
        return 4
    if blockType == "text":
        return 3
    if blockType == "heading":
        return 2
    return 1


def classifyContent(content: str) -> tuple[int, int, int]:
    table_lines = 0
    heading_lines = 0
    text_lines = 0
    for raw in (content or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("|"):
            table_lines += 1
            continue
        if RE_MAJOR.match(line) or RE_MINOR.match(line):
            heading_lines += 1
            continue
        text_lines += 1
    return text_lines, table_lines, heading_lines


def buildMarkdownBlocks(stockCode: str) -> pl.DataFrame:
    df = loadData(stockCode)
    ccol = contentCol(df)
    years = sorted({str(year) for year in df.get_column("year").to_list()}, reverse=True)
    rows: list[dict[str, object]] = []

    for year in years:
        for reportKind, suffix in REPORT_KINDS:
            period = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or ccol not in report.columns:
                continue

            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue

            for record in subset.to_dicts():
                rawTitle = normalizeTitle(str(record["section_title"] or ""))
                if not rawTitle:
                    continue
                content = str(record[ccol] or "")
                textLines, tableLines, headingLines = classifyContent(content)
                rows.append(
                    {
                        "stockCode": stockCode,
                        "period": period,
                        "periodOrder": periodOrderValue(period),
                        "sectionOrder": int(record["section_order"]),
                        "rawTitle": rawTitle,
                        "topic": mapSectionTitle(rawTitle),
                        "rawMarkdown": content,
                        "textLines": textLines,
                        "tableLines": tableLines,
                        "headingLines": headingLines,
                    }
                )

    return pl.DataFrame(rows)


def buildMarkdownWide(blocks: pl.DataFrame) -> pl.DataFrame:
    if blocks.height == 0:
        return pl.DataFrame()

    merged = (
        blocks.group_by(["topic", "period"])
        .agg(
            pl.col("rawMarkdown").implode().list.join("\n\n").alias("rawMarkdown"),
            pl.col("rawTitle").n_unique().alias("rawTitleVariants"),
            pl.col("sectionOrder").min().alias("firstOrder"),
        )
        .sort(["firstOrder", "topic", "period"])
    )

    periods = [period for period in sortPeriods(merged.get_column("period").unique().to_list())]
    wide = merged.select(["topic", "period", "rawMarkdown"]).pivot(
        on="period", index="topic", values="rawMarkdown"
    )
    existing = [period for period in periods if period in wide.columns]
    return wide.select(["topic", *existing])


def splitMarkdownBlocks(content: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    currentLabel = "(root)"
    textBuffer: list[str] = []
    tableBuffer: list[str] = []
    blockIndex = 0

    def flushText() -> None:
        nonlocal textBuffer, blockIndex
        text = "\n".join(textBuffer).strip()
        if text:
            rows.append(
                {
                    "blockIdx": blockIndex,
                    "blockType": "text",
                    "blockLabel": currentLabel,
                    "blockText": text,
                    "tableLines": 0,
                }
            )
            blockIndex += 1
        textBuffer = []

    def flushTable() -> None:
        nonlocal tableBuffer, blockIndex
        text = "\n".join(tableBuffer).strip()
        if text:
            rows.append(
                {
                    "blockIdx": blockIndex,
                    "blockType": "table",
                    "blockLabel": currentLabel,
                    "blockText": text,
                    "tableLines": len(tableBuffer),
                }
            )
            blockIndex += 1
        tableBuffer = []

    def flushAll() -> None:
        flushText()
        flushTable()

    for raw in content.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flushTable()
            if textBuffer:
                textBuffer.append("")
            continue
        if stripped.startswith("|"):
            flushText()
            tableBuffer.append(stripped)
            continue
        if RE_MAJOR.match(stripped) or RE_MINOR.match(stripped):
            flushAll()
            currentLabel = stripped
            rows.append(
                {
                    "blockIdx": blockIndex,
                    "blockType": "heading",
                    "blockLabel": stripped,
                    "blockText": stripped,
                    "tableLines": 0,
                }
            )
            blockIndex += 1
            continue
        flushTable()
        textBuffer.append(stripped)

    flushAll()
    return rows


def retrievalBlocks(stockCode: str) -> pl.DataFrame:
    df = loadData(stockCode)
    ccol = contentCol(df)
    years = sorted({str(year) for year in df.get_column("year").to_list()}, reverse=True)
    rows: list[dict[str, object]] = []

    for year in years:
        for reportKind, suffix in REPORT_KINDS:
            period = f"{year}{suffix}"
            report = selectReport(df, year, reportKind=reportKind)
            if report is None or ccol not in report.columns:
                continue
            subset = (
                report.select(["section_order", "section_title", ccol])
                .filter(pl.col(ccol).is_not_null() & (pl.col(ccol).str.len_chars() > 0))
                .sort("section_order")
            )
            if subset.height == 0:
                continue
            for record in subset.to_dicts():
                rawTitle = normalizeTitle(str(record["section_title"] or ""))
                if not rawTitle:
                    continue
                topic = mapSectionTitle(rawTitle)
                content = str(record[ccol] or "")
                for block in splitMarkdownBlocks(content):
                    blockText = str(block["blockText"])
                    blockLabel = str(block["blockLabel"])
                    blockType = str(block["blockType"])
                    semanticTopic = semanticTopicForBlock(topic, blockLabel, blockType, blockText)
                    detailTopic = detailTopicForBlock(topic, rawTitle, blockLabel, blockType, blockText)
                    boilerplate = isBoilerplateTopic(topic)
                    placeholder = isPlaceholderBlock(blockText)
                    cellKey = f"{stockCode}:{period}:{topic}"
                    rows.append(
                        {
                            "stockCode": stockCode,
                            "period": period,
                            "periodOrder": periodOrderValue(period),
                            "sectionOrder": int(record["section_order"]),
                            "rawTitle": rawTitle,
                            "topic": topic,
                            "sourceTopic": rawTitle,
                            "cellKey": cellKey,
                            "blockIdx": int(block["blockIdx"]),
                            "blockType": blockType,
                            "blockLabel": blockLabel,
                            "blockText": blockText,
                            "chars": len(blockText),
                            "tableLines": int(block["tableLines"]),
                            "semanticTopic": semanticTopic,
                            "detailTopic": detailTopic,
                            "isBoilerplate": boilerplate,
                            "isPlaceholder": placeholder,
                            "blockPriority": blockPriority(
                                blockType,
                                semanticTopic,
                                detailTopic,
                                boilerplate,
                                placeholder,
                            ),
                        }
                    )

    df = pl.DataFrame(
        rows,
        schema={
            "stockCode": pl.Utf8,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "sectionOrder": pl.Int64,
            "rawTitle": pl.Utf8,
            "topic": pl.Utf8,
            "sourceTopic": pl.Utf8,
            "cellKey": pl.Utf8,
            "blockIdx": pl.Int64,
            "blockType": pl.Utf8,
            "blockLabel": pl.Utf8,
            "blockText": pl.Utf8,
            "chars": pl.Int64,
            "tableLines": pl.Int64,
            "semanticTopic": pl.Utf8,
            "detailTopic": pl.Utf8,
            "isBoilerplate": pl.Boolean,
            "isPlaceholder": pl.Boolean,
            "blockPriority": pl.Int64,
        },
        strict=False,
    )
    return df.sort(
        ["periodOrder", "blockPriority", "sectionOrder", "blockIdx"],
        descending=[True, True, False, False],
    )


def splitContextText(text: str, maxChars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= maxChars:
        return [text]
    parts: list[str] = []
    lines = text.splitlines()
    buffer: list[str] = []
    currentLen = 0
    for line in lines:
        extra = len(line) + (1 if buffer else 0)
        if buffer and currentLen + extra > maxChars:
            parts.append("\n".join(buffer).strip())
            buffer = [line]
            currentLen = len(line)
        else:
            buffer.append(line)
            currentLen += extra
    if buffer:
        parts.append("\n".join(buffer).strip())
    return [part for part in parts if part]


def splitMarkdownTable(text: str, maxChars: int) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    joined = "\n".join(lines).strip()
    if len(joined) <= maxChars:
        return [joined]

    header = lines[:2]
    body = lines[2:] if len(lines) > 2 else []
    if not body:
        return [joined]

    parts: list[str] = []
    current: list[str] = []
    for line in body:
        candidate = "\n".join(header + current + [line]).strip()
        if current and len(candidate) > maxChars:
            parts.append("\n".join(header + current).strip())
            current = [line]
            continue
        current.append(line)
    if current:
        parts.append("\n".join(header + current).strip())
    return [part for part in parts if part]


def contextSlices(stockCode: str, *, maxChars: int = 1800) -> pl.DataFrame:
    blocks = retrievalBlocks(stockCode)
    rows: list[dict[str, object]] = []
    for record in blocks.to_dicts():
        isSemantic = record.get("semanticTopic") is not None or record.get("detailTopic") is not None
        if record.get("isBoilerplate") or (record.get("isPlaceholder") and not isSemantic):
            continue
        blockText = str(record["blockText"] or "")
        if record["blockType"] == "table":
            parts = splitMarkdownTable(blockText, maxChars)
        else:
            parts = splitContextText(blockText, maxChars)
        for idx, part in enumerate(parts):
            rows.append(
                {
                    "stockCode": stockCode,
                    "period": record["period"],
                    "periodOrder": record["periodOrder"],
                    "topic": record["topic"],
                    "sourceTopic": record.get("sourceTopic"),
                    "cellKey": record.get("cellKey"),
                    "semanticTopic": record.get("semanticTopic"),
                    "detailTopic": record.get("detailTopic"),
                    "blockType": record["blockType"],
                    "blockLabel": record["blockLabel"],
                    "sliceIdx": idx,
                    "sliceText": part,
                    "chars": len(part),
                    "isSemantic": isSemantic,
                    "isTable": record["blockType"] == "table",
                    "isBoilerplate": record.get("isBoilerplate"),
                    "isPlaceholder": record.get("isPlaceholder"),
                    "blockPriority": record.get("blockPriority"),
                }
            )
    df = pl.DataFrame(
        rows,
        schema={
            "stockCode": pl.Utf8,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "topic": pl.Utf8,
            "sourceTopic": pl.Utf8,
            "cellKey": pl.Utf8,
            "semanticTopic": pl.Utf8,
            "detailTopic": pl.Utf8,
            "blockType": pl.Utf8,
            "blockLabel": pl.Utf8,
            "sliceIdx": pl.Int64,
            "sliceText": pl.Utf8,
            "chars": pl.Int64,
            "isSemantic": pl.Boolean,
            "isTable": pl.Boolean,
            "isBoilerplate": pl.Boolean,
            "isPlaceholder": pl.Boolean,
            "blockPriority": pl.Int64,
        },
        strict=False,
    )
    return df.sort(
        ["periodOrder", "blockPriority", "topic", "sliceIdx"],
        descending=[True, True, False, False],
    )


def saveView(df: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(path)
