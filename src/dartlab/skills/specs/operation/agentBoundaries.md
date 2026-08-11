---
id: operation.agentBoundaries
title: Agent Boundaries — checkAgentBoundary lint 외부 공개 SSOT
kind: curated
scope: builtin
status: observed
category: operation
purpose: tests/audit/checkAgentBoundary.py lint 룰의 외부 공개 SSOT — graph 회귀 가드 8 번째 / chat-native 본체 유지 / Bold leaf 단일 Write / workbench 본체화 금지 4 회귀 신호. 외부 기여자 PR 작성 시 자가 점검 표준.
whenToUse:
  - agent boundaries
  - checkAgentBoundary
  - graph 회귀 가드
  - 본체화 금지
  - workbench boundary
inputs:
  - PR diff (ai/* + ai/tools/* + workbench/* 변경)
outputs:
  - boundary 위반 list
  - lint pass / fail
toolRefs: []
knowledgeRefs:
  - operation.architecture
sourceRefs:
  - dartlab://skills/operation.agentBoundaries
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
  - operation.architecture
  - runtime.toolComposition
---

## 4 회귀 신호

### 1. graph 회귀 가드

다음 패턴 추가 금지:
- `BRIEF` / `WORK` / `CRITIQUE` / `COMPOSE` / `GATE` / `HARVEST` 식 고정 노드 이름
- `*Loop` / `*Graph` / `*Kernel` 클래스 신설
- `verify 강제` / `GATE 차단` / `requiredEvidence 강제` 표현
- workbench 흐름 분기 4 번째 추가

본체 `ai/agent.py` = chat-native + LLM 자율 tool calling. graph 노드 추가는 본체 회귀 시도로 분류.

### 2. chat-native 본체 유지

- 본체 변경 최소 — 신규 능력은 `ai/tools/*` 별 파일 추가 + `registry._SPECS` dict 항목.
- 본체 system prompt 변경 시 → `runtime.promptingPatterns` 동시 갱신.

### 3. Bold leaf 단일 Write

- `SaveArtifact` 만 Write 권한. 다른 도구 Write 추가 금지.

### 4. workbench 본체화 금지

- workbench (`workbench/runner.py` 등) 의 자율 실행 흐름 분기 추가 금지.
- 흐름은 `runtime.workbenchEvidenceFlow` SSOT 단일.

## 실행

```bash
# PR 작성 후 자가 점검
uv run python -X utf8 tests/audit/checkAgentBoundary.py
# → 위반 list (0 = pass)

# CI 측 자동 실행 (tests/run.py preflight 일부)
```

## 강행 룰

1. PR 작성 전 본 lint 통과 확인.
2. 본 lint 신규 룰 추가 → 본 spec을 정본으로 갱신한다. 로컬 memory에 같은 본문을 복제하지 않는다.
3. workbench 흐름 분기 추가 의도 → 본 spec과 `runtime.workbenchEvidenceFlow`를 검토한 뒤 결정.

## 기본 검증

- lint 0 위반 (CI gate).
- 회귀 사례 발생 시 incidents.md 기록.
