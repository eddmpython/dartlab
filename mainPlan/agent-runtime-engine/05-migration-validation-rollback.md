# 05. Migration, Validation and Rollback

## 1. 구현 단계

### Phase A. Attempt proof

`tests/_attempts/agentRuntime/`에서 production source 변경 없이 다음을 실증한다.

- exact executable identity와 version.
- persistent two-turn session.
- native session resume.
- DartLab MCP `ReadSkill`과 `EngineCall` 실제 호출.
- partial text, tool, completion event.
- cancel settlement와 child cleanup.
- approval request와 reject.
- unknown event preservation.

Codex, Claude Code, Cline 세 runtime의 account-backed turn은 operator evidence다. credential 없는 CI는 deterministic fake CLI와 protocol captures로 같은 contract를 검증한다.

Exit: 세 runtime 중 최소 둘이 embedded full slice, 나머지 하나가 실패하면 exact incompatible reason을 낸다. Cline은 ACP generic path로만 통과해야 한다.

### Phase B. Foundation

- runtime contracts와 schema generator.
- closed manifest loader와 driver registry.
- discovery와 probe cache.
- process supervisor와 event buffer.
- fake CLI fixture와 cross-platform cleanup test.

Exit: provider isolation, queue bound, unknown event, program identity tests green.

### Phase C. Drivers

- Codex app-server.
- Claude stream-json.
- generic ACP.
- native session mapping과 approval binding.

Exit: deterministic two-turn, resume, cancel, approval, oversize event tests green.

### Phase D. DartLab capability bootstrap

- MCP profile contract.
- official config command adapters.
- conflict-safe connect/disconnect.
- Analysis Capsule MCP resource.

Exit: embedded agent가 `ask` 재귀 없이 canonical engine evidence를 만든다.

### Phase E. Server and compatibility

- runtime and session endpoints.
- `/api/ask` runtime facade.
- productOutcome lifecycle events.
- old provider APIs deprecated.

Exit: existing CLI ask와 UI stream consumer behavior parity.

### Phase F. UI

- Runtime Center.
- new session event consumer.
- approval and evidence verification.
- runtime switch and capsule handoff.

Exit: browser behavior test와 운영자 눈검수. UI 변경은 push 명시 승인 전 원격 반영 금지.

### Phase G. Cutover and deletion

- default를 runtime engine으로 전환.
- one release legacy rollback window.
- usage와 operator parity 확인.
- providers, OAuth/API key settings, static model resolver, simulated stream 삭제.
- stale Skill OS와 mainPlan relation 갱신.

Exit: no-direct-model-access audit green, legacy import 0, verified analysis loop green.

## 영향 파일

### 신규 runtime source

- `src/dartlab/ai/runtime/contracts.py`
- `src/dartlab/ai/runtime/schema.py`
- `src/dartlab/ai/runtime/registry.py`
- `src/dartlab/ai/runtime/discovery.py`
- `src/dartlab/ai/runtime/probeCache.py`
- `src/dartlab/ai/runtime/processSupervisor.py`
- `src/dartlab/ai/runtime/eventBuffer.py`
- `src/dartlab/ai/runtime/eventProjection.py`
- `src/dartlab/ai/runtime/sessionManager.py`
- `src/dartlab/ai/runtime/sessionStore.py`
- `src/dartlab/ai/runtime/mcpBootstrap.py`
- `src/dartlab/ai/runtime/installManager.py`
- `src/dartlab/ai/runtime/updateManager.py`
- `src/dartlab/ai/runtime/analysisCapsule.py`
- `src/dartlab/ai/runtime/drivers/base.py`
- `src/dartlab/ai/runtime/drivers/codexAppServer.py`
- `src/dartlab/ai/runtime/drivers/claudeStreamJson.py`
- `src/dartlab/ai/runtime/drivers/acp.py`
- `src/dartlab/server/api/agentRuntime.py`
- `src/dartlab/cli/commands/agent.py`
- `ui/packages/contracts/src/agentRuntime.generated.ts`
- `ui/apps/local/src/lib/agentRuntime/RuntimeCenter.svelte`
- `ui/apps/local/src/routes/settings/agents/+page.svelte`

### 변경

