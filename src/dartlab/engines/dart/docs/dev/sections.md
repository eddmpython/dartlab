# DART Docs Sections Development Guide

본체 위치:
- `src/dartlab/engines/dart/docs/sections/`

핵심 원칙:
- `sections`가 docs source of truth다.
- markdown/table 경계는 버리지 않는다.
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
- `Company.index`와 `Company.show()`의 뼈대를 제공한다.
- table-heavy topic은 raw markdown/table을 유지한 채 다시 추출 가능한 상태로 둔다.

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
