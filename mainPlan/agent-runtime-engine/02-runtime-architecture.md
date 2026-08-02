# 02. Runtime Architecture

## 1. Package boundary

```text
src/dartlab/ai/runtime/
  __init__.py
  contracts.py
  registry.py
  discovery.py
  probeCache.py
  processSupervisor.py
  sessionManager.py
  sessionStore.py
  eventBuffer.py
  eventProjection.py
  mcpBootstrap.py
  installManager.py
  updateManager.py
  analysisCapsule.py
  drivers/
    __init__.py
    base.py
    codexAppServer.py
    claudeStreamJson.py
    acp.py
  manifests/
    codex.toml
    claude.toml
    cline.toml
```

`runtime`은 AI가 provider API를 호출하는 계층이 아니다. 설치된 프로그램을 발견하고 structured session을 운반하는 local process boundary다.

## 2. Contracts

### `RuntimeDescriptor`

```text
runtimeId
displayName
protocolKind
state
programIdentity
version
capabilities
modelCatalog
authState
mcpState
diagnostics
```

`state`는 `notInstalled`, `installed`, `authRequired`, `ready`, `incompatible`, `broken`, `busy`다. `unknown`은 실제로 판정할 수 없는 auth/model substate에만 쓰고 runtime 전체 성공 상태로 사용하지 않는다.

### `RuntimeCapabilities`

```text
duplexStream
sessionResume
sessionList
modelCatalog
approvals
turnCancel
mcpConfig
attachments
reasoningEvents
structuredToolEvents
```

capability는 runtime ID로 추론하지 않는다. probe가 실제 표면을 관찰해 채운다.

### `ProgramIdentity`

```text
resolvedPath
launcherArgs
size
modifiedNs
versionText
```

probe한 exact program을 driver에 넘긴다. session open에서 PATH를 다시 resolve하지 않는다.

### `AgentRuntimeDriver`

```python
class AgentRuntimeDriver(Protocol):
    def probe(self, program: ProgramIdentity) -> RuntimeProbe: ...
    def openSession(self, request: SessionOpenRequest) -> AgentSession: ...
```

### `AgentSession`

```python
class AgentSession(Protocol):
    def sendTurn(self, request: TurnRequest) -> None: ...
    def nextEvent(self) -> RuntimeEvent | None: ...
    def answerApproval(self, response: ApprovalResponse) -> None: ...
    def cancelTurn(self) -> None: ...
    def close(self) -> None: ...
```

`sendTurn()`은 stdin 또는 protocol request 전달이 끝나면 반환한다. turn 완료는 `nextEvent()`의 `turnCompleted`로만 판정한다.

## 3. Driver construction

`registry.py` 한 곳에 protocol kind와 constructor를 연결한다.

```text
codex-app-server -> CodexAppServerDriver
claude-stream-json -> ClaudeStreamJsonDriver
acp -> AcpDriver
```

core, server, UI는 runtime ID나 provider 이름으로 driver를 고르지 않는다. Cline은 별도 core driver가 아니라 `protocolKind=acp` manifest다. 새 ACP CLI는 manifest 추가와 protocol compatibility proof만으로 들어온다.

manifest 허용 필드:

- stable runtime ID와 label
- binary candidate 이름
- protocol kind
- version command
- protocol bootstrap argv
- official install metadata와 channel detector
- stable model alias가 protocol상 불가피할 때만 alias

manifest 금지 필드:

- model ID 목록
- capability boolean
- account state
- auth token path
- transcript path
- UI feature flag
- prompt template

closed schema로 unknown key를 거부한다.

## 4. Drivers

### Codex app-server

1. exact binary로 app-server stdio 시작.
2. `initialize`와 `initialized` handshake.
3. `model/list`를 요청 시마다 runtime catalog로 취급.
4. `thread/start` 또는 `thread/resume`.
5. `turn/start`, notifications, `turn/completed`.
6. cancel은 `turn/interrupt`.
7. approval request는 native payload를 driver 내부에서 `ApprovalRequest`로 변환.
8. 모르는 notification은 `native` event.

### Claude stream-json

1. version/help probe로 consumed flags 확인.
2. stream-json input/output process 시작.
3. explicit session ID 또는 resume surface 사용.
4. partial message, tool use, control request, result, end turn을 normalized event로 변환.
5. provider permission framing은 driver 밖으로 노출하지 않고 digest-bound approval로 변환.
6. unknown frame은 `native` event.

### Generic ACP

1. initialize와 protocol version negotiation.
2. session new/load.
3. prompt, session update, completion.
4. capability와 auth method는 ACP response에서 취득.
5. Cline 전용 분기는 만들지 않는다.

## 5. Process supervisor

공통 정책:

- discovery one-shot deadline 15초.
- stdout와 stderr 각각 최대 256 KiB capture.
- event frame 최대 1 MiB.
- session replay ring 최대 256 events 또는 4 MiB.
- oversize는 silent drop하지 않고 `eventGap` 또는 `eventTruncated`를 emit.
- 한 session에 active turn 1개.
- 기본 hot runtime 4개.
- shutdown은 stdin close, protocol close, bounded graceful wait, process tree termination 순서.

Windows는 `ctypes` 기반 Job Object를 만들고 `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`로 child tree를 묶는다. POSIX는 new session process group과 `killpg`를 사용한다. shell string을 실행하지 않고 argument array만 사용한다.

## 6. Event boundary

public event kind는 다음 closed semantic subset과 open native escape hatch로 구성한다.

```text
sessionStarted
sessionResumed
turnStarted
messageDelta
reasoningDelta
toolStarted
toolCompleted
approvalRequested
artifactProduced
turnCompleted
runtimeError
eventGap
native
```

모든 event는 다음 envelope를 가진다.

```text
schemaVersion
sessionId
turnId
eventId
sequence
runtimeId
kind
timestamp
payload
nativeType
```

`native` payload는 credential key redaction과 size bound만 적용하고 의미를 재작성하지 않는다. UI가 모르면 generic diagnostic로 표시하거나 숨길 수 있지만 transport가 버리면 안 된다.

## 7. Session ownership

provider CLI가 소유:

- authentication
- model setting
- durable transcript
- native session storage
- provider permission policy
- provider update channel

DartLab이 저장:

- DartLab session ID
- runtime ID와 native session ID pointer
- workspace ID
- last event cursor
- Analysis Capsule ID
- evidence와 artifact pointer
- approval receipt digest

DartLab은 provider transcript 파일을 찾거나 복사하지 않는다. UI 재시작 시 history capability가 있는 runtime은 native history를 다시 읽고, 없는 runtime은 이전 transcript가 없다고 명시한다.

## 8. Analysis Capsule

Analysis Capsule은 대화 요약이 아니라 DartLab 분석 상태다.

```text
capsuleId
subjectRefs
questionIntent
skillIds
capabilityCalls
evidenceRefs
artifactRefs
asOf
limitations
verificationReceipts
```

prompt, provider message, hidden reasoning은 저장하지 않는다. 다른 runtime으로 handoff할 때 agent는 MCP resource `dartlab://analysis/{capsuleId}`를 읽는다. 이 구조가 transcript 복사 없이 runtime 교체와 retained outcome을 가능하게 한다.
