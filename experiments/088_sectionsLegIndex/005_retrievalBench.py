"""
실험 ID: 088-005
실험명: sections LegIndex retrieval benchmark

목적:
- 기존 069 benchmark를 unit retrieval 관점으로 다시 평가한다.
- raw/contextual BM25 및 기존 dense/hybrid winner 대비 LegIndex의 위치를 확인한다.

가설:
1. 구조 기반 LegIndex는 raw BM25보다 높은 hit 안정성을 가진다.
2. dense/hybrid baseline보다 latency와 build cost는 압도적으로 작다.
3. unit retrieval로 바꾸면 required fact coverage와 citation coverage도 함께 개선된다.

방법:
1. 069 benchmark corpus/cases를 그대로 사용한다.
2. 기존 baseline 4개(raw BM25, contextual BM25, dense winner, hybrid winner)를 함께 계산한다.
3. LegIndex로 case별 top10 unit을 검색한다.
4. Hit@1/3/5, MRR@10, nDCG@10, goldRecall@10, requiredFactCoverage, citationCoverage, latency를 비교한다.

결과 (실험 후 작성):
- safe codes: ["005930"]
- baselineMode: safe2
- caseCount: 9
- mappedCaseCount: 9
- raw BM25 hit@5: 0.0 / medianLatencyMs: 52.8122
- contextual BM25 hit@5: 0.0 / goldRecall@10: 0.0556 / medianLatencyMs: 61.2693
- LegIndex hit@1: 0.6667
- LegIndex hit@3: 0.8889
- LegIndex hit@5: 0.8889
- LegIndex mrr@10: 0.7593
- LegIndex requiredFactCoverage: 0.6852
- LegIndex citationCoverage: 1.0
- LegIndex medianLatencyMs: 48.3954
- LegIndex p95LatencyMs: 57.2249
- skipped baselines: D2_bge_dense, H2_contextual_plus_bge
- cache-backed safe2 codes: ["005930", "000660"]
- cache-backed caseCount: 20
- cache-backed LegIndex hit@5: 0.65
- cache-backed LegIndex mrr@10: 0.4963
- cache-backed LegIndex requiredFactCoverage: 0.6667
- cache-backed LegIndex medianLatencyMs: 74.3235
- first-build memory note: benchmark corpus build 과정에서 RSS 1.98GB까지 상승
- rerun note: `output/benchmarkCorpus/*.parquet` 재사용 시 `loadData(...,docs)` 메모리 경고 없이 재실행 가능

결론:
- candidate pruning과 gold expansion 수정 후, 1종목 safe benchmark에서는 BM25 대비 retrieval 품질 우위가 뚜렷하게 나왔다.
- 아직 dense/hybrid와의 직접 비교는 못 했지만, 구조 기반 LegIndex 자체의 유효성은 충분히 확인됐다.
- 2종목도 cache-backed rerun에서는 안정적으로 돌아가므로, cache 존재 시 기본 실행값을 2종목으로 올릴 수 있다.
- 다만 cache를 처음 만드는 cold start는 여전히 무거워서, 더 근본적인 경량 corpus 생성은 계속 필요하다.

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
    summary = mod.runRetrievalExperiment(codes=selectedCodes(), baselineMode="safe2")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
