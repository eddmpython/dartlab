# DART Engine Development Guide

상세 문서:
- `src/dartlab/engines/dart/docs/DEV.md`
- `src/dartlab/engines/dart/finance/DEV.md`
- `src/dartlab/engines/dart/report/DEV.md`

## [최우선] 데이터 원칙

### 기본 단위: 분기

**DART 원본 데이터의 기본 단위는 분기(quarter)다.**
- 사업보고서(Q4), 반기보고서(Q2), 분기보고서(Q1/Q3)
- finance 원본 parquet도 분기별 XBRL 데이터
- **연간(annual)은 분기를 집계한 파생 뷰**이다
- 현재 `c.BS`, `c.IS` 등은 연간 뷰만 노출 — 향후 분기별 뷰 추가 예정

### 기간 표현 통일

| 표현 | 의미 | 예시 |
|------|------|------|
| `YYYY` | 연간 | `2024` |
| `YYYYQN` | 분기 | `2024Q1`, `2024Q2`, `2024Q3`, `2024Q4` |

- 하이픈 없음: `2024Q1` (O) / `2024-Q1` (X)
- 모든 레이어에서 동일 포맷 사용
- finance timeseries 내부(`2015-Q4`)는 레거시 — 외부 노출 시 `2015Q4`로 변환
- `docs.sections` raw 컬럼은 source-of-truth로 연간을 `YYYY`로 유지할 수 있다.
- 대신 `c.docs.sections.periods() / ordered() / coverage()`와 `show(period="2025Q4")`는 연간 alias를 `YYYYQ4`로 받아들인다.

### 정렬 기준: raw와 소비층을 분리

- 내부 raw/helper는 계산 안정성을 위해 오름차순을 기본으로 둔다.
- 사용자-facing sections accessor는 최신 우선이 기본이다.
  - `c.docs.sections.periods()` → `2025Q4, 2025Q3, ...`
  - `c.docs.sections.ordered()` → 최신 period 열이 앞에 온다.
  - `c.docs.sections.coverage()` → 최신 period부터 진단한다.

## 핵심 사상 (DART 적용)

**1. sections 수평화 = 사업보고서 수평화**

DART 사업보고서는 I~XII장 12개 대분류가 전 종목 동일 (DART 규정).
소분류는 회사별 차이가 있으므로 sectionMappings.json으로 표준화한다.
하지만 수평화의 실제 단위는 큰 topic 자체가 아니라 **topic을 정확히 분해한 내부 section/block unit**이다.
sections pipeline은 `topic × blockType × blockOrder`(행) × `period`(열) DataFrame을 생성하며,
text는 body block을 다시 `heading/body` fine row로 분해해 수평화한다.
원래 큰 블록 순서는 `sourceBlockOrder`에 보존하고, `blockOrder`는 fine row의 안정 순서다.
text row matching은 `sourceBlockOrder`가 아니라 `textPathKey + occurrence` 기준으로 수행한다.
top-level text heading이 현재 topic과 같은 의미면 `textPathKey`는 `@topic:{topic}` canonical root를 사용한다.
`textSemanticPathKey` / `textSemanticParentPathKey`는 raw 구조를 덮어쓰지 않는 parallel semantic spine이며, 안전한 alias만 보수적으로 흡수한다.
row는 흡수된 raw wording drift를 `textPathVariants` / `textPathVariantCount`로 함께 보존한다.
시점 마커(`[2021년 12월]`)와 중복 topic alias heading은 row로는 보존하되 `textStructural=false`로 내려 outline stack에서 제외한다.
row별 period 분포는 `cadenceScope` / `cadenceKey` / `latestAnnualPeriod` / `latestQuarterlyPeriod` 메타로 보존한다.
c.docs.sections는 raw DataFrame을 감싼 source accessor다.
- DataFrame 속성/메서드는 그대로 위임된다. (`c.docs.sections.filter(...)`)
- 같은 경로에서 `c.docs.sections.raw`, `c.docs.sections.periods()`, `c.docs.sections.ordered()`, `c.docs.sections.coverage()`, `c.docs.sections.cadence(...)`, `c.docs.sections.semanticRegistry(...)`, `c.docs.sections.semanticCollisions(...)`를 바로 쓴다.
- 기존 `c.docs.sectionsOrdered()` / `c.docs.sectionsCoverage()` / `c.docs.sectionsCadence()` / `c.docs.sectionsSemanticRegistry()` / `c.docs.sectionsSemanticCollisions()`는 호환용 얇은 래퍼다.
셀에는 해당 기간의 원문 payload를 둔다.
어떤 기간에만 존재하는 unit은 해당 기간만 값이 있고 나머지는 `null`이다.
이것이 Company의 구조적 뼈대다.

