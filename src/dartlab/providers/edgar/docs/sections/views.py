"""EDGAR sections 뷰 유틸리티 — 정렬, 마크다운, retrievalBlocks, contextSlices."""

from __future__ import annotations

import re

import polars as pl

_TOPIC_RE = re.compile(r"^(10-K|10-Q|20-F)::")
_PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


def _periodOrderValue(period: str) -> int:
    """'2024' → 20244, '2024Q3' → 20243."""
    if "Q" not in period:
        return int(period) * 10 + 4
    return int(period[:4]) * 10 + int(period[-1])


def sortPeriods(periods: list[str], *, descending: bool = False) -> list[str]:
    def key(period: str) -> tuple[int, int]:
        if "Q" not in period:
            return int(period), 4
        return int(period[:4]), int(period[-1])

    return sorted(periods, key=key, reverse=descending)


def sortTopics(topics: list[str], topicOrder: dict[str, int]) -> list[str]:
    def key(topic: str) -> tuple[int, str, str]:
        match = _TOPIC_RE.match(topic)
        formType = match.group(1) if match else ""
        return topicOrder.get(topic, 999999), formType, topic

    return sorted(topics, key=key)


def buildMarkdownWide(df: pl.DataFrame | None) -> str:
    if df is None or df.is_empty():
        return ""
    periods = [col for col in df.columns if col != "topic"]
    header = "| topic | " + " | ".join(periods) + " |"
    sep = "| --- | " + " | ".join(["---"] * len(periods)) + " |"
    lines = [header, sep]
    for row in df.iter_rows(named=True):
        values = [str(row.get(period) or "") for period in periods]
        values = [value.replace("|", "｜").replace("\n", "<br>") for value in values]
        lines.append("| " + str(row["topic"]) + " | " + " | ".join(values) + " |")
    return "\n".join(lines)


# ── retrievalBlocks ──────────────────────────────────────────────


def retrievalBlocks(ticker: str) -> pl.DataFrame | None:
    """sections를 block × period 단위로 unpivot하여 LLM 검색용 DataFrame 반환.

    반환 컬럼:
        ticker, period, periodOrder, topic, blockType, blockOrder,
        textNodeType, textLevel, textPath, blockText, chars, blockPriority
    """
    from dartlab.providers.edgar.docs.sections.pipeline import sections

    sec = sections(ticker)
    if sec is None or sec.is_empty():
        return None

    periodCols = [c for c in sec.columns if _PERIOD_RE.fullmatch(c)]
    if not periodCols:
        return None

    # 메타 컬럼 (period 제외)
    metaCols = [c for c in sec.columns if c not in periodCols]

    # ── Python loop로 block 행 생성 (Polars unpivot보다 유연) ──
    tickers: list[str] = []
    periods: list[str] = []
    periodOrders: list[int] = []
    topics: list[str] = []
    blockTypes: list[str] = []
    blockOrders: list[int] = []
    textNodeTypes: list[str | None] = []
    textLevels: list[int | None] = []
    textPaths: list[str | None] = []
    blockTexts: list[str] = []

    for row in sec.iter_rows(named=True):
        topic = row.get("topic", "")
        blockType = row.get("blockType", "text")
        blockOrder = row.get("blockOrder", 0)
        textNodeType = row.get("textNodeType")
        textLevel = row.get("textLevel")
        textPath = row.get("textPath")

        for pCol in periodCols:
            content = row.get(pCol)
            if content is None:
                continue
            text = str(content).strip()
            if not text:
                continue

            tickers.append(ticker)
            periods.append(pCol)
            periodOrders.append(_periodOrderValue(pCol))
            topics.append(topic)
            blockTypes.append(blockType)
            blockOrders.append(blockOrder)
            textNodeTypes.append(textNodeType)
            textLevels.append(textLevel)
            textPaths.append(textPath)
            blockTexts.append(text)

    if not blockTexts:
        return None

    df = pl.DataFrame(
        {
            "ticker": tickers,
            "period": periods,
            "periodOrder": periodOrders,
            "topic": topics,
            "blockType": blockTypes,
            "blockOrder": blockOrders,
            "textNodeType": textNodeTypes,
            "textLevel": textLevels,
            "textPath": textPaths,
            "blockText": blockTexts,
        },
        schema={
            "ticker": pl.Utf8,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "topic": pl.Utf8,
            "blockType": pl.Utf8,
            "blockOrder": pl.Int64,
            "textNodeType": pl.Utf8,
            "textLevel": pl.Int64,
            "textPath": pl.Utf8,
            "blockText": pl.Utf8,
        },
    )

    # 벡터 연산 — chars, cellKey, blockPriority
    df = df.with_columns(
        pl.col("blockText").str.len_chars().alias("chars"),
        (pl.col("ticker") + pl.lit(":") + pl.col("period") + pl.lit(":") + pl.col("topic")).alias("cellKey"),
    )

    # blockPriority: heading=2, table=3, text=3, semantic(heading with path)=4
    df = df.with_columns(
        pl.when(pl.col("textNodeType") == "heading")
        .then(pl.when(pl.col("textPath").is_not_null()).then(pl.lit(4)).otherwise(pl.lit(2)))
        .when(pl.col("blockType") == "table")
        .then(pl.lit(3))
        .otherwise(pl.lit(3))
        .alias("blockPriority"),
    )

    # 정렬: 최신 기간 우선, 높은 우선순위 우선, topic/block 순
    df = df.sort(
        ["periodOrder", "blockPriority", "topic", "blockOrder"],
        descending=[True, True, False, False],
    )

    return df


