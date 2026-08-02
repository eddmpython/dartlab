# 04. Progress Ledger

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