**2. 장 제목 vs 소항목 분리**

원본 parquet의 section_title에는 장 제목(I. 회사의 개요)과 소항목(1. 회사의 개요)이 혼재.
장 제목의 content는 source-of-truth로 보존한다.
- 소항목이 있어도 장 제목 content를 먼저 등록한다.
- 이후 소항목이 같은 semantic row를 채우면 그 셀만 overwrite된다.
- 장 제목에만 존재하는 segment는 그대로 남는다.

이 로직은 `_reportRowsToTopicRows()`의 `pendingChapter` 등록 패턴으로 구현한다.

**3. 추가 내림 = retrievalBlocks → topicSubtables**

sections 뼈대 위에서 특정 기간에만 존재하는 세부 테이블은
retrievalBlocks → topicSubtables()로 행을 내려서 세분화한다.
salesOrder, segments, costByNature, rawMaterial 등이 이 방식.

retrievalBlocks/contextSlices는 **명시적 호출 전용** (c.docs.retrievalBlocks).
show()에서는 사용하지 않는다 — 전체 빌드가 ~10초로 무거움.

**4. 뼈대 위 대체 = profile.sections**

- finance (XBRL): BS/IS/CIS/CF/SCE, ratios — 숫자 authoritative
- report (DART API): 28개 apiType — 정형 공시 authoritative
- docs: business, mdna, 리스크, 주석 — 서술형/정성 authoritative
- profile.sections가 이 세 source를 merge한 최종 뷰

**5. 레거시 공존**

DART는 개별 파서(30+ 모듈)가 먼저 존재했고, sections가 나중에 왔다.
sections 기반 extractor를 우선 사용하고, 레거시 파서는 fallback으로만 남긴다.
tangibleAsset 등 레거시가 더 안정적인 경우는 archive/fallback 유지.

## 사용자 인터페이스

### show(topic) — 반환 형태 가이드

| topic 유형 | 반환 형태 | 예시 |
|-----------|----------|------|
| finance stmt (BS/IS/CIS/CF/SCE) | 계정명 × 연도 DataFrame | `c.show("BS")` → 59×12 |
| ratios | 분류/항목 × 연도 DataFrame | `c.show("ratios")` → 35×13 |
| report pivot 5개 | **toWide()** metric × 연도 | `c.show("dividend")` → 2×11 |
| report non-pivot | extractAnnual raw DataFrame | `c.show("nonAuditContract")` |
| docs topic | raw `sections` DataFrame (`chapter/topic/blockType/blockOrder/sourceBlockOrder/textNodeType/textStructural/segmentOccurrence/cadenceScope + period cols`) | `c.show("companyOverview")` |
| subtopic (salesOrder 등) | wide/long subtable | `c.show("salesOrder")` |

report pivot 5개(dividend, employee, majorHolder, executive, audit)는
show()에서 자동으로 toWide()를 반환하여 **한글 metric × 연도** 형태로 출력.

### show(topic, period=) — 기간 필터

```python
c.show("BS", period="2024")        # 2024 컬럼만
c.show("companyOverview", period="2025")  # 2025 기간만
c.show("companyOverview", period="2025Q4")  # 연간 alias도 허용
```

### diff(topic?, from?, to?) — 변경 분석

```python
c.diff()                                   # 전체 topic 변경 요약 DataFrame
c.diff("businessOverview")                 # 특정 topic 변경 이력
c.diff("businessOverview", "2024", "2025") # 줄 단위 상세 diff
```

