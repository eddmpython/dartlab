"""sections 파생 뷰 생성 helpers."""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from dartlab.engines.dart.docs.sections._common import (
    periodOrderValue,
    sortPeriods,
)
from dartlab.engines.dart.docs.sections.mapper import mapSectionTitle, stripSectionPrefix
from dartlab.engines.dart.docs.sections.pipeline import iterPeriodSubsets
from dartlab.engines.dart.docs.sections.runtime import (
    detailTopicForBlock,
    semanticTopicForBlock,
)

RE_MAJOR = re.compile(r"^([가-힣])\.\s*(.+)$")
RE_MINOR = re.compile(r"^\((\d+)\)\s*(.+)$")


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
    rows: list[dict[str, object]] = []

    for period, _reportKind, ccol, subset in iterPeriodSubsets(stockCode):
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

    periods = sortPeriods(merged.get_column("period").unique().to_list())
    wide = merged.select(["topic", "period", "rawMarkdown"]).pivot(on="period", index="topic", values="rawMarkdown")
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


_BOILERPLATE_SET = [
    "사업보고서", "분기보고서", "반기보고서", "정정신고(보고)", "ceoConfirmation",
]
_PLACEHOLDER_PHRASES = [
    "분기보고서에 기재하지 않습니다",
    "반기보고서에 기재하지 않습니다",
    "반기ㆍ사업보고서에 기재 예정",
    "반기·사업보고서에 기재 예정",
    "기업공시서식 작성기준에 따라 분기보고서에 기재하지 않습니다",
]


def _buildSemanticExpr() -> pl.Expr:
    """semanticTopicForBlock → Polars when/then 체인."""
    joined = pl.concat_str([pl.col("topic"), pl.lit("\n"), pl.col("blockLabel"), pl.lit("\n"), pl.col("blockText")])
    expr = (
        pl.when((pl.col("topic") == "audit") & joined.str.contains("감사의견|감사인|검토절차")).then(pl.lit("audit"))
        .when((pl.col("topic") == "auditSystem") & joined.str.contains("감사위원회|내부감사|내부회계|준법지원인")).then(pl.lit("auditSystem"))
        .when((pl.col("topic") == "majorHolder") & joined.str.contains("최대주주|주식소유|5%이상")).then(pl.lit("majorHolder"))
        .when((pl.col("topic") == "environmentRegulation") & joined.str.contains("환경|배출권|규제|녹색경영")).then(pl.lit("environmentRegulation"))
        .when((pl.col("topic") == "majorContractsAndRnd") & joined.str.contains("연구개발|R&D|주요계약")).then(pl.lit("majorContractsAndRnd"))
        .otherwise(pl.lit(None))
    )
    return expr


