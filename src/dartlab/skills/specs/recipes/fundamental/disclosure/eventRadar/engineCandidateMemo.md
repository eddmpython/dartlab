---
id: recipes.fundamental.disclosure.eventRadar.engineCandidateMemo
title: Event Radar Engine Candidate Memo
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.eventRadar
purpose: 이벤트 레이더에서 반복 가능한 신호를 나중에 엔진으로 환류할 후보로 정리하되, recipe 검산 경로는 계속 유지하는 L1/L1.5 절차다. 트리거 — 'Event Radar Engine Candidate Memo', 'engine candidate memo', 'engineCandidateMemo'.
whenToUse:
  - event radar engine candidate
  - 엔진 환류 후보
  - recipe to engine
inputs:
  - event radar memo tables
outputs:
  - engineCandidateMemo table
capabilityRefs:
  - Company.filings
  - Company.gather
  - scan.market
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - operation.architecture
  - operation.skillDevelopmentLoop
sourceRefs:
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.engineCandidateMemo
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - signalId별 status
  - recommendedEngineOwner
  - promotionGate
visualRefs:
  - engines.viz.evidenceCoverage
  - engines.viz.mermaidDiagram
visualGuidance:
  - "엔진 후보 흐름은 engines.viz.mermaidDiagram으로 8노드 이하만 표시한다."
linkedSkills:
  - recipes.fundamental.disclosure.eventRadar.falsifierLedger
  - recipes.fundamental.disclosure.eventRadar.deepDive
  - engines.company
gap:
  primary:
    - synth
    - gather
falsifier:
  description: "단일 실행 결과를 엔진 구현 완료처럼 표현하면 실패로 본다."
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
  - engineCandidateMemo를 실제 엔진 구현으로 표현하지 않는다.
failureModes:
  - selfRun 없이 엔진 승격 후보로 확정
examples:
  - 이벤트 레이더에서 엔진 후보 정리
audiences:
  llm: 이 표는 승격 후보 메모이지 엔진 결과가 아니다.
  agent: promotionGate와 keepAsSkillAfterPromotion을 그대로 보여준다.
  human: 어떤 recipe 신호가 엔진화될 만한지 검토한다.
humanIntro: "engineCandidateMemo는 사용자가 말한 '진짜 스킬은 recipe'라는 방향을 보존한다. 반복 가능한 축만 엔진으로 옮기고 recipe는 검산 경로로 남긴다."
lastUpdated: "2026-05-17"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEventRadarMemo`로 묶는 **RunPython fallback** 절차다.

```python
import dartlab
from dartlab.synth.eventRadar import buildEventRadarMemo

target = "005930"
c = dartlab.Company(target)

def rows(value, limit=30):
    if hasattr(value, "head") and hasattr(value, "to_dicts"):
        return value.head(limit).to_dicts()
    if isinstance(value, list):
        return value[:limit]
    return []

try:
    filings = rows(c.filings(), limit=50)
except Exception:
    filings = []

try:
    price_rows = rows(c.gather("price"), limit=40)
except Exception:
    price_rows = []

try:
    consensus_rows = rows(c.gather("consensus"), limit=12)
except Exception:
    consensus_rows = []

memo = buildEventRadarMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    filings=filings,
    priceRows=price_rows,
    consensusRows=consensus_rows,
)

emit_result(
    table=memo["tables"]["engineCandidateMemo"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

6 signal 후보 + promotionGate 단정. 예: "engineCandidateMemo 6 row — eventInbox status=watch promotionGate='ledger 통과 4 회 누적' / priceFlowReaction status=ok promotionGate='falsifier resolved 60%+' / insiderOwnershipSignal status=missing (data 없음) / capitalActionMonitor status=ok promotionGate='action 추세 12M+' / consensusDriftWatch status=watch / scanContext status=ok. 4 of 6 signal 승격 후보 (status=ok 또는 watch + gate 명시)."

### 2. 핵심 근거 수집

- Company.filings() filings + gather('price') + gather('consensus') 3 source
- buildEventRadarMemo() → 6 signal × (status + recommendedEngineOwner + promotionGate + keepAsSkillAfterPromotion)
- 각 signal 별 *recipe 검산 경로 유지* 명시 (keepAsSkillAfterPromotion=True)

### 3. 메커니즘 분석

```
6 signal 후보 → status 분류 + promotion 조건
   signalId               status        promotionGate                    engineOwner
   eventInbox             ok/watch      ledger 통과 ≥ 4 회                Company.filings
   priceFlowReaction      ok            falsifier resolved 비율 ≥ 60%    Company.gather(price/flow)
   insiderOwnershipSignal ok/missing    insider rows ≥ 12 회 (12M+)      Company.gather(insider)
   capitalActionMonitor   ok            action 추세 12M+                  Company.gather(dividend)
   consensusDriftWatch    ok/watch      consensus rows ≥ 12 회            Company.gather(consensus)
   scanContext            ok            scan universe 정합 12M+           scan.market
   ↓
승격 의사결정:
   status=ok + promotionGate 충족 → 엔진 환류 (구현 시작)
   status=watch + gate 부분 충족 → 검증 더 (1-2 분기 추적)
   status=missing               → 데이터 부재 (제외)
   ↓
keepAsSkillAfterPromotion=True 강제:
   엔진화 이후에도 recipe 보존 — 검산 경로 유지 + dogfood 가능성
```

본 메모는 *후보 정리* — 실제 엔진 구현 X. 단일 실행 결과를 엔진 완료처럼 표현 시 forbidden 위반.

### 4. 반례·한계

- 단일 실행 결과를 엔진 구현으로 표현 → forbidden 위반.
- promotionGate 가 없는 후보는 미완성 — 실패 처리.
- selfRun 없이 status=ok 단정 → 데이터 미검증 위험.
- engineOwner 정의가 너무 모호 (예: "Company") → 실제 환류 어려움.

### 5. 후속 모니터링

- promotionGate 충족 → engine 환류 plan 시작 (운영자 결정).
- 모든 후보 status=watch → `recipes.fundamental.disclosure.eventRadar.falsifierLedger` 로 ledger 통과율 점검.
- selfRun 결과 일관 → `recipes.fundamental.disclosure.eventRadar.visualDecisionPack` 으로 observed viz binding.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `signalId` | 후보 축 |
| `status` | missing/ok/watch/risk |
| `recommendedEngineOwner` | 나중에 담당할 엔진 영역 |
| `promotionGate` | 승격 조건 |
| `keepAsSkillAfterPromotion` | recipe 보존 여부 |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.falsifierLedger - 반증 통과 확인.
2. recipes.fundamental.disclosure.eventRadar.visualDecisionPack - observed viz binding 확인.

## 기본 검증

- promotionGate가 없는 후보는 실패다.
- 단일 실행 결과는 구현 완료가 아니다.
