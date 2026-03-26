"""
실험 ID: 074-011
실험명: manual hard-case gold set 평가

목적:
- weak label이 아닌 사람이 재판정한 disagreement case에서 모델이 실제로 나아지는지 본다.
- `prior`, `current baseline`, `feature_only`, `topic_plus`를 같은 hard set에서 비교한다.

가설:
1. hard case에서는 topic prior가 크게 무너진다.
2. current baseline도 retry/history/raw 경계에서 자주 틀린다.
3. topic+feature 학습 모델은 hard case에서 prior/baseline보다 높아질 수 있다.

방법:
1. 005와 topic prior가 충돌한 사례 중 19개를 수작업으로 판정한다.
2. 각 케이스에 대해 prior, baseline, 학습 모델 2종을 평가한다.
3. 정확도와 예측 분포를 비교한다.

결과 (실험 후 작성):
- 수동 hard-case gold set `19개`를 평가했다.
- accuracy:
  - `topic_prior 0.6842`
  - `baseline 0.1579`
  - `scorer 0.4211`
  - `feature_only 0.5789`
  - `topic_plus 0.6842`
- `topic_plus`는 hard set에서도 topic prior와 완전히 동일한 예측을 냈다.
- `feature_only`는 `horizontalize 14`, `raw_fallback 3`, `history_skip 2`를 예측해 baseline/scorer보다는 낫지만 topic prior는 넘지 못했다.
- 실행 시간: 약 `426.9초`

결론:
- 약지도 학습만으로는 topic prior를 넘어서는 판단층이 생기지 않았다.
- 현행 baseline은 hard case에서 거의 무너졌고, 현재 scorer도 일부 개선은 있지만 충분히 강하지 않다.
- 이번 hard set 기준 최선은 여전히 `topic prior`, 즉 "더 많은 weak label"보다 "더 좋은 gold label"이 먼저다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

from dartlab.providers.dart._table_horizontalizer import horizontalizeTableBlock

ROOT = Path(__file__).resolve().parent

HARD_CASES = [
    ("000100", "audit", 3, "horizontalize"),
    ("000100", "audit", 5, "retry_alt_header"),
    ("005930", "audit", 4, "retry_alt_header"),
    ("000100", "boardOfDirectors", 6, "history_skip"),
    ("000100", "boardOfDirectors", 15, "history_skip"),
    ("000100", "boardOfDirectors", 12, "history_skip"),
    ("000100", "companyHistory", 10, "history_skip"),
    ("000100", "companyHistory", 5, "history_skip"),
    ("000100", "companyOverview", 37, "history_skip"),
    ("000100", "companyOverview", 55, "horizontalize"),
    ("000100", "consolidatedNotes", 25, "raw_fallback"),
    ("000100", "fsSummary", 28, "raw_fallback"),
    ("000100", "fsSummary", 101, "raw_fallback"),
    ("000100", "fsSummary", 17, "horizontalize"),
    ("000100", "majorHolder", 9, "list_skip"),
    ("000100", "rawMaterial", 2, "horizontalize"),
    ("000100", "rawMaterial", 28, "raw_fallback"),
    ("051910", "riskDerivative", 9, "horizontalize"),
    ("000100", "salesOrder", 2, "horizontalize"),
]


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
_baseline = load_script("005_baselineReplay")
_scorer = load_script("006_understandingScorer")
_train = load_script("010_perceptronLearner")


def load_hard_rows() -> list[dict[str, object]]:
    rows_by_key = {
        (str(row["stockCode"]), str(row["topic"]), int(row["blockOrder"])): row for row in _seed.collect_sample_topic_rows()
    }
    hard_rows = []
    for stock_code, topic, block_order, gold in HARD_CASES:
        row = dict(rows_by_key[(stock_code, topic, block_order)])
        row["manualGoldAction"] = gold
        hard_rows.append(row)
    return hard_rows


def evaluate_hard_set() -> dict[str, object]:
    training = _train.train_models()
    topic_prior_map = training["topicPriorMap"]
    global_fallback = str(training["globalFallback"])
    feature_model = training["featureModel"]
    topic_model = training["topicModel"]
    rows = load_hard_rows()
    summary: dict[str, dict[str, object]] = {}

    def prior_predict(row: dict[str, object]) -> str:
        return _train.predict_topic_prior(row, topic_prior_map, global_fallback)

    def baseline_predict(row: dict[str, object]) -> str:
        frame = _seed.topic_frame(str(row["stockCode"]), str(row["topic"]))
        if frame is None:
            return _baseline.classify_none(row)
        period_cols = _seed.period_columns(frame)
        result = horizontalizeTableBlock(frame, int(row["blockOrder"]), period_cols, None)
        return "horizontalize" if result is not None else _baseline.classify_none(row)

    def feature_predict(row: dict[str, object]) -> str:
        return feature_model.predict(_train.extract_features(row, include_topic=False))

    def topic_plus_predict(row: dict[str, object]) -> str:
        return topic_model.predict(_train.extract_features(row, include_topic=True))

    def scorer_predict(row: dict[str, object]) -> str:
        return str(_scorer.score_entry(row)["predictedAction"])

    predictors = {
        "topic_prior": prior_predict,
        "baseline": baseline_predict,
        "scorer": scorer_predict,
        "feature_only": feature_predict,
        "topic_plus": topic_plus_predict,
    }
    for name, predictor in predictors.items():
        correct = 0
        preds: Counter[str] = Counter()
        for row in rows:
            pred = predictor(row)
            preds[pred] += 1
            if pred == row["manualGoldAction"]:
                correct += 1
        summary[name] = {
            "accuracy": round(correct / len(rows), 4),
            "predictions": preds.most_common(),
        }
    return {"count": len(rows), **summary}


def main() -> None:
    print(evaluate_hard_set())


if __name__ == "__main__":
    main()
