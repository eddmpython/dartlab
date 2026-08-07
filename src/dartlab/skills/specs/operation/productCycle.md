---
id: operation.productCycle
title: 제품 운영 주기 — Outcome Review
kind: curated
scope: builtin
status: observed
category: operation
purpose: 북극성 goal, 실행 증거, root scorecard, Skill OS 의 현재 제품 계약을 한 주기에서 정합시키는 운영 계약이다.
whenToUse:
  - 임시 initiative를 완료하고 확정 사실을 Skill OS 에 반영할 때
  - 북극성 축 점수를 재판정할 때
  - release acceptance와 operator journey를 기록할 때
inputs:
  - active initiatives
  - blocking gates
  - operator journey evidence
  - product outcome snapshot
outputs:
  - 유지·진행·중단 결정
  - evidence-backed scorecard update
capabilityRefs: []
toolRefs: []
knowledgeRefs:
  - operation.productDirection
  - operation.testing
sourceRefs:
  - dartlab://skills/operation.productCycle
requiredEvidence:
  - executionRef
  - sourceRef
expectedOutputs:
  - 주간 outcome review 기록
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
  - 코드가 존재한다는 이유만으로 점수를 올림
  - test fixture를 실제 사용자 결과로 셈
  - 실패와 미측정을 0 또는 성공으로 표시함
forbidden:
  - 자동 실행되지 않는 경로를 완결 여정으로 기록하지 않는다.
  - 근거 없이 root scorecard를 갱신하지 않는다.
examples:
  - Agent Runtime vertical slice를 operator journey로 검토
  - noData를 유지하고 목표 숫자 설정을 보류
linkedSkills:
  - operation.productDirection
  - operation.testing
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-02'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 주기

1. 이번 주 실제 사용자 outcome과 operator journey를 모은다.
2. 각 initiative의 primary goal과 disqualifier를 대조한다.
3. contracts, integration, UI, security, performance gate가 실제 runner에서 도는지 확인한다.
4. outcome이 없거나 권위가 부족하면 `noData` 또는 `미측정`을 유지한다.
5. root README 점수는 반복 검증이 늘거나 줄었을 때만 재판정한다.
6. 구현된 현재 계약은 코드에서 다시 확인해 Skill OS 운영문서에 반영한다. 완료는 이니셔티브 문서의 이관·승격이 아니라 확정 사실의 SSOT 반영이다. 반영 전 코드·테스트·README·Skill OS 가 임시 설계를 인용하지 않는지 감사하고, 완료된 임시 initiative 는 삭제한다. GUI 변경 완료는 desktop·tablet·mobile audit receipt 와 스크린숏이 함께 있어야 하며 브라우저 제어가 없으면 시각 검증 미완료로 명시한다.

## Release 질문

- 실제 질문에서 시작했는가.
- 정식 엔진 결과와 source identity가 있는가.
- 사용자가 exact evidence를 열 수 있는가.
- 실패, 취소, reconnect가 child process나 원장을 손상시키지 않는가.
- runtime을 바꿔도 같은 capability와 evidence 문법인가.

하나라도 아니면 기능 구현은 존재할 수 있어도 verified outcome 완료로 세지 않는다.
