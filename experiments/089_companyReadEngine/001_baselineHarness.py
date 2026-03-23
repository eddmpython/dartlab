"""
실험 ID: 001
실험명: Company 읽기 baseline harness

목적:
- Company 현재 공개 경로의 속도, 피크 메모리, 결과 해시를 fresh subprocess 기준으로 측정
- 후속 후보 실험이 baseline과 결과가 완전히 같은지 비교할 공통 harness 제공

가설:
1. 현 baseline은 metadata와 authoritative topic에서도 full sections/profile 경로에 자주 진입한다
2. `topics`, `show("BS")`, `trace("BS")`, docs topic `show()`는 피크 RSS가 특히 크다
3. fresh subprocess + RSS polling 기준으로 후보별 시간/메모리 절감률을 안정적으로 비교할 수 있다

방법:
1. 샘플 종목 6개에 대해 case matrix를 구성
2. 각 case를 fresh subprocess에서 3회 실행
3. child process 내부에서 psutil polling으로 rssPeakMb를 기록
4. payload를 canonical JSON으로 직렬화해 sha256 digest 비교
5. `_sections` cache touched 여부를 함께 기록

결과 (실험 후 작성):
- 총 60개 case(6종목 × 10 case)를 fresh subprocess 3회 median으로 측정
- init: 1.825~2.328s, peak 136.7~142.8MB
- availableApiTypes: 2.120~2.538s, peak 322.9~628.9MB
- topics: 6.104~8.093s, peak 714.4~902.9MB, 6/6에서 `_sections` cache 생성
- index: 5.783~7.358s, peak 720.4~925.6MB
- show("BS"): 5.468~7.748s, peak 688.3~908.3MB, 6/6에서 `_sections` cache 생성
- trace("BS"): 6.810~9.686s, peak 973.7~1362.0MB
- show("companyOverview"): 5.875~7.553s, peak 691.6~964.0MB, 6/6에서 `_sections` cache 생성
- show("businessOverview"): 5.638~8.593s, peak 720.6~943.3MB, 6/6에서 `_sections` cache 생성
- show(reportTopic=majorHolder): 5.649~7.822s, peak 745.2~940.1MB, 6/6에서 `_sections` cache 생성
- trace(reportTopic=majorHolder): 6.782~8.993s, peak 988.1~1330.8MB
- 105560, 035420의 `trace("BS")`와 005930, 105560, 035420의 `trace("majorHolder")`는 1200MB를 넘어 OOM-risk로 기록

결론:
- baseline은 authoritative/metadata path도 지나치게 무겁다
- 특히 `topics`, docs `show()`, authoritative `show()`가 `sections` 경유 때문에 700~900MB 급으로 부풀고 있다
- 최종 비교 기준은 이 baseline을 유지한다

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
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl
import psutil

SAMPLE_CODES = ["005930", "000660", "005380", "105560", "035420", "005490"]
REPORT_TOPIC_CANDIDATES = ["majorHolder", "auditOpinion", "employee"]
OOM_RSS_MB = 1200.0
ROUNDS = 3


def _jsonSafe(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _jsonSafe(value[k]) for k in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (list, tuple)):
        return [_jsonSafe(item) for item in value]
    return str(value)


def canonicalPayload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, pl.DataFrame):
        return {
            "kind": "DataFrame",
            "columns": list(payload.columns),
            "dtypes": [str(dtype) for dtype in payload.dtypes],
            "rows": [_jsonSafe(row) for row in payload.rows(named=False)],
        }
    if isinstance(payload, pl.Series):
        return {
            "kind": "Series",
            "name": payload.name,
            "dtype": str(payload.dtype),
            "values": _jsonSafe(payload.to_list()),
        }
    if payload is None:
        return {"kind": "None", "value": None}
    return {"kind": type(payload).__name__, "value": _jsonSafe(payload)}


def payloadDigest(payload: Any) -> str:
    blob = json.dumps(canonicalPayload(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(blob).hexdigest()


def payloadShape(payload: Any) -> str | None:
    if isinstance(payload, pl.DataFrame):
        return f"{payload.height}x{payload.width}"
    if isinstance(payload, pl.Series):
        return str(len(payload))
    if isinstance(payload, list):
        return str(len(payload))
    if isinstance(payload, dict):
        return str(len(payload))
    return None


def shapeString(df: pl.DataFrame | None) -> str:
    if df is None:
        return "missing"
    return f"{df.height}x{df.width}"


def loadCaseSpecs(caseGroup: str) -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for stockCode in SAMPLE_CODES:
        reportTopic = chooseReportTopic(stockCode)
        baseSpecs = [
            {"stockCode": stockCode, "caseName": "init"},
            {"stockCode": stockCode, "caseName": "availableApiTypes"},
            {"stockCode": stockCode, "caseName": "topics"},
            {"stockCode": stockCode, "caseName": "index"},
            {"stockCode": stockCode, "caseName": "showBS"},
            {"stockCode": stockCode, "caseName": "traceBS"},
            {"stockCode": stockCode, "caseName": "showCompanyOverview"},
            {"stockCode": stockCode, "caseName": "showBusinessOverview"},
        ]
        if reportTopic is not None:
            baseSpecs.append({"stockCode": stockCode, "caseName": "showReportTopic", "topic": reportTopic})
            baseSpecs.append({"stockCode": stockCode, "caseName": "traceReportTopic", "topic": reportTopic})

        if caseGroup == "all":
            specs.extend(baseSpecs)
            continue

        allowed = {
            "metadataDocs": {"availableApiTypes", "topics", "index", "showCompanyOverview", "showBusinessOverview"},
            "docsOnly": {"showCompanyOverview", "showBusinessOverview"},
            "authoritative": {"showBS", "traceBS", "showReportTopic", "traceReportTopic"},
        }.get(caseGroup)
        if allowed is None:
            raise ValueError(f"알 수 없는 caseGroup: {caseGroup}")
        specs.extend([spec for spec in baseSpecs if spec["caseName"] in allowed])
    return specs


def chooseReportTopic(stockCode: str) -> str | None:
    from dartlab.core.dataLoader import loadData

    try:
        df = loadData(stockCode, category="report", columns=["apiType"])
    except FileNotFoundError:
        return None
    if df is None or df.is_empty() or "apiType" not in df.columns:
        return None
    available = {str(value) for value in df["apiType"].drop_nulls().unique().to_list()}
    for candidate in REPORT_TOPIC_CANDIDATES:
        if candidate not in available:
            continue
        return "audit" if candidate == "auditOpinion" else candidate
    return None


def runCaseWithMetrics(
    caseRunner: Callable[[str, str, str | None], tuple[Any, dict[str, Any]]],
    stockCode: str,
    caseName: str,
    topic: str | None,
) -> dict[str, Any]:
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
    payload: Any = None
    meta: dict[str, Any] = {}
    error: str | None = None
    try:
        payload, meta = caseRunner(stockCode, caseName, topic)
    except Exception as exc:  # noqa: BLE001 - 실험 harness는 오류를 캡처해야 함
        error = f"{type(exc).__name__}: {exc}"
    finally:
        elapsedSec = time.perf_counter() - startedAt
        stopEvent.set()
        poller.join(timeout=1.0)
    rssEnd = process.memory_info().rss
    payloadHash = None if error else payloadDigest(payload)
    payloadFrameShape = None if error else payloadShape(payload)
    result = {
        "stockCode": stockCode,
        "caseName": caseName,
        "topic": topic,
        "elapsedSec": elapsedSec,
        "rssStartMb": rssStart / 1024 / 1024,
        "rssPeakMb": rssPeak / 1024 / 1024,
        "rssEndMb": rssEnd / 1024 / 1024,
        "rssDeltaMb": (rssPeak - rssStart) / 1024 / 1024,
        "payloadDigest": payloadHash,
        "payloadShape": payloadFrameShape,
        "error": error,
        "oomRisk": (rssPeak / 1024 / 1024) > OOM_RSS_MB,
    }
    result.update(meta)
    return result


def aggregateRounds(roundResults: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [row["error"] for row in roundResults if row["error"]]
    digests = [row["payloadDigest"] for row in roundResults if row["payloadDigest"] is not None]
    digestMismatch = len(set(digests)) > 1
    summary = {
        "stockCode": roundResults[0]["stockCode"],
        "caseName": roundResults[0]["caseName"],
        "topic": roundResults[0].get("topic"),
        "elapsedSec": statistics.median(row["elapsedSec"] for row in roundResults),
        "rssPeakMb": statistics.median(row["rssPeakMb"] for row in roundResults),
        "rssDeltaMb": statistics.median(row["rssDeltaMb"] for row in roundResults),
        "payloadDigest": digests[0] if digests else None,
        "payloadShape": roundResults[0].get("payloadShape"),
        "hasSectionsCache": any(bool(row.get("hasSectionsCache")) for row in roundResults),
        "reportTopic": roundResults[0].get("reportTopic"),
        "error": "; ".join(errors) if errors else None,
        "digestMismatch": digestMismatch,
        "oomRisk": any(bool(row.get("oomRisk")) for row in roundResults),
    }
    if digestMismatch and summary["error"] is None:
        summary["error"] = "payloadDigest mismatch across rounds"
    return summary


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
    if topic is not None:
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
            f"child failed: mode={modeName} case={caseSpec['caseName']} code={caseSpec['stockCode']}\n"
            f"stdout:\n{completed.stdout}\n\nstderr:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"child returned no output: {caseSpec}")
    return json.loads(lines[-1])


def collectMode(scriptPath: Path, modeName: str, caseGroup: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for caseSpec in loadCaseSpecs(caseGroup):
        rounds = [runChild(scriptPath, modeName, caseSpec) for _ in range(ROUNDS)]
        results.append(aggregateRounds(rounds))
    return results


def compareRuns(baselineRows: list[dict[str, Any]], candidateRows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidateMap = {(row["stockCode"], row["caseName"], row.get("topic")): row for row in candidateRows}
    comparisons: list[dict[str, Any]] = []
    for baselineRow in baselineRows:
        key = (baselineRow["stockCode"], baselineRow["caseName"], baselineRow.get("topic"))
        candidateRow = candidateMap[key]
        exactMatch = (
            baselineRow.get("payloadDigest") is not None
            and baselineRow.get("payloadDigest") == candidateRow.get("payloadDigest")
            and baselineRow.get("payloadShape") == candidateRow.get("payloadShape")
        )
        timeRatio = baselineRow["elapsedSec"] / candidateRow["elapsedSec"] if candidateRow["elapsedSec"] > 0 else None
        peakSavingsPct = (
            (1 - candidateRow["rssPeakMb"] / baselineRow["rssPeakMb"]) * 100
            if baselineRow["rssPeakMb"] > 0
            else None
        )
        deltaSavingsPct = (
            (1 - candidateRow["rssDeltaMb"] / baselineRow["rssDeltaMb"]) * 100
            if baselineRow["rssDeltaMb"] > 0
            else None
        )
        comparisons.append(
            {
                "stockCode": baselineRow["stockCode"],
                "caseName": baselineRow["caseName"],
                "topic": baselineRow.get("topic"),
                "exactMatch": exactMatch,
                "timeRatio": timeRatio,
                "peakSavingsPct": peakSavingsPct,
                "deltaSavingsPct": deltaSavingsPct,
                "baselineElapsedSec": baselineRow["elapsedSec"],
                "candidateElapsedSec": candidateRow["elapsedSec"],
                "baselinePeakMb": baselineRow["rssPeakMb"],
                "candidatePeakMb": candidateRow["rssPeakMb"],
                "baselineHasSectionsCache": baselineRow.get("hasSectionsCache"),
                "candidateHasSectionsCache": candidateRow.get("hasSectionsCache"),
                "baselineError": baselineRow.get("error"),
                "candidateError": candidateRow.get("error"),
                "candidateOomRisk": candidateRow.get("oomRisk"),
            }
        )
    return comparisons


def printSummary(title: str, rows: list[dict[str, Any]]) -> None:
    print("=" * 88)
    print(title)
    print("=" * 88)
    for row in rows:
        topicSuffix = f":{row['topic']}" if row.get("topic") else ""
        print(
            f"{row['stockCode']} {row['caseName']}{topicSuffix} | "
            f"{row['elapsedSec']:.3f}s | peak {row['rssPeakMb']:.1f}MB | "
            f"delta {row['rssDeltaMb']:.1f}MB | _sections={row.get('hasSectionsCache')}"
        )
        if row.get("error"):
            print(f"  error: {row['error']}")


def printComparisonSummary(title: str, rows: list[dict[str, Any]]) -> None:
    print("=" * 88)
    print(title)
    print("=" * 88)
    exactMatches = sum(1 for row in rows if row["exactMatch"])
    print(f"exact match: {exactMatches}/{len(rows)}")
    for row in rows:
        topicSuffix = f":{row['topic']}" if row.get("topic") else ""
        timeText = "-" if row["timeRatio"] is None else f"{row['timeRatio']:.2f}x"
        peakText = "-" if row["peakSavingsPct"] is None else f"{row['peakSavingsPct']:.1f}%"
        print(
            f"{row['stockCode']} {row['caseName']}{topicSuffix} | "
            f"exact={row['exactMatch']} | speed={timeText} | peakSave={peakText} | "
            f"_sections={row['candidateHasSectionsCache']}"
        )
        if row.get("candidateError"):
            print(f"  candidateError: {row['candidateError']}")


def runBaselineCase(stockCode: str, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
    import dartlab

    company = dartlab.Company(stockCode)
    if caseName == "init":
        payload: Any = {"stockCode": company.stockCode, "corpName": company.corpName}
    elif caseName == "availableApiTypes":
        payload = company.report.availableApiTypes
    elif caseName == "topics":
        payload = company.topics
    elif caseName == "index":
        payload = company.index
    elif caseName == "showBS":
        payload = company.show("BS")
    elif caseName == "traceBS":
        payload = company.trace("BS")
    elif caseName == "showCompanyOverview":
        payload = company.show("companyOverview")
    elif caseName == "showBusinessOverview":
        payload = company.show("businessOverview")
    elif caseName == "showReportTopic":
        payload = company.show(topic)
    elif caseName == "traceReportTopic":
        payload = company.trace(topic)
    else:
        raise ValueError(f"알 수 없는 caseName: {caseName}")
    meta = {
        "hasSectionsCache": "_sections" in company._cache,
        "reportTopic": topic,
    }
    return payload, meta


def childMain(caseRunner: Callable[[str, str, str | None], tuple[Any, dict[str, Any]]]) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", required=True)
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--caseName", required=True)
    parser.add_argument("--topic")
    args = parser.parse_args()
    result = runCaseWithMetrics(caseRunner, args.stockCode, args.caseName, args.topic)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def main() -> None:
    if "--child" in sys.argv:
        childMain(runBaselineCase)
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="baseline")
    parser.add_argument("--caseGroup", default="all", choices=["all", "metadataDocs", "docsOnly", "authoritative"])
    args = parser.parse_args()
    baselineRows = collectMode(Path(__file__), "baseline", args.caseGroup)
    printSummary(f"baseline / {args.caseGroup}", baselineRows)


if __name__ == "__main__":
    main()
