---
id: operation.aiEngine
title: AI Engine — Bring Your Agent Runtime
kind: curated
scope: builtin
status: observed
category: operation
purpose: 설치된 Codex CLI, Claude Code, ACP 호환 agent가 인증·모델·세션을 소유하고 DartLab은 Skill OS·MCP·금융 엔진·근거 계약을 제공하는 AI 실행 SSOT다.
whenToUse:
  - dartlab.ask 또는 /api/ask 실행 경계를 변경할 때
  - Codex, Claude Code, Cline runtime driver를 추가하거나 수정할 때
  - Runtime Center의 탐지, 설치, MCP 연결, 승인 UX를 변경할 때
  - AgentEvent와 AG-UI projection을 변경할 때
inputs:
  - 사용자 질문
  - 선택적 runtimeId와 sessionId
  - workspace context
outputs:
  - provider-neutral AgentEvent stream
  - AG-UI public stream
  - DartLab evidence refs와 artifacts
capabilityRefs: []
toolRefs:
  - ReadSkill
  - GetSkillBody
  - ReadCapability
  - EngineCall
  - RunPython
  - WebSearch
  - SaveArtifact
knowledgeRefs:
  - operation.productDirection
  - operation.productCycle
  - operation.architecture
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.aiEngine
  - dartlab://agent-runtime
requiredEvidence:
  - runtimeId
  - sessionId
  - executionRef
  - sourceRef
expectedOutputs:
  - 설치형 agent runtime 실행 결과
  - MCP 기반 DartLab 근거
  - 명시적 권한 승인 또는 안전한 거부
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
failureModes:
  - runtime별 business rule과 tool 목록을 driver에 복사함
  - CLI stdout 문장을 제품 계약으로 파싱함
  - 사용자 승인 없이 설치나 전역 MCP 설정을 실행함
  - DartLab이 provider API key, OAuth token, native transcript를 저장함
  - MCP 안에서 ask를 다시 호출해 runtime 재귀를 만듦
  - 고정 Graph나 Loop를 모든 질문에 강제함
forbidden:
  - direct model SDK를 production ask 경로에서 호출하지 않는다.
  - provider별 OAuth와 API key 입력 UI를 만들지 않는다.
  - shell 문자열, shell=True, 무검증 install argv를 실행하지 않는다.
  - 모델명과 vendor명을 Product Outcome 완료 조건에 넣지 않는다.
examples:
  - dartlab.ask("삼성전자 수익성", runtimeId="codex")
  - uv run python -X utf8 -m dartlab setup codex --yes
  - dartlab agent status --refresh
  - dartlab agent connect codex --approve-digest <digest>
  - uv run python -X utf8 -m dartlab invest 005930 --runtime codex --expert
procedure:
  - Runtime manifest에서 실행 파일 후보와 protocol driver를 읽는다.
  - 15초 TTL probe로 설치·버전, DartLab MCP 연결, embedded grounding capability를 확인하고 셋 다 준비된 groundedReady runtime만 선택한다.
  - native session을 열거나 저장된 opaque session mapping으로 재개한다.
  - 짧은 analysis capsule과 MCP 도구를 agent에 제공한다.
  - native event를 AgentEvent로 투영하고 AG-UI allowlist로 공개한다.
  - install과 MCP connect는 계획 argv와 SHA-256 digest를 먼저 보여주고 동일 digest 승인 뒤에만 실행한다.
linkedSkills:
  - operation.productDirection
  - operation.productCycle
  - runtime.mcp
  - operation.ui
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-07'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 제품 경계

```text
dartlab.ask / /api/ask / DartLab UI
  -> Agent Runtime Engine
  -> Codex app-server | Claude stream-json | ACP v1
  -> 사용자의 agent 계정, 모델, native session
  -> DartLab MCP
  -> Skill OS / Company / scan / analysis / macro / quant / evidence
```

