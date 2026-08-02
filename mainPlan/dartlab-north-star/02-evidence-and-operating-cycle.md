# 02. Evidence Registry and Operating Cycle

## 1. Evidence registry

영구 정본은 `tests/audit/northStarEvidence.py`다. 문서에 테스트 파일명을 손으로 나열하는 것만으로는 증거가 되지 않는다.

제안 schema:

```python
NORTH_STAR_EVIDENCE = {
    "completeVerifiedAnalysisLoop": GoalEvidence(
        contracts=(...),
        integration=(...),
        browser=(...),
        budgets=(...),
        operator=(...),
    ),
}
```

registry gate는 다음을 전부 검사한다.

1. Skill OS의 product goal ID와 registry key가 정확히 일치한다.
2. 모든 artifact path가 실제 존재한다.
3. contract, integration, browser, budget, operator kind와 확장자가 맞는다.
4. 자동 증거는 `tests/run.py`의 blocking gate에서 실제 실행된다.
5. operator 증거는 자동 증거로 표시되지 않는다.
6. 한 test artifact가 상충하는 두 claim의 유일한 증거가 되지 않는다.
7. 새 mainPlan README가 primary goal ID를 정확히 하나 가진다.

`northStarEvidence.py` 자체는 결함 fixture를 주입해 file missing과 runner missing을 실제 red로 만드는 self-test를 가진다.

## 2. Permanent product truth

구현 완료 시 정본 배치는 다음과 같다.

- 루트 `README.md`: 북극성 한 문장, 현재 authority 상태, scorecard 실행 포인터.
- `operation.productDirection`: lifecycle, goal, measure, target, guardrail, disqualifier.
- `operation.productCycle`: outcome brief, ready, done, weekly review, release review.
- `src/dartlab/productOutcome.py`: executable semantic authority.
- `tests/audit/northStarEvidence.py`: executable evidence authority.
- `mainPlan/README.md`: 활성 이니셔티브와 primary goal만 표시.

Skill JSON 여섯 산출물은 project rule에 따라 수동 동기화하고 `tests/audit/checkEngineSpecSchema.py`와 artifact sync test로 drift를 차단한다.

## 3. Outcome brief

모든 신규 mainPlan 이니셔티브는 다음 필드를 채운다.

```text
Primary goal ID:
Supporting goal IDs:
User and real subject:
Observed loss transition:
Baseline authority:
Expected metric movement:
Guardrails at risk:
Complete vertical slice:
Automated evidence:
Operator evidence:
Rollback:
Exit decision:
```

구현 파일 수, PR 수, 테스트 수, 모델 수는 expected movement가 될 수 없다.

## 4. Priority rule

후보가 경쟁할 때 순서는 고정한다.

1. `repair`: evidence 오류, 미래정보 누수, secret leak, orphan process, destructive write.
2. `unblock`: 가장 큰 verified analysis loop 손실 전이.
3. `accelerate`: 가장 느린 전이를 줄이되 evidence를 보존.
4. `retain`: analysis capsule 재사용과 반복 research job 강화.
5. `broaden`: 새 runtime, market, engine, UI surface 추가.

한 번에 primary bottleneck 하나만 활성 구현한다. 같은 outcome brief를 닫는 기반 작업은 함께 갈 수 있지만 무관한 기능 폭은 기다린다.

## 5. Definition of ready

- primary goal ID가 하나다.
- 실제 사용자와 subject가 구체적이다.
- 손실 전이가 재현되거나 현재 데이터가 없다는 사실이 증명됐다.
- expected movement와 guardrail이 구현 전에 쓰였다.
- vertical slice가 evidence verify까지 끝난다.
- 필요한 live CLI, 계정, 네트워크 evidence가 operator gate로 분리됐다.
- prior AI path와 artifact를 보존하는 rollback이 있다.

## 6. Definition of done

- 실제 제품 표면에서 complete vertical slice가 돈다.
- unit, contract, integration, browser, budget, operator gate가 claim에 맞게 통과한다.
- exact evidence 또는 artifact resolve가 completion receipt를 만든다.
- 실패와 cancel이 기존 결과, secret, child process를 보존한다.
- scorecard가 movement와 guardrail regression을 구분한다.
- 영구 계약이 Skill OS와 executable registry로 승격됐다.
- `expand`, `improve`, `repair`, `revert` 중 하나가 progress ledger에 기록됐다.
- mainPlan 완료 4매듭을 지어 `_done`으로 이동했다.

## 7. Review cadence

### Weekly outcome review

1. scorecard를 started부터 retained까지 인과 순서로 읽는다.
2. guardrail failure가 있으면 즉시 repair로 전환한다.
3. 가장 큰 comparable transition loss를 하나 고른다.
4. active outcome brief와 baseline을 비교한다.
5. exit decision 없이 다음 primary initiative를 시작하지 않는다.

### Release review

1. fixture 기반 local verified analysis acceptance.
2. changed engine과 MCP contract test.
3. supported embedded runtime의 operator journey.
4. privacy, untrusted, evidence, cancel, process budget.
5. source contract와 generated UI contract drift.

### Target review

권위 있는 4개 complete weekly window가 생긴 뒤에만 numeric target을 정한다. target은 결과를 본 뒤 과거 window에 소급 변경하지 않는다.
