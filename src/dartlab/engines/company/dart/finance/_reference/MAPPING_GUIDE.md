# 계정 매핑 가이드

eddmpython에서 dartlab으로 이관한 계정 매핑 시스템의 아키텍처 레퍼런스.
현황/실험/과제는 STATUS.md 참조.

## 출처

eddmpython 원본 경로:
```
C:\Users\MSI\OneDrive\Desktop\sideProject\nicegui\eddmpython\
└── core\dart\searchDart\finance\
    ├── v6\   ← config.py (ID_SYNONYMS, ACCOUNT_NAME_SYNONYMS 원본), search.py (데이터로더)
    └── v8\   ← 전체 매핑 시스템 (11개 파일, 이 폴더에 전부 복사됨)
```

---

## _reference 파일 목록

```
_reference/
+-- STATUS.md                      <- 현황/실험/과제 (메인 문서)
+-- MAPPING_GUIDE.md               <- 이 문서 (아키텍처 레퍼런스)
+-- LEARNING_WORKFLOW.md           <- 학습 절차 가이드
+-- experiments/                   <- dartlab 매핑 실험 (001~006 + 007)
+-- eddmpython/                    <- eddmpython 원본 (참조용)
|   +-- v6/                        <- config.py (ID_SYNONYMS 출처), search.py
|   +-- v7/                        <- StandardMapper, SynonymLearner, 학습 아카이브
|   +-- v8/                        <- ParquetMapper, FallbackMapper, SumValidator 등 11개
|   +-- standardAccounts.json      <- DART 표준계정 13,243개
|   +-- learnedSynonyms.json       <- 학습 동의어 31,493개
|   +-- learnedSortOrder.json      <- 정렬 순서
```

---

## v8 아키텍처 개요

### 역할 분류

v8의 11개 파일은 4가지 역할로 나뉜다.

**매핑 파이프라인 (3단계 진화, 택 1)**

| 클래스 | 파일 | 핵심 개념 | 프로덕션 여부 |
|--------|------|-----------|--------------|
| StandardMapper | standardMapping.py | dict lookup (korName → snakeId). standardAccounts.json 직접매칭 → learnedSynonyms 매칭 → 실패. 신뢰도 standard=1.0, synonym=0.9 | v7 기본 |
| ParquetMapper | parquetMapper.py | Polars DataFrame 기반. 동의어 조회 → parquet에서 컨텍스트(industry, statementKind) 점수 → DataFrame korName 검색 → FallbackMapper. 신뢰도 0.3~1.4 | **v8 프로덕션** |
| OntologyMapper | ontologyMapper.py | OWL 온톨로지(owlready2) 기반. 의미론적 검색. 로딩 느림(5초), 메모리 많음(30MB) | 실험적, 안 씀 |

StandardMapper → ParquetMapper로 진화한 것이고, OntologyMapper는 실험 후 폐기 방향.
dartlab의 mapper.py는 StandardMapper보다도 단순한 버전 (v6 재현).

**데이터 빌더**

| 파일 | 입력 | 출력 | 용도 |
|------|------|------|------|
| parquetBuilder.py | standardAccounts.json | standardAccounts.parquet | ParquetMapper가 소비하는 Polars-native 포맷 |
| ontologyBuilder.py | standardAccounts.json | OWL 파일 | OntologyMapper가 소비 (실험적) |

parquetBuilder는 JSON→Parquet 단순 변환기. 한 번만 실행하면 됨.

**학습/개선 도구**

| 클래스 | 파일 | 핵심 개념 |
|--------|------|-----------|
| SynonymLearner | synonymLearner.py | 종목 순회 → 미매칭 수집 → SequenceMatcher 유사도 후보 → 자동승인(≥95%) 또는 수동검토 → learnedSynonyms.json 갱신. 학습 사이클을 반복하면 동의어가 점진적으로 늘어남 |
| FallbackMapper | fallbackMapper.py | 매핑 완전 실패한 계정을 재무제표별 키워드 규칙으로 other_xxx에 분류. 재무제표 합계(자산=부채+자본 등) 보존이 목적. BS/IS/CF/CIS/SCE 각각 키워드 dict + 2단계 fallback |

SynonymLearner는 동의어 데이터 자체를 키우는 도구.
FallbackMapper는 매핑 실패를 안전하게 처리하는 안전망.

**검증 도구**

