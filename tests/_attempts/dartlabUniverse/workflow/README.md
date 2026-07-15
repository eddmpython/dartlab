# Workflow attempts

> 상태: U0-W02 compiler 계약 완료, live conclusion 차단
> 책임: 질문과 Skill OS recipe를 재현 가능한 `SceneBeat[]`와 evidence receipt로 컴파일한다.

## 가설

tested recipe의 procedure, requiredEvidence, falsifier를 유실 없이 장면으로 바꾸면 일반 그래프 또는 evidence table보다 사용자가 더 빨리 반증 가능한 판단에 도달한다.

## 실행 순서

1. U0-W02: tested recipe 10개의 필드를 센서스하고 generic SceneBeat compiler를 검증한다. 완료.
2. U0-W03: `UniverseFlightPlan`, `SceneBeat`, `EvidenceReceipt`, `GapReceipt` canonical fixture를 검증한다.
3. U1-Y01: 성장 지속성, 신용 취약, 공시 변화 3개 task를 baseline과 비교한다.
4. U1-V01: 판정 우주의 PASS, FAIL, MISSING, NOT_APPLICABLE 보존을 검증한다.

## 합격

- procedure, requiredEvidence, falsifier 유실 0
- claim별 sourceRef 또는 derivationRef 100%
- 결론별 open falsifier 1개 이상
- 같은 입력의 flight hash 일치 100%
- baseline 대비 task 완료시간 또는 정확도 개선

## U0-W02 실행

```powershell
uv run python -X utf8 tests/_attempts/dartlabUniverse/workflow/workflowProjectionProbe.py
uv run python -X utf8 tests/audit/docstring4Section.py tests/_attempts/dartlabUniverse/workflow --strict
uv run python -X utf8 tests/audit/docstring9Section.py tests/_attempts/dartlabUniverse/workflow --strict
```

Unit test는 repository test lock을 획득한 뒤 `testWorkflowProjectionProbe.py` 단일 파일만 실행한다.

## U0-W02 결과

| 항목 | 실측 |
|---|---:|
| 전체 recipe | 156 |
| tested recipe | 30 |
| procedure, requiredEvidence, negative condition, sourceRef 완비 | 22/30 |
| deterministic selected recipe | 10 |
| selected procedure | 80 |
| selected recipeSteps | 25 |
| selected requiredEvidence | 60 |
| selected sourceRef recipe | 10/10 |
| preserved negative condition candidate | 29 |
| qualified falsifier | 0 |
| tested explicit version field | 0/30 |
| tested explicit falsifier field | 0/30 |
| procedure preservation | 100% |
| requiredEvidence evidence 또는 gap accounting | 100% |
| falsifier candidate preservation | 100% |
| missing evidence GapReceipt | 60 |
| live conclusion beat | 0 |
| model fact promotion | 0 |
| recipe별 adapter | 0 |
| repeated flight hash | 10/10 |
| unit regression | 8/8 PASS |

Recipe version은 immutable catalog Git blob과 recipe canonical content hash로 만들었다. Current catalog blob `3c9c61cff18d19abb21cf275a1d8c55082dbb78e`는 U0-S01 SourceSnapshotSet에 기록한 blob과 일치했다. 따라서 explicit version field 0은 compiler가 content identity로 닫았고 live blocker로 보지 않는다.

반면 catalog의 `failureModes`와 `forbidden`은 origin을 보존한 falsifier candidate일 뿐 검증 reference가 결속된 qualified falsifier가 아니다. Compiler는 candidate를 전부 falsify beat로 보존하지만 conclude를 열지 않는다. Empty execution binding 60개도 `GapReceipt`로 남기고 missing을 fail, 0, fact로 바꾸지 않는다.

판정은 `revise`다. U0-W02 generic compiler 계약은 완료했다. 그러나 explicit falsifier schema, verificationRefs와 execution EvidenceReceipt가 준비되기 전 live Thesis Kill-Chain 결론은 차단한다. Synthetic qualified fixture에서는 모든 required evidence와 open qualified falsifier가 있을 때만 provisional conclude가 열렸다.

## 기각

- 모델 요약을 fact로 승격한 사례 1건
- missing을 fail 또는 0으로 바꾼 사례 1건
- recipe마다 전용 UI adapter가 필요한 경우
- 정보 수율 개선 없이 animation만 늘어난 경우

## 산출물

- `workflowProjectionProbe.py`, 완료
- `testWorkflowProjectionProbe.py`, 완료
- `flightPlanContract.py`
- `testFlightPlanContract.py`
- task fixture와 decision receipt

production 코드는 이 경로를 import하지 않는다. recipe compiler가 엔진 계산이나 predicate를 새로 만들면 실패다.