- `src/dartlab/ai/agent.py`: compatibility provider loop에서 runtime session bridge로 축소.
- `src/dartlab/ai/kernel.py`: `_resolveProvider`를 runtime selection으로 교체.
- `src/dartlab/server/agentGateway.py`: provider 분기와 수기 allowlist 제거.
- `src/dartlab/server/api/ask.py`: Agent Session facade.
- `src/dartlab/server/api/ai.py`: data credential만 남기고 model provider API deprecate 후 제거.
- `src/dartlab/server/security.py`: local runtime mutating endpoint 정책.
- `src/dartlab/server/__init__.py`: agent runtime router 등록.
- `src/dartlab/mcp/protocol.py`: `McpProfile`별 tools와 instructions.
- `src/dartlab/cli/commands/mcp.py`: `--profile`과 official config output.
- `src/dartlab/cli/commands/setup.py`: agent doctor 포인터.
- `src/dartlab/cli/commands/status.py`: runtime status로 교체.
- `src/dartlab/cli/parser.py`: agent command 등록.
- `ui/apps/local/src/lib/chat/chatStore.svelte.ts`: native session metadata와 cursor.
- `ui/apps/local/src/lib/chat/Composer.svelte`: ready capability와 cancel.
- `ui/apps/local/src/lib/chat/Evidence.svelte`: exact resolve receipt.
- `ui/packages/runtime/src/adapters/local/sources/aiSource.ts`: session API.
- `ui/packages/runtime/src/adapters/local/api/stream.ts`: generated event envelope.
- `ui/packages/contracts/src/ai.ts`: compatibility aliases.
- `pyproject.toml`, `uv.lock`: direct model SDK 제거는 final deletion commit에서만.

### 삭제

- `src/dartlab/ai/providers/`
- `src/dartlab/core/providers/registry.py`의 model provider catalog 부분
- `src/dartlab/ai/settings/modelResolver.py`
- `src/dartlab/ai/settings/providerCatalog.py`
- `ui/apps/local/src/lib/chat/ProviderSettings.svelte`
- `ui/apps/local/src/routes/settings/providers/+page.svelte` redirect window 종료 후
- model OAuth callback과 secret profile code
- direct OpenAI-compatible provider dependency

OpenDART, EDGAR 등 데이터 provider는 삭제 대상이 아니다.

## 영향 함수와 심볼

- `RuntimeDescriptor`, `RuntimeCapabilities`, `ProgramIdentity`, `RuntimeProbe`.
- `SessionOpenRequest`, `NativeSessionRef`, `TurnRequest`, `RuntimeEvent`.
- `ApprovalRequest`, `ApprovalResponse`, `RuntimeInstallPlan`.
- `AgentRuntimeDriver`, `AgentSession`.
- `discoverRuntimes()`, `probeRuntime()`, `resolveProgram()`.
- `openAgentSession()`, `resumeAgentSession()`, `closeAgentSession()`.
- `projectRuntimeEvent()`, `appendRuntimeEvent()`, `replayRuntimeEvents()`.
- `buildMcpConnectPlan()`, `connectDartlabMcp()`, `disconnectDartlabMcp()`.
- `buildInstallPlan()`, `executeInstallPlan()`, `rollbackRuntime()`.
- `createAnalysisCapsule()`, `readAnalysisCapsule()`, `handoffAnalysisCapsule()`.
- `mcpAdvertisedToolNames(profile)`, `advertisedTools(profile)`.
- `streamAgentRun()`은 provider object가 아니라 session service를 받는다.
- `ask()` public signature는 migration 동안 유지하고 `runtime` keyword를 추가한다. `provider`, `apiKey`, `baseUrl`, `model`은 deprecation 후 제거한다.

## 테스트

### Python contract and process

- `tests/ai/runtime/testContracts.py`
- `tests/ai/runtime/testManifest.py`
- `tests/ai/runtime/testDiscovery.py`
- `tests/ai/runtime/testProbeCache.py`
- `tests/ai/runtime/testProcessSupervisor.py`
- `tests/ai/runtime/testEventBuffer.py`
- `tests/ai/runtime/testSessionManager.py`
- `tests/ai/runtime/testMcpBootstrap.py`
- `tests/ai/runtime/testAnalysisCapsule.py`
- `tests/ai/runtime/testInstallManager.py`

### Driver fixtures

- `tests/ai/runtime/fixtures/fakeCodexAppServer.py`
- `tests/ai/runtime/fixtures/fakeClaudeStreamJson.py`
- `tests/ai/runtime/fixtures/fakeAcpAgent.py`
- two-turn, resume, cancel, approval, malformed frame, oversize, stderr flood, exit race.

