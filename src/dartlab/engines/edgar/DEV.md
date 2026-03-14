# EDGAR Engine Development Guide

## 핵심 사상 (EDGAR 적용)

**1. sections 수평화 = 10-K/10-Q 수평화 + blockType 분리**

EDGAR docs는 sections 수평화가 유일한 기초 경로다. 레거시 파서가 없다.
10-K와 10-Q의 topic을 form-native namespace로 구분한다:
- `10-K::item1Business`, `10-K::item1ARiskFactors`
- `10-Q::partIItem2Mdna`, `10-Q::partIIItem1ARiskFactors`

연간(10-K)과 분기(10-Q)가 같은 시간축에 자연 나열되며,
의미적 대응 6쌍(riskFactors, mdna, financialStatements, controls, legalProceedings, exhibits)으로
form 경계를 넘는 시계열 비교가 가능하다.

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

**3. 뼈대 위 대체 = finance authoritative**

- finance (SEC XBRL): BS/IS/CF, ratios — 숫자 authoritative
- docs (10-K/10-Q sections): 서술형 전체 — 정성 authoritative
- report (SEC API): 향후 — 정형 structured disclosure
- profile.sections: finance + docs merge layer (구현 완료)

**4. profile namespace**

DART Company.profile과 동일한 사상:
- docs.sections가 구조적 뼈대
- finance(BS/IS/CF/CIS)를 sections 형태로 변환하여 상단에 배치
- `c.profile.sections`로 접근

**5. DART와의 차이**

- 레거시 파서 없음 — sections가 처음부터 유일한 경로
- sectionMappings.json 매퍼 100% (109개 매핑)
- report namespace 아직 없음 (SEC API 정형 데이터는 향후)

## 현재 구조

```
c = Company("AAPL")

c.index                      # finance + docs 통합 보드 (blockType 표시)
c.show("BS")                 # DataFrame (finance)
c.show("ratios")             # DataFrame (ratio series)
c.show("10-K::item1Business")  # ShowResult(text, table)
c.trace("BS")                # {"primarySource": "finance", ...}
c.topics                     # ["BS", "IS", "CF", "ratios", "10-K::...", ...]

c.docs.sections              # (topic, blockType) × period DataFrame (pure source)
c.docs.filings()             # filings 목록
c.docs.show(topic)           # ShowResult(text, table)

c.finance.BS / IS / CF / CIS # 연도별 재무제표
c.finance.ratios / ratioSeries

c.profile.sections           # finance + docs merged sections

c.BS                         # finance.BS 바로가기
c.sections                   # docs.sections 바로가기
c.filings()                  # docs.filings() 바로가기

c.insights                   # 7영역 등급
```

DART와 동일한 index / show / trace 공개 인터페이스를 갖추고 있다.
- `index`: finance(BS/IS/CF/ratios) + docs(sections topics) 통합 보드
- `show(topic)`: finance 제표 → DataFrame, docs topic → ShowResult
- `trace(topic)`: source provenance 딕셔너리

## docs 매퍼 영구 학습 메커니즘

### 매핑 파이프라인

```
원본 section_title (SEC filing)
  ↓ normalizeSectionTitle()
  │   ├─ 특수문자/파이프/공백 정규화
  │   ├─ "Part I - Item 1A." 형식 → canonical "Part {num} - Item {num}. {label}"
  │   ├─ Reg S-K Item 405/406/601 → 표준화
  │   └─ 10-Q Part/Item 번호 교정 (Item 5→Part II, Item 1A Risk→Part II)
  ↓ loadSectionMappings() — sectionMappings.json 조회
  ↓ mapSectionTitle(formType, title) → "{formType}::{topicId}"
```

### 매핑 데이터

- 파일: `docs/sections/mapperData/sectionMappings.json`
- 형식: `{"정규화된 section_title": "camelCaseTopicId"}` (109개)
- 로드: `@lru_cache(maxsize=1)` 캐시

### 학습 원칙

1. **sectionMappings.json은 실험 검증 후에만 수정** — 무분별한 수작업 추가 금지
2. **정규화 우선** — normalizeSectionTitle()이 최대한 흡수 → 매핑 항목 최소화
3. **하드코딩 예외** — 정규화로 안 되는 건 sectionMappings.json에 추가
4. **form-native namespace** — topic에 formType prefix를 붙여 10-K/10-Q/20-F 구분 유지
5. **100% 매핑률 유지** — 새 title 발견 시 정규화 확장 또는 매핑 추가로 즉시 해소

### 학습 절차

1. 새 ticker 데이터 수집 시 미매핑 title 발견
2. `normalizeSectionTitle()`로 기존 매핑에 붙는지 확인
3. 안 붙으면 → 실험 폴더에서 패턴 분석 후 결정:
   - 정규화 규칙 추가 (mapper.py) — 반복 패턴이면 이쪽 우선
   - sectionMappings.json에 하드코딩 추가 — 일회성이면 이쪽
4. 변경 후 전체 ticker 회귀 테스트로 매핑률 100% 확인

### DART docs 매퍼와의 차이

| 항목 | DART | EDGAR |
|------|------|-------|
| 매핑 키 | 한글 section_title | 영문 section_title |
| 매핑 수 | 지속 증가 (업종 다양) | 109개 (SEC 양식 고정) |
| 정규화 | stripSectionPrefix + mapSectionTitle | normalizeSectionTitle + loadSectionMappings |
| namespace | 없음 (chapter로 구분) | formType:: prefix (10-K/10-Q/20-F) |
| 안정성 | ~98.9% (계속 학습) | 100% (SEC 양식 안정적) |

## 검증

- 335개 ticker, 333 성공, 에러 0 (2개는 CIK 매핑 누락)
- sections 매퍼 100% (106,023/106,023)
- 파이프라인 무에러 (211개 → 335개 검증)
- Company 인터페이스 테스트 통과 (index/show/trace/topics/filings)
- blockType 분리: AAPL text:35 table:33, MSFT text:34 table:25, NVDA text:34 table:16
