# Data

HuggingFace 데이터셋 관리, 수집 파이프라인, 카테고리 체계.

## HuggingFace 데이터셋

- **repo**: `eddmpython/dartlab-data`
- 단건: `loadData(stockCode, category)` → HF에서 개별 parquet 자동 다운로드 (ETag 캐시)
- 전체: `downloadAll(category)` → `huggingface_hub` snapshot_download

## DATA_RELEASES (중앙 설정)

`src/dartlab/core/dataConfig.py` 한 곳에서 관리:

| 카테고리 | 경로 | 설명 |
|----------|------|------|
| docs | dart/docs | 공시 문서 (~8GB, 2500+종목) |
| finance | dart/finance | 재무제표 (~600MB, 2700+종목) |
| report | dart/report | 정기보고서 (~320MB, 2700+종목) |
| scan | dart/scan | 전종목 횡단분석 프리빌드 |
| allFilings | dart/allFilings | 전체 공시 원문 (demo) |
| vectorIndex | dart/vectorIndex | 시맨틱 검색 벡터 인덱스 (demo) |
| edgarDocs | edgar/docs | SEC EDGAR 공시 문서 |
| edgar | edgar/finance | SEC EDGAR 재무 |

새 카테고리 추가: `DATA_RELEASES`에 한 줄 + `brand.ts` data 블록 추가.

## 수집 파이프라인 (DART)

```
dartlab collect 005930              # 단일 종목 (8분기)
dartlab collect 005930 --quarters 12
dartlab collect --stats             # 현황
```

- `ZipDocsCollector`: ZIP(document.xml) 기반 (빠름, 권장)
- `DocsCollector`: HTML 크롤링 (호환성, 느림)
- `batchCollect()`: 비동기 멀티키 병렬 (finance+report+docs)

## 3-Layer Freshness

1. **ETag**: HF 원격 vs 로컬 비교
2. **TTL**: 72시간 경과 시 갱신
3. **API**: 최근 4분기 누락 직접 조회

## 메모리 최적화

- Categorical + Int32 변환 (loadData 시 자동)
- `BoundedCache` 기본 800MB

## 관련 코드

- `src/dartlab/core/dataConfig.py` — DATA_RELEASES
- `src/dartlab/core/dataLoader.py` — parquet 캐싱, HF 동기화
- `src/dartlab/providers/dart/openapi/collector.py` — docs 수집
- `src/dartlab/providers/dart/openapi/batch.py` — 배치 수집
