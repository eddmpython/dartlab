"""
실험 ID: 069-006
실험명: full-stack winner 조합 평가

목적:
- retrieval, extraction, summary winner를 결합해 full-stack 기준으로 흡수 가능성을 평가한다.

가설:
1. retrieval winner + extraction winner + summary winner 조합으로 흡수 기준 근처까지 갈 수 있다.
2. 병목은 retrieval보다 summary 또는 extraction일 가능성이 높다.

방법:
1. 069-002/004/005 성격의 계산을 다시 수행한다.
2. 각 실험의 최고 점수 방법을 winner로 선택한다.
3. balanced gate와 비교해 PASS/WARN/FAIL을 출력한다.

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


def _gate(retrieval, extraction, summary):
    ok_retrieval = retrieval.hit5 >= 0.90 and retrieval.mrr10 >= 0.40
    ok_extraction = extraction.f1 >= 0.80 and min(extraction.labelF1.values()) >= 0.70
    ok_summary = (
        summary.requiredCoverage >= 0.85
        and summary.forbiddenHitRate <= 0.10
        and summary.citationCoverage == 1.0
    )
    if ok_retrieval and ok_extraction and ok_summary:
        return "PASS"
    if retrieval.hit5 >= 0.80 and extraction.f1 >= 0.60 and summary.requiredCoverage >= 0.60:
        return "WARN"
    return "FAIL"


def main() -> None:
    mod = _load_mod()
    corpus = mod.load_benchmark_corpus()
    cases = mod.build_benchmark_cases(corpus)
    retrieval = sorted(mod.run_retrieval_methods(corpus, cases).values(), key=lambda x: (x.hit5, x.mrr10), reverse=True)[0]
    extraction = sorted(mod.run_extraction_bench(corpus).values(), key=lambda x: x.f1, reverse=True)[0]
    summary = sorted(mod.run_summary_bench(corpus, cases).values(), key=lambda x: x.requiredCoverage, reverse=True)[0]
    gate = _gate(retrieval, extraction, summary)
    frame = pl.DataFrame(
        [
            {"kind": "retrieval", **asdict(retrieval)},
            {"kind": "extraction", **asdict(extraction)},
            {"kind": "summary", **asdict(summary)},
        ],
        strict=False,
    )
    print(frame)
    print({"gate": gate, "retrievalWinner": retrieval.method, "extractionWinner": extraction.method, "summaryWinner": summary.method})


if __name__ == "__main__":
    main()
