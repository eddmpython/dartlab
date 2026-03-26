# DART Docs Development Guide

sections 핵심 원칙과 텍스트 구조 계층 규칙은 아래에 기술한다.

## 데이터 수집 (openapi/collector.py)

공시 원문 수집은 `openapi/collector.py`가 담당한다.
eddmpython DartDocs.py의 수집 로직을 dartlab으로 완전 포팅하여 외부 의존 없이 동작한다.

- 수집 결과: `{dataDir}/docs/{stockCode}.parquet`
- 스키마: `corp_code, corp_name, stock_code, year, rcept_date, rcept_no, report_type, section_order, section_title, section_url, section_content`
- 이 parquet가 sections pipeline의 입력이다.

## sections 핵심 원칙

- `sections`가 docs source of truth다.
- markdown/table 경계를 버리지 않는다.
- 같은 topic 안의 원문 block 순서는 `sourceBlockOrder`로 보존한다.
- `blockOrder`는 수평화된 fine-grained row의 안정 순서다.
- 셀에는 요약이 아니라 해당 기간의 원문 payload를 유지한다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- 기존 docs 개별 parser는 archive/legacy fallback로 남긴다.

### 텍스트 구조 계층 원칙 (2026-03-18)

- 텍스트의 `소제목 레벨`, `headingPath`, `segment`, `paragraph` 복원은 viewer 임시 규칙이 아니라 `sections` 계층 책임이다.
- raw `sections`는 계속 `topic × blockType × blockOrder × period` source-of-truth로 유지하되, `blockOrder`는 fine row 기준이다.
- 원래 큰 블록 경계는 `sourceBlockOrder`에 보존한다.
- 그 위에 `sections` 파생 계층으로 `text structure` 또는 `textSegments`를 만든다.
  - `section title mapper`: 장/절 제목을 topic으로 매핑
  - `text heading splitter`: body 내부의 `가.`, `1.`, `(1)`, `①` 등 소제목 레벨 복원
  - `segment matcher`: 기간 간 같은 텍스트 segment를 `sourceBlockOrder`가 아니라 `textPathKey + occurrence` 기준으로 정렬
  - `paragraph splitter`: segment 내부 비교 단위 복원
- 현재 docs.sections text row 메타:
  - `textNodeType`: `heading` | `body`
  - `textStructural`: 구조 heading/body 여부 (`false`면 marker/alias row)
  - `textLevel`: heading/body level
  - `textPath`, `textPathKey`, `textParentPathKey`
  - `textPathVariantCount`, `textPathVariants`, `textParentPathVariants`
  - `textSemanticPathKey`, `textSemanticParentPathKey`
  - `textSemanticPathVariants`, `textSemanticParentPathVariants`
  - `segmentKey`, `segmentOrder`, `segmentOccurrence`, `sourceBlockOrder`
  - `cadenceKey`, `cadenceScope`, `annualPeriodCount`, `quarterlyPeriodCount`
  - `latestAnnualPeriod`, `latestQuarterlyPeriod`
- top-level heading이 현재 topic과 같은 의미로 매핑되면 `textPathKey`는 label 문자열이 아니라 `@topic:{topic}` canonical root를 쓴다.
- `[2021년 12월]` 같은 시점 마커와 중복 root alias는 raw row로는 남기되 `textStructural=false`로 내려서 outline stack을 오염시키지 않는다.
- `textSemanticPathKey`는 raw 구조선을 덮어쓰지 않는 parallel semantic spine이다.
  - `textPathKey`는 원문 구조를 그대로 보존한다.
  - `textSemanticPathKey`는 안전한 alias만 흡수한다.
  - 현재는 `...에 관한 사항`, `종속기업/종속회사`, `조직개편/조직의 변경`, `감사위원회에 관한 사항` 같은 보수적 케이스만 정규화한다.
