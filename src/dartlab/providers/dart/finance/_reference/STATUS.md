# DART Finance 매핑 현황

> dartlab DART 재무제표 정규화 엔진의 현재 상태, 실험 이력, 남은 과제를 한 곳에서 관리한다.
>
> **최종 업데이트**: 2026-03-10

---

## 1. 매핑 시스템 개요

### 현재 파이프라인 (v8 체계, CORE_MAP/SNAKE_ALIASES 제거 후)

```
원본 (account_id, account_nm)
  | prefix 제거 (ifrs-full_, dart_, ifrs_, ifrs-smes_)
  | ID_SYNONYMS (영문 동의어 통합, 59개)
  | ACCOUNT_NAME_SYNONYMS (한글명 동의어 통합, 106개)
  | accountMappings.json (34,249개 = standardAccounts + learnedSynonyms + 수동학습)
  | 괄호 제거 후 재조회 (fallback)
  | None (미매핑)
```

### 이전 파이프라인과 차이

```
[제거됨] CORE_MAP (38개 영문/한글 하드코딩 오버라이드)
  → accountMappings.json에 이미 동일 매핑 포함, 불필요
  → CORE_MAP의 snakeId가 standardAccounts와 달랐음 (예: revenue vs sales)

[제거됨] SNAKE_ALIASES (19개, pivot.py에서 매핑 후 snakeId 정규화)
  → CORE_MAP 제거 후 accountMappings.json이 직접 standardAccounts snakeId 반환
  → 별도 정규화 불필요
```

### 데이터 규모

| 항목 | 값 | 파일 |
|------|-----|------|
| accountMappings.json | 34,249개 (병합+수동학습) | mapperData/accountMappings.json |
| standardAccounts | 13,243개 (DART 표준계정코드) | _reference/eddmpython/standardAccounts.json |
| learnedSynonyms | 31,493개 (학습 동의어) | _reference/eddmpython/learnedSynonyms.json |
| ID_SYNONYMS | 59개 | mapper.py 하드코딩 |
| ACCOUNT_NAME_SYNONYMS | 106개 | mapper.py 하드코딩 |

### 프로덕션 파일

| 파일 | 역할 |
|------|------|
| mapper.py | AccountMapper: prefix제거 + ID_SYNONYMS + NAME_SYNONYMS + accountMappings.json |
| pivot.py | buildTimeseries/buildAnnual: 원본 parquet -> 분기/연간 시계열 dict |
| extract.py | getLatest, getTTM 등 시계열에서 값 추출 |
| ratios.py | 재무비율 계산 (수익성, 안정성, 밸류에이션) |

---

## 2. 실험 이력

### 001 - measureMapping (매핑률 측정)

- **목적**: 전체 2,743 종목 매핑률 측정
- **결과**: 96.49% (BS 98.91%, IS 94.16%, CF 96.56%, CIS 97.31%, SCE 91.60%)
- **상태**: 완료 (기준선 확립)

### 002 - accountCoverage (핵심 계정 보유율)

- **목적**: 핵심 21개 계정의 종목별 보유율 측정
- **결과**: sga_expenses 0% (snakeId명 불일치, 실제 selling_and_administrative_expenses)
- **상태**: 완료

### 003 - semanticConsistency (의미 일관성)

- **목적**: 같은 snakeId에 매핑된 계정명들의 의미 일관성 검사
- **결과**: 8개 snakeId 집중도 50% 미만 -> 006에서 대부분 false alarm 확인
- **상태**: 완료

### 004 - balanceSheetValidation (BS 항등식 검증)

- **목적**: 자산 = 부채 + 자본 항등식 검증
- **결과**: 99.7% 정확 일치, 99.9% 오차 1% 이내
- **상태**: 완료

### 005 - sectorComparability (업종별 비교가능성)

- **목적**: 업종별 핵심 계정 비교가능성 분석
- **결과**: 금융 55개가 약점의 주원인, 비금융 2,509개는 92%+
- **상태**: 완료

### 006 - diagnoseMismappings (오매핑 진단)

- **목적**: 003에서 발견된 의미 불일치의 실제 영향 분석
- **결과**: sj_div 분리로 cross-statement 오매핑은 수치 오염 없음 (false alarm)
- **상태**: 완료

### 007 - improvements.md (매핑 개선 적용)

- **목적**: 001~006 결과 기반 실제 개선 적용
- **적용**: SNAKE_ALIASES 2개 추가 (trade_receivables 통일), accountMappings.json 오학습 4건 제거
- **미적용**: income_taxes alias 유지, sga alias 불필요
- **상태**: 완료

### 008 - postV8MappingScan (CORE_MAP 제거 후 전종목 스캔)

