# EDGAR OpenAPI Development Guide

## 목표

- 공개 인터페이스는 `from dartlab import OpenEdgar`
- SEC public API surface를 source-native로 그대로 노출
- saver만 dartlab 저장 규약에 맞춘다

## 범위

- 포함:
  - issuer search / resolve
  - submissions raw JSON
  - filings convenience DataFrame
  - companyfacts / companyconcept / frames raw JSON
  - docs / finance saver
- 제외:
  - derived `report` 계층
  - docs/finance 로딩 fallback

## 설계 원칙

1. `OpenEdgar` facade 하나로 호출
2. raw endpoint는 dict 반환
3. convenience view만 DataFrame 반환
4. 저장 시 docs는 `edgarDocs`, finance는 raw companyfacts parquet 유지
5. 기존 `Company`, `docs`, `finance` 엔진이 저장물 소비를 계속 담당

## 저장 규약

- `saveDocs()` → `data/edgar/docs/{ticker}.parquet`
  - 기존 `fetchEdgarDocs()`가 생산하는 schema 그대로
  - canonical raw consumer contract:
    - `cik`, `company_name`, `ticker`, `year`, `filing_date`, `period_end`, `accession_no`, `form_type`, `report_type`, `period_key`, `section_order`, `section_title`, `filing_url`, `section_content`
- `saveFinance()` → `data/edgar/finance/{cik}.parquet`
  - raw companyfacts fact rows
  - 핵심 컬럼: `cik`, `entityName`, `namespace`, `tag`, `label`, `unit`, `val`, `fy`, `fp`, `form`, `filed`, `frame`, `start`, `end`, `accn`

## 저장 안전장치

- saver는 최종 parquet에 바로 쓰지 않는다
- 임시 파일에 저장 → schema gate → consumer smoke check → 최종 교체 순서로 진행
- 검증 실패 시 기존 parquet를 보존하고 예외를 올린다
- saved parquet는 raw consumer contract이며, `Company/docs/finance` 엔진이 그대로 읽을 수 있어야 한다

## 네이밍

- canonical: `OpenDart`, `OpenEdgar`
- compatibility alias: `Dart`
