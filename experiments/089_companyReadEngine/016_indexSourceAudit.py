"""
실험 ID: 016
실험명: Index Source Audit

목적:
- public `index`의 heavy path가 `docs`, `report`, `finance` 중 어디에서 발생하는지 분리 측정
- `_sections/_profileFacts/retrievalBlocks` cache 생성 여부를 source별로 확인해 다음 후보를 좁힌다

가설:
1. `index` 피크 메모리의 주범은 `docs` source rows다
2. `finance` rows는 이미 가볍고, `report` rows는 느리더라도 `_sections`를 만들지 않는다

방법:
1. 샘플 6종목 × (`finance`, `docs`, `report`) 18개 case를 fresh subprocess 1회로 실행한다
2. `finance`는 `company._indexFinanceRows()`, `docs`는 `company._indexDocsRows()`, `report`는 `company._indexReportRows(existingTopics=...)`만 단독 측정한다
3. `report`의 `existingTopics`는 `company.topics`와 finance rows topic으로 구성해 full index의 skip semantics를 그대로 맞춘다
4. child process 내부에서 elapsed, rssPeak, rowCount, heavy cache 생성 여부를 기록한다

결과 (실험 후 작성):
- 총 18개 case를 fresh subprocess로 비교
- `finance`
  - rowCount: `6` 고정
  - 시간: `0.130~0.185s`
  - peak RSS: `185.9~198.5MB`
  - `_sections/_profileFacts/retrievalBlocks` 생성: `0/6`
- `docs`
  - rowCount: `39~43`
  - 시간: `3.188~5.935s`
  - peak RSS: `490.2~786.4MB`
  - `_sections` 생성: `6/6`
  - `_profileFacts/retrievalBlocks` 생성: `0/6`
- `report`
  - rowCount: `18` 고정
  - 시간: `0.136~0.184s`
  - peak RSS: `254.3~288.4MB`
  - `_sections/_profileFacts/retrievalBlocks` 생성: `0/6`

결론:
- **채택**
- public `index`의 heavy path는 사실상 `docs` source rows다. `_sections` 생성도 `docs`에서만 발생했다
- `finance` rows는 무시 가능한 수준이고, `report` rows는 아직 exact 후보가 아니어도 `_sections` 없이 끝난다
- 다음 타깃은 `docs index row`의 exact reconstruction이며, report는 docs를 치운 뒤 보조 최적화 대상으로 본다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline016")


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


def rowCount(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    return 0


def childRun(stockCode: str, caseName: str) -> dict[str, Any]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "finance":
        payload, metrics = measurePhase(company._indexFinanceRows)
    elif caseName == "docs":
        payload, metrics = measurePhase(company._indexDocsRows)
    else:
        financeTopics = {str(row["topic"]) for row in company._indexFinanceRows()}
        topicDf = company.topics
        if topicDf.is_empty() or "topic" not in topicDf.columns:
            existingTopics = financeTopics
        else:
            existingTopics = financeTopics | {
                str(topic)
                for topic in topicDf["topic"].to_list()
                if isinstance(topic, str) and topic
            }
        payload, metrics = measurePhase(lambda: company._indexReportRows(existingTopics=existingTopics))

    cacheKeys = set(company._cache._store.keys())
    return {
        "stockCode": stockCode,
        "caseName": caseName,
        "rowCount": rowCount(payload),
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
    parser.add_argument("--caseName", required=True, choices=["finance", "docs", "report"])
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode, args.caseName), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        for caseName in ("finance", "docs", "report"):
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
    for caseName in ("finance", "docs", "report"):
        scoped = [row for row in rows if row["caseName"] == caseName]
        print(
            json.dumps(
                {
                    "caseName": caseName,
                    "rowCount": [min(row["rowCount"] for row in scoped), max(row["rowCount"] for row in scoped)],
                    "elapsedSec": [
                        round(min(row["elapsedSec"] for row in scoped), 3),
                        round(max(row["elapsedSec"] for row in scoped), 3),
                    ],
                    "rssPeakMb": [
                        round(min(row["rssPeakMb"] for row in scoped), 1),
                        round(max(row["rssPeakMb"] for row in scoped), 1),
                    ],
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
