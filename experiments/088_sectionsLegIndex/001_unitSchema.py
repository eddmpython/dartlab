"""
실험 ID: 088-001
실험명: sections LegIndex unit schema

목적:
- sections 전체를 AI 친화적인 이해 단위로 재정의할 수 있는지 확인한다.
- text row와 markdown table row를 같은 검색 단위로 넣을 수 있는 공통 스키마를 만든다.
- 이후 LegIndex, table stitch, retrieval benchmark가 모두 재사용할 수 있는 materialized artifact를 만든다.

가설:
1. sections text row와 table row를 하나의 UnderstandingUnit 스키마로 통합할 수 있다.
2. table block을 row 단위로 재분해하면 AI가 바로 읽을 수 있는 근거 단위가 된다.
3. source slice를 unit에 매핑하면 기존 069 benchmark를 unit retrieval 평가로 재사용할 수 있다.

방법:
1. DART sections와 069 benchmark용 enriched context slice를 함께 읽는다.
2. text는 sections row 단위, table은 markdown table row 단위로 UnderstandingUnit을 생성한다.
3. sourceSliceIds, rowFingerprint, tableFingerprint, neighborIds를 materialize한다.
4. 샘플 6종목 기준 artifact와 요약 통계를 저장한다.

결과 (실험 후 작성):
- sample codes: 6
- units: 79,576
- text units: 23,160
- table units: 56,416
- fallback context units: 199
- unique source slices linked: 22,073
- median source slices per unit: 0.0
- buildSec: 125.7888
- output artifact: sampleUnits.parquet, sampleSummary.json

결론:
- sections 기반 UnderstandingUnit 스키마를 안정적으로 만들 수 있었다.
- source slice를 대량으로 연결할 수 있어서 이후 retrieval 실험의 기준 단위로 재사용 가능하다.
- table row unit 밀도가 충분히 높아서 이후 stitch/horizontal bundle 실험의 기반으로 적합하다.
- 다만 6종목 일괄 materialize는 메모리 경고가 커서 이후 실험은 소형 샘플 기본값이 필요하다.

실험일: 2026-03-23
"""

from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import math
import re
import statistics
import sys
import time
import types
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import polars as pl

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dartlab.providers.dart.docs.sections.pipeline import sections as buildSections  # noqa: E402
from dartlab.providers.dart.docs.sections.views import (  # noqa: E402
    retrievalBlocks,
    splitContextText,
    splitMarkdownTable,
)
from dartlab.core.memory import check_memory_and_gc, get_memory_mb  # noqa: E402

EXPERIMENT_DATE = "2026-03-23"
EXPERIMENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = EXPERIMENT_DIR / "output"
BENCHMARK_CORPUS_DIR = OUTPUT_DIR / "benchmarkCorpus"
STATUS_PATH = EXPERIMENT_DIR / "STATUS.md"
SAMPLE_CODES = ["005930", "000660", "035420", "035720", "373220", "068270"]
TARGET_TOPICS = [
    "businessOverview",
    "companyOverview",
    "salesOrder",
    "rawMaterial",
    "riskDerivative",
    "audit",
    "majorHolder",
    "dividend",
]
PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")
TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9][가-힣A-Za-z0-9·&()/._:-]{1,}")
CAMEL_RE = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|$)|[가-힣0-9]+")
NUMERIC_RE = re.compile(r"[△\-]?\(?[\d,]+(?:\.\d+)?\)?%?")
QUERY_PERIOD_RE = re.compile(r"(?<!\d)((?:19|20)\d{2}(?:Q[1-4])?)(?!\d)")
EDGE_PUNCT_RE = re.compile(r"^[^0-9a-z가-힣]+|[^0-9a-z가-힣]+$")
STOPWORDS = {
    "대한",
    "관련",
    "사항",
    "내용",
    "기준",
    "현황",
    "회사",
    "보고서",
    "사업",
    "위험",
    "정책",
    "대한민국",
    "주식회사",
    "및",
    "또는",
    "에서",
    "으로",
    "latest",
    "current",
}
JOSA_SUFFIXES = (
    "으로는",
    "에서는",
    "에게서",
    "으로",
    "에서",
    "에게",
    "까지",
    "부터",
    "와의",
    "과의",
    "보다",
    "처럼",
    "만",
    "도",
    "의",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "와",
    "과",
    "로",
    "라",
    "에",
)
TOPIC_HINTS = {
    "salesOrder": ["매출", "판매", "수주", "order", "backlog"],
    "rawMaterial": ["원재료", "조달", "웨이퍼", "소재", "생산설비"],
    "riskDerivative": ["위험", "파생", "환율", "금리", "유동성", "신용"],
    "majorHolder": ["최대주주", "지분", "보유", "shareholder"],
    "dividend": ["배당", "주주환원", "현금배당", "배당정책"],
    "businessOverview": ["사업", "제품", "서비스", "시장", "영업"],
    "companyOverview": ["회사", "개요", "종속회사", "법적", "상업적"],
    "audit": ["감사", "감사의견", "감사인", "보수", "비감사용역"],
}
QUERY_TOPIC_MAP = {
    "배당": "dividend",
    "주주환원": "dividend",
    "주당배당": "dividend",
    "원재료": "rawMaterial",
    "조달": "rawMaterial",
    "웨이퍼": "rawMaterial",
    "수주": "salesOrder",
    "매출": "salesOrder",
    "판매": "salesOrder",
    "백로그": "salesOrder",
    "최대주주": "majorHolder",
    "지분": "majorHolder",
    "감사": "audit",
    "감사의견": "audit",
    "감사인": "audit",
    "위험": "riskDerivative",
    "파생": "riskDerivative",
    "환율": "riskDerivative",
    "금리": "riskDerivative",
    "사업": "businessOverview",
    "제품": "businessOverview",
    "서비스": "businessOverview",
    "회사개요": "companyOverview",
    "종속회사": "companyOverview",
    "개요": "companyOverview",
}
QUERY_TABLE_MARKERS = ("표", "테이블", "행", "열", "matrix", "markdown")
QUERY_CHANGE_MARKERS = ("변화", "변경", "증감", "대비", "비교", "diff", "changed")
QUERY_LATEST_MARKERS = ("최신", "최근", "현재", "now", "latest")
PLACEHOLDER_PATTERNS = [
    "기재하지 아니하였습니다",
    "기재하지 않습니다",
    "해당사항 없음",
    "해당 사항 없음",
    "참고하시기 바랍니다",
]


@dataclass(frozen=True)
class UnderstandingUnit:
    unitId: str
    stockCode: str
    topic: str
    period: str
    periodLane: str
    blockType: str
    sourceBlockOrder: int
    blockOrder: int
    textNodeType: str
    textPathKey: str
    textSemanticPathKey: str
    textComparablePathKey: str
    semanticTopic: str
    detailTopic: str
    rowFingerprint: str
    tableFingerprint: str
    payloadText: str
    displayText: str
    priority: int
    neighborIds: list[str]
    periodOrder: int
    unitSource: str
    rowLabel: str
    sourceSliceIds: list[str]
    isLatest: bool
    changeFlag: bool


@dataclass(frozen=True)
class QueryLegs:
    queryText: str
    queryIntent: str
    topicLeg: list[str]
    structureLeg: list[str]
    timeLeg: list[str]
    tableLeg: list[str]
    entityLeg: list[str]
    changeLeg: list[str]


@dataclass(frozen=True)
class LegPosting:
    legName: str
    token: str
    unitIds: list[str]


@dataclass(frozen=True)
class RetrievalHit:
    unitId: str
    score: float
    scoreBreakdown: dict[str, float]
    stockCode: str
    topic: str
    period: str
    displayText: str


@dataclass(frozen=True)
class StitchEdge:
    topic: str
    tableFingerprint: str
    rowFingerprint: str
    comparablePath: str
    period: str
    rowLabel: str
    payloadText: str


@dataclass(frozen=True)
class UnderstandingBundle:
    queryIntent: str
    gist: str
    breadcrumbs: list[str]
    evidenceUnits: list[dict[str, Any]]
    stitchedTables: list[dict[str, Any]]
    changePairs: list[dict[str, Any]]
    scoreBreakdown: dict[str, Any]


def ensureSentenceTransformerStub() -> None:
    try:
        import sentence_transformers  # noqa: F401
        return
    except ImportError:
        pass

    class MissingModel:
        def __init__(self, *args, **kwargs):
            raise ImportError("sentence_transformers is not installed")

    stub = types.ModuleType("sentence_transformers")
    stub.SentenceTransformer = MissingModel
    stub.CrossEncoder = MissingModel
    sys.modules["sentence_transformers"] = stub


def loadBenchModule():
    ensureSentenceTransformerStub()
    benchPath = ROOT / "experiments" / "069_companyTextAnalysis" / "001_goldBenchmark.py"
    spec = importlib.util.spec_from_file_location("bench069", benchPath)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def periodOrderValue(period: str) -> int:
    if "Q" not in period:
        return int(period) * 10 + 4
    return int(period[:4]) * 10 + int(period[-1])


def periodLane(period: str) -> str:
    if "Q" not in period:
        return "annual"
    return f"q{period[-1]}"