- `cadenceScope`는 `annual` / `quarterly` / `mixed` / `none`이며, 소비층이 연간 구조와 분기 구조를 섞지 않게 하는 기준 메타다.
- `projectCadenceRows(df, cadenceScope=..., includeMixed=...)`는 `sections` 내부에서 cadence-aware row projection을 제공하는 공식 helper다.
- `semanticRegistry(df, ...)` / `semanticCollisions(df, ...)`는 `textSemanticPathKey` 기준으로 row가 흡수한 raw wording drift를 진단하는 공식 helper다.
- `structureRegistry(df, ...)` / `structureCollisions(df, ...)`는 `textComparablePathKey` 기준으로 moved/split/merge/parallel 같은 구조 이벤트를 진단하는 공식 helper다.
- `structureEvents(df, ...)`는 comparable slot의 period 전이(`fromPeriod -> toPeriod`)를 직접 event row로 내리는 공식 helper다.
- `structureSummary(df, ...)`는 latest 구조 상태를 한 줄로 요약하는 공식 helper다.
- `structureChanges(df, ...)`는 latest 구조 변화만 압축해서 보여주는 공식 helper다.
  - `nodeType='body'`를 주면 heading anchor를 제외하고 본문 이벤트만 본다.
  - `periodLane` 기준으로 같은 report-kind 안에서만 비교한다. (`annual`, `q1`, `q2`, `q3`)
  - 즉 `Q3 -> annual -> Q1` 같은 교차 주기 전이는 event로 만들지 않는다.
  - `cadenceScope='annual'/'quarterly'`로 조회하면 `mixed` row를 포함하더라도 해당 lane period만 activity에 반영한다.
    - `quarterly` 조회에 annual lane이 섞이면 안 된다.
    - `annual` 조회에 q1/q2/q3 lane이 섞이면 안 된다.
  - 핵심 진단 메타:
    - `activePeriods`
    - `activePathCounts`
    - `multiPathPeriods`
    - `structurePattern`
  - `structurePattern` 값:
    - `same`: raw semantic path 충돌 없음
    - `variant`: period마다 하나의 path만 살아 있고 wording/root만 바뀜
    - `moved`: leaf는 같고 parent path만 이동
    - `reassigned`: business unit slot처럼 같은 comparable slot에 다른 leaf가 시계열로 교대
    - `split`: 초기 1개 path가 최근 여러 path로 분화
    - `merge`: 초기 여러 path가 최근 1개 path로 수렴
    - `split_merge`: 중간에만 다중 path가 나타나는 혼합형
    - `parallel`: 여러 path가 동시 병존하는 구조
  - `structureEvents()`의 `eventType` 값:
    - `variant`
    - `moved`
    - `reassigned`
    - `split`
    - `merge`
    - `parallel_change`
  - `structureSummary()` 핵심 컬럼:
    - `latestPeriod`
    - `latestPeriodLane`
    - `latestPathCount`
    - `eventCount`
    - `latestEventType`
    - `latestEventFromPeriod`
    - `latestEventToPeriod`
  - `structureChanges()` 추가 컬럼:
    - `anchorPeriod`
    - `anchorPeriodLane`
    - `isLatest`
    - `isStale`
  - 기본 `changedOnly=True`는 `eventCount > 0`인 최근 구조 이벤트 row만 남긴다.
    - persistent hotspot을 같이 보려면 `changedOnly=False`를 쓰거나 `structureSummary()` / `structureCollisions()`를 본다.
- `c.docs.sections`는 raw DataFrame을 감싼 source accessor다.
  - DataFrame 메서드는 그대로 위임된다.
  - 같은 경로에서 `.raw`, `.periods()`, `.ordered()`, `.coverage()`, `.cadence(...)`, `.semanticRegistry(...)`, `.semanticCollisions(...)`, `.structureRegistry(...)`, `.structureCollisions(...)`, `.structureEvents(...)`, `.structureSummary(...)`, `.structureChanges(...)`를 호출한다.
  - `periods()/ordered()/coverage()`는 사용자-facing projection이며 최신우선 + 연간 `Q4` alias를 지원한다.
  - `c.docs.sectionsOrdered()` / `c.docs.sectionsCoverage()` / `c.docs.sectionsCadence()` / `c.docs.sectionsSemanticRegistry()` / `c.docs.sectionsSemanticCollisions()` / `c.docs.sectionsStructureRegistry()` / `c.docs.sectionsStructureCollisions()` / `c.docs.sectionsStructureEvents()` / `c.docs.sectionsStructureSummary()` / `c.docs.sectionsStructureChanges()`는 호환용 thin wrapper다.