| 클래스 | 파일 | 핵심 개념 |
|--------|------|-----------|
| SumValidator | sumValidator.py | BS/IS/CF 회계 공식 검증. 자산=부채+자본, 매출총이익=매출-원가, CF합계=영업+투자+재무. 허용 오차 1%. 매핑이 정확한지 숫자로 증명 |
| MappingQualityChecker | qualityCheck.py | 실제 DART parquet 데이터로 매핑률/신뢰도/재무제표별 분석/표준화 품질 측정. 종합 등급 부여 (≥95% 우수) |

**통합 진입점**

| 클래스 | 파일 | 핵심 개념 |
|--------|------|-----------|
| FinanceSearch | search.py | v6 데이터 로더(_dataLoader) + StandardMapper 결합. timeseries/timeseriesStandard/compareByStandardId API 제공. 전 종목 표준ID 기준 비교 가능 |

### 데이터 흐름도

```
standardAccounts.json ──→ parquetBuilder ──→ standardAccounts.parquet
         │                                          │
         └──→ StandardMapper ←── learnedSynonyms.json
                    │                    ↑
                    v                    │ (학습 결과 저장)
              ParquetMapper              │
                    │                    │
                    ├── 매핑 성공 ───→ snakeId 반환
                    │
                    ├── 매핑 실패 ───→ FallbackMapper ───→ other_xxx 반환
                    │
                    └── 미매칭 수집 ──→ SynonymLearner
                                          │
                                          ├── 자동승인 (≥95% 유사도)
                                          └── 수동검토 (exportUnmatched → 사람 → importApproved)
                                                    │
                                                    v
                                          learnedSynonyms.json 갱신
                                                    │
                                                    v
                                          accountMappings.json 재병합 (standardAccounts + learnedSynonyms)

검증 흐름:
  매핑 결과 ──→ SumValidator (회계 공식 검증)
  매핑 결과 ──→ QualityCheck (매핑률/신뢰도 리포트)
```

### dartlab mapper.py와의 관계

dartlab은 이 v8 시스템 중 **StandardMapper의 단순 버전만** 흡수한 상태.

| v8 기능 | dartlab 상태 |
|---------|-------------|
| dict lookup (korName → snakeId) | mapper.py에 흡수됨 (accountMappings.json 사용) |
| ID_SYNONYMS, ACCOUNT_NAME_SYNONYMS, CORE_MAP | mapper.py에 하드코딩 |
| SNAKE_ALIASES (시계열 snakeId 병합) | pivot.py에 흡수됨 |
| 컨텍스트 매핑 (industry, statementKind) | **미흡수** |
| Fallback (other_xxx) | **미흡수** — 미매핑 → None → 시계열에서 제외 |
| SynonymLearner (동의어 자동 학습) | **미흡수** |
| SumValidator (합계 검증) | **미흡수** |
| QualityCheck (품질 리포트) | **미흡수** |
| OntologyMapper (OWL) | 흡수 불필요 (실험적) |

---

## 매핑 파이프라인 진화 과정

### v6 (eddmpython 원본)
- `config.py`에 ID_SYNONYMS, ACCOUNT_NAME_SYNONYMS 하드코딩
- account_id prefix 제거 → 동의어 통합 → 한글명 정규화
- 매핑 결과물: `learnedSynonyms.json` (자동 학습으로 축적)

### v7 (= v8/standardMapping.py)
- `standardAccounts.json` + `learnedSynonyms.json` 2파일 조합
- StandardMapper: korName 직접 매칭 → synonym 매칭 → 실패
- 신뢰도 개념 도입: standard=1.0, synonym=0.9, none=0.0

### v8 (= v8/parquetMapper.py, ontologyMapper.py)
- **ParquetMapper** — standardAccounts.parquet + learnedSynonyms.json, Polars 기반
  - 컨텍스트 매핑: industry(산업코드), statementKind(재무제표종류)로 정밀 매칭
  - Fallback: 미매핑 계정 → other_xxx 로 분류 (재무제표 합계 보존)
  - 로딩 속도 100배 빠름 (5초 → 0.05초)
- **OntologyMapper** — OWL 온톨로지 기반 (owlready2 의존)
  - 실험적, 프로덕션에서는 ParquetMapper 사용 권장
