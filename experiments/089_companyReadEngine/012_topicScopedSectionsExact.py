"""
실험 ID: 012
실험명: Topic-Scoped Sections Exact

목적:
- `sections()` 전체를 만들지 않고 topic 하나에 대해서만 동일한 blockOrder/period 정렬을 재현할 수 있는지 검증
- docs `show()`와 report blockless `show()`를 topic-scoped exact sections 경로로 대체할 가능성을 확인

가설:
1. `sections()`의 집계 공식을 topic 하나에만 적용해도 public blockless `show(topic)`와 exact가 나온다
2. docs `companyOverview`, `businessOverview`와 report `majorHolder` 모두 같은 topic-scoped exact sections 축으로 설명된다

방법:
1. 샘플 6종목에 대해 `companyOverview`, `businessOverview`, 대표 report topic(`majorHolder`) blockless `show()`를 fresh subprocess에서 비교
2. candidate는 `iterPeriodSubsets -> _reportRowsToTopicRows -> applyProjections -> _expandStructuredRows`를 그대로 타되 target topic만 남긴다
3. topic별 `segmentKey` 집계, `latestRank/firstRank/cadenceScope` 정렬, `blockOrder` 재부여를 `sections()`와 같은 규칙으로 수행한다
4. docs rows로 `buildBlockIndex`를 만들고, report topic이면 마지막에 synthetic report row 1개를 붙인다
5. baseline public `company.show(topic)`와 payload digest, 시간, 피크 RSS를 비교한다

결과 (실험 후 작성):
- 총 18개 case(`companyOverview`, `businessOverview`, `majorHolder` × 6종목)를 fresh subprocess로 비교
- exact match: `18/18`
- topic별 속도:
  - `companyOverview`: `0.93~1.51x`
  - `businessOverview`: `0.97~1.27x`
  - `majorHolder`: `0.98~1.42x`
- candidate peak RSS는 대략 `314~545MB` 범위였다
- docs `companyOverview`, `businessOverview`와 report blockless `show("majorHolder")` 모두 public payload와 같았다

결론:
- **채택**
- period column을 `profile.sections`와 동일하게 `descending + annualAsQ4`로 재정렬하면 topic-scoped exact sections 경로가 public blockless `show(topic)` semantics를 맞춘다
- docs `show()` 2종과 report blockless `show("majorHolder")`는 full `sections` 없이도 exact reconstruction이 가능하다
- 속도 이득은 크지 않지만 exact가 확보됐고, 이후 014 report hybrid path의 show 축 기초가 되었다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline012")
POLARS_SPLIT = loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit012")


DOC_TOPICS = ["companyOverview", "businessOverview"]


def hasReportTopic(stockCode: str, topic: str) -> bool:
    return topic in {POLARS_SPLIT.reportUserTopic(apiType) for apiType in POLARS_SPLIT.fastAvailableApiTypes(stockCode)}


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


def buildTopicScopedSections(stockCode: str, targetTopic: str) -> pl.DataFrame | None:
    from dartlab.engines.company.dart.docs.sections.pipeline import (
        _expandStructuredRows,
        _reportRowsToTopicRows,
        _rowCadenceMeta,
        applyProjections,
        chapterTeacherTopics,
        detailTopicForTopic,
        iterPeriodSubsets,
        projectionSuppressedTopics,
        sortPeriods,
    )

    topicMap: dict[str, dict[str, str]] = {}
    rowMeta: dict[str, dict[str, object]] = {}
    rowOrder: dict[str, dict[str, int]] = {}
    periodRows: dict[str, list[dict[str, object]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, object]] | None = None
    suppressed = projectionSuppressedTopics()
    topicFirstSeq: tuple[int, int] | None = None

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset, ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    if not validPeriods:
        return None

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    validPeriods = sortPeriods(validPeriods)
    latestPeriod = validPeriods[-1]

    def representativeRank(period: str | None) -> int:
        if not isinstance(period, str):
            return -1
        year = int(period[:4])
        quarter = {"Q1": 1, "Q2": 2, "Q3": 3}.get(period[4:], 4)
        return (year * 10) + quarter

    for periodKey in validPeriods:
        projected = applyProjections(periodRows.get(periodKey, []), teacherTopics)
        expanded = _expandStructuredRows(projected)
        for row in expanded:
            chapter = row.get("chapter")
            topic = row.get("topic")
            text = row.get("text")
            blockType = row.get("blockType", "text")
            segmentKey = row.get("segmentKey")
            if topic != targetTopic:
                continue
            if not isinstance(chapter, str) or not isinstance(text, str):
                continue
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(str(topic)) is not None:
                continue
            if not isinstance(segmentKey, str) or not segmentKey:
                continue
            if not isinstance(blockType, str):
                blockType = "text"

            topicMap.setdefault(segmentKey, {})[periodKey] = text
            majorNum = int(row.get("majorNum", 99))
            sortOrder = int(row.get("sortOrder", 999999))
            if topicFirstSeq is None or (majorNum, sortOrder) < topicFirstSeq:
                topicFirstSeq = (majorNum, sortOrder)

            orderInfo = rowOrder.setdefault(
                segmentKey,
                {
                    "latestRank": 999999999,
                    "latestMissing": 1,
                    "firstRank": 999999999,
                    "sourceBlockOrder": int(row.get("sourceBlockOrder") or 0),
                    "segmentOrder": int(row.get("segmentOrder") or 0),
                    "segmentOccurrence": int(row.get("segmentOccurrence") or 1),
                },
            )
            orderInfo["firstRank"] = min(orderInfo["firstRank"], sortOrder)
            orderInfo["sourceBlockOrder"] = min(orderInfo["sourceBlockOrder"], int(row.get("sourceBlockOrder") or 0))
            orderInfo["segmentOrder"] = min(orderInfo["segmentOrder"], int(row.get("segmentOrder") or 0))
            orderInfo["segmentOccurrence"] = min(orderInfo["segmentOccurrence"], int(row.get("segmentOccurrence") or 1))
            if periodKey == latestPeriod:
                orderInfo["latestMissing"] = 0
                orderInfo["latestRank"] = min(orderInfo["latestRank"], sortOrder)

            prevMeta = rowMeta.get(segmentKey)
            prevRank = representativeRank(prevMeta.get("_repPeriod")) if isinstance(prevMeta, dict) else -1
            currRank = representativeRank(periodKey)
            if prevMeta is None or currRank >= prevRank:
                rowMeta[segmentKey] = {
                    "blockType": blockType,
                    "_repPeriod": periodKey,
                }

        gc.collect()

    if not topicMap or topicFirstSeq is None:
        return None

    cadenceMetaByKey = {key: _rowCadenceMeta(periodMap) for key, periodMap in topicMap.items()}
    cadencePriority = {"mixed": 0, "annual": 1, "quarterly": 2, "none": 3}

    def sortKey(segmentKey: str) -> tuple[int, int, int, int, int, str]:
        info = rowOrder.get(segmentKey, {})
        cadenceMeta = cadenceMetaByKey.get(segmentKey, {})
        return (
            cadencePriority.get(str(cadenceMeta.get("cadenceScope") or "none"), 9),
            int(info.get("latestMissing", 1)),
            int(info.get("latestRank", 999999999)),
            int(info.get("firstRank", 999999999)),
            int(info.get("segmentOccurrence", 1)),
            str(segmentKey),
        )

    rows: list[dict[str, Any]] = []
    for blockOrder, segmentKey in enumerate(sorted(topicMap.keys(), key=sortKey)):
        row = {
            "topic": targetTopic,
            "blockType": str(rowMeta.get(segmentKey, {}).get("blockType") or "text"),
            "blockOrder": blockOrder,
            "source": "docs",
        }
        for period in validPeriods:
            row[period] = topicMap[segmentKey].get(period)
        rows.append(row)

    return pl.DataFrame(rows)


def buildCandidate(stockCode: str, topic: str) -> pl.DataFrame | None:
    from dartlab.engines.common.show import buildBlockIndex
    from dartlab.engines.company.dart.docs.sections import reorderPeriodColumns

    docsSec = buildTopicScopedSections(stockCode, topic)
    if docsSec is None:
        docsSec = pl.DataFrame({"topic": [], "blockType": [], "blockOrder": [], "source": []})

    frames: list[pl.DataFrame] = []
    if docsSec.height > 0:
        frames.append(docsSec)
    if hasReportTopic(stockCode, topic):
        nextBlock = 0 if docsSec.height == 0 else int(docsSec["blockOrder"].max()) + 1
        frames.append(
            pl.DataFrame(
                {
                    "topic": [topic],
                    "blockType": ["table"],
                    "blockOrder": [nextBlock],
                    "source": ["report"],
                }
            )
        )
    if not frames:
        return None
    merged = pl.concat(frames, how="diagonal_relaxed")
    merged = reorderPeriodColumns(merged, descending=True, annualAsQ4=True)
    return buildBlockIndex(merged)


def childRun(stockCode: str, topic: str) -> dict[str, Any]:
    import dartlab

    candidate, candidateMetrics = measurePhase(lambda: buildCandidate(stockCode, topic))
    candidateDigest = BASELINE.payloadDigest(candidate)
    candidateShape = BASELINE.payloadShape(candidate)

    gc.collect()

    baselineCompany = dartlab.Company(stockCode)
    baseline, baselineMetrics = measurePhase(lambda: baselineCompany.show(topic))
    baselineDigest = BASELINE.payloadDigest(baseline)
    baselineShape = BASELINE.payloadShape(baseline)
    baselineCacheKeys = set(baselineCompany._cache._store.keys())

    return {
        "stockCode": stockCode,
        "topic": topic,
        "exact": candidateDigest == baselineDigest,
        "candidateDigest": candidateDigest,
        "baselineDigest": baselineDigest,
        "candidateShape": candidateShape,
        "baselineShape": baselineShape,
        "candidateElapsedSec": candidateMetrics["elapsedSec"],
        "baselineElapsedSec": baselineMetrics["elapsedSec"],
        "candidateRssPeakMb": candidateMetrics["rssPeakMb"],
        "candidateRssDeltaMb": candidateMetrics["rssDeltaMb"],
        "baselineHasSections": ("sections" in baselineCacheKeys) or ("_sections" in baselineCacheKeys),
    }


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.topic), ensure_ascii=False))


def caseSpecs() -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        for topic in DOC_TOPICS:
            specs.append({"stockCode": stockCode, "topic": topic})
        reportTopic = BASELINE.chooseReportTopic(stockCode)
        if reportTopic is not None:
            specs.append({"stockCode": stockCode, "topic": reportTopic})
    return specs


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in caseSpecs():
        command = [
            "uv",
            "run",
            "python",
            "-X",
            "utf8",
            str(Path(__file__).resolve()),
            "--child",
            "--stockCode",
            spec["stockCode"],
            "--topic",
            spec["topic"],
        ]
        completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode != 0:
            raise RuntimeError(f"child failed: {spec}\nstdout={completed.stdout}\nstderr={completed.stderr}")
        rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    byTopic: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        byTopic.setdefault(row["topic"], []).append(row)
    print(
        json.dumps(
            {"total": len(rows), "exact": f"{sum(1 for row in rows if row['exact'])}/{len(rows)}"}, ensure_ascii=False
        )
    )
    for topic, topicRows in byTopic.items():
        exact = sum(1 for row in topicRows if row["exact"])
        speedups = [
            row["baselineElapsedSec"] / row["candidateElapsedSec"]
            for row in topicRows
            if row["candidateElapsedSec"] > 0 and row["baselineElapsedSec"] > 0
        ]
        print(
            json.dumps(
                {
                    "topic": topic,
                    "exact": f"{exact}/{len(topicRows)}",
                    "minSpeedup": round(min(speedups), 2) if speedups else None,
                    "maxSpeedup": round(max(speedups), 2) if speedups else None,
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
