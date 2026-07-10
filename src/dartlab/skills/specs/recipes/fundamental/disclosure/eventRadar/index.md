---
id: recipes.fundamental.disclosure.eventRadar.index
title: Event Radar Incubator 진입점
category: recipes
kind: recipe
scope: builtin
status: curated
entryHint: true
graphTier: L1.5
cluster: incubator.eventRadar
purpose: Company.filings, liveFilings, gather 원자료, scan primitive, observed viz skill만으로 단기 이벤트와 시장 반응을 묶어 촉매 후보를 찾는 L1/L1.5 스킬팩 진입점이다. 트리거 - '이벤트 레이더', '촉매 체크', '공시와 주가 반응'.
whenToUse:
  - 이벤트 레이더
  - 촉매 체크
  - 공시와 주가 반응
  - 단기 이벤트 모니터
  - 원자료 기반 catalyst
  - insider ownership signal
  - consensus drift watch
inputs:
  - 기업 코드 또는 ticker
  - Company.filings 또는 Company.filings row
  - Company.gather price flow news dividends splits consensus row
  - optional scan primitive row
outputs:
  - source coverage audit
  - event inbox
  - price flow reaction
  - insider ownership signal
  - capital action monitor
  - consensus drift watch
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
  - start.dartlabSkillOs
  - operation.architecture
  - operation.skillDevelopmentLoop
  - engines.company
  - engines.gather
  - engines.scan
  - engines.viz
sourceRefs:
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.index
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - L2 금지 조건을 통과한 event radar ledger
  - event별 supporting evidence와 counter evidence
  - observed viz surface 선택표
  - 엔진 환류 후보와 recipe 보존 계약
visualRefs:
  - engines.viz.priceChart
  - engines.viz.kpiRibbon
  - engines.viz.evidenceCoverage
  - engines.viz.mermaidDiagram
visualGuidance:
  - "가격 원자료가 있을 때만 engines.viz.priceChart를 사용하고, priceRows의 date/close/volume을 evidenceBinding으로 묶는다."
  - "headline의 radarScore, eventCount, openFalsifierCount는 engines.viz.kpiRibbon으로만 보조 표시한다."
  - "sourceCoverageAudit와 falsifierLedger는 engines.viz.evidenceCoverage로 표시할 수 있지만 표가 1차 산출물이다."
  - "공시-반응-반증 흐름은 engines.viz.mermaidDiagram으로 8노드 이하만 만든다."
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
  - recipes.fundamental.disclosure.eventRadar.deepDive
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
  description: "공시·뉴스·가격 반응을 반증 ledger 없이 투자 결론으로 승격하면 실패로 본다."
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
    limitations:
      - 브라우저 snapshot 범위에서는 live filing, price, flow, consensus row가 제한될 수 있다.
forbidden:
  - c.analysis, c.credit, c.quant, c.macro, c.industry, c.story를 호출하지 않는다.
  - 이벤트를 투자 결론으로 바로 단정하지 않는다.
  - observed 상태가 아닌 viz skill을 visualRefs에 연결하지 않는다.
  - RunPython에서 엔진이 이미 제공하는 수집 기능을 재구현하지 않는다.
failureModes:
  - 정기 공시를 새로운 촉매로 오해
  - 시장 전체 급락을 개별 이벤트 반응으로 단정
  - 내부자 거래의 계획 매도나 데이터 지연을 반증하지 않음
  - 가격 차트에 tableRef/evidenceBinding을 붙이지 않음
examples:
  - 삼성전자 이벤트 레이더로 촉매 체크
  - 공시와 주가 반응만으로 단기 이벤트 봐줘
  - analysis 없이 catalyst candidate 정리
audiences:
  llm: Company.filings/liveFilings/gather와 scan primitive는 EngineCall로 먼저 호출하고, buildEventRadarMemo는 RunPython fallback으로만 실행한다.
  agent: ReadSkill 후 capabilityRefs를 엔진 호출로 확보한다. helper 결과에는 tableRef/valueRef/dateRef/sourceRef를 붙이고 L2 결론으로 승격하지 않는다.
  human: 새 분석 엔진을 만들기 전, 원자료 이벤트와 시장 반응이 반복 가능한지 확인하는 촉매 인큐베이터다.
