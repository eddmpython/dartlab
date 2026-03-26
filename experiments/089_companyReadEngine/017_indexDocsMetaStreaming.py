"""
실험 ID: 017
실험명: Index Docs Meta Streaming

목적:
- `docs.sections` 전체 materialization 없이도 public `index`의 docs rows를 exact 재현할 수 있는지 검증
- full `index`에서 가장 비싼 docs source rows만 streaming metadata 집계로 대체 가능한지 확인

가설:
1. `sections` 내부 expansion 공식을 그대로 쓰되 rows를 저장하지 않고 topic metadata만 집계하면 docs rows exact가 나온다
2. finance + docs-streaming + current report rows 조합이면 full `index`도 exact가 되면서 메모리가 크게 줄어든다

방법:
1. 샘플 6종목에 대해 candidate full `index`와 baseline public `company.index`를 fresh subprocess로 비교한다
2. docs candidate는 `iterPeriodSubsets -> _reportRowsToTopicRows -> applyProjections -> _expandStructuredRows`를 그대로 타되 topic별 `chapter/periodCount/preview/topicOrder`만 집계한다
3. report rows는 현재 exact semantics를 유지하기 위해 `company._indexReportRows(existingTopics=...)`를 그대로 사용한다
4. payload digest, 시간, peak RSS, heavy cache 생성 여부를 기록한다

결과 (실험 후 작성):
- 총 6개 case(6종목 × full `index`)를 same-process candidate/baseline 비교로 검증
- exact match: `0/6`
- candidate shape는 `6/6` 모두 baseline과 같았다
- 같은 프로세스 비교 기준 속도는 `0.86~1.34x`였고, candidate peak RSS는 `353.7~517.2MB`였다
- `_sections/_profileFacts/retrievalBlocks` 생성은 `0/6`이었다

결론:
- **기각**
- `sections()` 내부 expansion을 쓰더라도 latest-first encounter 방식으로 topic order/chapter를 잡으면 public `index` docs rows exact가 되지 않는다
- 실패 원인은 성능이 아니라 ordering semantics였다. 특히 `dividend` 같은 topic의 chapter/order가 실제 `sections()` 공식을 따라가지 못했다
- 이 실패가 018에서 `topicChapter + topicFirstSeq + _topicRowSortKey`를 그대로 복제해야 한다는 근거가 되었다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline017")


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


def buildDocsRowsStreaming(company) -> list[dict[str, Any]]:
    from dartlab.providers.dart.company import _CHAPTER_ORDER, _CHAPTER_TITLES, _isPeriodColumn
    from dartlab.providers.dart.docs.sections import displayPeriod, formatPeriodRange, sortPeriods
    from dartlab.providers.dart.docs.sections.pipeline import (
        _expandStructuredRows,
        _reportRowsToTopicRows,
        applyProjections,
        chapterTeacherTopics,
        detailTopicForTopic,
        iterPeriodSubsets,
        projectionSuppressedTopics,
    )

    periodRows: dict[str, list[dict[str, Any]]] = {}
    validPeriods: list[str] = []
    latestAnnualRows: list[dict[str, Any]] | None = None

    for periodKey, reportKind, ccol, subset in iterPeriodSubsets(company.stockCode):
        validPeriods.append(periodKey)
        topicRows = _reportRowsToTopicRows(subset, ccol)
        periodRows[periodKey] = topicRows
        if reportKind == "annual" and latestAnnualRows is None:
            latestAnnualRows = topicRows

    if not validPeriods:
        return []

    teacherTopics = chapterTeacherTopics(latestAnnualRows or [])
    suppressed = projectionSuppressedTopics()
    periodCols = sortPeriods([period for period in validPeriods if _isPeriodColumn(period)], descending=True)
    periodRange = formatPeriodRange(periodCols, descending=True, annualAsQ4=True)

    topicMeta: dict[str, dict[str, Any]] = {}
    topicOrder: list[str] = []

    for periodKey in periodCols:
        projected = applyProjections(periodRows.get(periodKey, []), teacherTopics)
        expanded = _expandStructuredRows(projected)
        for row in expanded:
            topic = row.get("topic")
            chapter = row.get("chapter")
            textValue = row.get("text")
            if not isinstance(topic, str) or not topic:
                continue
            if not isinstance(chapter, str) or not chapter:
                continue
            if topic in suppressed.get(chapter, set()):
                continue
            if detailTopicForTopic(topic) is not None:
                continue

            meta = topicMeta.setdefault(
                topic,
                {
                    "chapter": chapter,
                    "periods": set(),
                    "firstTextByPeriod": {},
                },
            )
            if topic not in topicOrder:
                topicOrder.append(topic)
            if meta.get("chapter") in {None, "", "XII"} and chapter != "XII":
                meta["chapter"] = chapter
            if textValue is not None:
                meta["periods"].add(periodKey)
                if periodKey not in meta["firstTextByPeriod"]:
                    meta["firstTextByPeriod"][periodKey] = str(textValue)

        gc.collect()

    rows: list[dict[str, Any]] = []
    for rowIdx, topic in enumerate(topicOrder):
        meta = topicMeta[topic]
        chapter = str(meta.get("chapter") or "XII")
        firstText = None
        latestPeriod = None
        for period in periodCols:
            if period in meta["firstTextByPeriod"]:
                latestPeriod = period
                firstText = str(meta["firstTextByPeriod"][period]).replace("\n", " ").strip()[:80]
                break
        preview = "-" if latestPeriod is None else f"{displayPeriod(latestPeriod, annualAsQ4=True)}: {firstText}"
        chapterNum = _CHAPTER_ORDER.get(chapter, 12)
        rows.append(
            {
                "chapter": _CHAPTER_TITLES.get(chapter, chapter),
                "topic": topic,
                "label": company._topicLabel(topic),
                "kind": "docs",
                "source": "docs",
                "periods": periodRange,
                "shape": f"{len(meta['periods'])}기간",
                "preview": preview,
                "_sortKey": (chapterNum, 100 + rowIdx),
            }
        )
    return rows


def buildIndexCandidate(company) -> pl.DataFrame:
    rows: list[dict[str, Any]] = []
    financeRows = company._indexFinanceRows()
    docsRows = buildDocsRowsStreaming(company)
    rows.extend(financeRows)
    rows.extend(docsRows)
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
