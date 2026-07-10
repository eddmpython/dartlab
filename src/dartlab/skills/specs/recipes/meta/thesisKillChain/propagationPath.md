---
id: recipes.meta.thesisKillChain.propagationPath
title: Thesis Kill-Chain Propagation Path
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.thesisKillChain
purpose: trigger가 어떤 mechanism을 거쳐 어떤 assumption을 깨는지 연결하는 pre-mortem 전파 경로 절차다.
whenToUse:
  - propagation path
  - thesis kill-chain path
  - trigger to assumption
inputs:
  - triggerCatalog
  - assumptionLedger
outputs:
  - propagationPath table
capabilityRefs:
  - Company.panel
  - Company.filings
  - Company.gather
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.viz
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/recipes.meta.thesisKillChain.propagationPath
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - sourceRef
  - executionRef
expectedOutputs:
  - triggerId mechanism affectedAssumption tripwire
visualRefs:
  - engines.viz.mermaidDiagram
visualGuidance:
  - "propagationPath는 engines.viz.mermaidDiagram diagram으로 8 edge 이하만 시각화한다."
linkedSkills:
  - recipes.meta.thesisKillChain.triggerCatalog
  - recipes.meta.thesisKillChain.tripwireMonitor
  - engines.company
gap:
  primary:
    - synth
    - viz
falsifier:
  description: "mechanism 없이 trigger와 conclusion을 직접 연결하면 실패로 본다."
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
  - trigger 하나로 thesis 붕괴를 단정하지 않는다.
failureModes:
  - trigger → conclusion 직행
examples:
  - thesis가 깨지는 전파 경로 그려줘
audiences:
  llm: mechanism과 affectedAssumption을 반드시 같이 표시한다.
  agent: diagram edge마다 tableRef/sourceRef를 연결한다.
  human: 작은 trigger가 어떻게 핵심 가정으로 전파되는지 본다.
humanIntro: "propagationPath는 이 팩의 핵심이다. 시나리오가 강하려면 '무슨 일이 생김'이 아니라 '어떤 경로로 가정이 깨짐'을 보여야 한다."
lastUpdated: "2026-05-17"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildThesisKillChainMemo`로 묶는 **RunPython fallback** 절차다.

```python
from dartlab.synth.thesisKillChain import buildThesisKillChainMemo

target = "005930"
thesis = "매출 성장과 현금 전환이 유지되어 valuation discount가 해소된다"
assumptions = ["매출 성장이 둔화되지 않는다", "CFO가 순이익을 따라온다"]
filings = [{"rcept_dt": "20260510", "report_nm": "전환사채 발행 결정"}]

memo = buildThesisKillChainMemo(target=target, thesis=thesis, filings=filings, assumptions=assumptions)

emit_result(
    table=memo["tables"]["propagationPath"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

trigger → mechanism → assumption path 단정. 예: "propagationPath 4 row order=1-4. Path 1: opmCompression → margin pressure 누적 → marginDurability 가정 깨짐 → tripwire OPM YoY > -2%p. Path 2: cbIssuance → 희석 +3% → valuationSupport 깨짐 → tripwire 전환비율 ≥ 30%. → 4 path 모두 mechanism + tripwire 명시 (trigger → conclusion 직행 회피)."

### 2. 핵심 근거 수집

- triggerCatalog (watch/risk trigger)
- assumptionLedger (5 표준 카테고리)
- Company.panel + disclosure + gather 보조 데이터
- buildThesisKillChainMemo() → propagationPath table

### 3. 메커니즘 분석

```
각 trigger × 매칭 assumption 연결
   triggerId → mechanism (1-3 단계 인과 chain) → affectedAssumption → tripwire
   ↓
mechanism 정의 (구체 동사):
   "margin pressure 누적" / "희석 가중" / "수요 둔화" / "FX 이익 감소"
   1 mechanism 만 (직접 연결) → trigger → conclusion 직행 (forbidden)
   2-3 mechanism (간접 chain) → 진성 propagation
   ↓
order (경로 순서):
   1 = root trigger
   2-N = downstream propagation
   각 step 에 tripwire (임계값 + 모니터링 조건) 명시 필수
   ↓
diagram (mermaid):
   8 edge 이하 제한 (engines.viz.mermaidDiagram 가이드)
   각 edge = mechanism 문장 + sourceRef 명시
```

mermaidDiagram 으로 시각화 시 8 edge 이하 — engines.viz 가이드. mechanism 없이 trigger → conclusion 직접 연결 시 forbidden 위반 (failureMode 발동).

### 4. 반례·한계

- mechanism 없이 trigger → conclusion 직행 → forbidden + failureMode.
- affectedAssumption 누락 path → 실패.
- diagram 8 edge 초과 → engines.viz.mermaidDiagram 가이드 위반.
- 단일 trigger → 단일 path 강제 X — 1 trigger 가 multi assumption 영향 가능.

### 5. 후속 모니터링

- 4+ path → `recipes.meta.thesisKillChain.tripwireMonitor` 로 임계 모니터링.
- mechanism 약함 → `recipes.meta.thesisKillChain.fragilityMap` 로 fragility 재측정.
- path 가 scenario 로 → `recipes.meta.thesisKillChain.scenarioStoryboard` 로 변환.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `order` | 경로 순서 |
| `triggerId` | 촉발 조건 |
| `mechanism` | 전파 메커니즘 |
| `affectedAssumption` | 깨지는 가정 |
| `tripwire` | 모니터링 임계 |
| `status` | watch/risk/missing |

## 연계 절차

1. recipes.meta.thesisKillChain.tripwireMonitor - 경로별 임계값 확인.
2. recipes.meta.thesisKillChain.scenarioStoryboard - path를 시나리오로 변환.

## 기본 검증

- affectedAssumption이 없는 경로는 실패다.
- diagram은 8 edge 이하로 제한한다.
