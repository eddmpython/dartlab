---
id: engines.edgar.docs
title: edgar.docs — SEC 공시 sections + form-native payload
kind: curated
scope: builtin
status: observed
category: engines
purpose: edgar.docs 는 SEC EDGAR 원문 공시 (10-K · 10-Q · 20-F · 40-F) 를 섹션 단위 parquet 로 저장하고 form-native text 비교 계층을 제공하는 sub-engine 이다. `sections(stockCode, sinceYear)` 가 topic × period 매트릭스를 빌드 — topic namespace 는 `form_type::topicId`. 시장 진입점은 dartlab.providers.edgar.Company 이고 dartlab.Company 가 이 EDGAR 진입점을 통합 facade 로 감싼다. 트리거 — '10-K sections', 'SEC docs', 'sectionMappings', 'edgar parquet'.
whenToUse:
  - 10-K · 10-Q · 20-F · 40-F section 추출
  - form_type::topicId horizontal view
  - EDGAR docs parquet 스키마
  - dartlab.providers.edgar.Company panel/topic view
  - GitHub Release `data-edgar-docs` 배포
inputs:
  - SEC EDGAR API 또는 로컬 parquet (`data/edgar/docs/{ticker}.parquet`)
  - ticker (예 — AAPL · MSFT)
  - sinceYear 옵션 (기본 2009)
outputs:
  - topic × period DataFrame
  - 표준 공통 컬럼 (year · filing_date · report_type · period_key · section_order · section_title · section_content)
  - EDGAR 전용 메타 (cik · company_name · ticker · accession_no · form_type · filing_url)
capabilityRefs:
  - Company.panel
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.edgar
  - engines.panel
sourceRefs:
  - dartlab://skills/engines.edgar.docs
requiredEvidence:
  - ticker
  - form_type
  - period_key
  - accession_no
  - executionRef
  - sourceRef
expectedOutputs:
  - topic × period 매트릭스 (form_type::topicId 행)
  - 같은 연도 정렬 — annual → Q3 → Q2 → Q1
  - markdown table 보존 payload
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
failureModes:
  - 6-K 를 기본 docs 배치 대상으로 포함하는 시도 (정책상 제외)
  - 40-F 를 structured split 으로 강제 (annual Full Document fallback 정책)
  - 저장 시점에 HTML table 을 plain text 로 변환 (markdown 보존 의무)
  - 로더가 SEC EDGAR API 직접 수집 단계 건너뛰기 (parquet → release → API 3 단계)
forbidden:
  - "전체 mirror 다운로드 호출 — issuer-deduped 의무 (downloadListedEdgarDocs(limit=2000))"
  - "Full Document fallback 을 기본 흐름으로 사용"
  - "EDGAR 전용 컬럼 (cik · accession_no · filing_url) 제거"
  - "DART 와 EDGAR 의 저장 스키마를 강제 통일 (공통 뷰에서만 맞춘다)"
examples:
  - dartlab.Company('AAPL').panel('10-K::item1Business') → item1Business 본문
  - downloadListedEdgarDocs(limit=2000) → 배치 progress (forms_found · rows_saved · failure_kind)
  - 057 실험 — table markdown fidelity 감시 + 057-015 readiness 리포트
procedure:
  - dartlab.providers.edgar.docs.sections.sections(ticker, sinceYear=None) — topic × period DataFrame.
  - loadData(ticker, category="edgarDocs") — 로컬 → release → SEC API 3 단계 fallback.
  - 배치 수집 — `downloadListedEdgarDocs(limit=2000)` issuer-deduped.
  - sectionMappings.json — stable topic id SSOT.
linkedSkills:
  - engines.edgar
  - engines.panel
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-05-12'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 엔진 역할

`edgar.docs` 는 SEC EDGAR 원문 공시를 섹션 단위 parquet 로 저장하고, `sections()` 까지 포함한 form-native text 비교 계층을 제공한다. 현재 package 계약은 `10-K`, `10-Q`, `20-F`, `40-F` 를 `section_title`, `section_content`, `period_key` 중심으로 읽고, `form_type::topicId` 기준 horizontal view 를 만드는 것이다.

시장 진입점은 `dartlab.providers.edgar.Company` 다. 루트 `dartlab.Company` 가 이 EDGAR 진입점을 통합 facade 로 감싼다.

## 공개 호출 방식

```python
import dartlab
from dartlab.providers.edgar.docs.sections import sections
from dartlab.frame.dataLoader import loadData

# 사용자 진입점 — Company facade
c = dartlab.Company("AAPL")
df = c.panel("10-K::item1Business")    # 단일 EDGAR topic DataFrame

# 내부 진입점 — provider 직접
df = sections("AAPL", sinceYear=2015)  # 2015 이후만

# 로더 — 3 단계 fallback
docs = loadData("AAPL", category="edgarDocs")
docs2 = loadData("MSFT", category="edgarDocs", sinceYear=2015)
```

## 호출 동작

### 데이터 소스

- **원본** — `data/edgar/docs/{ticker}.parquet`
- **GitHub Release** — `data-edgar-docs`
- **기본 단위** — filing 별 section row
- **기본 파일명** — ticker 기준 (`AAPL.parquet`, `MSFT.parquet`)
- **기본 수집 시작점** — `2009 년`
- **기본 수집 범위** — `10-K`, `10-Q`, `20-F`, `40-F` 전 기간

### 로더 동작

`loadData("AAPL", category="edgarDocs")`:
1. 로컬 parquet 우선
2. 없으면 GitHub Release 시도
3. 없으면 SEC EDGAR API 에서 `2009 년부터` 직접 수집

