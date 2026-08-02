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
