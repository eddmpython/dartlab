# 03. Bootstrap, Install and Security

## 1. Discovery ladder

runtime list는 daemon 시작 시 모든 CLI를 띄우지 않는다. UI 또는 CLI가 상태를 요청할 때 lazy probe한다.

1. manifest의 binary candidate를 current-user PATH에서 resolve.
2. resolved file path, size, mtime, launcher args를 고정.
3. exact program의 version command 실행.
4. required protocol flag와 structured initialize를 probe.
5. runtime이 제공하면 model catalog와 account state 확인.
6. MCP 등록 상태를 공식 CLI command로 조회.
7. 결과를 `ProgramIdentity + probe question hash` key로 cache.

cache는 `~/.dartlab/runtime/probe.json`에 sibling temp write, flush, atomic replace한다. TTL은 사용하지 않는다. executable identity나 probe surface가 바뀌면 miss다.

상태 판정:

- binary 없음: `notInstalled`
- version만 확인, protocol 없음: `incompatible`
- protocol handshake 성공, auth 필요: `authRequired`
- protocol과 DartLab MCP 준비: `ready`
- required flag 또는 handshake 오류: `broken`

## 2. MCP profile

현재 `mcpAdvertisedToolNames()`는 `ask`와 canonical tools를 함께 노출한다. embedded agent가 `ask`를 호출하면 자신을 다시 시작할 수 있다.

제안:

```text
dartlab mcp --profile consumer
dartlab mcp --profile agent
dartlab mcp --profile public-readonly
```

| profile | 목적 | `ask` | RunPython | write artifact |
|---|---|---:|---:|---:|
| `consumer` | 기존 MCP client 호환 | yes | current policy | current policy |
| `agent` | installed agent가 DartLab capability 사용 | no | local guarded | explicit tool approval |
| `public-readonly` | remote connector projection | no | no | no |

`agent` profile의 server instructions는 provider별 prompt가 아니다. 다음 공통 흐름만 설명한다.

1. 모호한 domain은 `ReadSkill`.
2. 공개 API는 `ReadCapability`.
3. 단일 호출은 `EngineCall`.
4. 결합 계산만 `RunPython`.
5. 결과에 evidence와 limitation 보존.
6. `ask`를 다시 호출하지 않음.

tool set hash와 Skill OS version을 initialize metadata에 넣어 drift를 진단한다.

## 3. MCP bootstrap

설정 파일을 직접 수정하지 않는다. driver manifest가 공식 관리 명령의 argument template을 제공하고 subprocess array로 실행한다.

```text
codex mcp add dartlab -- <resolved dartlab> mcp --profile agent
claude mcp add dartlab -- <resolved dartlab> mcp --profile agent
cline mcp add --yes dartlab -- <resolved dartlab> mcp --profile agent
```

실제 지원 flag는 probe 결과로 확인한다. 명령 전후 `mcp list/get`을 비교하고 exact command와 args가 맞을 때만 connected다. 기존 이름에 다른 command가 있으면 덮어쓰지 않고 conflict를 표시한다.

## 4. Install flow

설치는 두 단계다.

### Plan

`RuntimeInstallPlan`은 실행 전에 다음을 UI와 CLI에 보여준다.

- runtime ID와 source
- 감지된 package channel
- exact executable and arguments
- 예상 변경 위치
- elevation 필요 여부
- target version policy
- verification command
- rollback 가능 여부와 exact rollback action

### Execute

1. 사용자의 explicit approval receipt 확인.
2. session active면 update를 defer.
3. argument array로 official installer 또는 package manager 실행.
4. executable identity를 새로 resolve.
5. version, handshake, empty session open/close smoke.
6. 성공 뒤 MCP bootstrap 제안.
7. 실패하면 last-known-good exact version으로 rollback.

silent install과 background auth는 금지한다.

## 5. Channel policy

- npm global: package manager가 보고한 package와 exact old version을 기록하고 version pin reinstall로 rollback.
- provider self-updater: documented rollback이 없으면 DartLab은 update를 실행하지 않고 official updater를 연다.
- native installer: signed artifact와 reversible installer가 확인된 경우만 automatic execute.
- unknown shim: install/update 불가, runtime 사용만 허용.

manifest에 임의 URL shell script를 넣지 않는다. install source allowlist와 checksum/signature 정책을 code에서 검증한다.

## 6. Authentication

DartLab auth button은 provider login process 또는 documented auth UI를 연다.

- stdout token parsing 금지.
- config와 credential file read 금지.
- browser callback intercept 금지.
- auth state는 provider protocol 또는 exit/status probe가 알려주는 범위만 표시.
- 판단 불가면 `authUnknown`, 성공으로 추정하지 않음.

## 7. Workspace and permissions

embedded session cwd는 기본 `~/.dartlab/runtime/workspaces/{sessionId}`다. DartLab repo나 사용자 프로젝트를 기본 cwd로 사용하지 않는다.

default profile:

- filesystem read는 capsule과 MCP가 제공한 artifact에 한정.
- arbitrary shell은 provider가 끌 수 있으면 disable.
- DartLab MCP write tool은 explicit approval.
- dangerous skip, unrestricted bypass flag 사용 금지.
- runtime이 safe embedded profile을 만들 수 없으면 external agent mode만 제공.

approval은 pending request ID, subject digest, offered choice, risk, expiry와 결박한다. UI는 provider decision string을 직접 보내지 않고 normalized option ID를 driver에 전달한다.

## 8. Secret and log policy

redaction 대상:

- access token, refresh token, API key
- authorization header와 cookie
- provider credential path
- prompt와 answer 본문을 포함한 native event field
- local absolute path

debug trace는 opt-in이어도 bounded event metadata와 hashes만 남긴다. transcript capture mode는 제품에 추가하지 않는다.
