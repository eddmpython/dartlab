# DART Docs Sections Development Guide

본체 위치:
- `src/dartlab/engines/dart/docs/sections/`

핵심 원칙:
- `sections`가 docs source of truth다.
- markdown/table 경계는 버리지 않는다.
- 같은 topic 내부에서도 block을 합치지 않고 `blockOrder`로 원문 순서를 유지한다.
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
  - `headingPath`, `level`, `body`, `paragraphs`

원칙:
- raw `sections` 셀 값은 계속 원문 payload를 유지한다.
- 소제목 분리와 문단 분리는 raw를 덮어쓰지 않고 파생 계층으로 추가한다.
- `show()`, `diff()`, viewer, AI가 같은 text structure를 공유해야 한다.

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
