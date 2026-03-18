"""
실험 ID: 069-005
실험명: grounded summary benchmark

목적:
- summary 케이스 8개에서 raw concat, grounded local summary, hierarchical local summary를 비교한다.

가설:
1. raw concat은 빠르지만 필수 사실 커버리지가 약하다.
2. grounded local summary가 필수 사실 커버리지를 높인다.
3. hierarchical local summary는 로컬 환경에서 더 안정적인 대안일 수 있다.

방법:
1. 069-001의 manual summary spec을 사용한다.
2. S0, S1, S2를 실행한다.
3. required-fact coverage, forbidden hit, citation coverage, latency를 비교한다.

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
    results = mod.run_summary_bench(corpus, cases)
    frame = pl.DataFrame([asdict(v) for v in results.values()]).sort("requiredCoverage", descending=True)
    print(frame)


if __name__ == "__main__":
    main()
