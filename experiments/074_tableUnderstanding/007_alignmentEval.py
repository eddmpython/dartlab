"""
실험 ID: 074-007
실험명: row/header alignment 품질 평가

목적:
- raw row label 대비 row core normalization이 실제로 period alignment를 개선하는지 본다.
- horizontalize 후보 bundle에서 row drift와 header drift가 어느 정도인지 수치화한다.

가설:
1. row label 그대로보다 row core를 쓰면 adjacent-period Jaccard가 올라간다.
2. comparative topic일수록 raw -> core overlap 개선폭이 크다.
3. alignment 개선폭은 scorer가 canonical row를 만드는 근거가 된다.

방법:
1. goldAction이 horizontalize인 seed entry만 고른다.
2. 같은 blockOrder row의 period별 markdown을 TableIR로 변환한다.
3. adjacent period 간 raw row label Jaccard와 row core Jaccard를 비교한다.

결과 (실험 후 작성):
- horizontalize gold subset의 adjacent-period pair `689개`를 평가했다.
- raw row-label Jaccard median `1.0000`, core Jaccard median `1.0000`
- raw mean `0.8405` -> core mean `0.8478`, 평균 개선폭 `+0.0073`
- 관측 topic은 `majorHolder 160`, `shareCapital 159`, `dividend 157`, `rawMaterial 72`, `salesOrder 72`, `riskDerivative 69`
- 실행 시간: 약 `154.9초`

결론:
- row core normalization은 분명히 도움은 주지만, 현재 seed subset에서는 개선폭이 작다.
- 즉 1차 병목은 row label 정규화 자체보다 action 판정과 bundle matching 쪽에 더 가깝다.
- alignment는 후속 개선 과제로 남기되, 이번 라운드의 핵심 승부처는 scorer/action layer다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parent


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_seed = load_script("002_seedGoldSet")
_ir = load_script("003_tableIR")


def jaccard(values1: list[str], values2: list[str]) -> float:
    set1 = {value for value in values1 if value}
    set2 = {value for value in values2 if value}
    union = len(set1 | set2)
    return len(set1 & set2) / union if union else 0.0


def evaluate_alignment() -> dict[str, object]:
    seed = [entry for entry in _seed.build_seed_gold_set() if str(entry["goldAction"]) == "horizontalize"]
    raw_scores: list[float] = []
    core_scores: list[float] = []
    topic_counter: Counter[str] = Counter()
    for entry in seed:
        frame = _seed.topic_frame(str(entry["stockCode"]), str(entry["topic"]))
        if frame is None:
            continue
        row = frame.filter(pl.col("blockOrder") == int(entry["blockOrder"]))
        if row.is_empty():
            continue
        row_dict = row.iter_rows(named=True).__next__()
        period_cols = _seed.period_columns(frame)
        period_payloads = []
        for period in period_cols:
            md = row_dict.get(period)
            if isinstance(md, str) and "|" in md:
                local_entry = dict(entry)
                local_entry["latestMarkdown"] = md
                local_entry["latestPeriod"] = period
                period_payloads.append(_ir.build_table_ir(local_entry))
        if len(period_payloads) < 2:
            continue
        for left, right in zip(period_payloads, period_payloads[1:]):
            raw_scores.append(jaccard(left.rowLabels, right.rowLabels))
            core_scores.append(jaccard(left.rowCore, right.rowCore))
            topic_counter[left.topic] += 1
    return {
        "pairs": len(raw_scores),
        "rawMedian": round(float(pl.Series(raw_scores).median()) if raw_scores else 0.0, 4),
        "coreMedian": round(float(pl.Series(core_scores).median()) if core_scores else 0.0, 4),
        "deltaMedian": round(
            (float(pl.Series(core_scores).median()) if core_scores else 0.0)
            - (float(pl.Series(raw_scores).median()) if raw_scores else 0.0),
            4,
        ),
        "rawMean": round(sum(raw_scores) / len(raw_scores), 4) if raw_scores else 0.0,
        "coreMean": round(sum(core_scores) / len(core_scores), 4) if core_scores else 0.0,
        "topics": topic_counter.most_common(10),
    }


def main() -> None:
    print(evaluate_alignment())


if __name__ == "__main__":
    main()
