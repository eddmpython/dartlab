"""
실험 ID: 019
실험명: Index Exact Fresh Rebaseline

목적:
- 018 exact candidate의 시간/메모리 개선폭을 fresh subprocess 기준으로 다시 측정
- 같은 프로세스 내 candidate→baseline 순서로 인한 편향 없이 실제 성능 차이를 확인

가설:
1. 018 candidate는 fresh subprocess 기준에서도 public `index`와 exact가 같다
2. `docs.sections`를 만들지 않으므로 peak RSS는 baseline보다 유의미하게 낮다
3. 시간은 큰 폭 개선이 아니어도 baseline보다 최소 동급 이상이다

방법:
1. 샘플 6종목에 대해 baseline과 candidate를 각각 별도 fresh subprocess에서 1회씩 실행한다
2. candidate는 018의 `buildIndexCandidate(company)`를 그대로 사용한다
3. payload digest, elapsed, rssPeak, heavy cache 생성 여부를 모드별로 기록한다
4. 종목별 exact 여부와 speedup, peak RSS 절감률을 계산한다

결과 (실험 후 작성):
- 총 6개 case(6종목)를 baseline/candidate 각각 별도 fresh subprocess로 비교
- exact match: `6/6`
- 속도: baseline 대비 `1.28~2.79x`
- peak RSS 절감: `29.1~36.3%`
- baseline은 `_sections` 생성 `6/6`, candidate는 `_sections` 생성 `0/6`
- 종목별 결과:
  - `005930`: `1.50x`, peak `688.4MB -> 457.1MB`
  - `000660`: `1.38x`, peak `542.6MB -> 358.3MB`
  - `005380`: `1.28x`, peak `664.4MB -> 471.1MB`
  - `105560`: `2.79x`, peak `807.6MB -> 514.2MB`
  - `035420`: `1.42x`, peak `675.8MB -> 452.6MB`
  - `005490`: `1.50x`, peak `790.9MB -> 506.7MB`

결론:
- **채택**
- 018 exact candidate는 fresh subprocess 기준에서도 결과가 완전히 같고, 시간과 메모리 모두 baseline보다 실제로 낫다
- current public `index`의 본질적 낭비는 `docs.sections` materialization이었다
- 이 축은 이제 실험상 `exact + no-sections + measurable win`까지 확보됐다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline019")
EXACT = loadModule(Path(__file__).with_name("018_indexDocsSectionsSort.py"), "exp089ExactIndex019")


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


def childRun(stockCode: str, mode: str) -> dict[str, Any]:
    import dartlab

    company = dartlab.Company(stockCode)
    if mode == "candidate":
        payload, metrics = measurePhase(lambda: EXACT.buildIndexCandidate(company))
    else:
        payload, metrics = measurePhase(lambda: company.index)
    cacheKeys = set(company._cache._store.keys())
    return {
        "stockCode": stockCode,
        "mode": mode,
        "digest": BASELINE.payloadDigest(payload),
        "shape": BASELINE.payloadShape(payload),
        "elapsedSec": metrics["elapsedSec"],
        "rssPeakMb": metrics["rssPeakMb"],
        "rssDeltaMb": metrics["rssDeltaMb"],
        "hasSections": ("sections" in cacheKeys) or ("_sections" in cacheKeys),
        "hasProfileFacts": "_profileFacts" in cacheKeys,
        "hasRetrievalBlocks": "retrievalBlocks" in cacheKeys,
    }


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--mode", required=True, choices=["baseline", "candidate"])
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.mode), ensure_ascii=False))


def runOne(stockCode: str, mode: str) -> dict[str, Any]:
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
        "--mode",
        mode,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
    if completed.returncode != 0:
        raise RuntimeError(f"child failed: {stockCode} {mode}\nstdout={completed.stdout}\nstderr={completed.stderr}")
    return json.loads(completed.stdout.strip())


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        baseline = runOne(stockCode, "baseline")
        gc.collect()
        candidate = runOne(stockCode, "candidate")
        rows.append(
            {
                "stockCode": stockCode,
                "exact": baseline["digest"] == candidate["digest"],
                "baselineShape": baseline["shape"],
                "candidateShape": candidate["shape"],
                "baselineElapsedSec": baseline["elapsedSec"],
                "candidateElapsedSec": candidate["elapsedSec"],
                "baselineRssPeakMb": baseline["rssPeakMb"],
                "candidateRssPeakMb": candidate["rssPeakMb"],
                "baselineHasSections": baseline["hasSections"],
                "candidateHasSections": candidate["hasSections"],
                "baselineHasProfileFacts": baseline["hasProfileFacts"],
                "candidateHasProfileFacts": candidate["hasProfileFacts"],
                "baselineHasRetrievalBlocks": baseline["hasRetrievalBlocks"],
                "candidateHasRetrievalBlocks": candidate["hasRetrievalBlocks"],
                "speedup": (baseline["elapsedSec"] / candidate["elapsedSec"]) if candidate["elapsedSec"] > 0 else None,
                "peakReductionPct": (
                    ((baseline["rssPeakMb"] - candidate["rssPeakMb"]) / baseline["rssPeakMb"]) * 100.0
                    if baseline["rssPeakMb"] > 0
                    else None
                ),
            }
        )
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    exact = sum(1 for row in rows if row["exact"])
    speedups = [row["speedup"] for row in rows if row["speedup"] is not None]
    reductions = [row["peakReductionPct"] for row in rows if row["peakReductionPct"] is not None]
    print(
        json.dumps(
            {
                "total": total,
                "exact": f"{exact}/{total}",
                "speedup": [round(min(speedups), 2), round(max(speedups), 2)] if speedups else None,
                "peakReductionPct": [round(min(reductions), 1), round(max(reductions), 1)] if reductions else None,
                "candidateHasSections": sum(1 for row in rows if row["candidateHasSections"]),
                "baselineHasSections": sum(1 for row in rows if row["baselineHasSections"]),
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
