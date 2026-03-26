# DART Finance Development Guide

본체 위치:
- `src/dartlab/providers/dart/finance/`
- 공통 비율 계산:
  - `src/dartlab/core/finance/ratios.py`
- 공통 재무 분석 아키텍처 상세: `src/dartlab/core/finance/DEV.md`

## authoritative surface

- `BS`
- `IS`
- `CIS`
- `CF`
- `SCE`

모두 `Company.finance`의 필수 statement다.

## engine spec

- 원본: `data/dart/finance/{stockCode}.parquet`
- 기간: `2015~`
- 단위: 원
- canonical 축:
  - `BS`
  - `IS`
  - `CIS`
  - `CF`
  - `SCE`
- `CIS`는 raw origin으로 유지하되 company 수평화에서는 `IS`와 함께 소비된다.

핵심 피벗:
- `timeseries`
- `annual`
- `cumulative`
- `sce`
- `sceMatrix`
- `ratios`
- `ratioSeries`

매핑 source of truth:
- `src/dartlab/providers/dart/finance/mapper.py`
- `src/dartlab/providers/dart/finance/mapperData/accountMappings.json`

## 현재 정확성 기준

- `YoY`
  - sign-flip(`+→-`, `-→+`)은 `None`
- equity
  - `totalEquity = total_stockholders_equity` 우선
  - `ownersEquity` 별도 유지
  - `ROE`는 `ownersEquity` 기준
- EBITDA
  - `CF`의 감가상각 계정 우선
  - 없을 때만 추정 fallback
  - `ebitdaEstimated` 플래그 유지
- `Q1 CF`
  - standalone 유지
- `SCE`
  - unmapped row도 generic key로 보존

## public contract

- `Company.finance`의 statement surface는 DataFrame 중심이다.
- `BS / IS / CIS / CF / SCE`는 모두 `pl.DataFrame | None`
- raw/helper 성격의 series 구조는 engine 내부 helper로 취급한다.

## 운영 원칙

- 재무 정확성 변경은 먼저 synthetic test로 고정한다.
- `ratios.py`, `pivot.py`, `mapper.py`를 건드리면 전종목 검증보다 먼저 fixture/sce 테스트를 통과시킨다.
