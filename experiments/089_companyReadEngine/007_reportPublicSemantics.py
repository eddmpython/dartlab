"""
실험 ID: 007
실험명: Report Public Semantics Audit

목적:
- public `show(reportTopic)`와 `trace(reportTopic)`가 실제로 어떤 의미를 가지는지 6종목 기준으로 고정
- direct report payload가 왜 public 경로와 exact가 아닌지 구조적으로 확인

가설:
1. 샘플 6종목의 대표 report topic은 모두 `majorHolder`다
2. public `show(reportTopic)`는 direct report payload가 아니라 docs 기반 block index다
3. public `trace(reportTopic)`는 `primarySource=report`지만 docs fallback을 항상 함께 포함한다

방법:
1. 샘플 6종목 각각을 fresh subprocess에서 실행한다
2. 각 child에서 대표 report topic을 고르고 `show(topic)`, `_showReportTopic(topic)`, `trace(topic)`를 수집한다
3. public show의 columns, source 분포, report block 존재 여부를 기록한다
4. public trace의 primary/fallback/availableSources 구성을 기록한다

결과 (실험 후 작성):
- 총 6개 child를 fresh subprocess로 실행
- 대표 report topic은 6/6 모두 `majorHolder`
- public `show("majorHolder")`는 6/6 모두 block index `Nx4` (`block,type,source,preview`)
- public show block index에는 6/6 모두 `report` block이 정확히 1개 포함됨
- direct `_showReportTopic("majorHolder")` payload는 6/6 모두 public `show("majorHolder")`와 digest 불일치
- 대신 `show("majorHolder", firstReportBlock)`의 payload digest는 6/6 모두 direct `_showReportTopic("majorHolder")`와 정확히 일치
- public `trace("majorHolder")`는 6/6 모두 `primarySource=report`, `fallbackSources=["docs"]`, `availableSourceOrder=["report","docs"]`
- 종목별 public show vs direct report shape:
  - `005930`: `83x4` vs `645x7`
  - `000660`: `654x4` vs `162x7`
  - `005380`: `127x4` vs `536x7`
  - `105560`: `68x4` vs `89x7`
  - `035420`: `89x4` vs `117x7`
  - `005490`: `130x4` vs `76x7`

결론:
- public `show(reportTopic)`의 blockless semantics는 direct report payload가 아니라 `docs block index + report row`다
- direct report payload는 block index의 report row를 선택했을 때만 exact로 도달한다
- public `trace(reportTopic)` exact 재현에는 report source뿐 아니라 docs fallback source까지 같이 만들어야 한다
- 다음 lightweight 후보는 direct report payload 자체가 아니라 `report row가 포함된 block index`와 `dual-source trace`다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import polars as pl


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline")


def frameInfo(df: pl.DataFrame | None) -> dict[str, Any]:
    if df is None:
        return {
            "shape": None,
            "columns": None,
            "looksLikeBlockIndex": False,
            "sourceCounts": {},
            "reportBlockCount": 0,
            "firstReportBlock": None,
        }
    looksLikeBlockIndex = list(df.columns) == ["block", "type", "source", "preview"]
    sourceCounts: dict[str, int] = {}
    firstReportBlock = None
    if "source" in df.columns:
        for row in df.group_by("source").len().iter_rows(named=True):
            sourceCounts[str(row["source"])] = int(row["len"])
        if "block" in df.columns:
            reportRows = df.filter(pl.col("source") == "report")
            if not reportRows.is_empty():
                firstReportBlock = int(reportRows["block"][0])
    return {
        "shape": f"{df.height}x{df.width}",
        "columns": list(df.columns),
        "looksLikeBlockIndex": looksLikeBlockIndex,
        "sourceCounts": sourceCounts,
        "reportBlockCount": int(sourceCounts.get("report", 0)),
        "firstReportBlock": firstReportBlock,
    }


def childRun(stockCode: str) -> dict[str, Any]:
    import dartlab

    topic = BASELINE.chooseReportTopic(stockCode)
    if topic is None:
        return {"stockCode": stockCode, "topic": None}

    company = dartlab.Company(stockCode)
    publicShow = company.show(topic)
    directReport = company._showReportTopic(topic)
    publicTrace = company.trace(topic)

    publicInfo = frameInfo(publicShow if isinstance(publicShow, pl.DataFrame) else None)
    directInfo = frameInfo(directReport if isinstance(directReport, pl.DataFrame) else None)

    blockPayloadDigest = None
    blockPayloadShape = None
    if publicInfo["firstReportBlock"] is not None:
        blockPayload = company.show(topic, publicInfo["firstReportBlock"])
        blockPayloadDigest = BASELINE.payloadDigest(blockPayload)
        blockPayloadShape = BASELINE.payloadShape(blockPayload)

    return {
        "stockCode": stockCode,
        "topic": topic,
        "publicShow": publicInfo,
        "directReport": directInfo,
        "publicShowDigest": BASELINE.payloadDigest(publicShow),
        "directReportDigest": BASELINE.payloadDigest(directReport),
        "publicShowEqualsDirectReport": BASELINE.payloadDigest(publicShow) == BASELINE.payloadDigest(directReport),
        "firstReportBlockPayloadDigest": blockPayloadDigest,
        "firstReportBlockPayloadShape": blockPayloadShape,
        "publicTrace": {
            "primarySource": None if publicTrace is None else publicTrace.get("primarySource"),
            "fallbackSources": [] if publicTrace is None else publicTrace.get("fallbackSources", []),
            "availableSourceOrder": []
            if publicTrace is None
            else [row.get("source") for row in publicTrace.get("availableSources", [])],
            "availableRows": []
            if publicTrace is None
            else [row.get("rows") for row in publicTrace.get("availableSources", [])],
            "availablePayloadRefs": []
            if publicTrace is None
            else [row.get("payloadRef") for row in publicTrace.get("availableSources", [])],
        },
    }


def childMain() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stockCode", required=True)
    args = parser.parse_args()
    print(json.dumps(childRun(args.stockCode), ensure_ascii=False))


def runParent() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stockCode in BASELINE.SAMPLE_CODES:
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
        ]
        completed = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
        if completed.returncode != 0:
            raise RuntimeError(
                f"child failed: {stockCode}\nstdout={completed.stdout}\nstderr={completed.stderr}"
            )
        rows.append(json.loads(completed.stdout.strip()))
    return rows


def printSummary(rows: list[dict[str, Any]]) -> None:
    topics = sorted({row["topic"] for row in rows if row.get("topic") is not None})
    blockIndexLike = sum(1 for row in rows if row["publicShow"]["looksLikeBlockIndex"])
    withReportBlock = sum(1 for row in rows if row["publicShow"]["reportBlockCount"] > 0)
    tracePrimaryReport = sum(1 for row in rows if row["publicTrace"]["primarySource"] == "report")
    traceHasDocsFallback = sum(1 for row in rows if "docs" in row["publicTrace"]["fallbackSources"])
    print(
        json.dumps(
            {
                "total": len(rows),
                "topics": topics,
                "blockIndexLike": f"{blockIndexLike}/{len(rows)}",
                "withReportBlock": f"{withReportBlock}/{len(rows)}",
                "publicShowEqualsDirectReport": f"{sum(1 for row in rows if row['publicShowEqualsDirectReport'])}/{len(rows)}",
                "tracePrimaryReport": f"{tracePrimaryReport}/{len(rows)}",
                "traceHasDocsFallback": f"{traceHasDocsFallback}/{len(rows)}",
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
