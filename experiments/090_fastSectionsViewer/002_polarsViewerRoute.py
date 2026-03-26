"""
실험 ID: 002
실험명: Polars topic-scoped viewer route

목적:
- `company.sections`를 만들지 않고 raw docs/report scan + 기존 viewer 직렬화 함수를 조합해
  viewer hot path를 얼마나 재현할 수 있는지 검증한다
- `toc`, docs text topic, report topic, period switch를 same-shape payload 기준으로 baseline과 비교한다

가설:
1. docs text topic은 `loadData(..., columns=...) + splitMarkdownBlocks()`만으로 문서형 viewer 흐름을 상당 부분 재현할 수 있다
2. report topic은 full sections 없이도 baseline payload에 매우 가깝게 맞출 수 있다
3. cold latency와 RSS는 baseline 대비 유의미하게 줄지만, docs topic exact hash는 table/path 메타 차이로 완전 일치하지 않을 가능성이 높다

방법:
1. 001 baseline harness를 import해 동일 case matrix와 계측 방식을 사용한다
2. docs는 Polars lazy `loadData(..., columns=...)`로 읽고 topic-scoped block map을 조립한다
3. text block은 viewer `_buildTextBlock()`를 재사용하고, table은 raw_markdown fallback으로 직렬화한다
4. report topic은 `_buildReportBlock()` direct path를 사용한다
5. baseline과 payload digest, cold/warm 시간, RSS, bytes를 비교한다

결과 (실험 후 작성):
- 최신 parity patch 후 `safe2` 재실행 기준 exact match는 여전히 `0/12`였다
- `_sections=False`를 전 case에서 유지했고, `toc` cold는 `1.733~2.004s`, peak RSS는 `376~490MB`로 baseline 대비 `28~30%` 절감됐다
- docs topic cold는 `companyOverview 1.744~2.181s`, `businessOverview 2.562~3.700s`로 baseline 대비 `3.46~5.84x` 빨라졌다
- docs/report mixed topic cold는 `dividend 1.596~1.684s`, `majorHolder 1.700~1.808s`였고 peak save는 대체로 `36~43%`였다
- `periodSwitch:businessOverview` cold는 `2.857~3.755s`, warm median은 `114.4~286.6ms`였고 selected period는 두 종목 모두 baseline과 같은 `2024Q4`로 맞췄다
- `toc` chapter list는 baseline과 같아졌지만, topic count와 block payload exact는 여전히 남았다

결론:
- 현재 090 후보 중 1차 winner다. exact hash는 못 맞췄지만, `viewer 저장물 없이 sections 미물질화`라는 제약 아래 cold latency와 RSS를 가장 잘 줄였다
- 다음 승부처는 parity다. 특히 docs topic의 canonical block 수, raw table fallback, text path metadata, chapter/topic count 정합성 때문에 baseline hash와 달라진다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = loadModule(Path(__file__).with_name("001_viewerApiBaseline.py"), "exp090Base")

from dartlab.core.dataLoader import loadData
from dartlab.core.reportSelector import selectReport
from dartlab.providers.dart.docs.sections._common import REPORT_KINDS, periodOrderValue, sortPeriods
from dartlab.providers.dart.docs.sections.chunker import parseMajorNum
from dartlab.providers.dart.docs.sections.mapper import mapSectionTitle
from dartlab.providers.dart.docs.sections.runtime import chapterFromMajorNum
from dartlab.providers.dart.docs.sections.views import normalizeTitle, splitMarkdownBlocks

HEADING_MAJOR_RE = re.compile(r"^[가-힣]\.\s")
HEADING_NUM_RE = re.compile(r"^\d+\.\s")
HEADING_MINOR_RE = re.compile(r"^\(\d+\)\s|^\([가-힣]\)\s")
HEADING_CIRCLED_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]\s")


class PolarsViewerRuntime:
    def __init__(self, stockCode: str):
        import dartlab
        from dartlab.providers.dart.docs import viewer as viewerModule
        from dartlab.server.services.company_api import _find_prev_comparable, filter_blocks_by_period

        self.company = dartlab.Company(stockCode)
        self.stockCode = stockCode
        self.corpName = self.company.corpName
        self.viewerModule = viewerModule
        self.findPrevComparable = _find_prev_comparable
        self.filterBlocksByPeriod = filter_blocks_by_period
        self.docsFrameCache: pl.DataFrame | None = None
        self.reportApiCache: pl.DataFrame | None = None
        self.viewerCache: dict[str, list[Any]] = {}
        self.tocCache: dict[str, Any] | None = None
        self.docsTopicSpecCache: dict[str, tuple[list[dict[str, Any]], list[str]]] = {}
        self.docsTopicSpecsReady = False

    @property
    def hasSectionsCache(self) -> bool:
        return "_sections" in self.company._cache

    def topicLabel(self, topic: str) -> str:
        return self.company._topicLabel(topic)

    def canonicalPeriod(self, period: str) -> str:
        value = str(period)
        return f"{value}Q4" if len(value) == 4 and value.isdigit() else value

    def readDocsFrame(self) -> pl.DataFrame:
        if self.docsFrameCache is None:
            self.docsFrameCache = loadData(
                self.stockCode,
                category="docs",
                sinceYear=2016,
                columns=["year", "report_type", "rcept_date", "section_order", "section_title", "section_content"],
            )
        return self.docsFrameCache

    def readReportApiFrame(self) -> pl.DataFrame:
        if self.reportApiCache is None:
            self.reportApiCache = loadData(self.stockCode, category="report", columns=["apiType"])
        return self.reportApiCache

    def availableReportTopics(self) -> set[str]:
        df = self.readReportApiFrame()
        if df is None or df.is_empty() or "apiType" not in df.columns:
            return set()
        available = {str(value) for value in df["apiType"].drop_nulls().unique().to_list()}
        mapped = set()
        for apiType in available:
            mapped.add("audit" if apiType == "auditOpinion" else apiType)
        return mapped

    def iterPeriodSubsets(self) -> list[tuple[str, pl.DataFrame]]:
        df = self.readDocsFrame()
        years = sorted(df["year"].unique().to_list(), reverse=True)
        subsets: list[tuple[str, pl.DataFrame]] = []
        for year in years:
            for reportKind, suffix in REPORT_KINDS:
                periodKey = f"{year}{suffix}"
                periodKey = self.canonicalPeriod(periodKey)
                report = selectReport(df, year, reportKind=reportKind)
                if report is None or "section_content" not in report.columns:
                    continue
                subset = (
                    report.select(["section_order", "section_title", "section_content"])
                    .filter(pl.col("section_content").is_not_null() & (pl.col("section_content").str.len_chars() > 0))
                    .sort("section_order")
                )
                if subset.height == 0:
                    continue
                subsets.append((periodKey, subset))
        subsets.sort(key=lambda item: periodOrderValue(item[0]), reverse=True)
        return subsets

    def headingLevel(self, label: str) -> int | None:
        if HEADING_MAJOR_RE.match(label):
            return 1
        if HEADING_NUM_RE.match(label):
            return 2
        if HEADING_MINOR_RE.match(label):
            return 3
        if HEADING_CIRCLED_RE.match(label):
            return 4
        return None

    def ensureDocsTopicSpecs(self) -> None:
        if self.docsTopicSpecsReady:
            return

        blockSpecsByTopic: dict[str, dict[str, dict[str, Any]]] = {}
        allPeriodsByTopic: dict[str, set[str]] = {}
        for periodKey, subset in self.iterPeriodSubsets():
            sectionSeenByTopic: dict[str, dict[str, int]] = {}
            for record in subset.iter_rows(named=True):
                rawTitle = normalizeTitle(str(record["section_title"] or ""))
                topic = mapSectionTitle(rawTitle) if rawTitle else None
                if not rawTitle or not topic:
                    continue
                allPeriodsByTopic.setdefault(topic, set()).add(periodKey)
                sectionSeen = sectionSeenByTopic.setdefault(topic, {})
                sectionSeen[rawTitle] = sectionSeen.get(rawTitle, 0) + 1
                sectionKey = f"{rawTitle}#{sectionSeen[rawTitle]}"
                localSeen: dict[tuple[str, str], int] = {}
                sectionOrder = int(record["section_order"] or 0)
                content = str(record["section_content"] or "")
                for block in splitMarkdownBlocks(content):
                    blockType = str(block["blockType"])
                    blockLabel = str(block["blockLabel"] or "(root)")
                    labelKey = normalizeTitle(blockLabel) or "(root)"
                    localKey = (blockType, labelKey)
                    localSeen[localKey] = localSeen.get(localKey, 0) + 1
                    occurrence = localSeen[localKey]
                    blockKey = f"{sectionKey}|{blockType}|{labelKey}|{occurrence}"
                    orderHint = (sectionOrder * 1000) + int(block["blockIdx"])
                    topicSpecs = blockSpecsByTopic.setdefault(topic, {})
                    spec = topicSpecs.get(blockKey)
                    if spec is None:
                        spec = {
                            "key": blockKey,
                            "blockType": blockType,
                            "blockLabel": blockLabel,
                            "orderHint": orderHint,
                            "periodMap": {},
                        }
                        topicSpecs[blockKey] = spec
                    spec["periodMap"][periodKey] = str(block["blockText"] or "")

        for topic, blockSpecs in blockSpecsByTopic.items():
            orderedSpecs = sorted(blockSpecs.values(), key=lambda item: (int(item["orderHint"]), str(item["key"])))
            orderedPeriods = sortPeriods(list(allPeriodsByTopic.get(topic, set())), descending=True)
            self.docsTopicSpecCache[topic] = (orderedSpecs, orderedPeriods)
        self.docsTopicSpecsReady = True

    def buildDocsTopicSpecs(self, topic: str) -> tuple[list[dict[str, Any]], list[str]]:
        self.ensureDocsTopicSpecs()
        return self.docsTopicSpecCache.get(topic, ([], []))

    def docsTopicExists(self, topic: str) -> bool:
        specs, _ = self.buildDocsTopicSpecs(topic)
        return len(specs) > 0

    def buildDocsBlocks(self, topic: str) -> list[Any]:
        specs, orderedPeriods = self.buildDocsTopicSpecs(topic)
        blocks: list[Any] = []
        for blockOrder, spec in enumerate(specs):
            blockType = str(spec["blockType"])
            periodMap = {period: text for period, text in spec["periodMap"].items() if text}
            if blockType in {"text", "heading"}:
                row = {
                    "textNodeType": "heading" if blockType == "heading" else "body",
                    "textStructural": True if blockType == "heading" else None,
                    "textLevel": self.headingLevel(str(spec["blockLabel"])) if blockType == "heading" else None,
                }
                for period in orderedPeriods:
                    row[period] = periodMap.get(period)
                boRows = pl.DataFrame([row])
                block = self.viewerModule._buildTextBlock(boRows, blockOrder, orderedPeriods)
                if block is not None:
                    blocks.append(block)
                continue
            if blockType == "table":
                periods = [period for period in orderedPeriods if period in periodMap]
                block = self.viewerModule.ViewerBlock(
                    block=blockOrder,
                    kind="raw_markdown",
                    source="docs",
                    data=None,
                    meta=self.viewerModule.BlockMeta(
                        periods=periods,
                        rowCount=1,
                        colCount=len(periods),
                    ),
                    rawMarkdown={period: periodMap[period] for period in periods},
                )
                blocks.append(block)
        return blocks

    def buildDocsViewerPayload(self, topic: str) -> dict[str, Any]:
        blocks = self.viewerCache.get(topic)
        if blocks is None:
            blocks = self.buildDocsBlocks(topic)
            self.viewerCache[topic] = blocks
        return {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "topic": topic,
            "topicLabel": self.topicLabel(topic),
            "period": None,
            "blocks": [self.viewerModule.serializeViewerBlock(block) for block in blocks],
            "textDocument": self.viewerModule.serializeViewerTextDocument(
                self.viewerModule.viewerTextDocument(topic, blocks)
            ),
        }

    def buildReportViewerPayload(self, topic: str) -> dict[str, Any]:
        blocks = self.viewerCache.get(topic)
        if blocks is None:
            block = self.viewerModule._buildReportBlock(self.company, topic, 0)
            blocks = [] if block is None else [block]
            self.viewerCache[topic] = blocks
        return {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "topic": topic,
            "topicLabel": self.topicLabel(topic),
            "period": None,
            "blocks": [self.viewerModule.serializeViewerBlock(block) for block in blocks],
            "textDocument": self.viewerModule.serializeViewerTextDocument(
                self.viewerModule.viewerTextDocument(topic, blocks)
            ),
        }

    def buildTocPayload(self) -> dict[str, Any]:
        if self.tocCache is not None:
            return self.tocCache

        docsTopicMeta: dict[str, dict[str, Any]] = {}
        for periodKey, subset in self.iterPeriodSubsets():
            for record in subset.iter_rows(named=True):
                rawTitle = normalizeTitle(str(record["section_title"] or ""))
                topic = mapSectionTitle(rawTitle) if rawTitle else None
                if not topic:
                    continue
                meta = docsTopicMeta.setdefault(
                    topic,
                    {
                        "chapter": None,
                        "periods": set(),
                    },
                )
                majorNum = parseMajorNum(str(record["section_title"] or "").strip())
                chapter = chapterFromMajorNum(majorNum) if majorNum is not None else None
                if meta["chapter"] is None:
                    meta["chapter"] = chapter or self.company._chapterForTopic(topic)
                meta["periods"].add(periodKey)

        chapterMap: dict[str, list[dict[str, Any]]] = {}
        chapterOrder: list[str] = []

        def addTopic(chapter: str, payload: dict[str, Any]) -> None:
            if chapter not in chapterMap:
                chapterMap[chapter] = []
                chapterOrder.append(chapter)
            chapterMap[chapter].append(payload)

        financeChapter = "III. 재무에 관한 사항"
        for financeTopic in ("BS", "IS", "CIS", "CF", "SCE", "ratios"):
            try:
                if financeTopic == "ratios":
                    if self.company._ratioSeries() is None:
                        continue
                elif self.company._showFinanceTopic(financeTopic) is None:
                    continue
            except (AttributeError, TypeError):
                continue
            addTopic(
                financeChapter,
                {
                    "topic": financeTopic,
                    "label": self.topicLabel(financeTopic),
                    "textCount": 0,
                    "tableCount": 1,
                    "hasChanges": False,
                },
            )

        reportTopics = self.availableReportTopics()
        for topic, meta in docsTopicMeta.items():
            specs, orderedTopicPeriods = self.buildDocsTopicSpecs(topic)
            latest = orderedTopicPeriods[0] if orderedTopicPeriods else None
            prev = self.findPrevComparable(orderedTopicPeriods, latest) if latest else None
            textCount = sum(1 for spec in specs if str(spec["blockType"]) in {"text", "heading"})
            tableCount = sum(1 for spec in specs if str(spec["blockType"]) == "table")
            hasChanges = False
            if latest and prev:
                for spec in specs:
                    if str(spec["blockType"]) not in {"text", "heading"}:
                        continue
                    latestText = str(spec["periodMap"].get(latest) or "").strip()
                    prevText = str(spec["periodMap"].get(prev) or "").strip()
                    if latestText and prevText and latestText != prevText:
                        hasChanges = True
                        break
            addTopic(
                str(meta["chapter"] or self.company._chapterForTopic(topic) or "기타"),
                {
                    "topic": topic,
                    "label": self.topicLabel(topic),
                    "textCount": int(textCount),
                    "tableCount": int(tableCount),
                    "hasChanges": hasChanges,
                },
            )

        for reportTopic in sorted(reportTopics):
            if reportTopic in docsTopicMeta:
                continue
            chapter = self.company._chapterForTopic(reportTopic)
            addTopic(
                chapter,
                {
                    "topic": reportTopic,
                    "label": self.topicLabel(reportTopic),
                    "textCount": 0,
                    "tableCount": 1,
                    "hasChanges": False,
                },
            )

        romanOrder = {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12,
        }
        orderedChapters = sorted(
            chapterOrder,
            key=lambda chapter: (romanOrder.get(chapter.split(".")[0].strip(), 99), chapter),
        )
        payload = {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "chapters": [{"chapter": chapter, "topics": chapterMap[chapter]} for chapter in orderedChapters],
        }
        self.tocCache = payload
        return payload

    def pickSwitchPeriod(self, topic: str) -> str | None:
        blocks = self.viewerCache.get(topic)
        if blocks is None:
            if self.docsTopicExists(topic):
                self.buildDocsViewerPayload(topic)
            elif topic in self.availableReportTopics():
                self.buildReportViewerPayload(topic)
            else:
                self.buildDocsViewerPayload(topic)
            blocks = self.viewerCache.get(topic, [])
        allPeriods = sorted({period for block in blocks for period in getattr(block.meta, "periods", [])})
        if not allPeriods:
            return None
        latest = allPeriods[-1]
        return self.findPrevComparable(allPeriods, latest) or latest

    def runCase(self, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
        if caseName == "toc":
            return self.buildTocPayload(), {"hasSectionsCache": self.hasSectionsCache}
        if caseName == "viewerTopic":
            if self.docsTopicExists(str(topic)):
                payload = self.buildDocsViewerPayload(str(topic))
            elif str(topic) in self.availableReportTopics():
                payload = self.buildReportViewerPayload(str(topic))
            else:
                payload = self.buildDocsViewerPayload(str(topic))
            return payload, {"hasSectionsCache": self.hasSectionsCache}
        if caseName == "periodSwitch":
            selectedPeriod = self.pickSwitchPeriod(str(topic))
            blocks = self.viewerCache.get(str(topic))
            if blocks is None:
                self.buildDocsViewerPayload(str(topic))
                blocks = self.viewerCache[str(topic)]
            filtered = self.filterBlocksByPeriod(blocks, selectedPeriod) if selectedPeriod else blocks
            payload = {
                "stockCode": self.stockCode,
                "corpName": self.corpName,
                "topic": topic,
                "topicLabel": self.topicLabel(str(topic)),
                "period": selectedPeriod,
                "blocks": [self.viewerModule.serializeViewerBlock(block) for block in filtered],
                "textDocument": self.viewerModule.serializeViewerTextDocument(
                    self.viewerModule.viewerTextDocument(str(topic), filtered)
                ),
            }
            return payload, {"hasSectionsCache": self.hasSectionsCache, "selectedPeriod": selectedPeriod}
        raise ValueError(f"알 수 없는 caseName: {caseName}")


def childMain() -> None:
    BASE.childMain(PolarsViewerRuntime)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=BASE.DEFAULT_SAMPLE, choices=["safe2", "all6"])
    args = parser.parse_args()
    baselineRows = BASE.collectMode(Path(__file__).with_name("001_viewerApiBaseline.py"), "baseline", args.sample)
    candidateRows = BASE.collectMode(Path(__file__), "polars", args.sample)
    BASE.printSummary(f"090 polars / {args.sample}", candidateRows)
    BASE.printComparisonSummary(
        f"090 polars vs baseline / {args.sample}",
        BASE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
