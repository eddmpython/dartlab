# DART Docs Sections Development Guide

본체 위치:
- `src/dartlab/engines/dart/docs/sections/`

핵심 원칙:
- `sections`가 docs source of truth다.
- markdown/table 경계는 버리지 않는다.
- 같은 topic 내부에서도 block을 합치지 않고 raw 큰 블록 순서는 `sourceBlockOrder`로 유지한다.
- 수평화 후 fine row의 안정 순서는 `blockOrder`로 관리한다.
- 셀 값은 요약/파생 결과가 아니라 해당 기간 원문 payload를 그대로 유지한다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- 기존 docs 개별 parser는 archive/legacy fallback로 남긴다.

## 운영 구조

- `mapper.py`
  - title normalization
  - `sectionMappings.json` lookup
- `extractors.py`
  - topic -> subtopic DataFrame 재구성
- `pipeline.py`
  - raw markdown 기반 horizontalization
- `runtime.py`
  - projection, semantic/detail topic 보조

## 역할

- 사업보고서의 기본 section 구조를 수평화한다.
- 수평화 단위는 `topic × blockType × blockOrder × period`다.
- 여기서 행은 큰 topic 자체가 아니라, topic을 정확히 절개한 내부 section/block unit이다.
- text row는 body block을 다시 `heading/body` 단위로 분해한 fine row를 포함한다.
- 원래 큰 block 경계는 `sourceBlockOrder`에 남긴다.
- 어떤 기간에만 존재하는 block/unit은 그 기간만 값이 있고 다른 기간은 `null`로 유지한다.
- `Company.index`와 `Company.show()`의 뼈대를 제공한다.
- table-heavy topic은 raw markdown/table을 유지한 채 다시 추출 가능한 상태로 둔다.

## 텍스트 품질 향상 원칙

- 텍스트 품질은 `sectionMappings.json` 하나만으로 해결되지 않는다.
- `sections` 품질을 끌어올리는 공식 경로는 아래 3층이다.
  1. `section title mapper`
     - `section_title -> topic` 정규화
     - 현재 `mapper.py` + `sectionMappings.json`이 담당
  2. `text structure mapper`
     - body 내부의 `가.`, `1.`, `(1)`, `①` 같은 소제목 레벨을 복원
     - `headingPath`, `segmentOrder`, `level` 같은 구조 메타를 만든다
  3. `segment matcher`
     - 기간 간 같은 텍스트 segment를 정렬하고 추가/삭제/이동을 보수적으로 판정한다
- 즉, `sections` 품질 향상은 단순 제목 매퍼 보강이 아니라 `문서 구조 매퍼`를 확장하는 일이다.
- viewer는 이 구조를 표시하는 소비자다. viewer 안에서 소제목/문단을 다시 추정하는 로직은 임시 보정으로만 둔다.

## 목표 계층

- raw source:
  - `topic × blockType × blockOrder × period`
- derived text structure:
  - `topic × blockOrder × segmentOrder × period`
- segment payload:
  - `textNodeType`, `textStructural`, `textLevel`, `textPath`, `textPathKey`, `textParentPathKey`
  - `textPathVariantCount`, `textPathVariants`, `textParentPathVariants`
  - `textSemanticPathKey`, `textSemanticParentPathKey`
  - `textSemanticPathVariants`, `textSemanticParentPathVariants`
  - `segmentKey`, `segmentOrder`, `segmentOccurrence`, `sourceBlockOrder`
  - `cadenceKey`, `cadenceScope`, `annualPeriodCount`, `quarterlyPeriodCount`
  - `latestAnnualPeriod`, `latestQuarterlyPeriod`

