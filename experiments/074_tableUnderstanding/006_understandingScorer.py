"""
실험 ID: 074-006
실험명: sections-aware understanding scorer

목적:
- topic prior와 TableIR/bundle 피처를 결합한 경량 scorer로 action을 예측한다.
- baseline보다 seed set action 분류를 더 잘하는지 확인한다.

가설:
1. topic prior + bundle drift + row core overlap만으로도 baseline보다 세부 action 분류가 좋아진다.
2. multi_year/numeric-heavy 표는 horizontalize 점수가 안정적으로 높다.
3. note/list/history 표는 aggressive horizontalize를 피할 수 있다.

방법:
1. 002/003/004의 seed, TableIR, bundle 요약을 불러온다.
2. action별 점수를 계산하고 최고점 action을 택한다.
3. baseline과 같은 지표로 비교한다.

결과 (실험 후 작성):
- seed set `60개` 기준 exact action accuracy `0.7333`
- horizontalize precision `0.6154`, recall `1.0000`, F1 `0.7619`
- prediction 분포: `horizontalize 39`, `list_skip 7`, `raw_fallback 7`, `history_skip 5`, `retry_alt_header 2`
- baseline 대비 exact accuracy `+0.3666p`, horizontalize F1 `+0.2262`
- 실행 시간: 약 `255.9초`

결론:
- topic prior + TableIR + bundle drift만 결합해도 baseline보다 훨씬 낫다.
- 다만 scorer는 아직 `retry_alt_header`를 과소예측하고 `horizontalize`를 다소 과다예측한다.
- 즉 1차 결론은 "경량 understanding scorer는 유효하다. 하지만 retry/raw 경계는 더 세밀한 피처가 필요하다"다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

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
_bundle = load_script("004_temporalBundle")
ACTION_ORDER = ["horizontalize", "retry_alt_header", "list_skip", "history_skip", "raw_fallback"]


@lru_cache(maxsize=1)
def bundle_lookup() -> dict[tuple[str, str, int], dict[str, object]]:
    lookup: dict[tuple[str, str, int], dict[str, object]] = {}
    for bundle in _bundle.build_temporal_bundles():
        for block_order in bundle["blockOrders"]:
            lookup[(str(bundle["stockCode"]), str(bundle["topic"]), int(block_order))] = bundle
    return lookup


def score_entry(entry: dict[str, object]) -> dict[str, object]:
    ir = _ir.build_table_ir(entry)
    bundle = bundle_lookup().get((str(entry["stockCode"]), str(entry["topic"]), int(entry["blockOrder"])))
    scores = defaultdict(float)
    topic = str(entry["topic"])
    approx_row_count = int(entry["approxRowCount"])
    numeric_ratio = float(entry["numericRatio"])
    mean_overlap = float(bundle["meanRowCoreJaccard"]) if bundle else 0.0

    if topic in {"dividend", "rawMaterial", "salesOrder", "shareCapital", "majorHolder", "riskDerivative"}:
        scores["horizontalize"] += 0.55
    if topic in {"audit", "executivePay"}:
        scores["retry_alt_header"] += 0.45
    if topic in {"employee", "companyOverview"}:
        scores["list_skip"] += 0.45
    if topic in {"boardOfDirectors", "companyHistory"}:
        scores["history_skip"] += 0.45
    if topic in {"financialNotes", "consolidatedNotes", "fsSummary"}:
        scores["raw_fallback"] += 0.55

    if ir.structureType == "multi_year":
        scores["horizontalize"] += 0.3
    if ir.structureType in {"key_value", "matrix"}:
        scores["horizontalize"] += 0.1
        scores["retry_alt_header"] += 0.05
    if numeric_ratio >= 0.45:
        scores["horizontalize"] += 0.2
    if mean_overlap >= 0.35:
        scores["horizontalize"] += 0.2
    if approx_row_count >= 30:
        scores["list_skip"] += 0.3
    if approx_row_count >= 50:
        scores["list_skip"] += 0.2
    if mean_overlap <= 0.15 and approx_row_count >= 6:
        scores["history_skip"] += 0.25
    if bundle and "header_drift" in bundle["driftFlags"]:
        scores["retry_alt_header"] += 0.2
    if bundle and "block_drift" in bundle["driftFlags"]:
        scores["horizontalize"] += 0.1
    if ir.emptyRatio >= 0.4:
        scores["raw_fallback"] += 0.15
    if not any(scores.values()):
        scores["raw_fallback"] += 0.1

    ordered = sorted(((action, scores[action]) for action in ACTION_ORDER), key=lambda item: item[1], reverse=True)
    best, second = ordered[0], ordered[1]
    confidence = round(best[1] - second[1], 4)
    canonical_rows = []
    seen: set[str] = set()
    for value in ir.rowCore:
        if value and value not in seen:
            canonical_rows.append(value)
            seen.add(value)
        if len(canonical_rows) >= 10:
            break
    return {
        "predictedAction": best[0],
        "confidence": confidence,
        "scores": {action: round(scores[action], 4) for action in ACTION_ORDER},
        "canonicalRows": canonical_rows,
        "canonicalHeaders": [ir.headerSignature],
        "driftFlags": bundle["driftFlags"] if bundle else [],
    }


def evaluate_scorer() -> dict[str, object]:
    seed = _seed.build_seed_gold_set()
    exact = 0
    horiz_tp = horiz_fp = horiz_fn = 0
    predictions: Counter[str] = Counter()
    for entry in seed:
        predicted = score_entry(entry)["predictedAction"]
        gold = str(entry["goldAction"])
        predictions[predicted] += 1
        if predicted == gold:
            exact += 1
        if predicted == "horizontalize" and gold == "horizontalize":
            horiz_tp += 1
        elif predicted == "horizontalize" and gold != "horizontalize":
            horiz_fp += 1
        elif predicted != "horizontalize" and gold == "horizontalize":
            horiz_fn += 1
    precision = horiz_tp / (horiz_tp + horiz_fp) if horiz_tp + horiz_fp else 0.0
    recall = horiz_tp / (horiz_tp + horiz_fn) if horiz_tp + horiz_fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "count": len(seed),
        "exactActionAccuracy": round(exact / len(seed), 4) if seed else 0.0,
        "horizontalizePrecision": round(precision, 4),
        "horizontalizeRecall": round(recall, 4),
        "horizontalizeF1": round(f1, 4),
        "predictions": predictions.most_common(),
    }


def main() -> None:
    print(evaluate_scorer())


if __name__ == "__main__":
    main()
