# EDGAR Engine Development Guide

## 안정성 Tier

| 기능 | Tier | 비고 |
|------|------|------|
| Company facade, sections, show, trace, diff | **Tier 1 (Stable)** | DART와 동등 |
| docs (retrievalBlocks, contextSlices) | **Tier 1 (Stable)** | |
| finance (BS/IS/CF, ratios, timeseries) | **Tier 1 (Stable)** | |
| profile (merge layer) | **Tier 1 (Stable)** | |
| valuation(), forecast() | **Tier 1 (Stable)** | USD 자동 감지 |
| simulation() | **Tier 1 (Stable)** | US 매크로 프리셋 |
| SCE, explore(), listTags() | Tier 2 (Beta) | 파워유저 기능 |
| notes(), freq(), coverage() | Tier 2 (Beta) | 파워유저 기능 |

## 핵심 사상 (EDGAR 적용)

**1. sections 수평화 = 10-K/10-Q/20-F 수평화 + blockType 분리**

EDGAR docs는 sections 수평화가 유일한 기초 경로다. 레거시 파서가 없다.
10-K와 10-Q의 topic을 form-native namespace로 구분한다:
- `10-K::item1Business`, `10-K::item1ARiskFactors`
- `10-Q::partIItem2Mdna`, `10-Q::partIIItem1ARiskFactors`
- `20-F::item5OperatingAndFinancialReview`

**sections 반환 형태** (DART와 동일):
```
│ topic                  │ blockType │ blockOrder │ textNodeType │ textLevel │ textPath │ 2024Q4 │ 2023Q4 │
│ 10-K::item1Business    │ text      │ 0          │ heading      │ 1         │ Products │ Products│ ...   │
│ 10-K::item1Business    │ text      │ 1          │ body         │ 0         │ Products │ iPhone…│ ...    │
│ 10-K::item1Business    │ table     │ 2          │ null         │ null      │ null     │ 테이블  │ ...   │
│ 10-K::item7Mdna        │ text      │ 0          │ heading      │ 1         │ Overview │ ...    │ ...   │
```

- 같은 topic 안에서 blockType으로 text/table 분리
- text는 heading/body로 세분화 (textNodeType, textLevel, textPath 메타)
- 기간 정렬은 descending (최신 먼저, DART와 동일)
- 연간 보고서는 Q4 라벨 (`2024` → `2024Q4`)

**2. show(topic, block) — sections 기반**

DART Company와 동일한 show() 계약:
```python
c.show("10-K::item1Business")        # 블록 목차 DataFrame
c.show("10-K::item1Business", 0)     # block 0의 실제 데이터
c.show("BS")                         # finance DataFrame
```

finance topic (BS/IS/CF/CIS, ratios)은 기존대로 DataFrame 반환.

**3. index — DART와 동일한 8컬럼 구조**

```python
c.index  # chapter, topic, label, kind, source, periods, shape, preview
```
- `chapter`: "Part I", "Part II", "Financial Statements", "20-F" 등
- `label`: "Business", "Risk Factors", "Balance Sheet" 등
- `shape`: docs → "17기간", finance → "57x19"

**4. 뼈대 위 대체 = finance authoritative**

- finance (SEC XBRL): BS/IS/CF, ratios — 숫자 authoritative
- docs (10-K/10-Q sections): 서술형 전체 — 정성 authoritative
- report (SEC API): 향후 — 정형 structured disclosure
- profile.sections: finance + docs merge layer (구현 완료)

**5. DART와의 차이**

- 레거시 파서 없음 — sections가 처음부터 유일한 경로
- report namespace 아직 없음 (SEC API 정형 데이터는 향후)
- `openapi/`는 SEC public API wrapper + saver 역할만 담당
- raw 응답은 source-native dict/DataFrame 유지, parquet 저장만 dartlab 규약에 맞춘다

## 현재 구조

