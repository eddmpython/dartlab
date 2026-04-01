# Search *(alpha)*

전체 공시 원문 검색 엔진. 모델 불필요, cold start 0ms, precision 95%.

| 항목 | 내용 |
|------|------|
| 레이어 | L0 (core/search/) |
| 진입점 | `dartlab.search()` |
| 소비 | allFilings(수시공시) + docs(사업보고서) |
| 생산 | 검색 결과 + dartUrl(공시 뷰어 링크) |
| 상태 | alpha — 데이터 범위 확장 중 |

## 구조

```
core/search/
├── __init__.py       # search(), buildIndex(), rebuildIndex()
├── ngramIndex.py     # stem ID 역인덱스 (CSR + bincount)
├── derived.py        # 파생 집계 (보류 — 가치 미확정)
├── vectorStore.py    # 벡터 검색 (optional, 보강용)

providers/dart/openapi/
├── allFilingsCollector.py  # 수시공시 2단계 수집
```

## search() API

```python
import dartlab

dartlab.search("유상증자 결정")                     # 공시 검색
dartlab.search("대표이사 변경", corp="005930")       # 종목 필터
dartlab.search("전환사채", start="20240101")         # 기간 필터
```

- 모델 불필요, cold start 0ms
- 결과에 dartUrl 포함 — DART 공시 뷰어 바로 이동
- 종목 찾기는 `dartlab.searchName("삼성전자")`

## 핵심 기술 — stem ID 역인덱스

agiPath 프로젝트의 posting 방식을 적용. 세상에 없는 접근.

### Stem ID

텍스트를 bigram/trigram 토큰으로 분해하고 각 토큰에 정수 ID를 부여.
DART 공시 어휘가 제한적이라 **400만 문서에서도 ~5,500 stems**.

```
"유상증자 결정" → ["유상", "상증", "증자", "자 ", " 결", "결정", "유상증", "상증자", "증자 ", ...]
각 토큰 → stemId (정수)
```

### CSR (Compressed Sparse Row)

역인덱스를 두 numpy 배열로 저장:

```
offsets[stemId] ~ offsets[stemId+1] → docIds 범위
docIds[start:end] → 해당 stem을 포함하는 문서 ID 목록
```

scipy CSR과 동일 구조, **numpy만으로 동작** (의존성 0).
JSON 대비 8.5x 축소 (2,986KB → 350KB).

### bincount 검색

매칭 docId 배열을 `np.concatenate` → `np.bincount()`로 문서별 매칭 수 한번에 집계.
Python 루프 대비 **32x 가속** (400만 문서에서 3.5초 → 140ms).

### BM25F 필드 가중치 리랭킹

검색 결과를 report_nm/section_title 매칭 여부로 리랭킹한다.

```
report_nm에 쿼리 키워드 있으면 → score × 5
section_title에 있으면 → score × 2
```

효과: "대표이사 변경" 검색 시 사업보고서가 아닌 **대표이사변경 공시**가 1위.
인덱스 변경 없이 검색 후처리만으로 구현. Elasticsearch BM25F와 동일 원리.

### content 인덱싱은 하지 않는다

실험 014에서 content[:50] 인덱싱을 시도했으나, stems 폭발(8K→260K)로 노이즈 유발.
precision 95% → 35%로 급락. content 인덱싱은 기각.

비공식 표현("사장", "횡령")은 **AI 레이어**(`dartlab.ask()`)에서 처리한다.
search는 DART 공식 용어(report_nm + section_title)만 정확 매칭하는 역할.

### TF×IDF는 사용하지 않는다

실험에서 IDF 가중치를 시도했으나, 희귀 stem 과대평가로 비공식 쿼리 precision 하락 (88%→76%).
DART 공시에서는 **TF(bincount) + BM25F 리랭킹이 최적** — IDF 없이도 report_nm 필드 가중치가 순위를 결정한다.

### 계층적 유형 라우팅 (실험 015)

DART 114개 정규화 유형을 L0 라우터로 사용:

```
L0: 114개 유형에서 Jaccard+Coverage로 쿼리 매칭 → 후보 유형 선택
L1: 후보 유형의 문서만 필터 → 노이즈 원천 차단
L2: 필터 내 BM25F 리랭킹
```

비공식 표현은 L0에서만 변환 (114개 대상이라 노이즈 없음):
- "M&A" → "합병 인수" → 유형 "합병등종료보고서" 매칭
- "CB 발행" → "전환사채" → 유형 "전환사채" 매칭

