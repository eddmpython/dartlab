---
id: recipes.meta.thesisKillChain.premortemQualityGate
title: Thesis Kill-Chain Premortem Quality Gate
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.thesisKillChain
purpose: Thesis Kill-Chain 결과를 최종 답변으로 쓰기 전, thesis·근거 폭·가정 수·취약 지표·trigger·전파 경로·tripwire·falsifier·scenario·visual binding을 모두 통과했는지 막판에 차단하는 품질 게이트다. 트리거 — '타협 없이 thesis 깨기', 'premortem quality gate', '강한 스킬 검증'.
whenToUse:
  - premortem quality gate
  - thesis kill-chain 품질 게이트
  - 타협 없이 thesis 깨기
  - 강한 스킬 검증
  - 약한 결론 차단
inputs:
  - thesisIntake
  - evidenceCoverageAudit
  - assumptionLedger
  - fragilityMap
  - triggerCatalog
  - propagationPath
  - tripwireMonitor
  - falsifierLedger
  - scenarioStoryboard
  - visualDecisionPack
outputs:
  - premortemQualityGate table
  - premortemQualityScore
  - qualityGateStatus
capabilityRefs:
  - Company.panel
  - Company.filings
  - Company.gather
  - scan.market
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - runtime.workbenchEvidenceFlow
  - operation.skillDevelopmentLoop
  - engines.viz
sourceRefs:
  - dartlab://skills/recipes.meta.thesisKillChain.premortemQualityGate
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - gate별 ok/risk 판정
  - weak/operatorReview/flagshipReady 상태
  - 답변 차단 사유와 nextAction
visualRefs:
  - engines.viz.evidenceCoverage
  - engines.viz.kpiRibbon
visualGuidance:
  - "premortemQualityGate는 engines.viz.evidenceCoverage 표로만 보조한다."
  - "premortemQualityScore와 qualityGateStatus는 engines.viz.kpiRibbon으로 작게 표시한다."
linkedSkills:
  - recipes.meta.thesisKillChain.visualDecisionPack
  - recipes.meta.thesisKillChain.deepDive
  - engines.company
gap:
  primary:
    - synth
    - gather
  secondary:
    - viz
testUniverse:
  market: KR+US
  stockCodes:
    - "005930"
    - "247540"
    - "AAPL"
  asOfPolicy: latest
falsifier:
  description: "qualityGateStatus가 weak인데도 thesis 결론을 확정하면 실패로 본다."
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: limited
forbidden:
  - qualityGateStatus가 weak이면 final conclusion을 쓰지 않는다.
  - premortemQualityGate risk row를 숨기지 않는다.
  - blocked visualRef를 emit하지 않는다.
failureModes:
  - sourceBreadth가 부족한데 narrative로 보강
  - propagationPath 없이 trigger만 나열
  - open falsifier 없이 scenario 확정
  - weak 상태를 usable처럼 표현
examples:
  - 이 thesis kill-chain이 답변 가능한 품질인지 게이트로 막아봐
  - 타협 없이 thesis 프리모템 품질 검증
audiences:
  llm: 이 스킬은 최종 답변 차단 게이트다. risk row가 있으면 그 사유와 nextAction을 먼저 말한다.
  agent: answer draft 전에 premortemQualityGate를 확인하고 weak/operatorReview이면 보수적으로 답한다.
  human: pre-mortem 결과가 정말 강한지, 아니면 근거가 빈 narrative인지 판정하는 마지막 게이트다.
humanIntro: "premortemQualityGate는 Thesis Kill-Chain을 강하게 만드는 장치다. 분석이 그럴듯해 보여도 thesis, 근거 폭, 전파 경로, 반증, 시각화 결합 중 하나가 비면 최종 답변을 막는다."
lastUpdated: "2026-05-17"
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel`, `Company.filings`, `Company.gather`, `scan.market`, `scan.audit`, `scan.quality`로 근거를 먼저 확보하고, 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildThesisKillChainMemo`로 묶는 **RunPython fallback** 절차다.

