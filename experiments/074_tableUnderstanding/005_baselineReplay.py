"""
실험 ID: 074-005
실험명: 현재 DART horizontalizer baseline 재현

목적:
- 현행 `_table_horizontalizer`가 seed set에서 어떤 판단을 하는지 같은 좌표계로 재현한다.
- scorer와 비교하기 위한 baseline accuracy와 horizontalize recall을 고정한다.

가설:
1. 현행 baseline은 horizontalize 여부 판정에서는 강하지만, non-horizontalize 세부 action 분류는 약하다.
2. audit/executivePay는 `retry_alt_header` 계열로 더 세분화해야 한다.
3. list/history/raw_fallback 분리는 baseline 단독으로는 충분히 설명되지 않는다.

방법:
1. 002의 seed gold set을 불러온다.
2. 각 seed entry에 대해 현재 `horizontalizeTableBlock()`를 실제 실행한다.
3. 성공/실패를 goldAction과 비교하고, 실패는 단순 heuristic action으로 재분류한다.

결과 (실험 후 작성):
- seed set `60개` 기준 exact action accuracy `0.3667`
- horizontalize precision `0.4688`, recall `0.6250`, F1 `0.5357`
- prediction 분포: `horizontalize 32`, `list_skip 17`, `raw_fallback 7`, `history_skip 3`, `retry_alt_header 1`
- goldAction 분포 대비 baseline은 `retry_alt_header`, `history_skip`를 거의 설명하지 못했다.
- 실행 시간: 약 `187.1초`

결론:
- 현행 baseline은 "수평화할 수 있으면 한다"는 축에서는 쓸 만하지만, action taxonomy까지 보면 많이 거칠다.
- 특히 `audit`, `executivePay` 같은 header 변형형과 history/list/raw 경계가 약하다.
- 이 실험의 baseline은 충분히 약한 기준점이고, understanding layer 추가 여지가 분명하다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

from dartlab.providers.dart._table_horizontalizer import horizontalizeTableBlock

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


def classify_none(entry: dict[str, object]) -> str:
    topic = str(entry["topic"])
    approx_row_count = int(entry["approxRowCount"])
    if topic in {"employee", "companyOverview"} or approx_row_count >= 25:
        return "list_skip"
    if topic in {"boardOfDirectors", "companyHistory"}:
        return "history_skip"
    if topic in {"audit", "executivePay"}:
        return "retry_alt_header"
    return "raw_fallback"


def evaluate_baseline() -> dict[str, object]:
    seed = _seed.build_seed_gold_set()
    exact = 0
    horiz_tp = horiz_fp = horiz_fn = 0
    predictions: Counter[str] = Counter()
    for entry in seed:
        frame = _seed.topic_frame(str(entry["stockCode"]), str(entry["topic"]))
        if frame is None:
            predicted = classify_none(entry)
        else:
            period_cols = _seed.period_columns(frame)
            result = horizontalizeTableBlock(frame, int(entry["blockOrder"]), period_cols, None)
            predicted = "horizontalize" if result is not None else classify_none(entry)
        predictions[predicted] += 1
        gold = str(entry["goldAction"])
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
        "goldActions": Counter(str(entry["goldAction"]) for entry in seed).most_common(),
    }


def main() -> None:
    print(evaluate_baseline())


if __name__ == "__main__":
    main()
