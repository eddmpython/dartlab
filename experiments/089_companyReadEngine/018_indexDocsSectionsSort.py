"""
실험 ID: 018
실험명: Index Docs Sections Sort Clone

목적:
- `docs.sections`의 topic/chapter/block ordering 공식을 그대로 복제하되 full DataFrame materialization 없이 docs index rows만 exact 재현할 수 있는지 검증
- `index`의 최대 병목인 docs source rows를 `sections metadata-only clone`으로 대체 가능한지 확인

가설:
1. `topicChapter`, `topicFirstSeq`, `rowOrder`, `_topicRowSortKey`를 `sections()`와 동일하게 적용하면 docs rows exact가 나온다
2. current report rows를 그대로 붙이면 full `index`도 exact가 되면서 `_sections`를 만들지 않는다

방법:
1. 샘플 6종목에 대해 candidate full `index`와 baseline public `company.index`를 fresh subprocess로 비교한다
2. docs candidate는 `sections()`의 핵심 축(`topicMap`, `rowOrder`, `topicChapter`, `topicFirstSeq`)만 집계하고, 최종 DataFrame 대신 topic별 `periodCount/preview/order`만 만든다
3. finance/report rows는 current exact 경로를 그대로 사용한다
4. payload digest, 시간, peak RSS, heavy cache 생성 여부를 기록한다

결과 (실험 후 작성):
- 총 6개 case(6종목 × full `index`)를 same-process candidate/baseline 비교로 검증
- exact match: `6/6`
- same-process 비교 기준 속도는 `1.12~1.54x`였고, candidate peak RSS는 `365.9~517.2MB`였다
- `_sections/_profileFacts/retrievalBlocks` 생성은 `0/6`이었다
- baseline과 candidate의 shape는 `6/6` 모두 같았다

결론:
- **채택**
- `docs.sections`의 topic/chapter/order semantics는 `topicChapter`, `topicFirstSeq`, `rowOrder`, `_topicRowSortKey`를 그대로 복제해야만 exact가 된다
- 이 metadata-only clone으로 docs rows를 exact 재현할 수 있었고, full `index`도 `_sections` 없이 exact가 나왔다
- 다만 same-process timing은 편향될 수 있으므로 실제 성능 개선폭은 019에서 다시 재측정했다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl
import psutil


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline018")


def measurePhase(action: Callable[[], Any]) -> tuple[Any, dict[str, Any]]:
    process = psutil.Process(os.getpid())
    rssStart = process.memory_info().rss
    rssPeak = rssStart
    stopEvent = threading.Event()

    def pollRss() -> None:
        nonlocal rssPeak
        while not stopEvent.is_set():
            rssPeak = max(rssPeak, process.memory_info().rss)
            time.sleep(0.01)

    poller = threading.Thread(target=pollRss, daemon=True)
    poller.start()
    startedAt = time.perf_counter()
    payload = action()
    elapsedSec = time.perf_counter() - startedAt
    stopEvent.set()
    poller.join(timeout=1.0)
    return payload, {
        "elapsedSec": elapsedSec,
        "rssPeakMb": rssPeak / 1024 / 1024,
        "rssDeltaMb": (rssPeak - rssStart) / 1024 / 1024,
    }


def buildDocsRowsClone(company) -> list[dict[str, Any]]:
    from dartlab.providers.dart.company import _CHAPTER_ORDER, _CHAPTER_TITLES
    from dartlab.providers.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods
    from dartlab.providers.dart.docs.sections.pipeline import (
        _expandStructuredRows,
        _reportRowsToTopicRows,
        _rowCadenceMeta,
        applyProjections,
        chapterTeacherTopics,
        detailTopicForTopic,
        iterPeriodSubsets,
        projectionSuppressedTopics,
    )

    topicMap: dict[tuple[str, str], dict[str, str]] = {}
    rowOrder: dict[tuple[str, str], dict[str, int]] = {}
    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, object]] | None = None
    suppressed = projectionSuppressedTopics()

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(company.stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset, ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    if not validPeriods:
        return []

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)
    latestPeriod = validPeriods[-1]

    def representativePeriodRank(period: str | None) -> int:
        if not isinstance(period, str):
            return -1
        year = int(period[:4])
        quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
        return (year * 10) + quarter

    topicChapter: dict[str, str] = {}
    topicFirstSeq: dict[str, tuple[int, int]] = {}

    for pIdx, periodKey in enumerate(validPeriods):
        projected = applyProjections(periodRows.pop(periodKey, []), teacherTopics)
        for row in _expandStructuredRows(projected):
            chapter = row.get("chapter")
            topic = row.get("topic")
            text = row.get("text")
            blockType = row.get("blockType", "text")
            segmentKey = row.get("segmentKey")
            if not isinstance(chapter, str) or not isinstance(topic, str) or not isinstance(text, str):
                continue
            if topic not in topicChapter:
                topicChapter[topic] = chapter
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue
            if not isinstance(blockType, str):
                blockType = "text"
            if not isinstance(segmentKey, str) or not segmentKey:
                continue

            key = (topic, segmentKey)
            topicMap.setdefault(key, {})[periodKey] = text

            majorNum = int(row.get("majorNum", 99))
            sortOrder = int(row.get("sortOrder", 999999))
            if topic not in topicFirstSeq or (majorNum, sortOrder) < topicFirstSeq[topic]:
                topicFirstSeq[topic] = (majorNum, sortOrder)

            orderInfo = rowOrder.setdefault(
                key,
                {
                    "latestRank": 999999999,
                    "latestMissing": 1,
                    "firstRank": 999999999,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                    "_repPeriod": None,
                },
            )
            orderInfo["firstRank"] = min(orderInfo["firstRank"], sortOrder)
            orderInfo["sourceBlockOrder"] = min(orderInfo["sourceBlockOrder"], int(row.get("sourceBlockOrder") or 0))
            orderInfo["segmentOrder"] = min(orderInfo["segmentOrder"], int(row.get("segmentOrder") or 0))
            orderInfo["segmentOccurrence"] = min(orderInfo["segmentOccurrence"], int(row.get("segmentOccurrence") or 1))
            if periodKey == latestPeriod:
                orderInfo["latestMissing"] = 0
                orderInfo["latestRank"] = min(orderInfo["latestRank"], sortOrder)

            prevRank = representativePeriodRank(orderInfo.get("_repPeriod"))
            currRank = representativePeriodRank(periodKey)
            if currRank >= prevRank:
                orderInfo["_repPeriod"] = periodKey

        if pIdx % 4 == 3:
            gc.collect()

    if not topicMap:
        return []

    cadenceMetaByKey = {key: _rowCadenceMeta(periodMap) for key, periodMap in topicMap.items()}
    topicKeysByTopic: dict[str, list[tuple[str, str]]] = {}
    for key in topicMap:
        topicKeysByTopic.setdefault(key[0], []).append(key)

    topicIndex: dict[str, int] = {}
    for topic, _seq in sorted(topicFirstSeq.items(), key=lambda item: item[1]):
        topicIndex[topic] = len(topicIndex)

    cadencePriority = {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}

    def topicRowSortKey(key: tuple[str, str]) -> tuple[int, int, int, int, int, int, int, int, str]:
        topic, segmentKey = key
        majorNum, firstSeq = topicFirstSeq.get(topic, (99, 999999))
        tIdx = topicIndex.get(topic, 999999)
        info = rowOrder.get(key, {})
        cadenceMeta = cadenceMetaByKey.get(key, {})
        return (
            majorNum,
            firstSeq,
            tIdx,
            cadencePriority.get(str(cadenceMeta.get("cadenceScope") or "none"), 9),
            int(info.get("latestMissing", 1)),
            int(info.get("latestRank", 999999999)),
            int(info.get("firstRank", 999999999)),
            int(info.get("segmentOccurrence", 1)),
            str(segmentKey),
        )

    descendingPeriods = sortPeriods(validPeriods, descending=True)
    periodRange = formatPeriodRange(descendingPeriods, descending=True, annualAsQ4=True)
    sortedTopics = [topic for topic, _seq in sorted(topicFirstSeq.items(), key=lambda item: item[1])]

    rows: list[dict[str, Any]] = []
    for rowIdx, topic in enumerate(sortedTopics):
        topicKeys = sorted(topicKeysByTopic.get(topic, []), key=topicRowSortKey)
        periodCount = 0
        preview = "-"
        for period in descendingPeriods:
            firstText: str | None = None
            anyNonNull = False
            for key in topicKeys:
                value = topicMap.get(key, {}).get(period)
                if value is None:
                    continue
                anyNonNull = True
                if firstText is None:
                    firstText = str(value)
            if anyNonNull:
                periodCount += 1
                if preview == "-" and firstText is not None:
                    previewText = firstText.replace("\n", " ").strip()[:80]
                    preview = f"{displayPeriod(period, annualAsQ4=True)}: {previewText}"

        chapter = topicChapter.get(topic, "XII")
        chapterNum = _CHAPTER_ORDER.get(chapter, 12)
        rows.append(
            {
                "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": company._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"{periodCount}기간",
                "preview": preview,
                "_sortKey": (chapterNum, 100 + rowIdx),
            }
        )

    return rows


def buildIndexCandidate(company) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    rows.extend(company._indexFinanceRows())
    rows.extend(buildDocsRowsClone(company))
    existingTopics = {str(row["topic"]) for row in rows if isinstance(row.get("topic"), str)}
    rows.extend(company._indexReportRows(existingTopics=existingTopics))
    rows.sort(key=lambda row: row.get("_sortKey", (99, 999)))
    for row in rows:
        row.pop("_sortKey", None)
    if rows:
        return pl.DataFrame(rows)
    return pl.DataFrame(
        schema={
            "chapter": pl.Utf8,
            "topic": pl.Utf8,
            "label": pl.Utf8,
            "kind": pl.Utf8,
            "source": pl.Utf8,
            "periods": pl.Utf8,
            "shape": pl.Utf8,
            "preview": pl.Utf8,
        }
    )


def childRun(stockCode: str) -> dict[str, Any]:
    import dartlab

    candidateCompany = dartlab.Company(stockCode)
    candidate, candidateMetrics = measurePhase(lambda: buildIndexCandidate(candidateCompany))
    candidateCacheKeys = set(candidateCompany._cache._store.keys())
    candidateDigest = BASELINE.payloadDigest(candidate)
    candidateShape = BASELINE.payloadShape(candidate)
    del candidateCompany
    del candidate
    gc.collect()

    baselineCompany = dartlab.Company(stockCode)
    baseline, baselineMetrics = measurePhase(lambda: baselineCompany.index)
    baselineDigest = BASELINE.payloadDigest(baseline)
    baselineShape = BASELINE.payloadShape(baseline)

    return {
        "stockCode": stockCode,
        "exact": candidateDigest == baselineDigest,
        "candidateDigest": candidateDigest,
        "baselineDigest": baselineDigest,
        "candidateShape": candidateShape,
        "baselineShape": baselineShape,
        "candidateElapsedSec": candidateMetrics["elapsedSec"],
        "baselineElapsedSec": baselineMetrics["elapsedSec"],
        "candidateRssPeakMb": candidateMetrics["rssPeakMb"],
        "candidateRssDeltaMb": candidateMetrics["rssDeltaMb"],
        "candidateHasSections": ("sections" in candidateCacheKeys) or ("_sections" in candidateCacheKeys),
        "candidateHasProfileFacts": "_profileFacts" in candidateCacheKeys,
        "candidateHasRetrievalBlocks": "retrievalBlocks" in candidateCacheKeys,
    }


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        command = [
            "uv",
            "run",
            "python",
            "-X",
            "utf8",
            str(Path(__file__).resolve()),
            "--child",
            "--stockCode",
            stockCode,
        ]
        completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode != 0:
            raise RuntimeError(f"child failed: {stockCode}\nstdout={completed.stdout}\nstderr={completed.stderr}")
        rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    exact = sum(1 for row in rows if row["exact"])
    speedups = [
        row["baselineElapsedSec"] / row["candidateElapsedSec"]
        for row in rows
        if row["candidateElapsedSec"] > 0 and row["baselineElapsedSec"] > 0
    ]
    print(
        json.dumps(
            {
                "total": total,
                "exact": f"{exact}/{total}",
                "minSpeedup": round(min(speedups), 2) if speedups else None,
                "maxSpeedup": round(max(speedups), 2) if speedups else None,
                "hasSections": sum(1 for row in rows if row["candidateHasSections"]),
                "hasProfileFacts": sum(1 for row in rows if row["candidateHasProfileFacts"]),
                "hasRetrievalBlocks": sum(1 for row in rows if row["candidateHasRetrievalBlocks"]),
            },
            ensure_ascii=False,
        )
    )
    for row in rows:
        print(json.dumps(row, ensure_ascii=False))


def main() -> None:
    if "--child" in sys.argv:
        sys.argv.remove("--child")
        childMain()
        return
    rows = runParent()
    printSummary(rows)


if __name__ == "__main__":
    main()
