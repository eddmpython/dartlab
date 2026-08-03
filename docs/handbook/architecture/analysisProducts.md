# 분석 결과 조립

## 시뮬레이션과 기대 원장

`dartlab.simulate(...)`는 결정론 driver DAG를 실행한다. 노드는 입력, 계산, 출력을 명시하며 결과는 재현 가능한 scenario set이다. expectation ledger는 관측값, prior, 검증 상태를 분리하고 표본이 부족하면 검증된 것처럼 표시하지 않는다. 거시 시뮬레이션은 regime transition과 결과 container를 공통 타입으로 유지한다.

## 리포트

story의 thesis와 report model은 엔진 결과를 재계산하지 않고 구조화된 결론, 근거, 결손을 조립한다. Python과 UI는 `Company.reportModel`의 같은 모델을 소비한다. 기존 UI 전용 report 계약과 분석 model은 역할을 섞지 않는다.

## 산업 재무

산업 비교의 재무 지표는 회사 자료와 산업 집계의 source identity를 보존한다. dual source 값이 다를 때 임의로 합치지 않고 canonicalization 규칙과 결손 상태를 따른다.