- **SynonymLearner** — 종목 분석 → 미매칭 수집 → 유사도 기반 후보 제안 → 학습
- **SumValidator** — BS/IS/CF 합계 공식 검증
- **QualityCheck** — 매핑률, 신뢰도 분포, 재무제표별 분석

### dartlab 현재 (= mapper.py)
- v6 파이프라인을 간결하게 재현한 단일 파일
- 7단계: prefix 제거 → ID_SYNONYMS → ACCOUNT_NAME_SYNONYMS → CORE_MAP → accountMappings.json → 괄호 제거 fallback → None
- v8의 컨텍스트 매핑, Fallback, SynonymLearner, SumValidator는 **아직 미흡수**

---

## 현재 매핑 수준 (dartlab mapper.py 기준)

### 매핑 데이터 규모

| 계층 | 항목 수 | 역할 |
|------|---------|------|
| ID_SYNONYMS | 59개 | 영문 XBRL ID 동의어 통합 |
| ACCOUNT_NAME_SYNONYMS | 106개 | 한글명 동의어 통합 |
| CORE_MAP | 38개 | 핵심 계정 오버라이드 (영문 23 + 한글 15) |
| accountMappings.json | 34,175개 | standardAccounts(3,402) + learnedSynonyms(31,493) 병합 |
| SNAKE_ALIASES (pivot.py) | 17개 | 시계열 단위 snakeId 병합 |

### 핵심 계정 (CORE_MAP이 보장하는 21개)

| snakeId | 용도 |
|---------|------|
| `revenue` | 매출액 |
| `cost_of_sales` | 매출원가 |
| `gross_profit` | 매출총이익 |
| `operating_income` | 영업이익 |
| `net_income` | 당기순이익 |
| `total_assets` | 자산총계 |
| `current_assets` | 유동자산 |
| `non_current_assets` | 비유동자산 |
| `cash_and_equivalents` | 현금및현금성자산 |
| `inventories` | 재고자산 |
| `total_liabilities` | 부채총계 |
| `current_liabilities` | 유동부채 |
| `non_current_liabilities` | 비유동부채 |
| `short_term_borrowings` | 단기차입금 |
| `long_term_borrowings` | 장기차입금 |
| `bonds` | 사채 |
| `total_equity` | 지배기업 귀속 자본 (EquityAttributableToOwnersOfParent) |
| `equity_including_nci` | 자본총계 (Equity, 비지배지분 포함) |
| `operating_cashflow` | 영업활동 CF |
| `investing_cashflow` | 투자활동 CF |
| `financing_cashflow` | 재무활동 CF |

### 미흡수 v8 기능

| 기능 | v8 파일 | 상태 |
|------|---------|------|
| 컨텍스트 매핑 (industry, statementKind) | parquetMapper.py | 미흡수 |
| Fallback 매핑 (other_xxx) | fallbackMapper.py | 미흡수 |
| 동의어 자동 학습 | synonymLearner.py | 미흡수 |
| 재무제표 합계 검증 | sumValidator.py | 미흡수 |
| 매핑 품질 리포트 | qualityCheck.py | 미흡수 |
| Parquet 기반 표준계정 조회 | parquetBuilder.py, parquetMapper.py | 미흡수 |
| OWL 온톨로지 매핑 | ontologyBuilder.py, ontologyMapper.py | 미흡수 (실험적) |

---

## 매핑 데이터 상세

### standardAccounts.json 구조
```json
{
  "_metadata": {
    "source": "DART 표준계정코드.xlsx",
    "totalAccounts": 13243,
    "industryMapping": { "0": "전체업종", "1": "제조업", "2": "은행업", ... },
    "statementKindMapping": { "1": "BS", "2": "IS", "4": "CF", "20": "공통" },
    "codeTypeMapping": { "M": "주코드", "S": "부코드" }
  },
  "accounts": [
    {
      "code": "ifrs_Revenue",
      "korName": "수익(매출액)",
      "engName": "Revenue",
      "snakeId": "revenue",
      "industry": 0,
      "codeType": "M",
      "statementKind": 2,
      "level": 1
    },
    ...
  ]
}
```

각 계정에는 industry(산업코드), statementKind(재무제표종류), level(계층)이 있어 컨텍스트 매핑이 가능.

### learnedSynonyms.json 구조
```json
{
  "_metadata": {
    "version": "1.2",
    "description": "v6 stdAccountNm → standardAccounts snakeId 동의어 매핑",
    "totalSynonyms": 31493
  },
  "synonyms": {
    "매출액": "revenue",
    "영업이익": "operating_income",
    "관계기업투자": "investments_in_associates",
    ...
  }
}
```