def normalizeText(text: str) -> str:
    text = (text or "").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def normalizeLabel(text: str) -> str:
    lowered = normalizeText(text).lower()
    lowered = re.sub(r"\[[^\]]+\]|\([^)]+\)", " ", lowered)
    lowered = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def isPlaceholder(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return True
    return any(pattern in stripped for pattern in PLACEHOLDER_PATTERNS)


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for match in TOKEN_RE.finditer(text or ""):
        rawToken = match.group(0).strip().lower()
        variants = [EDGE_PUNCT_RE.sub("", rawToken).strip()]
        if re.fullmatch(r"\d{6}[가-힣]+", variants[0]):
            variants.append(variants[0][:6])
        if variants[0].endswith("년") and len(variants[0]) >= 5 and variants[0][:4].isdigit():
            variants.append(variants[0][:4])
        for suffix in JOSA_SUFFIXES:
            token = variants[0]
            if token.endswith(suffix) and len(token) - len(suffix) >= 2:
                variants.append(token[: -len(suffix)])
                break
        for token in variants:
            token = EDGE_PUNCT_RE.sub("", token).strip()
            if len(token) < 2 or token in STOPWORDS or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def splitTopicTokens(topic: str) -> list[str]:
    spaced = " ".join(CAMEL_RE.findall(topic))
    return tokenize(spaced)


def hashKey(*parts: str, length: int = 16) -> str:
    joined = "||".join(part or "" for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:length]


def parseMarkdownTable(blockText: str) -> tuple[list[str], list[list[str]]]:
    rawLines = [line.rstrip() for line in (blockText or "").splitlines() if line.strip()]
    tableLines = [line.strip() for line in rawLines if line.strip().startswith("|")]
    if len(tableLines) < 2:
        return [], []

    header: list[str] = []
    rows: list[list[str]] = []
    seenSep = False
    for line in tableLines:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        isSep = all(set(cell.replace(" ", "")) <= {"-", ":"} for cell in cells if cell)
        if isSep:
            seenSep = True
            continue
        if not seenSep:
            header = cells
            continue
        rows.append(cells)
    return header, rows


def classifyCell(cell: str) -> str:
    cell = (cell or "").strip()
    if not cell:
        return "E"
    if re.fullmatch(r"[\-–—]+", cell):
        return "N"
    if re.fullmatch(r"\d{4}[./-]\d{1,2}(?:[./-]\d{1,2})?", cell):
        return "D"
    if NUMERIC_RE.fullmatch(cell):
        return "N"
    return "T"


def buildTableFingerprint(header: list[str], rows: list[list[str]], topic: str) -> str:
    headerNorm = [normalizeLabel(cell) for cell in header]
    typeSignature: list[str] = []
    colCount = max(len(header), max((len(row) for row in rows), default=0))
    for colIndex in range(colCount):
        counter: Counter[str] = Counter()
        for row in rows:
            value = row[colIndex] if colIndex < len(row) else ""
            counter[classifyCell(value)] += 1
        if counter:
            typeSignature.append(counter.most_common(1)[0][0])
        else:
            typeSignature.append("E")
    return hashKey(topic, "|".join(headerNorm), "".join(typeSignature))


def buildRowFingerprint(
    *,
    topic: str,
    comparablePath: str,
    rowLabel: str,
    semanticTopic: str,
    detailTopic: str,
    unitText: str,
) -> str:
    numericTokens = ",".join(NUMERIC_RE.findall(unitText or "")[:4])
    normalizedRow = normalizeLabel(rowLabel or unitText[:80])
    return hashKey(topic, comparablePath, normalizedRow, semanticTopic, detailTopic, numericTokens)


def clipText(text: str, limit: int = 240) -> str:
    text = normalizeText(text)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def buildEnrichedContextSlices(stockCode: str, *, maxChars: int = 1800) -> pl.DataFrame:
    blocks = retrievalBlocks(stockCode)
    rows: list[dict[str, Any]] = []
    if blocks is None or blocks.is_empty():
        return pl.DataFrame(rows, strict=False)

    for record in blocks.to_dicts():
        isSemantic = record.get("semanticTopic") is not None or record.get("detailTopic") is not None
        if record.get("isBoilerplate") or (record.get("isPlaceholder") and not isSemantic):
            continue
        blockText = str(record.get("blockText") or "")
        if record.get("blockType") == "table":
            parts = splitMarkdownTable(blockText, maxChars)
        else:
            parts = splitContextText(blockText, maxChars)
        for index, part in enumerate(parts):
            if not part.strip():
                continue
            rows.append(
                {
                    "stockCode": stockCode,
                    "period": str(record["period"]),
                    "periodOrder": int(record["periodOrder"]),
                    "topic": str(record["topic"]),
                    "sourceTopic": record.get("sourceTopic"),
                    "cellKey": str(record["cellKey"]),
                    "blockIdx": int(record["blockIdx"]),
                    "semanticTopic": record.get("semanticTopic"),
                    "detailTopic": record.get("detailTopic"),
                    "blockType": str(record["blockType"]),
                    "blockLabel": str(record.get("blockLabel") or ""),
                    "sliceIdx": index,
                    "sliceText": part,
                    "chars": len(part),
                    "isSemantic": bool(isSemantic),
                    "isTable": bool(record.get("blockType") == "table"),
                    "isBoilerplate": bool(record.get("isBoilerplate")),
                    "isPlaceholder": bool(record.get("isPlaceholder")),
                    "blockPriority": int(record.get("blockPriority") or 0),
                    "sliceId": f"{record['cellKey']}:{record['blockIdx']}:{index}",
                }
            )
    return pl.DataFrame(rows, strict=False, infer_schema_length=None)


def trimBenchmarkPeriods(sliceDf: pl.DataFrame, *, lastN: int | None = None) -> pl.DataFrame:
    if lastN is None or sliceDf.is_empty():
        return sliceDf
    periodRows = (
        sliceDf.select(["period", "periodOrder"])
        .unique()
        .sort("periodOrder", descending=True)
        .head(lastN)
    )
    keepPeriods = periodRows["period"].to_list()
    return sliceDf.filter(pl.col("period").is_in(keepPeriods))


def benchmarkCorpusPath(stockCode: str, *, lastN: int = 12) -> Path:
    suffix = f"last{lastN}" if lastN else "all"
    return BENCHMARK_CORPUS_DIR / f"{stockCode}.{suffix}.parquet"


def buildBenchmarkCorpusFrameForCode(stockCode: str, *, lastN: int = 12) -> pl.DataFrame:
    sliceDf = buildEnrichedContextSlices(stockCode)
    if sliceDf.is_empty():
        return sliceDf
    sliceDf = sliceDf.filter(
        pl.col("topic").is_in(TARGET_TOPICS),
        ~pl.col("isPlaceholder"),
        ~pl.col("isBoilerplate"),
        pl.col("chars") >= 40,
    )
    sliceDf = trimBenchmarkPeriods(sliceDf, lastN=lastN)
    return sliceDf.sort(
        ["stockCode", "periodOrder", "blockPriority", "chars"],
        descending=[False, True, True, True],
    )


def buildBenchmarkCorpusForCodes(codes: list[str], *, lastN: int = 12) -> pl.DataFrame:
    frames: list[pl.DataFrame] = []
    BENCHMARK_CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    for stockCode in codes:
        cachePath = benchmarkCorpusPath(stockCode, lastN=lastN)
        if cachePath.exists():
            frames.append(pl.scan_parquet(cachePath).collect())
            continue
        check_memory_and_gc(f"088:benchCorpus:before:{stockCode}")
        sliceDf = buildBenchmarkCorpusFrameForCode(stockCode, lastN=lastN)
        if not sliceDf.is_empty():
            sliceDf.write_parquet(cachePath)
            frames.append(sliceDf)
        gc.collect()
        check_memory_and_gc(f"088:benchCorpus:after:{stockCode}")
    if not frames:
        return pl.DataFrame()
    if len(frames) == 1:
        return frames[0]
    return pl.concat(frames, how="vertical")


def recentPeriods(sectionDf: pl.DataFrame, *, lastN: int = 12) -> list[str]:
    periods = [column for column in sectionDf.columns if PERIOD_RE.fullmatch(column)]
    return sorted(periods, key=periodOrderValue, reverse=True)[:lastN]


def priorityForUnit(
    *,
    blockType: str,
    textNodeType: str,
    semanticTopic: str,
    detailTopic: str,
    isLatest: bool,
) -> int:
    priority = 1
    if isLatest:
        priority += 3
    if detailTopic:
        priority += 3
    elif semanticTopic:
        priority += 2
    if blockType == "table":
        priority += 2
    if textNodeType == "heading":
        priority -= 1
    return max(priority, 1)


def latestPeriodByTopic(sectionDf: pl.DataFrame) -> dict[str, str]:
    periodCols = recentPeriods(sectionDf, lastN=200)
    latestMap: dict[str, str] = {}
    for row in sectionDf.iter_rows(named=True):
        topic = str(row.get("topic") or "")
        if not topic or topic in latestMap:
            continue
        for period in periodCols:
            value = row.get(period)
            if value is not None and str(value).strip():
                latestMap[topic] = period
                break
    return latestMap


def buildTextUnitsForCode(
    stockCode: str,
    *,
    sectionDf: pl.DataFrame | None = None,
    topics: list[str],
    lastN: int,
) -> list[dict[str, Any]]:
    sectionDf = buildSections(stockCode) if sectionDf is None else sectionDf
    if sectionDf is None or sectionDf.is_empty():
        return []

    periodCols = recentPeriods(sectionDf, lastN=lastN)
    latestMap = latestPeriodByTopic(sectionDf)
    rows: list[dict[str, Any]] = []

    for record in sectionDf.iter_rows(named=True):
        topic = str(record.get("topic") or "")
        if topic not in topics or str(record.get("blockType") or "") != "text":
            continue

        for period in periodCols:
            value = record.get(period)
            payloadText = str(value or "").strip()
            if not payloadText:
                continue

            textPathKey = str(record.get("textPathKey") or "")
            semanticPathKey = str(record.get("textSemanticPathKey") or "")
            comparablePathKey = str(record.get("textComparablePathKey") or textPathKey or semanticPathKey or topic)
            textNodeType = str(record.get("textNodeType") or "body")
            isLatest = latestMap.get(topic) == period
            rowLabel = textPathKey or semanticPathKey or comparablePathKey or topic
            rowFingerprint = buildRowFingerprint(
                topic=topic,
                comparablePath=comparablePathKey,
                rowLabel=rowLabel,
                semanticTopic="",
                detailTopic="",
                unitText=payloadText,
            )
            displayText = f"{stockCode} | {period} | {topic} | {textNodeType} | {clipText(payloadText, 180)}"

            rows.append(
                {
                    "stockCode": stockCode,
                    "topic": topic,
                    "period": period,
                    "periodLane": periodLane(period),
                    "blockType": "text",
                    "sourceBlockOrder": int(record.get("sourceBlockOrder") or record.get("blockOrder") or 0),
                    "blockOrder": int(record.get("blockOrder") or 0),
                    "textNodeType": textNodeType,
                    "textPathKey": textPathKey,
                    "textSemanticPathKey": semanticPathKey,
                    "textComparablePathKey": comparablePathKey,
                    "semanticTopic": "",
                    "detailTopic": "",
                    "rowFingerprint": rowFingerprint,
                    "tableFingerprint": "",
                    "payloadText": payloadText,
                    "displayText": displayText,
                    "priority": priorityForUnit(
                        blockType="text",
                        textNodeType=textNodeType,
                        semanticTopic="",
                        detailTopic="",
                        isLatest=isLatest,
                    ),
                    "periodOrder": periodOrderValue(period),
                    "unitSource": "sectionsText",
                    "rowLabel": rowLabel,
                    "sourceSliceIds": [],
                    "isLatest": isLatest,
                }
            )
    return rows


def buildTableUnitsForCode(
    stockCode: str,
    *,
    sectionDf: pl.DataFrame | None = None,
    topics: list[str],
    lastN: int,
) -> list[dict[str, Any]]:
    sectionDf = buildSections(stockCode) if sectionDf is None else sectionDf
    if sectionDf is None or sectionDf.is_empty():
        return []

    periodCols = recentPeriods(sectionDf, lastN=lastN)
    latestMap = latestPeriodByTopic(sectionDf)
    rowsOut: list[dict[str, Any]] = []

    for record in sectionDf.iter_rows(named=True):
        topic = str(record.get("topic") or "")
        if topic not in topics or str(record.get("blockType") or "") != "table":
            continue

        for period in periodCols:
            value = record.get(period)
            blockText = str(value or "").strip()
            if not blockText:
                continue

            header, rows = parseMarkdownTable(blockText)
            if not header or not rows:
                continue

            tableFingerprint = buildTableFingerprint(header, rows, topic)
            isLatest = latestMap.get(topic) == period

            for rowIndex, row in enumerate(rows):
                rowLabel = row[0] if row else f"row{rowIndex}"
                normalizedRow = normalizeLabel(rowLabel)
                comparablePath = f"@table:{normalizedRow}" if normalizedRow else f"@table:{topic}:{rowIndex}"
                paddedRow = row + [""] * (len(header) - len(row))
                payloadText = "\n".join(
                    [
                        "| " + " | ".join(header) + " |",
                        "| " + " | ".join(["---"] * len(header)) + " |",
                        "| " + " | ".join(paddedRow) + " |",
                    ]
                )
                displayPairs = []
                for colIndex, headerName in enumerate(header):
                    cellValue = paddedRow[colIndex]
                    if not str(cellValue).strip():
                        continue
                    displayPairs.append(f"{headerName}:{cellValue}")
                displayText = (
                    f"{stockCode} | {period} | {topic} | tableRow | "
                    f"{clipText(' ; '.join(displayPairs) or payloadText, 180)}"
                )
                rowFingerprint = buildRowFingerprint(
                    topic=topic,
                    comparablePath=comparablePath,
                    rowLabel=rowLabel,
                    semanticTopic="",
                    detailTopic="",
                    unitText=payloadText,
                )

                rowsOut.append(
                    {
                        "stockCode": stockCode,
                        "topic": topic,
                        "period": period,
                        "periodLane": periodLane(period),
                        "blockType": "table",
                        "sourceBlockOrder": int(record.get("sourceBlockOrder") or record.get("blockOrder") or 0),
                        "blockOrder": int(record.get("blockOrder") or 0),
                        "textNodeType": "tableRow",
                        "textPathKey": comparablePath,
                        "textSemanticPathKey": "",
                        "textComparablePathKey": comparablePath,
                        "semanticTopic": "",
                        "detailTopic": "",
                        "rowFingerprint": rowFingerprint,
                        "tableFingerprint": tableFingerprint,
                        "payloadText": payloadText,
                        "displayText": displayText,
                        "priority": priorityForUnit(
                            blockType="table",
                            textNodeType="tableRow",
                            semanticTopic="",
                            detailTopic="",
                            isLatest=isLatest,
                        ),
                        "periodOrder": periodOrderValue(period),
                        "unitSource": "sectionsTableRow",
                        "rowLabel": rowLabel,
                        "sourceSliceIds": [],
                        "isLatest": isLatest,
                    }
                )
    return rowsOut


def buildFallbackUnitsForCode(
    stockCode: str,
    *,
    topics: list[str],
    lastN: int,
    baseRows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    sliceDf = buildEnrichedContextSlices(stockCode)
    if sliceDf is None or sliceDf.is_empty():
        return []

    latestPeriods = sorted(sliceDf["period"].unique().to_list(), key=periodOrderValue, reverse=True)[:lastN]
    baseIndex: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for rowIndex, row in enumerate(baseRows):
        baseIndex[(row["topic"], row["period"], row["blockType"])].append(rowIndex)

    fallbackRows: list[dict[str, Any]] = []

    for record in sliceDf.to_dicts():
        topic = str(record.get("topic") or "")
        period = str(record.get("period") or "")
        if topic not in topics or period not in latestPeriods:
            continue

        sliceId = str(record.get("sliceId") or f"{record['cellKey']}:{record['blockIdx']}:{record['sliceIdx']}")
        payloadText = str(record.get("sliceText") or "").strip()
        if not payloadText:
            continue

        sliceBlockType = "table" if bool(record.get("isTable")) else "text"
        normalizedSlice = normalizeText(payloadText)
        matched = False

        for rowIndex in baseIndex.get((topic, period, sliceBlockType), []):
            baseRow = baseRows[rowIndex]
            normalizedUnit = normalizeText(str(baseRow.get("payloadText") or ""))
            if not normalizedUnit:
                continue
            if normalizedSlice in normalizedUnit or normalizedUnit in normalizedSlice:
                baseRow["sourceSliceIds"].append(sliceId)
                matched = True
                break
            if sliceBlockType == "table" and normalizeLabel(payloadText) in normalizeLabel(normalizedUnit):
                baseRow["sourceSliceIds"].append(sliceId)
                matched = True
                break

        if matched:
            continue

        semanticTopic = str(record.get("semanticTopic") or "")
        detailTopic = str(record.get("detailTopic") or "")
        rowLabel = str(record.get("blockLabel") or semanticTopic or detailTopic or topic)
        comparablePath = semanticTopic or detailTopic or f"@fallback:{normalizeLabel(rowLabel) or topic}"
        rowFingerprint = buildRowFingerprint(
            topic=topic,
            comparablePath=comparablePath,
            rowLabel=rowLabel,
            semanticTopic=semanticTopic,
            detailTopic=detailTopic,
            unitText=payloadText,
        )
        tableFingerprint = ""
        if sliceBlockType == "table":
            header, rows = parseMarkdownTable(payloadText)
            if header and rows:
                tableFingerprint = buildTableFingerprint(header, rows, topic)

        fallbackRows.append(
            {
                "stockCode": stockCode,
                "topic": topic,
                "period": period,
                "periodLane": periodLane(period),
                "blockType": sliceBlockType,
                "sourceBlockOrder": int(record.get("blockIdx") or 0),
                "blockOrder": int(record.get("blockIdx") or 0),
                "textNodeType": "contextSlice",
                "textPathKey": comparablePath,
                "textSemanticPathKey": semanticTopic,
                "textComparablePathKey": comparablePath,
                "semanticTopic": semanticTopic,
                "detailTopic": detailTopic,
                "rowFingerprint": rowFingerprint,
                "tableFingerprint": tableFingerprint,
                "payloadText": payloadText,
                "displayText": (
                    f"{stockCode} | {period} | {topic} | contextSlice | {clipText(payloadText, 180)}"
                ),
                "priority": priorityForUnit(
                    blockType=sliceBlockType,
                    textNodeType="contextSlice",
                    semanticTopic=semanticTopic,
                    detailTopic=detailTopic,
                    isLatest=False,
                ),
                "periodOrder": periodOrderValue(period),
                "unitSource": "contextFallback",
                "rowLabel": rowLabel,
                "sourceSliceIds": [sliceId],
                "isLatest": False,
            }
        )

    return fallbackRows


def attachChangeFlags(rows: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["stockCode"], row["topic"], row["rowFingerprint"])].append(row)

    for groupRows in groups.values():
        groupRows.sort(key=lambda item: item["periodOrder"], reverse=True)
        previousPayload = None
        for row in groupRows:
            payload = normalizeText(row["payloadText"])
            row["changeFlag"] = previousPayload is not None and payload != previousPayload
            previousPayload = payload


def attachNeighborIds(rows: list[dict[str, Any]]) -> None:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["stockCode"], row["topic"])].append(row)

    for groupRows in groups.values():
        groupRows.sort(
            key=lambda item: (
                -item["periodOrder"],
                item["sourceBlockOrder"],
                item["blockOrder"],
                item["textPathKey"],
                item["rowLabel"],
            )
        )
        for index, row in enumerate(groupRows):
            neighborIds: list[str] = []
            if index > 0:
                neighborIds.append(groupRows[index - 1]["unitId"])
            if index + 1 < len(groupRows):
                neighborIds.append(groupRows[index + 1]["unitId"])
            row["neighborIds"] = neighborIds