- 장 제목 content는 source-of-truth로 보존한다.
  - 소항목이 있어도 장 제목 text block을 먼저 등록한다.
  - 이후 소항목이 같은 semantic row를 채우면 그 셀만 overwrite된다.
  - 장 제목에만 남아 있는 segment는 그대로 유지된다.
- viewer는 위 구조를 소비해 렌더링만 담당한다. viewer 안에서 문서 구조를 다시 해석하는 로직은 임시 보정으로 보고 점진적으로 제거한다.

### 현재 정확한 기준 위치 (2026-03-18)

- 이번 `sections` 텍스트 구조 개선의 정확한 source of truth는 아래 두 문서다.
  - 개요/원칙/책임: `src/dartlab/providers/dart/docs/DEV.md`
- 핵심 변경 요약:
  - text row spine은 `sourceBlockOrder`가 아니라 `textPathKey + occurrence` 기준이다.
  - top-level root alias는 `@topic:{topic}` canonical root로 정규화한다.
  - semantic alias spine은 `textSemanticPathKey` / `textSemanticParentPathKey`로 병렬 보존한다.
  - row가 흡수한 raw wording drift는 `textPathVariants` / `textPathVariantCount`에 보존한다.
  - 시점 marker와 중복 root alias는 `textStructural=false` row로 보존하고 outline stack에서는 제외한다.
  - row별 period 분포는 `cadenceKey`, `cadenceScope`, `latestAnnualPeriod`, `latestQuarterlyPeriod`로 기록한다.
  - accessor는 `periods()/ordered()/coverage()`로 최신우선 `Q4` alias projection을 바로 제공한다.
  - `show(period="2025Q4")`는 raw annual column `2025`를 alias로 받아들이고, 반환 컬럼도 `2025Q4`로 맞춘다.
  - comparable slot spine은 `textComparablePathKey` / `textComparableParentPathKey`로 따로 보존한다.
  - `structureRegistry()`는 comparable spine 기준 `activePathCounts`와 `structurePattern`을 계산해 구조 이동과 병합/분화를 진단한다.
  - `structureEvents()`는 comparable spine 기준으로 `fromPeriod -> toPeriod` 구조 전이 row를 만든다.
- 실제 구현 기준 파일:
  - `src/dartlab/providers/dart/docs/sections/textStructure.py`
  - `src/dartlab/providers/dart/docs/sections/pipeline.py`
  - `src/dartlab/providers/dart/company.py`

### 다종목 검증 기준과 다음 단계 (2026-03-18)

- 검증 샘플:
  - `005930`, `000660`, `035720`, `035420`, `373220`, `068270`
  - topic: `companyOverview`, `businessOverview`, `mdna`
- 현재 semantic alias는 보수적으로만 적용한다.
  - 실제 row merge가 확인된 축은 `companyOverview`, `mdna` 쪽이 먼저다.
  - `businessOverview`는 `영업의 개황 등 -> 영업현황`, `매출에 관한 사항 -> 매출` 같은 safe rename은 많지만, 병목은 여전히 `부문/구조 이동`을 흡수하는 matcher 쪽이다.
  - 다만 최신 연간 sparse의 큰 원인 하나는 raw source 손실이 아니라 `_reportRowsToTopicRows()`의 chapter content drop이었고, 지금은 장 제목 content를 보존하도록 수정했다.
  - 삼성전자 `businessOverview` 최신 annual coverage는 `2/318`에서 `177/436`으로 올라왔다.
- 다음 단계 우선순위:
  1. `topic + cadenceScope` 기준 `semantic registry` 도입
  2. parent-guard가 있는 alias만 추가 (`companyOverview` slot alias, `mdna` root alias 우선)
  3. 법인명/시점 marker/부문명은 alias가 아니라 별도 guard 또는 이벤트 레이어로 분리
  4. `businessOverview`는 alias dict 확장보다 `same/moved/split/merge` 판정이 가능한 구조 matcher를 먼저 올린다
  5. 성능은 `sections` materialized projection/cache를 추가해 first-build를 더 줄인다

## viewer.py — 공시뷰어 presentation layer

### textDocument 계층 (2026-03-18)