def _buildDetailExpr() -> pl.Expr:
    """detailTopicForBlock → Polars when/then 체인."""
    hay = pl.concat_str([pl.col("rawTitle"), pl.lit("\n"), pl.col("blockLabel"), pl.lit("\n"), pl.col("blockText")])
    expr = (
        pl.when((pl.col("topic") == "productService") & hay.str.contains("신탁업무\\(상세\\)", literal=False)).then(pl.lit("trustBusinessDetail"))
        .when((pl.col("topic") == "productService") & hay.str.contains("예금업무\\(상세\\)|예금상품\\(상세\\)", literal=False)).then(pl.lit("bankDepositProductDetail"))
        .when((pl.col("topic") == "productService") & hay.str.contains("대출업무\\(상세\\)|대출상품\\(상세\\)", literal=False)).then(pl.lit("bankLoanProductDetail"))
        .when((pl.col("topic") == "productService") & hay.str.contains("신용카드상품\\(상세\\)", literal=False)).then(pl.lit("cardProductDetail"))
        .when((pl.col("topic") == "productService") & hay.str.contains("상품및서비스개요\\(상세\\)", literal=False)).then(pl.lit("financialProductOverviewDetail"))
        .when((pl.col("topic") == "riskDerivative") & hay.str.contains("장내파생상품거래현황\\(상세\\)|신용파생상품상세명세\\(상세\\)", literal=False)).then(pl.lit("derivativeProductDetail"))
        .when((pl.col("topic") == "intellectualProperty") & hay.str.contains("지적재산권보유현황|주요지적재산권현황", literal=False)).then(pl.lit("ipPortfolioDetail"))
        .when((pl.col("topic") == "majorContractsAndRnd") & hay.str.contains("연구개발실적\\(", literal=False)).then(pl.lit("rndPortfolioDetail"))
        .when((pl.col("topic") == "salesOrder") & hay.str.contains("수주상황\\(상세\\)|수주현황\\(상세\\)", literal=False)).then(pl.lit("orderBacklogDetail"))
        .when((pl.col("topic") == "majorContractsAndRnd") & hay.str.contains("경영상의주요계약\\(상세\\)|경영상의주요계약\\[상세\\]", literal=False)).then(pl.lit("majorContractDetail"))
        .when((pl.col("topic") == "affiliateGroupDetail") & hay.str.contains("기업집단에소속된회사\\(상세\\)", literal=False)).then(pl.lit("affiliateCompanyDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("재고자산|inventory", literal=False)).then(pl.lit("noteInventoryDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("감가상각|depreciation", literal=False)).then(pl.lit("noteDepreciationDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("제조원가|manufacturing", literal=False)).then(pl.lit("noteManufacturingCostDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("법인세|세무|tax", literal=False)).then(pl.lit("noteTaxDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("유가증권|securities", literal=False)).then(pl.lit("noteSecuritiesDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("채권|매출채권|receivables", literal=False)).then(pl.lit("noteReceivablesDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("차입금|사채|채무|debt|borrowings", literal=False)).then(pl.lit("noteDebtDetail"))
        .when((pl.col("topic") == "financialNotes") & hay.str.contains("예금|현금|cash", literal=False)).then(pl.lit("noteCashDetail"))
        .when((pl.col("topic") == "audit") & hay.str.contains("감사보수|보수|비감사용역", literal=False)).then(pl.lit("auditFeeDetail"))
        .otherwise(pl.lit(None))
    )
    return expr


def retrievalBlocks(stockCode: str) -> pl.DataFrame:
    # 1단계: Python에서 split까지 처리 → 컬럼별 리스트 (가장 빠른 경로)
    cPeriod: list[str] = []
    cPeriodOrder: list[int] = []
    cSectionOrder: list[int] = []
    cRawTitle: list[str] = []
    cTopic: list[str] = []
    cBlockIdx: list[int] = []
    cBlockType: list[str] = []
    cBlockLabel: list[str] = []
    cBlockText: list[str] = []
    cTableLines: list[int] = []

    for period, _reportKind, ccol, subset in iterPeriodSubsets(stockCode):
        pOrder = periodOrderValue(period)
        for record in subset.to_dicts():
            rawTitle = normalizeTitle(str(record["section_title"] or ""))
            if not rawTitle:
                continue
            topic = mapSectionTitle(rawTitle)
            content = str(record[ccol] or "")
            sOrder = int(record["section_order"])
            for block in splitMarkdownBlocks(content):
                cPeriod.append(period)
                cPeriodOrder.append(pOrder)
                cSectionOrder.append(sOrder)
                cRawTitle.append(rawTitle)
                cTopic.append(topic)
                cBlockIdx.append(int(block["blockIdx"]))
                cBlockType.append(str(block["blockType"]))
                cBlockLabel.append(str(block["blockLabel"]))
                cBlockText.append(str(block["blockText"]))
                cTableLines.append(int(block["tableLines"]))

    if not cPeriod:
        return pl.DataFrame()

    # 2단계: DataFrame 생성 + 벡터 연산만 (Polars 네이티브)
    df = pl.DataFrame({
        "stockCode": pl.Series([stockCode] * len(cPeriod), dtype=pl.Utf8),
        "period": cPeriod,
        "periodOrder": cPeriodOrder,
        "sectionOrder": cSectionOrder,
        "rawTitle": cRawTitle,
        "topic": cTopic,
        "blockIdx": cBlockIdx,
        "blockType": cBlockType,
        "blockLabel": cBlockLabel,
        "blockText": cBlockText,
        "tableLines": cTableLines,
    })

    # 벡터 연산
    df = df.with_columns([
        pl.col("rawTitle").alias("sourceTopic"),
        pl.concat_str([pl.lit(stockCode + ":"), pl.col("period"), pl.lit(":"), pl.col("topic")]).alias("cellKey"),
        pl.col("blockText").str.len_chars().alias("chars"),
        pl.col("topic").is_in(_BOILERPLATE_SET).alias("isBoilerplate"),
    ])

    phExpr = pl.lit(False)
    for phrase in _PLACEHOLDER_PHRASES:
        phExpr = phExpr | pl.col("blockText").str.contains(phrase, literal=True)
    df = df.with_columns(phExpr.alias("isPlaceholder"))

    df = df.with_columns([
        _buildSemanticExpr().alias("semanticTopic"),
        _buildDetailExpr().alias("detailTopic"),
    ])

    df = df.with_columns(
        pl.when(pl.col("isBoilerplate") | pl.col("isPlaceholder")).then(0)
        .when(pl.col("detailTopic").is_not_null()).then(5)
        .when(pl.col("semanticTopic").is_not_null()).then(4)
        .when(pl.col("blockType") == "text").then(3)
        .when(pl.col("blockType") == "heading").then(2)
        .otherwise(1)
        .alias("blockPriority"),
    )

    return df.select([
        "stockCode", "period", "periodOrder", "sectionOrder", "rawTitle", "topic",
        "sourceTopic", "cellKey", "blockIdx", "blockType", "blockLabel", "blockText",
        "chars", "tableLines", "semanticTopic", "detailTopic", "isBoilerplate",
        "isPlaceholder", "blockPriority",
    ]).sort(
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
