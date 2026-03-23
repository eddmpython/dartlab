"""
실험 ID: 088-006
실험명: understanding bundle benchmark

목적:
- 검색 결과를 단순 row 목록이 아닌 AI 이해용 bundle로 묶을 수 있는지 확인한다.
- summary/change 계열 질문에서 gist, evidence, stitched table, change pair가 실제로 채워지는지 본다.

가설:
1. bundle 조립만으로도 summary/change 질문의 required fact coverage를 높일 수 있다.
2. stitchedTables와 changePairs를 함께 주면 AI가 후속 reasoning을 더 쉽게 할 수 있다.

방법:
1. 069 benchmark의 summary/change 케이스만 사용한다.
2. case마다 UnderstandingBundle을 만든다.
3. requiredFactCoverage, citationCoverage, stitched table 수, change pair 수를 집계한다.

결과 (실험 후 작성):
- safe codes: ["005930"]
- caseCount: 3
- requiredFactCoverage: 0.5556
- citationCoverage: 1.0
- avgStitchedTables: 2.6667
- avgChangePairs: 1.6667
- cache-backed safe2 codes: ["005930", "000660"]
- cache-backed caseCount: 7
- cache-backed requiredFactCoverage: 0.6667
- cache-backed avgStitchedTables: 2.8571
- cache-backed avgChangePairs: 1.8571
- first-build memory note: benchmark corpus build 과정에서 RSS 1.98GB까지 상승
- rerun note: corpus cache 재사용 시 메모리 경고 없이 재실행 가능

결론:
- 1종목 안전 샘플에서도 bundle 계층이 fact coverage를 끌어올릴 수 있다는 신호가 나왔다.
- stitchedTables와 changePairs가 모두 실질적으로 생성되어 “AI 이해 단위” 설계 방향이 더 설득력 있어졌다.
- 2종목 cache-backed 실행에서는 bundle 품질이 더 좋아졌고 재실행 안정성도 확보됐다.

실험일: 2026-03-23
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

SAFE_CODES = ["005930"]
PREFERRED_CODES = ["005930", "000660"]
LAST_N = 12


def loadUnitModule():
    path = Path(__file__).with_name("001_unitSchema.py")
    spec = importlib.util.spec_from_file_location("leg001", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selectedCodes() -> list[str]:
    raw = os.getenv("LEGINDEX_CODES", "").strip()
    if not raw:
        outputDir = Path(__file__).with_name("output") / "benchmarkCorpus"
        cacheReady = all((outputDir / f"{code}.last{LAST_N}.parquet").exists() for code in PREFERRED_CODES)
        return PREFERRED_CODES if cacheReady else SAFE_CODES
    return [code.strip() for code in raw.split(",") if code.strip()]


def main() -> None:
    mod = loadUnitModule()
    summary = mod.runUnderstandingBundleExperiment(codes=selectedCodes())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
