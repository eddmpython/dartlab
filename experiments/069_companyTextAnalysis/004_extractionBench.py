"""
실험 ID: 069-004
실험명: entity extraction benchmark

목적:
- benchmark의 extraction 케이스 8개에서 regex, GLiNER, 로컬 LLM 추출을 비교한다.

가설:
1. regex baseline은 precision은 높지만 recall이 낮다.
2. GLiNER가 가장 균형적인 F1을 보인다.
3. 로컬 LLM 추출은 지연시간이 크고 JSON 안정성이 약할 수 있다.

방법:
1. 069-001의 manual extraction spec을 사용한다.
2. regex baseline, GLiNER, qwen3 extraction을 실행한다.
3. precision/recall/F1, label별 F1, latency를 비교한다.

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
    results = mod.run_extraction_bench(corpus)
    frame = pl.DataFrame([asdict(v) for v in results.values()]).sort("f1", descending=True)
    print(frame)


if __name__ == "__main__":
    main()
