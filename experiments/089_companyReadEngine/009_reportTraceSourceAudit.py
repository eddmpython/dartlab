"""
실험 ID: 009
실험명: Report Trace Source Audit

목적:
- public `trace("majorHolder")`의 report/docs source가 각각 어떤 lightweight 입력에서 복원되는지 검증
- exact reconstruction 전에 source별 rows/payloadRef/summary 공식이 맞는지 확인

가설:
1. `trace("majorHolder")`의 docs source는 `retrievalBlocks(topic)`만으로 rows/payloadRef/summary를 그대로 복원할 수 있다
2. `trace("majorHolder")`의 report source는 direct report payload 요약으로 rows/payloadRef/summary를 그대로 복원할 수 있다

방법:
1. 샘플 6종목을 fresh subprocess에서 실행한다
2. baseline `company.trace(topic)`에서 docs/report source row를 분리한다
3. docs candidate는 `retrievalBlocks(stockCode).filter(topic == topic)`의 `height`, 첫 `cellKey`, 첫 `blockText[:400]`를 사용한다
4. report candidate는 006의 direct report trace helper를 재사용한다
5. source별 rows/payloadRef/summary 일치 여부를 기록한다

결과 (실험 후 작성):
- 총 6개 child를 fresh subprocess로 실행
- docs source 공식은 `rows/payloadRef/summary` 모두 `6/6` exact
  - `rows` = `retrievalBlocks(topic).height`
  - `payloadRef` = 첫 `cellKey`
  - `summary` = 첫 `blockText[:400]`
- report source 공식도 `rows/payloadRef/summary` 모두 `6/6` exact
  - `rows/payloadRef/summary`가 006의 direct report trace helper와 완전히 같음
- 즉 public `trace("majorHolder")`의 `availableSources`는 source별로 가볍게 완전 재구성 가능함

결론:
- docs source는 `retrievalBlocks(topic)`만으로 exact 복원된다
- report source는 direct report trace helper로 exact 복원된다
- 따라서 `trace("majorHolder")` full dict exact candidate는 바로 만들 수 있다

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


def loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline009")
AUTH = loadModule(Path(__file__).with_name("006_authoritativeFollowUp.py"), "exp089Authoritative009")


def childRun(stockCode: str) -> dict[str, Any]:
    import dartlab
    from dartlab.providers.dart.docs.sections import retrievalBlocks

    topic = BASELINE.chooseReportTopic(stockCode)
    if topic is None:
        return {"stockCode": stockCode, "topic": None}

    company = dartlab.Company(stockCode)
    trace = company.trace(topic)
    if trace is None:
        return {"stockCode": stockCode, "topic": topic, "trace": None}

    docsSource = next(row for row in trace["availableSources"] if row.get("source") == "docs")
    reportSource = next(row for row in trace["availableSources"] if row.get("source") == "report")

    blocks = retrievalBlocks(stockCode).filter(__import__("polars").col("topic") == topic)
    firstCellKey = None if blocks.is_empty() else str(blocks["cellKey"][0])
    firstBlockText = None if blocks.is_empty() else str(blocks["blockText"][0])[:400]

    reportFast = AUTH.reportTraceFast(company, topic)
    reportFastSource = None if reportFast is None else reportFast["availableSources"][0]

    return {
        "stockCode": stockCode,
        "topic": topic,
        "docsBaseline": docsSource,
        "docsCandidate": {
            "rows": int(blocks.height),
            "payloadRef": firstCellKey,
            "summary": firstBlockText,
        },
        "docsRowsMatch": int(docsSource.get("rows")) == int(blocks.height),
        "docsPayloadMatch": docsSource.get("payloadRef") == firstCellKey,
        "docsSummaryMatch": docsSource.get("summary") == firstBlockText,
        "reportBaseline": reportSource,
        "reportCandidate": reportFastSource,
        "reportRowsMatch": None if reportFastSource is None else reportSource.get("rows") == reportFastSource.get("rows"),
        "reportPayloadMatch": None
        if reportFastSource is None
        else reportSource.get("payloadRef") == reportFastSource.get("payloadRef"),
        "reportSummaryMatch": None
        if reportFastSource is None
        else reportSource.get("summary") == reportFastSource.get("summary"),
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
    total = len(rows)
    print(
        json.dumps(
            {
                "total": total,
                "docsRowsMatch": f"{sum(1 for row in rows if row.get('docsRowsMatch'))}/{total}",
                "docsPayloadMatch": f"{sum(1 for row in rows if row.get('docsPayloadMatch'))}/{total}",
                "docsSummaryMatch": f"{sum(1 for row in rows if row.get('docsSummaryMatch'))}/{total}",
                "reportRowsMatch": f"{sum(1 for row in rows if row.get('reportRowsMatch'))}/{total}",
                "reportPayloadMatch": f"{sum(1 for row in rows if row.get('reportPayloadMatch'))}/{total}",
                "reportSummaryMatch": f"{sum(1 for row in rows if row.get('reportSummaryMatch'))}/{total}",
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
