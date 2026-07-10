---
id: recipes.meta.thesisKillChain.index
title: Thesis Kill-Chain Scenario 진입점
category: recipes
kind: recipe
scope: builtin
status: curated
entryHint: true
graphTier: L1.5
cluster: incubator.thesisKillChain
purpose: 사용자의 투자 thesis를 지지하는 대신 일부러 깨보는 pre-mortem 시나리오 스킬팩 진입점이다. Company.panel 원표, Company.filings, Company.gather, scan primitive만으로 가정, 취약 지표, 촉발 조건, 전파 경로, tripwire, 반증 조건을 만든다. 트리거 - 'thesis kill chain', '프리모템', '투자 논리 깨보기'.
whenToUse:
  - thesis kill chain
  - 프리모템
  - 투자 논리 깨보기
  - thesis 반증
  - break scenario
  - 시나리오 스토리보드
inputs:
  - 기업 코드 또는 ticker
  - 사용자 thesis 또는 명시 assumptions
  - Company.panel 원표 IS BS CF
  - Company.filings filing rows
  - Company.gather price flow consensus rows
  - optional scan primitive rows
outputs:
  - thesis intake
  - evidence coverage audit
  - assumption ledger
  - fragility map
  - trigger catalog
  - propagation path
  - tripwire monitor
  - falsifier ledger
  - scenario storyboard
  - visual decision pack
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
  - start.dartlabSkillOs
  - operation.architecture
  - operation.skillDevelopmentLoop
  - engines.company
  - engines.gather
  - engines.scan
  - engines.viz
sourceRefs:
  - dartlab://skills/recipes.meta.thesisKillChain.index
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - thesis를 깨는 kill-chain scenario ledger
  - assumption별 취약 지표와 tripwire
  - open falsifier와 counter-evidence
  - premortemQualityGate와 qualityGateStatus
  - observed viz surface 선택
visualRefs:
  - engines.viz.scenarioVisuals
  - engines.viz.mermaidDiagram
  - engines.viz.evidenceCoverage
  - engines.viz.kpiRibbon
visualGuidance:
  - "scenarioStoryboard table이 있을 때만 engines.viz.scenarioVisuals chart를 사용한다."
  - "propagationPath는 engines.viz.mermaidDiagram으로 8 edge 이하 diagram만 만든다."
  - "evidenceCoverageAudit와 falsifierLedger는 engines.viz.evidenceCoverage 표 시각화로만 보조한다."
  - "headline의 killRiskScore/openTripwireCount는 engines.viz.kpiRibbon으로 작게 표시한다."
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
  - recipes.meta.thesisKillChain.deepDive
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
  description: "thesis를 지지하는 증거만 제시하고 깨지는 경로, tripwire, open falsifier를 누락하면 실패로 본다."
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
      - 브라우저 snapshot 범위에서는 filings, price, flow, consensus row가 제한될 수 있다.
forbidden:
  - c.analysis, c.credit, c.quant, c.macro, c.industry, c.story를 호출하지 않는다.
  - thesis를 지지하는 결론부터 쓰지 않는다.
  - open tripwire가 있는데 확정 표현을 쓰지 않는다.
  - premortemQualityGate가 weak인데 thesis 결론을 쓰지 않는다.
  - observed 상태가 아닌 viz skill을 visualRefs에 연결하지 않는다.
failureModes:
  - thesis를 testable assumption으로 쪼개지 않음
  - 취약 지표 없이 시나리오 문장만 생성
  - counter-evidence 없는 kill scenario 단정
  - blocked visualRef를 emit
examples:
  - 삼성전자 투자 thesis를 kill chain으로 깨봐
  - 이 성장 스토리가 무너지는 시나리오 작성
  - thesis 프리모템과 tripwire 만들어줘
audiences:
  llm: 이 팩은 지지 논리를 만드는 팩이 아니다. L1/L1.5 근거를 EngineCall로 먼저 확보하고 RunPython fallback으로 kill-chain memo를 만든다.
  agent: 답변에는 assumption, propagationPath, tripwireMonitor, falsifierLedger를 함께 포함한다. L2 결론으로 승격하지 않는다.
  human: 투자 thesis를 방어하기 전에 어떤 조건에서 깨지는지 보는 pre-mortem 시나리오 팩이다.
humanIntro: "Thesis Kill-Chain은 완전히 다른 관점의 시나리오 팩이다. 좋은 점을 더 찾는 대신, 내가 믿는 thesis가 어떤 작은 균열에서 시작해 어떤 경로로 무너지는지 구조화한다."
lastUpdated: "2026-05-17"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel`, `Company.filings`, `Company.gather`, `scan.market`, `scan.audit`, `scan.quality`는 엔진 surface로 호출한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildThesisKillChainMemo`로 묶는 **RunPython fallback** 절차다.

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
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

