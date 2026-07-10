---
id: recipes.fundamental.disclosure.eventRadar.visualDecisionPack
title: Event Radar Visual Decision Pack
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.eventRadar
purpose: 이벤트 레이더 결과에서 사용할 수 있는 observed viz surface만 선택하고, evidenceBinding이 없으면 차트를 막는 L1/L1.5 절차다. 트리거 — 'Event Radar Visual Decision Pack', 'visual decision pack', 'visualDecisionPack'.
whenToUse:
  - event radar visualization
  - 촉매 레이더 차트
  - observed viz binding
inputs:
  - event radar memo tables
outputs:
  - visualDecisionPack table
capabilityRefs:
  - Company.gather
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.viz
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.visualDecisionPack
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - visualRef별 ready/blocked
  - requiredBinding
visualRefs:
  - engines.viz.priceChart
  - engines.viz.kpiRibbon
  - engines.viz.evidenceCoverage
  - engines.viz.mermaidDiagram
visualGuidance:
  - "사용 가능한 visualRef는 observed 상태의 priceChart, kpiRibbon, evidenceCoverage, mermaidDiagram으로 제한한다."
  - "requiredBinding이 blocked이면 차트 대신 tableRef를 답변한다."
linkedSkills:
  - recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit
  - recipes.fundamental.disclosure.eventRadar.deepDive
  - engines.company
gap:
  primary:
    - viz
    - synth
falsifier:
  description: "근거 없는 시각화를 만들면 실패로 본다."
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
  - unverified viz skill을 visualRefs에 연결하지 않는다.
  - priceRows 없이 priceChart를 만들지 않는다.
failureModes:
  - blocked visual을 무시하고 차트 emit
examples:
  - 이벤트 레이더 시각화 가능 여부 확인
audiences:
  llm: visualDecisionPack의 ready visualRef만 사용한다.
  agent: 차트를 만들기 전 requiredBinding을 확인한다.
  human: 시각화가 가능한 결과와 아직 표로 봐야 하는 결과를 구분한다.
humanIntro: "visualDecisionPack은 사용자가 요청한 시각 요소 품질 게이트다. 완성도 높은 observed viz만 연결하고, 근거가 없으면 막는다."
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

def rows(value, limit=40):
    if hasattr(value, "head") and hasattr(value, "to_dicts"):
        return value.head(limit).to_dicts()
    if isinstance(value, list):
        return value[:limit]
    return []

try:
    price_rows = rows(c.gather("price"), limit=40)
except Exception:
    price_rows = []

try:
    filings = rows(c.filings(), limit=50)
except Exception:
    filings = []

memo = buildEventRadarMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    filings=filings,
    priceRows=price_rows,
)

emit_result(
    table=memo["tables"]["visualDecisionPack"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

4 visualRef ready/blocked + requiredBinding 단정. 예: "visualDecisionPack 4 row — priceChart ready (priceRows 40개 + date/close/volume 컬럼 통과) / kpiRibbon ready (action count + filing count 동행) / evidenceCoverage ready (coverage table 통과) / mermaidDiagram blocked (사건 cluster 노드 < 3 — 메커니즘 부재). 3 ready + 1 blocked → blocked 항목은 tableRef 로 우회."

### 2. 핵심 근거 수집

- Company.gather('price') latest 40 row — priceChart binding
- Company.filings() filings — kpiRibbon + evidenceCoverage binding
- buildEventRadarMemo() → visualDecisionPack table (4 viz × status + requiredBinding)
- viz status (engines.viz.{name}) observed 상태 확인

### 3. 메커니즘 분석

```
4 visualRef × (status + requiredBinding + evidence)
   priceChart:
     ready 조건  → priceRows 존재 + date/close/volume 컬럼 통과
     blocked 시 → priceRows 결손 또는 컬럼 부적합 (tableRef 우회)
   kpiRibbon:
     ready 조건  → action count + filing count ≥ 1
     blocked 시 → 모든 row 0 (의미 없음)
   evidenceCoverage:
     ready 조건  → sourceCoverageAudit table 통과
     blocked 시 → audit 비어 있음
   mermaidDiagram:
     ready 조건  → cluster 노드 ≥ 3 + edge 근거 명시
     blocked 시 → 메커니즘 흐름 부재 (8 노드 이하 의미 X)
   ↓
forbidden 발동 (회피):
   unverified viz skill (예: engines.viz.experimental) → visualRefs 추가 X
   priceRows 없이 priceChart → 차트 만들지 X (tableRef 우회)
   blocked visual emit → false visualization
```

visualDecisionPack 은 *시각화 품질 게이트* — completed observed viz 만 통과. blocked 시 차트 대신 tableRef 로 답변 (forbidden 위반 회피).

### 4. 반례·한계

- visualRefs 에 unverified viz skill (incubator / experimental) 포함 → 품질 게이트 무너짐.
- priceRows 결손인데 priceChart=ready 표시 → false binding.
- requiredBinding 정의 모호 (예: "data 필요") → 실제 검증 불가.
- 4 viz 외 mermaidDiagram 가 8 노드 이상 → engines.viz 가이드 위반.

### 5. 후속 모니터링

- 4 visualRef 모두 ready → `recipes.fundamental.disclosure.eventRadar.deepDive` 의 visual gate 통과.
- priceChart blocked → `recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit` 으로 source 확인.
- mermaidDiagram blocked → cluster 분석 부재 — `recipes.news.eventTimelineFusion` 으로 cluster 만들기.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `visualRef` | observed viz skill |
| `status` | ready/blocked |
| `requiredBinding` | 필요한 근거 결합 |
| `evidence` | 선택 사유 |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit - source coverage 확인.
2. recipes.fundamental.disclosure.eventRadar.deepDive - 최종 답변의 visual gate.

## 기본 검증

- visualRefs는 observed viz만 포함한다.
- blocked visualRef를 emit하지 않는다.