추가 범위 제어 — `loadData(..., category="edgarDocs", sinceYear=2015)` 처럼 시작 연도 공개 파라미터.

### sections 계약

- `dartlab.providers.edgar.docs.sections.sections(stockCode, sinceYear=None)`
  - 반환 — `topic(행) × period(열)` DataFrame
  - topic namespace — `form_type::topicId`
  - 기간 정렬 — 같은 연도에서는 annual → Q3 → Q2 → Q1
- `10-K`, `10-Q`, `20-F` — structured split 대상
- `40-F` — 현재 annual `Full Document` fallback 으로 저장
- `Full Document` — hard fallback 으로만 남기고 기본 흐름에서는 최소화
- `sectionMappings.json` — stable topic id 의 source of truth

### 테이블 보존 계약

- 저장 시점에 HTML table 은 markdown table 로 보존
- `section_content` 는 text + markdown table 을 함께 보존하는 source-native payload
- table-only fidelity 는 `057` 실험에서 계속 감시

### 대량 수집 정책

- `downloadListedEdgarDocs(limit=2000)` 처럼 issuer-deduped collectible universe 를 기준으로 배치 수집.
- 배치 수집은 요청 폭주를 막기 위해 일정 건수마다 휴지 시간을 둔다.
- `6-K` 는 기본 docs 배치 대상에서 제외.
- 배치 progress 는 ticker · cik · status 뿐 아니라 `forms_found`, `rows_saved`, `filings_saved`, `full_document_rows`, `table_rows`, `failure_kind` 까지 남긴다.
- readiness 리포트는 `057-015` 에서 progress 와 로컬 parquet 품질을 함께 요약.

## 대표 반환 형태

### 최소 공통 스키마

모든 EDGAR docs parquet 가 반드시 포함해야 하는 컬럼:

| 컬럼 | 설명 |
|---|---|
| `year` | 사업연도 |
| `filing_date` | 제출일 |
| `report_type` | 보고서 유형 (10-K · 10-Q · 20-F · 40-F) |
| `period_key` | 기간 식별자 |
| `section_order` | 섹션 순서 |
| `section_title` | 섹션 제목 |
| `section_content` | 본문 payload (text + markdown table) |

### EDGAR 전용 보존 컬럼

| 컬럼 | 설명 |
|---|---|
| `cik` | SEC 등록 번호 |
| `company_name` | 발행사명 |
| `ticker` | 거래 심볼 |
| `accession_no` | filing 고유 ID |
| `form_type` | 양식 (10-K / 10-Q / 20-F / 40-F) |
| `filing_url` | SEC 원본 URL |

### sections() DataFrame 구조

```text
form_type::topicId          │ 2024-Q4 │ 2024-Q3 │ 2024-Q2 │ 2024-Q1 │ 2023-Q4 │ …
10-K::item1Business         │ "…"     │ null    │ null    │ null    │ "…"     │
10-Q::item2MDA              │ null    │ "…"     │ "…"     │ "…"     │ null    │
20-F::item3KeyInformation   │ "…"     │ null    │ null    │ null    │ "…"     │
```

## DART docs 와의 관계

- 완전 동일 스키마를 강제하지 않는다.
- 공통 소비 계층은 `year`, `section_title`, `section_content` 와 문서 식별자 fallback 만 가정.
- 문서 식별자 — DART `rcept_no`, EDGAR `accession_no` 각각 사용.
- 기업명 — DART `corp_name`, EDGAR `company_name` 각각 사용.
- 로더 공통 뷰에서는 `source`, `entity_id`, `doc_id`, `doc_date`, `doc_url`, `period_key` 를 추가해 비교 축만 맞춘다.

## source-native 원칙

- 저장 parquet 는 EDGAR 메타를 그대로 유지.
- `form_type`, `accession_no`, `filing_url`, `cik`, `period_end` 같은 EDGAR 고유 컬럼은 제거하지 않는다.
- DART 와의 비교 가능성은 저장 포맷 통일이 아니라 로더 공통 뷰에서 확보.

## 현재 readiness 기준

- local corpus 기준 `sections()` 무에러
- candidate coverage **100%**
- raw coverage 는 최신 표본 기준 계속 감시, 새 long-tail 은 `057` 루프에서 흡수
- `10-K`, `10-Q`, `20-F` 모두 structured split
- `40-F` annual fallback 허용
- table markdown regression 없음
- progress 기준 failure taxonomy 가 운영적으로 해석 가능함

## 후속 과제

- `dartlab.providers.edgar.Company` 연동 (M-track P-PR6/7/8 — XBRL 깊이 + 10-K extractor + Form 4 / DEF 14A / 8-K)
- registry, AI, export, server 노출
- `business`, `mdna`, `riskFactors` 같은 개별 공개 모듈

## 기본 검증

EDGAR docs 변경 시 동기화 경로:

- 위 "table markdown regression 없음" · "40-F annual fallback 허용" · "progress 기준 failure taxonomy" 가 회귀 가드.
- `dartlab.providers.edgar.docs` 공개 메서드·반환 컬럼·실패 taxonomy 가 바뀌면 본 sub-spec + base `engines.edgar` 동시 갱신.
- 결손 표시: 본문 fetch 실패 시 빈 string X → `flags.docs_fetch_status` 에 실패 사유 명시. failure taxonomy 누락 시 운영 해석 불가능.

## 변경 이력

- 2026-05-12 — `providers/edgar/docs/SPEC.md` → 본 sub-spec 통합 (Skill OS 운영 SSOT 승격)
