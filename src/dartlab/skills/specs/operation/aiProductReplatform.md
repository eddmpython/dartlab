---
id: operation.aiProductReplatform
title: AI 제품 전환 — Agent Runtime 표면
kind: curated
scope: builtin
status: observed
category: operation
purpose: 옛 direct provider와 고정 research graph 제품 계약을 설치형 Agent Runtime, AG-UI, Runtime Center, Product Outcome 계약으로 전환하는 마이그레이션 기준이다.
whenToUse:
  - 기존 provider 설정 API와 UI를 제거할 때
  - /api/ask 또는 Agent Gateway 공개 이벤트를 바꿀 때
  - 채팅 UI를 Runtime Center와 연결할 때
inputs:
  - user question
  - runtimeId and sessionId
  - workspace context
outputs:
  - AG-UI stream
  - evidence refs
  - product outcome receipt
toolRefs:
  - ReadSkill
  - ReadCapability
  - EngineCall
  - RunPython
knowledgeRefs:
  - operation.aiEngine
  - operation.ui
  - operation.productDirection
sourceRefs:
  - dartlab://skills/operation.aiProductReplatform
requiredEvidence:
  - executionRef
  - sourceRef
expectedOutputs:
  - provider-neutral product path
  - explicit runtime recovery action
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
failureModes:
  - provider 설정 화면을 Runtime Center 옆에 계속 유지함
  - 내부 native event나 raw JSON을 채팅에 노출함
  - 설치되지 않은 runtime에서 가짜 fallback 답변을 만듦
forbidden:
  - 새 production path에서 direct provider, OAuth token store, Ollama pull을 호출하지 않는다.
  - 고정 Graph나 Loop를 새 정점 SSOT로 만들지 않는다.
examples:
  - /settings/providers를 /settings/runtimes 안내로 전환
  - /api/provider/*를 410 migration 응답으로 전환
linkedSkills:
  - operation.aiEngine
  - operation.ui
  - operation.productDirection
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: '2026-08-03'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 확정 제품 경계

```text
DartLab local UI
  -> /api/ask 또는 /api/agent/runs
  -> Agent Gateway
  -> Agent Runtime Engine
  -> 사용자 설치형 agent CLI
  -> DartLab MCP와 정식 데이터 엔진
```

- 공개 답변 진입점은 `dartlab.ask`와 `/api/ask`다.
- UI는 공통 `AiPort`와 local API adapter만 사용한다.
- provider별 로그인, model catalog, transcript는 CLI가 소유한다.
- Runtime Center는 상태, 설치 계획, MCP 연결 계획, runtime 선택을 한곳에서 제공한다.
- runtime이 없으면 heuristic 답변을 만들지 않고 단일 recovery action을 보여 준다.

## 호환 경로

- `/api/provider/validate`, profile secret, OAuth authorize/logout, Ollama pull은 410과 Runtime Center 안내를 반환한다.
- `/settings/providers`는 삭제된 설정 양식을 렌더하지 않고 Runtime Center로 안내한다.
- `provider` request 필드는 한 전환 기간 runtimeId alias로만 받으며 direct provider 이름은 거부하거나 무시한다.
- DART, EDGAR, FRED 같은 데이터 provider는 이 마이그레이션 대상이 아니다.

## 공개 이벤트

허용 표면은 `TEXT_MESSAGE_*`, `THINKING_DELTA`, `TOOL_CALL_*`, `STATE_*`, `ACTIVITY_*`, `VIEW_SPEC`, `APPROVAL_REQUESTED`, `RUN_FINISHED`, `RUN_ERROR`다. native event와 raw stderr는 adapter 안에 머문다.

## 완료 조건

1. 기본·분석 모드가 모두 Agent Runtime을 사용한다.
2. 세 runtime manifest와 driver가 실제 CLI handshake를 통과한다.
3. install과 MCP 설정이 digest 승인 전에는 실행되지 않는다.
4. MCP tools/list에 ask가 없고 canonical registry와 일치한다.
5. UI 타입검사와 build가 통과한다.
6. exact evidence 확인 전 Product Outcome이 verified로 올라가지 않는다.
7. 서버 종료, cancel, session eviction 뒤 child process가 남지 않는다.
8. 질문별 information coverage와 실제 사용 capability가 `runtimeCoverage`로 구분돼 공개된다.
9. 정량·비교·문서 답변은 인용 문자열 존재가 아니라 evidence payload의 값·기간·대상·주장을 통과해야 한다.
