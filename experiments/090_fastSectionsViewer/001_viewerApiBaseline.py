"""
실험 ID: 001
실험명: Fast Sections Viewer baseline harness

목적:
- 현재 `/toc`, `/viewer/{topic}`, period switch 경로의 cold/warm latency, RSS, payload bytes를 fresh subprocess 기준으로 계측한다
- 090 후보 runtime이 같은 payload를 얼마나 가깝게 재현하는지 비교할 공통 하네스를 제공한다

가설:
1. baseline은 `build_toc()`와 `build_viewer()`에서 `company.sections` materialization이 자주 발생해 cold RSS가 높다
2. warm path는 `_viewer_cache`와 `company._cache` 덕분에 빠르지만 cold 비용이 커서 topic open UX를 제약한다
3. period switch는 full topic open보다 훨씬 싸지만 raw block cache를 이미 가진 상태를 전제로 한다

방법:
1. 샘플 종목 2개(`005930`, `000660`)와 viewer case matrix를 정의한다
2. 각 case를 fresh subprocess에서 3회 반복 실행한다
3. child process 내부에서 cold 1회 + warm 10회를 돌려 cold/warm 지표를 동시에 기록한다
4. payload는 canonical JSON sha256과 bytes로 저장하고 candidate와 exact match 비교 기준으로 쓴다
5. `_sections` cache touched 여부를 함께 기록한다

결과 (실험 후 작성):
- `safe2` (`005930`, `000660`) 12개 case 기준 cold subprocess 3회 + warm 10회 반복 측정 완료
- `toc` cold는 `7.317~7.449s`, warm median은 `756~811ms`, peak RSS는 `805~900MB`
- docs topic cold는 `companyOverview 7.830~7.991s`, `businessOverview 8.392~8.720s`
- report topic warm은 상대적으로 가볍다: `dividend 10.5~21.7ms`, `majorHolder 28.2~88.9ms`
- `periodSwitch:businessOverview`도 cold는 `8.435~9.266s`로 높고, selected period는 두 종목 모두 `2024Q4`

결론:
- baseline hot path 병목은 명확하다. cold open은 대부분 `sections` materialization 비용이 지배하고 `_sections=True`가 전 case에서 확인됐다
- warm에서도 docs text topic은 여전히 무겁다. 즉 현재 viewer UX 개선의 핵심 타겟은 `docs text topic cold path`다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Protocol

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl
import psutil

SAFE_CODES = ["005930", "000660"]
FULL_CODES = ["005930", "000660", "035420", "035720", "373220", "068270"]
COLD_ROUNDS = 3
WARM_ROUNDS = 10
OOM_RSS_MB = 1200.0
DEFAULT_SAMPLE = os.environ.get("FAST_VIEWER_SAMPLE", "safe2")


class ViewerRuntime(Protocol):
    stockCode: str
    corpName: str

    @property
    def hasSectionsCache(self) -> bool: ...

    def runCase(self, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]: ...


def jsonSafe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, pl.DataFrame):
        return canonicalPayload(value)
    if isinstance(value, dict):
        return {str(key): jsonSafe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [jsonSafe(item) for item in value]
    return str(value)


def canonicalPayload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, pl.DataFrame):
        return {
            "kind": "DataFrame",
            "columns": list(payload.columns),
            "dtypes": [str(dtype) for dtype in payload.dtypes],
            "rows": [jsonSafe(row) for row in payload.rows(named=False)],
        }
    if isinstance(payload, pl.Series):
        return {
            "kind": "Series",
            "name": payload.name,
            "dtype": str(payload.dtype),
            "values": jsonSafe(payload.to_list()),
        }
    return {"kind": type(payload).__name__, "value": jsonSafe(payload)}


def payloadBlob(payload: Any) -> bytes:
    return json.dumps(canonicalPayload(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def payloadDigest(payload: Any) -> str:
    return hashlib.sha256(payloadBlob(payload)).hexdigest()


def payloadBytes(payload: Any) -> int:
    return len(payloadBlob(payload))


def p95(values: list[float]) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    idx = max(0, math.ceil(len(ordered) * 0.95) - 1)
    return ordered[idx]


def loadCaseSpecs(sampleName: str) -> list[dict[str, str]]:
    if sampleName == "safe2":
        stockCodes = SAFE_CODES
    elif sampleName == "all6":
        stockCodes = FULL_CODES
    else:
        raise ValueError(f"알 수 없는 sampleName: {sampleName}")

    specs: list[dict[str, str]] = []
    for stockCode in stockCodes:
        specs.extend(
            [
                {"stockCode": stockCode, "caseName": "toc"},
                {"stockCode": stockCode, "caseName": "viewerTopic", "topic": "companyOverview"},
                {"stockCode": stockCode, "caseName": "viewerTopic", "topic": "businessOverview"},
                {"stockCode": stockCode, "caseName": "viewerTopic", "topic": "dividend"},
                {"stockCode": stockCode, "caseName": "viewerTopic", "topic": "majorHolder"},
                {"stockCode": stockCode, "caseName": "periodSwitch", "topic": "businessOverview"},
            ]
        )
    return specs


def runRuntimeWithMetrics(runtimeFactory, stockCode: str, caseName: str, topic: str | None) -> dict[str, Any]:
    process = psutil.Process(os.getpid())
    rssStart = process.memory_info().rss
    rssPeak = rssStart
    stopEvent = threading.Event()

    def pollRss() -> None:
        nonlocal rssPeak
        while not stopEvent.is_set():
            try:
                rssPeak = max(rssPeak, process.memory_info().rss)
            except psutil.Error:
                break
            time.sleep(0.01)

    poller = threading.Thread(target=pollRss, daemon=True)
    poller.start()

    runtime = None
    payload = None
    coldMeta: dict[str, Any] = {}
    warmTimes: list[float] = []
    error: str | None = None
    warmDigestMismatch = False
    warmMetaMismatch = False
    coldElapsedSec = 0.0

    try:
        startedAt = time.perf_counter()
        runtime = runtimeFactory(stockCode)
        payload, coldMeta = runtime.runCase(caseName, topic)
        coldElapsedSec = time.perf_counter() - startedAt

        baselineDigest = payloadDigest(payload)
        baselineBytes = payloadBytes(payload)
        baselineShape = canonicalPayload(payload).get("kind")

        for _ in range(WARM_ROUNDS):
            warmStartedAt = time.perf_counter()
            warmPayload, warmMeta = runtime.runCase(caseName, topic)
            warmTimes.append(time.perf_counter() - warmStartedAt)
            if payloadDigest(warmPayload) != baselineDigest:
                warmDigestMismatch = True
            if warmMeta.get("selectedPeriod") != coldMeta.get("selectedPeriod"):
                warmMetaMismatch = True
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"
        baselineDigest = None
        baselineBytes = 0
        baselineShape = None
    finally:
        stopEvent.set()
        poller.join(timeout=1.0)

    rssEnd = process.memory_info().rss
    warmMedianSec = statistics.median(warmTimes) if warmTimes else None
    warmP95Sec = p95(warmTimes) if warmTimes else None
    hasSectionsCache = False
    corpName = stockCode
    if runtime is not None:
        hasSectionsCache = bool(getattr(runtime, "hasSectionsCache", False))
        corpName = str(getattr(runtime, "corpName", stockCode))

    result = {
        "stockCode": stockCode,
        "corpName": corpName,
        "caseName": caseName,
        "topic": topic,
        "coldElapsedSec": coldElapsedSec,
        "warmMedianSec": warmMedianSec,
        "warmP95Sec": warmP95Sec,
        "warmRuns": len(warmTimes),
        "rssStartMb": rssStart / 1024 / 1024,
        "rssPeakMb": rssPeak / 1024 / 1024,
        "rssEndMb": rssEnd / 1024 / 1024,
        "rssDeltaMb": (rssPeak - rssStart) / 1024 / 1024,
        "payloadDigest": baselineDigest,
        "payloadBytes": baselineBytes,
        "payloadShape": baselineShape,
        "hasSectionsCache": hasSectionsCache,
        "warmDigestMismatch": warmDigestMismatch,
        "warmMetaMismatch": warmMetaMismatch,
        "error": error,
        "oomRisk": (rssPeak / 1024 / 1024) > OOM_RSS_MB,
    }
    result.update(coldMeta)
    return result


def aggregateRounds(roundResults: list[dict[str, Any]]) -> dict[str, Any]:
    first = roundResults[0]
    digests = [row["payloadDigest"] for row in roundResults if row.get("payloadDigest")]
    digestMismatch = len(set(digests)) > 1
    errors = [row["error"] for row in roundResults if row.get("error")]
    warmMedianValues = [row["warmMedianSec"] for row in roundResults if row["warmMedianSec"] is not None]
    warmP95Values = [row["warmP95Sec"] for row in roundResults if row["warmP95Sec"] is not None]
    return {
        "stockCode": first["stockCode"],
        "corpName": first["corpName"],
        "caseName": first["caseName"],
        "topic": first.get("topic"),
        "coldElapsedSec": statistics.median(row["coldElapsedSec"] for row in roundResults),
        "warmMedianSec": statistics.median(warmMedianValues) if warmMedianValues else None,
        "warmP95Sec": statistics.median(warmP95Values) if warmP95Values else None,
        "rssPeakMb": statistics.median(row["rssPeakMb"] for row in roundResults),
        "rssDeltaMb": statistics.median(row["rssDeltaMb"] for row in roundResults),
        "payloadDigest": digests[0] if digests else None,
        "payloadBytes": statistics.median(row["payloadBytes"] for row in roundResults),
        "payloadShape": first.get("payloadShape"),
        "hasSectionsCache": any(bool(row.get("hasSectionsCache")) for row in roundResults),
        "selectedPeriod": first.get("selectedPeriod"),
        "digestMismatch": digestMismatch or any(bool(row.get("warmDigestMismatch")) for row in roundResults),
        "metaMismatch": any(bool(row.get("warmMetaMismatch")) for row in roundResults),
        "error": "; ".join(errors) if errors else None,
        "oomRisk": any(bool(row.get("oomRisk")) for row in roundResults),
    }


def runChild(scriptPath: Path, modeName: str, caseSpec: dict[str, str]) -> dict[str, Any]:
    cmd = [
        sys.executable,
        "-X",
        "utf8",
        str(scriptPath),
        "--child",
        "--mode",
        modeName,
        "--stockCode",
        caseSpec["stockCode"],
        "--caseName",
        caseSpec["caseName"],
    ]
    topic = caseSpec.get("topic")
    if topic:
        cmd.extend(["--topic", topic])
    completed = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"child failed: {modeName} {caseSpec['stockCode']} {caseSpec['caseName']} {topic or ''}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"child returned no output: {caseSpec}")
    return json.loads(lines[-1])


def collectMode(scriptPath: Path, modeName: str, sampleName: str = DEFAULT_SAMPLE) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for caseSpec in loadCaseSpecs(sampleName):
        rounds = [runChild(scriptPath, modeName, caseSpec) for _ in range(COLD_ROUNDS)]
        rows.append(aggregateRounds(rounds))
    return rows


def compareRuns(baselineRows: list[dict[str, Any]], candidateRows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidateMap = {(row["stockCode"], row["caseName"], row.get("topic")): row for row in candidateRows}
    comparisons: list[dict[str, Any]] = []
    for baselineRow in baselineRows:
        key = (baselineRow["stockCode"], baselineRow["caseName"], baselineRow.get("topic"))
        candidateRow = candidateMap[key]
        exactMatch = (
            baselineRow.get("payloadDigest") is not None
            and baselineRow.get("payloadDigest") == candidateRow.get("payloadDigest")
            and not candidateRow.get("digestMismatch")
        )
        coldSpeedRatio = (
            baselineRow["coldElapsedSec"] / candidateRow["coldElapsedSec"]
            if candidateRow["coldElapsedSec"] > 0
            else None
        )
        warmSpeedRatio = (
            baselineRow["warmMedianSec"] / candidateRow["warmMedianSec"]
            if candidateRow["warmMedianSec"] and candidateRow["warmMedianSec"] > 0
            else None
        )
        peakSavingsPct = (
            (1 - candidateRow["rssPeakMb"] / baselineRow["rssPeakMb"]) * 100 if baselineRow["rssPeakMb"] > 0 else None
        )
        comparisons.append(
            {
                "stockCode": baselineRow["stockCode"],
                "caseName": baselineRow["caseName"],
                "topic": baselineRow.get("topic"),
                "exactMatch": exactMatch,
                "coldSpeedRatio": coldSpeedRatio,
                "warmSpeedRatio": warmSpeedRatio,
                "peakSavingsPct": peakSavingsPct,
                "baselineColdSec": baselineRow["coldElapsedSec"],
                "candidateColdSec": candidateRow["coldElapsedSec"],
                "baselineWarmSec": baselineRow["warmMedianSec"],
                "candidateWarmSec": candidateRow["warmMedianSec"],
                "baselinePeakMb": baselineRow["rssPeakMb"],
                "candidatePeakMb": candidateRow["rssPeakMb"],
                "candidateBytes": candidateRow["payloadBytes"],
                "candidateHasSectionsCache": candidateRow.get("hasSectionsCache"),
                "candidateSelectedPeriod": candidateRow.get("selectedPeriod"),
                "candidateError": candidateRow.get("error"),
                "candidateDigestMismatch": candidateRow.get("digestMismatch"),
            }
        )
    return comparisons


def printSummary(title: str, rows: list[dict[str, Any]]) -> None:
    print("=" * 96)
    print(title)
    print("=" * 96)
    for row in rows:
        topicSuffix = f":{row['topic']}" if row.get("topic") else ""
        warmText = "-" if row.get("warmMedianSec") is None else f"{row['warmMedianSec'] * 1000:.1f}ms"
        p95Text = "-" if row.get("warmP95Sec") is None else f"{row['warmP95Sec'] * 1000:.1f}ms"
        print(
            f"{row['stockCode']} {row['caseName']}{topicSuffix} | "
            f"cold {row['coldElapsedSec']:.3f}s | warm {warmText} / p95 {p95Text} | "
            f"peak {row['rssPeakMb']:.1f}MB | bytes {int(row['payloadBytes'])} | _sections={row.get('hasSectionsCache')}"
        )
        if row.get("selectedPeriod"):
            print(f"  selectedPeriod: {row['selectedPeriod']}")
        if row.get("error"):
            print(f"  error: {row['error']}")


def printComparisonSummary(title: str, rows: list[dict[str, Any]]) -> None:
    print("=" * 96)
    print(title)
    print("=" * 96)
    exactMatches = sum(1 for row in rows if row["exactMatch"])
    print(f"exact match: {exactMatches}/{len(rows)}")
    for row in rows:
        topicSuffix = f":{row['topic']}" if row.get("topic") else ""
        coldText = "-" if row["coldSpeedRatio"] is None else f"{row['coldSpeedRatio']:.2f}x"
        warmText = "-" if row["warmSpeedRatio"] is None else f"{row['warmSpeedRatio']:.2f}x"
        peakText = "-" if row["peakSavingsPct"] is None else f"{row['peakSavingsPct']:.1f}%"
        print(
            f"{row['stockCode']} {row['caseName']}{topicSuffix} | "
            f"exact={row['exactMatch']} | cold={coldText} | warm={warmText} | "
            f"peakSave={peakText} | _sections={row['candidateHasSectionsCache']}"
        )
        if row.get("candidateSelectedPeriod"):
            print(f"  selectedPeriod: {row['candidateSelectedPeriod']}")
        if row.get("candidateError"):
            print(f"  candidateError: {row['candidateError']}")


class BaselineViewerRuntime:
    def __init__(self, stockCode: str):
        import dartlab
        from dartlab.engines.company.dart.docs.viewer import (
            serializeViewerBlock,
            serializeViewerTextDocument,
            viewerBlocks,
            viewerTextDocument,
        )
        from dartlab.server.services.company_api import (
            _find_prev_comparable,
            build_toc,
            build_viewer,
            filter_blocks_by_period,
        )

        self.company = dartlab.Company(stockCode)
        self.stockCode = stockCode
        self.corpName = self.company.corpName
        self.buildToc = build_toc
        self.buildViewer = build_viewer
        self.findPrevComparable = _find_prev_comparable
        self.filterBlocksByPeriod = filter_blocks_by_period
        self.viewerBlocks = viewerBlocks
        self.viewerTextDocument = viewerTextDocument
        self.serializeViewerBlock = serializeViewerBlock
        self.serializeViewerTextDocument = serializeViewerTextDocument
        self.blockCache: dict[str, list[Any]] = {}

    @property
    def hasSectionsCache(self) -> bool:
        return "_sections" in self.company._cache

    def pickSwitchPeriod(self, topic: str) -> str | None:
        blocks = self.blockCache.get(topic)
        if blocks is None:
            blocks = self.viewerBlocks(self.company, topic)
            self.blockCache[topic] = blocks
        allPeriods = sorted({period for block in blocks for period in getattr(block.meta, "periods", [])})
        if not allPeriods:
            return None
        latest = allPeriods[-1]
        return self.findPrevComparable(allPeriods, latest) or latest

    def runCase(self, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
        if caseName == "toc":
            payload = self.buildToc(self.company)
            return payload, {"hasSectionsCache": self.hasSectionsCache}
        if caseName == "viewerTopic":
            payload = self.buildViewer(self.company, str(topic))
            return payload, {"hasSectionsCache": self.hasSectionsCache}
        if caseName == "periodSwitch":
            selectedPeriod = self.pickSwitchPeriod(str(topic))
            blocks = self.blockCache[str(topic)]
            filtered = self.filterBlocksByPeriod(blocks, selectedPeriod) if selectedPeriod else blocks
            payload = {
                "stockCode": self.company.stockCode,
                "corpName": self.company.corpName,
                "topic": topic,
                "topicLabel": self.company._topicLabel(str(topic)),
                "period": selectedPeriod,
                "blocks": [self.serializeViewerBlock(block) for block in filtered],
                "textDocument": self.serializeViewerTextDocument(self.viewerTextDocument(str(topic), filtered)),
            }
            return payload, {"hasSectionsCache": self.hasSectionsCache, "selectedPeriod": selectedPeriod}
        raise ValueError(f"알 수 없는 caseName: {caseName}")


def childMain(runtimeFactory) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", required=True)
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--caseName", required=True)
    parser.add_argument("--topic")
    args = parser.parse_args()
    result = runRuntimeWithMetrics(runtimeFactory, args.stockCode, args.caseName, args.topic)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> None:
    if "--child" in sys.argv:
        childMain(BaselineViewerRuntime)
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=DEFAULT_SAMPLE, choices=["safe2", "all6"])
    args = parser.parse_args()
    rows = collectMode(Path(__file__), "baseline", args.sample)
    printSummary(f"090 baseline / {args.sample}", rows)


if __name__ == "__main__":
    main()