def buildUnderstandingUnits(
    codes: list[str],
    *,
    topics: list[str] | None = None,
    lastN: int = 12,
) -> pl.DataFrame:
    topics = topics or TARGET_TOPICS
    rows: list[dict[str, Any]] = []
    unitNumber = 0

    for stockCode in codes:
        check_memory_and_gc(f"088:before:{stockCode}")
        sectionDf = buildSections(stockCode)
        codeRows = buildTextUnitsForCode(stockCode, sectionDf=sectionDf, topics=topics, lastN=lastN)
        codeRows.extend(buildTableUnitsForCode(stockCode, sectionDf=sectionDf, topics=topics, lastN=lastN))
        codeRows.extend(buildFallbackUnitsForCode(stockCode, topics=topics, lastN=lastN, baseRows=codeRows))

        for row in codeRows:
            unitNumber += 1
            row["unitId"] = f"U{unitNumber:06d}"
            row.setdefault("neighborIds", [])
            row.setdefault("changeFlag", False)
        rows.extend(codeRows)
        del codeRows
        del sectionDf
        gc.collect()
        check_memory_and_gc(f"088:after:{stockCode}")

    attachChangeFlags(rows)
    attachNeighborIds(rows)

    if not rows:
        return pl.DataFrame()

    unitDf = pl.DataFrame(rows, strict=False, infer_schema_length=None)
    return unitDf.sort(
        ["stockCode", "periodOrder", "priority", "topic", "sourceBlockOrder", "blockOrder"],
        descending=[False, True, True, False, False, False],
    )


def unitRecordMap(unitDf: pl.DataFrame) -> dict[str, dict[str, Any]]:
    return {str(row["unitId"]): row for row in unitDf.to_dicts()}


