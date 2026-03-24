"""
실험 ID: 091-001
실험명: contextual prefix BM25 bench

목적:
- `contextSlices`에 최소 contextual prefix를 붙였을 때 BM25 recall이 실제로 좋아지는지 확인한다.
- dense 없이도 구조 메타 prefix만으로 retrieval 품질을 끌어올릴 수 있는지 본다.

가설:
1. `stockCode/topic/period/block/semantic/detail/blockLabel` prefix를 붙이면 contextual BM25보다 hit 안정성이 좋아질 수 있다.
2. prefix는 build cost를 거의 늘리지 않으면서 goldRecall과 hit@5를 개선할 수 있다.

방법:
1. `088` benchmark corpus cache를 우선 사용한다.
2. `safe2` 종목에서 기존 contextual BM25와 prefix-added contextual BM25를 비교한다.
3. Hit@1/3/5, MRR@10, nDCG@10, goldRecall@10, latency를 기록한다.

결과 (실험 후 작성):
- codes: `005930`, `000660`
- caseCount: `20`
- current contextual BM25: `hit@3 0.05`, `hit@5 0.1`, `mrr@10 0.0675`, `goldRecall@10 0.15`, `medianLatencyMs 46.1481`
- prefixed contextual BM25: `hit@3 0.1`, `hit@5 0.1`, `mrr@10 0.0850`, `goldRecall@10 0.2`, `medianLatencyMs 47.8396`
- winner: `B3_prefixed_contextual_bm25`

결론:
- 짧은 prefix만으로도 contextual BM25보다 `hit@3`, `mrr`, `goldRecall`이 개선됐다.
- latency 증가는 작아서, 이 prefix 규칙은 다음 단계 hybrid retrieval의 저비용 recall 보강책으로 채택할 가치가 있다.

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
    summary = mod.runContextualPrefixExperiment(codes=selectedCodes(), lastN=LAST_N)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
