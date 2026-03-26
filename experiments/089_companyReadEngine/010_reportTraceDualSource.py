"""
실험 ID: 010
실험명: Report Trace Dual-Source Candidate

목적:
- `trace("majorHolder")`를 `sections/profile.facts` 없이 exact 재현 가능한지 최종 확인
- report source + retrievalBlocks docs source 조합이 full trace dict까지 동일한지 검증

가설:
1. 009에서 확인한 source별 공식으로 full `trace("majorHolder")` dict를 exact 재현할 수 있다
2. candidate는 `_sections/_profileFacts/retrievalBlocks` cache를 만들지 않는다

방법:
1. 샘플 6종목을 fresh subprocess에서 실행한다
2. candidate는 006의 report direct trace source와 raw `retrievalBlocks(topic)` docs source를 합쳐 full dict를 만든다
3. baseline public `company.trace(topic)`와 payload digest를 비교한다
4. candidate 단계의 elapsed, RSS, heavy cache 생성 여부를 기록한다

결과 (실험 후 작성):
- 총 6개 case를 fresh subprocess 1회로 비교
- exact match: `6/6`
- candidate는 baseline 대비 `3.66~4.74x` 빨랐다
- candidate 단계에서 `_sections`, `_profileFacts`, `retrievalBlocks` cache 생성 `0건`
- candidate peak RSS는 `568.7~920.4MB`였다
- representative report topic `majorHolder`에 대해 full trace dict exact reconstruction이 성립했다

결론:
- **채택 후보**
- `trace("majorHolder")`는 `report direct source + retrievalBlocks docs source`만으로 exact 재현 가능하다
- 문제는 더 이상 동일성이 아니라 비용이다. `retrievalBlocks`가 아직 무거워서 peak RSS는 완전히 작지 않다
- 그래도 `sections/profile.facts`를 피하면서 exact와 속도 이득을 동시에 확보한 첫 report path다

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
from functools import partial
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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline010")
AUTH = loadModule(Path(__file__).with_name("006_authoritativeFollowUp.py"), "exp089Authoritative010")


def buildDocsSource(stockCode: str, topic: str) -> dict[str, Any] | None:
    from dartlab.providers.dart.docs.sections import retrievalBlocks

    blocks = retrievalBlocks(stockCode).filter(pl.col("topic") == topic)
    if blocks.is_empty():
        return None
    return {
        "source": "docs",
        "rows": int(blocks.height),
        "payloadRef": str(blocks["cellKey"][0]),
        "summary": str(blocks["blockText"][0])[:400],
        "priority": 100,
    }


def reportTraceDualSource(company, stockCode: str, topic: str) -> dict[str, Any] | None:
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


def childRun(stockCode: str, topic: str) -> dict[str, Any]:
    import dartlab

    candidateCompany = dartlab.Company(stockCode)
    candidateAction = partial(reportTraceDualSource, candidateCompany, stockCode, topic)
    candidate, candidateMetrics = measurePhase(candidateAction)
    candidateCacheKeys = set(candidateCompany._cache._store.keys())
    candidateDigest = BASELINE.payloadDigest(candidate)
    candidateShape = BASELINE.payloadShape(candidate)
    del candidateCompany
    del candidate
    gc.collect()

    baselineCompany = dartlab.Company(stockCode)
    baseline, baselineMetrics = measurePhase(lambda: baselineCompany.trace(topic))
    baselineDigest = BASELINE.payloadDigest(baseline)
    baselineShape = BASELINE.payloadShape(baseline)

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
        "candidateHasSections": ("sections" in candidateCacheKeys) or ("_sections" in candidateCacheKeys),
        "candidateHasProfileFacts": "_profileFacts" in candidateCacheKeys,
        "candidateHasRetrievalBlocks": "retrievalBlocks" in candidateCacheKeys,
    }


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.topic), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        topic = BASELINE.chooseReportTopic(stockCode)
        if topic is None:
            continue
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
        ]
        completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode != 0:
            raise RuntimeError(
                f"child failed: {stockCode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    exact = sum(1 for row in rows if row["exact"])
    speedups = [
        row["baselineElapsedSec"] / row["candidateElapsedSec"]
        for row in rows
        if row["candidateElapsedSec"] > 0 and row["baselineElapsedSec"] > 0
    ]
    print(
        json.dumps(
            {
                "total": len(rows),
                "exact": f"{exact}/{len(rows)}",
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
