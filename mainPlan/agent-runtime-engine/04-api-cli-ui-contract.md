# 04. API, CLI and UI Contract

## 1. Server API

신규 router는 `src/dartlab/server/api/agentRuntime.py`가 소유한다.

### Runtime lifecycle

| Method | Path | 결과 |
|---|---|---|
| GET | `/api/ai/runtimes` | lazy cached descriptor list |
| POST | `/api/ai/runtimes/{runtimeId}/probe` | forced fresh probe |
| POST | `/api/ai/runtimes/{runtimeId}/install-plan` | non-mutating install plan |
| POST | `/api/ai/runtimes/{runtimeId}/install` | approval receipt와 plan digest 실행 |
| POST | `/api/ai/runtimes/{runtimeId}/auth` | provider-owned auth surface 시작 |
| POST | `/api/ai/runtimes/{runtimeId}/mcp/connect` | official CLI config command 실행 |
| POST | `/api/ai/runtimes/{runtimeId}/mcp/disconnect` | DartLab-owned exact entry만 제거 |

### Session lifecycle

| Method | Path | 결과 |
|---|---|---|
| POST | `/api/ai/sessions` | runtime 선택, new/resume session |
| GET | `/api/ai/sessions/{sessionId}` | metadata and capability state |
| POST | `/api/ai/sessions/{sessionId}/turns` | turn handoff |
| DELETE | `/api/ai/sessions/{sessionId}/turns/current` | bounded cancel |
| POST | `/api/ai/sessions/{sessionId}/approvals/{approvalId}` | digest-bound answer |
| GET | `/api/ai/sessions/{sessionId}/events?cursor=` | SSE replay and live events |
| DELETE | `/api/ai/sessions/{sessionId}` | supervisor pointer close, native transcript 보존 |

모든 mutating endpoint는 기존 local admin, Origin, CSRF 정책에 등록한다. install과 auth는 local loopback에서만 허용한다.

`POST /api/ask`는 migration compatibility facade다. selected ready runtime에 session/turn을 만들고 기존 stream consumer가 받을 event projection을 반환한다. 신규 UI는 session API를 직접 쓴다.

## 2. Runtime selection

default는 provider ranking이 아니다.

1. 사용자가 고정한 ready runtime.
2. 마지막 verified analysis를 완료한 ready runtime.
3. required capability를 만족하는 유일한 ready runtime.
4. 여러 개면 사용자의 선택 필요 상태를 UI에 표시.

모델 가격, 이름, 추정 성능으로 자동 vendor ranking하지 않는다. requested attachment, approval, resume 같은 capability 부족은 명시적으로 거부한다.

## 3. CLI

기존 `dartlab setup`과 `dartlab status`의 provider surface를 다음으로 교체한다.

```text
dartlab agent list
dartlab agent doctor [runtime]
dartlab agent install <runtime>
dartlab agent login <runtime>
dartlab agent connect <runtime>
dartlab agent update <runtime>
dartlab agent rollback <runtime>
dartlab ask "질문" --runtime <runtime>
dartlab mcp --profile agent
```

`doctor`는 install, version, protocol, auth, MCP를 각 행으로 보여준다. status가 불명확하면 실패 원인과 repair action을 제공한다.

legacy `dartlab setup`은 migration 기간 `dartlab agent doctor` 포인터를 출력하고 direct provider 설정을 더 만들지 않는다.

## 4. Runtime Center UI

`settings/providers`를 `settings/agents`로 교체한다. redirect는 한 release 동안 유지한다.

각 runtime card:

- display name, resolved version
- installed, auth, protocol, MCP 상태
- supported capability chips
- primary action 한 개
- detail diagnostics
- update availability와 rollback state

primary action state:

```text
notInstalled -> 설치 계획 보기
installed + authRequired -> 로그인
authenticated + mcpMissing -> DartLab 연결
ready -> 이 agent로 시작
incompatible -> 업데이트 또는 외부 모드로 사용
broken -> 진단 복사와 복구
```

API key input, base URL, static model list, OAuth polling은 제거한다.

## 5. Chat UI

chat surface는 runtime-neutral event만 소비한다.

- header: runtime과 native session 상태
- activity: tool, evidence, artifact, approval
- message: delta와 final
- unknown native event: collapsed diagnostic
- event gap: 재연결 또는 native resume 안내
- evidence: exact resolve action과 verification receipt
- runtime switch: Analysis Capsule handoff, transcript 복사 없음

모델 picker는 `RuntimeDescriptor.modelCatalog`가 `known`일 때만 나타난다. partial이면 CLI default와 알려진 option을 구분한다. unavailable이면 picker를 숨기고 `CLI 기본 모델`을 표시한다.

## 6. Contract generation

Python Pydantic contract가 public schema SSOT다.

- `src/dartlab/ai/runtime/contracts.py`: discriminated models.
- `src/dartlab/ai/runtime/schema.py`: deterministic JSON Schema export.
- `ui/packages/contracts/src/agentRuntime.generated.ts`: generated projection.
- `tests/audit/agentRuntimeContract.py --check`: source와 projection drift 차단.

`ui/packages/contracts/src/ai.ts`는 migration alias만 남기고 event union을 손으로 복제하지 않는다. `agentGateway.py`의 allowlist는 generated mapping으로 교체하고 `native` escape hatch를 보존한다.

## 7. Analysis Capsule API

| Method | Path | 목적 |
|---|---|---|
| POST | `/api/ai/capsules` | current session의 structured evidence state 저장 |
| GET | `/api/ai/capsules/{capsuleId}` | UI render, no transcript |
| POST | `/api/ai/sessions/{sessionId}/handoff` | target runtime new session에 capsule ref 연결 |

MCP resource `dartlab://analysis/{capsuleId}`는 동일 contract를 bounded text와 JSON으로 제공한다. capsule read가 성공해도 verified outcome은 아니다. capsule이 후속 분석의 grounded input으로 사용될 때 retained transition을 만든다.

## 8. API compatibility and deprecation

한 release deprecation window:

- `/api/ai/profile`, `/api/models/{provider}`, `/api/oauth/*`, `/api/codex/logout`, `/api/ollama/pull`은 deprecated response와 Runtime Center link 제공.
- legacy direct provider가 active일 때만 old request를 받고 warning event emit.
- 새 설치에는 legacy profile을 만들지 않는다.
- parity 뒤 endpoint, schema, secret store, UI를 함께 삭제한다.

OpenDART API key는 금융 데이터 credential이므로 model credential 제거와 별개다. `/api/openapi/dart-key`는 유지한다.
