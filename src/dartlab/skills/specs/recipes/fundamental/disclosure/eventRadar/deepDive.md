---
id: recipes.fundamental.disclosure.eventRadar.deepDive
title: Event Radar Deep Dive
category: recipes
kind: recipe
scope: builtin
status: curated
entryHint: true
graphTier: L1.5
cluster: incubator.eventRadar
purpose: source coverage, event inbox, price/flow reaction, insider/ownership, capital action, consensus drift, falsifier, engine candidate, visual gate를 한 번에 실행하는 이벤트 레이더 최종 절차다. 트리거 — 'Event Radar Deep Dive', 'deep dive', 'deepDive'.
whenToUse:
  - 이벤트 레이더 deep dive
  - 촉매 후보 전체 실행
  - 공시 주가 수급 컨센서스 종합
inputs:
  - filing/news/price/flow/insider/ownership/dividend/split/consensus rows
outputs:
  - deepDive step ledger
  - headline radar score
  - falsifier ledger
  - engine candidate memo
  - visual decision pack
capabilityRefs:
  - Company.filings
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
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.deepDive
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 11단계 deepDive ledger
  - radarScore와 eventCount
  - open falsifier 수
  - ready visualRef 수
visualRefs:
  - engines.viz.priceChart
  - engines.viz.kpiRibbon
  - engines.viz.evidenceCoverage
  - engines.viz.mermaidDiagram
visualGuidance:
  - "priceFlowReaction에 priceRows binding이 있을 때만 engines.viz.priceChart를 사용한다."
  - "headline metric은 engines.viz.kpiRibbon으로만 작게 보조한다."
  - "coverage/falsifier 상태는 engines.viz.evidenceCoverage로 보조 가능하지만 표가 우선이다."
  - "공시→반응→반증→엔진후보 흐름은 engines.viz.mermaidDiagram 8노드 이하로만 만든다."
linkedSkills:
  - recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit
  - recipes.fundamental.disclosure.eventRadar.eventInbox
  - recipes.fundamental.disclosure.eventRadar.priceFlowReaction
  - recipes.fundamental.disclosure.eventRadar.insiderOwnershipSignal
  - recipes.fundamental.disclosure.eventRadar.capitalActionMonitor
  - recipes.fundamental.disclosure.eventRadar.consensusDriftWatch
  - recipes.fundamental.disclosure.eventRadar.falsifierLedger
  - recipes.fundamental.disclosure.eventRadar.engineCandidateMemo
  - recipes.fundamental.disclosure.eventRadar.visualDecisionPack
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
  description: "deepDive가 radarScore만 말하고 open falsifier와 visual gate를 누락하면 실패로 본다."
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
  - radarScore를 투자 결론으로 해석하지 않는다.
  - blocked visualRef를 emit하지 않는다.
failureModes:
  - ask가 기존 분석 엔진으로 우회
  - RunPython 결과는 있는데 답변이 근거 표 없이 요약만 제시
  - visualDecisionPack 없이 차트 생성
examples:
  - 삼성전자 이벤트 레이더 deep dive
  - analysis 없이 촉매 후보 전체 실행
audiences:
  llm: capabilityRefs는 EngineCall로 우선 호출하고 공개 호출 블록은 L1.5 memo builder용 RunPython fallback으로만 실행한다.
  agent: ReadSkill 결과에서 이 스킬이 상위에 오면 Company/gather/scan primitive를 EngineCall로 실행하고 L2 capability를 쓰지 않는다.
  human: 이벤트 후보, 반응, 반증, 시각화 가능 여부를 한 번에 보는 실제 사용 경로다.
humanIntro: "deepDive는 이벤트 레이더 팩의 실제 사용 경로다. 신호를 만들기보다 원자료와 반증 조건, 시각화 가능 여부를 함께 묶는다."
lastUpdated: "2026-05-17"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.filings`, `Company.filings`, `Company.gather`, `scan.market`, `scan.insider`, `scan.capital`은 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEventRadarMemo`로 묶는 **RunPython fallback** 절차다.

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
    filings = rows(c.filings(), limit=20)