- **목적**: CORE_MAP/SNAKE_ALIASES 제거 후 전종목 매핑률 재측정 + 수동 학습 보강
- **배경**: v8 체계 마이그레이션 (CORE_MAP 38개 + SNAKE_ALIASES 19개 제거)
- **결과**:
  - Phase 1 (제거 직후): 96.49% — 001과 동일 (CORE_MAP 불필요 확인)
  - Phase 2 (수동 학습 78개 추가 후): 96.87% (+0.38%p)
  - 미매핑 42,341→37,692 (-4,649개)
  - SCE 최대 개선: 91.60%→93.13% (+1.53%p)
  - CF: 95.68%→95.98% (+0.30%p)
- **핵심 발견**: 공백 있는 계정명이 미매핑 주원인 (공백 없는 버전은 이미 매핑)
- **상태**: 완료

---

## 3. 로직 변경 이력

### 2026-03-10: v8 체계 마이그레이션

**변경 범위**: mapper.py, pivot.py + 다운스트림 전체 (17+ 파일)

#### mapper.py

| 항목 | 이전 | 이후 |
|------|------|------|
| CORE_MAP | 38개 (영문23+한글15) 하드코딩 오버라이드 | **제거** |
| 매핑 파이프라인 | prefix→ID_SYNONYMS→NAME_SYNONYMS→**CORE_MAP**→accountMappings.json | prefix→ID_SYNONYMS→NAME_SYNONYMS→accountMappings.json |
| snakeId 체계 | CORE_MAP 자체 snakeId (revenue, net_income 등) | standardAccounts snakeId (sales, net_profit 등) |

#### pivot.py

| 항목 | 이전 | 이후 |
|------|------|------|
| SNAKE_ALIASES | 19개 하드코딩 정규화 | **제거** |
| _PIVOT_TO_STD | mapper 결과 후처리 | **제거** |
| snakeId 출력 | SNAKE_ALIASES로 정규화된 snakeId | mapper에서 직접 standardAccounts snakeId 반환 |

#### 다운스트림 snakeId 변경 맵

```
revenue → sales
operating_income → operating_profit
net_income → net_profit
cash_and_equivalents → cash_and_cash_equivalents
non_current_assets → noncurrent_assets
non_current_liabilities → noncurrent_liabilities
total_equity → owners_of_parent_equity
equity_including_nci → total_stockholders_equity
equity_nci → noncontrolling_interests_equity
short_term_borrowings → shortterm_borrowings
long_term_borrowings → longterm_borrowings
bonds → debentures
trade_payables → trade_and_other_payables
trade_receivables → trade_and_other_receivables
issued_capital → paidin_capital
other_equity_components → other_equity
financing_cashflow → cash_flows_from_financing_activities
dividends_paid → dividends
income_tax_expense → income_taxes
basic_eps → basic_earnings_per_share
diluted_eps → diluted_earnings_per_share
finance_cost → finance_costs
equity_method_income → gainslosses_in_equity_method
ppe → tangible_assets
```

#### 변경된 파일 목록

| 영역 | 파일 | 변경 |
|------|------|------|
| L1 매핑 | mapper.py | CORE_MAP 제거 |
| L1 피벗 | pivot.py | SNAKE_ALIASES, _PIVOT_TO_STD 제거 |
| L2 인사이트 | insight/anomaly.py | 24개 snakeId 전체 교체 |
| L2 인사이트 | insight/detector.py | revenue→sales, operating_income→operating_profit |
| L2 인사이트 | insight/grading.py | snakeId 참조 확인 (변경 불필요) |
| L3 AI | ai/context.py | _FE_DISPLAY_ACCOUNTS, _QUESTION_ACCOUNT_FILTER 전면 교체 |
| 서버 | server/chat.py | revenue→sales |
| 비교 | compare.py | revenue→sales, net_income→net_profit |
| 내보내기 | export/excel.py | _ACCOUNT_LABELS_OVERRIDE 교체 |
| 내보내기 | export/template.py | docstring 교체 |
| Company | company.py | docstring 교체 |
| EDGAR | edgar/finance/mapper.py | EDGAR_TO_DART_ALIASES 13→37개 확장 |
| EDGAR | edgar/finance/pivot.py | _computeEquity, _DERIVED_FORMULAS 교체 |
| 테스트 | test_insightEngine.py | 8개 snakeId replace_all |
| 테스트 | test_excelExport.py | revenue→sales, net_income→net_profit |
| 테스트 | test_edgarFinance.py | 기대값 + l2Coverage 전면 교체 |

### 2026-03-10: 수동 학습 보강

- accountMappings.json에 78개 매핑 수동 추가 (34,171→34,249)
- 1차(22개): CIS 매출원가 세부, BS 금융기관차입금, SCE 배당/전환사채, CF VAT/법인세
- 2차(56개): CF 증감 세부(26개), SCE 세부(30개)
- 매핑률: 96.49% → 96.87% (+0.38%p)

---

## 4. 매핑 품질 요약

### 전체 매핑률: 96.87%

