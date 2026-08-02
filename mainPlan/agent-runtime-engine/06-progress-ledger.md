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
- MCP bootstrap: Codex·Claude·Cline 공식 CLI 연결 계획과 digest 승인. Cline ACP 3.0.49가 session/new의 embedded MCP를 무시하는 실제 동작은 전역 공식 설정 경로로 격리했다.
- Runtime Center API·CLI·Svelte UI: probe, install plan/apply, MCP plan/apply, runtime 선택, session, model, approval.
- `/api/ask`, Agent Gateway, `dartlab.ask` 기본과 분석 모드를 모두 runtime 경로로 전환.
- provider validate/secret/OAuth/Ollama pull 제품 API는 410 migration 경계로 전환.
- MCP tools/list에서 recursive `ask` 제거.
- Python Pydantic runtime schema에서 UI TypeScript 계약 생성.

### 실증

- throwaway attempts 9건 통과 후 `tests/ai/runtime`, `tests/productOutcome`로 승격.
- Codex 0.146.0: initialize, thread/start, model/list 실제 handshake 통과.
- Cline 3.0.49: ACP initialize와 session/new는 통과했지만 session/new의 embedded MCP가 실제 도구 목록에 반영되지 않았고 provider/model CLI 플래그도 ACP에서 무시됐다. 일반 headless Cline 응답은 통과했으나 DartLab 근거 경로는 미연결로 판정하고 실행을 차단한다.
- Claude Code 2.1.220: 실제 public `dartlab ask --runtime claude` 턴에서 `ToolSearch`, `ReadSkill`, `EngineCall(Company.panel)`만 호출해 `table:005930:IS:2026Q1`, `value:005930:IS:2026Q1:sales`, `date:005930:IS:2026Q1` 근거 답변까지 완주했다. Bash, PowerShell, 파일 수정, 외부 웹 호출은 0회였다.
- Runtime Center status 실측에서 Claude만 `groundedReady=true`, Cline·Codex는 설치됐어도 MCP 미연결인 `groundedReady=false`로 반환했다. 두 미연결 runtime의 public ask는 모델 호출 전에 실패하고 exact digest 연결 계획을 안내한다.
- Cline과 Codex의 환경별 exact argv·digest 연결 계획이 생성됐으며 아직 사용자의 동일 digest 적용 승인을 받지 않아 실행하지 않았다.
- 보안·준비 상태 회귀 24건, UI `svelte-check`, production build가 통과했다. 기존 접근성·chunk size 경고는 남지만 새 Runtime Center 오류는 없다.
- UI `svelte-check`: 오류 0. production build 성공.
- runtime, outcome, gateway, CLI, security, MCP, Skill OS 핵심 계약 126건 통과, 1건 기존 skip.
- 저장소 quality gate, changed camelCase/docstring, folder-size, init-thin, agent-boundary, public API audit 통과.
- 전체 preflight에서 이번 변경의 format·quality 실패는 수정했다. 남은 차단은 기존 `.tmp` 장기 잔재와 AI 범위 밖 search/story/quant 데이터 unit 실패이며 본 작업에서 기존 임시 자료를 임의 삭제하거나 기준선을 완화하지 않았다.

### 제품 경계 결정

- runtrol 코드·daemon·패키지를 가져오지 않았다. process supervision, discovery, native session, opaque event 원칙만 DartLab 구현으로 흡수했다.
- 옛 provider/workbench 모듈은 기존 내부 회귀용 compatibility island로 남아 있지만 public ask, server, CLI, UI에서 도달하지 않는다. 새 기능과 설정은 이 경로에 추가하지 않는다.
- direct provider dependency의 물리 삭제는 compatibility test 폐기와 함께 별도 정리 commit으로만 수행한다. production engine 완료 조건에는 포함하지 않고 공개 도달성 0을 gate로 삼는다.

### Exit decision

