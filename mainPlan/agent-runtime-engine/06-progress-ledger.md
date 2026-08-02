# 06. Progress Ledger

## 2026-08-02 설계 수립

상태: 상세 설계 완료, production 구현 0.

### 검증한 기준선

- `src/dartlab/ai` tracked Python 126개, 약 19,805줄.
- model provider와 auth가 core, server, CLI, UI에 분산.
- Codex adapter는 one-shot `codex exec`와 simulated stream.
- 현재 설치: Codex CLI 0.146.0, Claude Code 2.1.220, Cline 3.0.49.
- Codex app-server, Claude stream-json, Cline ACP의 structured surface 확인.
- Claude Code는 DartLab MCP 연결됨. Codex는 미연결.
- runtrol은 별도 레포이며 DartLab runtime dependency로 사용하지 않음.

### 결정

1. public abstraction은 `LLMProvider`가 아니라 `AgentRuntime`.
2. runtrol은 설계 참고만 하고 코드, daemon, package dependency 없음.
3. auth, model, transcript, native session은 CLI 소유.
4. DartLab은 Skill OS, MCP, engine, evidence, capsule 소유.
5. embedded는 structured duplex와 safe permission이 확인된 runtime만.
6. Cline은 generic ACP driver로 연결.
7. MCP agent profile에서 `ask` 제외.
8. unknown event 보존.
9. UI contract는 Python schema generated projection.
10. direct provider는 parity 뒤 삭제.

### Open decisions가 아닌 implementation facts

- exact current CLI flags는 Phase A probe가 다시 기록한다.
- auto update는 rollback 가능한 channel만.
- remote global North Star aggregation은 본 계획 범위 밖.
- public browser surface는 local CLI를 직접 제어하지 않는다.

### NEXT

1. `dartlab-north-star` Phase 0 contract와 failing evidence gate.
2. `tests/_attempts/agentRuntime/` three-runtime proof.
3. runtime contract와 process supervisor foundation.
4. Codex, Claude, generic ACP driver 순서로 졸업.

### Exit decision

아직 없음. 첫 runtime의 verified analysis vertical slice 뒤 기록한다.

## 2026-08-02 production vertical slice

상태: Agent Runtime production 경로 구현 완료. root 북극성 점수 재판정은 주간 outcome review까지 보류.

### 구현된 정본

- `src/dartlab/ai/runtime/manifests/*.toml`: Codex, Claude, Cline의 실행·설치 계약.
- `AgentRuntimeEngine`: runtime 선택, 세션 재개, turn stream, cancel, approval, replay.
- `ProcessSupervisor`: shell 없는 argv 실행, Windows Job/POSIX process group 정리, frame·stderr·timeout 상한.
- native driver 3종: Codex app-server JSON-RPC, Claude stream-json, ACP v1.
- `analysisCapsule`: Skill OS 탐색, EngineCall/RunPython, ref, untrusted content 지침.
- MCP bootstrap: Cline ACP embedded MCP, Codex·Claude 공식 CLI 연결 계획과 digest 승인.
- Runtime Center API·CLI·Svelte UI: probe, install plan/apply, MCP plan/apply, runtime 선택, session, model, approval.
- `/api/ask`, Agent Gateway, `dartlab.ask` 기본과 분석 모드를 모두 runtime 경로로 전환.
- provider validate/secret/OAuth/Ollama pull 제품 API는 410 migration 경계로 전환.
- MCP tools/list에서 recursive `ask` 제거.
- Python Pydantic runtime schema에서 UI TypeScript 계약 생성.

### 실증

- throwaway attempts 9건 통과 후 `tests/ai/runtime`, `tests/productOutcome`로 승격.
- Codex 0.146.0: initialize, thread/start, model/list 실제 handshake 통과.
- Cline 3.0.49: ACP initialize, session/new, embedded DartLab MCP 실제 handshake 통과.
- Claude Code 2.1.220: 실제 public `dartlab ask --runtime claude` 턴에서 `ReadSkill`과 `EngineCall(Company.panel)`을 호출해 `table:005930:IS:2026Q1`, `value:005930:IS:2026Q1:sales` 근거 답변까지 완주했다. read-only MCP allowlist와 `dontAsk` permission mode가 이 실행에서 동작했다.
- Runtime Center status 실측에서 Claude·Cline MCP 연결, Codex 미연결 상태를 구분해 반환했다. Codex 연결은 digest 승인 UI/CLI로만 수행한다.
- UI `svelte-check`: 오류 0. production build 성공.
- runtime, outcome, gateway, CLI, security, MCP, Skill OS 핵심 계약 126건 통과, 1건 기존 skip.
- 저장소 quality gate, changed camelCase/docstring, folder-size, init-thin, agent-boundary, public API audit 통과.
- 전체 preflight에서 이번 변경의 format·quality 실패는 수정했다. 남은 차단은 기존 `.tmp` 장기 잔재와 AI 범위 밖 search/story/quant 데이터 unit 실패이며 본 작업에서 기존 임시 자료를 임의 삭제하거나 기준선을 완화하지 않았다.

### 제품 경계 결정

- runtrol 코드·daemon·패키지를 가져오지 않았다. process supervision, discovery, native session, opaque event 원칙만 DartLab 구현으로 흡수했다.
- 옛 provider/workbench 모듈은 기존 내부 회귀용 compatibility island로 남아 있지만 public ask, server, CLI, UI에서 도달하지 않는다. 새 기능과 설정은 이 경로에 추가하지 않는다.
- direct provider dependency의 물리 삭제는 compatibility test 폐기와 함께 별도 정리 commit으로만 수행한다. production engine 완료 조건에는 포함하지 않고 공개 도달성 0을 gate로 삼는다.

### Exit decision

Agent Runtime vertical slice는 production 진입 가능. 실제 CLI의 grounded delivery까지 실증했다. root score 상향과 initiative 완료 이동은 실제 사용자가 UI에서 exact evidence를 연 verified operator journey 뒤에만 한다.
