# 03. Implementation Plan

## 1. 단계와 의존 순서

### Phase 0. Contract and failing gate

1. `tests/_attempts/productOutcome/`에서 state transition, duplicate, crash recovery, evidence resolve를 fixture로 실증한다.
2. `tests/audit/northStarEvidence.py`와 self-test를 먼저 만들고 의도적으로 없는 artifact와 runner 누락에서 red를 확인한다.
3. `operation.productDirection`, `operation.productCycle`을 추가하고 registry와 goal ID를 대조한다.
4. 루트 README에는 현재 값 `미측정`과 authority 포인터만 추가한다. 수기 점수는 만들지 않는다.

Exit: gate가 실제 결함을 잡고, goal vocabulary가 한 곳에서만 정의된다.

### Phase 1. Local semantic authority

1. `src/dartlab/productOutcome/contracts.py`에 frozen contract를 둔다.
2. `stateMachine.py`가 단조 전이와 completion 조건을 판정한다.
3. `store.py`가 SQLite transaction과 migration을 소유한다.
4. `recorder.py`가 local UI, CLI, MCP host의 명시적 boundary event만 받는다.
5. `scorecard.py`가 local causal scorecard와 `noData`를 출력한다.

Exit: fixture journey 한 건이 정확히 한 verified outcome을 만들고 duplicate/retry가 count를 늘리지 않는다.

### Phase 2. First product slice

첫 소비자는 `mainPlan/agent-runtime-engine`이다.

1. runtime session start에서 `started`.
2. canonical subject resolution에서 `scoped`.
3. DartLab MCP engine result에서 `grounded`.
4. turn complete와 evidence gate에서 `delivered`.
5. UI evidence open 또는 artifact reopen에서 `verified`.
6. capsule handoff 또는 reopen에서 `retained`.

Exit: Codex, Claude Code, generic ACP 중 하나의 operator journey가 transcript 복사 없이 완료된다.

### Phase 3. Surface expansion

CLI와 Python은 같은 state machine을 소비하되 자동 phone-home은 하지 않는다.

- CLI: evidence resolve, report/artifact reopen이 terminal outcome action.
- Python: explicit outcome context를 사용한 public engine journey부터 지원. 모든 library call을 몰래 계측하지 않는다.
- public web: siteSignals는 방향성 진단으로 유지하고 별도 numerator로 승격하지 않는다.

Exit: surface별 완료 의미가 다르지 않고 capability parity gate가 green이다.

### Phase 4. Baseline and target review

1. 4개 complete local/operator evidence window를 수집한다.
2. 데이터가 적으면 계속 `noData`로 둔다.
3. 권위가 충분한 signal에만 first evidence, verified conversion, retained conversion target을 설정한다.
4. 원격 aggregate가 필요하면 별도 privacy PRD를 작성한다.

## 영향 파일

### 신규

- `src/dartlab/productOutcome/__init__.py`
- `src/dartlab/productOutcome/contracts.py`
- `src/dartlab/productOutcome/stateMachine.py`
- `src/dartlab/productOutcome/store.py`
- `src/dartlab/productOutcome/recorder.py`
- `src/dartlab/productOutcome/scorecard.py`
- `tests/audit/northStarEvidence.py`
- `tests/audit/testNorthStarEvidence.py`
- `tests/productOutcome/testStateMachine.py`
- `tests/productOutcome/testStore.py`
- `tests/productOutcome/testScorecard.py`
- `src/dartlab/skills/specs/operation/productDirection.md`
- `src/dartlab/skills/specs/operation/productCycle.md`

### 변경

- `README.md`: 북극성 정의와 authority 상태.
- `mainPlan/README.md`: primary goal column과 북극성 initiative.
- `tests/run.py`: `north-star-evidence` blocking gate 등록.
- `.github/workflows/ci-fast.yml`: 동일 gate matrix 등록.
- `tests/audit/test_runEntrypoint.py`: runner drift 기대값.
- `src/dartlab/server/agentGateway.py`: Phase 2 outcome boundary event 전달.
- `src/dartlab/server/api/ask.py`: request origin과 outcome ID 수명주기.
- `ui/packages/contracts/src/ai.ts`: generated outcome ID와 evidence receipt 소비로 전환.
- `ui/apps/local/src/lib/chat/Evidence.svelte`: exact evidence resolve 성공 이벤트.
- Skill OS 여섯 JSON artifact: project sync rule에 따라 수동 갱신.

