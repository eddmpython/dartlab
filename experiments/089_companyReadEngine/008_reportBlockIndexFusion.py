"""
실험 ID: 008
실험명: Report Block Index Fusion

목적:
- `majorHolder` 같은 report authoritative topic의 public `show()` block index를 raw docs + synthetic report row로 exact 재현 가능한지 검증
- full `sections` 없이 report topic block index만 따로 분리할 가능성을 확인

가설:
1. `majorHolder` public `show()`는 docs block index 뒤에 report block 1개가 붙은 구조다
2. raw docs block index에 `(report)` synthetic row를 추가하면 baseline과 exact 동일하다

방법:
1. 샘플 6종목에 대해 fresh subprocess에서 대표 report topic의 public `show(topic)` baseline을 수집한다
2. candidate는 `002.buildDocsTopicBlockIndex(stockCode, topic)`로 docs block index를 만든다
3. report parquet에 해당 topic이 있으면 마지막 block에 `type=table, source=report, preview=(report)` row를 추가한다
4. baseline과 payload digest, 시간, 피크 RSS를 비교한다

결과 (실험 후 작성):
- 총 6개 case를 fresh subprocess 1회로 비교
- exact match: `0/6`
- candidate는 baseline 대비 `22.69~62.90x` 빨랐지만 payload가 모두 달랐다
- baseline public `show("majorHolder")`는 6/6 모두 `_sections` cache를 생성했다
- candidate shape vs baseline shape:
  - `005930`: `35x4` vs `83x4`
  - `000660`: `74x4` vs `654x4`
  - `005380`: `40x4` vs `127x4`
  - `105560`: `29x4` vs `68x4`
  - `035420`: `21x4` vs `89x4`
  - `005490`: `24x4` vs `130x4`
- latest docs subset로 만든 block index는 public docs block 수를 크게 과소계산했다

결론:
- **기각**
- `majorHolder` public `show()`는 raw docs 최신 subset + synthetic report row만으로는 exact 재현이 안 된다
- mismatch의 핵심은 report row가 아니라 docs block identity다
- 즉 report authoritative topic이라도 public block index는 기간 정렬/블록 정합 규칙을 함께 가져와야 한다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline008")
POLARS_SPLIT = loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit008")


def hasReportTopic(stockCode: str, topic: str) -> bool:
    return topic in {POLARS_SPLIT.reportUserTopic(apiType) for apiType in POLARS_SPLIT.fastAvailableApiTypes(stockCode)}


def fusedBlockIndex(stockCode: str, topic: str) -> pl.DataFrame | None:
    docsIndex = POLARS_SPLIT.buildDocsTopicBlockIndex(stockCode, topic)
    if docsIndex is None:
        docsIndex = pl.DataFrame({"block": [], "type": [], "source": [], "preview": []})

    if not hasReportTopic(stockCode, topic):
        return docsIndex if docsIndex.height > 0 else None

    nextBlock = 0 if docsIndex.height == 0 else int(docsIndex["block"].max()) + 1
    reportRow = pl.DataFrame(
        {
            "block": [nextBlock],
            "type": ["table"],
            "source": ["report"],
            "preview": ["(report)"],
        }
    )
    return pl.concat([docsIndex, reportRow], how="vertical")


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

    candidate, candidateMetrics = measurePhase(lambda: fusedBlockIndex(stockCode, topic))
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
                "baselineHasSections": f"{sum(1 for row in rows if row['baselineHasSections'])}/{len(rows)}",
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