v6에서 전 종목 데이터를 순회하며 자동 학습한 결과물. 한글명(공백 제거) → snakeId.

### accountMappings.json 구조
```json
{
  "_metadata": {
    "description": "DART 표준계정 매핑 테이블 (korName/synonym -> snakeId)",
    "standardAccounts": 3402,
    "learnedSynonyms": 31493,
    "merged": 34175
  },
  "mappings": {
    "매출액": "revenue",
    "Revenue": "revenue",
    ...
  }
}
```

standardAccounts의 korName(3,402개) + learnedSynonyms(31,493개)를 병합한 것.
dartlab의 mapper.py가 직접 사용하는 파일.

---

## dartlab mapper.py 매핑 흐름 (상세)

```
입력: (account_id, account_nm)
  │
  ├─ 1. prefix 제거: ifrs-full_Revenue → Revenue
  │
  ├─ 2. ID_SYNONYMS 적용: RevenueFromOperations → Revenue
  │
  ├─ 3. ACCOUNT_NAME_SYNONYMS 적용: "영업이익(손실)" → "영업이익"
  │
  ├─ 4. CORE_MAP 조회 (normalizedId 먼저, 없으면 normalizedNm)
  │   Revenue → "revenue" ✓ 반환
  │
  ├─ 5. accountMappings.json 조회 (normalizedId 먼저, 없으면 normalizedNm)
  │   "관계기업투자및대여금" → "investments_in_associates_and_loans" ✓ 반환
  │
  ├─ 6. 괄호 제거 후 재조회
  │   "영업이익(손실)" → "영업이익" → accountMappings.json에서 조회
  │
  └─ 7. 모두 실패 → None (미매핑, 시계열에서 조용히 제외)
```

### SNAKE_ALIASES (pivot.py, 매핑 후 시계열 병합)
```
sales           → revenue
net_profit      → net_income
total_stockholders_equity → total_equity
noncurrent_assets → non_current_assets
cash_and_cash_equivalents → cash_and_equivalents
tangible_assets → ppe
cash_flows_from_operating_activities → operating_cashflow
... (17개)
```

---

## v8 기능별 상세 설명

### 1. ParquetMapper (parquetMapper.py) — 컨텍스트 기반 매핑

dartlab의 mapper.py와 달리 **산업코드(industry)와 재무제표종류(statementKind)를 활용한 정밀 매핑**.

같은 한글명이라도:
- 은행업(industry=2)에서의 "수익"과 제조업(industry=1)에서의 "수익"은 다른 표준계정에 매핑될 수 있음
- BS(statementKind=1)의 계정과 IS(statementKind=2)의 계정은 같은 이름이라도 다를 수 있음

매핑 순서:
1. learnedSynonyms.json에서 snakeId 조회 (공백 제거)
2. 괄호 제거 후 재조회
3. snakeId 발견 시 → standardAccounts.parquet에서 컨텍스트(industry, statementKind) 점수 매기기
4. snakeId 미발견 시 → DataFrame korName 직접 검색 + 컨텍스트 점수
5. 모두 실패 시 → FallbackMapper로 other_xxx 분류

신뢰도 점수 체계:
- synonym: 0.7~0.9
- synonym+context: 1.0+ (industry 매칭 +0.2, statementKind 매칭 +0.2)
- ontology (DataFrame 직접매칭): 1.0+
- fuzzy: 0.5~
- fallback: 0.3

### 2. FallbackMapper (fallbackMapper.py) — 미매핑 안전망

**재무제표 합계 정확성**을 위해 미매핑 계정도 적절한 분류로 포함시킴.

재무제표별 키워드 → fallback snakeId 규칙:
- **BS**: "자산" → other_noncurrent_assets, "현금" → other_current_assets, "부채" → other_noncurrent_liabilities, "자본" → other_equity_components, ...
- **IS**: "매출" → revenue, "비용" → other_operating_expenses, "손익" → net_income, ...
- **CF**: "영업활동" → cash_flows_from_operating_activities, "차입" → proceeds_from_borrowings, ...
- **CIS**: "기타포괄손익" → other_comprehensive_income, ...
- **SCE**: "배당" → dividends, "자기주식" → treasury_stock_transactions, ...

