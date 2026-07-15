# Workflow attempts

> 상태: 계획 확정, 미실행
> 책임: 질문과 Skill OS recipe를 재현 가능한 `SceneBeat[]`와 evidence receipt로 컴파일한다.

## 가설

tested recipe의 procedure, requiredEvidence, falsifier를 유실 없이 장면으로 바꾸면 일반 그래프 또는 evidence table보다 사용자가 더 빨리 반증 가능한 판단에 도달한다.

## 실행 순서

1. U0-W02: tested recipe 10개의 필드를 센서스하고 archetype을 만든다.
2. U0-W03: `UniverseFlightPlan`, `SceneBeat`, `EvidenceReceipt`, `GapReceipt` canonical fixture를 검증한다.
3. U1-Y01: 성장 지속성, 신용 취약, 공시 변화 3개 task를 baseline과 비교한다.
4. U1-V01: 판정 우주의 PASS, FAIL, MISSING, NOT_APPLICABLE 보존을 검증한다.

## 합격

- procedure, requiredEvidence, falsifier 유실 0
- claim별 sourceRef 또는 derivationRef 100%
- 결론별 open falsifier 1개 이상
- 같은 입력의 flight hash 일치 100%
- baseline 대비 task 완료시간 또는 정확도 개선

## 기각

- 모델 요약을 fact로 승격한 사례 1건
- missing을 fail 또는 0으로 바꾼 사례 1건
- recipe마다 전용 UI adapter가 필요한 경우
- 정보 수율 개선 없이 animation만 늘어난 경우

## 산출물 예정

- `workflowProjectionProbe.py`
- `testWorkflowProjectionProbe.py`
- `flightPlanContract.py`
- `testFlightPlanContract.py`
- task fixture와 decision receipt

production 코드는 이 경로를 import하지 않는다. recipe compiler가 엔진 계산이나 predicate를 새로 만들면 실패다.
