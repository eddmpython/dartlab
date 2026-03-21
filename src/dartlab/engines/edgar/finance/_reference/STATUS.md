# EDGAR Finance 매핑 현황

> dartlab EDGAR 재무제표 정규화 엔진의 현재 상태, 실험 이력, 남은 과제를 한 곳에서 관리한다.
>
> **최종 업데이트**: 2026-03-10

---

## 1. 매핑 시스템 개요

```
원본 XBRL tag (영문 CamelCase)
  | STMT_OVERRIDES (NetIncomeLoss -> IS/CF 분리)
  | commonTags (standardAccounts.json, 344 tag -> 179 snakeId)
  | learnedSynonyms (tagMappings, 10,799 tag)
  | EDGAR_TO_DART_ALIASES (13개, edgar snakeId -> dart snakeId)
  | None (미매핑)
```

### 데이터 규모

| 항목 | 값 | 파일 |
|------|-----|------|
| 표준계정 | 179개 (BS54, IS42, CF53, EQ6, CI4, NT20) | mapperData/standardAccounts.json |
| commonTags | 344 tag | standardAccounts.json 내 |
| 학습 태그 (tagMappings) | 10,680개 | mapperData/learnedSynonyms.json |
| EDGAR→DART aliases | 13개 | mapper.py EDGAR_TO_DART_ALIASES |
| eddmpython 학습 이력 | 51차 (8,158/10,301 CIK, 79.2%) | _reference/SYNONYM_LEARNING_SUMMARY.md |

### 프로덕션 파일

| 파일 | 역할 |
|------|------|
| mapper.py | EdgarMapper: STMT_OVERRIDES + commonTags + tagMappings + EDGAR_TO_DART_ALIASES (13개) |
| pivot.py | buildTimeseries: 원본 parquet -> 분기별 시계열 dict |

---

## 2. 실험 이력 (dartlab 흡수 후)

### 001 - mappingQuality (기초 매핑 품질 측정)

- **목적**: 10개 대형주 (AAPL, MSFT, GOOG 등)의 매핑률 + 핵심 21개 계정 커버리지 측정
- **결과**: 태그 매핑률 92.8%, 핵심 계정 평균 89%
- **상태**: 완료 (기준선 확립)

### 002 - frequencyLearning (빈도 기반 분석)

- **목적**: 전체 CIK에서 미매핑 태그 빈도 수집, 패턴 분류
- **결과**: 280개 1%+ 출현 미매핑 태그 식별, autoClassify 확장 기반 확보
- **상태**: 완료

### 003 - fixAndDerive (오매핑 수정 + 학습)

- **목적**: 오매핑 수정 + 신규 태그 학습으로 커버리지 개선
- **결과**:
  - +280 신규 태그 학습, +284 오매핑 수정 (11,386 -> 11,666)
  - 핵심 계정 89% -> 93.3% (10사 평균)
- **문제**: 284 수정 중 92개가 오수정 (liability -> asset 등) -> 005에서 롤백
- **상태**: 완료 (오수정은 005에서 해결)

### 004 - gapAnalysis (갭 원인 분석)

- **목적**: AMZN/WMT total_liabilities 갭 원인 + 003 수정 검증
- **결과**:
  - AMZN/WMT는 `Liabilities` XBRL 태그 자체를 미보고 (매핑 문제 아님)
  - 003 수정 중 71개 의심 패턴 식별 -> 005에서 92개로 확정 후 롤백
  - 파생 계산으로 해결 가능: `total_liabilities = total_assets - equity_including_nci`
- **상태**: 완료

### 005 - rollbackBadFixes (오수정 롤백)

- **목적**: 003의 오수정 92개 롤백
- **결과**:
  - 6개 삭제, 86개 원복 (11,666 -> 11,660)
  - AMZN 95% -> 100% (파생 계산 성공)
  - WMT 90% 유지 (total_liabilities = total_assets - equity 파생으로 해결 가능, 49Q 검증)
- **상태**: 완료

### 006 - universalCoverage (전체 CIK 커버리지 스캔)

- **목적**: 16,601 CIK 전수 스캔, 표준계정 149개(BS+IS+CF) 커버리지 측정
- **결과**:

#### 핵심 21개 계정 보정 커버리지

