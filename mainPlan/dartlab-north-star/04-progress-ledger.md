# 04. Progress Ledger

## 2026-08-02 결정 4 번복: 축별 점수표 도입 (루트 README)

상태: 점수표 라이브. 운영자 지시로 xlpod README식 축별 점수표를 도입했다. 자리는 mainPlan이 아니라 **루트 README `## 북극성`** (운영자 확정).

1. 결정 4(수기 10점 maturity table 미도입)를 번복한다. 기각 사유였던 "수기"는 규율로 막는다: 점수 근거는 실제로 도는 게이트와 실측 여정뿐이며, 자동으로 실행되지 않는 경로는 구현돼 있어도 점수로 세지 않는다.
2. 초기 12축 점수(총 67.5/120)는 캘리브레이션이다. 재판정은 주간 outcome review에서만 하고, 근거 없는 상향은 무효다.
3. 북극성 전역 값(주간 검증 완료 분석 루프)은 여전히 `미측정`이다. 점수표는 축 성숙도이지 북극성 분자가 아니다.
4. 관찰: `src/dartlab/productOutcome/` 모듈 골격(contracts·store·service)이 작업 트리에 착수돼 "구현 0" 표기는 더 이상 정확하지 않다. 해당 작업 커밋 시 본 원장을 갱신한다.

## 2026-08-02 계획 수립

상태: 설계 완료, 구현 0.

### 확인한 현재 사실

- 루트 README에 repo-level 북극성 정의가 없다.
- `infra/workers/siteSignals`는 익명 path와 event counter이며 outcome identity가 없다.
- `tests/audit/aiMetricsDigest.py`는 turn과 latency 진단이다.
- `src/dartlab/server/agentMetrics.py`는 agent/workbench 분기 회귀 지표다.
- `Ref`, artifact, `responseStatus`, evidence gate는 verified analysis lifecycle의 기반으로 재사용 가능하다.
- 현재 전역 verified analysis count는 계산할 수 없다.

### 결정

1. 북극성 이름은 `Weekly Verified Analysis Loops`다.
2. completion은 delivered가 아니라 exact evidence 또는 artifact verify에서 발생한다.
3. current value는 `미측정`이다.
4. 수기 10점 maturity table은 도입하지 않는다.
5. remote aggregate는 admission authority와 opt-in 전까지 범위 밖이다.
6. 첫 실제 소비자는 `agent-runtime-engine`이다.

### NEXT

1. `tests/_attempts/productOutcome/` state machine 실증.
2. 실패 가능한 `northStarEvidence` audit 작성.
3. Skill OS product direction과 cycle 승격.
4. local semantic store와 scorecard 구현.

### Exit decision

아직 없음. Phase 0 완료 후 `expand`, `improve`, `repair`, `revert` 중 하나를 기록한다.
