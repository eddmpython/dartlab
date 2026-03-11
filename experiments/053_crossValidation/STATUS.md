# 053. 교차검증 (docs vs finance vs report)

## 실험 현황

| # | 실험명 | 상태 | 핵심 결과 |
|---|--------|------|----------|
| 001 | docs vs finance 초기 비교 | 완료 | 연도 시차+단위 미보정 → 일치율 0.4% |
| 002 | 삼성전자 심층 비교 | 완료 | docs year N = finance year N-1, 단위 ×1M 발견 |
| 003 | 연도-1 + 단위 보정 비교 | 완료 | **일치율 80.9%**, BS 95%, IS 82% |

## 핵심 발견

### 1. docs fsSummary 특성
- **연도 시차**: docs year N의 값(idx=0) = finance year N-1의 실제 값
  - 이유: docs는 보고서 제출연도를 year로 사용, 요약재무정보의 "당기" 칸이 전년도 결산 데이터
- **단위**: 대부분 **백만원** (docs × 1,000,000 = finance 원 단위)
  - 소수 종목: 원 단위(15건), 천원 단위(5건)
- **커버리지**: 1999년~현재 (finance는 2015~)

### 2. 계정별 일치율 (연도+단위 보정 후)

| 계정 | 비교건수 | 일치율 |
|------|---------|--------|
| total_assets | 678 | **95.0%** |
| noncurrent_assets | 608 | **95.4%** |
| capital_surplus | 342 | **95.0%** |
| paidin_capital | 588 | **93.9%** |
| cash | 382 | **93.7%** |
| intangible_assets | 476 | **93.1%** |
| current_assets | 616 | **92.9%** |
| retained_earnings | 530 | **92.3%** |
| inventories | 465 | **91.8%** |
| tangible_assets | 495 | **89.3%** |
| operating_profit | 582 | **84.2%** |
| sales | 556 | **81.7%** |
| total_stockholders_equity | 665 | 75.0% (지배/비지배 혼재) |
| net_profit | 467 | 60.0% (표기 불일치) |
| noncontrolling_interests_equity | 348 | 8.3% (이름 변이 심각) |

### 3. 불일치 원인
1. **EPS 단위 오보정**: EPS는 원 단위인데 ×1M 적용됨 → 계정별 단위 예외 필요
2. **지배기업자본/자본총계 혼재**: docs "자본총계" → finance `total_stockholders_equity` vs `owners_of_parent_equity`
3. **비지배지분 이름 변이**: "비지배지분", "소수주주지분", "비재배지분" 등
4. **IS 커버리지 낮음**: docs 요약재무정보에 매출원가/영업활동CF가 없는 경우 많음

## 결론: 프로덕션 배치 불필요

런타임 교차검증은 배치하지 않는다.

**이유:**
- insight, AI context, Excel export 모두 `finance/pivot` 단일 경로만 소비
- docs fsSummary는 정량 분석 경로에서 사용되지 않음
- 매 요청마다 docs 파싱 + 단위 감지 + 비교는 성능 악화만 초래
- 실험 053에서 두 소스의 일치(BS 95%)를 확인했으므로 finance XBRL 신뢰성 검증 완료

**이 실험의 가치:** 일회성 데이터 품질 감사. docs year N = finance year N-1 시차 발견은 향후 docs 장기 히스토리(1999~2014) 활용 시 참고사항.

### docs ↔ finance ↔ report 역할 분담 (현행 유지)

| 용도 | 소스 | 비고 |
|------|------|------|
| 정량 비교 (비율, 회사간) | **finance** (XBRL) | snakeId 통일, 원 단위 정밀 |
| 장기 히스토리 (2014 이전) | **docs** | 1999~현재 (finance는 2015~) |
| 정성 정보 (텍스트, 서술) | **docs** | 34개 모듈 |
| 실시간 (배당/직원/주주 등) | **report** (API) | 구조화된 API |

### 향후 참고사항
- docs 장기 히스토리 활용 시: year -1 보정 + 단위 자동감지(median ratio) 필요
- EPS/DPS 등 주당지표는 단위 보정 제외 대상
- 비지배지분 한글 이름 변이 심각 (8.3% 일치) → accountMappings.json 보강 여지
