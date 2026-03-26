"""
실험 ID: 014
실험명: Report Hybrid Paths V2

목적:
- 013의 실패 원인(`executive show` 단일 block auto-expand, `audit trace` docs source coalesce 규칙)을 반영해 report 대표 topic 5종을 다시 전수 검증
- report hybrid 경로의 일반화 가능성을 최종 확인

가설:
1. blockless `show(topic)`는 block index가 1행이면 payload로 auto-expand해야 public semantics와 맞는다
2. docs trace source는 raw `topic == target`이 아니라 `coalesce(detailTopic, semanticTopic, topic) == target` 규칙을 써야 한다
3. 두 규칙을 넣으면 대표 report topic 5종 × 6종목 × (`show`,`trace`)가 전부 exact가 된다

방법:
1. 샘플 6종목 × report topic 5종 × (`show`, `trace`) 60개 case를 fresh subprocess 1회로 비교
2. show candidate는 012의 topic-scoped exact sections 기반 block index를 만들되, index가 1행이면 public 규칙대로 payload로 auto-expand한다
3. trace candidate는 006 report source + `coalesce(detailTopic, semanticTopic, topic)` 기준 docs source를 합친다
4. baseline public `company.show(topic)`, `company.trace(topic)`와 payload digest를 비교한다

결과 (실험 후 작성):
- 총 60개 case(6종목 × report topic 5종 × `show/trace`)를 fresh subprocess로 비교
- 전체 exact match: `60/60`
- `show`: exact `30/30`, 속도 `0.85~1.53x`, `_sections/_profileFacts/retrievalBlocks` 생성 `0건`
- `trace`: exact `30/30`, 속도 `2.43~5.00x`, `_sections/_profileFacts/retrievalBlocks` 생성 `0건`
- topic별 exact:
  - `dividend`: `12/12`
  - `employee`: `12/12`
  - `majorHolder`: `12/12`
  - `executive`: `12/12`
  - `audit`: `12/12`

결론:
- **채택**
- 013의 두 실패 원인만 바로잡으면 대표 report topic 5종의 blockless `show()`와 `trace()`를 모두 lightweight hybrid 경로로 일반화할 수 있다
- `show()`는 `single-row block index -> payload auto-expand`가 필수였고, `trace()`는 docs source를 `coalesce(detailTopic, semanticTopic, topic)` 기준으로 잡아야 exact가 된다
- report representative path는 014로 사실상 정리됐고, 이후 남은 큰 축은 `index`뿐이었다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline014")
SHOW = loadModule(Path(__file__).with_name("012_topicScopedSectionsExact.py"), "exp089Show014")
AUTH = loadModule(Path(__file__).with_name("006_authoritativeFollowUp.py"), "exp089Authoritative014")

REPORT_TOPICS = ["dividend", "employee", "majorHolder", "executive", "audit"]


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


def reportShowHybrid(company, stockCode: str, topic: str) -> Any:
    blockIndex = SHOW.buildCandidate(stockCode, topic)
    if not isinstance(blockIndex, pl.DataFrame):
        return blockIndex
    if blockIndex.height != 1:
        return blockIndex
    source = str(blockIndex["source"][0]) if "source" in blockIndex.columns else "docs"
    block = int(blockIndex["block"][0]) if "block" in blockIndex.columns else 0
    if source == "report":
        return company._showReportTopic(topic)
    if source == "finance":
        return company._showFinanceTopic(topic)
    return company.show(topic, block)


def buildDocsSource(stockCode: str, topic: str) -> dict[str, Any] | None:
    from dartlab.providers.dart.docs.sections import retrievalBlocks

    blocks = retrievalBlocks(stockCode)
    if blocks is None or blocks.is_empty():
        return None

    topicExpr = pl.col("topic")
    if "semanticTopic" in blocks.columns:
        topicExpr = pl.coalesce(pl.col("semanticTopic"), topicExpr)
    if "detailTopic" in blocks.columns:
        topicExpr = pl.coalesce(pl.col("detailTopic"), topicExpr)

    valueKeyExpr = topicExpr.cast(pl.Utf8)
    if "rawTitle" in blocks.columns:
        valueKeyExpr = pl.coalesce(pl.col("rawTitle"), valueKeyExpr)
    if "blockLabel" in blocks.columns:
        valueKeyExpr = pl.coalesce(pl.col("blockLabel"), valueKeyExpr)

    payloadExpr = pl.concat_str([pl.lit("docs:"), topicExpr.cast(pl.Utf8), pl.lit(":"), pl.col("period").cast(pl.Utf8)])
    if "cellKey" in blocks.columns:
        payloadExpr = pl.coalesce(pl.col("cellKey"), payloadExpr)

    docsDf = (
        blocks.filter(pl.col("period").is_not_null() & pl.col("blockText").is_not_null() & (pl.col("blockText") != ""))
        .with_columns(topicExpr.alias("_topic"))
        .filter(pl.col("_topic") == topic)
        .select(
            [
                pl.col("_topic").cast(pl.Utf8).alias("topic"),
                pl.col("period").cast(pl.Utf8).alias("period"),
                pl.lit("docs").alias("source"),
                (pl.col("blockType") if "blockType" in blocks.columns else pl.lit("text")).alias("valueType"),
                valueKeyExpr.alias("valueKey"),
                pl.col("blockText").cast(pl.Utf8).alias("value"),
                payloadExpr.alias("payloadRef"),
                pl.lit(100).alias("priority"),
                pl.col("blockText").cast(pl.Utf8).str.slice(0, 400).alias("summary"),
            ]
        )
    )
    if docsDf.is_empty():
        return None
    first = docsDf.row(0, named=True)
    return {
        "source": "docs",
        "rows": int(docsDf.height),
        "payloadRef": first["payloadRef"],
        "summary": first["summary"],
        "priority": 100,
    }


def reportTraceHybrid(company, stockCode: str, topic: str) -> dict[str, Any] | None:
    reportTrace = AUTH.reportTraceFast(company, topic)
    docsSource = buildDocsSource(stockCode, topic)
    if reportTrace is None and docsSource is None:
        return None

    sources: list[dict[str, Any]] = []
    if reportTrace is not None:
        sources.extend(reportTrace["availableSources"])
    if docsSource is not None:
        sources.append(docsSource)
    sources.sort(key=lambda row: (row.get("priority", 0), row.get("source", "")), reverse=True)
    primary = sources[0]
    return {
        "topic": topic,
        "period": None,
        "primarySource": primary.get("source"),
        "fallbackSources": [row.get("source") for row in sources[1:]],
        "selectedPayloadRef": primary.get("payloadRef"),
        "availableSources": sources,
        "whySelected": "report authoritative priority",
    }


def childRun(stockCode: str, topic: str, caseName: str) -> dict[str, Any]:
    import dartlab

    candidateCompany = dartlab.Company(stockCode)
    if caseName == "show":
        candidate, candidateMetrics = measurePhase(
            lambda company=candidateCompany: reportShowHybrid(company, stockCode, topic)
        )
    else:
        candidate, candidateMetrics = measurePhase(
            lambda company=candidateCompany: reportTraceHybrid(company, stockCode, topic)
        )
    candidateCacheKeys = set(candidateCompany._cache._store.keys())
    candidateDigest = BASELINE.payloadDigest(candidate)
    candidateShape = BASELINE.payloadShape(candidate)
    del candidateCompany
    del candidate
    gc.collect()

    baselineCompany = dartlab.Company(stockCode)
    if caseName == "show":
        baseline, baselineMetrics = measurePhase(lambda: baselineCompany.show(topic))
    else:
        baseline, baselineMetrics = measurePhase(lambda: baselineCompany.trace(topic))
    baselineDigest = BASELINE.payloadDigest(baseline)
    baselineShape = BASELINE.payloadShape(baseline)

    return {
        "stockCode": stockCode,
        "topic": topic,
        "caseName": caseName,
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
    parser.add_argument("--topic", required=True)
    parser.add_argument("--caseName", required=True, choices=["show", "trace"])
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.topic, args.caseName), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        for topic in REPORT_TOPICS:
            for caseName in ("show", "trace"):
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
                    "--topic",
                    topic,
                    "--caseName",
                    caseName,
                ]
                completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
                if completed.returncode != 0:
                    raise RuntimeError(
                        f"child failed: {stockCode} {topic} {caseName}\nstdout={completed.stdout}\nstderr={completed.stderr}"
                    )
                rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    exact = sum(1 for row in rows if row["exact"])
    print(json.dumps({"total": total, "exact": f"{exact}/{total}"}, ensure_ascii=False))
    for caseName in ("show", "trace"):
        scoped = [row for row in rows if row["caseName"] == caseName]
        exactCount = sum(1 for row in scoped if row["exact"])
        speedups = [
            row["baselineElapsedSec"] / row["candidateElapsedSec"]
            for row in scoped
            if row["candidateElapsedSec"] > 0 and row["baselineElapsedSec"] > 0
        ]
        print(
            json.dumps(
                {
                    "caseName": caseName,
                    "exact": f"{exactCount}/{len(scoped)}",
                    "minSpeedup": round(min(speedups), 2) if speedups else None,
                    "maxSpeedup": round(max(speedups), 2) if speedups else None,
                    "hasSections": sum(1 for row in scoped if row["candidateHasSections"]),
                    "hasProfileFacts": sum(1 for row in scoped if row["candidateHasProfileFacts"]),
                    "hasRetrievalBlocks": sum(1 for row in scoped if row["candidateHasRetrievalBlocks"]),
                },
                ensure_ascii=False,
            )
        )
    for topic in REPORT_TOPICS:
        scoped = [row for row in rows if row["topic"] == topic]
        print(json.dumps({"topic": topic, "exact": f"{sum(1 for row in scoped if row['exact'])}/{len(scoped)}"}, ensure_ascii=False))
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