### Architecture audits

- `tests/audit/agentRuntimeIsolation.py`: core와 UI provider ID branch 0.
- `tests/audit/noDirectModelAccess.py`: production direct model network, OAuth, API key input 0.
- `tests/audit/agentRuntimeContract.py`: Python schema와 generated TS drift 0.
- `tests/audit/agentMcpProfile.py`: agent profile에 `ask` 0, canonical tool identity drift 0.
- `tests/audit/runtimeModelHonesty.py`: probe한 model ID가 source에 hardcode되지 않음.
- `tests/audit/runtimeProcessLeak.py`: test 뒤 child process 0.

### Server and UI

- `tests/server/testAgentRuntimeApi.py`: Origin, CSRF, local-only mutation, status codes.
- `tests/server/testAskRuntimeCompatibility.py`: old ask stream behavior.
- `ui/apps/local/src/lib/agentRuntime/runtimeState.test.ts`: card state machine.
- local Playwright behavior: not installed, login required, MCP conflict, ready, cancel, evidence resolve, runtime switch.

### Operator lane

`tests/ai/runtime/operatorSmoke.py --runtime codex|claude|cline`:

1. account-backed two-turn.
2. DartLab MCP engine call.
3. native resume.
4. cancel.
5. approval reject.
6. process cleanup.

operator evidence는 credential 없는 CI pass로 둔갑시키지 않는다.

## 롤백

- Phase B~D는 기존 provider path를 건드리지 않는 additive commits다.
- Phase E에서 `/api/ask` routing selector는 persisted user profile이 아니라 explicit local config `aiRuntimeMode=legacy|runtime`로 한 release만 제공한다.
- runtime session store는 native session pointer만 가지므로 rollback에 transcript migration이 없다.
- UI cutover commit은 Provider Settings 삭제 commit과 분리한다. UI 문제가 있으면 route와 adapter만 legacy로 되돌린다.
- provider deletion은 operator parity와 no-direct-access gate가 green인 뒤 마지막 commit으로 수행한다.
- dependency 제거는 source deletion과 wheel smoke가 같은 commit에서 통과할 때만 한다.
- installer update 실패는 exact last-known-good version rollback을 수행한다. rollback 불가능한 channel은 애초에 자동 update하지 않는다.
- 어떤 rollback도 provider-owned credential이나 native transcript를 삭제하지 않는다.

## 평가

### 전문 개발자 렌즈

- 강점: protocol 차이가 drivers에 갇히고 source와 UI가 generated contract를 공유한다. generic ACP로 Cline 전용 분기를 피한다.
- 발견한 위험: 별도 runtime마다 auth와 model을 추측하면 provider hardcoding이 재발한다. capability probe와 honest partial/unknown state를 계약에 반영했다.
- 발견한 위험: subprocess 종료가 부모 process만 죽이고 child를 남길 수 있다. Windows Job Object와 POSIX process group을 foundation gate로 올렸다.
- 발견한 위험: unknown event allowlist가 provider drift를 data loss로 만든다. bounded `native` event와 explicit gap을 넣었다.
- 발견한 위험: MCP에 `ask`가 남으면 recursive agent loop가 생긴다. agent profile에서 제거하고 audit로 잠근다.
- 발견한 위험: runtime UI가 Python contract를 다시 손으로 적을 수 있다. generated TypeScript와 drift gate를 설계했다.

### 전문 PM 렌즈

- 강점: 사용자가 이미 구매하고 로그인한 agent를 활용하며 DartLab은 근거와 금융 도구에 집중한다. provider setup friction을 제품 가치 이전에 제거한다.
- 발견한 위험: CLI 설치 성공을 제품 성공으로 착각할 수 있다. 북극성 completion을 MCP engine call과 evidence resolve까지로 고정했다.
- 발견한 위험: 모든 CLI를 embedded 지원한다고 약속하면 text-only 또는 unsafe runtime이 경험을 망친다. capability-based eligibility와 external-only state를 추가했다.
- 발견한 위험: runtime 선택 자동화가 vendor ranking으로 변질될 수 있다. last verified runtime과 required capability만 사용하고 여러 후보면 사용자가 선택한다.
- 결론: 방향은 높은 ROI다. 단 Phase A account-backed proof와 North Star Phase 0 없이 UI부터 교체하면 안 된다.
