"""
실험 ID: 074-010
실험명: 약지도 기반 multiclass perceptron 학습

목적:
- sections-aware row feature로 action classifier를 실제 학습시킨다.
- topic prior만 외우는 모델과 feature-only 모델, topic+feature 모델을 비교한다.

가설:
1. weak-label holdout에서는 topic prior가 가장 강하지만, feature-only 모델도 일정 수준까지 따라온다.
2. topic+feature 모델은 weak-label holdout에서 prior에 근접하면서 hard case 대응 잠재력이 더 크다.
3. perceptron 정도의 경량 모델로도 CPU에서 실험이 가능하다.

방법:
1. 009 데이터셋에서 train/test split을 불러온다.
2. sparse binary feature를 만들고 multiclass perceptron을 학습한다.
3. `prior`, `feature_only`, `topic_plus` 세 모델을 holdout weak label에서 비교한다.

결과 (실험 후 작성):
- holdout weak-label 기준 `topic_prior accuracy 1.0000`
- `feature_only accuracy 0.1480`
- `topic_plus accuracy 1.0000`
- `feature_only` prediction은 `horizontalize 3,251`로 크게 쏠렸고, `topic_plus` prediction은 topic prior와 완전히 동일했다.
- 실행 시간: 약 `131.4초`

결론:
- weak-label 자체가 topic prior로 정의돼 있어 holdout 평가는 사실상 포화됐다.
- `topic_plus`가 `1.0`인 것은 모델이 잘 배워서라기보다, 약지도 정의를 그대로 복제한 결과다.
- 따라서 "데이터가 많으니 학습시키면 된다"는 주장은 이 좌표계만으로는 검증되지 않는다. 진짜 판단은 manual hard set이 필요하다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ACTIONS = ["horizontalize", "raw_fallback", "history_skip", "list_skip", "retry_alt_header"]


def load_script(stem: str):
    path = ROOT / f"{stem}.py"
    module_name = f"_exp074_{stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_dataset = load_script("009_learningDataset")


def bucket_numeric(value: float, boundaries: list[float]) -> str:
    for boundary in boundaries:
        if value <= boundary:
            return str(boundary)
    return f">{boundaries[-1]}"


def extract_features(row: dict[str, object], *, include_topic: bool) -> dict[str, float]:
    md = str(row["latestMarkdown"])
    topic = str(row["topic"])
    struct = str(row["dominantStruct"])
    period_count = int(row["periodCount"])
    row_count = int(row["approxRowCount"])
    numeric_ratio = float(row["numericRatio"])
    features: dict[str, float] = {
        f"struct={struct}": 1.0,
        f"period_bin={bucket_numeric(period_count, [5, 10, 20, 40, 80])}": 1.0,
        f"row_bin={bucket_numeric(row_count, [3, 8, 15, 30, 60, 120])}": 1.0,
        f"num_ratio={bucket_numeric(numeric_ratio, [0.05, 0.2, 0.4, 0.6, 0.8])}": 1.0,
        f"line_bin={bucket_numeric(float(len(md.splitlines())), [5, 10, 20, 40, 80, 160])}": 1.0,
        f"char_bin={bucket_numeric(float(len(md)), [200, 500, 1000, 3000, 8000, 20000])}": 1.0,
        f"has_unit={int('단위' in md)}": 1.0,
        f"has_kisu={int(any(token in md for token in ['당기', '전기', '전전기', '당분기', '전분기']))}": 1.0,
        f"has_date={int(bool(re.search(r'\\d{4}[.년]', md)))}": 1.0,
        f"has_person={int(any(token in md for token in ['성명', '이사', '대표자', '참석률']))}": 1.0,
        f"has_balance_move={int(any(token in md for token in ['기초', '기말', '취득', '처분', '증가', '감소']))}": 1.0,
        f"has_entity={int(any(token in md for token in ['법인명', '회사명', '계약처', '거래처']))}": 1.0,
        f"has_history={int(any(token in md for token in ['개최일자', '일자', '변동일자', '연혁']))}": 1.0,
    }
    if include_topic:
        features[f"topic={topic}"] = 1.0
    return features


class MulticlassPerceptron:
    def __init__(self, classes: list[str], epochs: int = 6) -> None:
        self.classes = classes
        self.epochs = epochs
        self.weights: dict[str, dict[str, float]] = {klass: defaultdict(float) for klass in classes}

    def predict(self, features: dict[str, float]) -> str:
        best_class = self.classes[0]
        best_score = -math.inf
        for klass in self.classes:
            score = 0.0
            weights = self.weights[klass]
            for key, value in features.items():
                score += weights.get(key, 0.0) * value
            if score > best_score:
                best_score = score
                best_class = klass
        return best_class

    def fit(self, rows: list[dict[str, object]], *, include_topic: bool) -> None:
        ordered = sorted(rows, key=lambda row: (str(row["stockCode"]), str(row["topic"]), int(row["blockOrder"])))
        for _ in range(self.epochs):
            for row in ordered:
                gold = str(row["goldAction"])
                features = extract_features(row, include_topic=include_topic)
                pred = self.predict(features)
                if pred == gold:
                    continue
                for key, value in features.items():
                    self.weights[gold][key] += value
                    self.weights[pred][key] -= value


def evaluate_model(rows: list[dict[str, object]], predictor) -> dict[str, object]:
    correct = 0
    predictions: Counter[str] = Counter()
    for row in rows:
        pred = predictor(row)
        predictions[pred] += 1
        if pred == row["goldAction"]:
            correct += 1
    return {
        "accuracy": round(correct / len(rows), 4) if rows else 0.0,
        "predictions": predictions.most_common(),
    }


def build_topic_prior(train_rows: list[dict[str, object]]) -> tuple[dict[str, str], str]:
    per_topic: dict[str, Counter[str]] = defaultdict(Counter)
    overall: Counter[str] = Counter()
    for row in train_rows:
        topic = str(row["topic"])
        action = str(row["goldAction"])
        per_topic[topic][action] += 1
        overall[action] += 1
    topic_map = {topic: counts.most_common(1)[0][0] for topic, counts in per_topic.items()}
    global_fallback = overall.most_common(1)[0][0] if overall else ACTIONS[0]
    return topic_map, global_fallback


def predict_topic_prior(row: dict[str, object], topic_map: dict[str, str], global_fallback: str) -> str:
    return topic_map.get(str(row["topic"]), global_fallback)


def train_models() -> dict[str, object]:
    rows = _dataset.build_learning_rows()
    train_rows = [row for row in rows if row["split"] == "train"]
    test_rows = [row for row in rows if row["split"] == "test"]
    topic_prior, global_fallback = build_topic_prior(train_rows)

    feature_only = MulticlassPerceptron(ACTIONS, epochs=6)
    feature_only.fit(train_rows, include_topic=False)

    topic_plus = MulticlassPerceptron(ACTIONS, epochs=6)
    topic_plus.fit(train_rows, include_topic=True)

    return {
        "trainRows": len(train_rows),
        "testRows": len(test_rows),
        "topicPrior": evaluate_model(test_rows, lambda row: predict_topic_prior(row, topic_prior, global_fallback)),
        "feature_only": evaluate_model(test_rows, lambda row: feature_only.predict(extract_features(row, include_topic=False))),
        "topic_plus": evaluate_model(test_rows, lambda row: topic_plus.predict(extract_features(row, include_topic=True))),
        "topicPriorMap": topic_prior,
        "globalFallback": global_fallback,
        "featureModel": feature_only,
        "topicModel": topic_plus,
    }


def summarize_training() -> dict[str, object]:
    result = train_models()
    return {
        "trainRows": result["trainRows"],
        "testRows": result["testRows"],
        "topicPriorAccuracy": result["topicPrior"]["accuracy"],
        "featureOnlyAccuracy": result["feature_only"]["accuracy"],
        "topicPlusAccuracy": result["topic_plus"]["accuracy"],
        "topicPriorPredictions": result["topicPrior"]["predictions"],
        "featureOnlyPredictions": result["feature_only"]["predictions"],
        "topicPlusPredictions": result["topic_plus"]["predictions"],
    }


def main() -> None:
    print(summarize_training())


if __name__ == "__main__":
    main()