```
90%+ (6개): total_assets(94.8%), net_income(94.6%), cash(93.9%),
            operating_CF(94.1%), financing_CF(93.6%), total_liabilities(92.1%/파생)
80%+ (5개): operating_income(83.5%), current_assets(83.3%),
            non_current_assets(83.3%/파생), current_liab(80.5%), non_current_liab(80.5%/파생)
70%+ (4개): revenue(78.8%), investing_CF(87.5%), ppe(74.7%), profit_before_tax(74.7%)
50%+ (3개): cost_of_sales(54.2%), gross_profit(54.2%/파생), trade_receivables(61.8%)
<50% (3개): inventories(41.6%), total_equity/equity_including_nci(92.1%/alias)
```

#### 파생 효과

| 계정 | 파생 전 | 파생 후 | 증가 CIK |
|------|---------|---------|-----------|
| total_liabilities | 87.2% | 92.1% | +807 |
| non_current_liabilities | 38.5% | 80.5% | +6,964 |
| gross_profit | 44.6% | 54.2% | +1,599 |
| non_current_assets | 79.7% | 83.3% | +599 |

#### 측정 주의점

- mapToDart() stmt 없이 호출 시 STMT_OVERRIDES/EDGAR_TO_DART_ALIASES 왜곡 발생
- net_income -> net_income_cf(94.6%), total_equity -> equity_including_nci(92.1%)
- 14개 alias 원본 snakeId는 0% 표시되지만 실제로는 alias 대상에 포함
- ~5,600 CIK(34%)는 revenue 없음 (SPV/SPC/Fund/Shell)

- **상태**: 완료

### 007 - derivedValidation (파생 계정 정확도 검증)

- **목적**: 5개 파생 공식의 실제 정확도를 S&P 100 대형주에서 검증
- **결과**:
  - 파생 공식 자체는 수학적으로 정확 (회계 항등식)
  - 정확도 병목은 파생이 아니라 **learnedSynonyms 오매핑** + **BS 전기비교값 혼입**
  - 오매핑 예시: DeferredTaxLiabilitiesTaxDeferredIncome → total_liabilities
  - XBRL 원본 태그 직접 검증 (R2/R5): 91.5% ≤1% 정확 (PG FY 제외 시 100%)
  - 커버리지 증가: gross_profit +38%, non_current_liabilities +47% (최대 효과)
- **판단**: _computeDerived() 배치 가능 (보고값 없을 때만 파생, 덮어쓰기 안 함)
- **후속**: learnedSynonyms 오매핑 정리 필요 → 008에서 해결
- **상태**: 완료

### 008 - mappingCleanup (오매핑 제거 + 미매핑 학습)

- **목적**: level=1 합산계정 오매핑 929개 제거 + S&P 100 미매핑 태그 68개 학습
- **결과**:
  - Phase 1-2: 929개 오매핑 제거 (11,660 → 10,731)
    - operating_cash_flow(251), revenue(222), total_other_comprehensive_income(200) 등
  - Phase 3-4: 68개 태그 학습 (10,731 → 10,799)
    - 매핑률: 87.2% → 92.1% (+4.9%p, S&P 100 dei 제외 기준)
  - 007 재검증:
    - D2 (cur+noncur liab): 34.0% → **98.8%** ★
    - D5 (total_liab - cur_liab): 45.7% → **98.8%** ★
    - D3 (gross_profit): 80.7% → 84.5%
    - D1 (assets - equity): 57.3% (변화없음, BS 전기비교값 문제)
- **교훈**: level=1 합산계정에는 commonTags만 매핑, learnedSynonyms는 level=2/3만
- **상태**: 완료

### 009 - bsPriorPeriod (BS 전기비교값 분석 + majorityEnd 전략)

- **목적**: D1(61.9%), D4(72.0%) 낮은 정확도의 근본 원인인 BS 전기비교값 혼입 정량화 + 해결 전략 도출
- **결과**:
  - S&P 100, 38,070개 (tag, fy, fp) 중 **7,567개(19.9%)가 복수 end date** 보유
  - 전략 비교 (R1: Liabilities = Assets - Equity(NCI)):
    - baseline: 61.9% ≤1%
    - **majorityEnd: 94.8% ≤1%** ★ (+32.9%p)
    - instantOnly: 61.9% (BS 모두 instant라 효과 없음)
  - R4 (NoncurrentAssets = Assets - CurrentAssets): 72.0% → **80.8%** (+8.8%p)