`killRiskScore`, `assumptionCount`, `openTripwireCount`, `openFalsifierCount`, `decisionStatus`를 반환한다. 이 값은 thesis를 확정하는 점수가 아니라, 깨지는 경로가 얼마나 열려 있는지 보는 우선순위다.

### 2. 핵심 근거 수집

근거는 사용자 thesis, 명시 assumption, IS/BS/CF 원표, filings, price/flow/consensus, optional scan primitive에서만 나온다. 답변에는 target, date, tableRef, valueRef, sourceRef, executionRef가 있어야 한다.

### 3. 메커니즘 분석

```mermaid
graph LR
  A["user thesis"] --> B["assumption ledger"]
  C["Company.panel IS/BS/CF"] --> D["fragility map"]
  E["filings/gather/scan"] --> F["trigger catalog"]
  B --> G["propagation path"]
  D --> G
  F --> G
  G --> H["tripwire monitor"]
  H --> I["falsifier ledger"]
  I --> J["scenario storyboard"]
```

### 4. 반례·한계

kill-chain은 반증 시나리오다. 반증 조건이 닫히면 thesis는 유지될 수 있다. 계절성, 일회성 현금흐름, 시장 전체 움직임, stale consensus, 정기 공시는 반드시 counter-evidence로 남긴다.

### 5. 후속 모니터링

tripwire가 watch/risk로 바뀌면 같은 helper를 다시 실행한다. 사용자는 “thesis가 맞나?”보다 “어떤 tripwire가 먼저 깨졌나?”를 확인한다.

## 대표 반환 형태

`memo : dict`

| key | 의미 |
|---|---|
| `headline` | killRiskScore, premortemQualityScore, qualityGateStatus, openTripwireCount, openFalsifierCount |
| `tables.thesisIntake` | 사용자 thesis와 파싱된 theme |
| `tables.assumptionLedger` | testable assumption |
| `tables.fragilityMap` | 원자료 취약 지표 |
| `tables.triggerCatalog` | thesis를 흔드는 촉발 조건 |
| `tables.propagationPath` | trigger → mechanism → assumption |
| `tables.tripwireMonitor` | 임계값과 현재 상태 |
| `tables.falsifierLedger` | 반증 조건 |
| `tables.scenarioStoryboard` | base/erosion/kill-chain 시나리오 |
| `tables.premortemQualityGate` | 최종 답변 차단 gate |

## 타협 없는 사용 기준

- `qualityGateStatus == "flagshipReady"`가 아니면 thesis를 방어하는 결론으로 가지 않는다.
- `premortemQualityGate`의 risk row는 최종 답변 앞부분에 그대로 드러낸다.
- sourceBreadth, propagationConnected, falsifierOpen 중 하나라도 risk면 다음 EngineCall/RunPython 보강 절차가 답변의 결론이다.
- 시각화는 `visualDecisionPack`이 ready인 observed viz만 사용한다.

## 연계 절차

1. recipes.meta.thesisKillChain.thesisIntake - thesis를 입력하고 theme을 파싱.
2. recipes.meta.thesisKillChain.evidenceCoverageAudit - 원자료 coverage 확인.
3. recipes.meta.thesisKillChain.assumptionLedger - 가정을 testable row로 분해.
4. recipes.meta.thesisKillChain.fragilityMap - 원표·시장·기대 취약성 계산.
5. recipes.meta.thesisKillChain.triggerCatalog - 촉발 조건 정리.
6. recipes.meta.thesisKillChain.propagationPath - 깨지는 전파 경로 구성.
7. recipes.meta.thesisKillChain.tripwireMonitor - 임계와 current 상태 확인.
8. recipes.meta.thesisKillChain.falsifierLedger - counter-evidence 열기.
9. recipes.meta.thesisKillChain.scenarioStoryboard - pre-mortem 시나리오 작성.
10. recipes.meta.thesisKillChain.visualDecisionPack - observed viz 선택.
11. recipes.meta.thesisKillChain.premortemQualityGate - 약한 결론 차단.
12. recipes.meta.thesisKillChain.deepDive - 전체 실행.

## 기본 검증

- 공개 호출 블록에 L2/L3 호출 문자열이 없어야 한다.
- `buildThesisKillChainMemo` 결과에는 12개 table이 모두 있어야 한다.
- scenarioStoryboard는 baseIntact, erosionCase, killChainCase를 모두 포함해야 한다.
- premortemQualityGate가 weak이면 `decisionStatus`는 usable이면 안 된다.
- 답변은 propagationPath와 falsifierLedger 없이 thesis 결론을 쓰면 실패다.