- 전체 요약: chapter, topic, periods, changed, stable, changeRate
- topic 이력: fromPeriod, toPeriod, status, fromLen, toLen, delta, deltaRate
- 줄 단위: line(순서), status(`-`=삭제/`+`=추가/` `=유지), text — 인터리빙 맥락 순서

### index — 전체 토픽 인덱스

`c.index` — lazy 구축, 문서 순서(I~XII장) 정렬, 메타데이터 포함.

- docs topic의 shape은 `N기간` 형태 (예: `66기간`)
- finance/report는 `행x열` 형태 (예: `59x12`)

### trace(topic) — source 추적

`c.trace("topic")` — 어떤 source(docs/finance/report)에서 왔는지 provenance.

## 전수조사 결과 (2026-03-14)

### 검증 종목 (6종목)
삼성전자(005930), SK하이닉스(000660), 카카오(035720),
LG에너지솔루션(373220), 네이버(035420), 셀트리온(068270)

### show() 전수검증 결과

| 종목 | topic 수 | 에러 | 정렬 | 메타컬럼 |
|------|---------|------|------|---------|
| 삼성전자 | 70 | 0 | 오름차순 ✅ | 누출 0 |
| SK하이닉스 | 86 | 0 | 오름차순 ✅ | 누출 0 |
| 카카오 | 89 | 0 | 오름차순 ✅ | 누출 0 |
| LG에너지솔루션 | 78 | 0 | 오름차순 ✅ | 누출 0 |
| 네이버 | 82 | 0 | 오름차순 ✅ | 누출 0 |
| 셀트리온 | 80 | 0 | 오름차순 ✅ | 누출 0 |
| **합계** | **485** | **0** | | |

### 추가 검증 항목

| 검증 | 결과 |
|------|------|
| BS 항등식 (자산=부채+자본) | 6종목 전부 OK |
| SCE 계정명 한글화 | 6종목 전부 한글 |
| period filter label 보존 | 분류/항목/metric 정상 유지 |
| diff() 3-mode | 전체요약/topic이력/줄단위 정상 |
| index periods 오름차순 | `1999Q2..2025` 형태 정상 |
| report 메타 컬럼 (6종목×전체 apiType) | 누출 0건 |

### 확정 로직

#### report show() 메타 컬럼 제거
`_reportFrame()` → extractAnnual() 결과에서 `stlm_dt`, `apiType`, `stockCode`, `year`, `quarter`, `quarterNum` 자동 drop.

#### index period range 오름차순
`1999Q2..2025`, `2015..2025` — `[0]..[−1]` 형태.

#### sectionMappings.json 매핑 추가 (30건)
`상세표`, `반기보고서`, `분기보고서`, `사업보고서`, `정정신고(보고)` 등 빈도 상위 항목.
매핑률 94.6% → ~98.9% (행 기준).

#### diff() 줄 단위 출력 개선
인터리빙 순서로 맥락 보존 (`line`, `status`, `text`).
topic 이력에 `delta`(글자수 변화), `deltaRate`(변화율) 추가.

#### _applyPeriodFilter non-period 컬럼 보존
`show(topic, period="2024")` 실행 시 `분류`, `항목`, `metric` 등 label 컬럼이 누락되던 버그 수정.
`_isPeriodColumn()` 기반으로 non-period 컬럼을 자동 보존.

### 데이터 품질 이슈 (해결됨)

| 이슈 | 상태 | 해결 방법 |
|------|------|---------|
| show(report pivot)이 raw DataFrame 반환 | ✅ | _reportFrame()에서 pivot 5개는 toWide() 반환 |
| report 메타 컬럼 노출 | ✅ | _reportFrame()에서 6개 메타 컬럼 자동 drop |
| SCE 계정명 영문 | ✅ | CAUSE_LABELS/DETAIL_LABELS + compound cause 처리 |
| 미매핑 topic 10개 | ✅ | 로마숫자 prefix 정규화 + sectionMappings.json 5건 추가 |
| sections 정렬 불일치 | ✅ | sortPeriods default descending=False |
| index period range 역순 | ✅ | `[0]..[−1]` 오름차순으로 수정 |
| index docs shape "1xN" | ✅ | "N기간" 형태로 변경 |
| docs 매퍼 커버리지 94.6% | ✅ | 30건 추가 → ~98.9% |
| diff 줄 단위 맥락 부재 | ✅ | 인터리빙 순서 + delta/deltaRate 추가 |
| period filter label 컬럼 누락 | ✅ | _applyPeriodFilter에서 non-period 컬럼 자동 보존 |
| audit 2015-2017 null | 확인 | DART API 데이터 한계 — 코드 변경 불요 |

