# EDGAR Engine Development Guide

## 핵심 사상 (EDGAR 적용)

**1. sections 수평화 = 10-K/10-Q/20-F 수평화 + blockType 분리**

EDGAR docs는 sections 수평화가 유일한 기초 경로다. 레거시 파서가 없다.
10-K와 10-Q의 topic을 form-native namespace로 구분한다:
- `10-K::item1Business`, `10-K::item1ARiskFactors`
- `10-Q::partIItem2Mdna`, `10-Q::partIIItem1ARiskFactors`
- `20-F::item5OperatingAndFinancialReview`

**sections 반환 형태** (DART와 동일):
```
│ topic                  │ blockType │ 2020   │ 2021   │ 2022   │
│ 10-K::item1Business    │ text      │ 서술문 │ 서술문 │ 서술문 │
│ 10-K::item1Business    │ table     │ 테이블 │ null   │ 테이블 │
│ 10-K::item7Mdna        │ text      │ 서술문 │ 서술문 │ 서술문 │
```

- 같은 topic 안에서 blockType으로 text/table 분리
- 기간 정렬은 ascending (오래된 순 → 최신 순, DART와 동일)

**2. show() → ShowResult(text, table)**

DART Company와 동일한 `ShowResult(text, table)` NamedTuple 반환:
```python
result = c.show("10-K::item1Business")
result.text   # pl.DataFrame | None — 서술문
result.table  # pl.DataFrame | None — 테이블
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
c.docs.filings()             # filings 목록
c.docs.show(topic)           # ShowResult(text, table)

c.finance.BS / IS / CF / CIS # 연도별 재무제표
c.finance.ratios / ratioSeries

c.profile.sections           # finance + docs merged sections (연도별 finance 채움)

c.BS                         # finance.BS 바로가기
c.sections                   # docs.sections 바로가기
c.filings()                  # docs.filings() 바로가기

c.insights                   # 7영역 등급
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
from dartlab.engines.edgar.docs.sections.mapper import normalizeSectionTitle, loadSectionMappings, _lowercaseMappings
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

## 검증 (2026-03-15)

- **974개 ticker 전수조사**: 에러 0, sections None 0
- **sections 매퍼**: 100.0000% (442,025/442,025행, 182개 매핑)
- **blockType 분리**: 974종목 704,846셀, leak 0
- **text 행**: 30,862, **table 행**: 20,834
- **show()**: 974종목 ShowResult 반환 성공
- **profile**: 974종목 생성 성공
- **index**: 8컬럼 DART 동일 구조 (chapter, topic, label, kind, source, periods, shape, preview)
- **테스트**: 62개 통과
