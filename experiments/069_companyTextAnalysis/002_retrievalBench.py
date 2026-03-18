"""
실험 ID: 069-002
실험명: retrieval baseline vs hybrid benchmark

목적:
- benchmark 40개 케이스에서 lexical/dense/hybrid/rerank retrieval을 비교한다.

가설:
1. contextual BM25가 raw BM25보다 유리하다.
2. dense 단독보다 hybrid가 안정적이다.
3. reranker는 상위권 정밀도를 높인다.

방법:
1. 069-001 benchmark corpus/cases를 로드한다.
2. B1, B2, D1, D2, H1, H2, R1을 동일 benchmark로 평가한다.
3. Hit@k, MRR@10, nDCG@10, goldRecall@10, latency를 비교한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import asdict
from pathlib import Path

import polars as pl


def _load_mod():
    path = Path(__file__).with_name("001_goldBenchmark.py")
    spec = importlib.util.spec_from_file_location("bench001", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    mod = _load_mod()
    corpus = mod.load_benchmark_corpus()
    cases = mod.build_benchmark_cases(corpus)
    results = mod.run_retrieval_methods(corpus, cases)
    frame = pl.DataFrame([asdict(v) for v in results.values()]).sort("hit5", descending=True)
    print(frame)


if __name__ == "__main__":
    main()