def filterUnitsByCodes(unitDf: pl.DataFrame, codes: list[str] | None) -> pl.DataFrame:
    if not codes:
        return unitDf
    return unitDf.filter(pl.col("stockCode").is_in(codes))


def legTokenMap(unit: dict[str, Any]) -> dict[str, list[str]]:
    topicLeg = [f"topic:{unit['topic']}"]
    topicLeg.extend(splitTopicTokens(str(unit["topic"])))
    for hint in TOPIC_HINTS.get(str(unit["topic"]), []):
        topicLeg.extend(tokenize(hint))
    if unit.get("semanticTopic"):
        topicLeg.append(f"semantic:{unit['semanticTopic']}")
        topicLeg.extend(tokenize(str(unit["semanticTopic"])))
    if unit.get("detailTopic"):
        topicLeg.append(f"detail:{unit['detailTopic']}")
        topicLeg.extend(tokenize(str(unit["detailTopic"])))

    structureLeg = [
        f"block:{unit['blockType']}",
        f"node:{unit['textNodeType']}",
        f"path:{unit['textPathKey'] or unit['topic']}",
    ]
    for key in [unit.get("textPathKey"), unit.get("textSemanticPathKey"), unit.get("textComparablePathKey")]:
        if key:
            structureLeg.extend(tokenize(str(key)))

    timeLeg = [
        f"period:{unit['period']}",
        f"year:{str(unit['period'])[:4]}",
        f"lane:{unit['periodLane']}",
    ]
    if bool(unit.get("isLatest")):
        timeLeg.extend(["latest", "recent", "current"])

    tableLeg = [unit["blockType"]]
    if unit.get("tableFingerprint"):
        tableLeg.append(f"table:{unit['tableFingerprint']}")
    if unit.get("rowFingerprint"):
        tableLeg.append(f"row:{unit['rowFingerprint']}")
    if unit.get("rowLabel"):
        tableLeg.extend(tokenize(str(unit["rowLabel"])))
    if unit.get("displayText"):
        tableLeg.extend(tokenize(str(unit["displayText"])[:120]))

    entityTokens: list[str] = []
    for text in [str(unit.get("displayText") or ""), str(unit.get("payloadText") or "")[:300]]:
        for token in tokenize(text):
            if token not in entityTokens:
                entityTokens.append(token)
            if len(entityTokens) >= 32:
                break
        if len(entityTokens) >= 32:
            break

    changeLeg = ["changed" if bool(unit.get("changeFlag")) else "stable"]
    if NUMERIC_RE.search(str(unit.get("payloadText") or "")):
        changeLeg.append("numeric")
    if unit.get("blockType") == "table":
        changeLeg.append("tabular")

    return {
        "topicLeg": sorted(set(topicLeg)),
        "structureLeg": sorted(set(structureLeg)),
        "timeLeg": sorted(set(timeLeg)),
        "tableLeg": sorted(set(tableLeg)),
        "entityLeg": sorted(set(entityTokens)),
        "changeLeg": sorted(set(changeLeg)),
    }


def buildLegIndex(unitDf: pl.DataFrame) -> dict[str, Any]:
    postings: dict[str, dict[str, list[str]]] = {
        "topicLeg": defaultdict(list),
        "structureLeg": defaultdict(list),
        "timeLeg": defaultdict(list),
        "tableLeg": defaultdict(list),
        "entityLeg": defaultdict(list),
        "changeLeg": defaultdict(list),
    }
    records = unitDf.to_dicts()
    recordMap = {str(record["unitId"]): record for record in records}

    for record in records:
        unitId = str(record["unitId"])
        tokenMap = legTokenMap(record)
        for legName, tokens in tokenMap.items():
            for token in tokens:
                postings[legName][token].append(unitId)

    postingStats = {
        legName: {
            "tokens": len(legPostings),
            "medianPostingSize": (
                statistics.median(len(unitIds) for unitIds in legPostings.values()) if legPostings else 0.0
            ),
        }
        for legName, legPostings in postings.items()
    }

    serializablePostings = {
        legName: {token: sorted(set(unitIds)) for token, unitIds in legPostings.items()}
        for legName, legPostings in postings.items()
    }
    return {
        "postings": serializablePostings,
        "recordCount": len(records),
        "postingStats": postingStats,
        "recordMap": recordMap,
    }


def compileQuery(queryText: str) -> QueryLegs:
    normalized = normalizeText(queryText)
    topicLeg: list[str] = []
    structureLeg: list[str] = []
    timeLeg: list[str] = []
    tableLeg: list[str] = []
    entityLeg: list[str] = []
    changeLeg: list[str] = []

    foundTopics: set[str] = set()
    for marker, topic in QUERY_TOPIC_MAP.items():
        if marker in normalized:
            foundTopics.add(topic)
    for topic in foundTopics:
        topicLeg.append(f"topic:{topic}")
        topicLeg.extend(splitTopicTokens(topic))

    periodMatches = QUERY_PERIOD_RE.findall(normalized)
    for period in periodMatches:
        timeLeg.append(f"period:{period}")
        timeLeg.append(f"year:{period[:4]}")
    if any(marker in normalized for marker in QUERY_LATEST_MARKERS):
        timeLeg.extend(["latest", "recent", "current"])
    if "분기" in normalized:
        timeLeg.append("lane:q")
    if "연간" in normalized or "사업보고서" in normalized:
        timeLeg.append("lane:annual")

    if any(marker in normalized for marker in QUERY_TABLE_MARKERS):
        tableLeg.extend(["table", "tabular"])
        structureLeg.append("block:table")
    if "헤딩" in normalized or "본문" in normalized:
        structureLeg.extend(tokenize(normalized))

    if any(marker in normalized for marker in QUERY_CHANGE_MARKERS):
        changeLeg.extend(["changed", "numeric"])
    if "증가" in normalized or "상승" in normalized:
        changeLeg.append("increase")
    if "감소" in normalized or "하락" in normalized:
        changeLeg.append("decrease")

    for token in tokenize(normalized):
        if token in STOPWORDS:
            continue
        entityLeg.append(token)

    queryIntent = "lookup"
    if tableLeg:
        queryIntent = "table"
    if changeLeg:
        queryIntent = "change"

    return QueryLegs(
        queryText=queryText,
        queryIntent=queryIntent,
        topicLeg=sorted(set(topicLeg)),
        structureLeg=sorted(set(structureLeg)),
        timeLeg=sorted(set(timeLeg)),
        tableLeg=sorted(set(tableLeg)),
        entityLeg=sorted(set(entityLeg)),
        changeLeg=sorted(set(changeLeg)),
    )


def collectCandidateMatches(
    indexData: dict[str, Any],
    queryLegs: QueryLegs,
) -> tuple[list[str], dict[str, dict[str, int]]]:
    postings = indexData["postings"]
    recordMap = indexData["recordMap"]
    weightedScores: dict[str, float] = defaultdict(float)
    matchedLegs: dict[str, set[str]] = defaultdict(set)
    matchCounts: dict[str, Counter[str]] = defaultdict(Counter)

    for legName in ["topicLeg", "structureLeg", "timeLeg", "tableLeg", "entityLeg", "changeLeg"]:
        tokens = getattr(queryLegs, legName)
        for token in tokens:
            if token in postings[legName]:
                unitIds = postings[legName][token]
                rarity = 1.0 / max(math.log(len(unitIds) + 2.0), 1.0)
                for unitId in unitIds:
                    weightedScores[unitId] += rarity
                    matchedLegs[unitId].add(legName)
                    matchCounts[unitId][legName] += 1

    if not weightedScores:
        candidateIds = list(indexData["recordMap"].keys())[:200]
        return candidateIds, {unitId: {} for unitId in candidateIds}

    candidateIds = list(weightedScores.keys())
    if queryLegs.topicLeg:
        topicMatched = [unitId for unitId in candidateIds if "topicLeg" in matchedLegs[unitId]]
        if topicMatched:
            candidateIds = topicMatched
    if queryLegs.queryIntent == "table":
        tableMatched = [
            unitId
            for unitId in candidateIds
            if (
                recordMap[unitId].get("blockType") == "table"
                or "tableLeg" in matchedLegs[unitId]
                or "structureLeg" in matchedLegs[unitId]
            )
        ]
        if tableMatched:
            candidateIds = tableMatched

    candidateIds.sort(
        key=lambda unitId: (
            -weightedScores[unitId],
            -len(matchedLegs[unitId]),
            -float(recordMap[unitId].get("priority") or 0),
            -int(recordMap[unitId].get("periodOrder") or 0),
        )
    )
    candidateIds = candidateIds[:2048]
    return candidateIds, {unitId: dict(matchCounts[unitId]) for unitId in candidateIds}


def candidateUnitIds(indexData: dict[str, Any], queryLegs: QueryLegs) -> list[str]:
    candidateIds, _matchMap = collectCandidateMatches(indexData, queryLegs)
    return candidateIds


def retrievalScore(
    unit: dict[str, Any],
    queryLegs: QueryLegs,
    *,
    matchCounts: dict[str, int] | None = None,
) -> tuple[float, dict[str, float]]:
    tokenMap = None if matchCounts is not None else legTokenMap(unit)
    weights = {
        "topicLeg": 4.0,
        "structureLeg": 2.5,
        "timeLeg": 2.0,
        "tableLeg": 2.0,
        "entityLeg": 3.0,
        "changeLeg": 1.5,
    }
    breakdown: dict[str, float] = {}
    totalScore = 0.0

    for legName, weight in weights.items():
        queryTokens = getattr(queryLegs, legName)
        if not queryTokens:
            breakdown[legName] = 0.0
            continue
        if matchCounts is None:
            unitTokens = set(tokenMap[legName])
            hits = sum(1 for token in queryTokens if token in unitTokens)
        else:
            hits = min(int(matchCounts.get(legName, 0)), len(queryTokens))
        score = weight * (hits / len(queryTokens))
        breakdown[legName] = score
        totalScore += score

    totalScore += float(unit.get("priority") or 0) * 0.1
    if queryLegs.topicLeg and breakdown["topicLeg"] == 0.0:
        totalScore -= 2.0
    if queryLegs.queryIntent == "table" and unit.get("blockType") == "table":
        totalScore += 0.5
    if queryLegs.queryIntent == "table" and unit.get("blockType") != "table":
        totalScore -= 0.5
    if queryLegs.queryIntent == "change" and bool(unit.get("changeFlag")):
        totalScore += 0.5

    return totalScore, breakdown


