# Agent Runtime 계약

## CLI

```text
dartlab agent status [runtimeId] --refresh
dartlab agent install <runtimeId>
dartlab agent connect <runtimeId>
dartlab agent sessions --limit <N>
dartlab ask --runtime <runtimeId> "질문"
```

`install`과 `connect`는 기본 실행에서 계획과 digest만 출력한다. 같은 명령에 `--approve-digest <digest>`를 붙였을 때만 그 계획을 실행한다.

## HTTP API

| 메서드 | 경로 | 의미 |
|---|---|---|
| GET | `/api/agent/runtimes` | 설치, 인증, 프로토콜, MCP, 준비 상태와 서버 기본값 조회 |
| POST | `/api/agent/runtimes/default` | 준비 완료 런타임을 새 대화 기본값으로 저장 |
| POST | `/api/agent/runtimes/{id}/probe` | 상태 캐시를 무시하고 다시 확인 |
| POST | `/api/agent/runtimes/{id}/install/plan` | 승인 가능한 설치 계획 생성 |
| POST | `/api/agent/runtimes/{id}/login/plan` | 공식 로그인 명령 생성 |
| POST | `/api/agent/runtimes/{id}/mcp/plan` | 승인 가능한 DartLab MCP 연결 계획 생성 |
| POST | `/api/agent/runtimes/install/apply` | digest가 일치하는 설치 계획 실행 |
| POST | `/api/agent/runtimes/mcp/apply` | digest가 일치하는 MCP 연결 계획 실행 |
| POST | `/api/agent/sessions` | 런타임에 결속된 대화 세션 열기 또는 재개 |
| DELETE | `/api/agent/sessions/{sessionId}` | 세션과 자식 프로세스 종료 |
| GET | `/api/agent/sessions/{sessionId}/events` | sequence 이후 이벤트 재생 |
| POST | `/api/agent/sessions/{sessionId}/cancel` | 현재 네이티브 turn 취소 |
| GET | `/api/agent/product-outcomes/{outcomeId}/evidence/{refId}` | 상태 변경 없이 exact evidence 조회 |
| POST | `/api/agent/product-outcomes/{outcomeId}/verify` | 사용자가 확인한 exact ref를 검증 상태로 기록 |

## 준비 상태

한 런타임은 설치, 인증, embedded grounding protocol, DartLab MCP 연결을 모두 통과할 때만 `groundedReady=true`다. 상태 응답의 `readiness`는 `install`, `auth`, `protocol`, `grounding`, `ready`를 분리한다.

## 공개 스트림

공개 이벤트 이름은 `src/dartlab/ai/runtime/contracts.py`의 `PUBLIC_AGENT_EVENT_KINDS`가 정본이고 TypeScript 계약은 여기서 생성한다. 현재 종류는 다음과 같다.

```text
TEXT_MESSAGE_START
TEXT_MESSAGE_CONTENT
TEXT_MESSAGE_END
THINKING_DELTA
TOOL_CALL_START
TOOL_CALL_ARGS
TOOL_CALL_END
TOOL_CALL_RESULT
STATE_SNAPSHOT
STATE_DELTA
MESSAGES_SNAPSHOT
ACTIVITY_SNAPSHOT
ACTIVITY_DELTA
VIEW_SPEC
APPROVAL_REQUESTED
RUN_FINISHED
RUN_ERROR
```

성공 종료는 최종 근거 ID와 품질 metadata를 담는다. 실패 종료는 최종 근거를 commit하지 않고 candidate ref와 공개 가능한 실패 이유를 담는다.