| 재무제표 | 매핑률 (이전→현재) |
|----------|---------------------|
| BS (재무상태표) | 98.91% → 98.94% |
| IS (손익계산서) | 94.16% → 98.39% |
| CF (현금흐름표) | 95.68% → 95.98% |
| CIS (포괄손익) | 97.31% → 97.84% |
| SCE (자본변동) | 91.60% → 93.13% |

### BS 항등식 정확도: 99.7%

### 종목 분포

| 구간 | 종목 수 | 비율 |
|------|---------|------|
| 100% | 172 | 6.7% |
| 99-100% | 324 | 12.6% |
| 95-99% | 1,795 | 70.0% |
| 90-95% | 255 | 9.9% |
| 80-90% | 18 | 0.7% |
| <80% | 0 | 0% |

### 핵심 안전장치

- **sj_div 분리**: BS/IS/CF/CIS/SCE 별도 처리 → cross-statement 오매핑이 수치를 오염시키지 않음
- **accountMappings.json 단일 소스**: standardAccounts snakeId를 직접 반환 (중간 변환 없음)

---

## 5. 남은 과제

### P0 - 현재 이슈 없음

- 매핑률 96.87%, BS 정확도 99.7%로 프로덕션 수준
- v8 체계 마이그레이션 완료, 테스트 371개 패스

### P1 - 공백 정규화 (97% 돌파 시 필요)

- 미매핑의 주원인: 공백 있는 계정명 (예: "부가가치세 예수금의 증가(감소)" vs "부가가치세예수금의증가(감소)")
- mapper.py에 공백 제거 정규화 단계 추가하면 ~97.5% 가능
- 현재는 수동 학습으로 대응 (78개 추가)

### P2 - 미흡수 v8 기능 (필요 시)

| 기능 | v8 파일 | 필요성 |
|------|---------|--------|
| 컨텍스트 매핑 (industry, statementKind) | parquetMapper.py | 낮음 |
| Fallback 매핑 (other_xxx) | fallbackMapper.py | 낮음 |
| 동의어 자동 학습 | synonymLearner.py | 중간 (SCE 93.1% 추가 개선에 유효) |
| 재무제표 합계 검증 | sumValidator.py | 낮음 (004에서 99.7% 확인) |

### P3 - 금융업 약점

- 55개 금융업종 종목에서 핵심 계정 커버리지 낮음
- sales, current_assets, cost_of_sales 등이 은행업 계정 체계와 다름
- 현재 ratios.py에서 해당 계정 없으면 None 반환 (에러는 아님)

---

## 6. 파일 구조

```
engines/dart/finance/
+-- mapper.py                       <- AccountMapper (프로덕션)
+-- pivot.py                        <- buildTimeseries/buildAnnual (프로덕션)
+-- extract.py                      <- getLatest, getTTM (프로덕션)
+-- ratios.py                       <- 재무비율 계산 (프로덕션)
+-- mapperData/
|   +-- accountMappings.json        <- 34,249개 병합 매핑 (프로덕션)
+-- _reference/                     <- 로컬 전용 (.gitignore)
    +-- STATUS.md                   <- 이 문서 (현황/실험/과제)
    +-- MAPPING_GUIDE.md            <- 아키텍처/출처 레퍼런스
    +-- LEARNING_WORKFLOW.md        <- 학습 절차 가이드
    +-- experiments/                <- dartlab 매핑 실험 (활성)
    |   +-- 001_measureMapping.py
    |   +-- 002_accountCoverage.py
    |   +-- 003_semanticConsistency.py
    |   +-- 004_balanceSheetValidation.py
    |   +-- 005_sectorComparability.py
    |   +-- 006_diagnoseMismappings.py
    |   +-- 007_improvements.md
    |   +-- 007_postV8MappingScan.py  <- v8 체계 마이그레이션 후 전종목 스캔
    +-- eddmpython/                 <- eddmpython 원본 (참조용)
    |   +-- v6/                     <- config.py (ID_SYNONYMS 출처), search.py
    |   +-- v7/                     <- StandardMapper, SynonymLearner, 학습 아카이브
    |   +-- v8/                     <- ParquetMapper, FallbackMapper, SumValidator 등 11개 파일
    |   +-- standardAccounts.json   <- DART 표준계정 13,243개
    |   +-- learnedSynonyms.json    <- 학습 동의어 31,493개
    |   +-- learnedSortOrder.json   <- 정렬 순서
```

---

## 7. 참조 문서

| 문서 | 용도 |
|------|------|
| MAPPING_GUIDE.md | v8 아키텍처 상세, eddmpython 출처, 매핑 흐름도, 미흡수 기능 목록 |
| LEARNING_WORKFLOW.md | 학습 사이클 (측정->수집->학습->병합->검증), accountMappings.json 병합 스크립트 |
| 007_improvements.md | 매핑 개선 투입 워크플로우, 변경 이력 + 사유 + 미변경 사유 |
| eddmpython/ | eddmpython 원본 코드/데이터 (v6/v7/v8, standardAccounts, learnedSynonyms) |