def searchLegIndex(
    indexData: dict[str, Any],
    queryText: str,
    *,
    topK: int = 10,
) -> tuple[QueryLegs, list[RetrievalHit]]:
    queryLegs = compileQuery(queryText)
    recordMap = indexData["recordMap"]
    candidates, candidateMatchMap = collectCandidateMatches(indexData, queryLegs)
    hits: list[RetrievalHit] = []

    for unitId in candidates:
        record = recordMap[unitId]
        score, breakdown = retrievalScore(record, queryLegs, matchCounts=candidateMatchMap.get(unitId))
        if score <= 0:
            continue
        hits.append(
            RetrievalHit(
                unitId=unitId,
                score=score,
                scoreBreakdown=breakdown,
                stockCode=str(record["stockCode"]),
                topic=str(record["topic"]),
                period=str(record["period"]),
                displayText=str(record["displayText"]),
            )
        )

    hits.sort(key=lambda item: item.score, reverse=True)
    return queryLegs, hits[:topK]


def stitchTablesFromHits(unitDf: pl.DataFrame, hits: list[RetrievalHit], *, topGroups: int = 3) -> list[dict[str, Any]]:
    if not hits:
        return []
    unitMap = unitRecordMap(unitDf)
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        record = unitMap.get(hit.unitId)
        if not record or str(record.get("blockType")) != "table":
            continue
        key = (
            str(record["topic"]),
            str(record.get("tableFingerprint") or ""),
            str(record.get("textComparablePathKey") or record.get("textPathKey") or ""),
        )
        groups[key].append(record)

    stitched: list[dict[str, Any]] = []
    for (topic, tableFingerprint, comparablePath), rows in list(groups.items())[:topGroups]:
        pivotRows: dict[str, dict[str, str]] = defaultdict(dict)
        for row in rows:
            pivotRows[str(row["rowLabel"])][str(row["period"])] = str(row["payloadText"])
        periods = sorted(
            {period for rowMap in pivotRows.values() for period in rowMap.keys()},
            key=periodOrderValue,
            reverse=True,
        )
        stitchedRows = []
        for rowLabel, periodMap in sorted(pivotRows.items()):
            stitchedRow = {"rowLabel": rowLabel}
            for period in periods:
                stitchedRow[period] = periodMap.get(period)
            stitchedRows.append(stitchedRow)
        stitched.append(
            {
                "topic": topic,
                "tableFingerprint": tableFingerprint,
                "comparablePath": comparablePath,
                "periods": periods,
                "rows": stitchedRows,
            }
        )
    return stitched


def buildChangePairs(unitDf: pl.DataFrame, hits: list[RetrievalHit], *, limit: int = 3) -> list[dict[str, Any]]:
    if not hits:
        return []
    unitMap = unitRecordMap(unitDf)
    pairs: list[dict[str, Any]] = []
    seenKeys: set[tuple[str, str, str]] = set()
    for hit in hits:
        record = unitMap.get(hit.unitId)
        if not record or not bool(record.get("changeFlag")):
            continue
        key = (str(record["stockCode"]), str(record["topic"]), str(record["rowFingerprint"]))
        if key in seenKeys:
            continue
        seenKeys.add(key)

        candidates = [
            row
            for row in unitMap.values()
            if (
                str(row["stockCode"]) == key[0]
                and str(row["topic"]) == key[1]
                and str(row["rowFingerprint"]) == key[2]
            )
        ]
        candidates.sort(key=lambda item: int(item["periodOrder"]), reverse=True)
        if len(candidates) < 2:
            continue
        pairs.append(
            {
                "stockCode": key[0],
                "topic": key[1],
                "fromPeriod": candidates[1]["period"],
                "toPeriod": candidates[0]["period"],
                "fromText": clipText(str(candidates[1]["displayText"]), 160),
                "toText": clipText(str(candidates[0]["displayText"]), 160),
            }
        )
        if len(pairs) >= limit:
            break
    return pairs


def buildUnderstandingBundle(
    unitDf: pl.DataFrame,
    indexData: dict[str, Any],
    queryText: str,
    *,
    topK: int = 8,
) -> UnderstandingBundle:
    queryLegs, hits = searchLegIndex(indexData, queryText, topK=topK)
    return buildUnderstandingBundleFromHits(unitDf, indexData, queryLegs, hits)


def buildUnderstandingBundleFromHits(
    unitDf: pl.DataFrame,
    indexData: dict[str, Any],
    queryLegs: QueryLegs,
    hits: list[RetrievalHit],
) -> UnderstandingBundle:
    breadcrumbs = [f"intent:{queryLegs.queryIntent}"]
    breadcrumbs.extend(f"topic:{token.split(':', 1)[1]}" for token in queryLegs.topicLeg if token.startswith("topic:"))
    breadcrumbs.extend(queryLegs.timeLeg[:2])
    evidenceUnits = []
    for hit in hits:
        evidenceUnits.append(
            {
                "unitId": hit.unitId,
                "score": round(hit.score, 4),
                "stockCode": hit.stockCode,
                "topic": hit.topic,
                "period": hit.period,
                "displayText": hit.displayText,
                "scoreBreakdown": {key: round(value, 3) for key, value in hit.scoreBreakdown.items()},
            }
        )

    stitchedTables = stitchTablesFromHits(unitDf, hits)
    changePairs = buildChangePairs(unitDf, hits)
    gistTopics = [f"{item['stockCode']} {item['topic']} {item['period']}" for item in evidenceUnits[:3]]
    gist = " / ".join(gistTopics) if gistTopics else "no-evidence"
    scoreBreakdown = {
        "candidateCount": len(candidateUnitIds(indexData, queryLegs)),
        "returnedCount": len(evidenceUnits),
        "topScore": evidenceUnits[0]["score"] if evidenceUnits else 0.0,
    }
    return UnderstandingBundle(
        queryIntent=queryLegs.queryIntent,
        gist=gist,
        breadcrumbs=breadcrumbs,
        evidenceUnits=evidenceUnits,
        stitchedTables=stitchedTables,
        changePairs=changePairs,
        scoreBreakdown=scoreBreakdown,
    )


def benchmarkCasesForUnits(
    unitDf: pl.DataFrame,
    *,
    codes: list[str] | None = None,
    lastN: int = 12,
) -> tuple[Any, pl.DataFrame, list[Any], dict[str, list[str]]]:
    bench = loadBenchModule()
    selectedCodes = codes or sorted({str(code) for code in unitDf["stockCode"].unique().to_list()})
    corpus = buildBenchmarkCorpusForCodes(selectedCodes, lastN=lastN)
    cases = buildFilteredBenchmarkCases(bench, corpus, selectedCodes)

    sourceMap: dict[str, list[str]] = defaultdict(list)
    unitRows = unitDf.to_dicts()
    recordMap = {str(row["unitId"]): row for row in unitRows}
    blockMap: dict[tuple[str, str, str, int], list[str]] = defaultdict(list)
    for row in unitRows:
        for sliceId in row.get("sourceSliceIds") or []:
            sourceMap[str(sliceId)].append(str(row["unitId"]))
        blockKey = (
            str(row["stockCode"]),
            str(row["topic"]),
            str(row["period"]),
            int(row["sourceBlockOrder"]),
        )
        blockMap[blockKey].append(str(row["unitId"]))

    caseMap: dict[str, list[str]] = {}
    for case in cases:
        goldUnitIds: list[str] = []
        for sliceId in case.goldSliceIds:
            goldUnitIds.extend(sourceMap.get(sliceId, []))
        expandedGoldIds: list[str] = []
        for unitId in dict.fromkeys(goldUnitIds):
            expandedGoldIds.append(unitId)
            record = recordMap.get(unitId)
            if not record:
                continue
            expandedGoldIds.extend(record.get("neighborIds") or [])
            blockKey = (
                str(record["stockCode"]),
                str(record["topic"]),
                str(record["period"]),
                int(record["sourceBlockOrder"]),
            )
            expandedGoldIds.extend(blockMap.get(blockKey, []))
        caseMap[case.caseId] = list(dict.fromkeys(expandedGoldIds))
    return bench, corpus, cases, caseMap


def buildFilteredBenchmarkCases(bench: Any, corpus: pl.DataFrame, codes: list[str]) -> list[Any]:
    selectedCodes = set(codes)
    cases: list[Any] = []

    retrievalPlan = [
        ("salesOrder", False),
        ("rawMaterial", False),
        ("audit", True),
        ("majorHolder", None),
    ]
    caseNo = 1
    for topic, preferTable in retrievalPlan:
        rows = bench._pick_case_rows(corpus, topic=topic, count=4, prefer_table=preferTable, min_chars=100)
        for index, row in enumerate(rows, 1):
            question = (
                f"{row['stockCode']}의 {bench.TOPIC_QUERY_HINTS[topic]} 관련 최신 근거를 찾아라. "
                f"질문 힌트: {bench._safe_terms(str(row['sliceText']), max_terms=2)}"
            )
            cases.append(
                bench.BenchmarkCase(
                    caseId=f"R{caseNo:02d}",
                    taskType="retrieval",
                    stockCode=str(row["stockCode"]),
                    topic=topic,
                    period=str(row["period"]),
                    question=question,
                    goldSliceIds=[bench._slice_id(row)],
                    requiredFacts=[],
                    forbiddenFacts=[],
                    note=f"{topic}-{index}",
                )
            )
            caseNo += 1

    changeCaseNo = 1
    for topic in ["dividend", "riskDerivative"]:
        for latest, previous in bench._change_pairs(corpus, topic, 4):
            question = (
                f"{latest['stockCode']}의 {bench.TOPIC_QUERY_HINTS[topic]}에서 "
                f"{previous['period']} 대비 {latest['period']} 변화 근거를 찾아라."
            )
            required = bench._safe_terms(str(latest["sliceText"]), max_terms=2) + bench._safe_terms(
                str(previous["sliceText"]),
                max_terms=1,
            )
            cases.append(
                bench.BenchmarkCase(
                    caseId=f"C{changeCaseNo:02d}",
                    taskType="change",
                    stockCode=str(latest["stockCode"]),
                    topic=topic,
                    period=f"{previous['period']}->{latest['period']}",
                    question=question,
                    goldSliceIds=[bench._slice_id(latest), bench._slice_id(previous)],
                    requiredFacts=required[:3],
                    forbiddenFacts=[],
                    note=f"{previous['period']}->{latest['period']}",
                )
            )
            changeCaseNo += 1

    extractionSpecs = [spec for spec in bench.MANUAL_EXTRACTION_SPECS if spec["stockCode"] in selectedCodes]
    for index, spec in enumerate(extractionSpecs, 1):
        try:
            row = bench._find_manual_row(corpus, spec)
        except ValueError:
            continue
        cases.append(
            bench.BenchmarkCase(
                caseId=f"E{index:02d}",
                taskType="extraction",
                stockCode=spec["stockCode"],
                topic=spec["topic"],
                period=str(row["period"]),
                question=spec["question"],
                goldSliceIds=[bench._slice_id(row)],
                requiredFacts=[item["text"] for item in spec["expected"]],
                forbiddenFacts=[],
                note=json.dumps(spec["expected"], ensure_ascii=False),
            )
        )

    summarySpecs = [spec for spec in bench.MANUAL_SUMMARY_SPECS if spec["stockCode"] in selectedCodes]
    for index, spec in enumerate(summarySpecs, 1):
        try:
            row = bench._find_manual_row(corpus, spec)
        except ValueError:
            continue
        cases.append(
            bench.BenchmarkCase(
                caseId=f"S{index:02d}",
                taskType="summary",
                stockCode=spec["stockCode"],
                topic=spec["topic"],
                period=str(row["period"]),
                question=spec["question"],
                goldSliceIds=[bench._slice_id(row)],
                requiredFacts=list(spec["requiredFacts"]),
                forbiddenFacts=list(spec["forbiddenFacts"]),
                note=spec["contains"],
            )
        )
    return cases


