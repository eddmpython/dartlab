---
id: operation.productDirection
title: 제품 방향 — Weekly Verified Analysis Loops
kind: curated
scope: builtin
status: observed
category: operation
purpose: 기능 수나 모델 호출 수가 아니라 사용자가 정확한 근거를 확인한 분석 결과를 DartLab의 북극성으로 삼는 제품 방향 계약이다.
whenToUse:
  - 임시 initiative의 primary goal을 정할 때
  - AI, UI, Python, CLI 기능의 제품 완료를 판정할 때
  - 북극성 지표 또는 scorecard를 변경할 때
inputs:
  - product initiative
  - verified operator evidence
outputs:
  - primary goal ID
  - outcome lifecycle acceptance
capabilityRefs: []
toolRefs: []
knowledgeRefs:
  - operation.productCycle
  - operation.aiEngine
sourceRefs:
  - dartlab://skills/operation.productDirection
requiredEvidence:
  - sourceRef
  - executionRef
expectedOutputs:
  - verified analysis loop
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
  - tool call, token, pageview, 테스트 통과를 사용자 결과로 셈
  - evidence chip 렌더를 verified로 셈
  - 권위 있는 baseline 전에 성장 목표 숫자를 만듦
forbidden:
  - 질문, 답변, provider, model, token, 파일 경로를 outcome 원장에 저장하지 않는다.
  - 원격 집계를 별도 privacy 승인 없이 추가하지 않는다.
examples:
  - completeVerifiedAnalysisLoop
  - reachFirstEvidence
  - verifyAnalysisResult
linkedSkills:
  - operation.productCycle
  - operation.aiEngine
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-02'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 북극성

`weeklyVerifiedAnalysisLoops`는 실제 질문이 정식 DartLab 엔진의 non-empty 계산과 source identity를 거쳐 전달되고, 사용자가 같은 outcome의 exact evidence 또는 artifact를 직접 확인한 distinct 건수다.

상태는 `started -> scoped -> grounded -> delivered -> verified -> retained` 순서로만 전이한다. 분자는 verified이며 retained는 후행 품질 지표다.

## Goal ID

- `completeVerifiedAnalysisLoop`
- `startFromRealQuestion`
- `reachFirstEvidence`
- `verifyAnalysisResult`
- `retainAnalysisOutcome`
- `protectResearchTrust`
- `keepAnalysisResponsive`
- `keepCapabilityParity`

모든 initiative는 primary goal을 정확히 하나 고른다. 모델 응답, 설치 성공, MCP 등록, artifact 생성만으로 완료를 선언하지 않는다.

## 권위

- 전역 값은 원격 privacy PRD와 권위 window가 생기기 전까지 `미측정`이다.
- 로컬 SQLite는 사용자 기기에서 outcome 상태와 opaque ref hash만 보존한다.
- root README 축별 점수는 실제 gate와 operator journey에 근거하고 주간 review에서만 재판정한다.
- 제품 성숙도는 근거, 커버리지, 검증강도, 직관성, 속도, 효율성, 안정성, 혁신성 8차원을 독립적으로 본다. 기능 코드가 있다는 사실만으로 점수를 올리지 않는다. 실제 공개 표면의 반복 여정과 실패 가능한 실행 가드가 추가되거나 사라졌을 때만 outcome review 에서 재판정한다.
