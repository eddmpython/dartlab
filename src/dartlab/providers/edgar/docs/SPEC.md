# edgar/docs 엔진 스펙

## 역할

SEC EDGAR 원문 공시를 섹션 단위 parquet로 저장하고, `sections()`까지 포함한 form-native text 비교 계층을 제공한다.
현재 package 계약은 `10-K`, `10-Q`, `20-F`, `40-F`를 `section_title`, `section_content`, `period_key` 중심으로 읽고, `form_type::topicId` 기준 horizontal view를 만드는 것이다.

시장 진입점은 `dartlab.engines.edgar.Company`다.
루트 `dartlab.Company`가 이 EDGAR 진입점을 통합 facade로 감싼다.

핵심 근거 실험은 `experiments/055_edgarDocs/`와 `experiments/057_edgarSectionMap/`이다.

## 데이터 소스

- **원본**: `data/edgar/docs/{ticker}.parquet`
- **GitHub Release**: `data-edgar-docs`
- **기본 단위**: filing별 section row
- **기본 파일명**: ticker 기준 (`AAPL.parquet`, `MSFT.parquet`)
- **기본 수집 시작점**: `2009년`
- **기본 수집 범위**: `10-K`, `10-Q`, `20-F`, `40-F` 전 기간

## 로더 동작

- `loadData("AAPL", category="edgarDocs")`
  - 로컬 parquet 우선
  - 없으면 GitHub Release 시도
  - 없으면 SEC EDGAR API에서 `2009년부터` 직접 수집
- 추가 범위 제어가 필요하면 `loadData(..., category="edgarDocs", sinceYear=2015)`처럼 시작 연도를 공개 파라미터로 바꿀 수 있다.

## sections 계약

- `dartlab.engines.edgar.docs.sections.sections(stockCode, sinceYear=None)`
  - 반환 형식: `topic(행) × period(열)` DataFrame
  - topic namespace: `form_type::topicId`
  - 기간 정렬: 같은 연도에서는 annual → Q3 → Q2 → Q1 순
- `10-K`, `10-Q`, `20-F`는 structured split 대상이다.
- `40-F`는 현재 annual `Full Document` fallback으로 저장한다.
- `Full Document`는 hard fallback으로만 남기고 기본 흐름에서는 최소화한다.
- `sectionMappings.json`은 stable topic id의 source of truth다.

## 테이블 보존 계약

- 저장 시점에 HTML table은 markdown table로 보존한다.
- `section_content`는 text + markdown table을 함께 보존하는 source-native payload다.
- table-only fidelity는 `057` 실험에서 계속 감시한다.

## 대량 수집 정책

- `downloadAll("edgarDocs")`는 지원하지 않는다.
- 대신 `downloadListedEdgarDocs(limit=2000)`처럼 issuer-deduped collectible universe를 기준으로 배치 수집한다.
- 배치 수집은 요청 폭주를 막기 위해 일정 건수마다 휴지 시간을 둔다.
- `6-K`는 기본 docs 배치 대상에서 제외한다.
- 배치 progress는 ticker/cik/status뿐 아니라 `forms_found`, `rows_saved`, `filings_saved`, `full_document_rows`, `table_rows`, `failure_kind`까지 남긴다.
- readiness 리포트는 `057-015`에서 progress와 로컬 parquet 품질을 함께 요약한다.

## 최소 공통 스키마

모든 EDGAR docs parquet는 아래 공통 소비 컬럼을 반드시 포함한다.

- `year`
- `filing_date`
- `report_type`
- `period_key`
- `section_order`
- `section_title`
- `section_content`

EDGAR 전용 보존 컬럼은 다음과 같다.

- `cik`
- `company_name`
- `ticker`
- `accession_no`
- `form_type`
- `filing_url`

## DART docs와의 관계

- 완전 동일 스키마를 강제하지 않는다.
- 공통 소비 계층은 `year`, `section_title`, `section_content`와 문서 식별자 fallback만 가정한다.
- 문서 식별자는 DART `rcept_no`, EDGAR `accession_no`를 각각 사용한다.
- 기업명은 DART `corp_name`, EDGAR `company_name`을 각각 사용한다.
- 로더 공통 뷰에서는 `source`, `entity_id`, `doc_id`, `doc_date`, `doc_url`, `period_key`를 추가해 비교 축만 맞춘다.

## source-native 원칙

- 저장 parquet는 EDGAR 메타를 그대로 유지한다.
- `form_type`, `accession_no`, `filing_url`, `cik`, `period_end` 같은 EDGAR 고유 컬럼은 제거하지 않는다.
- DART와의 비교 가능성은 저장 포맷 통일이 아니라 로더 공통 뷰에서 확보한다.

## 현재 readiness 기준

- local corpus 기준 `sections()` 무에러
- candidate coverage `100%`
- raw coverage는 최신 표본 기준 계속 감시하고, 새 long-tail은 `057` 루프에서 흡수
- `10-K`, `10-Q`, `20-F` 모두 structured split
- `40-F` annual fallback 허용
- table markdown regression 없음
- progress 기준 failure taxonomy가 운영적으로 해석 가능함

## 후속 과제

- `dartlab.engines.edgar.Company` 연동
- registry, AI, export, server 노출
- `business`, `mdna`, `riskFactors` 같은 개별 공개 모듈