```
c = Company("AAPL")

c.index                      # 8컬럼: chapter, topic, label, kind, source, periods, shape, preview
c.show("BS")                 # DataFrame (finance)
c.show("ratios")             # DataFrame (ratio series)
c.show("10-K::item1Business")  # ShowResult(text, table)
c.trace("BS")                # {"primarySource": "finance", ...}
c.trace("10-K::item1Business")  # {..., "chapter": "Part I", "label": "Business", "hasText": True, "hasTable": True}
c.topics                     # ["BS", "IS", "CF", "ratios", "10-K::...", ...]

c.docs.sections              # (topic, blockType) × period DataFrame (pure source)
c.docs.retrievalBlocks       # block × period unpivot (LLM 검색용)
c.docs.contextSlices         # 슬라이스 (LLM 컨텍스트 창 크기 대응)
c.docs.notes()               # XBRL TextBlock 주석 (AccountingPolicies 등)
c.docs.freq()             # topic × period 분포 매트릭스
c.docs.coverage()            # topic별 커버리지 요약
c.docs.filings()             # filings 목록
c.finance.BS / IS / CF / CIS # 연도별 재무제표
c.finance.SCE                # 자본변동표 (BS delta + CF equity 거래)
c.finance.ratios / ratioSeries
c.finance.explore("Revenue") # XBRL 태그 검색 (전 기간 값 탐색)
c.finance.listTags()         # 보고된 모든 us-gaap 태그 목록
c.profile.sections           # docs + finance merge (= c.sections)

c.BS                         # finance.BS 바로가기
c.sections                   # profile.sections 위임 (docs+finance 통합)
c.stockCode                  # ticker alias (서버 API 호환)
c.filings()                  # docs.filings() 바로가기
c.liveFilings()              # SEC source-native 최신 filing 목록
c.readFiling(rowOrUrl)       # filing HTML/.txt 원문 회수

c.insights                   # 10영역 등급
```

## docs 매퍼 영구 학습 메커니즘

### 매핑 파이프라인

```
원본 section_title (SEC filing)
  ↓ normalizeSectionTitle()
  │   ├─ 특수문자/파이프/공백/curly quote 정규화
  │   ├─ 오타 보정: "IT EM 1A", "I tem 1A" → "Item 1A"
  │   ├─ 중복 label 제거: "Item 12D. ITEM 12D" → "Item 12D."
  │   ├─ "Part I - Item 1A." 형식 → canonical "Part {num} - Item {num}. {label}"
  │   ├─ Part-no-Item: "Part I - Risk Factors" → canonical 매핑
  │   ├─ non-Item title: "EXECUTIVE OFFICERS" → Item 4A 매핑
  │   ├─ Reg S-K 3자리+: Item 304/401/1300 등 → 일괄 흡수
  │   ├─ "ITEM 4A" (마침표 없음) → "Item 4A." 보정
  │   └─ 10-Q Part/Item 번호 교정 (Item 5→Part II, Item 1A Risk→Part II)
  ↓ loadSectionMappings() — sectionMappings.json 조회 (exact match)
  ↓ _lowercaseMappings() — case-insensitive fallback
  ↓ mapSectionTitle(formType, title) → "{formType}::{topicId}"
```

### 매핑 데이터

- 파일: `docs/sections/mapperData/sectionMappings.json`
- 형식: `{"정규화된 section_title": "camelCaseTopicId"}` (182개)
- 로드: `@lru_cache(maxsize=1)` 캐시
- case-insensitive fallback: `_lowercaseMappings()` 자동 생성

### 커버리지

- 10-K: Item 1~16 전체 + Item 4A/1D/8A/8B/15A 변형
- 10-Q: Part I Item 1~4, Part II Item 1~8 + 변형
- 20-F: Item 1~19 + Item 4A~16K sub-item + Item 5A~12D 세부항목
- Regulation S-K: Item 103/304/401/403/404/405/406/408/601 + 1117/1119/1122/1123/1300/1303/1304
- 비Item: Executive Officers, Controls, Financial Statements, Recovery, Signatures 등

### 학습 원칙

1. **정규화 우선** — normalizeSectionTitle()이 최대한 흡수 → 매핑 항목 최소화
2. **하드코딩 예외** — 정규화로 안 되는 건 sectionMappings.json에 추가
3. **case-insensitive fallback** — exact match 실패 시 소문자 매칭
4. **form-native namespace** — topic에 formType prefix를 붙여 10-K/10-Q/20-F 구분 유지
5. **100% 매핑률 유지** — 새 title 발견 시 정규화 확장 또는 매핑 추가로 즉시 해소

### 학습 절차