# ── contextSlices ────────────────────────────────────────────────


def _splitText(text: str, maxChars: int) -> list[str]:
    """텍스트를 줄 경계에서 maxChars 이내로 분할."""
    if len(text) <= maxChars:
        return [text]

    lines = text.split("\n")
    slices: list[str] = []
    current: list[str] = []
    currentLen = 0

    for line in lines:
        lineLen = len(line) + 1  # +1 for newline
        if currentLen + lineLen > maxChars and current:
            slices.append("\n".join(current))
            current = []
            currentLen = 0
        current.append(line)
        currentLen += lineLen

    if current:
        slices.append("\n".join(current))
    return slices


def _splitTable(text: str, maxChars: int) -> list[str]:
    """마크다운 테이블을 헤더 보존하며 분할."""
    if len(text) <= maxChars:
        return [text]

    lines = text.split("\n")
    # 헤더 = 첫 두 줄 (header row + separator)
    header: list[str] = []
    dataLines: list[str] = []
    for i, line in enumerate(lines):
        if i < 2 and ("|" in line or line.startswith("---")):
            header.append(line)
        else:
            dataLines.append(line)

    headerText = "\n".join(header)
    headerLen = len(headerText) + 1

    slices: list[str] = []
    current: list[str] = []
    currentLen = headerLen

    for line in dataLines:
        lineLen = len(line) + 1
        if currentLen + lineLen > maxChars and current:
            slices.append(headerText + "\n" + "\n".join(current))
            current = []
            currentLen = headerLen
        current.append(line)
        currentLen += lineLen

    if current:
        slices.append(headerText + "\n" + "\n".join(current) if header else "\n".join(current))

    return slices if slices else [text]