DartLab은 모델 provider가 아니다. 사용자가 이미 로그인한 agent CLI를 실행하고, 그 agent가 DartLab MCP로 공시·재무·시장 능력을 사용하게 한다. runtrol은 별도 레포의 설계 참고이며 runtime dependency, daemon, shared package가 아니다.

## 코드 SSOT

| 책임 | 정본 |
|---|---|
| 공개 진입점 | `dartlab.ask`, `/api/ask` |
| 런타임 조정 | `src/dartlab/ai/runtime/engine.py` |
| runtime 목록·실행 argv | `src/dartlab/ai/runtime/manifests/*.toml` |
| Codex protocol | `drivers/codexAppServer.py` |
| Claude protocol | `drivers/claudeStreamJson.py` |
| ACP protocol | `drivers/acp.py` |
| process 수명주기 | `processSupervisor.py` |
| 이벤트 계약 | `contracts.AgentEvent`, `schema.py` |
| MCP 연결 계획 | `mcpBootstrap.py` |
| 설치 계획 | `installManager.py` |
| 세션 mapping | `sessionStore.py` |
| 안전한 evidence 복구 | `evidenceStore.py` |
| 답변 공개 품질 | `answerQuality.py` |
| 준비 상태 판정 | `ai/runtime/readiness.py` |
| 분석 캡슐 | `ai/runtime/analysisCapsule.py` |
| 공개 SSE 게이트웨이 | `server/agentGateway.py` |
| 근거 제시 projection | `ai/tools/panelInsight/`, `ai/tools/engineResult.py` |
| 통합 준비·투자 CLI | `cli/commands/setup.py`, `cli/commands/invest.py` |
| UI 관리 표면 | `/api/agent/*`, Runtime Center |
| 북극성 결과 원장 | `src/dartlab/productOutcome.py` |

`agent.py`는 runtime event를 기존 `TraceEvent` adapter로 투영한다. 새 실행 의미는 runtime package가 정본이며 provider별 조건문을 gateway와 UI에 추가하지 않는다.

## 안정 계약