L0 비공식 변환은 22개 규칙 — 400만 문서가 아닌 114개 유형에만 적용하므로 하드코딩이 아닌 "유형 라우팅 규칙".

### 역할 분리 — search vs AI

| 역할 | 담당 | 처리 |
|------|------|------|
| DART 공식 용어 검색 | `dartlab.search()` | ngram + BM25F (88%, 124ms) |
| 비공식 → 공식 변환 | L0 유형 라우팅 (114개 대상) | "M&A"→"합병", "CB"→"전환사채" |
| 완전 자연어 이해 | `dartlab.ask()` | AI가 "사장이 바뀌었어" → search("대표이사변경") |

search 내부에서 처리 가능한 범위(유형 라우팅)와 AI가 필요한 범위(자연어 이해)를 분리한다.

### 통합 인덱스

allFilings(수시공시) + docs(사업보고서) → 단일 stemIndex.
중복은 (rcept_no, section_order)로 제거, allFilings 우선.

## 저장 구조

```
data/dart/stemIndex/
├── stemIndex.npz       # CSR 역인덱스 (offsets + docIds, int32)
├── stemDict.json       # stem → ID 매핑
└── meta.parquet        # 문서 메타 + text[:2000]

data/dart/allFilings/
├── {date}.parquet      # 수시공시 원문 (일자별)
├── {date}_meta.parquet # 목록만 (원문 미수집)
```

## 2단계 수집

```
Phase 1: collectMeta() ← 목록만 (일자당 API ~15회, 가볍다)
  → {date}_meta.parquet

Phase 2: fillContent() ← 원문 채우기 (건당 API 1회, 무겁다)
  → {date}.parquet (승격, _meta 삭제)
```

## 인덱스 빌드 파이프라인

```python
from dartlab.core.search import collectMeta, fillContent, rebuildIndex, pushIndex

# 1. 수시공시 수집
collectMeta("20260301", "20260330")
fillContent()

# 2. 통합 인덱스 빌드 (allFilings + docs, ~220초)
rebuildIndex()

# 3. HF 공유
pushIndex(token="hf_xxx")
```

증분 전략: **전체 리빌드** (220초, CSR append 복잡도 대비 이점 없음)

## HF 배포

```python
from dartlab.core.search import pushIndex, pullIndex

pushIndex(token="hf_xxx")  # stemIndex.npz + stemDict.json + meta.parquet 업로드
pullIndex()                 # 다운로드 → 즉시 검색
```

stemIndex.npz가 이미 압축된 numpy 형태라 별도 압축 불필요.

## 실험 105 결과

| 방법 | precision@5 | cold start | 속도 | 의존성 |
|------|:---:|:---:|:---:|------|
| **Ngram+Synonym** | **95%** | **0ms** | **1ms** | **없음** |
| Trigram 단독 | 88% | 0ms | 1ms | 없음 |
| 임베딩(ko-sroberta) | 83% | 12,700ms | 58ms | PyTorch 2GB |
| BM25(FTS) | 71% | 0ms | 14ms | 없음 |

대규모 (400만 문서):
- 인덱스 빌드: 218초 (3.6분)
- 인덱스 크기: ~320MB
- 검색 속도: 140ms (bincount)

부산물: DART Taxonomy(15카테고리), 동반공시 PMI 그래프, DART 특화 Model2Vec(24.7MB)

## 왜 임베딩 없이 되는가 — 이론적 기반

### 정형 문서의 구조적 특성

일반 텍스트 검색에서 임베딩이 필요한 이유는 **동일한 의미를 다른 단어로 표현**하기 때문이다.
"자동차를 구매했다"와 "차를 샀다"는 같은 의미지만 단어가 다르다.

DART 공시는 다르다. **법적 정형 문서**로서:
- 공시 유형(report_nm)이 257개로 고정 — "유상증자결정", "대표이사변경" 등 표준 용어
- 섹션 제목(section_title)이 반복 패턴 — "재무에 관한 사항", "배당에 관한 사항"
- 용어가 법률로 규정 — 같은 의미를 다른 단어로 표현하지 않는다

따라서 **단어 자체가 의미를 완전히 표현**하고, ngram 매칭만으로 의미 검색이 가능하다.

### Stem ID 역인덱스가 임베딩을 대체하는 원리

