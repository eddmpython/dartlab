# 090_fastSectionsViewer — 저장물 없는 sections viewer runtime 벤치

## 목표
- `sections`를 source of truth로 유지하면서, 별도 viewer 저장물 없이 사람이 읽는 공시문서형 viewer hot path를 벤치마크한다.
- 우선순위는 `API 열기`다: `/toc`, `/viewer/{topic}`, same-topic period switch의 cold/warm latency, RSS, payload bytes를 baseline과 비교한다.

## 실험 구성
- `001_viewerApiBaseline.py` — 현재 server/company viewer 경로 baseline 계측
- `002_polarsViewerRoute.py` — raw docs/report + Polars lazy scan 후보
- `003_pyarrowViewerRoute.py` — PyArrow Dataset scanner 후보
- `004_duckdbViewerRoute.py` — DuckDB parquet 후보

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
  - `toc` cold `1.344~1.471s`, peak `315~364MB`
  - `companyOverview` cold `0.994~1.276s`
  - `businessOverview` cold `1.739~2.212s`
  - report topic cold `0.543~0.670s`
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

## 현재 판단
- 1차 winner는 `002_polarsViewerRoute.py`
- 이유:
  - `viewer 전용 저장물` 없이 `_sections=False` 유지
  - cold latency와 RSS 모두 가장 크게 절감
  - report topic은 baseline 대비 매우 큰 속도 이득
- 남은 과제:
  - docs topic payload parity
  - period switch comparable period를 baseline의 `2024Q4`와 맞추는 로직 보정
  - raw table fallback과 text path metadata 정합성 향상