- manifest가 runtime ID, executable 후보, version args, launch args, Windows native launch, install args, embedded grounding 지원, 공식 문서를 선언한다.
- process 실행은 argv 배열과 `shell=False`만 사용한다.
- stdout/stderr frame은 각각 1 MiB와 256 KiB 한도를 적용한다.
- 세션 event ring은 256건 또는 4 MiB로 제한하고 sequence 이후 replay를 지원한다.
- hot session은 최대 4개이며 퇴거·서버 종료 시 child process를 닫는다.
- DartLab DB에는 session ID, runtime ID, native session ID, cwd mapping만 저장한다. transcript는 저장하지 않는다.
- 알 수 없는 native event는 버리지 않고 `native` event로 보존한다.
- application context는 종목, 기간, 보고 모드, include/exclude, bounded dashboard snapshot만 16 KiB 이하로 전달한다. 대화 transcript는 CLI native session이 소유한다.
- 품질 판정은 답을 삭제하는 게이트가 아니라 사용자에게 보이는 검증 뱃지다. native 성공, grounding tool 성공, 본문 인용 표/문서·값·기준일 exact ref 가 모두 있으면 `verified`, 근거 계약을 못 채운 답은 `unverified` 뱃지와 함께 본문·근거를 그대로 전달하고, 런타임 자체가 실패한 경우만 `failed` 다. 자동 repair 재주입은 하지 않는다 (모델 루프를 소유하지 않는다). 근거: 게이트 시절 실측 2026-08-04, 8질문 중 6건이 인용 서식 사유로 기각됐고 기각된 답도 근거 8~56개를 실인용한 실분석이었다.
- 정량 답변은 ref ID 인용만으로 충분하지 않다. 인용한 value/date payload의 실제 값과 기간이 답변 산문에 함께 결합돼야 한다. 문서형 질문은 값 ref를 강제하지 않고 문서와 기준시점 결합을 요구한다.
- evidence는 transcript 없이 ref별 64 KiB 이하 공개 projection만 bounded SQLite에 저장하며 exact outcome/ref 조합으로만 재시작 복구한다. 상한을 넘는 원본 표와 문서는 table/doc/value/date ref 및 bounded preview로 축약한다.
- 같은 세션의 동시 턴은 거부하고 활성 세션은 LRU 퇴거하지 않는다.
- 총 턴 제한은 기본 300초이고 `DARTLAB_AGENT_TURN_TIMEOUT_SECONDS`로 30~900초 범위에서만 조정한다. 제한 초과와 SSE 소비자 이탈은 native cancel/interrupt를 실행한다.
- 턴이 상한을 넘겨 끝나지 않아도 그때까지 쓴 본문과 근거는 미완 표시와 함께 전달한다.
- 런타임이 말한 실패 사유는 그대로 사용자에게 보인다. 사유를 품질 라벨로 갈아 끼우지 않는다.
- Python ask 와 CLI 는 실패 `done` 을 빈 문자열이나 종료코드 0 으로 낮추지 않는다.
- `server/agentGateway.py` 는 공개 이벤트 allowlist 만 SSE 로 투영한다. 실행마다 `RUN_ERROR` 는 최대 1회, `RUN_FINISHED` 는 정확히 1회다. 공개 이벤트 종류(17종)의 정본은 `ai/runtime/contracts.py` `PUBLIC_AGENT_EVENT_KINDS` 이고 TypeScript 계약은 여기서 생성한다. 성공 종료는 최종 근거 ID 와 품질 metadata 를, 실패 종료는 candidate ref 와 공개 가능한 실패 이유를 담는다.
- `ai/runtime/analysisCapsule.py` 는 질문에서 대상·지표·기간을 분해한 `claimCellContract` 를 application context 에 넣는다. 최초 턴과 교정 턴은 같은 원 질문 계약을 사용한다.
- `EngineCall` 결과는 canonical tool name, tool call ID, source identity, 기간과 값을 보존한다. 로컬 계산 결과는 canonical upstream lineage 가 있을 때만 최종 근거로 인정한다.

## 권한과 설치

- 탐지는 자동이지만 설치와 전역 MCP 설정은 자동 실행하지 않는다.
- Runtime Center와 CLI는 먼저 exact argv, 공식 문서 URL, digest를 표시한다.
- apply 요청의 digest와 현재 manifest로 다시 계산한 계획이 모두 일치해야 실행한다.
- Codex와 ACP의 native approval request는 UI로 전달한다.
- Claude print mode는 MCP 지연 검색용 `ToolSearch` 하나와 registry가 read-only로 판정한 DartLab MCP 도구만 노출·허용하며 write 권한을 확대하지 않는다.
- Codex, Claude, Cline의 MCP 연결은 각 공식 CLI 계획과 exact digest 승인 뒤에만 적용한다. 설치만 된 runtime은 실행 가능 상태가 아니다.
- 전역 MCP 설정 파일이 있어도 embedded protocol이 MCP tool을 실제 노출하지 않으면 groundedReady가 아니다. Cline 3.0.49 ACP는 이 조건을 만족하지 않아 fail-closed다.
- agent 인증은 해당 CLI의 공식 로그인 명령에서만 수행한다.
- Claude driver 는 명시적 허용 목록과 함께 내장 실행 도구를 이름으로 차단한다. 허용 목록만으로는 차단이 되지 않는다 (실측). 도구 검색은 막지 않는다. 지연 로딩되는 DartLab 도구를 그 경로로 발견하므로 막으면 도구 사용이 0 이 된다 (실측 후 되돌림).
- 일반 사용자 여정은 통합 준비 하나다: `dartlab setup codex --yes` (`--yes` 없으면 변경 없이 계획만 출력, GUI 는 Runtime Center `분석 엔진 준비`). 완료된 단계는 재실행하지 않는다. 지원 대상은 Codex 와 Claude Code 이고 Cline 은 상태 확인 계약만 유지한다. 정상 사용 가능 상태는 `dartlab agent status --refresh` 의 `investmentReady=true` 다.
- `install` 과 `connect` 는 기본 실행에서 계획과 digest 만 출력하고 같은 명령에 `--approve-digest <digest>` 를 붙였을 때만 실행한다. 관리 API 는 `/api/agent/*` (runtimes·default·probe·install/login/mcp plan·apply·sessions·events·cancel·product-outcomes evidence·verify).
- 런타임이 하나만 준비되면 자동 선택할 수 있다. 둘 이상 준비됐고 기본값이 없으면 임의 선택하지 않고 Runtime Center 선택을 요구한다. 대화가 시작되면 그 런타임은 대화 끝까지 고정된다.
- 종목 의사결정 브리프는 `dartlab invest <code> --runtime <id>` 전용 명령이다. 기본 브리프는 중심논지, 가장 강한 반대논지, 실적 변곡, 산업·거시 전파, 현재가에 반영된 기대, bear/base/bull 시나리오, 촉매, 리스크, 논지 훼손 조건, 다음 점검 시점을 요구하고 `--expert` 는 WACC, reverse DCF, 시나리오 driver, 근거 계보와 결손까지 편다.

