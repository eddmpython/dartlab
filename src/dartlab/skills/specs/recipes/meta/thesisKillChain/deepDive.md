---
id: recipes.meta.thesisKillChain.deepDive
title: Thesis Kill-Chain Deep Dive
category: recipes
kind: recipe
scope: builtin
status: curated
entryHint: true
graphTier: L1.5
cluster: incubator.thesisKillChain
purpose: thesis intake, evidence coverage, assumption ledger, fragility map, trigger catalog, propagation path, tripwire, falsifier, scenario storyboard, visual gate, premortem quality gate를 한 번에 실행하는 pre-mortem 시나리오 최종 절차다.
whenToUse:
  - thesis kill-chain deep dive
  - 프리모템 전체 실행
  - 투자 논리 깨보기 전체
inputs:
  - thesis
  - Company.panel 원표
  - filing/price/flow/consensus/scan rows
outputs:
  - deepDive step ledger
  - killRiskScore
  - open tripwire count
  - scenario storyboard
  - premortem quality gate
capabilityRefs:
  - Company.panel
  - Company.filings
  - Company.gather
  - scan.market
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - operation.skillDevelopmentLoop
  - runtime.workbenchEvidenceFlow
  - engines.viz
sourceRefs:
  - dartlab://skills/recipes.meta.thesisKillChain.deepDive
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 12단계 deepDive ledger
  - killRiskScore와 openTripwireCount
  - premortemQualityScore와 qualityGateStatus
  - propagationPath와 scenarioStoryboard
  - visualDecisionPack
visualRefs:
  - engines.viz.scenarioVisuals
  - engines.viz.mermaidDiagram
  - engines.viz.evidenceCoverage
  - engines.viz.kpiRibbon
visualGuidance:
  - "scenarioStoryboard table이 있을 때만 engines.viz.scenarioVisuals chart를 사용한다."
  - "propagationPath는 engines.viz.mermaidDiagram diagram으로 8 edge 이하만 표시한다."
  - "coverage/falsifier 상태는 evidenceCoverage 표 시각화로만 보조한다."
  - "killRiskScore/openTripwireCount는 kpiRibbon chart로만 작게 보조한다."
linkedSkills:
  - recipes.meta.thesisKillChain.thesisIntake
  - recipes.meta.thesisKillChain.evidenceCoverageAudit
  - recipes.meta.thesisKillChain.assumptionLedger
  - recipes.meta.thesisKillChain.fragilityMap
  - recipes.meta.thesisKillChain.triggerCatalog
  - recipes.meta.thesisKillChain.propagationPath
  - recipes.meta.thesisKillChain.tripwireMonitor
  - recipes.meta.thesisKillChain.falsifierLedger
  - recipes.meta.thesisKillChain.scenarioStoryboard
  - recipes.meta.thesisKillChain.visualDecisionPack
  - recipes.meta.thesisKillChain.premortemQualityGate
gap:
  primary:
    - synth
    - gather
  secondary:
    - scan
    - viz
testUniverse:
  market: KR+US
  stockCodes:
    - "005930"
    - "247540"
    - "AAPL"
  asOfPolicy: latest
falsifier:
  description: "deepDive가 thesis 결론만 말하고 propagationPath, tripwire, falsifier를 누락하면 실패로 본다."
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
  - c.analysis, c.credit, c.quant, c.macro, c.industry, c.story를 호출하지 않는다.
  - thesis 지지 결론으로 답변을 시작하지 않는다.
  - premortemQualityGate가 weak이면 final conclusion을 쓰지 않는다.
  - blocked visualRef를 emit하지 않는다.
failureModes:
  - 기존 companyDeepAnalysis로 우회
  - scenarioStoryboard만 있고 tripwire가 없음
  - open falsifier를 숨김
examples:
  - 삼성전자 thesis kill-chain deep dive
  - 투자 논리 pre-mortem 전체 실행
audiences:
  llm: capabilityRefs는 EngineCall로 우선 호출하고 공개 호출 블록은 L1.5 memo builder용 RunPython fallback으로만 실행한다.
  agent: 답변은 assumption, fragility, propagation, tripwire, falsifier, scenario를 함께 묶는다.
  human: thesis가 깨지는 경로를 한 번에 실행하는 실제 사용 경로다.
humanIntro: "deepDive는 Thesis Kill-Chain 팩의 실제 사용 경로다. 투자 논리를 더 멋지게 만드는 게 아니라, 그 논리가 어디서부터 무너질 수 있는지 끝까지 추적한다."
lastUpdated: "2026-05-17"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel`, `Company.filings`, `Company.gather`, `scan.market`, `scan.audit`, `scan.quality`는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildThesisKillChainMemo`로 묶는 **RunPython fallback** 절차다.