except Exception:
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
    table=memo["tables"]["deepDive"],
    values={
        "target": target,
        "radarScore": memo["headline"]["radarScore"],
        "eventCount": memo["headline"]["eventCount"],
        "openFalsifiers": memo["headline"]["openFalsifierCount"],
        "decisionStatus": memo["headline"]["decisionStatus"],
    },
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

eventRadar `finalDecision` row 의 `radarScore` + `decisionStatus` 단정. 예: "radarScore=72/100, decision=actionable — 촉매 후보 N 건 확정, 시장 반응 검증 후 매수 후보 K 건."

### 2. 핵심 근거 수집

- IS/BS/CF 시계열 (Company.panel)
- 공시 row 50 건 (Company.filings)
- 가격·수급·컨센서스 row (Company.gather price/flow/consensus)
- L1.5 ledger 7 단계 (sourceCoverageAudit → eventInbox → priceFlowReaction → consensusReactionAudit → catalystThesisBridge → premortemCheck → visualDecisionPack)

### 3. 메커니즘 분석

```
공시 + 뉴스 + 가격 + 수급 + 컨센서스 5 layer 입력
   ↓
sourceCoverageAudit (각 layer 데이터 신뢰도 점검)
   ↓
eventInbox (잠재 촉매 row 분류)
   ↓
priceFlowReaction (촉매 시점 ±5일 가격·수급 반응)
   ↓
consensusReactionAudit (컨센서스 revision 동행 여부)
   ↓
catalystThesisBridge (반응 + 컨센서스 동행 → 촉매 후보 확정)
   ↓
premortemCheck (반증 검증)
   ↓
visualDecisionPack + finalDecision: radarScore + decisionStatus
```

각 ledger 의 missing/ok/watch/risk status 가 누적돼 radarScore 산출. 5 layer 모두 ok 면 decisionStatus=actionable.

### 4. 반례·한계

- 가격·수급·컨센서스 5 layer 중 2+ layer missing 시 catalystThesisBridge 신뢰도 ↓.
- 단일 이벤트만 보고 시장 반응 단정 금지 — peer 동행 여부 별도 확인.
- thesis 가 너무 일반적이면 catalystThesisBridge 가 weak narrative 만 생성 — premortemCheck risk row 발생.
- decisionStatus=operatorReview 시 보강 EngineCall 목록 답안 우선.

### 5. 후속 모니터링

- radarScore ≥ 70 & actionable: `recipes.fundamental.disclosure.eventRadar.eventInbox` 의 confirmed 후보 매주 추적.
- watchStatus row 1+ 건: 다음 turn `recipes.fundamental.disclosure.eventRadar.priceFlowReaction` 재측정.
- premortemCheck risk row: `recipes.meta.thesisKillChain.deepDive` 로 thesis 전반 재검토.

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

1. recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit - source coverage.
2. recipes.fundamental.disclosure.eventRadar.eventInbox - event inbox.
3. recipes.fundamental.disclosure.eventRadar.priceFlowReaction - price/flow reaction.
4. recipes.fundamental.disclosure.eventRadar.insiderOwnershipSignal - insider/ownership.
5. recipes.fundamental.disclosure.eventRadar.capitalActionMonitor - capital action.
6. recipes.fundamental.disclosure.eventRadar.consensusDriftWatch - consensus drift.
7. recipes.fundamental.disclosure.eventRadar.falsifierLedger - falsifier.
8. recipes.fundamental.disclosure.eventRadar.engineCandidateMemo - engine candidate.
9. recipes.fundamental.disclosure.eventRadar.visualDecisionPack - visual gate.

## 기본 검증

- 공개 호출 블록은 AST parse가 되어야 한다.
- 공개 호출 블록은 L2/L3 호출 문자열을 포함하면 실패다.
- `deepDive`, `falsifierLedger`, `engineCandidateMemo`, `visualDecisionPack`이 모두 있어야 한다.
- ready가 아닌 visualRef는 차트로 emit하지 않는다.
