# 01. Current State Audit

## 1. 코드 기준선

2026-08-02 실측 기준 `src/dartlab/ai`는 tracked Python 파일 126개, 약 19,805줄이다. 그중 tools 약 8,439줄, providers 약 3,715줄, workbench 약 2,610줄, memory 약 1,973줄이다. AI 경계가 한 agent loop보다 provider와 orchestration 부속 계층에 크게 퍼져 있다.

### Hardcoded provider plane

- `src/dartlab/core/providers/registry.py`: OAuth, API key, CLI, none auth와 9개 provider spec.
- `src/dartlab/ai/providers/__init__.py`: env key, base URL, API key, factory, direct OpenAI-compatible client, simulated stream.
- `src/dartlab/ai/settings/modelResolver.py`: static latest model fallback.
- `src/dartlab/ai/settings/providerCatalog.py`: provider role과 wired provider 목록.
- `src/dartlab/server/api/ai.py`: profile, secret, provider validate, model list, OAuth, Ollama pull.
- `src/dartlab/cli/commands/setup.py`: API key, OAuth Codex, Ollama, custom provider setup.
- `src/dartlab/cli/commands/status.py`: provider별 상태와 비용.
- `ui/apps/local/src/lib/chat/ProviderSettings.svelte`: API key 저장과 OAuth polling.

### Codex가 agent로 쓰이지 않는 지점

- `src/dartlab/ai/providers/support/codexCli.py`: `~/.codex/config.toml`, default model list, keyword sandbox 선택, `codex exec - --json`.
- `src/dartlab/ai/providers/codex.py`: 전체 message를 prompt 하나로 만들고 one-shot 실행, 최종 text simulated stream.

이 경로는 native thread, turn, approval, MCP, model discovery를 사용하지 않는다.

### 중복 public event authority

- `src/dartlab/server/agentGateway.py`: provider/workbench 분기와 public event allowlist.
- `ui/packages/contracts/src/ai.ts`: TypeScript event union.
- `ui/packages/runtime/src/adapters/local/api/stream.ts`: 실제 SSE parser.

Python과 TypeScript가 둘 다 정본을 자처하며 unknown event를 제품적으로 보존하는 계약이 없다.

### 재사용할 자산

- `src/dartlab/ai/contracts.py`: `Ref`, `TraceEvent`, verification contract.
- `src/dartlab/ai/tools/registry.py`: canonical DartLab tool schema.
- `src/dartlab/mcp/protocol.py`: Skill OS, EngineCall, RunPython, artifact의 실제 MCP 표면.
- `src/dartlab/server/streaming.py`: 사용자 activity와 raw evidence 분리 원칙.
- `src/dartlab/ai/tools/saveArtifact.py`: artifact receipt 기반.
- `ui/apps/local/src/lib/chat/Evidence.svelte`, `ToolCard.svelte`: evidence와 tool result 표현.

## 2. 로컬 CLI 실측

| Runtime | 설치 버전 | embedded protocol | session | MCP |
|---|---:|---|---|---|
| Codex CLI | 0.146.0 | `app-server` stdio JSON-RPC | thread start, resume, turn, interrupt | `codex mcp` |
| Claude Code | 2.1.220 | bidirectional stream-json | session ID, resume | `claude mcp` |
| Cline | 3.0.49 | ACP stdio | ACP session | `cline mcp` |

현재 Claude Code에는 DartLab MCP가 연결돼 있다. Codex에는 등록돼 있지 않다. 이는 runtime 상태가 단순 installed boolean이 아니라 install, auth, protocol, MCP connection으로 나뉘어야 한다는 실증이다.

버전과 capability는 계획 문서에 고정하지 않는다. implementation은 실행 시 resolved binary의 version, help, structured initialize response를 다시 probe한다.

## 3. runtrol에서 흡수할 원칙

| 원칙 | DartLab 구현 |
|---|---|
| CLI가 auth와 transcript 소유 | credential/token/history를 DartLab store에 복제하지 않음 |
| manifest는 CLI 도달 방법만 선언 | binary candidates, protocol kind, install channel만 |
| capability와 model runtime discovery | probe result가 `RuntimeCapabilities`와 `ModelCatalog` 제공 |
| provider-neutral session boundary | `AgentRuntimeDriver`, `AgentSession` Protocol |
| send와 completion 분리 | `sendTurn()`은 handoff 후 반환, 완료는 event |
| unknown notification 보존 | public `native` event에 bounded payload 유지 |
| bounded queues와 replay | session budget, cursor, explicit gap |
| provider name branch core 금지 | driver kind registry 한 곳에서만 construction |
| native session resume | provider storage path를 읽지 않고 native ID 사용 |

흡수하지 않는 것:

- Rust crate
- runtrol daemon과 store
- PWA transport
- runtrol release/update schedule
- provider manifest 파일의 직접 복사

## 4. 기존 mainPlan과 충돌

### `first-party-ai`

기존 계획은 local `advanced` provider와 Cloudflare Workers AI edge를 전제로 한다. 사용자 PC의 agent CLI를 공식 경로로 삼는 결정과 충돌한다.

정리:

- deterministic과 on-device evidence composition은 유지 후보.
- local advanced는 Agent Runtime으로 대체.
- direct edge model은 구현 전 ROI와 정책 재검. 공식 Agent Runtime path에는 포함하지 않음.
- `runtime.ai` port가 남더라도 model tier가 아니라 `deterministic`, `onDevice`, `agentRuntime` capability를 보고 선택.

### `ai-workbench-connector`

remote public connector와 local MCP는 deployment와 권한이 다르다. 다만 Evidence Pack schema와 tool identity를 두 번 만들면 안 된다.

정리:

- canonical domain response는 `src/dartlab` 정본.
- local agent profile은 full local analysis tools.
- remote connector는 read-only public subset.
- tool name과 evidence envelope는 generated projection으로 공유.

## 5. Skill OS drift

- `operation.aiProductReplatform`은 LibreChat, fixed `DartLabResearchGraph`, backup directory를 공식 경계로 기록한다.
- `operation.ui`도 graph를 제품 path로 고정한다.
- `operation.aiEngine`은 provider 9종과 model-oriented contract를 정본으로 둔다.

구현 시작 전 이 셋을 current `agent.py` 본체 규칙과 Agent Runtime 목표에 맞춰 교체해야 한다. 옛 문서를 주석으로 남기지 않고 잘못된 계약은 삭제하거나 새 정본 포인터로 축약한다.
