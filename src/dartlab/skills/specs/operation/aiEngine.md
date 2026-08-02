---
id: operation.aiEngine
title: AI Engine — Bring Your Agent Runtime
kind: curated
scope: builtin
status: observed
category: operation
purpose: 설치된 Codex CLI, Claude Code, ACP 호환 agent가 인증·모델·세션을 소유하고 DartLab은 Skill OS·MCP·금융 엔진·근거 계약을 제공하는 AI 실행 SSOT다.
whenToUse:
  - dartlab.ask 또는 /api/ask 실행 경계를 변경할 때
  - Codex, Claude Code, Cline runtime driver를 추가하거나 수정할 때
  - Runtime Center의 탐지, 설치, MCP 연결, 승인 UX를 변경할 때
  - AgentEvent와 AG-UI projection을 변경할 때
inputs:
  - 사용자 질문
  - 선택적 runtimeId와 sessionId
  - workspace context
outputs:
  - provider-neutral AgentEvent stream
  - AG-UI public stream
  - DartLab evidence refs와 artifacts
capabilityRefs: []
toolRefs:
  - ReadSkill
  - GetSkillBody
  - ReadCapability
  - EngineCall
  - RunPython
  - WebSearch
  - SaveArtifact
knowledgeRefs:
  - operation.productDirection
  - operation.productCycle
  - operation.architecture
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.aiEngine
  - dartlab://agent-runtime
requiredEvidence:
  - runtimeId
  - sessionId
  - executionRef
  - sourceRef
expectedOutputs:
  - 설치형 agent runtime 실행 결과
  - MCP 기반 DartLab 근거
  - 명시적 권한 승인 또는 안전한 거부
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
  - runtime별 business rule과 tool 목록을 driver에 복사함
  - CLI stdout 문장을 제품 계약으로 파싱함
  - 사용자 승인 없이 설치나 전역 MCP 설정을 실행함
  - DartLab이 provider API key, OAuth token, native transcript를 저장함
  - MCP 안에서 ask를 다시 호출해 runtime 재귀를 만듦
  - 고정 Graph나 Loop를 모든 질문에 강제함
forbidden:
  - direct model SDK를 production ask 경로에서 호출하지 않는다.
  - provider별 OAuth와 API key 입력 UI를 만들지 않는다.
  - shell 문자열, shell=True, 무검증 install argv를 실행하지 않는다.
  - 모델명과 vendor명을 Product Outcome 완료 조건에 넣지 않는다.
examples:
  - dartlab.ask("삼성전자 수익성", runtimeId="codex")
  - dartlab agent status --refresh
  - dartlab agent install cline
  - dartlab agent connect codex
procedure:
  - Runtime manifest에서 실행 파일 후보와 protocol driver를 읽는다.
  - 15초 TTL probe로 설치·버전, DartLab MCP 연결, embedded grounding capability를 확인하고 셋 다 준비된 groundedReady runtime만 선택한다.
  - native session을 열거나 저장된 opaque session mapping으로 재개한다.
  - 짧은 analysis capsule과 MCP 도구를 agent에 제공한다.
  - native event를 AgentEvent로 투영하고 AG-UI allowlist로 공개한다.
  - install과 MCP connect는 계획 argv와 SHA-256 digest를 먼저 보여주고 동일 digest 승인 뒤에만 실행한다.
linkedSkills:
  - operation.productDirection
  - operation.productCycle
  - runtime.mcp
  - operation.ui
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-02'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 제품 경계

```text
dartlab.ask / /api/ask / DartLab UI
  -> Agent Runtime Engine
  -> Codex app-server | Claude stream-json | ACP v1
  -> 사용자의 agent 계정, 모델, native session
  -> DartLab MCP
  -> Skill OS / Company / scan / analysis / macro / quant / evidence
```

DartLab은 모델 provider가 아니다. 사용자가 이미 로그인한 agent CLI를 실행하고, 그 agent가 DartLab MCP로 공시·재무·시장 능력을 사용하게 한다. runtrol은 별도 레포의 설계 참고이며 runtime dependency, daemon, shared package가 아니다.

## 코드 SSOT

| 책임 | 정본 |
|---|---|
| 공개 진입점 | `dartlab.ask`, `/api/ask` |
| 런타임 조정 | `src/dartlab/ai/runtime/engine.py` |
| runtime 목록·실행 argv | `src/dartlab/ai/runtime/manifests/*.toml` |
| Codex protocol | `drivers/codexAppServer.py` |
| Claude protocol | `drivers/claudeStreamJson.py` |
| ACP protocol | `drivers/acp.py` |
| process 수명주기 | `processSupervisor.py` |
| 이벤트 계약 | `contracts.AgentEvent`, `schema.py` |
| MCP 연결 계획 | `mcpBootstrap.py` |
| 설치 계획 | `installManager.py` |
| 세션 mapping | `sessionStore.py` |
| UI 관리 표면 | `/api/agent/*`, Runtime Center |
| 북극성 결과 원장 | `src/dartlab/productOutcome.py` |