## 영향 함수와 심볼

- `AnalysisOutcomeState`: started, scoped, grounded, delivered, verified, retained.
- `AnalysisOutcomeEvent`: transition input. prompt와 answer 본문 필드 금지.
- `AnalysisOutcomeReceipt`: idempotent state receipt.
- `GoalEvidence`: contracts, integration, browser, budgets, operator.
- `applyOutcomeEvent(current, event)`: 유일한 transition 판정 함수.
- `recordOutcomeEvent(event)`: SQLite transaction boundary.
- `analysisOutcomeScorecard(windowDays=7)`: causal report.
- `assertNorthStarEvidence()`: goal, file, runner projection 검증.
- `streamAgentRun()`: outcome event를 직접 저장하지 않고 recorder port에 전달.
- `apiAsk()`: user origin outcome ID 발급과 response header 또는 event 연결.

provider, model, transcript 이름은 productOutcome contract에 들어가지 않는다.

## 테스트

| 위험 | 테스트 |
|---|---|
| 잘못된 상태 건너뛰기 | `testStateMachine.py` property transition matrix |
| duplicate count | 동일 receipt, reconnect, retry 반복 후 distinct 1 |
| partial write | transaction fault injection 후 delivered/verified 승격 0 |
| test traffic 오염 | `origin=test` count 제외 |
| evidence 없는 완료 | delivered와 verified 거부 |
| 다른 outcome ref 사용 | token/ref mismatch 거부 |
| privacy | DB schema와 serialized event에 question, answer, provider, model, token, path 금지 |
| registry drift | goal 추가, file rename, CI runner 누락 각각 red self-test |
| scorecard no data | 0을 success로 표시하지 않고 `noData` |
| UI false verify | chip render만으로 completion 0, ref resolve 200 뒤 1 |
| runtime cancel | cancelled turn completion 0, child cleanup guardrail |

검증 명령은 구현 시 `tests/run.py` gate에 들어가며 문서에만 남지 않는다.

## 롤백

- Phase 0은 문서와 audit gate만 독립 commit으로 되돌릴 수 있다.
- Phase 1 store는 새 DB만 만들며 기존 AI memory와 history를 수정하지 않는다. rollback은 recorder 배선을 제거하고 DB 파일을 보존한 채 reader를 비활성화한다.
- Phase 2는 outcome recording feature flag가 아니라 recorder dependency injection으로 격리한다. recorder 장애 시 분석은 실패시키지 않되 completion claim은 만들지 않고 명시적 metric error를 남긴다.
- schema migration은 forward migration과 read-only export를 제공한다. rollback에서 신규 DB를 자동 삭제하지 않는다.
- 원격 전송이 없으므로 사용자 데이터 회수 작업은 없다.
- mainPlan completion 전에는 root README에 숫자를 publish하지 않는다.

## 평가

### 전문 개발자 렌즈

- 강점: 기존 `Ref`, `TraceEvent`, artifact store를 재사용하고 transcript와 별도 outcome pointer만 저장한다. semantic authority와 count authority가 분리돼 provider 교체에 안전하다.
- 발견한 위험: UI click을 곧바로 검증으로 세면 vanity metric이 된다. exact ref resolve 또는 artifact reopen receipt가 있어야 하는 조건을 lifecycle에 반영했다.
- 발견한 위험: `tests/audit/aiMetricsDigest.py`를 확장하면 기술 KPI와 제품 outcome이 섞인다. 별도 `productOutcome` package와 scorecard로 분리했다.
- 발견한 위험: 문서에 evidence 파일을 나열해도 runner에서 빠질 수 있다. registry와 CI projection self-test를 필수로 넣었다.

### 전문 PM 렌즈

- 강점: 모델 호출이나 기능 출시가 아니라 사용자가 근거를 확인한 분석 결과를 센다. Agent Runtime 전환의 성공 여부도 같은 결과로 비교할 수 있다.
- 발견한 위험: 전역 사용량이 없는 상태에서 숫자를 내면 허위 정밀도가 된다. 현재 상태를 `미측정`으로 잠그고 4주 권위 window 전 target 설정을 금지했다.
- 발견한 위험: 지나치게 엄격한 verify 조건이 일회성 유용한 결과를 누락할 수 있다. delivered conversion을 별도 진단으로 보존하되 북극성은 verify까지 요구한다.
- 결론: Phase 0은 즉시 착수 가치가 있고, 원격 집계는 별도 승인 전 범위 밖이다.