2단계 fallback:
1. 키워드 매칭 (우선순위 순서)
2. 키워드 없으면 재무제표 유형별 기본값 (BS → 자산/부채/자본 키워드 체크, IS → 수익/비용 체크, CF → other_adjustments)

### 3. SynonymLearner (synonymLearner.py) — 동의어 자동 학습

**학습 사이클**:
1. `analyzeCompany(stockCode)` — 종목 데이터에서 매칭률 분석
2. `suggestMappings(unmatchedNames)` — 미매칭에 대해 SequenceMatcher로 유사도 기반 후보 제안
3. `learnSynonym(stdAccountNm, snakeId)` — 승인된 매핑을 learnedSynonyms.json에 추가
4. `autoLearn(stockCodes, threshold=0.95)` — 높은 유사도(≥95%) 자동 승인

수동 학습 워크플로우:
1. `exportUnmatched(outputPath)` — 미매핑 리스트 + 후보 제안을 JSON으로 내보내기
2. 사람이 JSON에서 `"approved": "snakeId"` 입력
3. `importApproved(inputPath)` — 승인된 매핑 가져와서 학습

### 4. SumValidator (sumValidator.py) — 재무제표 합계 검증

검증 항목:
- BS: total_assets = total_liabilities + total_equity
- BS: total_assets = current_assets + noncurrent_assets
- BS: total_liabilities = current_liabilities + noncurrent_liabilities
- IS: gross_profit = revenue - cost_of_sales
- IS: net_income = profit_before_tax - income_tax_expense
- CF: net_change = operating + investing + financing

허용 오차: 1% (tolerance=0.01)

### 5. QualityCheck (qualityCheck.py) — 매핑 품질 종합 리포트

6개 분석 항목:
1. 매핑률 분석 (총/성공/실패, 신뢰도 분포)
2. Confidence 분포 (0.0~1.0 히스토그램)
3. 미매핑 계정 상위 20개 (빈도순)
4. 표준화 품질 (같은 개념의 변형이 같은 snakeId로 수렴하는지)
5. 재무제표별 매핑률 (BS/IS/CIS/CF/SCE)
6. 종합 평가 (≥95% 우수, ≥90% 양호, ≥80% 보통, <80% 개선 필요)

---

## 향후 작업

STATUS.md 섹션 4 "남은 과제" 참조

---

## 동의어 매핑 수 상위 snakeId

accountMappings.json에서 하나의 snakeId에 매핑되는 키(한글명/영문ID) 수 상위:

| snakeId | 동의어 수 |
|---------|---------|
| investments_in_subsidiaries | 1,104 |
| investments_in_associates | 884 |
| sga (판관비) | 828 |
| bonds (사채) | 811 |
| financial_assets_at_fvoci | 710 |
| other_current_financial_assets | 702 |
| tangible_assets (유형자산) | 677 |
| gainslosses_in_subsidiaries | 616 |

이 숫자는 DART에 상장된 회사마다 같은 계정을 다른 이름으로 표기하기 때문.
예: "종속기업투자", "종속기업투자주식", "종속기업에대한투자자산" 등이 모두 `investments_in_subsidiaries`에 매핑.

---

## 주의사항

### total_equity vs equity_including_nci

- `total_equity` = EquityAttributableToOwnersOfParent (지배기업 귀속 자본)
- `equity_including_nci` = Equity (자본총계, 비지배지분 포함)

CORE_MAP에서:
- "자본총계" → equity_including_nci
- "지배기업 소유주지분" → total_equity

ratios.py는 ROE 계산 시 total_equity를 사용 (지배기업 기준).

### 은행/금융업 특수성

은행업은 제조업과 다른 계정 체계:
- revenue, current_assets, cost_of_sales 등이 없을 수 있음
- 영업이익 대신 영업손익, 매출액 대신 이자수익/수수료수익
- ratios.py에서 해당 계정이 없으면 None 반환 (에러 아님)

### DART 계정명 공백/괄호 문제

같은 계정인데 공백이 다른 경우:
- "영업 이익" vs "영업이익"
- ACCOUNT_NAME_SYNONYMS에 "영업 이익": "영업이익" 등록

괄호 안 내용이 다른 경우:
- "영업이익(손실)" vs "영업이익"
- ACCOUNT_NAME_SYNONYMS에 등록 + mapper.py의 괄호 제거 fallback
