# 083_bizModelDna — 사업모델 DNA 추출 실험

## 목표
공시 데이터(finance + report + docs)에서 사업모델 아키타입을 자동 분류하는 방법론 검증

## 실험 현황

| # | 실험명 | 상태 | 핵심 결과 |
|---|--------|------|----------|
| 001 | dataAudit | ✅ 완료 | finance 96%, report 98%, docs section_title 6~66% |
| 002 | revenueStructure | ✅ 완료 | F-stat < 2 (단일 비율 분리 불충분), segments 0/5 가용 |
| 003 | costFingerprint | ✅ 완료 | 자산집약도×인건비집약도 4사분면: 섹터 직관과 높은 일치 |
| 004 | capitalAllocation | ✅ 완료 | capex+배당+투자사수 3축: IT→Growth 75%, 금융→CashReturner 43% |
| 005 | cashConversion | ✅ 완료 | CCC×CF마진 2D: 식품→빠른현금화, 반도체→품질수익, 바이오→현금압박 |
| 006 | moatDetection | ✅ 완료 | 해자 vs 영업이익률 ρ=0.441 (>0.3), 무형자산 해자 압도적 |
| 007 | archetypeClassify | ✅ 완료 | k=3 silhouette=0.223, 3 아키타입 분리 (산업재70%, 소비재80% 매칭) |

## 핵심 발견

### 001: 데이터 커버리지
- finance + report: 96~98% 커버리지 → 사업모델 DNA의 핵심 축
- docs section_title: segments/costByNature 6%로 매우 낮음 → sections 수평화 필요
- 금융 섹터: finance 기간 짧음(9p), 일반 제조업 계정 부재 → 별도 처리

### 002: 매출 구조
- 단일 finance 비율(grossMargin 등) F-stat < 2 → 섹터 간 80% 분리 불가
- segments 토픽 0/5사 가용 → 매출 구조는 다차원 비율 조합으로 근사 필요

### 003: 비용 구조 (핵심 성과)
- 자산집약도(tangibleAssets/totalAssets) × 인건비집약도(totalSalary/revenue) 4사분면이
  섹터 직관과 높은 일치: 반도체→Q3, SW→Q2, 자동차→Q4, 플랫폼→Q1
- 유효 데이터: assetIntensity 96%, laborIntensity 77%

### 004: 자본배분
- capexRatio + dividendPayoutRatio + investedCompanyCount 3축으로 4 아키타입 분류
- IT/반도체 → Growth Investor 75% ✓, 금융 → Cash Returner 43%
- R&D비율: IS 별도 계정 4%뿐 → 텍스트 기반(006)으로 전환 필요
- investedCompanyCount 98% 커버리지: 확장 성향 식별에 강력

### 005: 현금전환
- CCC × 영업CF마진 2D 분류: 4패턴(빠른현금화/품질수익/현금압박/자금회전)
- 식품/유통 → 빠른현금화, 반도체 → 품질수익, 바이오 → 현금압박, 자동차 → 자금회전
- 금융 CCC 계산 불가 → 별도 지표 필요
- 이상값 주의: SW/게임사 매출원가 극소, 바이오 CCC 극대

### 006: 해자 탐지 (핵심 성과)
- 해자 점수 vs 영업이익률 Spearman ρ=0.441 > 0.3 기준 충족
- 무형자산 해자(특허/R&D/인증) 21사 압도적 — 한국 사업보고서 서술 특성
- TOP: 셀트리온(51.3), SK바이오팜(39.4), NAVER(34.9)
- 전환비용/비용우위 키워드는 밀도 0에 가까움 → 키워드 확장 또는 문맥 분석 필요

### 007: 아키타입 분류 (종합)
- 최적 k=3, silhouette=0.223 (목표 0.25 약간 미달)
- 3개 아키타입: Heavy Manufacturer(6사) / Cash Returner(15사) / Balanced Operator(17사)
- 산업재 70%, 필수소비재 80% 매칭 — 직관과 부합
- dividendPayoutRatio 54% 결측이 가장 큰 노이즈 원인
- 금융 별도 분류 필요 → Phase 4에서 3+1(비금융3+금융1) 구조

## Phase 1 종합 결론

1. **유효한 축**: 비용구조(003), 자본배분(004), 현금전환(005), 해자(006) — 4축 모두 유효
2. **기각된 축**: 매출구조(002) — segments 부재, 단일 비율 분리력 부족
3. **데이터 한계**: R&D 비율(4%), 배당성향(46%), docs 텍스트(65%) — 보강 필요
4. **금융 섹터**: 모든 축에서 별도 처리 필요 (CCC/자산집약도/매출 개념 상이)
5. **프로덕션 적용**: 3+1 아키타입 (비금융 3개 + 금융 1개) 구조로 engines/bizmodel/ 설계 권장
