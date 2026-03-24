# 090_fastSectionsViewer — 저장물 없는 sections viewer runtime 벤치

## 목표
- `sections`를 source of truth로 유지하면서, 별도 viewer 저장물 없이 사람이 읽는 공시문서형 viewer hot path를 벤치마크한다.
- 우선순위는 `API 열기`다: `/toc`, `/viewer/{topic}`, same-topic period switch의 cold/warm latency, RSS, payload bytes를 baseline과 비교한다.

## 실험 구성
- `001_viewerApiBaseline.py` — 현재 server/company viewer 경로 baseline 계측
- `002_polarsViewerRoute.py` — raw docs/report + Polars lazy scan 후보
- `003_pyarrowViewerRoute.py` — PyArrow Dataset scanner 후보
- `004_duckdbViewerRoute.py` — DuckDB parquet 후보
- `005_sectionsHybridRoute.py` — direct `sections(stockCode)` hybrid 경로 후보

## 실행 원칙
- 기본 샘플은 `safe2` (`005930`, `000660`)
- cold subprocess 3회 + warm 10회
- disk viewer artifact 생성 금지
- company 동시 로드 금지

## 결과
- 실행 샘플: `safe2` (`005930`, `000660`)
- baseline:
  - `toc` cold `7.317~7.449s`, peak `805~900MB`
  - `companyOverview` cold `7.830~7.991s`
  - `businessOverview` cold `8.392~8.720s`
  - `_sections=True` 전 case
- Polars 후보:
  - exact match `0/12`
  - 최신 parity patch 후 `toc` cold `1.733~2.004s`, peak `376~490MB`
  - `companyOverview` cold `1.744~2.181s`
  - `businessOverview` cold `2.562~3.700s`
  - docs/report mixed topic cold `1.596~1.808s`
  - `periodSwitch:businessOverview` selected period `2024Q4`
  - `toc` chapter list는 baseline과 같아졌지만 topic count와 payload exact는 미달
  - `_sections=False` 전 case
- PyArrow 후보:
  - exact match `0/12`
  - `toc` cold `2.273~2.725s`, peak `470~568MB`
  - docs topic warm/cold 모두 Polars보다 열세
- DuckDB 후보:
  - exact match `0/12`
  - 초기 `pyarrow` 의존 오류 수정 후 재실행
  - `toc` cold `2.268~2.944s`, peak `563~852MB`
  - docs topic RSS와 warm latency가 나빠 reject
- Sections hybrid 후보:
  - exact match `0/12`
  - `toc` cold `4.752~5.540s`, peak `510~666MB`
  - `companyOverview` cold `5.520~5.644s`
  - `businessOverview` cold `6.164~7.148s`
  - `dividend`, `majorHolder`도 `4.469~5.385s`로 002보다 크게 느림
  - `periodSwitch:businessOverview` selected period `2024Q3`
  - `_sections=False`는 지켰지만 hot path 후보로는 reject

## 현재 판단
- 1차 winner는 `002_polarsViewerRoute.py`
- 이유:
  - `viewer 전용 저장물` 없이 `_sections=False` 유지
  - 최신 재실행 후에도 cold latency와 RSS 모두 가장 크게 절감
  - period switch comparable period를 baseline의 `2024Q4`로 맞췄다
  - `005` direct sections hybrid보다 훨씬 낫다
- 남은 과제:
  - docs topic payload parity
  - raw table fallback과 text path metadata 정합성 향상
  - TOC topic count와 canonical block count 정합성 향상
