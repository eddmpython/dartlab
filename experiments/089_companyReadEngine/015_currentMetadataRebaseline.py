"""
실험 ID: 015
실험명: Current Metadata Rebaseline

목적:
- 현재 working tree 기준 public `topics`와 `index`가 여전히 heavy path인지 다시 확인
- `_sections/_profileFacts/retrievalBlocks` cache 생성 여부와 피크 메모리를 fresh subprocess 기준으로 재측정

가설:
1. 현재 public `topics`, `index`는 old baseline(001)보다 가볍고 `_sections`를 만들지 않는다
2. 남은 병목은 metadata보다 docs/report show/trace 쪽이다

방법:
1. 샘플 6종목 × (`topics`, `index`) 12개 case를 fresh subprocess 1회로 실행
2. child process 내부에서 elapsed, rssPeak, `_sections/_profileFacts/retrievalBlocks` touched 여부를 기록한다
3. 결과는 001 baseline 수치와 나란히 해석한다

결과 (실험 후 작성):
- 총 12개 case(6종목 × `topics/index`)를 fresh subprocess로 비교
- `topics`
  - 시간: `0.074~0.087s`
  - peak RSS: `164.6~166.7MB`
  - `_sections/_profileFacts/retrievalBlocks` 생성: `0/6`
- `index`
  - 시간: `3.002~4.902s`
  - peak RSS: `542.6~810.4MB`
  - `_sections` 생성: `6/6`
  - `_profileFacts/retrievalBlocks` 생성: `0/6`

결론:
- **채택**
- 현재 working tree 기준 `topics`는 이미 가볍고 heavy cache를 전혀 만들지 않는다
- 남은 metadata 병목은 사실상 `index` 하나이며, 그 원인은 `_sections` 생성이다
- 이후 실험은 `topics`가 아니라 `index` docs source rows에 집중하면 된다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline015")


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


def childRun(stockCode: str, caseName: str) -> dict[str, Any]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "topics":
        payload, metrics = measurePhase(lambda: company.topics)
    else:
        payload, metrics = measurePhase(lambda: company.index)
    cacheKeys = set(company._cache._store.keys())
    return {
        "stockCode": stockCode,
        "caseName": caseName,
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
    parser.add_argument("--caseName", required=True, choices=["topics", "index"])
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.caseName), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        for caseName in ("topics", "index"):
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
                "--caseName",
                caseName,
            ]
            completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
            if completed.returncode != 0:
                raise RuntimeError(
                    f"child failed: {stockCode} {caseName}\nstdout={completed.stdout}\nstderr={completed.stderr}"
                )
            rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    print(json.dumps({"total": len(rows)}, ensure_ascii=False))
    for caseName in ("topics", "index"):
        scoped = [row for row in rows if row["caseName"] == caseName]
        print(
            json.dumps(
                {
                    "caseName": caseName,
                    "elapsedSec": [round(min(row["elapsedSec"] for row in scoped), 3), round(max(row["elapsedSec"] for row in scoped), 3)],
                    "rssPeakMb": [round(min(row["rssPeakMb"] for row in scoped), 1), round(max(row["rssPeakMb"] for row in scoped), 1)],
                    "hasSections": sum(1 for row in scoped if row["hasSections"]),
                    "hasProfileFacts": sum(1 for row in scoped if row["hasProfileFacts"]),
                    "hasRetrievalBlocks": sum(1 for row in scoped if row["hasRetrievalBlocks"]),
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
