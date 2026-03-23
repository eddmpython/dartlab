"""
실험 ID: 006
실험명: Authoritative Path Follow-up

목적:
- 002의 `show("BS")` 판정 하락이 비교 코드 문제인지 확인하고 finance/report authoritative path를 다시 전수 점검
- `sections/profile.facts/retrievalBlocks` 없이도 exact가 유지되는 authoritative path 범위를 재측정

가설:
1. finance `show()` 6종(`BS`, `IS`, `CF`, `CIS`, `SCE`, `ratios`)은 direct helper로 baseline과 exact 동일하다
2. finance `trace()` 5종(`BS`, `IS`, `CF`, `CIS`, `SCE`)은 series 기반 dict 재구성으로 baseline과 exact 동일하다
3. report `show()`는 `_showReportTopic()` direct path로 baseline과 exact 동일하다
4. report `trace()`는 docs fallback을 같이 재현하지 못하면 exact가 아니다

방법:
1. 샘플 종목 6개에 대해 finance show 6종, finance trace 5종, report show/trace 대표 topic 1개를 구성
2. 각 케이스를 fresh subprocess 1회로 실행한다
3. child process 내부에서 candidate 경로와 baseline 공개 경로를 순서대로 실행해 payload digest를 비교한다
4. candidate 단계에서는 elapsed, rssPeak, `_sections/_profileFacts/retrievalBlocks` touched 여부를 기록한다

결과 (실험 후 작성):
- 총 78개 case를 fresh subprocess 1회로 비교
- exact match: 66/78
- finance `show()` 6종: exact 36/36, candidate에서 `_sections/_profileFacts/retrievalBlocks` 생성 0건
- finance `trace()` 5종: exact 30/30, candidate에서 `_sections/_profileFacts/retrievalBlocks` 생성 0건
- report `show()` 대표 topic(`majorHolder`)은 exact 0/6
  - 005930 기준 baseline은 docs block index `83x4`, candidate `_showReportTopic()`는 report payload `645x7`
- report `trace()` 대표 topic(`majorHolder`)은 exact 0/6
  - candidate는 report source만 재현했고 baseline의 docs fallback source를 같이 못 맞춤
- 현재 working tree에는 finance fast path가 이미 적용돼 있어 finance show/trace의 시간 비교는 유의미하지 않았음
- 반대로 report show/trace candidate는 baseline 대비 145x~411x 빠르지만 payload가 달라 채택 불가
- 결론적으로 authoritative path 중 exact가 확보된 것은 finance show/trace 전체이고, report topic은 현재 public `show()` semantics 자체가 docs block index 중심이다

결론:
- 002의 `show("BS") 3/6`은 comparison bug였다. finance `show()`는 6종 전부 exact다
- finance authoritative path는 `show()/trace()` 전체가 route split 가능 구간으로 확정됐다
- report는 `trace()`뿐 아니라 `show()`도 단순 direct report payload로는 exact가 아니다
- 다음 실험 우선순위는 report topic의 현재 public semantics를 정확히 정의하고, docs/report dual-source 경로를 그대로 재현하는 lightweight route를 찾는 것이다

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


def _loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = _loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline")

FINANCE_SHOW_TOPICS = ["BS", "IS", "CF", "CIS", "SCE", "ratios"]
FINANCE_TRACE_TOPICS = ["BS", "IS", "CF", "CIS", "SCE"]


def chooseReportTopic(stockCode: str) -> str | None:
    return BASELINE.chooseReportTopic(stockCode)


def financeShowFast(company, topic: str) -> pl.DataFrame | None:
    df = company._showFinanceTopic(topic)
    if df is None:
        return None
    if topic in {"BS", "IS", "CF", "CIS", "SCE"} and df.width > 0:
        return company._cleanFinanceDataFrame(df, topic)
    return df


def financeTraceFast(company, topic: str, period: str | None = None) -> dict[str, Any] | None:
    from dartlab.engines.company.dart.docs.sections import rawPeriod

    requestedPeriod = rawPeriod(period) if isinstance(period, str) else period
    rows: list[tuple[str, str]] = []

    def collect(series: dict[str, list[Any]] | None, years: list[Any], payloadTopic: str) -> None:
        if not series:
            return
        for item, values in series.items():
            for idx, year in enumerate(years):
                if requestedPeriod is not None and str(year) != requestedPeriod:
                    continue
                value = values[idx] if idx < len(values) else None
                if value is None:
                    continue
                rows.append((f"finance:{payloadTopic}:{item}", f"{item}={value}"))

    if topic in {"BS", "IS", "CF"}:
        annual = company.finance.annual
        if annual is None:
            return None
        series, years = annual
        collect(series.get(topic), years, topic)
    elif topic == "CIS":
        annual = company._financeCisAnnual()
        if annual is None:
            return None
        series, years = annual
        collect(series.get("CIS"), years, "CIS")
    elif topic == "SCE":
        annual = company._sceSeriesAnnual()
        if annual is None:
            return None
        series, years = annual
        collect(series.get("SCE"), years, "SCE")
    else:
        return None

    if not rows:
        return None

    payloadRef, summary = rows[0]
    return {
        "topic": topic,
        "period": requestedPeriod,
        "primarySource": "finance",
        "fallbackSources": [],
        "selectedPayloadRef": payloadRef,
        "availableSources": [
            {
                "source": "finance",
                "rows": len(rows),
                "payloadRef": payloadRef,
                "summary": summary,
                "priority": 300,
            }
        ],
        "whySelected": "finance authoritative priority",
    }


def reportTraceFast(company, topic: str) -> dict[str, Any] | None:
    apiType = BASELINE._REPORT_TOPIC_TO_API_TYPE.get(topic, topic) if hasattr(BASELINE, "_REPORT_TOPIC_TO_API_TYPE") else topic
    if apiType == "audit":
        apiType = "auditOpinion"
    df = company.report.extractAnnual(apiType)
    if df is None or df.is_empty():
        return None

    rows: list[dict[str, Any]] = []
    canonicalTopic = "audit" if apiType == "auditOpinion" else apiType
    for row in df.iter_rows(named=True):
        quarter = row.get("quarter")
        summaryParts: list[str] = []
        fieldCount = 0
        for key, value in row.items():
            if key in {"stockCode", "year", "quarter", "quarterNum", "apiType", "stlm_dt"}:
                continue
            if value is None:
                continue
            fieldCount += 1
            summaryParts.append(f"{key}={value}")
        if fieldCount == 0:
            continue
        rows.append(
            {
                "topic": canonicalTopic,
                "period": str(row.get("year")),
                "source": "report",
                "rows": fieldCount,
                "payloadRef": f"report:{apiType}:{quarter}",
                "summary": "; ".join(summaryParts[:6]),
                "priority": 200,
            }
        )
    if not rows:
        return None

    first = rows[0]
    return {
        "topic": canonicalTopic,
        "period": None,
        "primarySource": "report",
        "fallbackSources": [],
        "selectedPayloadRef": first["payloadRef"],
        "availableSources": [
            {
                "source": "report",
                "rows": sum(int(row["rows"]) for row in rows),
                "payloadRef": first["payloadRef"],
                "summary": first["summary"],
                "priority": 200,
            }
        ],
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


def baselinePayload(company, caseName: str, topic: str | None) -> Any:
    if caseName == "financeShow":
        return company.show(topic)
    if caseName == "financeTrace":
        return company.trace(topic)
    if caseName == "reportShow":
        return company.show(topic)
    if caseName == "reportTrace":
        return company.trace(topic)
    raise ValueError(f"unknown caseName: {caseName}")


def candidatePayload(company, caseName: str, topic: str | None) -> Any:
    if caseName == "financeShow":
        return financeShowFast(company, str(topic))
    if caseName == "financeTrace":
        return financeTraceFast(company, str(topic))
    if caseName == "reportShow":
        return company._showReportTopic(str(topic))
    if caseName == "reportTrace":
        return reportTraceFast(company, str(topic))
    raise ValueError(f"unknown caseName: {caseName}")


def runChildCase(stockCode: str, caseName: str, topic: str | None) -> dict[str, Any]:
    import dartlab

    candidateCompany = dartlab.Company(stockCode)
    candidate, candidateMetrics = measurePhase(lambda: candidatePayload(candidateCompany, caseName, topic))
    candidateCacheKeys = set(candidateCompany._cache._store.keys())
    candidateDigest = BASELINE.payloadDigest(candidate)
    candidateShape = BASELINE.payloadShape(candidate)
    del candidateCompany
    del candidate
    gc.collect()

    baselineCompany = dartlab.Company(stockCode)
    baseline, baselineMetrics = measurePhase(lambda: baselinePayload(baselineCompany, caseName, topic))
    baselineDigest = BASELINE.payloadDigest(baseline)
    baselineShape = BASELINE.payloadShape(baseline)

    result = {
        "stockCode": stockCode,
        "caseName": caseName,
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
    return result


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    parser.add_argument("--caseName", required=True)
    parser.add_argument("--topic")
    args = parser.parse_args()
    result = runChildCase(args.stockCode, args.caseName, args.topic)
    print(json.dumps(result, ensure_ascii=False))


def caseSpecs() -> list[dict[str, str]]:
    specs: list[dict[str, str]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
        for topic in FINANCE_SHOW_TOPICS:
            specs.append({"stockCode": stockCode, "caseName": "financeShow", "topic": topic})
        for topic in FINANCE_TRACE_TOPICS:
            specs.append({"stockCode": stockCode, "caseName": "financeTrace", "topic": topic})
        reportTopic = chooseReportTopic(stockCode)
        if reportTopic is not None:
            specs.append({"stockCode": stockCode, "caseName": "reportShow", "topic": reportTopic})
            specs.append({"stockCode": stockCode, "caseName": "reportTrace", "topic": reportTopic})
    return specs


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in caseSpecs():
        command = [
            "uv",
            "run",
            "python",
            "-X",
            "utf8",
            str(Path(__file__).resolve()),
            "--child",
            "--stockCode",
            spec["stockCode"],
            "--caseName",
            spec["caseName"],
            "--topic",
            spec["topic"],
        ]
        completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode != 0:
            raise RuntimeError(
                f"child failed: {spec}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    total = len(rows)
    exact = sum(1 for row in rows if row["exact"])
    print(f"total={total} exact={exact}/{total}")
    byCase: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        byCase.setdefault(row["caseName"], []).append(row)
    for caseName, caseRows in byCase.items():
        exactCount = sum(1 for row in caseRows if row["exact"])
        speedups = [
            row["baselineElapsedSec"] / row["candidateElapsedSec"]
            for row in caseRows
            if row["candidateElapsedSec"] > 0 and row["baselineElapsedSec"] > 0
        ]
        minSpeedup = min(speedups) if speedups else None
        maxSpeedup = max(speedups) if speedups else None
        print(
            json.dumps(
                {
                    "caseName": caseName,
                    "exact": f"{exactCount}/{len(caseRows)}",
                    "minSpeedup": None if minSpeedup is None else round(minSpeedup, 2),
                    "maxSpeedup": None if maxSpeedup is None else round(maxSpeedup, 2),
                    "hasSections": sum(1 for row in caseRows if row["candidateHasSections"]),
                    "hasProfileFacts": sum(1 for row in caseRows if row["candidateHasProfileFacts"]),
                    "hasRetrievalBlocks": sum(1 for row in caseRows if row["candidateHasRetrievalBlocks"]),
                },
                ensure_ascii=False,
            )
        )


def main() -> None:
    if "--child" in sys.argv:
        sys.argv.remove("--child")
        childMain()
        return
    rows = runParent()
    printSummary(rows)


if __name__ == "__main__":
    main()
