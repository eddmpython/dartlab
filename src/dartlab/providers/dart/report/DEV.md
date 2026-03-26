# DART Report Development Guide

본체 위치:
- `src/dartlab/providers/dart/report/`

## 구조

- 28개 apiType 체계를 기준으로 본다.
- 현재 데이터 availability는 구조 축소 근거가 아니라 상태 정보다.

## engine spec

- 원본: `data/dart/report/{stockCode}.parquet`
- 기간: `2015~`
- 하나의 parquet에 `apiType` 컬럼으로 모든 report 데이터가 함께 들어간다.
- `preferredQuarter` 기준으로 annual view를 만든다.

공식 surface:
- `c.report.apiTypes`
- `c.report.availableApiTypes`
- `c.report.status()`
- `c.report.extract(apiType)`
- `c.report.extractAnnual(apiType, quarterNum=None)`
- `c.report.result(apiType, quarterNum=None)`
- `c.report.labels`

## 결과 규칙

- pivot 5개
  - `dividend`
  - `employee`
  - `majorHolder`
  - `executive`
  - `audit`
  - 기존 Result 객체 유지
- 나머지 apiType
  - `ReportResult`로 통일

## 운영 원칙

- 28개 apiType 체계는 줄이지 않는다.
- availability는 종목별/데이터별 상태로만 다룬다.
- 새 report parquet가 들어오면
  1. `availableApiTypes` 확인
  2. `status()` 회귀 확인
  3. `Company.trace()`의 primary source 일관성 확인

## Company 역할

- `report`는 sections보다 더 좋은 structured 시계열을 채우는 source다.
- `show()`에서 report topic은 `pl.DataFrame` 또는 `None` 계약을 유지한다.
- `trace()`는 report가 primary source로 선택됐는지 보여준다.
- `availableApiTypes`는 metadata-only scan이다. `extract()` 28회를 돌려 availability를 확인하지 않는다.