humanIntro: "이 팩은 복잡한 엔진 호출법을 여러 스킬로 쪼개는 대신, 이미 있는 L1/L1.5 표면을 조합해 촉매 후보와 반증 조건을 빠르게 남긴다. 유효한 축은 나중에 엔진으로 환류하되 recipe는 원자료 검산 경로로 유지한다."
lastUpdated: "2026-05-17"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.filings`, `Company.filings`, `Company.gather`, `scan.market`, `scan.insider`, `scan.capital`은 엔진 surface로 호출한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEventRadarMemo`로 묶는 **RunPython fallback** 절차다.

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
except TypeError:
    filings = rows(c.filings(), limit=50)
except Exception:
    filings = []

try:
    live_filings = rows(c.filings(), limit=20)
except Exception:
    live_filings = []

memo = buildEventRadarMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    filings=[*live_filings, *filings],
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
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

`radarScore`, `eventCount`, `openFalsifierCount`, `decisionStatus`를 뽑는다. 점수는 이벤트 강도와 반응의 우선순위이지 매수·매도 결론이 아니다.

### 2. 핵심 근거 수집

근거는 filing/news/price/flow/insider/ownership/dividend/split/consensus/scan primitive row에서만 나온다. 답변에는 target, date, sourceRef, tableRef, valueRef, executionRef가 있어야 한다.

### 3. 메커니즘 분석

```mermaid
graph LR
  A["filing/news"] --> B["event inbox"]
  C["price/flow"] --> D["reaction ledger"]
  E["insider/ownership"] --> F["holder signal"]
  G["dividend/split"] --> H["capital action"]
  I["consensus"] --> J["drift watch"]
  B --> K["falsifier ledger"]
  D --> K
  F --> K
  H --> K
  J --> K
  K --> L["engine candidate memo"]
```

### 4. 반례·한계

정기 공시, 중복 기사, 시장 전체 변동, stale consensus, 계획 매도, 기계적 배당·분할은 반드시 falsifier로 남긴다.

### 5. 후속 모니터링

3개 이상 target selfRun에서 반복되고, falsifier가 닫히며, observed viz binding이 안정되면 engineCandidateMemo에 승격 후보로 남긴다.

## 대표 반환 형태

`memo : dict`

| key | 의미 |
|---|---|
| `headline` | target, radarScore, eventCount, openFalsifierCount, decisionStatus |
| `tables.sourceCoverageAudit` | 입력 source별 row coverage |
| `tables.eventInbox` | 공시·뉴스 이벤트 분류 |
| `tables.priceFlowReaction` | 가격·거래량·수급 반응 |
| `tables.insiderOwnershipSignal` | 내부자·주요주주 변화 |
| `tables.capitalActionMonitor` | 배당·분할·자사주·증자 이벤트 |
| `tables.consensusDriftWatch` | 컨센서스 변화 |
| `tables.falsifierLedger` | 반증 조건 |
| `tables.engineCandidateMemo` | 엔진 환류 후보 |
| `tables.visualDecisionPack` | observed viz 선택 |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.sourceCoverageAudit - 원자료 coverage 확인.
2. recipes.fundamental.disclosure.eventRadar.eventInbox - 공시·뉴스 이벤트 분류.
3. recipes.fundamental.disclosure.eventRadar.priceFlowReaction - 가격·거래량·수급 반응.
4. recipes.fundamental.disclosure.eventRadar.insiderOwnershipSignal - 내부자·주요주주 변화.
5. recipes.fundamental.disclosure.eventRadar.capitalActionMonitor - 배당·분할·자사주·증자 이벤트.
6. recipes.fundamental.disclosure.eventRadar.consensusDriftWatch - 컨센서스 변화.
7. recipes.fundamental.disclosure.eventRadar.falsifierLedger - 반증 ledger.
8. recipes.fundamental.disclosure.eventRadar.engineCandidateMemo - 엔진 환류 후보.
9. recipes.fundamental.disclosure.eventRadar.visualDecisionPack - observed viz 선택.
10. recipes.fundamental.disclosure.eventRadar.deepDive - 전체 실행.

## 기본 검증

- 공개 호출 블록에 L2/L3 호출 문자열이 없어야 한다.
- RunPython은 `buildEventRadarMemo` 결합과 `emit_result(...)` 발급에만 쓴다.
- visualRefs는 observed 상태의 viz skill만 포함한다.
- `deepDive`, `falsifierLedger`, `engineCandidateMemo`, `visualDecisionPack`이 모두 있어야 한다.