- **핵심**: 각 (fy, fp)에서 가장 많은 태그가 보고하는 end date를 "기대 end"로 사용
- **적용**: pivot.py `_selectBS()`에 majorityEnd 전략 적용 완료
- 007 재검증 (majorityEnd 적용 후):
  - D1: 57.3% → **88.1%** ★ (+30.8%p)
  - D4: 40.8% → 42.9% (+2.1%p, CSCO/ABBV 매핑 문제 잔존)
  - D2/D5: 98.8% (유지)
  - D3: 84.5% → 83.6% (-0.9%p, 변동폭 내)
  - 파생 체인(D1→D5): 52.0% → **81.8%** (+29.8%p)
- **상태**: 완료

### 010 - d4ErrorAnalysis (D4 오차 원인 분석 + non_current_assets 오매핑 제거)

- **목적**: D4(42.9%) 정확도 병목의 근본 원인 파악 + 해결
- **결과**:
  - 근본 원인: `noncurrent` suffix 세부 태그 119개가 `non_current_assets`로 오매핑
  - 10개 오차 기업 중 AssetsNoncurrent 직접 보고: 0개
  - 010b에서 119개 오매핑 제거 (10,799 → 10,680)
  - D4: 42.9%(27사) → **62.3%**(13사) (+19.4%p)
  - D4 커버리지: 보고 14%, 파생가능 83% → +70% 신규 커버
- **교훈**: level=2 합산계정도 suffix 기반 학습으로 세부 태그 유입 가능
- **상태**: 완료

### 011 - perCompanyDiagnosis (오차 기업 1:1 정밀 진단)

- **목적**: D1/D4 오차 >5% 기업 12+4개를 원본 parquet로 1:1 진단, 원인 분류
- **결과**:
  - majorityEnd 이후 해결된 기업 (0% 오차): BKNG, DHR, DUK, EMR, INTU, PYPL, SO
  - 잔존 오차 원인 3가지 발견:
    1. **SE/SE_NCI 동일 매핑 충돌**: total_equity commonTags에 두 태그 공존 → NEE 8-10%, KHC 0.4%, TSLA 1.6-3.3%
    2. **NoncurrentAssets 의미 불일치**: 부분 소계로 보고하는 기업 → META 36.9%, TSLA 56.3%
    3. **TemporaryEquity/RedeemableNCI 누락**: BS 등식 gap → NEE 401M, KHC 6M, TSLA 63M
- **상태**: 완료 → 012에서 해결

### 012 - equitySplit (equity 분리 매핑)

- **목적**: SE와 SE_NCI를 분리하여 D1/D4 정확도 개선
- **수정**:
  - standardAccounts.json: total_equity commonTags → SE만, 신규 equity_including_nci(BS) → SE_NCI만
  - mapper.py: EDGAR_TO_DART_ALIASES에서 total_equity→equity_including_nci 제거 (14→13개)
  - pivot.py: _computeEquity() 양방향 파생 (eq_nci↔teq, NCI 없는 기업 자동 처리)
- **007 검증 결과**:
  - D1: 88.6% → **96.9%** (+8.3%p) ★
  - D2: 98.8% → 99.0%
  - D3: 83.7% → **91.8%** (+8.1%p)
  - D4: 62.3% → **96.4%** (+34.1%p) ★
  - D5: 98.8% → 99.0%
- **개별 기업**: NEE 9.8%→0.3%, KHC 0.5%→0.0%, TSLA 3.3%→0.1%, BKNG 0%(유지)
- **테스트**: 18/18 통과
- **상태**: 완료

### 013 - fullValidation (전체 CIK 파생 정확도 검증 + mezzanine equity 반영)

- **목적**: 012까지의 개선이 전체 16,601 CIK에서도 유효한지 검증 + 잔존 문제 해결
- **결과**:
  - Phase 1 (012 그대로 2000 샘플): D1 93.3%, D2 98.9%, D3 90.6%, D4 95.5%, D5 98.7%
  - D1 >10% 분석: 92%가 equity undercount (mezzanine equity 누락)
  - TemporaryEquityCarryingAmountAttributableToParent (2,561 CIK) 미매핑 발견
  - Phase 2: mezzanine equity 반영
    - _computeEquity()에 redeemable_noncontrolling_interest → equity_including_nci 합산
    - sanity check: merged > total_assets이면 합산 안 함 (SPAC trust 이상치 방지)
    - standardAccounts.json commonTags에 2개 태그 추가 (2,804 CIK 커버)
  - Phase 3 (최종 2000 샘플): **D1 95.7%**, D2 99.0%, D3 91.1%, D4 95.5%, D5 98.7%
  - D1 개선: 93.3% → 95.7% (+2.4%p)