`agent.py`는 runtime event를 기존 `TraceEvent` adapter로 투영한다. 새 실행 의미는 runtime package가 정본이며 provider별 조건문을 gateway와 UI에 추가하지 않는다.

## 안정 계약

- manifest가 runtime ID, executable 후보, version args, launch args, Windows native launch, install args, embedded grounding 지원, 공식 문서를 선언한다.
- process 실행은 argv 배열과 `shell=False`만 사용한다.
- stdout/stderr frame은 각각 1 MiB와 256 KiB 한도를 적용한다.
- 세션 event ring은 256건 또는 4 MiB로 제한하고 sequence 이후 replay를 지원한다.
- hot session은 최대 4개이며 퇴거·서버 종료 시 child process를 닫는다.
- DartLab DB에는 session ID, runtime ID, native session ID, cwd mapping만 저장한다. transcript는 저장하지 않는다.
- 알 수 없는 native event는 버리지 않고 `native` event로 보존한다.
- application context는 종목, 기간, 보고 모드, include/exclude, bounded dashboard snapshot만 16 KiB 이하로 전달한다. 대화 transcript는 CLI native session이 소유한다.
- native 성공, DartLab grounding tool 성공, 본문에 인용된 표 또는 문서, 값, 기준일 exact ref가 모두 있어야 공개 답변을 커밋한다.

## 권한과 설치

- 탐지는 자동이지만 설치와 전역 MCP 설정은 자동 실행하지 않는다.
- Runtime Center와 CLI는 먼저 exact argv, 공식 문서 URL, digest를 표시한다.
- apply 요청의 digest와 현재 manifest로 다시 계산한 계획이 모두 일치해야 실행한다.
- Codex와 ACP의 native approval request는 UI로 전달한다.
- Claude print mode는 MCP 지연 검색용 `ToolSearch` 하나와 registry가 read-only로 판정한 DartLab MCP 도구만 노출·허용하며 write 권한을 확대하지 않는다.
- Codex, Claude, Cline의 MCP 연결은 각 공식 CLI 계획과 exact digest 승인 뒤에만 적용한다. 설치만 된 runtime은 실행 가능 상태가 아니다.
- 전역 MCP 설정 파일이 있어도 embedded protocol이 MCP tool을 실제 노출하지 않으면 groundedReady가 아니다. Cline 3.0.49 ACP는 이 조건을 만족하지 않아 fail-closed다.
- agent 인증은 해당 CLI의 공식 로그인 명령에서만 수행한다.

## MCP 계약

- MCP tools/list는 `ai.tools.registry.CANONICAL_V2`에서만 파생한다.
- `ask`는 광고하지 않는다. agent가 MCP ask를 통해 agent를 재귀 실행하면 안 된다.
- 권장 순서는 `ReadSkill -> ReadCapability -> EngineCall 또는 RunPython -> ref가 있는 답변`이다.
- Skill 읽기나 모델 산문은 북극성 `grounded`가 아니다. 실제 계산 도구가 성공하고 정형 ref가 있어야 한다.

## Product Outcome 연결

상태는 `started -> scoped -> grounded -> delivered -> verified -> retained` 순서다.

- 질문 시작으로 `started`를 발급한다.
- canonical 실행 도구가 정형 ref를 반환해야 `scoped`, `grounded`가 된다.
- 성공 turn과 근거가 함께 있어야 `delivered`다.
- 사용자가 같은 outcome의 exact ref를 열어 서버의 opaque hash receipt가 일치해야 `verified`다.
- 근거 확인 API는 active runtime의 bounded evidence journal에서 exact ref detail을 먼저 resolve한 뒤 hash receipt를 검증한다.
- tool call, 텍스트 생성, evidence chip 렌더만으로 verified를 자동 기록하지 않는다.

## 검증

- `tests/ai/runtime/`: manifest, protocol projection, supervisor, session, engine vertical slice.
- `tests/productOutcome/`: 단조 전이, duplicate receipt, privacy schema.
- `tests/mcp/`: registry와 tools/list drift, 재귀 ask 부재.
- UI는 `npm run check`와 `npm run build`를 모두 통과해야 한다.
- 최종 release 전 실제 설치 계정으로 Codex, Claude, ACP handshake를 각각 확인하고 child process가 남지 않았는지 점검한다.