```
임베딩 방식:
  "유상증자" → [0.12, -0.34, 0.56, ...] (768차원 실수 벡터)
  검색: cosine similarity 계산 → 유사 벡터 탐색

Stem ID 방식:
  "유상증자" → stemId=42
  검색: invertedIndex[42] → [docId1, docId2, ...] → 즉시 반환
```

임베딩은 의미를 **연속 공간**에 매핑하지만, DART 공시는 의미가 **이산적**(discrete)이다.
"유상증자"와 "전환사채"는 유사하지만 같지 않다 — 임베딩 공간에서의 거리보다, **DART 분류 체계에서의 관계**가 더 정확하다.

### 비공식 표현 처리 — 2계층 변환

사용자의 비공식 표현("사장이 바뀌었다")을 DART 공식 용어("대표이사변경")로 변환하는 것이 핵심.

```
L1: 비공식→공식 변환 (16개 규칙, 데이터에서 도출)
    "사장" → "대표이사", "M&A" → "합병", "CB" → "전환사채"

L2: ngram 정확 매칭 (stem ID 역인덱스)
    "대표이사" → stemId → docIds → 결과
```

L1 규칙은 report_nm 472개 유형을 분석하여 도출. 130개 DART 공식 키워드에 비공식 별칭을 매핑.
수작업이지만 **데이터가 정의한 어휘 체계 위에 올리는 것**이라 범용 동의어 사전과 다르다.

### 성능 원리 요약

| 요소 | 임베딩 | Stem ID |
|------|--------|---------|
| 의미 표현 | 연속 벡터 (768d float32) | 정수 ID (int32) |
| 저장 | 벡터 × 문서 수 | CSR (offsets + docIds) |
| 검색 | ANN (근사 최근접) | bincount (정확 집합) |
| 모델 | 420MB transformer | 없음 |
| cold start | 12.7초 | 0ms |
| 정밀도 | 83% (의미 유사도 기반) | 95% (정확 매칭 + 동의어) |

**정형 문서에서는 정확 매칭이 의미 유사도보다 정밀하다.**
임베딩은 범용성이 강점이지만, 도메인 특화 정형 문서에서는 구조를 직접 활용하는 것이 우월하다.

### 핵심 통찰

**역인덱스 자체가 의미 구조다.** 별도 신경망이 필요 없다.
1,460만 문장 코퍼스에서 CSR 구조의 효율성과 정확성을 검증했으며,
비트맵/set/CSR 비교에서 CSR + bincount 조합이 최적임을 확인.

## 파생 집계 레이어 (보류 — 가치 미확정)

`buildNgramIndex()` 시 meta.parquet에서 group_by로 추출하는 파생 데이터.
코드는 `core/search/derived.py`에 구현되어 있으나, **실제 가치가 검증되지 않아 현장 배치 보류.**

| 파생물 | 내용 | 상태 |
|--------|------|------|
| companyProfile.parquet | 기업별 공시 건수/유형/속도 | 보류 — 유형 건수만으로 인사이트 부족 |
| eventTimeline.parquet | 유형×월 빈도 시계열 | 보류 — "그래서 뭐?" 문제 |
| dna.npz | 114차원 유형 빈도 벡터 | 보류 — 행동 peer 가치 미검증 |

**보류 사유**: allFilings meta의 공시 유형 건수 집계만으로는 의미 있는 인사이트가 나오지 않는다. 진짜 가치는 공시 내용(section_content)에 있다. 전체 데이터 축적 + 실제 사용 사례에서 가치가 입증되면 배치 위치를 결정한다.

**현장 배치 완료된 것**:
- AI 시스템 프롬프트에 `dartlab.search()` 도구 설명 추가
- AI sandbox에 `disclosureSearch()` 노출
- AI prefetch에 `_preGroundDisclosure()` (companyProfile 기반 — 프로필 파일 있을 때만 동작)

## 관련 코드

| 파일 | 역할 |
|------|------|
| `src/dartlab/core/search/ngramIndex.py` | stem ID 역인덱스 (빌드 + 검색 + HF push/pull) |
| `src/dartlab/core/search/__init__.py` | 통합 진입점 (search, buildIndex, rebuildIndex) |
| `src/dartlab/core/search/derived.py` | 파생 집계 (companyProfile, eventTimeline, dna) — 보류 |
| `src/dartlab/core/search/vectorStore.py` | 벡터 검색 (optional 보강) |
| `src/dartlab/providers/dart/openapi/allFilingsCollector.py` | 수시공시 수집기 |
