"""
실험 ID: 091-002
실험명: LegIndex + rerank benchmark

목적:
- `LegIndex only`와 `LegIndex + rerank`를 직접 비교한다.
- dense retrieval 없이 top-K rerank만 붙여도 retrieval 품질이 실제로 개선되는지 본다.

가설:
1. `LegIndex + rerank`는 `Hit@5` 비열세를 유지하면서 requiredFactCoverage를 올릴 수 있다.
2. safe2와 top30 rerank 제한이면 latency와 RSS를 제어할 수 있다.

방법:
1. `088` sampleUnits/benchmark corpus cache를 재사용한다.
2. baseline은 raw/contextual BM25만 두고, candidate는 `LegIndex only`와 `LegIndex + rerank`를 비교한다.
3. reranker는 069의 `load_reranker()`를 그대로 쓴다.
4. retrieval/latency/RSS gate를 함께 본다.

결과 (실험 후 작성):
- codes: `005930`, `000660`
- caseCount / mappedCaseCount: `20 / 20`
- LegIndex only: `hit@5 0.65`, `mrr@10 0.4963`, `requiredFactCoverage 0.6667`, `medianLatencyMs 70.6481`
- LegIndex + rerank: `hit@1 0.45`, `hit@5 0.7`, `mrr@10 0.53`, `goldRecall@10 0.1768`, `requiredFactCoverage 0.6083`, `medianLatencyMs 34290.6811`
- rerankerLoadSec: `5.0483`
- peakMemoryMb: `4205.57`
- accepted: `False`

결론:
- 현재 `BAAI/bge-reranker-v2-m3`를 top30 rerank로 붙이는 경로는 reject다.
- retrieval rank 자체는 조금 좋아졌지만 `requiredFactCoverage`가 오히려 떨어졌고, latency와 메모리가 gate를 심각하게 위반했다.
- 즉 “rerank only” 개념은 남지만, 현재 모델과 경로는 DartLab의 메모리/속도 조건에 맞지 않는다.

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
    path = Path(__file__).resolve().parents[1] / "088_sectionsLegIndex" / "001_unitSchema.py"
    spec = importlib.util.spec_from_file_location("leg088", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def selectedCodes() -> list[str]:
    raw = os.getenv("LEGRERANK_CODES", "").strip()
    if raw:
        return [code.strip() for code in raw.split(",") if code.strip()]
    outputDir = Path(__file__).resolve().parents[1] / "088_sectionsLegIndex" / "output" / "benchmarkCorpus"
    cacheReady = all((outputDir / f"{code}.last{LAST_N}.parquet").exists() for code in PREFERRED_CODES)
    return PREFERRED_CODES if cacheReady else SAFE_CODES


def main() -> None:
    mod = loadUnitModule()
    summary = mod.runLegRerankExperiment(codes=selectedCodes(), lastN=LAST_N)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
