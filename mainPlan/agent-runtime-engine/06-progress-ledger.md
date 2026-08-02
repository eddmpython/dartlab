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

## 2026-08-02 완전성 강화와 실가동 재검증

상태: 답변 공개, 근거 복구, 총 실행시간, 연결 이탈, 동시성, FY 계산, Runtime Center의 실패 계약을 하나의 production 경계로 묶었다. "주요 구현"이 아니라 실제 질문이 정확한 근거와 함께 끝나거나 명시적으로 실패하는지를 완료 기준으로 삼는다.

### 강화한 실행 계약

- 중앙 `answerQuality`가 질문을 정량·문서 계약으로 분류한다. 정량 답변은 표/문서, 값, 기준시점 ref의 본문 인용뿐 아니라 인용 ref payload의 실제 값과 기간이 산문에 함께 결합돼야 공개된다. ref ID 문자열만 복사한 답변은 통과하지 못한다.
- 공개 답변은 native 정상 완료와 품질 게이트 통과 전까지 버퍼에 보류한다. 실패·중단·제한 초과 턴의 부분 산문은 UI에 공개하지 않는다.
- evidence는 transcript 없이 16 KiB 이하 공개 projection만 SQLite에 bounded 저장한다. 서버 재시작 뒤에도 exact `(outcomeId, refId)`만 복구하며 다른 outcome의 ref는 해석하지 않는다.
- 같은 세션의 동시 턴은 non-blocking lock으로 거부한다. hot-session LRU는 활성 턴을 퇴거하지 않고, 모두 활성 상태면 새 세션을 실패 폐쇄형으로 거부한다.
- 세 native driver는 프레임마다 갱신되지 않는 총 턴 deadline을 공유한다. 기본 300초, 환경 설정 범위 30~900초이며 초과 시 native interrupt/cancel과 공개 실패 이벤트를 남긴다.
- SSE 소비자 이탈과 async generator close도 native cancel로 연결한다. 실제 연결 종료 뒤 세션이 거짓 idle로 남거나 child turn이 계속 도는 경로를 차단했다.
- 분석 캡슐은 호스트가 완료한 bootstrap을 반복하지 않고, 사용자 의도의 `ReadSkill` 1회, 일반 질문 도구 8회 이내, 동일 인자 반복 금지, DartLab 외 MCP 금지, 근거 충족 즉시 종료를 선언한다.
- 질문에 명시된 첫 연도·분기를 bounded application context의 `period` 힌트로 승격한다. `Company.panel(period=YYYY, freq=Y)`는 IS/CF 네 분기를 FY로 직접 합산하고 FY table/value/date ref를 반환하므로 모델의 수기 재계산이 필요 없다.
- Runtime Center는 `groundedReady`, `canInstall`, `canConnect`, `blockingReason`, `recommendedAction`을 서버 정본 그대로 표시한다. protocol이 DartLab 근거 도구를 노출하지 않는 runtime에는 성공할 수 없는 설치·연결 동작을 제안하지 않는다.
- `dartlab ai --dev`는 UI app이 아니라 npm workspace root에서 의존성과 Vite binary를 찾고 workspace 명령으로 기동한다. 실제 5174/8400 동시 listen을 재검증했다.

### 실제 제품 여정

- 정량 CLI 질의: 2024년 매출액과 영업이익의 전년 비교를 실제 설치형 runtime에서 6개 도구로 완주했고 exact 값·표·기간 근거를 반환했다.
- 문서 CLI 질의: 2024 감사인과 별도/연결 감사의견을 실제 설치형 runtime에서 공시 문서·보고일·감사보고서 기준일 근거로 완주했다.
- UTF-8 local GUI SSE 질의: 삼성전자 2024년 연간 매출액 질문이 61.6초, 의미 도구 `ReadSkill -> EngineCall` 2회로 끝났다. 답변은 300,870,903,000,000원, `table:005930:IS:2024FY`, `value:005930:IS:2024FY:sales`, `date:005930:IS:2024FY`를 인용했고 정량 품질 100점이었다.
- 같은 GUI outcome의 exact value ref를 verification API로 다시 열어 `period=2024FY`, `value=300870903000000`, outcome state `verified`를 확인했다.
- 장기 실행 GUI 턴을 실제 cancel API로 중단했을 때 native terminal status가 `interrupted`, `activeTurnId=null`로 끝났다. 별도 연결 이탈 회귀도 native interrupt 1회를 보장한다.
- 의도적으로 끝나지 않는 턴은 302.9초에 "300초 제한 초과"로 실패했고 답변과 refs를 공개하지 않았다. 이 실측으로 무한 연장 결함을 회귀 자산으로 전환했다.
- `/chat`은 HTTP 200으로 기동했고, 준비된 runtime은 `groundedReady=true`, protocol 근거 미지원 runtime은 `groundedReady=false`와 차단 사유를 반환했다.

### Exit decision

`improve`. 지원 protocol의 정량·문서 질의, GUI streaming, 품질 commit, exact evidence verify, cancel, timeout, restart recovery가 production 경로에서 실증됐다. 모든 질문의 정답을 보장한다는 의미의 절대적 "완벽"은 선언하지 않으며, 미지원 protocol은 계속 fail-closed다. 다음 운영 과제는 질문군별 golden set과 주간 verified/retained cohort를 누적해 품질 하락을 자동 탐지하는 것이다.
