"""
실험 ID: 069-008
실험명: Company 흡수 readiness 판정

목적:
- 069 전체 결과를 흡수 관점에서 ABSORB / HOLD / REJECT로 정리한다.

가설:
1. retrieval, extraction, summary를 함께 보면 흡수 시점이 분명해진다.
2. retrieval만 강하고 summary/extraction이 약하면 HOLD가 적절하다.

방법:
1. benchmark corpus/cases를 다시 만든다.
2. retrieval/extraction/summary winner를 계산한다.
3. gate와 비교해 최종 판정을 내린다.

결과 (실험 후 작성):

결론:

실험일: 2026-03-18
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_mod():
    path = Path(__file__).with_name("001_goldBenchmark.py")
    spec = importlib.util.spec_from_file_location("bench001", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _judge(retrieval, extraction, summary):
    retrieval_pass = retrieval.hit5 >= 0.90 and retrieval.mrr10 >= 0.40
    extraction_pass = extraction.f1 >= 0.80 and min(extraction.labelF1.values()) >= 0.70
    summary_pass = summary.requiredCoverage >= 0.85 and summary.forbiddenHitRate <= 0.10 and summary.citationCoverage == 1.0
    if retrieval_pass and extraction_pass and summary_pass:
        return "ABSORB"
    if retrieval.hit5 >= 0.80 and (extraction.f1 >= 0.50 or summary.requiredCoverage >= 0.60):
        return "HOLD"
    return "REJECT"


def main() -> None:
    mod = _load_mod()
    corpus = mod.load_benchmark_corpus()
    cases = mod.build_benchmark_cases(corpus)
    retrieval = sorted(mod.run_retrieval_methods(corpus, cases).values(), key=lambda x: (x.hit5, x.mrr10), reverse=True)[0]
    extraction = sorted(mod.run_extraction_bench(corpus).values(), key=lambda x: x.f1, reverse=True)[0]
    summary = sorted(mod.run_summary_bench(corpus, cases).values(), key=lambda x: x.requiredCoverage, reverse=True)[0]
    print(
        {
            "decision": _judge(retrieval, extraction, summary),
            "retrievalWinner": retrieval.method,
            "extractionWinner": extraction.method,
            "summaryWinner": summary.method,
        }
    )


if __name__ == "__main__":
    main()
