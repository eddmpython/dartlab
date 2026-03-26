# EDGAR 매핑 학습 워크플로우

## 학습 사이클

```
[측정] → [분석] → [학습] → [검증] → [반복]

1. 측정: experiments/001_mappingQuality.py
   - 태그 매핑률, 핵심 계정 커버리지, 시계열 gap 측정
   - 종목간 비교 가능성 확인

2. 분석: experiments/002_frequencyLearning.py
   - 전체 CIK에서 미매핑 태그 빈도 수집
   - 패턴 분류 (Notes/핵심/오매핑)

3. 학습: mapperData/learnedSynonyms.json 수정
   - 오매핑 수정 (P0)
   - 신규 태그 추가 (autoClassify 기반)
   - 수동 검토 후 승인

4. 검증: 001 재실행으로 개선 확인

5. 반복: 매핑률이 목표(95%+)에 도달할 때까지
```

## 학습 메커니즘 (DART에서 차용)

### 태그 빈도 기반 정규화 (핵심 원리)
```
많이 쓰이는 태그 = 정답일 가능성 높음

1. 전체 CIK에서 태그 출현 빈도 집계
2. 빈도 높은 미매핑 태그 우선 처리
3. 이미 매핑된 유사 태그와 대조하여 snakeId 결정
4. 역방향: 매핑된 snakeId → 같은 의미 다른 태그 자동 수집
```

### autoClassify (키워드 기반 자동 분류)
```python
scripts/batchLearner.py의 autoClassify() 함수:
- 100+ 키워드 규칙으로 XBRL 태그 자동 분류
- 예: 'deferredtax' + 'asset' → deferred_tax_assets
- 예: 'derivative' + 'liabilit' → derivative_liabilities_detail
- 기본값: other_note_detail
```

### rapidfuzz 유사도 (수동 검토 보조)
```python
v1/synonymLearner.py의 suggestMapping():
- tag → camelCase 분리 → 정규화 → 표준계정 engName과 유사도 비교
- token_set_ratio로 순서 무관 매칭
- 상위 5개 후보 제안 → 수동 검토
```

## 현재 데이터 규모

| 항목 | 값 | 출처 |
|------|-----|------|
| 표준계정 | 179개 (344 commonTags) | mapperData/standardAccounts.json |
| 학습 태그 | 11,375개 | mapperData/learnedSynonyms.json |
| 학습 종목 | 8,158/10,301 (79.2%) | _reference/learnedTickers.json |
| 태그 매핑률 | 92.8% (10사 대형주) | experiments/001 |
| 핵심 계정 | 89% (21개 중 평균) | experiments/001 |

## 학습 이력

eddmpython에서 51차에 걸쳐 학습:
- 초기 6개 종목 660태그 → 최종 8,158개 종목 11,375태그
- 상세: SYNONYM_LEARNING_SUMMARY.md

## 오매핑 수정 절차

1. mapperData/learnedSynonyms.json 열기
2. tagMappings에서 잘못된 매핑 찾기
3. 올바른 snakeId로 수정
4. 001 실험 재실행하여 검증

예시: NoncurrentAssets 수정
```json
// 수정 전
"noncurrentassets": "other_noncurrent_assets"
// 수정 후
"noncurrentassets": "non_current_assets"
```

## 신규 태그 학습 절차

1. 002 실험으로 미매핑 태그 빈도 확인
2. suggestSnakeId() 또는 autoClassify()로 후보 결정
3. mapperData/learnedSynonyms.json의 tagMappings에 추가
4. 001 실험 재실행하여 매핑률 개선 확인

## 다음 작업

### 즉시 (P0)
- [ ] NoncurrentAssets → non_current_assets 수정
- [ ] 오매핑 전수 점검 (핵심 계정 중심)

### 단기 (P1)
- [ ] gross_profit 자체 계산 (pivot.py에서 revenue - cost_of_sales)
- [ ] non_current_assets 자체 계산 (total_assets - current_assets)

### 중기 (P2)
- [ ] 280개 1%+ 출현 미매핑 태그 autoClassify 확장
- [ ] DART↔EDGAR snakeId 교차 비교 실험
