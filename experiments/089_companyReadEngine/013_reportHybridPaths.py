"""
실험 ID: 013
실험명: Report Hybrid Paths Generalization

목적:
- `majorHolder`에서 확인한 report hybrid 경로가 대표 report topic 5종 전체에 일반화되는지 검증
- blockless `show(topic)`와 `trace(topic)`를 topic-scoped exact sections + direct report/docs source 조합으로 재현 가능한지 확인

가설:
1. `dividend`, `employee`, `majorHolder`, `executive`, `audit`의 blockless `show(topic)`는 012 후보로 exact 재현된다
2. 같은 5종의 `trace(topic)`는 010 dual-source 후보로 exact 재현된다

방법:
1. 샘플 6종목 × report topic 5종 × (`show`, `trace`) 60개 case를 fresh subprocess 1회로 비교한다
2. show candidate는 012의 `buildCandidate(stockCode, topic)`를 재사용한다
3. trace candidate는 010의 `reportTraceDualSource(company, stockCode, topic)`를 재사용한다
4. baseline public `company.show(topic)`, `company.trace(topic)`와 payload digest를 비교한다

결과 (실험 후 작성):
- 총 60개 case(6종목 × 5개 report topic × `show/trace`)를 fresh subprocess로 비교
- 전체 exact match: `48/60`
- `show`: exact `24/30`, 속도 `0.94~1.49x`, `_sections/_profileFacts/retrievalBlocks` 생성 `0건`
- `trace`: exact `24/30`, 속도 `2.80~4.88x`, `_sections/_profileFacts/retrievalBlocks` 생성 `0건`
- topic별 exact:
  - `dividend`: `12/12`
  - `employee`: `12/12`
  - `majorHolder`: `12/12`
  - `executive`: `6/12`
  - `audit`: `6/12`
- `executive`는 `trace`만 exact이고 blockless `show()`는 6종목 모두 `1x4` candidate vs `271~1176x11` baseline으로 실패했다
- `audit`는 blockless `show()`는 6/6 exact였지만 `trace()`는 6종목 모두 digest가 달랐다

결론:
- **부분 채택**
- report hybrid 경로는 `dividend`, `employee`, `majorHolder`에서는 `show/trace` 모두 일반화됐다
- `executive`는 `trace()`는 exact지만 blockless `show()`는 아직 public semantics를 못 맞춘다
- `audit`는 blockless `show()`는 exact지만 `trace()` source 조합이 baseline과 달라 추가 규칙이 필요하다
- heavy cache 3종을 전혀 만들지 않고도 48/60 exact를 확보했으므로, report topic별 분기 설계는 유지할 가치가 있다

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

import psutil


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline013")
SHOW = loadModule(Path(__file__).with_name("012_topicScopedSectionsExact.py"), "exp089Show013")
TRACE = loadModule(Path(__file__).with_name("010_reportTraceDualSource.py"), "exp089Trace013")

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


def childRun(stockCode: str, topic: str, caseName: str) -> dict[str, Any]:
    import dartlab

    candidateCompany = dartlab.Company(stockCode)
    if caseName == "show":
        candidate, candidateMetrics = measurePhase(lambda: SHOW.buildCandidate(stockCode, topic))
    else:
        candidate, candidateMetrics = measurePhase(
            lambda company=candidateCompany: TRACE.reportTraceDualSource(company, stockCode, topic)
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
        print(
            json.dumps(
                {
                    "topic": topic,
                    "exact": f"{sum(1 for row in scoped if row['exact'])}/{len(scoped)}",
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
