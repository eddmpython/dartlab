# 04. Progress Ledger

## 2026-08-02 점수제 세분화: 8차원 능력 매트릭스

운영자 지시(혁신성·효율성·직관성·속도 등 다양한 능력으로 철저히 세분화)로 축별 단일 성숙도 점수를 8차원 평균으로 분해했다.

1. 차원 = 근거·커버리지·검증강도·직관성·속도·효율성·안정성·혁신성. 정의·앵커·축별 채점 근거는 [05-score-rubric.md](05-score-rubric.md)가 정본이며, 근거 줄 없이 숫자만 바꾸는 diff는 무효다.
2. 축 종합 = 8차원 산술평균(0.1 단위). 총점 67.5 → 72.0/120(평균 6.0). 상승분은 분해 재캘리브레이션과 local semantic foundation 실측(운영자 실행 delivered 통과) 반영분이며 성장 실적이 아니다.
3. 채점 규율 유지: 자동으로 돌지 않는 경로는 세지 않는다. 운영자 수동 실행은 현 상태 서술에만 남기고 검증강도로 세지 않는다. 실측·게이트와 연결되지 않은 차원 점수는 주간 재판정에서 우선 하향 대상.
4. 설계·문서만 있는 축은 차원 무관 0.5~2.5 밴드 상한(Agent Runtime 1.5, 북극성 측정 2.0이 해당).

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

## 2026-08-02 local semantic foundation

- `src/dartlab/productOutcome`에 SQLite 상태 원장과 단조 전이를 구현했다.
- 저장 필드는 opaque outcome ID, feature, state, created/updated 시각과 SHA-256 evidence hash뿐이다.
- 질문, 답변, provider, model, token, 원본 ref, 파일 경로는 저장하지 않는다.
- Agent Runtime은 실제 grounding tool이 정형 ref를 반환한 경우에만 scoped·grounded로 전진하고, 성공 turn과 근거가 함께 있을 때 delivered로 끝난다.
- UI evidence chip 렌더는 completion이 아니다. 사용자가 `근거 확인`을 눌러 같은 outcome의 exact ref hash가 일치할 때만 verified가 된다.
- duplicate verification receipt는 idempotent하며 다른 outcome/ref 조합은 거부한다.
- 로컬 `/api/agent/product-outcomes` snapshot은 phone-home 없이 상태 집계만 반환한다.
- 실제 Claude CLI가 ReadSkill과 EngineCall을 호출해 grounded·delivered까지 전진하는 운영자 실행을 통과했다. UI의 exact evidence 확인은 대신 누르지 않았으므로 verified로 과장하지 않는다.

전역 북극성 값은 계속 `미측정`이다. remote aggregation, 4주 baseline, retained 28일 판정, root score 재판정은 아직 권위가 없으므로 만들지 않았다.

### NEXT

1. `tests/_attempts/productOutcome/` state machine 실증.
2. 실패 가능한 `northStarEvidence` audit 작성.
3. Skill OS product direction과 cycle 승격.
4. local semantic store와 scorecard 구현.

### Exit decision

아직 없음. Phase 0 완료 후 `expand`, `improve`, `repair`, `revert` 중 하나를 기록한다.
