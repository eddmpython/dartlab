"""
실험 ID: 069-007
실험명: full-universe operational stress

목적:
- benchmark winner retrieval stack의 운영 가능성을 전체 docs universe에서 확인한다.

가설:
1. benchmark winner가 전체 종목에서도 예외 없이 반복 실행된다.
2. 최근 4개 기간 기준으로는 전체 universe에서도 운영 가능한 시간/메모리 범위에 들어온다.

방법:
1. 로컬 docs 보유 전체 종목 코드를 수집한다.
2. target topic 10개, 최근 4개 기간으로 corpus를 만든다.
3. benchmark retrieval winner를 같은 방식으로 전체 corpus에 적용한다.
4. rows, index build time, query latency, memory, error count를 출력한다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

import polars as pl
import psutil


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
    all_codes = mod.all_available_doc_codes()
    t0 = time.perf_counter()
    corpus = mod.build_corpus_for_codes(all_codes, last_n=4)
    build_sec = time.perf_counter() - t0
    cases = mod.build_benchmark_cases(mod.load_benchmark_corpus())
    retrieval_results = mod.run_retrieval_methods(mod.load_benchmark_corpus(), cases)
    winner = sorted(retrieval_results.values(), key=lambda x: (x.hit5, x.mrr10), reverse=True)[0]
    process = psutil.Process()
    mem_mb = process.memory_info().rss / 1024 / 1024
    summary = {
        "codes": len(all_codes),
        "rows": corpus.height,
        "periods": corpus["period"].n_unique(),
        "winner": winner.method,
        "corpusBuildSec": round(build_sec, 2),
        "rssMB": round(mem_mb, 2),
    }
    print(pl.DataFrame([summary], strict=False))


if __name__ == "__main__":
    main()
