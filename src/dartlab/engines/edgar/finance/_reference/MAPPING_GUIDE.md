# EDGAR 계정 매핑 가이드

eddmpython에서 dartlab으로 이관한 EDGAR 매핑/학습 시스템의 아키텍처 레퍼런스.
현황/실험/과제는 STATUS.md 참조.

## 출처

eddmpython 원본 경로:
```
C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\
└── core\edgar\
    ├── config.py                    ← SEC API 설정
    ├── ytdProcessor.py              ← YTD 처리 시스템
    ├── ytdTickers.json              ← YTD 종목 수동 플래그
    ├── learnedTickers.json          ← 학습 완료 종목 캐시 (8,158개)
    ├── searchEdgar\finance\
    │   ├── standardAccounts.json    ← 179개 표준계정
    │   ├── learnedSynonyms.json     ← 11,375개 학습 매핑
    │   ├── sortOrder.json           ← 정렬 순서
    │   └── v1\                      ← 매핑 엔진
    │       ├── standardMapping.py   ← StandardMapper
    │       ├── synonymLearner.py    ← SynonymLearner
    │       └── search.py            ← FinanceSearch
    └── scripts\
        ├── batchLearner.py          ← 배치 학습 스크립트
        └── checkProgress.py         ← 진행상황 확인
```

---

## _reference 파일 목록

```
_reference/
+-- STATUS.md                      <- 현황/실험/과제 (메인 문서)
+-- MAPPING_GUIDE.md               <- 이 문서 (아키텍처 레퍼런스)
+-- LEARNING_WORKFLOW.md           <- 학습 절차 가이드
+-- experiments/                   <- dartlab 매핑 실험 (001~006)
+-- learningLogs/                  <- 학습 변경 JSON 로그
+-- eddmpython/                    <- eddmpython 원본 (참조용)
|   +-- v1/                        <- StandardMapper, SynonymLearner, FinanceSearch
|   +-- scripts/                   <- batchLearner, checkProgress
|   +-- config.py, ytdProcessor.py, ytdTickers.json, learnedTickers.json, sortOrder.json
+-- _archive/                      <- 아카이브 문서 (역사적 참조용)
```

---

## 2-Tier 매핑 시스템

```
Layer 1: STANDARD (고정) → mapperData/standardAccounts.json
├── 179개 표준계정 (BS 54, IS 42, CF 53, EQ 6, CI 4, NT 20)
└── 각 계정: code, snakeId, korName, engName, level, line, parent, commonTags

Layer 2: LEARNED (동적) → mapperData/learnedSynonyms.json
├── tagMappings: 11,660개 {XBRL태그(소문자) → snakeId}
└── plabelMappings: (미사용, 향후 확장)
```

### 매핑 우선순위

1. **commonTags 직접 매칭** (confidence: 1.0) — standardAccounts의 commonTags 리스트
2. **tagMappings 학습 매칭** (confidence: 0.9) — learnedSynonyms의 11,375개
3. **plabelMappings** (confidence: 0.85) — 미사용
4. **Fuzzy 매칭** (confidence: 0.65+) — rapidfuzz 기반 token+fuzzy 조합

---

## dartlab mapper.py와의 관계

dartlab의 `mapper.py` (EdgarMapper)는 eddmpython v1의 단순 버전:

| eddmpython v1 기능 | dartlab 상태 |
|-------------------|-------------|
| commonTags 직접 매칭 | mapper.py에 흡수됨 |
| tagMappings 학습 매칭 | mapper.py에 흡수됨 |
| STMT_OVERRIDES | mapper.py에 흡수됨 |
| EDGAR_TO_DART_ALIASES | mapper.py에 흡수됨 (14개) |
| Fuzzy 매핑 (rapidfuzz) | **미흡수** |
| plabel 매핑 | **미흡수** |
| SynonymLearner | **미흡수** ← 최우선 흡수 대상 |
| batchLearner (autoClassify) | **미흡수** |
| YTD 처리 | **미흡수** |
| search.py (피벗/시계열) | pivot.py로 별도 구현 |

---

## 학습 현황 (2026-03-10 기준)

| 항목 | 값 |
|------|-----|
| 학습된 동의어 (tagMappings) | **11,660개** |
| 표준계정 (commonTags) | 179개 (344 태그) |
| eddmpython 학습 종목 | 8,158개 / 10,301개 (79.2%) |
| dartlab 실험 | 003: +280학습/+284수정, 005: -6삭제/86복원 |

상세 학습 이력: STATUS.md 참조

---

## YTD 이슈

### 문제
EDGAR는 Q2/Q3에 YTD(누적)와 개별 값이 혼재. 같은 tag, period에 여러 값 존재.

### 현재 해결책
- Q1/FY: `max(values)` 선택 (전체 합계, 세그먼트 배제)
- Q2/Q3: `min(values)` 선택 (개별 분기, YTD 배제)
- GOOG 등 YTD 전용: `ytdTickers.json`으로 수동 플래그 → `deaccumulateYTD()` 역산

### 데이터 정확도
| 구분 | 정확도 |
|-----|--------|
| Q1 | 95% |
| Q2/Q3 | 90% |
| Q4 (FY-Q1-Q2-Q3) | 95% |
| FY | 95% |
| 종합 | 90% |

---

## autoClassify 로직 (batchLearner.py)

키워드 기반 XBRL 태그 자동 분류. 100개+ 규칙:

| 키워드 | snakeId |
|--------|---------|
| othercomprehensiveincome | total_other_comprehensive_income |
| derivative + asset | derivative_assets_detail |
| fairvalue | fair_value_measurement_detail |
| lease | lease_investment_detail |
| sharebased, stockoption | stock_option_detail |
| incometax, deferredtax | income_tax_expense / deferred_tax_detail |
| businesscombination, goodwill | acquisition_detail |
| depreciation, amortization | depreciation_amortization / depreciation_cf |
| proceedsfrom | other_investing/financing_activities |
| asset + current | other_current_assets |
| liabilit + noncurrent | other_noncurrent_liabilities |
| (기본값) | other_note_detail |

---

## 향후 작업

STATUS.md 섹션 6 "남은 과제" 참조