- `viewerBlocks()`는 여전히 원자 블록 단위(`text`, `structured`, `raw_markdown`, `finance`, `report`)를 반환한다.
- 그 위에 `viewerTextDocument()`를 추가하여 **텍스트 전용 타임라인 문서**를 만든다.
- 기본 단위는 `body text block`이다.
  - `heading` 블록은 다음 `body` 블록의 section header로 흡수한다.
  - body 앞머리의 짧은 heading line도 현재는 viewer 단계에서 구조 anchor로 분리하지만, 장기적으로는 `sections text structure`로 이동한다.
  - 테이블/정형 블록은 textDocument에서 제외하고 하단 별도 구역에서 렌더링한다.
- `textDocument` 책임:
  - `PeriodRef` canonical period (`2024`, `2024Q1`)
  - section별 `latest` snapshot
  - section별 `timeline[]`
  - period별 `views[label] = { body, prevPeriod, diff }`
- 초기 UI는 `latest` 원문만 보여준다.
- timeline click 시 그 section만 `선택 period vs 직전 동주기` diff를 원문 위치에 맞춰 렌더링한다.
- `blocks`는 raw/non-text source layer, `textDocument`는 현재의 fully-renderable text layer다.
- 다만 `heading 추출`, `segment 분리`, `paragraph 분리`는 장기적으로 viewer가 아니라 `sections` 파생 계층으로 승격한다.

### 품질 검증 체크리스트 (매 변경 시 필수)

#### 1. 데이터 검증
- [ ] 삼성전자 companyOverview, businessOverview, salesOrder, dividend에서 viewerBlocks() 실행
- [ ] 삼성전자 companyOverview, businessOverview에서 viewerTextDocument() 실행
- [ ] text 블록: heading(소제목) vs body(서술형) 분류 정확한지
- [ ] heading 블록이 독립 본문으로 노출되지 않고 다음 body section header로 흡수되는가
- [ ] stale section에 최신 보유 period와 배지가 함께 노출되는가
- [ ] timeline이 절대 기간 라벨(2024, 2024Q1)만 쓰는가
- [ ] 클릭 시 선택 period와 직전 동주기만 비교하는가
- [ ] diff가 문서 순서대로 `same/removed/added` 위치를 보존하는가
- [ ] digest: 같은 유형 비교인지 (연간↔연간, Q1↔Q1), 숫자 추출이 의미 있는지
- [ ] structured 테이블: 기간 정렬, null 컬럼 제거
- [ ] finance 블록: scale/unit 정확

#### 2. 사용자 관점 검증
- [ ] 기간 라벨 일관성 (축약 금지, 2024/2024Q1 형식 통일)
- [ ] 첫 화면이 최신 원문만 보여주는가
- [ ] timeline을 눌렀을 때만 diff가 열리는가
- [ ] 텍스트가 body block 중심 보고서처럼 읽히는가 (섹션 헤더↔메타↔timeline↔본문)
- [ ] 기본 화면에 block별 raw 기간 선택기가 노출되지 않는가
- [ ] sticky 헤더와 겹치는 요소 없는가
- [ ] 호버/팝업 가려지지 않는가
- [ ] 전체화면 모드 정상 동작

### text 블록 분류 기준

| 분류 | 조건 | 처리 |
|------|------|------|
| heading | 3줄 이하 + 80자 미만 + 제목 패턴 | 제목 렌더링만, 변경 추적 없음 |
| body | 그 외 | digest + blame 적용 |

### 기간 라벨 규칙

- **모든 곳에서 동일 형식**: 2024, 2024Q1, 2024Q2, 2024Q3
- 축약 금지: `'24`, `24Q1` 등 사용하지 않음
- 사업보고서 = 연간 (2024), 분기/반기보고서 = 2024Q1/Q2/Q3

### digest 규칙

- 같은 보고서 유형 간 비교 (연간↔연간, Q1↔Q1)
- heading 블록에는 digest 생성하지 않음
- body 앞머리 inline heading도 diff/digest에서 제외
- 숫자 변경: 컨텍스트 포함 ("종속회사 232개 → 228개")
- 추가/삭제: 최대 3건, 나머지 "외 N건"
