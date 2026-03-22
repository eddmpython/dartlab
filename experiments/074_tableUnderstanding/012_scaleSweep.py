"""
실험 ID: 074-012
실험명: 학습 데이터 규모별 hard-case 효과

목적:
- 더 많은 weak-label row가 hard case 성능에 실제로 도움이 되는지 본다.
- "데이터가 떡하니 있는데 학습시키면 되는가"를 규모 효과로 확인한다.

가설:
1. feature_only보다 topic_plus 모델이 데이터 증가 효과를 더 잘 먹는다.
2. hard-case accuracy는 작은 train split보다 큰 split에서 좋아진다.
3. 규모 효과가 보이면 weak supervision 확대 실험의 가치가 생긴다.

방법:
1. 009 train stock을 고정 순서로 정렬한다.
2. 앞에서부터 `4`, `8`, `12`, `14`개 stock만 써서 topic_plus perceptron을 다시 학습한다.
3. 011 hard set 정확도를 비교한다.

결과 (실험 후 작성):
- hard-case 19개 기준 규모별 accuracy:
  - `4개 stock / 3,021행`: topic_prior `0.6842`, feature_only `0.4211`, topic_plus `0.6842`
  - `8개 stock / 6,064행`: topic_prior `0.6842`, feature_only `0.3158`, topic_plus `0.6842`
  - `12개 stock / 9,453행`: topic_prior `0.6842`, feature_only `0.3684`, topic_plus `0.6842`
  - `14개 stock / 11,565행`: topic_prior `0.6842`, feature_only `0.5789`, topic_plus `0.6842`
- topic_plus는 데이터가 늘어나도 한 번도 topic prior를 넘지 못했다.
- feature_only는 규모 효과가 단조롭지 않았고, full train에서만 `0.5789`까지 회복했다.
- 실행 시간: 약 `264.7초`

결론:
- 단순 weak supervision 확대만으로 hard-case 판단이 좋아지지는 않았다.
- 데이터 규모보다 라벨 품질이 더 큰 병목이라는 결론이 강화됐다.
- 다음 단계는 weak label 증설이 아니라 `retry/raw/history` 경계 중심 manual gold set 확대다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
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


_dataset = load_script("009_learningDataset")
_train = load_script("010_perceptronLearner")
_hard = load_script("011_manualHardSet")


def scale_sweep() -> dict[str, object]:
    rows = _dataset.build_learning_rows()
    train_rows = [row for row in rows if row["split"] == "train"]
    train_stocks = sorted({str(row["stockCode"]) for row in train_rows})
    hard_rows = _hard.load_hard_rows()
    points = []
    for stock_count in [4, 8, 12, len(train_stocks)]:
        chosen = set(train_stocks[:stock_count])
        subset = [row for row in train_rows if str(row["stockCode"]) in chosen]
        topic_prior_map, global_fallback = _train.build_topic_prior(subset)
        feature_model = _train.MulticlassPerceptron(_train.ACTIONS, epochs=6)
        feature_model.fit(subset, include_topic=False)
        topic_model = _train.MulticlassPerceptron(_train.ACTIONS, epochs=6)
        topic_model.fit(subset, include_topic=True)
        prior_correct = feature_correct = topic_correct = 0
        prior_preds: Counter[str] = Counter()
        feature_preds: Counter[str] = Counter()
        topic_preds: Counter[str] = Counter()
        for row in hard_rows:
            prior_pred = _train.predict_topic_prior(row, topic_prior_map, global_fallback)
            feature_pred = feature_model.predict(_train.extract_features(row, include_topic=False))
            topic_pred = topic_model.predict(_train.extract_features(row, include_topic=True))
            prior_preds[prior_pred] += 1
            feature_preds[feature_pred] += 1
            topic_preds[topic_pred] += 1
            if prior_pred == row["manualGoldAction"]:
                prior_correct += 1
            if feature_pred == row["manualGoldAction"]:
                feature_correct += 1
            if topic_pred == row["manualGoldAction"]:
                topic_correct += 1
        points.append(
            {
                "stockCount": stock_count,
                "rowCount": len(subset),
                "topicPriorAccuracy": round(prior_correct / len(hard_rows), 4),
                "featureOnlyAccuracy": round(feature_correct / len(hard_rows), 4),
                "topicPlusAccuracy": round(topic_correct / len(hard_rows), 4),
                "topicPriorPredictions": prior_preds.most_common(),
                "featureOnlyPredictions": feature_preds.most_common(),
                "topicPlusPredictions": topic_preds.most_common(),
            }
        )
    return {"points": points}


def main() -> None:
    print(scale_sweep())


if __name__ == "__main__":
    main()