## 준비 상태

- 상태 응답 `readiness` 는 `install`, `auth`, `protocol`, `grounding`, `delivery`, `ready` 여섯 축을 분리한다 (`ai/runtime/readiness.py`).
- 앞 네 축은 CLI 에게 물어보면 알 수 있지만 "질문하면 답이 나오는가" 는 알 수 없다. 설치·로그인·MCP 등록이 전부 정상이면서 계정 사용량 한도로 모델이 한 토큰도 못 만드는 상태가 실재한다. `delivery` 축이 그 간극을 담당한다.
- delivery 는 3상태다. `verified` = 마지막 턴이 DartLab MCP 도구를 실제 호출. `blocked` = 마지막 턴이 도구를 하나도 못 부른 채 런타임 오류로 종료 (사유는 `blockingReason` 에 런타임 원문 그대로). `unknown` = 아직 턴을 돌린 적 없음 (준비로도 미준비로도 단정하지 않는다). `blocked` 만 groundedReady 를 false 로 만든다.
- 판정은 턴 종료 시 기록되고 상태 조회는 그 기록만 읽는다 (조회에 실호출 비용 0). `blocked` 해제는 셋뿐이다: 다음 성공 턴, 사용자의 명시적 다시 확인 (도달을 증명하지 않으므로 `verified` 가 아니라 `unknown` 으로 되돌림), 6시간 경과.
- 설치, 인증, embedded grounding protocol, DartLab MCP 연결을 모두 통과하고 마지막 실제 턴이 도구 도달에 실패하지 않았을 때만 `groundedReady=true` 다.

## 장애 복구

- 여러 런타임이 준비됐는데 기본값이 없으면 Runtime Center 에서 하나를 고른다.
- 통합 setup 이 중단되면 같은 명령을 다시 실행한다. 완료된 단계는 건너뛰고 실패한 단계부터 재개한다.
- 인증 실패는 계정 정보나 명령 원문을 노출하지 않고 로그인 필요 상태로 낮춘다.
- MCP 연결이 오래된 설정이면 새 연결 계획을 적용하고 probe 를 다시 실행한다.
- 브라우저 연결이 끊기면 서버 session event replay 를 sequence 기준으로 사용한다.

## MCP 계약

