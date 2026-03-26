"""
실험 ID: 011
실험명: Report Block Index From RetrievalBlocks

목적:
- `show("majorHolder")` blockless index를 `retrievalBlocks`만으로 exact 재현 가능한지 검증
- docs block identity를 `rawTitle + blockIdx + blockType` 최신 우선 dedupe로 근사할 수 있는지 확인

가설:
1. `majorHolder` docs block index는 `retrievalBlocks(topic)`를 `(rawTitle, blockIdx, blockType)`로 dedupe하면 public index와 같아진다
2. 여기에 report row 1개를 끝에 붙이면 blockless `show("majorHolder")` exact가 가능하다

방법:
1. 샘플 6종목을 fresh subprocess에서 실행한다
2. `retrievalBlocks(stockCode)`에서 topic=`majorHolder`만 고른 뒤 최신 우선 정렬 상태에서 `(rawTitle, blockIdx, blockType)` unique를 유지한다
3. 각 대표 row로 `block,type,source,preview`를 만들고 report row를 1개 추가한다
4. baseline public `show(topic)`와 digest를 비교한다

결과 (실험 후 작성):
- 총 6개 case 비교
- exact match: `0/6`
- candidate shape vs baseline shape:
  - `005930`: `68x4` vs `83x4`
  - `000660`: `219x4` vs `654x4`
  - `005380`: `110x4` vs `127x4`
  - `105560`: `87x4` vs `68x4`
  - `035420`: `76x4` vs `89x4`
  - `005490`: `97x4` vs `130x4`
- `rawTitle + blockIdx + blockType` 최신 우선 dedupe만으로는 어떤 종목은 block 수가 부족하고 어떤 종목은 과다했다

결론:
- **기각**
- `retrievalBlocks`에는 public blockless `show("majorHolder")`를 복원하기 위한 안정적인 block identity key가 그대로 있지 않다
- report blockless `show()`는 여전히 docs block identity 정렬 규칙을 별도로 풀어야 한다

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


BASELINE = loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline011")
POLARS_SPLIT = loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit011")


def hasReportTopic(stockCode: str, topic: str) -> bool:
    return topic in {POLARS_SPLIT.reportUserTopic(apiType) for apiType in POLARS_SPLIT.fastAvailableApiTypes(stockCode)}


def buildCandidate(stockCode: str, topic: str) -> pl.DataFrame | None:
    from dartlab.providers.dart.docs.sections import retrievalBlocks

    blocks = retrievalBlocks(stockCode).filter(pl.col("topic") == topic)
    if blocks.is_empty() and not hasReportTopic(stockCode, topic):
        return None

    docsRows: list[dict[str, Any]] = []
    if not blocks.is_empty():
        deduped = blocks.unique(subset=["rawTitle", "blockIdx", "blockType"], keep="first", maintain_order=True)
        for idx, row in enumerate(deduped.iter_rows(named=True)):
            docsRows.append(
                {
                    "block": idx,
                    "type": str(row["blockType"]),
                    "source": "docs",
                    "preview": str(row["blockText"] or "")[:50],
                }
            )

    if hasReportTopic(stockCode, topic):
        docsRows.append(
            {
                "block": len(docsRows),
                "type": "table",
                "source": "report",
                "preview": "(report)",
            }
        )

    return pl.DataFrame(docsRows) if docsRows else None


def childRun(stockCode: str, topic: str) -> dict[str, Any]:
    import dartlab

    candidate = buildCandidate(stockCode, topic)
    baseline = dartlab.Company(stockCode).show(topic)
    return {
        "stockCode": stockCode,
        "topic": topic,
        "exact": BASELINE.payloadDigest(candidate) == BASELINE.payloadDigest(baseline),
        "candidateDigest": BASELINE.payloadDigest(candidate),
        "baselineDigest": BASELINE.payloadDigest(baseline),
        "candidateShape": BASELINE.payloadShape(candidate),
        "baselineShape": BASELINE.payloadShape(baseline),
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
    print(json.dumps({"total": len(rows), "exact": f"{sum(1 for row in rows if row['exact'])}/{len(rows)}"}, ensure_ascii=False))
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
