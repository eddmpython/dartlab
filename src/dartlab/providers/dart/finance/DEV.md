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

## scanAccount / scanRatio — 전종목 배치 조회

위치: `providers/dart/finance/scanAccount.py`

전종목 × 기간 시계열을 한 번에 뽑는 배치 함수.
`dartlab.scanAccount("매출액")`, `dartlab.scanRatio("roe")` 등으로 사용.

### 2-Tier 가속 구조

```
1순위: scan/finance.parquet (프리빌드)
  → _scanAccountFromMerged(): 단일 파일에서 Polars 벡터 연산
  → 분기 0.37초, 연간 0.30초

2순위: finance/{stockCode}.parquet × 2700+ (fallback)
  → _FileProcessor + ThreadPoolExecutor 병렬
  → 분기 3초+, 연간 3초+
```

scan/finance.parquet이 없으면 `_ensureScanData()`가 HF에서 자동 다운로드(271MB).
다운로드도 실패하면 종목별 파일 순회로 fallback.

### 분기 standalone 계산 로직

- IS/CIS 1~3분기: `thstrm_amount` = 당분기 standalone
- IS/CIS 4분기: `thstrm_amount` - Q3 `thstrm_add_amount` = Q4 standalone
- BS: 시점 잔액이므로 `thstrm_amount` 그대로
- CF: IS와 동일 패턴

### scanRatio

`_RATIO_DEFS`에 정의된 비율(ROE, ROA, 영업이익률 등 13개).
내부에서 `scanAccount(분자)` / `scanAccount(분모)`를 호출하므로 가속이 자동 전파.
YoY 성장률은 `_calcYoyRatio`에서 전년 대비 변화율 계산.

### CFS/OFS 우선 로직

종목별로 연결재무제표(CFS)가 존재하면 연결만 사용, 없으면 별도(OFS) 사용.
merged 경로에서는 `hasCfsSet`으로 종목 집합을 나눠 한 번에 필터.

## 운영 원칙

- 재무 정확성 변경은 먼저 synthetic test로 고정한다.
- `ratios.py`, `pivot.py`, `mapper.py`를 건드리면 전종목 검증보다 먼저 fixture/sce 테스트를 통과시킨다.
- `scanAccount.py`의 가속 경로(`_scanAccountFromMerged`)와 fallback 경로(`_FileProcessor`)는 동일한 출력을 보장해야 한다.
- scan 프리빌드 구조 변경 시 `market/DEV.md`와 동시 갱신.
