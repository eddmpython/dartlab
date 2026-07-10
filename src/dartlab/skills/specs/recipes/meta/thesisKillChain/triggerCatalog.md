---
id: recipes.meta.thesisKillChain.triggerCatalog
title: Thesis Kill-Chain Trigger Catalog
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.thesisKillChain
purpose: fragilityMap, filings, scan primitive에서 thesis를 흔드는 촉발 조건을 모으는 L1/L1.5 절차다. 트리거 — 'Thesis Kill-Chain Trigger Catalog', 'trigger catalog', 'triggerCatalog'.
whenToUse:
  - trigger catalog
  - thesis 촉발 조건
  - break trigger
inputs:
  - fragilityMap rows
  - filing rows
  - scan primitive rows
outputs:
  - triggerCatalog table
capabilityRefs:
  - Company.filings
  - scan.market
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.company
  - engines.scan
sourceRefs:
  - dartlab://skills/recipes.meta.thesisKillChain.triggerCatalog
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - triggerId trigger source status evidence
visualRefs:
  - engines.viz.evidenceCoverage
visualGuidance:
  - "triggerCatalog는 table/표가 1차 산출물이며 evidenceCoverage로 source 상태만 보조한다."
linkedSkills:
  - recipes.meta.thesisKillChain.fragilityMap
  - recipes.meta.thesisKillChain.propagationPath
  - engines.company
gap:
  primary:
    - synth
    - scan
falsifier:
  description: "trigger 없이 propagationPath를 만들면 실패로 본다."
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
  - 공시 제목만으로 thesis 파괴를 확정하지 않는다.
failureModes:
  - 정기 공시를 risk trigger로 오인
examples:
  - thesis를 흔드는 trigger catalog
audiences:
  llm: trigger는 시나리오의 시작점이지 결론이 아니다.
  agent: triggerId를 propagationPath와 falsifierLedger에 연결한다.
  human: 어떤 사건이나 지표가 thesis 붕괴를 시작할 수 있는지 본다.
humanIntro: "triggerCatalog는 균열의 시작점을 모은다. 하나의 trigger가 바로 결론이 되지는 않는다."
lastUpdated: "2026-05-17"
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildThesisKillChainMemo`로 묶는 **RunPython fallback** 절차다.

```python
import dartlab
from dartlab.synth.thesisKillChain import buildThesisKillChainMemo

target = "005930"
thesis = "매출 성장과 현금 전환이 유지되어 valuation discount가 해소된다"
c = dartlab.Company(target)
try:
    filings = c.filings().head(50).to_dicts()
except Exception:
    filings = []

memo = buildThesisKillChainMemo(target=target, thesis=thesis, filings=filings)

emit_result(
    table=memo["tables"]["triggerCatalog"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

triggerId × source 별 trigger catalog 단정. 예: "catalog 8 row — T1=opmCompression source=fragilityMap status=risk evidence='OPM -2%p 5y trend' / T2=consensusDownRevision source=fragilityMap status=risk / T3=marginCompressionFiling source=filing status=watch evidence='3Q 컨퍼런스콜 비용 가속' / T4=peerStress source=scan status=watch / T5-T8 routine missing → 3 risk trigger + 2 watch + 3 routine. 진성 trigger 5 종 (filing routine 제외)."

### 2. 핵심 근거 수집

- fragilityMap watch/risk metric → triggerId 변환
- Company.filings() filings risk keyword (구조조정 / 감액 / 정정신고 등)
- scan primitive score (peer 동조 / 시장 stress)
- buildThesisKillChainMemo() → triggerCatalog table

### 3. 메커니즘 분석

```
3 source → trigger row 변환
   fragilityMap risk/watch metric → triggerId = metricId
     status 그대로 보존
     evidence = metric 값 + thesisBreak
   filing risk keyword 매칭:
     "감액 / 정정 / 구조조정 / 감리"  → status=risk
     "신규계약 / 자사주" 일부 호재    → status=watch
     "분기보고서 / 정기" → routine 제외
   scan primitive:
     peer 동조 stress 신호  → status=watch
     market-wide vol expand → status=watch
   ↓
trigger 의 의미:
   *시나리오 시작점* — propagationPath 의 root 노드
   1 trigger = 결론 아님 (assumption ledger 와 결합 필요)
   ↓
filing trigger 처리:
   routine (정기보고서 / 8.01) → catalog 제외
   비정기 (5.02 / 1.01 / 8.01 중 risk) → catalog 포함
```

trigger 는 *균열의 시작점* — 결론 아님. 공시 제목만으로 thesis 파괴 확정 X (forbidden). routine filing 을 risk trigger 로 오인 시 false positive (failureMode 발동).

### 4. 반례·한계

- 공시 제목만으로 thesis 파괴 확정 → forbidden.
- 정기 공시를 risk trigger 로 오인 (예: 분기보고서를 catalog 에 포함) → false positive.
- scan primitive score 임계가 산업/시장별 다름 — 일관 적용 어려움.
- triggerId 없는 row → 실패.

### 5. 후속 모니터링

- risk ≥ 3 → `recipes.meta.thesisKillChain.propagationPath` 로 assumption 에 연결.
- filing trigger → `recipes.meta.thesisKillChain.falsifierLedger` 로 counter-evidence 작성.
- scan trigger → `recipes.industry.sectorMomentumLeadership` 으로 peer 동조성 확인.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `triggerId` | 촉발 조건 id |
| `trigger` | 지표 또는 공시 제목 |
| `source` | fragilityMap/filing/scan |
| `status` | watch/risk/missing |
| `evidence` | trigger 근거 |

## 연계 절차

1. recipes.meta.thesisKillChain.propagationPath - trigger를 assumption에 연결.
2. recipes.meta.thesisKillChain.falsifierLedger - counter-evidence 작성.

## 기본 검증

- triggerId가 없으면 실패다.
- filing trigger는 routine filing 반증을 남긴다.