원칙:
- raw `sections` 셀 값은 계속 원문 payload를 유지한다.
- 소제목 분리와 문단 분리는 raw를 덮어쓰지 않고 파생 계층으로 추가한다.
- body row 수평화는 번호(`가.`, `1.`, `(1)`)가 바뀌어도 유지되도록 번호 제거 path를 우선 사용한다.
- text row identity는 raw block 위치가 아니라 `textPathKey + occurrence`를 우선 사용하고, 원래 큰 블록 위치는 `sourceBlockOrder`로만 보존한다.
- top-level heading이 현재 topic과 같은 의미면 `textPathKey`는 `@topic:{topic}` canonical root를 사용한다.
- `textSemanticPathKey`는 raw `textPathKey`를 덮어쓰지 않는 parallel semantic spine이다.
  - raw wording은 `textPathKey`에 남긴다.
  - row가 흡수한 과거 raw wording drift는 `textPathVariants`에 남긴다.
  - semantic alias는 `textSemanticPathKey`에서만 흡수한다.
  - 보수적으로 검증된 alias만 허용한다.
- 장 제목 content는 source-of-truth로 보존한다.
  - 소항목이 있어도 pending chapter text를 먼저 등록한다.
  - 이후 소항목이 같은 semantic row를 채우면 그 셀만 overwrite된다.
  - 장 제목에만 남아 있던 segment는 sparse row가 아니라 실제 최신 row로 살아남는다.
- `[2021년 12월]` 같은 시점 마커와 중복 topic alias heading은 row로는 보존하되 `textStructural=false`로 내려 구조 stack에는 넣지 않는다.
- row별 period 분포는 `cadenceScope`로 요약한다.
  - `annual`: 연간에만 존재
  - `quarterly`: Q1/Q2/Q3에만 존재
  - `mixed`: 연간과 분기에 모두 존재
  - `cadenceKey`: `annual,q1,q2,q3` 같은 finer set
- `projectCadenceRows(df, cadenceScope=..., includeMixed=...)`로 `sections` 내부에서 annual/quarterly/mixed row projection을 바로 만들 수 있다.
- `semanticRegistry(df, ...)` / `semanticCollisions(df, ...)`로 semantic spine 기준 raw wording drift와 collision을 바로 진단할 수 있다.
- `c.docs.sections`는 raw DataFrame을 감싼 source accessor다.
  - `c.docs.sections.filter(...)`처럼 DataFrame 연산을 그대로 쓸 수 있다.
  - 같은 경로에서 `c.docs.sections.raw`, `c.docs.sections.periods()`, `c.docs.sections.ordered()`, `c.docs.sections.coverage()`, `c.docs.sections.cadence(...)`, `c.docs.sections.semanticRegistry(...)`, `c.docs.sections.semanticCollisions(...)`를 쓴다.
  - `periods()/ordered()/coverage()`는 최신우선 + 연간 `Q4` alias projection이다.
  - `c.docs.sectionsOrdered()` / `c.docs.sectionsCoverage()` / `c.docs.sectionsCadence()` / `c.docs.sectionsSemanticRegistry()` / `c.docs.sectionsSemanticCollisions()`는 호환용 wrapper다.
- `show()`, `diff()`, viewer, AI가 같은 text structure를 공유해야 한다.

## 2026-03-18 현재 기준

- 이번 개선의 정확한 기준은 이 문서와 `src/dartlab/engines/dart/docs/DEV.md`다.
- 현재 `sections` 텍스트 row 정렬의 핵심은 아래 네 가지다.
  - `textPathKey + occurrence`가 논리 row identity다.
  - `sourceBlockOrder`는 원래 큰 블록 경계 보존용이다.
  - `@topic:{topic}` root는 같은 topic을 가리키는 top-level heading alias를 하나의 구조선으로 묶는다.
  - `textSemanticPathKey`는 안전한 wording drift만 흡수하는 병렬 의미 구조선이다.
  - `textStructural=false` row는 marker/alias 보존용이며 outline tree를 구성하지 않는다.
- 현재 row 메타 해석:
  - `cadenceScope=annual`: 연간 row
  - `cadenceScope=quarterly`: 분기 전용 row
  - `cadenceScope=mixed`: 연간/분기 공용 row
  - `latestAnnualPeriod`, `latestQuarterlyPeriod`: 각 cadence에서 마지막 실존 period