- MCP tools/list는 `ai.tools.registry.CANONICAL_V2`에서만 파생한다.
- `ask`는 광고하지 않는다. agent가 MCP ask를 통해 agent를 재귀 실행하면 안 된다.
- 호스트가 Skill OS bootstrap을 완료했으므로 runtime은 `start.dartlabSkillOs`와 operation skill을 다시 읽지 않는다.
- capability registry는 공개 계약 241개를 분류하고, 그중 실행 가능한 182개에는 구조화된 `engineCallContract`를 둔다. reference-only 59개는 실행 가능한 canonical replacement를 선언하며 runtime이 존재하지 않는 도구를 호출하게 하지 않는다.
- `ReadSkill`은 질문별 `informationCoverage`를 반환한다. 여기에는 우선 capability, 보조 capability, 필요한 근거 종류, 비교축, 최신성 정책, 결손이 포함되며 실행 순서를 고정하지 않는다.
- 권장 순서는 `사용자 의도의 ReadSkill 정확히 1회 -> capabilityDetails의 EngineCall -> ref가 있는 답변`이다. ReadCapability는 capabilityDetails가 부족한 경우에만, RunPython은 실제 다단 가공이 필요한 경우에만 쓴다.
- 같은 도구와 인자를 반복하지 않고 일반 질문은 8회 이내에서 끝낸다. 필요한 table/doc, value, date ref가 확보되면 즉시 최종 답변을 작성한다.
- 질문에 명시된 연도/분기는 bounded period hint로 전달한다. `Company.panel`의 `period=YYYY`, `freq=Y`는 IS/CF 네 분기를 FY로 합산해 FY table/value/date ref를 직접 반환한다.
- 정량 답변은 한국어 조·억·만·원 단위를 precision-aware 방식으로 원시 값과 검산한다. 비교 질문은 대상·지표·기간의 같은 축을, 감사 질문은 감사의견 등급과 핵심감사사항을 인용 doc payload와 직접 대조한다.
- `turnCompleted`는 사용한 capability, 지원 capability, 충족·미충족 근거와 결손을 `runtimeCoverage`로 공개한다. coverage는 실행 영수증이지 성공을 가장하는 완료율이 아니다.
- Skill 읽기나 모델 산문은 북극성 `grounded`가 아니다. 실제 계산 도구가 성공하고 정형 ref가 있어야 한다.

## 근거 제시 계약

모델 루프를 소유하지 않으므로 답변 품질의 정공법은 답을 고쳐 쓰는 것이 아니라 건네주는 근거 자체를 판단 가능한 형태로 만드는 것이다. 지침 추가는 이미 실패한 방법이다. 지침이 안 지켜지는 이유는 대개 데이터가 그것을 불가능하거나 비싸게 만들기 때문이다 (스크리닝의 도구 56회 호출은 지침 불이행이 아니라 `scan` 이 행 본문 없이 개수만 돌려줘서 종목마다 다시 부를 수밖에 없던 결과였다).

