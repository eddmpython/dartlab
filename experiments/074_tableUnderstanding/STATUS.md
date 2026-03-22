# 074_tableUnderstanding — sections-aware markdown table understanding

## 목표

- `sections` 안에 이미 들어온 markdown table을 기간축에서 더 잘 이해한다.
- 핵심 질문은 "표를 뽑아냈는가"가 아니라 "해마다 변하는 같은 논리 표를 얼마나 잘 묶고 판단하는가"다.
- 이번 라운드는 프로덕션 흡수 전 실험이다. 결과는 각 실험 파일 docstring과 이 문서에 기록한다.

## 진행 상황

| # | 실험 | 상태 | 핵심 결과 |
|---|------|------|----------|
| 001 | corpusSnapshot | ✅ 완료 | raw corpus: DART 319, EDGAR 974. DART sample 18개 sections에서 table rows 22,312, topic 51개 |
| 002 | seedGoldSet | ✅ 완료 | seed set 60개. action 분포: horizontalize 24 / raw 12 / retry 8 / history 8 / list 8 |
| 003 | tableIR | ✅ 완료 | TableIR 60개. structure: matrix 37, multi_year 10, key_value 7, skip 6 |
| 004 | temporalBundle | ✅ 완료 | bundle 5,662개. block_drift 2,369, header_drift 720, unit_drift 706 |
| 005 | baselineReplay | ✅ 완료 | exact action accuracy 0.3667, horizontalize F1 0.5357 |
| 006 | understandingScorer | ✅ 완료 | exact action accuracy 0.7333, horizontalize F1 0.7619 |
| 007 | alignmentEval | ✅ 완료 | row core normalization 평균 개선폭 +0.0073로 작음. 병목은 alignment보다 action layer |
| 008 | edgarTransfer | ✅ 완료 | EDGAR sample 48개에 scorer 적용. list 16 / horizontalize 15 / raw 12 / history 5 |
| 009 | learningDataset | ✅ 완료 | weak-label row 15,207개. train 11,565 / test 3,642. raw_fallback 쏠림 큼 |
| 010 | perceptronLearner | ✅ 완료 | weak-label holdout에서 topic prior 1.0000, topic+feature 1.0000, feature-only 0.1480 |
| 011 | manualHardSet | ✅ 완료 | hard-case 19개에서 topic prior 0.6842, feature-only 0.5789, scorer 0.4211, baseline 0.1579 |
| 012 | scaleSweep | ✅ 완료 | 데이터 규모를 늘려도 topic+feature는 0.6842에서 정체. weak-label 증설만으로는 개선 없음 |

## 메모

- 결과 placeholder를 남기지 않기 위해 각 파일을 같은 턴에서 최소 1회 실행하고 바로 갱신했다.
- 별도 결과 artifact 파일은 만들지 않았다. 결과는 docstring과 이 문서만 source of truth로 둔다.

## 핵심 판단

- **핵심 질문의 답**: 현재 bottleneck은 "raw markdown을 못 읽어서"가 아니라 "해마다 변하는 같은 논리 표를 어떻게 action 단위로 이해할 것인가"다.
- baseline은 단순 수평화 여부에는 쓸 만하지만, `retry_alt_header`, `history_skip`, `raw_fallback` 같은 이해 레이어를 충분히 설명하지 못했다.
- 경량 scorer는 seed set 기준으로 baseline보다 분명히 좋아졌다.
  - exact action accuracy: `0.3667 -> 0.7333`
  - horizontalize F1: `0.5357 -> 0.7619`
- 반면 row-core alignment 개선폭은 작았다. 이번 라운드의 진짜 승부처는 alignment보다 `action decision + bundle context`다.
- EDGAR 전이는 부분적으로 가능했다. 완전 공통 엔진이라기보다, DART에서 만든 구조 피처가 EDGAR에도 어느 정도 통하는 수준이다.
- 학습 실험까지 확장해 보니, **weak label만 많이 먹인다고 해결되지는 않았다.**
  - weak-label holdout은 topic prior 정의를 그대로 복제해 `topic_prior = topic_plus = 1.0000`으로 포화됐다.
  - manual hard-case 19개에서는 `topic_prior 0.6842 > feature_only 0.5789 > scorer 0.4211 > baseline 0.1579`
  - 즉 지금 필요한 건 모델 크기나 데이터 양보다 `manual gold label` 품질 개선이다.
