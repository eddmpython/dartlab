"""
실험 ID: 003
실험명: topic-scoped docs only

목적:
- docs topic `show()`를 Company 인스턴스 없이 raw docs 파일만으로 재현 가능한지 검증
- latest report + target topic block index 경로가 baseline과 얼마나 같은지 측정

가설:
1. docs block index는 Company를 만들지 않고도 raw docs만으로 충분히 재현 가능하다
2. `show("companyOverview")`, `show("businessOverview")`는 `_sections` 없이도 메모리를 크게 줄인다

방법:
1. 001 baseline harness의 docsOnly case group만 사용
2. 002의 topic-scoped block index helper를 재사용하되 Company 생성은 생략
3. baseline과 payload digest, 시간, 피크 RSS를 비교한다

결과 (실험 후 작성):
- 총 12개 case(6종목 × docs show 2개) 비교
- exact match: 0/12
- show("companyOverview"): 47.69~97.58x faster, peak 62.0~72.8% 절감
- show("businessOverview"): 40.81~93.33x faster, peak 59.0~73.0% 절감
- `_sections` cache는 12/12에서 생성되지 않음
- 대표 케이스 005930 `show("companyOverview")`는 baseline block index와 달리 95x4 shape로 나와 digest가 완전히 달랐음

결론:
- **기각**
- latest report 기준 topic-scoped block index는 매우 빠르고 가볍지만, 현재 public `show()`와 동일 결과를 만들지 못한다
- docs exact를 원하면 최신 기간만 보는 우회로는 부족하고, period alignment / block identity 규칙을 더 가져와야 한다

실험일: 2026-03-23
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))


def _loadModule(path: Path, moduleName: str):
    spec = importlib.util.spec_from_file_location(moduleName, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module load failed: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINE = _loadModule(Path(__file__).with_name("001_baselineHarness.py"), "exp089Baseline003")
POLARS_SPLIT = _loadModule(Path(__file__).with_name("002_polarsRouteSplit.py"), "exp089PolarsSplit003")


def runTopicScopedDocsCase(stockCode: str, caseName: str, topic: str | None) -> tuple[Any, dict[str, Any]]:
    if caseName == "showCompanyOverview":
        payload: Any = POLARS_SPLIT.buildDocsTopicBlockIndex(stockCode, "companyOverview")
    elif caseName == "showBusinessOverview":
        payload = POLARS_SPLIT.buildDocsTopicBlockIndex(stockCode, "businessOverview")
    else:
        raise ValueError(f"docsOnly 실험에 없는 caseName: {caseName}")
    return payload, {"hasSectionsCache": False, "reportTopic": topic}


def childMain() -> None:
    BASELINE.childMain(runTopicScopedDocsCase)


def main() -> None:
    if "--child" in sys.argv:
        childMain()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--mode", default="topicScopedDocs")
    parser.add_argument("--caseGroup", default="docsOnly", choices=["docsOnly"])
    args = parser.parse_args()
    baselineRows = BASELINE.collectMode(Path(__file__).with_name("001_baselineHarness.py"), "baseline", "docsOnly")
    candidateRows = BASELINE.collectMode(Path(__file__), "topicScopedDocs", "docsOnly")
    BASELINE.printSummary("topicScopedDocs / docsOnly", candidateRows)
    BASELINE.printComparisonSummary(
        "topicScopedDocs vs baseline / docsOnly",
        BASELINE.compareRuns(baselineRows, candidateRows),
    )


if __name__ == "__main__":
    main()
