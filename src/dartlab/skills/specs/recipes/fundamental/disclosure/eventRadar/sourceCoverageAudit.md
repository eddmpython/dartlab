---
id: recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit
title: Event Radar Source Coverage Audit
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.eventRadar
purpose: 이벤트 레이더 실행 전에 filing, news, price, flow, insider, ownership, dividend, split, consensus, scan primitive의 row coverage를 확인하는 L1/L1.5 절차다. 트리거 — 'Event Radar Source Coverage Audit', 'source coverage audit', 'sourceCoverageAudit'.
whenToUse:
  - 이벤트 레이더 coverage
  - catalyst source audit
  - 원자료 결손 확인
inputs:
  - raw event radar input rows
outputs:
  - sourceCoverageAudit table
capabilityRefs:
  - Company.filings
  - Company.filings
  - Company.gather
  - scan.market
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.company
  - engines.gather
  - engines.scan
sourceRefs:
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit
requiredEvidence:
  - skillRef
  - tableRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - source별 rowCount와 latestDate
  - missing source와 requiredFor
visualRefs:
  - engines.viz.evidenceCoverage
visualGuidance:
  - "sourceCoverageAudit table row가 있을 때만 engines.viz.evidenceCoverage coverage 표 시각화를 사용한다."
linkedSkills:
  - recipes.fundamental.disclosure.eventRadar.index
  - recipes.fundamental.disclosure.eventRadar.deepDive
  - engines.company
gap:
  primary:
    - synth
    - gather
falsifier:
  description: "coverage 결손을 숨기고 이벤트 결론을 내면 실패로 본다."
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
  - 결손 source를 0 또는 없음으로 단정하지 않는다.
failureModes:
  - priceRows 없이 priceChart를 선택
  - filings 결손인데 eventInbox를 정상으로 처리
examples:
  - 이벤트 레이더 source coverage 확인
audiences:
  llm: EngineCall로 원자료를 먼저 받고 RunPython fallback은 coverage table emit에만 사용한다.
  agent: missing source를 답변 한계로 노출한다.
  human: 실행 전에 어떤 원자료가 비었는지 보는 게이트다.
humanIntro: "source coverage는 이벤트 레이더의 첫 번째 중단점이다. 없는 source를 추정하지 않고, 어떤 판단을 못 하는지 먼저 고정한다."
lastUpdated: "2026-05-17"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
validatedAt: '2026-05-27'
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

def gather_rows(axis, limit=30):
    try:
        return rows(c.gather(axis), limit=limit)
    except Exception:
        try:
            return rows(dartlab.gather(axis, target=target), limit=limit)
        except Exception:
            return []

try:
    filings = rows(c.filings(), limit=50)
except Exception:
    filings = []

memo = buildEventRadarMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    filings=filings,
    newsRows=gather_rows("news", limit=20),
    priceRows=gather_rows("price", limit=40),
    flowRows=gather_rows("flow", limit=40),
    insiderRows=gather_rows("insiderTrading", limit=20),
    ownershipRows=gather_rows("ownership", limit=20),
    dividendRows=gather_rows("dividends", limit=20),
    splitRows=gather_rows("splits", limit=20),
    consensusRows=gather_rows("consensus", limit=12),
)

emit_result(
    table=memo["tables"]["sourceCoverageAudit"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

9 source coverage audit 단정. 예: "9 source audit — filings 50 rows latest 2026-05-26 / news 18 / price 40 / flow 40 / insiderTrading 0 (missing — KR 임원 신고 미수신) / ownership 12 / dividends 16 / splits 4 / consensus 12 → 8 of 9 ok + 1 missing (insiderOwnershipSignal 후속 제한 발생)."

### 2. 핵심 근거 수집

- Company.filings() filings (limit 50)
- Company.gather() × 8 axis (news / price / flow / insiderTrading / ownership / dividends / splits / consensus)
- 각 source rowCount + latestDate 추출
- buildEventRadarMemo() → sourceCoverageAudit table

### 3. 메커니즘 분석

```
9 source × (rowCount + latestDate + status + requiredFor)
   status 판정:
     rowCount ≥ 1 → ok
     rowCount = 0 → missing
     stale (latestDate > 30d) → watch
   ↓
requiredFor 매핑 (어떤 후속 recipe 가 필요로 하나):
   filings → eventInbox + capitalActionMonitor + falsifierLedger
   news    → eventInbox
   price   → priceFlowReaction + falsifierLedger + visualDecisionPack (priceChart)
   flow    → priceFlowReaction
   insider → insiderOwnershipSignal
   ownership → insiderOwnershipSignal
   dividends → capitalActionMonitor
   splits  → capitalActionMonitor
   consensus → consensusDriftWatch
   ↓
missing source 의 영향:
   priceRows 결손 → priceChart 비활성 + priceFlowReaction 결론 X
   filings 결손  → eventInbox 결론 X (whole pack 차단)
   insider 결손  → insiderOwnershipSignal 만 미산출 (전체 차단 X)
```

이벤트 레이더의 *첫 중단점* — 실행 전 게이트. missing source 가 어떤 후속 recipe 를 차단하는지 명시 필수.

### 4. 반례·한계

- 결손 source 를 0 또는 없음으로 단정 → forbidden 위반 (불확실로 표기).
- priceRows 결손인데 priceChart 만들면 false visualization.
- filings 결손인데 eventInbox 정상 처리 시 missing 누락.
- KR vs US source 비대칭 (insider 신고 형식 다름) — market 별 조정 필요.

### 5. 후속 모니터링

- 8+ source ok → `recipes.fundamental.disclosure.eventRadar.index` 로 전체 pack 진입.
- missing 다수 → `recipes.fundamental.disclosure.eventRadar.deepDive` 의 ledger 결손 처리 점검.
- stale (≥30일) → 데이터 sync recipe 또는 manual refresh trigger.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `dataset` | source 이름 |
| `status` | ok/missing |
| `rowCount` | row 수 |
| `latestDate` | 가장 최신 날짜 |
| `requiredFor` | 필요한 후속 판단 |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.index - 전체 팩 진입.
2. recipes.fundamental.disclosure.eventRadar.deepDive - 전체 ledger로 연결.

## 기본 검증

- sourceCoverageAudit가 비어 있으면 실패다.
- missing source를 답변 한계에 포함한다.
