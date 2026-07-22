---
id: operation.apiContract
title: API Contract — dartlab 호출 규칙 단일 진실의 원천
kind: curated
scope: builtin
status: observed
category: operation
purpose: API Contract — dartlab 호출 규칙 단일 진실의 원천 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - API Contract — dartlab 호출 규칙 단일 진실의 원천
  - api contract
  - 1. 단일 진입점 — Dual Access (call form + attr form) 로 간다
  - 공개 진입점 정책
  - 엔진명 축 dispatch
  - provider facade 예외
  - 구현
  - 좋은 예
  - 내부 series-tuple 빌더
  - 검증 방법
inputs:
  - 작업 목적
  - 대상 엔진 또는 실행 환경
  - 검증 범위
outputs:
  - selected skill
  - capability/docstring handoff
  - verification gate
capabilityRefs: []
toolRefs:
  - search_reference
knowledgeRefs:
  - start.dartlabSkillOs
sourceRefs:
  - dartlab://skills/operation.apiContract
procedure:
  - 공개 진입점은 provider facade 예외를 제외하면 엔진명/축 dispatch 로만 노출한다.
  - provider facade 신규 추가는 장기 유지 가치와 회사/시장 단위 안정 surface 인지 먼저 검토한다.
  - 내부 helper/ops/recipe/builder 함수는 공개 API, migration target, 사용자 예시로 안내하지 않는다.
  - 1. 단일 진입점 — Dual Access (call form + attr form) 로 간다 기준을 확인한다.
  - 구현 기준을 확인한다.
  - 좋은 예 기준을 확인한다.
  - 내부 series-tuple 빌더 기준을 확인한다.
  - 검증 방법 기준을 확인한다.
  - '**IS · CIS · CF (flow)** — 4 분기 모두 있을 때만 단순 합 (3 분기 이하 → None).'
  - '**BS (stock)** — Q4 (= 연말잔액). 없으면 그 해 가장 최근 분기.'
  - Company 중심 공개 함수는 종목코드 또는 Company를 받고, data는 typed request와 동형 JSON mapping을 받는다.
  - data의 public axis는 catalog와 query 둘뿐이며 factor와 lineage는 별도 axis로 만들지 않는다.
  - 추가 import 금지 — `import dartlab` 하나로 모든 기능 접근.
requiredEvidence:
  - skillRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 작업 경로
  - 확인한 근거
  - 검증 결과
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
    notes: []
failureModes:
  - Skill OS 검색 없이 과거 문서 경로를 직접 찾음
  - API schema를 skill 본문에 중복해 docstring/capability와 어긋남
  - 검증 게이트 없이 변경 또는 답변을 완료 처리함
forbidden:
  - 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다.
  - 공개 호출 방식, 대표 반환 형태, 오류/제한 동작을 skill과 불일치한 채 방치하지 않는다.
  - provider facade 밖에서 엔진명/축 dispatch 가 아닌 새 공개 진입점을 만들지 않는다.
  - 내부 helper/ops/recipe/builder 함수를 사용자 migration 대상이나 공식 사용 예시로 노출하지 않는다.
examples:
  - API Contract — dartlab 호출 규칙 단일 진실의 원천 규칙 확인
  - api-contract 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: api-contract
  format: markdown
lastUpdated: '2026-07-22'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## Skill OS 흡수 규칙

- 이 skill이 공식 진입점이다. 삭제된 운영 문서 경로를 다시 안내하지 않는다.
- 공개 호출 방식과 대표 반환 형태는 skill에서 확인하고, 세부 필드는 capability/docstring으로 검산한다.
- 분석이나 변경 결과는 ref, 실행 로그, 테스트 결과로 검증한다.

## 공개 진입점 정책

- 기본 원칙: 공개 진입점은 엔진명/축 dispatch 방식으로만 만든다.
- provider facade 는 예외적으로 허용하지만, 새 메서드는 장기 유지 가치가 있는 회사/시장 단위 안정 surface 일 때만 추가한다.
- provider facade 밖에서는 별도 공개 함수, 편의 wrapper, migration target 을 만들지 않는다.
- 내부 helper, ops, builder, recipe 실행 함수는 구현 세부사항이다. 사용자 문서, CHANGELOG, Skill 예시에서 직접 호출 대상으로 안내하지 않는다.
- 새 기능은 먼저 기존 엔진의 축으로 수용 가능한지 판단한다. 축으로 표현할 수 없고 회사 객체의 자연스러운 장기 기능일 때만 provider facade 승격을 검토한다.
- 공개 문서에서 허용되는 표현은 `dartlab.{engine}("{axis}", ...)`, `Company.{method}(...)`, 또는 이미 정의된 provider facade 뿐이다.
- `data` 엔진도 같은 규칙을 따르며 공개 axis는 `catalog`, `query` 두 개다. factor, graph, narrative, resource를 별도 axis나 helper로 노출하지 않는다.
- 다중 자산 질의처럼 종목코드 하나로 표현할 수 없는 엔진은 typed request와 동일한 JSON mapping을 함께 받는다. 외부 프로세스와 EngineCall이 별도 adapter 없이 같은 계약을 호출할 수 있어야 한다.

## 실행 순서

- 공개 진입점 변경이면 먼저 위 공개 진입점 정책을 통과하는지 검토한다.
- 1. 단일 진입점 — Dual Access (call form + attr form) 로 간다 기준을 확인한다.
- 구현 기준을 확인한다.
- 좋은 예 기준을 확인한다.
- 내부 series-tuple 빌더 기준을 확인한다.
- 검증 방법 기준을 확인한다.
- **IS · CIS · CF (flow)** — 4 분기 모두 있을 때만 단순 합 (3 분기 이하 → None).
- **BS (stock)** — Q4 (= 연말잔액). 없으면 그 해 가장 최근 분기.
- Company 중심 엔진의 공개 함수는 종목코드 또는 Company를 받는다. `data("catalog")`, `data("query")`는 CatalogQuery, DataQuery 또는 동형 JSON mapping을 받는 명시적 예외다.
- 추가 import 금지 — `import dartlab` 하나로 모든 기능 접근.

