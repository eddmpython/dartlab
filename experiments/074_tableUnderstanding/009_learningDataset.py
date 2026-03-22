"""
실험 ID: 074-009
실험명: sections-aware weak-label learning dataset

목적:
- sample topic rows 전체를 약지도 학습 데이터셋으로 재구성한다.
- 학습/평가 split을 stock 기준으로 고정해 이후 모델 실험이 같은 데이터 분할을 쓰게 한다.

가설:
1. 18개 sample company만으로도 1만 건 이상 table-action 약지도 데이터셋을 만들 수 있다.
2. stock-holdout split을 써도 각 action 클래스가 train/test에 모두 남는다.
3. hard case에 쓰이는 종목을 holdout으로 빼면 learning 실험이 더 설득력 있다.

방법:
1. 002의 `collect_sample_topic_rows()` 전체를 읽는다.
2. holdout stock을 `{000100, 005930, 051910, 000150}`로 고정한다.
3. row 단위로 split과 action 분포를 집계한다.

결과 (실험 후 작성):
- weak-label dataset 총 `15,207행`을 만들었다.
- split: train `11,565행` (`14개 stock`), test `3,642행` (`4개 stock`)
- train action 분포: `raw_fallback 8,130`, `list_skip 1,225`, `history_skip 919`, `horizontalize 805`, `retry_alt_header 486`
- test action 분포: `raw_fallback 2,734`, `list_skip 347`, `history_skip 229`, `horizontalize 210`, `retry_alt_header 122`
- topic 상위: `fsSummary 5,447`, `financialNotes 3,102`, `consolidatedNotes 2,315`, `boardOfDirectors 926`
- 실행 시간: 약 `131.8초`

결론:
- 18개 sample company만으로도 row 단위 약지도 학습 데이터는 충분히 만들 수 있다.
- 다만 클래스 분포가 `raw_fallback` 쪽으로 매우 치우쳐 있어 단순 정확도만 보면 착시가 생길 수 있다.
- 이후 학습 평가는 반드시 weak-label holdout과 manual hard set을 분리해서 봐야 한다.

실험일: 2026-03-20
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOLDOUT_STOCKS = {"000100", "005930", "051910", "000150"}


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


def build_learning_rows() -> list[dict[str, object]]:
    rows = []
    for row in _seed.collect_sample_topic_rows():
        copied = dict(row)
        copied["split"] = "test" if str(row["stockCode"]) in HOLDOUT_STOCKS else "train"
        rows.append(copied)
    return rows


def summarize_dataset() -> dict[str, object]:
    rows = build_learning_rows()
    train = [row for row in rows if row["split"] == "train"]
    test = [row for row in rows if row["split"] == "test"]
    return {
        "totalRows": len(rows),
        "trainRows": len(train),
        "testRows": len(test),
        "trainStocks": sorted({str(row["stockCode"]) for row in train}),
        "testStocks": sorted({str(row["stockCode"]) for row in test}),
        "actionsTrain": Counter(str(row["goldAction"]) for row in train).most_common(),
        "actionsTest": Counter(str(row["goldAction"]) for row in test).most_common(),
        "topicsTop": Counter(str(row["topic"]) for row in rows).most_common(12),
    }


def main() -> None:
    print(summarize_dataset())


if __name__ == "__main__":
    main()