```python
import dartlab
from dartlab.synth.thesisKillChain import buildThesisKillChainMemo

target = "005930"
thesis = "매출 성장과 현금 전환이 유지되어 valuation discount가 해소된다"
c = dartlab.Company(target)

def rows(value, limit=30):
    if hasattr(value, "head") and hasattr(value, "to_dicts"):
        return value.head(limit).to_dicts()
    if isinstance(value, list):
        return value[:limit]
    return []

def gather_rows(axis, limit=30):
    try:
        return rows(c.gather(axis), limit=limit)
    except Exception:
        try:
            return rows(dartlab.gather(axis, target=target), limit=limit)
        except Exception:
            return []

statements = {}
for topic in ("IS", "BS", "CF"):
    try:
        statements[topic] = c.panel(topic, freq="Y")
    except TypeError:
        statements[topic] = c.panel(topic)
    except Exception:
        pass

try:
    filings = rows(c.filings(), limit=50)
except Exception:
    filings = []

memo = buildThesisKillChainMemo(
    target=target,
    thesis=thesis,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    statements=statements,
    filings=filings,
    priceRows=gather_rows("price", limit=40),
    flowRows=gather_rows("flow", limit=40),
    consensusRows=gather_rows("consensus", limit=12),
)

emit_result(
    table=memo["tables"]["deepDive"],
    values={
        "target": target,
        "killRiskScore": memo["headline"]["killRiskScore"],
        "openTripwires": memo["headline"]["openTripwireCount"],
        "openFalsifiers": memo["headline"]["openFalsifierCount"],
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

`finalDecision` row 의 `killRiskScore` + `qualityGateStatus` + `decisionStatus` 3 축 단정. 예: "killRiskScore=0.6, qualityGate=acceptable, decisionStatus=usable — thesis 유효하지만 propagationPath 2 단계 + tripwire X 활성 필요."

### 2. 핵심 근거 수집

- IS/BS/CF 시계열 (Company.panel)
- 공시 row 50 건 (Company.filings)
- L1.5 ledger 11 단계 (thesisIntake → evidenceCoverageAudit → assumptionLedger → fragilityMap → triggerCatalog → propagationPath → tripwireMonitor → falsifierLedger → scenarioStoryboard → visualDecisionPack → premortemQualityGate)

### 3. 메커니즘 분석

```
thesis 입력 → buildThesisKillChainMemo
   ↓
thesisIntake → assumption 추출 → fragilityMap (가정 깨질 조건)
   ↓
triggerCatalog (외부 충격 후보) → propagationPath (충격 → 결론 전파)
   ↓
tripwireMonitor (조기 경보 임계) + falsifierLedger (open 반증)
   ↓
scenarioStoryboard (baseIntact / erosionCase / killChainCase 3 시나리오)
   ↓
visualDecisionPack + premortemQualityGate (10 gate 검증)
   ↓
finalDecision: killRiskScore + qualityGateStatus + decisionStatus
```

각 ledger 의 status (missing/ok/watch/risk) 가 누적돼 killRiskScore 산출. qualityGate weak 이면 decisionStatus=usable 진입 불가.

### 4. 반례·한계

- thesis 가 모호하면 (예: "좋아 보임") fragilityMap 추출 실패 → assumption ledger 빈약.
- propagationPath 가 정량 ref 없이 순수 narrative 면 추적 불가능 — qualityGate 가 weak 판정.
- L2/L3 엔진 (c.analysis/c.credit/c.quant/c.macro 등) 호출 금지 — 호출 시 본 recipe 의 *원자료 trace* 정체성 위반.
- premortemQualityGate risk row 가 있으면 결론보다 차단 사유 우선 답안.

### 5. 후속 모니터링

- decisionStatus=operatorReview 시: 보강할 EngineCall 목록 + 막힌 gate 명시 후 다음 turn 에 보강 (`recipes.meta.thesisKillChain.evidenceCoverageAudit`).
- killRiskScore > 0.5: `recipes.meta.thesisKillChain.tripwireMonitor` 임계 활성 추적.
- open falsifier 1+ 건: `recipes.meta.thesisKillChain.falsifierLedger` 매 분기 재측정.

## 대표 반환 형태

`deepDive : list[dict]`

| column | 의미 |
|---|---|
| `order` | 실행 순서 |
| `step` | 세부 ledger 이름 |
| `status` | missing/ok/watch/risk |
| `rowCount` | 해당 ledger row 수 |
| `evidence` | 대표 근거 |
| `nextAction` | 다음 조치 |

## 연계 절차

1. recipes.meta.thesisKillChain.thesisIntake - thesis intake.
2. recipes.meta.thesisKillChain.evidenceCoverageAudit - evidence coverage.
3. recipes.meta.thesisKillChain.assumptionLedger - assumption ledger.
4. recipes.meta.thesisKillChain.fragilityMap - fragility map.
5. recipes.meta.thesisKillChain.triggerCatalog - trigger catalog.
6. recipes.meta.thesisKillChain.propagationPath - propagation path.
7. recipes.meta.thesisKillChain.tripwireMonitor - tripwire monitor.
8. recipes.meta.thesisKillChain.falsifierLedger - falsifier ledger.
9. recipes.meta.thesisKillChain.scenarioStoryboard - scenario storyboard.
10. recipes.meta.thesisKillChain.visualDecisionPack - visual gate.
11. recipes.meta.thesisKillChain.premortemQualityGate - final answer gate.

## 타협 없는 사용 기준

- `premortemQualityGate`의 risk row가 있으면 결론보다 차단 사유와 nextAction을 먼저 쓴다.
- `qualityGateStatus == "weak"`이면 `decisionStatus == "usable"`이 될 수 없다.
- `operatorReview`이면 확정 결론 대신 보강할 EngineCall 목록과 어떤 gate가 막혔는지 답한다.

## 기본 검증

- 공개 호출 블록은 AST parse가 되어야 한다.
- 공개 호출 블록은 L2/L3 호출 문자열을 포함하면 실패다.
- scenarioStoryboard에는 baseIntact, erosionCase, killChainCase가 모두 있어야 한다.
- premortemQualityGate는 10개 gate를 반환해야 한다.
- ready가 아닌 visualRef는 차트로 emit하지 않는다.