```python
from dartlab.synth.thesisKillChain import buildThesisKillChainMemo

target = "005930"
thesis = "매출 성장과 현금 전환이 유지되어 valuation discount가 해소된다"
priceRows = [{"date": "2026-05-11", "close": 90000}, {"date": "2026-05-10", "close": 100000}]

memo = buildThesisKillChainMemo(target=target, thesis=thesis, priceRows=priceRows)

emit_result(
    table=memo["tables"]["premortemQualityGate"],
    values={
        "premortemQualityScore": memo["headline"]["premortemQualityScore"],
        "qualityGateStatus": memo["headline"]["qualityGateStatus"],
        "decisionStatus": memo["headline"]["decisionStatus"],
    },
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

10 gate × premortemQualityScore + qualityGateStatus 단정. 예: "premortemQualityGate 10 row — 8 ok + 2 risk (sourceBreadth + falsifierOpen). qualityScore=8/10 → qualityGateStatus=operatorReview (90% 미달, weak 아님). decisionStatus=mediated — 누락 gate 2 종 보강 후 결론 가능."

### 2. 핵심 근거 수집

- thesisIntake + assumptionLedger + fragilityMap + triggerCatalog + propagationPath + tripwireMonitor + falsifierLedger + scenarioStoryboard + visualDecisionPack (9 sub-recipe)
- evidenceCoverageAudit (source 폭)
- buildThesisKillChainMemo() → premortemQualityGate table

### 3. 메커니즘 분석

10개 gate를 모두 확인한다.

| gate | 차단 의미 |
|---|---|
| `explicitThesis` | thesis가 없으면 프리모템이 아니라 입력 요청이다. |
| `sourceBreadth` | L1/L1.5 근거가 좁으면 narrative로 본다. |
| `assumptionDepth` | testable assumption 3개 미만이면 결론을 막는다. |
| `fragilityDetected` | 취약 지표가 없으면 kill-chain이 아니다. |
| `triggerConnected` | trigger가 없으면 시나리오가 시작되지 않는다. |
| `propagationConnected` | trigger → mechanism → assumption 경로가 없으면 분석이 아니다. |
| `tripwireOperational` | threshold/action 없는 risk는 모니터링할 수 없다. |
| `falsifierOpen` | counter-evidence가 없으면 confirmation bias다. |
| `scenarioComplete` | base/erosion/kill-chain 세 시나리오가 모두 필요하다. |
| `visualBindingReady` | observed viz라도 table/value ref에 묶이지 않으면 emit하지 않는다. |

### 4. 반례·한계

- qualityGateStatus=weak 인데 thesis 결론 확정 → forbidden + falsifier 위반.
- risk row 삭제 또는 평균 점수로 숨김 → 스킬 실패 (forbidden).
- sourceBreadth 부족하지만 narrative 로 보강 → failureMode (분석 왜곡).
- propagationPath 없이 trigger 만 나열 → failureMode + premortem 무효.

### 5. 후속 모니터링

- flagshipReady → `recipes.meta.thesisKillChain.deepDive` 로 최종 답변 통합.
- operatorReview → 누락 gate 보강 (사용자에게 nextAction 제시).
- weak → 답변 차단 + 보강 EngineCall 목록 제시.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `order` | gate 순서 |
| `gate` | 품질 조건 이름 |
| `status` | ok/risk |
| `required` | 통과 조건 |
| `evidence` | 현재 근거 |
| `failureMode` | 실패 시 분석 왜곡 |
| `nextAction` | 보강 조치 |

## 타협 없는 사용 기준

- `qualityGateStatus == "flagshipReady"`일 때만 `decisionStatus == "usable"`로 답한다.
- `operatorReview`이면 결론보다 누락 gate와 보강 순서를 먼저 말한다.
- `weak`이면 thesis 결론을 쓰지 않고, 부족한 근거와 다음 EngineCall 목록을 제시한다.
- `risk` row를 삭제하거나 평균 점수로 숨기면 이 스킬은 실패다.

## 연계 절차

1. recipes.meta.thesisKillChain.visualDecisionPack - visual binding 확인.
2. recipes.meta.thesisKillChain.deepDive - 최종 실행 ledger.

## 기본 검증

- `premortemQualityGate`는 10개 gate를 반환해야 한다.
- `flagshipReady`는 gate 90% 이상 통과일 때만 가능하다.
- `weak` 상태에서는 thesis 결론을 확정하지 않는다.
