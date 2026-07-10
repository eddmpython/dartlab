---
id: runtime.toolComposition
title: Tool Composition — 11 도구 조합 패턴 SSOT
kind: curated
scope: builtin
status: drafted
category: runtime
purpose: dartlab agent 의 25+ 도구 (ai/tools/registry.py SSOT) 의 조합 패턴 카탈로그 — 어떤 질문에 어떤 도구를 어떤 순서로 호출하는지. parallel vs sequential 가이드. FSI "Bold leaf" 패턴 흡수.
whenToUse:
  - tool composition
  - 도구 조합
  - parallel vs sequential
  - tool selection
  - 도구 선택 패턴
inputs:
  - 사용자 질문 의도
  - 가용 도구 list (registry._SPECS)
outputs:
  - 도구 호출 순서 + parallel 가능 여부
  - evidence GATE 적용 시점
toolRefs: []
knowledgeRefs:
  - runtime.workbenchEvidenceFlow
  - runtime.mcp
sourceRefs:
  - dartlab://skills/runtime.toolComposition
requiredEvidence:
  - skillRef
  - executionRef
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
    status: limited
linkedSkills:
  - runtime.workbenchEvidenceFlow
  - runtime.untrustedContent
---

## 분류

### 1. 정보 수집 (parallel 가능)

- `EngineCall` (구체 axis) × N — independent axis 동시 호출.
- `RunPython` + `gather()` — 데이터 수집 독립적 호출 parallel.
- `WebSearch` — 외부 search, untrusted wrap 자동.

### 2. 의존 chain (sequential 강제)

- `EngineCall("Company.panel")` → `EngineCall("Company.filings")` (rcept_no 의존).
- `gather()` → `RunPython` (raw 데이터 변환).
- `EngineCall` → `EvidenceGate` (결과 검증 강제).

### 3. Bold leaf (Write 권한 1 개)

FSI 패턴 — 다음 단일 도구만 Write 가능:
- `SaveArtifact` (사용자 산출물 저장)

다른 도구는 read-only. 데이터 mutation 단일 책임.

### 4. 자율 작업 패턴

- `RunWorkbench` (자율 실행 — `runtime.workbenchEvidenceFlow` SSOT)
- `ProposeRecipe` (사용자 검토 후 박힘)
- `CreateUserSkill` (사용자 skill 저장)

### 5. evidence + 신뢰 결합

모든 정보 수집 후 → `EvidenceGate(refs)` 강제 → `GroundingCheck(claims)` 선택. 외부 본문 (web/news) 자동 `wrap_external_in_result` (`runtime.untrustedContent` SSOT).

## 권장 흐름

1. 사용자 질문 분류 (단일 회사 / 횡단 / 매크로 / 시나리오).
2. axis 결정 — `ReadSkill` + `ListEngineGaps` 가이드.
3. parallel 도구 동시 호출 (chat-native concurrent — agent.py 본체).
4. evidence GATE 통과 후 답변 합성.

## 안티패턴

- 도구 호출 → 결과 무시 → 추가 호출 ("재호출 round" 회피, `engines.search.disclosureSearch` 가드).
- Bold leaf 외 다른 도구로 Write (`SaveArtifact` 없이 사용자 산출물 저장 금지).
- evidence GATE 우회 — 모든 숫자 claim 강행.

## 기본 검증

본 spec 의 5 분류는 ai/tools/registry.py 의 25+ 도구 그대로 매핑. 도구 추가/제거 시 본 spec + agent.py system prompt 동시 갱신.