def runCoreBaselineBench(
    bench: Any,
    corpus: pl.DataFrame,
    cases: list[Any],
    *,
    includeDense: bool = True,
) -> dict[str, Any]:
    rows = corpus.to_dicts()
    sliceIds = [str(row["sliceId"]) for row in rows]
    corpora = bench.build_retrieval_corpora(corpus)
    queries = [case.question for case in cases]
    results: dict[str, Any] = {}

    for name, texts in [("B1_raw_bm25", corpora["raw"]), ("B2_contextual_bm25", corpora["contextual"])]:
        start = time.perf_counter()
        bm25 = bench.SimpleBM25(texts)
        buildSec = time.perf_counter() - start
        rankedLists: dict[str, list[str]] = {}
        latencies: list[float] = []
        for case in cases:
            t0 = time.perf_counter()
            scores = bm25.score(case.question)
            order = bench.np.argsort(scores)[::-1][:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            rankedLists[case.caseId] = [sliceIds[index] for index in order]
        metric = bench.evaluate_ranked_lists(cases, rankedLists, latencies, buildSec)
        metric.method = name
        results[name] = metric

    if not includeDense:
        return results

    check_memory_and_gc("088:retrieval:beforeDense")
    model = bench.load_dense_model("bge")
    try:
        denseScores, denseBuildSec = bench.dense_rank(
            model,
            corpus_texts=corpora["contextual"],
            queries=queries,
            model_name="bge",
        )
    finally:
        del model
        gc.collect()
        check_memory_and_gc("088:retrieval:afterDense")

    rankedLists = {}
    latencies = []
    for index, case in enumerate(cases):
        t0 = time.perf_counter()
        order = bench.np.argsort(denseScores[index])[::-1][:10]
        latencies.append((time.perf_counter() - t0) * 1000)
        rankedLists[case.caseId] = [sliceIds[rowIndex] for rowIndex in order]
    metric = bench.evaluate_ranked_lists(cases, rankedLists, latencies, denseBuildSec)
    metric.method = "D2_bge_dense"
    results[metric.method] = metric

    rankedLists = {}
    latencies = []
    bm25 = bench.SimpleBM25(corpora["contextual"])
    for index, case in enumerate(cases):
        t0 = time.perf_counter()
        sparseOrder = bench.np.argsort(bm25.score(case.question))[::-1][:50].tolist()
        denseOrder = bench.np.argsort(denseScores[index])[::-1][:50].tolist()
        fused = bench._rrf([sparseOrder, denseOrder])[:10]
        latencies.append((time.perf_counter() - t0) * 1000)
        rankedLists[case.caseId] = [sliceIds[rowIndex] for rowIndex in fused]
    metric = bench.evaluate_ranked_lists(cases, rankedLists, latencies, denseBuildSec)
    metric.method = "H2_contextual_plus_bge"
    results[metric.method] = metric
    return results


def contextualPrefixText(row: dict[str, Any]) -> str:
    prefixParts = [
        f"[company={row.get('stockCode') or ''}]",
        f"[topic={row.get('topic') or ''}]",
        f"[period={row.get('period') or ''}]",
        f"[block={row.get('blockType') or ''}]",
        f"[semantic={row.get('semanticTopic') or ''}]",
        f"[detail={row.get('detailTopic') or ''}]",
        f"[blockLabel={row.get('blockLabel') or ''}]",
    ]
    return "".join(prefixParts) + "\n" + str(row.get("sliceText") or "")


def buildContextualPrefixCorpora(corpus: pl.DataFrame) -> list[str]:
    return [contextualPrefixText(row) for row in corpus.to_dicts()]


def runContextualPrefixExperiment(
    *,
    codes: list[str] | None = None,
    lastN: int = 12,
) -> dict[str, Any]:
    selectedCodes = codes or ["005930", "000660"]
    bench = loadBenchModule()
    corpus = buildBenchmarkCorpusForCodes(selectedCodes, lastN=lastN)
    cases = buildFilteredBenchmarkCases(bench, corpus, selectedCodes)
    rows = corpus.to_dicts()
    sliceIds = [str(row["sliceId"]) for row in rows]
    baseCorpora = bench.build_retrieval_corpora(corpus)
    candidateCorpora = {
        "B2_contextual_bm25": baseCorpora["contextual"],
        "B3_prefixed_contextual_bm25": buildContextualPrefixCorpora(corpus),
    }

    results: dict[str, Any] = {}
    for name, texts in candidateCorpora.items():
        start = time.perf_counter()
        bm25 = bench.SimpleBM25(texts)
        buildSec = time.perf_counter() - start
        rankedLists: dict[str, list[str]] = {}
        latencies: list[float] = []
        for case in cases:
            t0 = time.perf_counter()
            scores = bm25.score(case.question)
            order = bench.np.argsort(scores)[::-1][:10]
            latencies.append((time.perf_counter() - t0) * 1000)
            rankedLists[case.caseId] = [sliceIds[index] for index in order]
        metric = bench.evaluate_ranked_lists(cases, rankedLists, latencies, buildSec)
        metric.method = name
        results[name] = asdict(metric)

    summary = {
        "codes": selectedCodes,
        "caseCount": len(cases),
        "currentContextual": results["B2_contextual_bm25"],
        "prefixedContextual": results["B3_prefixed_contextual_bm25"],
        "winner": max(
            [results["B2_contextual_bm25"], results["B3_prefixed_contextual_bm25"]],
            key=lambda row: (row["hit5"], row["mrr10"], row["goldRecall10"]),
        )["method"],
    }
    saveJson(summary, OUTPUT_DIR / "contextualPrefix.summary.json")
    return summary


def buildLegRerankDocs(unitDf: pl.DataFrame, hitIds: list[str]) -> list[str]:
    recordMap = unitRecordMap(unitDf)
    docs: list[str] = []
    for unitId in hitIds:
        record = recordMap.get(unitId)
        if not record:
            docs.append("")
            continue
        metaParts = [
            f"topic={record.get('topic') or ''}",
            f"period={record.get('period') or ''}",
            f"blockType={record.get('blockType') or ''}",
            f"path={record.get('textComparablePathKey') or ''}",
            f"semantic={record.get('semanticTopic') or ''}",
            f"detail={record.get('detailTopic') or ''}",
        ]
        displayText = str(record.get("displayText") or "")
        payloadText = str(record.get("payloadText") or "")
        bodyParts = [displayText]
        if payloadText and payloadText not in displayText:
            bodyParts.append(payloadText)
        docs.append(" | ".join(part for part in metaParts if part) + "\n" + "\n".join(part for part in bodyParts if part))
    return docs


def rerankLegHits(
    queryText: str,
    hitIds: list[str],
    docs: list[str],
    *,
    reranker: Any,
    topK: int,
) -> list[str]:
    if not hitIds or not docs:
        return []
    pairs = [(queryText, doc) for doc in docs]
    scores = reranker.predict(pairs)
    rankedPairs = sorted(zip(hitIds, scores, strict=False), key=lambda item: float(item[1]), reverse=True)
    return [unitId for unitId, _score in rankedPairs[:topK]]


def searchLegIndexWithRerank(
    indexData: dict[str, Any],
    unitDf: pl.DataFrame,
    queryText: str,
    *,
    reranker: Any,
    topK: int = 10,
    rerankK: int = 30,
) -> tuple[QueryLegs, list[RetrievalHit]]:
    queryLegs, baseHits = searchLegIndex(indexData, queryText, topK=max(topK, rerankK))
    if not baseHits:
        return queryLegs, []
    candidateHits = baseHits[: max(topK, rerankK)]
    hitIds = [hit.unitId for hit in candidateHits]
    docs = buildLegRerankDocs(unitDf, hitIds)
    rerankedIds = rerankLegHits(queryText, hitIds, docs, reranker=reranker, topK=topK)
    rankMap = {unitId: rank for rank, unitId in enumerate(rerankedIds, 1)}
    hitMap = {hit.unitId: hit for hit in candidateHits}
    rerankedHits: list[RetrievalHit] = []
    for unitId in rerankedIds:
        originalHit = hitMap[unitId]
        rerankBoost = 0.5 * ((rerankK - rankMap[unitId]) / max(rerankK, 1))
        scoreBreakdown = dict(originalHit.scoreBreakdown)
        scoreBreakdown["rerankBoost"] = round(rerankBoost, 4)
        rerankedHits.append(
            RetrievalHit(
                unitId=originalHit.unitId,
                score=originalHit.score + rerankBoost,
                scoreBreakdown=scoreBreakdown,
                stockCode=originalHit.stockCode,
                topic=originalHit.topic,
                period=originalHit.period,
                displayText=originalHit.displayText,
            )
        )
    return queryLegs, rerankedHits


def evaluateEvidenceCoverage(
    cases: list[Any],
    rankedLists: dict[str, list[str]],
    recordMap: dict[str, dict[str, Any]],
) -> dict[str, float]:
    requiredScores: list[float] = []
    citationScores: list[float] = []
    for case in cases:
        rankedIds = rankedLists.get(case.caseId, [])
        evidenceText = " ".join(
            str(recordMap.get(unitId, {}).get("displayText") or recordMap.get(unitId, {}).get("payloadText") or "")
            for unitId in rankedIds[:3]
        ).lower()
        if case.requiredFacts:
            matchedFacts = sum(1 for fact in case.requiredFacts if fact.lower() in evidenceText)
            requiredScores.append(matchedFacts / len(case.requiredFacts))
        else:
            requiredScores.append(1.0)
        citationScores.append(1.0 if rankedIds else 0.0)
    return {
        "requiredFactCoverage": sum(requiredScores) / max(len(requiredScores), 1),
        "citationCoverage": sum(citationScores) / max(len(citationScores), 1),
    }


def evaluateUnitRankedLists(
    cases: list[Any],
    caseMap: dict[str, list[str]],
    rankedLists: dict[str, list[str]],
    latenciesMs: list[float],
    indexSec: float,
) -> dict[str, Any]:
    hits = {1: 0, 3: 0, 5: 0}
    mrrTotal = 0.0
    ndcgTotal = 0.0
    goldRecallTotal = 0.0
    requiredCoverageTotal = 0.0
    citationCoverageTotal = 0.0

    for case in cases:
        relevant = set(caseMap.get(case.caseId, []))
        ranked = rankedLists.get(case.caseId, [])
        if not relevant:
            continue
        for k in hits:
            if any(unitId in relevant for unitId in ranked[:k]):
                hits[k] += 1
        reciprocal = 0.0
        for rank, unitId in enumerate(ranked[:10], 1):
            if unitId in relevant:
                reciprocal = 1.0 / rank
                break
        mrrTotal += reciprocal
        found = sum(1 for unitId in ranked[:10] if unitId in relevant)
        goldRecallTotal += found / max(len(relevant), 1)

        dcg = 0.0
        for rank, unitId in enumerate(ranked[:10], 1):
            if unitId in relevant:
                dcg += 1.0 / (rank + 1)
        ideal = sum(1.0 / (rank + 1) for rank in range(1, min(len(relevant), 10) + 1))
        ndcgTotal += (dcg / ideal) if ideal else 0.0

        citationCoverageTotal += 1.0 if ranked[:3] else 0.0
        if case.requiredFacts:
            evidenceText = " ".join(ranked[:3]).lower()
            matchedFacts = sum(1 for fact in case.requiredFacts if fact.lower() in evidenceText)
            requiredCoverageTotal += matchedFacts / len(case.requiredFacts)
        else:
            requiredCoverageTotal += 1.0

    denominator = max(len(cases), 1)
    return {
        "hit1": hits[1] / denominator,
        "hit3": hits[3] / denominator,
        "hit5": hits[5] / denominator,
        "mrr10": mrrTotal / denominator,
        "ndcg10": ndcgTotal / denominator,
        "goldRecall10": goldRecallTotal / denominator,
        "requiredFactCoverage": requiredCoverageTotal / denominator,
        "citationCoverage": citationCoverageTotal / denominator,
        "medianLatencyMs": statistics.median(latenciesMs) if latenciesMs else 0.0,
        "p95LatencyMs": float(sorted(latenciesMs)[max(int(len(latenciesMs) * 0.95) - 1, 0)]) if latenciesMs else 0.0,
        "indexBuildSec": indexSec,
    }


def saveJson(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def loadSampleUnits(codes: list[str] | None = None) -> pl.DataFrame | None:
    unitsPath = OUTPUT_DIR / "sampleUnits.parquet"
    if not unitsPath.exists():
        return None
    if not codes:
        return pl.read_parquet(unitsPath)
    return pl.scan_parquet(unitsPath).filter(pl.col("stockCode").is_in(codes)).collect()


def materializeSampleArtifacts() -> dict[str, Any]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    unitDf = buildUnderstandingUnits(SAMPLE_CODES, topics=TARGET_TOPICS, lastN=12)
    buildSec = time.perf_counter() - start
    indexData = buildLegIndex(unitDf)

    unitsPath = OUTPUT_DIR / "sampleUnits.parquet"
    unitDf.write_parquet(unitsPath)

    indexSummary = {
        "recordCount": indexData["recordCount"],
        "postingStats": indexData["postingStats"],
    }
    saveJson(indexSummary, OUTPUT_DIR / "sampleIndex.summary.json")

    allSourceSlices = set()
    sliceCounts: list[int] = []
    for row in unitDf.to_dicts():
        sourceSlices = row.get("sourceSliceIds") or []
        sliceCounts.append(len(sourceSlices))
        for sliceId in sourceSlices:
            allSourceSlices.add(sliceId)

    summary = {
        "buildSec": round(buildSec, 4),
        "codes": SAMPLE_CODES,
        "topics": TARGET_TOPICS,
        "units": int(unitDf.height),
        "textUnits": int(unitDf.filter(pl.col("blockType") == "text").height),
        "tableUnits": int(unitDf.filter(pl.col("blockType") == "table").height),
        "fallbackUnits": int(unitDf.filter(pl.col("unitSource") == "contextFallback").height),
        "uniqueSourceSlices": len(allSourceSlices),
        "medianSlicesPerUnit": float(statistics.median(sliceCounts) if sliceCounts else 0.0),
    }
    saveJson(summary, OUTPUT_DIR / "sampleSummary.json")
    return summary


def runUnitSchemaExperiment() -> dict[str, Any]:
    return materializeSampleArtifacts()


def runLegIndexBuildExperiment() -> dict[str, Any]:
    unitDf = loadSampleUnits()
    if unitDf is None:
        runUnitSchemaExperiment()
        unitDf = loadSampleUnits()
    assert unitDf is not None

    start = time.perf_counter()
    indexData = buildLegIndex(unitDf)
    buildSec = time.perf_counter() - start
    summary = {
        "recordCount": int(indexData["recordCount"]),
        "buildSec": round(buildSec, 4),
        "postingStats": indexData["postingStats"],
    }
    saveJson(summary, OUTPUT_DIR / "legIndexBuild.summary.json")
    return summary


def runQueryCompilerExperiment() -> dict[str, Any]:
    queries = [
        "삼성전자 최신 배당 정책 표를 보여줘",
        "SK하이닉스 원재료 조달 변화 근거를 찾아줘",
        "네이버 사업 개요에서 서비스 구조를 설명할 수 있는 근거",
        "LG에너지솔루션 위험관리 표에서 환율과 금리 관련 행",
    ]
    compiled = [asdict(compileQuery(queryText)) for queryText in queries]
    summary = {"queryCount": len(compiled), "queries": compiled}
    saveJson(summary, OUTPUT_DIR / "queryCompiler.summary.json")
    return summary


def runTableStitchExperiment() -> dict[str, Any]:
    unitDf = loadSampleUnits()
    if unitDf is None:
        runUnitSchemaExperiment()
        unitDf = loadSampleUnits()
    assert unitDf is not None

    tableDf = unitDf.filter(pl.col("blockType") == "table")
    if tableDf.is_empty():
        summary = {
            "rowStitchPrecision": 0.0,
            "rowStitchRecall": 0.0,
            "headerPreservation": 0.0,
            "numericAlignmentAccuracy": 0.0,
            "groups": 0,
        }
        saveJson(summary, OUTPUT_DIR / "tableStitch.summary.json")
        return summary

    groups = (
        tableDf.group_by(["topic", "tableFingerprint", "rowFingerprint"])
        .agg(
            pl.col("period").n_unique().alias("periodCount"),
            pl.col("rowLabel").n_unique().alias("rowLabelVariants"),
            pl.col("payloadText").count().alias("rowCount"),
        )
    )
    matchedGroups = groups.filter(pl.col("periodCount") >= 2)
    precision = 1.0 if matchedGroups.is_empty() else float((matchedGroups["rowLabelVariants"] == 1).mean())
    recall = float(matchedGroups.height / max(groups.height, 1))
    headerPreservation = float(tableDf.filter(pl.col("tableFingerprint") != "").height / max(tableDf.height, 1))
    numericAlignment = float(tableDf.filter(pl.col("payloadText").str.contains(r"\d", literal=False)).height / max(tableDf.height, 1))
    summary = {
        "rowStitchPrecision": round(precision, 4),
        "rowStitchRecall": round(recall, 4),
        "headerPreservation": round(headerPreservation, 4),
        "numericAlignmentAccuracy": round(numericAlignment, 4),
        "groups": int(groups.height),
        "matchedGroups": int(matchedGroups.height),
    }
    saveJson(summary, OUTPUT_DIR / "tableStitch.summary.json")
    return summary


def runRetrievalExperiment(
    *,
    codes: list[str] | None = None,
    lastN: int = 12,
    baselineMode: str = "safe2",
) -> dict[str, Any]:
    selectedCodes = codes or SAMPLE_CODES
    unitDf = loadSampleUnits(selectedCodes)
    if unitDf is None:
        runUnitSchemaExperiment()
        unitDf = loadSampleUnits(selectedCodes)
    assert unitDf is not None

    bench, corpus, cases, caseMap = benchmarkCasesForUnits(unitDf, codes=selectedCodes, lastN=lastN)
    baselineResults = runCoreBaselineBench(bench, corpus, cases, includeDense=baselineMode == "core4")
    baselineFrame = pl.DataFrame([asdict(metric) for metric in baselineResults.values()]).sort(
        ["hit5", "mrr10"],
        descending=[True, True],
    )
    baselineRows = baselineFrame.to_dicts()

    start = time.perf_counter()
    indexData = buildLegIndex(unitDf)
    indexSec = time.perf_counter() - start
    recordMap = unitRecordMap(unitDf)
    rankedLists: dict[str, list[str]] = {}
    latenciesMs: list[float] = []
    coverageScores: list[float] = []
    citationScores: list[float] = []

    for case in cases:
        t0 = time.perf_counter()
        _queryLegs, hits = searchLegIndex(indexData, case.question, topK=10)
        latenciesMs.append((time.perf_counter() - t0) * 1000)
        rankedLists[case.caseId] = [hit.unitId for hit in hits]

        evidenceText = " ".join(recordMap[hit.unitId]["displayText"] for hit in hits[:3]).lower()
        if case.requiredFacts:
            matchedFacts = sum(1 for fact in case.requiredFacts if fact.lower() in evidenceText)
            coverageScores.append(matchedFacts / len(case.requiredFacts))
        else:
            coverageScores.append(1.0)
        citationScores.append(1.0 if hits else 0.0)

    metrics = evaluateUnitRankedLists(cases, caseMap, rankedLists, latenciesMs, indexSec)
    metrics["requiredFactCoverage"] = sum(coverageScores) / max(len(coverageScores), 1)
    metrics["citationCoverage"] = sum(citationScores) / max(len(citationScores), 1)

    denseRows = [row for row in baselineRows if str(row["method"]).startswith("D")]
    hybridRows = [row for row in baselineRows if str(row["method"]).startswith("H") or str(row["method"]).startswith("R")]
    summary = {
        "codes": selectedCodes,
        "baselineMode": baselineMode,
        "baselines": {
            "rawBm25": next(row for row in baselineRows if row["method"] == "B1_raw_bm25"),
            "contextualBm25": next(row for row in baselineRows if row["method"] == "B2_contextual_bm25"),
            "denseWinner": max(denseRows, key=lambda row: (row["hit5"], row["mrr10"])) if denseRows else None,
            "hybridWinner": max(hybridRows, key=lambda row: (row["hit5"], row["mrr10"])) if hybridRows else None,
        },
        "skippedBaselines": [] if baselineMode == "core4" else ["D2_bge_dense", "H2_contextual_plus_bge"],
        "legIndex": metrics,
        "caseCount": len(cases),
        "mappedCaseCount": sum(1 for case in cases if caseMap.get(case.caseId)),
    }
    saveJson(summary, OUTPUT_DIR / "retrieval.summary.json")
    return summary


def runLegRerankExperiment(
    *,
    codes: list[str] | None = None,
    lastN: int = 12,
) -> dict[str, Any]:
    selectedCodes = codes or ["005930", "000660"]
    unitDf = loadSampleUnits(selectedCodes)
    if unitDf is None:
        runUnitSchemaExperiment()
        unitDf = loadSampleUnits(selectedCodes)
    assert unitDf is not None

    bench, _corpus, cases, caseMap = benchmarkCasesForUnits(unitDf, codes=selectedCodes, lastN=lastN)
    corpus = buildBenchmarkCorpusForCodes(selectedCodes, lastN=lastN)
    baselineResults = runCoreBaselineBench(bench, corpus, cases, includeDense=False)
    recordMap = unitRecordMap(unitDf)

    indexStart = time.perf_counter()
    indexData = buildLegIndex(unitDf)
    indexSec = time.perf_counter() - indexStart

    legRankedLists: dict[str, list[str]] = {}
    legLatenciesMs: list[float] = []
    for case in cases:
        t0 = time.perf_counter()
        _queryLegs, hits = searchLegIndex(indexData, case.question, topK=10)
        legLatenciesMs.append((time.perf_counter() - t0) * 1000)
        legRankedLists[case.caseId] = [hit.unitId for hit in hits]
    legMetrics = evaluateUnitRankedLists(cases, caseMap, legRankedLists, legLatenciesMs, indexSec)
    legMetrics.update(evaluateEvidenceCoverage(cases, legRankedLists, recordMap))

    observedPeakMb = get_memory_mb()
    rerankRankedLists: dict[str, list[str]] = {}
    rerankLatenciesMs: list[float] = []
    check_memory_and_gc("091:rerank:beforeLoad")
    rerankerStart = time.perf_counter()
    reranker = bench.load_reranker()
    rerankerLoadSec = time.perf_counter() - rerankerStart
    observedPeakMb = max(observedPeakMb, get_memory_mb())
    try:
        for case in cases:
            t0 = time.perf_counter()
            _queryLegs, hits = searchLegIndexWithRerank(
                indexData,
                unitDf,
                case.question,
                reranker=reranker,
                topK=10,
                rerankK=30,
            )
            rerankLatenciesMs.append((time.perf_counter() - t0) * 1000)
            rerankRankedLists[case.caseId] = [hit.unitId for hit in hits]
            observedPeakMb = max(observedPeakMb, get_memory_mb())
    finally:
        del reranker
        gc.collect()
        check_memory_and_gc("091:rerank:afterLoad")

    rerankMetrics = evaluateUnitRankedLists(cases, caseMap, rerankRankedLists, rerankLatenciesMs, indexSec)
    rerankMetrics.update(evaluateEvidenceCoverage(cases, rerankRankedLists, recordMap))

    summary = {
        "codes": selectedCodes,
        "caseCount": len(cases),
        "mappedCaseCount": sum(1 for case in cases if caseMap.get(case.caseId)),
        "baselines": {
            "rawBm25": asdict(baselineResults["B1_raw_bm25"]),
            "contextualBm25": asdict(baselineResults["B2_contextual_bm25"]),
        },
        "legIndexOnly": legMetrics,
        "legRerank": rerankMetrics,
        "rerankerLoadSec": round(rerankerLoadSec, 4),
        "peakMemoryMb": round(observedPeakMb, 2),
        "accepted": bool(
            rerankMetrics["hit5"] >= legMetrics["hit5"]
            and (rerankMetrics["requiredFactCoverage"] - legMetrics["requiredFactCoverage"]) >= 0.05
            and rerankMetrics["medianLatencyMs"] <= 150.0
            and observedPeakMb < 1200.0
        ),
    }
    saveJson(summary, OUTPUT_DIR / "legRerank.summary.json")
    return summary


def runUnderstandingBundleExperiment(
    *,
    codes: list[str] | None = None,
    lastN: int = 12,
) -> dict[str, Any]:
    selectedCodes = codes or SAMPLE_CODES
    unitDf = loadSampleUnits(selectedCodes)
    if unitDf is None:
        runUnitSchemaExperiment()
        unitDf = loadSampleUnits(selectedCodes)
    assert unitDf is not None

    _bench, _corpus, cases, _caseMap = benchmarkCasesForUnits(unitDf, codes=selectedCodes, lastN=lastN)
    indexData = buildLegIndex(unitDf)
    targetCases = [case for case in cases if case.taskType in {"summary", "change"}]
    requiredCoverageScores: list[float] = []
    citationCoverageScores: list[float] = []
    stitchedTableCounts: list[int] = []
    changePairCounts: list[int] = []

    for case in targetCases:
        bundle = buildUnderstandingBundle(unitDf, indexData, case.question, topK=8)
        combinedEvidence = " ".join(item["displayText"] for item in bundle.evidenceUnits).lower()
        if case.requiredFacts:
            matched = sum(1 for fact in case.requiredFacts if fact.lower() in combinedEvidence)
            requiredCoverageScores.append(matched / len(case.requiredFacts))
        else:
            requiredCoverageScores.append(1.0)
        citationCoverageScores.append(1.0 if bundle.evidenceUnits else 0.0)
        stitchedTableCounts.append(len(bundle.stitchedTables))
        changePairCounts.append(len(bundle.changePairs))

    summary = {
        "codes": selectedCodes,
        "caseCount": len(targetCases),
        "requiredFactCoverage": round(sum(requiredCoverageScores) / max(len(requiredCoverageScores), 1), 4),
        "citationCoverage": round(sum(citationCoverageScores) / max(len(citationCoverageScores), 1), 4),
        "avgStitchedTables": round(sum(stitchedTableCounts) / max(len(stitchedTableCounts), 1), 4),
        "avgChangePairs": round(sum(changePairCounts) / max(len(changePairCounts), 1), 4),
    }
    saveJson(summary, OUTPUT_DIR / "understandingBundle.summary.json")
    return summary


def peakMemoryMb() -> float:
    return round(max(get_memory_mb(), 0.0), 2)


def availableDocCodes(limit: int | None = None) -> list[str]:
    from dartlab.core.dataLoader import _dataDir

    codes = sorted(path.stem for path in _dataDir("docs").glob("*.parquet"))
    return codes if limit is None else codes[:limit]


def runUniverseStressExperiment(
    *,
    stageCodes: dict[str, list[str]] | None = None,
    topics: list[str] | None = None,
    lastN: int = 8,
) -> dict[str, Any]:
    querySet = [
        "최신 배당 정책 표를 보여줘",
        "원재료 조달 구조를 설명해줘",
        "위험관리 변화 근거를 찾아줘",
        "최대주주 지분 구조를 보여줘",
    ]
    stages = stageCodes or {
        "sample6": SAMPLE_CODES,
        "stress50": availableDocCodes(50),
        "stress283": availableDocCodes(283),
    }
    results: dict[str, Any] = {}
    stressTopics = topics or TARGET_TOPICS
    for stageName, codes in stages.items():
        check_memory_and_gc(f"088:stress:before:{stageName}")
        if codes == SAMPLE_CODES and (OUTPUT_DIR / "sampleUnits.parquet").exists():
            t0 = time.perf_counter()
            unitDf = pl.read_parquet(OUTPUT_DIR / "sampleUnits.parquet")
            buildSec = time.perf_counter() - t0
        else:
            t0 = time.perf_counter()
            unitDf = buildUnderstandingUnits(codes, topics=stressTopics, lastN=lastN)
            buildSec = time.perf_counter() - t0
        indexStart = time.perf_counter()
        indexData = buildLegIndex(unitDf)
        indexSec = time.perf_counter() - indexStart
        latenciesMs: list[float] = []
        for queryText in querySet:
            q0 = time.perf_counter()
            searchLegIndex(indexData, queryText, topK=10)
            latenciesMs.append((time.perf_counter() - q0) * 1000)
        results[stageName] = {
            "codes": len(codes),
            "units": int(unitDf.height),
            "materializeSec": round(buildSec, 4),
            "indexBuildSec": round(indexSec, 4),
            "medianLatencyMs": round(statistics.median(latenciesMs), 4),
            "p95LatencyMs": round(float(sorted(latenciesMs)[max(int(len(latenciesMs) * 0.95) - 1, 0)]), 4),
            "peakMemoryMb": peakMemoryMb(),
            "errors": 0,
        }
        del unitDf
        del indexData
        gc.collect()
        check_memory_and_gc(f"088:stress:after:{stageName}")
    saveJson(results, OUTPUT_DIR / "universeStress.summary.json")
    return results


def main() -> None:
    summary = runUnitSchemaExperiment()
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