def contextSlices(ticker: str, *, maxChars: int = 1800) -> pl.DataFrame | None:
    """retrievalBlocks를 LLM 컨텍스트 창에 맞게 슬라이스.

    반환 컬럼:
        ticker, period, periodOrder, topic, cellKey,
        blockType, textPath, sliceIdx, sliceText, chars,
        isTable, blockPriority
    """
    blocks = retrievalBlocks(ticker)
    if blocks is None or blocks.is_empty():
        return None

    # ── slice 생성 ──
    sTickers: list[str] = []
    sPeriods: list[str] = []
    sPeriodOrders: list[int] = []
    sTopics: list[str] = []
    sCellKeys: list[str] = []
    sBlockTypes: list[str] = []
    sTextPaths: list[str | None] = []
    sSliceIdxs: list[int] = []
    sSliceTexts: list[str] = []
    sIsTables: list[bool] = []
    sBlockPriorities: list[int] = []

    for row in blocks.iter_rows(named=True):
        blockText = row["blockText"]
        blockType = row["blockType"]
        isTable = blockType == "table"

        parts = _splitTable(blockText, maxChars) if isTable else _splitText(blockText, maxChars)

        for idx, part in enumerate(parts):
            sTickers.append(row["ticker"])
            sPeriods.append(row["period"])
            sPeriodOrders.append(row["periodOrder"])
            sTopics.append(row["topic"])
            sCellKeys.append(row["cellKey"])
            sBlockTypes.append(blockType)
            sTextPaths.append(row.get("textPath"))
            sSliceIdxs.append(idx)
            sSliceTexts.append(part)
            sIsTables.append(isTable)
            sBlockPriorities.append(row["blockPriority"])

    if not sSliceTexts:
        return None

    df = pl.DataFrame(
        {
            "ticker": sTickers,
            "period": sPeriods,
            "periodOrder": sPeriodOrders,
            "topic": sTopics,
            "cellKey": sCellKeys,
            "blockType": sBlockTypes,
            "textPath": sTextPaths,
            "sliceIdx": sSliceIdxs,
            "sliceText": sSliceTexts,
            "isTable": sIsTables,
            "blockPriority": sBlockPriorities,
        },
        schema={
            "ticker": pl.Utf8,
            "period": pl.Utf8,
            "periodOrder": pl.Int64,
            "topic": pl.Utf8,
            "cellKey": pl.Utf8,
            "blockType": pl.Utf8,
            "textPath": pl.Utf8,
            "sliceIdx": pl.Int64,
            "sliceText": pl.Utf8,
            "isTable": pl.Boolean,
            "blockPriority": pl.Int64,
        },
    )

    df = df.with_columns(pl.col("sliceText").str.len_chars().alias("chars"))

    df = df.sort(
        ["periodOrder", "blockPriority", "topic", "sliceIdx"],
        descending=[True, True, False, False],
    )

    return df


# ── freq / coverage ───────────────────────────────────────────


def freq(ticker: str) -> pl.DataFrame | None:
    """topic별 기간 분포 매트릭스.

    반환 컬럼: topic, {period columns...}
    각 셀: 해당 (topic, period)에 비어있지 않은 블록 수.
    """
    from dartlab.providers.edgar.docs.sections.pipeline import sections

    sec = sections(ticker)
    if sec is None or sec.is_empty():
        return None

    periodCols = [c for c in sec.columns if _PERIOD_RE.fullmatch(c)]
    if not periodCols:
        return None

    topics = sec["topic"].unique().sort().to_list()
    rows: list[dict] = []

    for topic in topics:
        topicRows = sec.filter(pl.col("topic") == topic)
        row: dict = {"topic": topic}
        for p in periodCols:
            nonNull = topicRows[p].drop_nulls().len()
            row[p] = nonNull if nonNull > 0 else None
        rows.append(row)

    if not rows:
        return None

    df = pl.DataFrame(rows)
    sorted_periods = sortPeriods(periodCols, descending=True)
    return df.select(["topic"] + sorted_periods)


def coverage(ticker: str) -> pl.DataFrame | None:
    """topic별 커버리지 요약 — 기간 수, 블록 수, 문자 수.

    반환 컬럼: topic, periods, blocks, chars, hasText, hasTable
    """
    from dartlab.providers.edgar.docs.sections.pipeline import sections

    sec = sections(ticker)
    if sec is None or sec.is_empty():
        return None

    periodCols = [c for c in sec.columns if _PERIOD_RE.fullmatch(c)]
    if not periodCols:
        return None

    topics = sec["topic"].unique().sort().to_list()
    rows: list[dict] = []

    for topic in topics:
        topicRows = sec.filter(pl.col("topic") == topic)

        nonNullPeriods = 0
        totalChars = 0
        for p in periodCols:
            colVals = topicRows[p].drop_nulls()
            if colVals.len() > 0:
                nonNullPeriods += 1
                totalChars += sum(len(str(v)) for v in colVals.to_list())

        hasText = False
        hasTable = False
        if "blockType" in topicRows.columns:
            hasText = topicRows.filter(pl.col("blockType") == "text").height > 0
            hasTable = topicRows.filter(pl.col("blockType") == "table").height > 0

        rows.append(
            {
                "topic": topic,
                "periods": nonNullPeriods,
                "blocks": topicRows.height,
                "chars": totalChars,
                "hasText": hasText,
                "hasTable": hasTable,
            }
        )

    if not rows:
        return None

    return pl.DataFrame(rows).sort("topic")