## Profile Pipeline 로드맵

5개 Phase, 아래부터 위로 쌓는 구조:

```
Phase 5: viewer (한 장의 문서 렌더링)          — 미착수
Phase 4: diff (텍스트 변화분 + 숫자 변곡점)     — ✅ 완료
Phase 3: period 형식 (통일 불필요 — 확정)       — ✅ 확정
Phase 2: index 순서 (I~XII장 문서 순서)        — ✅ 완료
Phase 1: report toWide (metric×year 와이드)    — ✅ 완료
```

### Phase 1: report toWide ✅

5개 pivot Result에 `toWide() -> pl.DataFrame | None` 추가.
축: metric(행) × year(열) — finance BS/IS/CF와 동일.
위치: `engines/dart/report/types.py` — `_seriesToWide()` 공통 헬퍼.

| Result | metric 수 | 비고 |
|--------|----------|------|
| DividendResult | 2 | 숫자 |
| EmployeeResult | 3 | 숫자 |
| MajorHolderResult | 1 | 숫자 |
| AuditResult | 2 | 문자열 |
| ExecutiveResult | 3 | snapshot (시계열 아님) |

### Phase 2: index 순서 정렬 ✅

**Phase 2a**: sections DataFrame에 `chapter` 컬럼 추가 (pipeline.py)
**Phase 2b**: index 정렬키 `(chapterOrder, subOrder)`

### Phase 3: period 형식 — 확정 ✅

통일 불필요. 각 소스 고유 포맷 유지.

### Phase 4: diff 레이어 ✅

**4a 텍스트 diff** (sections 위):
- `sectionsDiff(sections)` → DiffResult (entries + summaries)
- `topicDiff(sections, topic, fromPeriod, toPeriod)` → LineDiff
- Company에서 `c.diff()` 3가지 모드로 노출
- 위치: `engines/dart/docs/sections/diff.py`

**4b 숫자 변곡점** (finance 위):
- `detectInflections(df)` → list[Inflection]
- 위치: `engines/common/finance/inflection.py`

### Phase 5: viewer — 미착수

`ViewerSection` / `ViewerDocument` dataclass — 데이터 구조만 정의.
렌더링은 UI(Svelte) 또는 markdown export가 담당.

## 속도 최적화 이력

| 변경 | before | after | 원인 |
|------|--------|-------|------|
| lazy index (060) | 30초 | 1.77초 | 모든 property eager 로드 → lazy 캐시 |
| show() _compressTopicFrame 제거 | ~11초 | ~1초 | retrievalBlocks 전체 빌드 → sections만 |
| pipeline 장 제목 skip | 71 topic | 54 topic | 장 제목 content 중복 제거 |
| show() unpivot 세로 전환 | 1행×108열 | 66행×4열 | 수평 → 세로 |

## 미해결 과제

- **retrievalBlocks 속도**: Python 문자열 처리 ~10초. Rust(PyO3) 네이티브 모듈로 이전 시 ~0.5초 예상.
- **Phase 5 viewer**: 데이터 구조 정의 후 UI(Svelte) 렌더링 연동.
- **report source 충돌**: capitalChange 등 report와 docs 양쪽에 존재 — show()는 report 우선. docs 텍스트는 `c.docs.sections`로 직접 접근.
- **non-pivot report 컬럼명**: DART API 원본 영문 약어 그대로 노출 (`bsns_year`, `adtor` 등). 향후 한글화 검토.
- **finance 분기별 뷰**: 현재 `c.BS`/`c.IS` 등은 연간만 노출. 분기별 DataFrame 뷰 추가 필요.