- **S&P 100 vs 전체 CIK 비교**: 차이 1~2%p 이내로 일관적
- **남은 >10% 오류**: 합병 과도기(KHC 2015), SPAC trust 이상, 데이터 품질 문제
- Phase 4: >10% 기업 전수 개별 진단
  - D1 238개: multiEnd(71), 거대gap(142), 극소기업(23), 음수부채(2), **미매핑equity=0**
  - D2/D4/D5: 100% majorityEnd cross-period mixing, 매핑문제 0
  - D3: 66% Q4 역산(YTD 혼입), 34% multiEnd, 매핑문제 0
  - **매핑 데이터는 완벽 — 추가 수정 대상 없음**
- **테스트**: 18/18 통과
- **상태**: 완료

---

## 3. 파생 계정 전략 (_computeDerived)

### 확정된 공식 (우선순위 순)

1. `total_liabilities = total_assets - equity_including_nci` (회계 항등식)
2. `total_liabilities = current_liabilities + non_current_liabilities` (합산)
3. `gross_profit = revenue - cost_of_sales`
4. `non_current_assets = total_assets - current_assets`
5. `non_current_liabilities = total_liabilities - current_liabilities`

### 순서

- total_liabilities 먼저 파생 → non_current_liabilities 파생에 사용
- pivot.py의 _computeEquity() 패턴 확장 예정

### 007 검증 결과

- 파생 공식 자체는 정확하나, **보고값이 오매핑으로 왜곡된 경우** 비교 불가
- "보고값 없을 때만 파생"이므로 오매핑 값을 덮어쓸 위험 없음 → **안전하게 배치 가능**
- 커버리지 효과: S&P 100 기준 total_liabilities 70%→100%, gross_profit 33%→72%
- 008 이후 보고 종목 감소 (거짓양성 제거): D1 보고 84→70%, D5 보고 30→17%

---

## 4. 데이터 품질 이슈 (요약)

### 해결됨

| 이슈 | 해결 방법 |
|------|----------|
| 동일 Period 다중 값 혼재 | FY/Q1: max(), Q2/Q3: min() |
| Amended Period 파싱 (2012-Q2A) | 숫자만 추출 |
| Q4 직접 보고 부재 | Q4 = FY - Q1 - Q2 - Q3 (IS/CF), Q4 = FY (BS) |

### 미해결/제약

| 이슈 | 상태 | 영향 |
|------|------|------|
| YTD 전용 종목 (GOOG 등) | eddmpython에서 수동 플래그 처리, dartlab 미흡수 | Q2/Q3 정확도 저하 (~20% 종목) |
| Frame 필드 신뢰성 | frame=null 우선 사용, 100% 보장 없음 | 모니터링 필요 |
| 타입 충돌 (UPS, LMT, NKE) | val 컬럼에 문자열 혼입, 미수정 | 해당 종목 로드 실패 |
| SEC CIK 비활성 기업 | 34% revenue 없음 (SPV/Fund/Shell) | 커버리지 통계 희석 |

---

## 5. 학습 이력 요약

### dartlab 흡수 전 (eddmpython, 2026-01-23~25)

```
51차 학습, 8,158/10,301 CIK (79.2%)
660 -> 11,375 tagMappings (17.2배 증가)
S&P 100: 100%, S&P 500: 97.5%
```

상세: SYNONYM_LEARNING_SUMMARY.md (아카이브)

### dartlab 흡수 후 (2026-03-10)

```
003: +280 학습, +284 수정 (11,386 -> 11,666)
005: -6 삭제, 86 복원 (11,666 -> 11,660)
008: -929 오매핑 제거 + 68 학습 (11,660 -> 10,799)
  - S&P 100 매핑률: 87.2% → 92.1%
  - D2/D5 정확도: 34%/46% → 98.8%
010: -119 noncurrent 세부태그 오매핑 제거 (10,799 -> 10,680)
  - D4 정확도: 42.9% → 62.3%
012: standardAccounts.json equity 분리 + EDGAR_TO_DART_ALIASES 14→13개
  - D1: 88.6% → 96.9%, D4: 62.3% → 96.4%
013: mezzanine equity 반영 + TemporaryEquity commonTags 추가
  - standardAccounts.json: redeemable_noncontrolling_interest commonTags 2→4개
  - pivot.py: _computeEquity() mezzanine → equity_including_nci 합산 + sanity check
  - 전체 2000 CIK D1: 93.3% → 95.7%
로그: learningLogs/ 디렉토리
```

---

