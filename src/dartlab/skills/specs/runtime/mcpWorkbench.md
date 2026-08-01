---
id: runtime.mcpWorkbench
title: MCP 외부 AI Workbench 연결
kind: curated
scope: builtin
status: unverified
category: runtime
purpose: MCP 클라이언트가 DartLab skill resolver와 workbench action을 같은 방식으로 쓰게 한다.
whenToUse:
  - MCP에서 DartLab 쓰기
  - 외부 AI가 DartLab skill 검색
inputs:
  - MCP client
outputs:
  - canonical workbench flow
  - skill search flow
toolRefs:
  - ReadSkill
  - ReadCapability
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - execution
  - executionRef
  - sourceRef
expectedOutputs:
  - MCP setup guide
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: unsupported
  pyodide:
    status: unsupported
    limitations:
      - MCP stdio는 브라우저 Pyodide runtime이 아니라 로컬/서버 프로세스 경로다.
failureModes:
  - legacy engine tool을 기본 표면으로 안내
forbidden:
  - MCP에서 skills 의미론을 새로 정의
examples:
  - MCP에서 DartLab skill을 어떻게 쓰나
source:
  type: curated_markdown
  owner: dartlab
lastUpdated: "2026-08-01"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 절차

- MCP 기본 표면은 workbench action과 skill resolver다.
- 먼저 `ReadSkill`로 목적 skill을 찾는다.
- API 상세와 canonical `apiRef`는 `ReadCapability`로 확인한다.
- 단일 공개 API는 `EngineCall`, 여러 결과의 결합·가공만 `RunPython`으로 실행한다.
- 실제 이름과 schema는 `tools/list`를 정본으로 삼는다. 목록 밖 legacy alias와 내부 도구는 호출하지 않는다.

