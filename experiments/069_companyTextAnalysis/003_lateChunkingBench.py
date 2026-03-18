"""
실험 ID: 069-003
실험명: chunking 전략 비교

목적:
- 현재 slice, paragraph split, late-context proxy 중 어떤 전략이 장문 텍스트 retrieval에 유리한지 확인한다.

가설:
1. 단순 현재 slice보다 paragraph 분할이 장문 retrieval에 유리하다.
2. late-context proxy가 dense retrieval 정밀도를 추가로 높인다.

방법:
1. retrieval/change/summary 케이스만 사용한다.
2. current / paragraph / late 전략으로 bge dense retrieval을 평가한다.
3. Hit@k, MRR@10, nDCG@10, latency를 비교한다.

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
    results = mod.run_late_chunking_bench(cases)
    frame = pl.DataFrame([asdict(v) for v in results.values()]).sort("hit5", descending=True)
    print(frame)


if __name__ == "__main__":
    main()