## 6. 남은 과제

### P0 - 파생 계정 프로덕션 배치 ✅

- [x] pivot.py에 _computeDerived() 함수 추가
- [x] _computeEquity() 패턴 확장 (보고값 없을 때만 파생, 덮어쓰기 없음)
- [x] 파생 값 vs 실제 보고 값 교차 검증 실험 (007 완료)
- [x] 5개 공식: total_liabilities(D1/D2), gross_profit(D3), non_current_assets(D4), non_current_liabilities(D5)
- [x] 실행 순서: total_liabilities 먼저 → non_current_liabilities 파생에 사용
- [x] 테스트 18/18 통과, AMZN 파생 검증 완료

### P0.5 - learnedSynonyms 오매핑 정리 ✅

- [x] level=1 합산계정 24종에 매핑된 929개 오매핑 전량 제거 (008)
- [x] S&P 100 미매핑 태그 68개 학습 (008b)
- [x] 매핑률 87.2% → 92.1%, D2/D5 98.8% 달성

### P1 - 활성 기업 필터링

- [ ] 16,601 CIK 중 비활성(SPV/Fund/Shell) 필터링
- [ ] 활성 기업만 커버리지 재측정

### P2 - DART<->EDGAR snakeId 교차 비교

- [ ] EDGAR_TO_DART_ALIASES 14개 충분한지 확인
- [ ] standardAccounts.json alias 원본 snakeId 정리

### P3 - 미흡수 기능

- [ ] YTD 처리 (ytdProcessor.py -> pivot.py 통합)
- [ ] SynonymLearner 포팅 (증분 학습 사이클)
- [ ] Fuzzy 매핑 (rapidfuzz) 흡수 여부 결정

---

## 7. 파일 구조

```
engines/edgar/finance/
+-- mapper.py                       <- EdgarMapper (프로덕션)
+-- pivot.py                        <- buildTimeseries (프로덕션)
+-- mapperData/
|   +-- standardAccounts.json       <- 179개 표준계정
|   +-- learnedSynonyms.json        <- 10,799개 학습 태그
+-- _reference/                     <- 로컬 전용 (.gitignore)
    +-- STATUS.md                   <- 이 문서 (현황/실험/과제)
    +-- MAPPING_GUIDE.md            <- 아키텍처/출처 레퍼런스
    +-- LEARNING_WORKFLOW.md        <- 학습 절차 가이드
    +-- experiments/                <- dartlab 매핑 실험 (활성)
    |   +-- 001_mappingQuality.py
    |   +-- 002_frequencyLearning.py
    |   +-- 003_fixAndDerive.py
    |   +-- 004_gapAnalysis.py
    |   +-- 005_rollbackBadFixes.py
    |   +-- 006_universalCoverage.py
    |   +-- 007_derivedValidation.py
    |   +-- 008_mappingCleanup.py
    |   +-- 008b_learnNewTags.py
    |   +-- 009_bsPriorPeriod.py
    |   +-- 010_d4ErrorAnalysis.py
    |   +-- 010b_ncaCleanup.py
    |   +-- 011_perCompanyDiagnosis.py
    |   +-- 012_equitySplit.py
    |   +-- 013_fullValidation.py
    +-- learningLogs/               <- 학습 변경 JSON 로그 (활성)
    +-- eddmpython/                 <- eddmpython 원본 (참조용)
    |   +-- v1/                     <- StandardMapper, SynonymLearner, FinanceSearch
    |   +-- scripts/                <- batchLearner, checkProgress
    |   +-- config.py, ytdProcessor.py, ytdTickers.json, learnedTickers.json, sortOrder.json
    +-- _archive/                   <- 아카이브 문서 (역사적 참조)
```

---

## 8. 참조 문서

| 문서 | 용도 |
|------|------|
| MAPPING_GUIDE.md | 2-Tier 매핑 아키텍처, eddmpython 원본 경로, autoClassify 로직, 미흡수 기능 목록 |
| LEARNING_WORKFLOW.md | 학습 사이클 (측정->분석->학습->검증), 오매핑 수정 절차, 신규 태그 학습 절차 |
| eddmpython/ | eddmpython 원본 코드/데이터 (v1/, scripts/, config, ytdProcessor 등) |
| _archive/*.md | eddmpython 시절 세션 기록, 계획, 데이터 품질 분석 (역사적 참조용) |
| memory/edgar-mapping.md | Claude 메모리: DART vs EDGAR 비교, 커버리지 데이터, 파생 전략 |
