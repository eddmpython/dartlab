"""
실험 ID: 005
실험명: Direct sections hybrid viewer route

목적:
- `company._cache['_sections']`는 건드리지 않으면서 `sections(stockCode)`를 직접 사용해 docs topic parity를 얼마나 회복할 수 있는지 검증한다
- 002의 speed winner와 baseline 사이에서 정확도-속도 절충점이 있는지 본다

가설:
1. docs topic은 `sections(stockCode)` direct frame + 기존 viewer helper 조합으로 baseline payload와 훨씬 가까워질 수 있다
2. cold latency와 RSS는 002보다는 나빠지지만 baseline보다는 여전히 나을 수 있다
3. `periodSwitch`와 `topicLabel`은 baseline과 거의 동일하게 맞출 수 있다

방법:
1. 001 baseline harness를 그대로 재사용한다
2. docs topic은 `sections(stockCode)` direct frame에서 `topicFrame`을 잘라 `_buildTextBlock/_buildTableBlock`으로 조립한다
3. report-only topic은 `_buildReportBlock()`을 그대로 쓴다
4. `toc`는 direct sections frame + finance/report 보강으로 재구성한다
5. safe2 샘플에서 cold/warm/RSS/bytes/exact hash를 baseline과 비교한다

결과 (실험 후 작성):
- 실행 후 본문 업데이트

결론:
- 실행 후 본문 업데이트

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


BASE = loadModule(Path(__file__).with_name("001_viewerApiBaseline.py"), "exp090Base005")
POLARS = loadModule(Path(__file__).with_name("002_polarsViewerRoute.py"), "exp090Polars005")

from dartlab.engines.company.dart.docs.sections.pipeline import sections as buildSections

PERIOD_RE = re.compile(r"^\d{4}(Q[1-4])?$")


class SectionsHybridRuntime(POLARS.PolarsViewerRuntime):
    def __init__(self, stockCode: str):
        super().__init__(stockCode)
        self.sectionsFrameCache: pl.DataFrame | None = None

    def readSectionsFrame(self) -> pl.DataFrame | None:
        if self.sectionsFrameCache is None:
            self.sectionsFrameCache = buildSections(self.stockCode)
        return self.sectionsFrameCache

    def docsTopicExists(self, topic: str) -> bool:
        frame = self.readSectionsFrame()
        if frame is None or frame.is_empty():
            return False
        return frame.filter(pl.col("topic") == topic).height > 0

    def buildDocsViewerPayload(self, topic: str) -> dict[str, Any]:
        blocks = self.viewerCache.get(topic)
        if blocks is None:
            sec = self.readSectionsFrame()
            topicFrame = None if sec is None else sec.filter(pl.col("topic") == topic)
            blocks = []
            if topicFrame is not None and topicFrame.height > 0:
                periodCols = [column for column in topicFrame.columns if PERIOD_RE.fullmatch(str(column))]
                blockOrders = topicFrame["blockOrder"].unique().sort().to_list() if "blockOrder" in topicFrame.columns else []
                for bo in blockOrders:
                    boRows = topicFrame.filter(pl.col("blockOrder") == bo)
                    blockType = str(boRows["blockType"][0]) if "blockType" in boRows.columns else "text"
                    if blockType == "text":
                        block = self.viewerModule._buildTextBlock(boRows, int(bo), periodCols)
                    else:
                        block = self.viewerModule._buildTableBlock(self.company, topic, topicFrame, int(bo), periodCols)
                    if block is not None:
                        blocks.append(block)
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
        sec = self.readSectionsFrame()
        if sec is None:
            self.tocCache = {"stockCode": self.stockCode, "corpName": self.corpName, "chapters": []}
            return self.tocCache

        chapterMap: dict[str, list[dict[str, Any]]] = {}
        chapterOrder: list[str] = []
        seenTopics: set[str] = set()

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
            seenTopics.add(financeTopic)
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

        periodCols = sorted([column for column in sec.columns if PERIOD_RE.fullmatch(str(column))], reverse=True)
        latest2 = periodCols[:2]

        for row in sec.iter_rows(named=True):
            topic = row.get("topic")
            if not isinstance(topic, str) or not topic or topic in seenTopics:
                continue
            seenTopics.add(topic)
            topicFrame = sec.filter(pl.col("topic") == topic)
            blockTypes = topicFrame["blockType"] if "blockType" in topicFrame.columns else None
            textCount = blockTypes.eq("text").sum() if blockTypes is not None else topicFrame.height
            tableCount = blockTypes.eq("table").sum() if blockTypes is not None else 0
            hasChanges = False
            if latest2 and blockTypes is not None:
                textRows = topicFrame.filter(pl.col("blockType") == "text")
                for textRow in textRows.iter_rows(named=True):
                    current = str(textRow.get(latest2[0]) or "").strip()
                    previous = str(textRow.get(latest2[1]) or "").strip()
                    if current and previous and current != previous:
                        hasChanges = True
                        break
            chapter = topicFrame.item(0, "chapter") if "chapter" in topicFrame.columns else "기타"
            addTopic(
                chapter if isinstance(chapter, str) and chapter else "기타",
                {
                    "topic": topic,
                    "label": self.topicLabel(topic),
                    "textCount": int(textCount),
                    "tableCount": int(tableCount),
                    "hasChanges": hasChanges,
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
        orderedChapters = sorted(chapterOrder, key=lambda chapter: (romanOrder.get(chapter.split(".")[0].strip(), 99), chapter))
        self.tocCache = {
            "stockCode": self.stockCode,
            "corpName": self.corpName,
            "chapters": [{"chapter": chapter, "topics": chapterMap[chapter]} for chapter in orderedChapters],
        }
        return self.tocCache


def childMain() -> None:
    BASE.childMain(SectionsHybridRuntime)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=BASE.DEFAULT_SAMPLE, choices=["safe2", "all6"])
    args = parser.parse_args()
    baselineRows = BASE.collectMode(Path(__file__).with_name("001_viewerApiBaseline.py"), "baseline", args.sample)
    candidateRows = BASE.collectMode(Path(__file__), "sectionsHybrid", args.sample)
    BASE.printSummary(f"090 sectionsHybrid / {args.sample}", candidateRows)
    BASE.printComparisonSummary(
        f"090 sectionsHybrid vs baseline / {args.sample}",
        BASE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