- 현재 공식 period projection helper:
  - `src/dartlab/engines/dart/docs/sections/_common.py:displayPeriod`
  - `src/dartlab/engines/dart/docs/sections/_common.py:reorderPeriodColumns`
- 현재 공식 cadence projection helper:
  - `src/dartlab/engines/dart/docs/sections/pipeline.py:projectCadenceRows`
- 현재 공식 semantic registry helper:
  - `src/dartlab/engines/dart/docs/sections/pipeline.py:semanticRegistry`
  - `src/dartlab/engines/dart/docs/sections/pipeline.py:semanticCollisions`
- 구현 파일:
  - `src/dartlab/engines/dart/docs/sections/textStructure.py`
  - `src/dartlab/engines/dart/docs/sections/pipeline.py`

## 다종목 검증 메모 (2026-03-18)

- 검증 종목:
  - `005930`, `000660`, `035720`, `035420`, `373220`, `068270`
- 대표 topic:
  - `companyOverview`, `businessOverview`, `mdna`
- 현재 semantic spine 결과:
  - `companyOverview`, `mdna`는 safe alias가 실제 row merge로 이어지는 케이스가 확인된다.
  - `businessOverview`는 `...에 관한 사항 -> 핵심 slot 이름` 같은 semantic rename은 많지만, 대다수 회사에서는 row count가 거의 줄지 않는다.
  - 해석: `businessOverview`의 병목은 wording drift보다 `부문 이동/구조 이동`이다.
  - 다만 최신 연간 sparse의 큰 원인 하나는 raw source 자체가 아니라 chapter content drop이었다.
  - 장 제목 content 보존 후 `005930` 최신 annual `businessOverview` coverage는 `177/436 (40.6%)`까지 회복됐다.
- 현재 안전 alias의 예:
  - `연결대상 종속기업/종속회사 개황 -> 연결대상 종속사 현황`
  - `조직개편 / 조직의 변경 -> 조직변경`
  - `유동성 및 자금조달과 지출 -> 유동성 및 자금조달`
  - `감사위원회에 관한 사항 -> 감사위원회`
  - `...에 관한 사항 -> slot name` 계열의 좁은 정규화
- 현재 금지 merge의 예:
  - `DX부문`, `CE부문`, `DS부문` 같은 부문명은 automatic merge 금지
  - 법인명 suffix 차이(`PTE`, `PTE. LTD`)는 heading alias가 아니라 별도 법인명 정규화 레이어가 필요
  - `산업의 특성`, `시장여건`, `경쟁환경`은 형제 slot이지 alias가 아니다

## 다음 품질/성능 우선순위

1. `topic + cadenceScope` 기준 `semantic registry`를 올린다.
2. parent guard가 있는 alias만 추가한다.
3. `businessOverview`는 alias dict보다 `same/moved/split/merge`를 판정하는 구조 matcher를 먼저 올린다.
4. `show()`/viewer가 `projectCadenceRows()`조차 직접 부르지 않도록 `sections` materialized projection/cache를 추가한다.
5. 다종목 all-topic collision 리포트를 정기적으로 돌려 unsafe merge를 감시한다.

## production 정책

- sections 우선 topic은 `Company.show()`가 sections extractor를 먼저 탄다.
- sections에서 안정적으로 재구성되지 않는 topic만 legacy parser를 유지한다.
- `show()`는 sections 결과를 우선 사용하고, legacy parser는 fallback이다.

## coverage 검증

검증 스크립트:
- `experiments/056_sectionMap/051_validateCompanyShowCoverage.py`
- `experiments/056_sectionMap/052_validateAdditionalShowCoverage.py`

현재 전회사(`283`) 기준 failure `0`:
- `salesOrder`
- `riskDerivative`
- `segments`
- `rawMaterial`
- `costByNature`
- `tangibleAsset`는 legacy 유지 기준으로 검증 완료
