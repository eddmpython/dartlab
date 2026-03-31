# Search *(alpha)*

전체 공시 원문 시맨틱 검색 엔진.

## 구조

```
core/search/
├── __init__.py       # search() 통합 진입점 — 종목명 + 공시 시맨틱 검색
├── vectorStore.py    # GPU 임베딩 + LanceDB 검색 + HF push/pull

providers/dart/openapi/
├── allFilingsCollector.py  # 2단계 수집기 (L1, DART API 의존)
```

## 2단계 수집

```
Phase 1: collectMetaRange()  ← 목록만 (일자당 API ~15회, 가볍다)
  → {date}_meta.parquet 저장

Phase 2: fillContent()       ← 원문 채우기 (건당 API 1회, 무겁다)
  → _parseSections() 또는 HTML fallback
  → {date}.parquet로 승격, _meta 삭제
```

DART API 일일 한도: 키당 10,000건. 목록은 키 1개로 5년치 가능, 원문은 키 소비 큼.

## search() API

```python
import dartlab

dartlab.search("유상증자 결정")                     # 공시 시맨틱 검색
dartlab.search("대표이사 변경", corp="005930")       # 종목 필터
dartlab.search("전환사채", start="20240101")         # 기간 필터
```

- `dartlab.search()`는 공시 원문 검색 전용
- 종목 찾기는 `dartlab.Company("삼성전자")` 또는 `dartlab.searchName("삼성전자")`
- 결과에 dartUrl 컬럼 포함 — DART 공시 뷰어 바로 이동

## 벡터 임베딩

- **모델**: `jhgan/ko-sroberta-multitask` (768d, 한국어)
- **GPU 자동 감지**: CUDA > MPS > CPU
- **청킹**: 섹션 단위, 10,000자 초과 시 분할
- **저장**: LanceDB (파일 기반, Arrow 호환)
- **증분**: 기수집 날짜/원문/벡터 건너뜀
- **압축**: LanceDB IVF-PQ (검색용) + TurboQuant (배포용)

## 압축 전략 — LanceDB + TurboQuant 하이브리드

### 실측 결과 (2026-03-31, 9,033벡터)

| 항목 | LanceDB (원본) | TurboQuant 4bit |
|------|:-----------:|:------------:|
| 저장 크기 | 96.5MB | **6.6MB** |
| 검색 속도 | **58ms** | 329ms |
| 검색 품질 | 동등 | 동등 |

**결론**: 검색은 LanceDB가 6배 빠르고, 저장은 TurboQuant가 15배 작다.

### 하이브리드 전략

```
HF 배포: TurboQuant 압축 벡터 (6.6MB) ← 다운로드 부담 최소
로컬 검색: LanceDB 인덱스 (자동 빌드) ← 검색 속도 58ms
```

- `pushIndex()`: LanceDB → TurboQuant 압축 → HF 업로드 (작은 파일)
- `pullIndex()`: HF 다운로드 → decompress → LanceDB 인덱스 자동 빌드
- 검색은 항상 LanceDB — TurboQuant는 전송 계층에서만 사용

### TurboQuant 패키지

- `turboquant-vectors` (pip install, numpy only)
- `compress(vectors, bits=4)` → `search(compressed, query, top_k)` API
- ANN 인덱스 미지원 (brute-force만) → 대규모 직접 검색에는 부적합
- 배포용 압축/해제에 적합

GPU 필요 → GitHub Actions 부적합 → 로컬 빌드 후 수동 push.

## 검색 아키텍처 — 2계층 하이브리드

실험 105에서 5가지 방법론 비교 후 결정:

```
L1: LanceDB FTS (BM25) — 모델 불필요, 즉시 반환
L2: 벡터 ANN — 백그라운드 모델 로딩 완료 후 의미 검색 보강
합산: RRF (Reciprocal Rank Fusion)
```

첫 검색은 FTS로 즉시 반환하고, 모델 로딩이 완료되면 벡터 검색으로 자동 보강.

### 실험 105 결과 요약

| 방법 | precision@5 | cold start |
|------|:---:|:---:|
| BM25(FTS) | 71% | 0ms |
| SemanticMap | 68% | 0ms |
| Model2Vec(DART증류) | 67% | 265ms |
| **하이브리드(FTS+벡터)** | **~80%** | **190ms** |
| 임베딩 단독(ko-sroberta) | 83% | 12,700ms |

부산물: DART 공시 Taxonomy(15카테고리), 동반공시 PMI 그래프, DART 특화 Model2Vec 모델(24.7MB)

## 성능 실측 (2026-03-31)

| 항목 | 수치 |
|------|------|
| 파싱 성공률 | 99.4% |
| precision@5 (하이브리드) | ~80% |
| Warm 검색 | 58ms (GPU) |
| 임베딩 속도 | 193 chunks/sec (RTX 4060) |

## 저장

```
data/dart/allFilings/{date}.parquet          # 원문
data/dart/allFilings/{date}_meta.parquet     # 목록만 (원문 미수집)
data/dart/vectorIndex/filings.lance/         # LanceDB
```

## 관련 코드

- `src/dartlab/core/search/__init__.py` — 통합 진입점
- `src/dartlab/core/search/vectorStore.py` — 벡터 엔진
- `src/dartlab/providers/dart/openapi/allFilingsCollector.py` — 수집기