- `ai/tools/panelInsight/` 가 이 원칙의 구현이다. 값을 꺼내는 원시 도구(`values`), 표에서 계산되는 파생 지표(`derived`), 회사 밖 기준과 뒤집히는 지점(`anchors`) 3분할. 손에 이미 있는 시계열만 쓰므로 추가 조회와 지연이 없다.
- 한 도구에만 적용하면 그 도구를 안 쓰는 질문에서 통째로 빠진다. 실측(2026-08-06): `Company.panel` 은 본문 1810자를 건네는데 `analysis`·`quant`·`credit` 은 본문 0자였다 ("실행 완료" 5글자 + 9184자 중첩 dict). panel 경로 답변은 근거 39건, analysis 경로는 3226자를 쓰고도 근거 3건 인용 2건이었다.
- `ai/tools/engineResult.py` 가 그 구멍을 막는다. 기간별 행 목록, 기간 키 맵, 최상위 스칼라, 격자 미리보기 네 모양을 받아 표와 줄로 편다. 계산도 해석도 하지 않고 옮겨 적기만 한다. 표를 그리면 그 표를 가리키는 근거를 함께 발급하고 표 제목 옆에 근거 id 를 적는다. 가리킬 이름이 본문에 없으면 인용은 비싼 일이 되고 실제로 안 된다.
- 못 재는 것은 못 잰다고 적는다. `assessmentStatus partial` 을 본문에 실으면 모델이 그것으로 자기 확신의 범위를 스스로 좁힌다.
- 비교 기준은 질문의 결을 따른다. 재무 건전성 질문이 업종 기준 0개로 끝난 원인은 업종 축이 영업이익률·ROE·매출성장률뿐이어서였고, 부채비율·유동비율 축을 더해 닫았다. 방향이 다른 축은 방향을 문장에 적는다 (부채비율을 "업종 상위 몇 %" 로 쓰면 정확히 반대로 읽힌다).
- 비용이 드는 재료는 임계 경로 순차가 배경 예열보다 빠를 수 있다 (실측: 동시 69.2초, 순차 44.4초. 같은 저장소를 읽는 병렬이 서로를 느리게 한다). 예열은 겨루는 상대가 없을 때만 이득이다.
- 시장 횡단면 표는 회사가 아니라 시장 소속이다. 프로세스 안에 한 번만 읽되 (`industry/calcs/sectorTables.py`) 원본 격자 대신 필요한 열만 실수로 뽑은 3MB projection 을 든다. 압력 관리 캐시에 수천 행 격자를 넣으면 이 저장소의 메모리 압력에서 곧바로 되돌려진다.
- 지켜야 할 선은 하나다. 사실만 적고 판정하지 않는다. 완만한 시계열에 기저효과 경고를 붙이지 않고, 조합표에 없는 현금흐름 모양에 해석을 지어내지 않으며, 하방 산술은 임의 시나리오가 아니라 실제 관측치만 쓰고 전망이 아님을 문장에 명시한다.
- `Panel` wide 격자의 형태와 내용은 불가침이다. 여기서 만드는 것은 표현 계층의 병존 projection 이다.

## Product Outcome 연결

상태는 `started -> scoped -> grounded -> delivered -> verified -> retained` 순서다.

- 질문 시작으로 `started`를 발급한다.
- canonical 실행 도구가 정형 ref를 반환해야 `scoped`, `grounded`가 된다.
- 성공 turn과 근거가 함께 있어야 `delivered`다.
- 사용자가 같은 outcome의 exact ref를 열어 서버의 opaque hash receipt가 일치해야 `verified`다.
- 근거 확인 API는 active runtime의 bounded evidence journal에서 exact ref detail을 먼저 resolve한 뒤 hash receipt를 검증한다.
- tool call, 텍스트 생성, evidence chip 렌더만으로 verified를 자동 기록하지 않는다.

## 검증

- `tests/ai/runtime/`: manifest, protocol projection, supervisor, session, engine vertical slice.
- `tests/ai/runtime/test_answerQuality.py`: 질문 유형, exact 값·기간 binding, ref 문자열 위조 거부.
- `tests/reference/capability/test_informationCoverage.py`: 질문별 coverage, 실행 계약, reference-only replacement.
- `tests/ai/test_engine_call_auto_gather.py`: 명시 FY 집계와 period-bound value/date ref.
- `tests/productOutcome/`: 단조 전이, duplicate receipt, privacy schema.
- `tests/mcp/`: registry와 tools/list drift, 재귀 ask 부재.
- UI는 `npm run check`와 `npm run build`를 모두 통과해야 한다.
- 실질 ask 판정은 답변 문자열 유무가 아니라 실행 결과다: `finalEvent=answer`, `requiredClaimCells` 와 `coveredClaimCells` 일치, 최종 답변이 인용한 ref 가 committed evidence 에 존재, CLI 상태줄 마지막 품질 판정 `verify: ok`.
- 최종 release 전 실제 설치 계정으로 Codex, Claude, ACP handshake를 각각 확인하고 child process가 남지 않았는지 점검한다.