1. 새 ticker 데이터 수집 시 미매핑 title 발견
2. `normalizeSectionTitle()`로 기존 매핑에 붙는지 확인
3. 안 붙으면:
   - **반복 패턴** → mapper.py 정규화 규칙 추가
   - **일회성** → sectionMappings.json에 하드코딩 추가
4. 전수조사로 매핑률 100% 확인: `unmapped == 0`
5. 기존 테스트 통과 확인: `pytest tests/test_edgarDocs_foundation.py`

### 전수조사 스크립트 (즉시 실행 가능)

```python
from pathlib import Path
from dartlab import config
from dartlab.engines_legacy.edgar.docs.sections.mapper import normalizeSectionTitle, loadSectionMappings, _lowercaseMappings
import polars as pl
from collections import Counter

loadSectionMappings.cache_clear()
_lowercaseMappings.cache_clear()
mappings = loadSectionMappings()
lcMappings = _lowercaseMappings()
docsDir = Path(config.dataDir) / 'edgar' / 'docs'
unmapped = Counter()
totalRows = mappedRows = 0
for f in sorted(docsDir.glob('*.parquet')):
    df = pl.read_parquet(f)
    if 'section_title' not in df.columns: continue
    for row in df.iter_rows(named=True):
        rawTitle = str(row.get('section_title') or '')
        if not rawTitle: continue
        totalRows += 1
        n = normalizeSectionTitle(rawTitle)
        if n in mappings or n.lower() in lcMappings: mappedRows += 1
        else: unmapped[n] += 1
print(f'총: {totalRows}, 매핑: {mappedRows} ({mappedRows/totalRows*100:.4f}%), 미매핑: {totalRows-mappedRows}')
for t, c in unmapped.most_common(20): print(f'  {c}x  {t}')
```

## 파일 구조 (2026-03-22)

```
providers/edgar/
├── company.py               # Company 본체 (~1,050줄)
├── _docs_accessor.py        # docs namespace (sections, retrievalBlocks, contextSlices, notes, freq, coverage, filings)
├── _finance_accessor.py     # finance namespace (BS/IS/CF/CIS/SCE/ratios/ratioSeries/explore/listTags)
├── _profile_accessor.py     # profile namespace (docs+finance merge)
├── docs/
│   ├── notes.py             # XBRL TextBlock 주석 추출
│   └── sections/
│       ├── pipeline.py      # sections() 메인 함수
│       ├── mapper.py        # section title → topic 매핑
│       ├── views.py         # sortPeriods, retrievalBlocks, contextSlices, freq, coverage
│       ├── textStructure.py # 영문 heading/body 파서
│       └── mapperData/      # sectionMappings.json (182개)
├── finance/
│   ├── mapper.py            # XBRL tag → snakeId 매핑
│   ├── pivot.py             # buildTimeseries, buildAnnual, buildSce
│   └── explore.py           # XBRL Fact Explorer (태그 검색, 목록)
└── openapi/                 # SEC public API wrapper
```

## 검증 (2026-03-22)

- **974개 ticker 전수조사**: 에러 0, sections None 0
- **sections 매퍼**: 100.0000% (442,025/442,025행, 182개 매핑)
- **blockType 분리**: 974종목 704,846셀, leak 0
- **text 행**: 30,862, **table 행**: 20,834
- **show()**: 974종목 ShowResult 반환 성공
- **profile**: 974종목 생성 성공
- **index**: 8컬럼 DART 동일 구조 (chapter, topic, label, kind, source, periods, shape, preview)
- **테스트**: 48개 통과 (기존 30 + 신규 18)
- **accessor 분리**: company.py 1,243→1,050줄, 3개 accessor 파일 분리
- **retrievalBlocks/contextSlices**: views.py 40→420줄, LLM 증거층 + freq/coverage
- **서버 API**: resolve.py US ticker 인식 추가, stockCode 호환 property
- **SCE**: BS equity 컴포넌트 delta + CF equity 거래 + IS net income + CI OCI
- **XBRL Fact Explorer**: 태그 단위 전 기간 값 탐색, 태그 목록
- **XBRL Notes**: TextBlock 주석 추출 (20개 주요 태그 label 내장)
- **insight pipeline**: EDGAR Company 완전 지원 (governance graceful fallback)