Agent Runtime vertical slice와 Claude grounded delivery는 production 진입 가능하다. Cline·Codex는 공식 MCP 연결 후 같은 operator journey를 통과하기 전까지 fail-closed 상태다. root score 상향과 initiative 완료 이동은 실제 사용자가 UI에서 exact evidence를 연 verified operator journey 뒤에만 한다.

## 2026-08-02 답변 품질과 GUI 종단간 강화

상태: Claude와 Codex는 실제 grounded ask를 완주했고, local GUI 경로에서 exact evidence 확인과 `verified` 전이를 실증했다. Cline은 upstream ACP가 session MCP를 노출하지 않는 사실을 재확인해 embedded 실행을 계속 fail-closed로 둔다.

### 추가 구현

- runtime 턴 컨텍스트는 `stockCode`, `period`, `reportMode`, `include`, `exclude`, `dashboardSnapshot`만 16 KiB 이하로 전달한다. transcript는 DartLab이 재주입하거나 브라우저에 저장하지 않고 CLI native session이 소유한다.
- 공개 답변은 native turn 성공, DartLab grounding tool 성공, 본문에 인용된 표 또는 문서, 값, 기준일 exact ref가 모두 있을 때만 커밋한다. 실패한 턴의 부분 답변은 공개하지 않는다.
- Windows npm shim의 한글 인자 손상을 피하도록 manifest가 native 실행 진입점을 선언한다. Claude는 native executable, Codex와 Cline은 Node 진입점을 shell 없이 실행한다.
- Codex instruction은 thread start 또는 resume의 `developerInstructions`로 전달하고 turn은 read-only sandbox와 approval never를 고정한다. interrupt는 request ID가 있는 JSON-RPC 요청이다.
- Cline은 auto approve를 끄고, ACP가 embedded MCP를 실제 제공하지 않는 현 버전은 global 설정 존재만으로 `groundedReady`가 되지 않는다.
- local chat은 DOMPurify allowlist, content-free session metadata, raw thinking 및 tool payload 비노출, 실제 cancel과 session delete, 모바일 sidebar overlay를 적용했다.
- 근거 확인은 active runtime의 bounded evidence journal에서 exact detail을 먼저 resolve한 뒤 product outcome receipt를 `verified`로 전이한다.
- `/ask`는 placeholder를 제거하고 실제 `/chat`으로 연결한다. `dartlab ai --dev`는 Windows에서 `npm.cmd`를 선택한다.

### 실증 결과

- Claude 실제 ask: 삼성전자 2026Q1 매출액 133,873,444,000,000원, table, value, date ref 인용, exit 0.
- Codex 실제 ask: 같은 값과 세 exact ref를 한 문단으로 반환, exit 0.
- local GUI와 같은 `/api/agent/runs` SSE: HTTP 200, unique run과 message ID, grounded 답변, `RUN_FINISHED status=ok` 확인.
- 같은 GUI outcome에서 `value:005930:IS:2026Q1:sales`를 resolve해 값 133,873,444,000,000원을 반환하고 `verified` 상태 1건을 기록했다.
- Cline ACP는 일반 응답과 permission round-trip은 동작하지만 session MCP가 tool catalog에 없어 DartLab refs를 만들지 못했다. 설치 및 설정 성공을 제품 성공으로 오인하지 않고 `groundedReady=false`를 유지한다.
- targeted Python 회귀 52건, Ruff, Svelte check 오류 0, local production build 성공. 내장 브라우저 인스턴스가 없어 시각 클릭 자동화는 수행하지 못했으며 HTTP, 타입, 빌드 경로로 대체 검증했다.

### Exit decision

Claude와 Codex, local GUI의 verified analysis loop는 production 진입 가능하다. Cline embedded는 upstream capability proof 전까지 명시적으로 unavailable이며, 이 제한은 runtime 전체의 Claude 또는 Codex 사용을 막지 않는다. root 점수는 계약대로 즉시 올리지 않고 주간 outcome review에서 재판정한다.
