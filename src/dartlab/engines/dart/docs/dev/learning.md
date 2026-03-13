# DART Sections Learning Workflow

본 문서는 DART docs `sections` 매퍼와 extractor를 지속적으로 갱신하는 내부 운영 문서다.

## 목적

- 신규 docs parquet가 추가될 때 기존 수평화가 유지되는지 확인한다.
- 새 raw title, 새 detail table, 새 업종 특화 row를 `sections` 체계에 흡수한다.
- `Company.index / show / trace` 계약이 깨지지 않게 한다.

## Source Of Truth

- docs 구조의 단일 진실 원천은 `sections`다.
- `src/dartlab/engines/dart/docs/sections/`가 production 로직이다.
- 기존 docs 개별 parser는 archive/legacy fallback이다.
- 새 docs 기능은 legacy parser에 먼저 추가하지 않고, 가능하면 `sections` extractor에 먼저 추가한다.

## 주요 파일

- `src/dartlab/engines/dart/docs/sections/mapper.py`
- `src/dartlab/engines/dart/docs/sections/mapperData/sectionMappings.json`
- `src/dartlab/engines/dart/docs/sections/extractors.py`
- `src/dartlab/engines/dart/docs/sections/pipeline.py`
- `src/dartlab/engines/dart/docs/sections/runtime.py`
- `src/dartlab/engines/dart/company.py`

## 기본 원칙

- `sections`는 docs source of truth다.
- markdown/table 경계를 버리지 않는다.
- table-heavy topic은 `sections`에서 다시 추출한다.
- `Company.show()`가 기본 경로다.
- legacy parser는 즉시 삭제하지 않고 fallback으로만 유지한다.

## sections 우선 topic

- `salesOrder`
- `riskDerivative`
- `segments`
- `rawMaterial`
- `costByNature`

## legacy 유지 topic

- `tangibleAsset`

## 신규 docs parquet 반영 절차

1. 신규 parquet를 `data/dart/docs/`에 반영한다.
2. core horizontalization이 깨지지 않는지 확인한다.
3. 새 raw title과 detail row를 수집한다.
4. broad canonical로 흡수 가능한 것은 `sectionMappings.json`에 반영한다.
5. table/detail row는 `extractors.py` 또는 `runtime.py`의 semantic/detail topic으로 흡수한다.
6. `Company.show()` coverage를 다시 측정한다.
7. 이 문서와 `src/dartlab/engines/dart/DEV.md`를 먼저 갱신하고, 그 뒤 규칙 파일(`CLAUDE.md`, `AGENT.md`)은 원칙 수준만 유지한다.

## 변경 판단 기준

- `Company.index`가 같은 source story를 유지해야 한다.
- `Company.show()`는 topic별 계약을 유지해야 한다.
  - statement topic -> DataFrame
  - report topic -> DataFrame
  - sections-heavy topic -> subtopic DataFrame
- `trace()`는 `finance/report/docs` 우선순위를 그대로 설명해야 한다.

## 하지 말 것

- 상위 facade나 CLI에서 docs 구조를 우회해 고치지 않는다.
- `docs/` 공개 문서에 내부 운영 절차를 바로 쓰지 않는다.
- 새 docs 기능을 legacy parser에만 추가하지 않는다.
