---
id: recipes.fundamental.disclosure.eventRadar.capitalActionMonitor
title: Event Radar Capital Action Monitor
category: recipes
kind: recipe
scope: builtin
status: curated
graphTier: L1.5
cluster: incubator.eventRadar
purpose: dividends, splits, 자사주, 증자, 전환사채 등 자본 이벤트 원자료를 묶어 단기 촉매를 확인하는 L1/L1.5 절차다. 트리거 — 'Event Radar Capital Action Monitor', 'capital action monitor', 'capitalActionMonitor'.
whenToUse:
  - capital action monitor
  - 배당 자사주 분할 증자
  - 전환사채 이벤트
inputs:
  - dividend rows
  - split rows
  - filing event rows
outputs:
  - capitalActionMonitor table
capabilityRefs:
  - Company.filings
  - Company.gather
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - engines.company
  - engines.gather
  - engines.scan
sourceRefs:
  - dartlab://skills/recipes.fundamental.disclosure.eventRadar.capitalActionMonitor
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - dividend/split/filing capital action rows
visualRefs:
  - engines.viz.kpiRibbon
  - engines.viz.evidenceCoverage
visualGuidance:
  - "capital action count는 engines.viz.kpiRibbon chart의 보조 숫자로만 표시하고 원표는 table/표로 보존한다."
linkedSkills:
  - recipes.fundamental.disclosure.eventRadar.eventInbox
  - recipes.fundamental.disclosure.eventRadar.falsifierLedger
  - engines.company
gap:
  primary:
    - gather
    - synth
falsifier:
  description: "정기 배당, 기계적 분할, 희석 이벤트 여부를 분리하지 않으면 실패로 본다."
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
  - 배당·분할을 항상 호재로 단정하지 않는다.
failureModes:
  - 유상증자와 무상증자 영향을 섞음
examples:
  - 배당 자사주 분할 증자 이벤트 확인
audiences:
  llm: capital 관련 원자료는 EngineCall로 받고 helper fallback으로 action table을 만든다.
  agent: action과 value를 source/date에 묶어 표시한다.
  human: 자본 이벤트가 실제 촉매인지 따로 확인한다.
humanIntro: "capitalActionMonitor는 배당·분할·증자 같은 표면상 큰 이벤트를 모으되, 반복 배당과 희석 이벤트를 분리해 과잉 해석을 막는다."
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

def rows(value, limit=20):
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
    dividend_rows = rows(c.gather("dividends"), limit=20)
except Exception:
    dividend_rows = []

try:
    split_rows = rows(c.gather("splits"), limit=20)
except Exception:
    split_rows = []

memo = buildEventRadarMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    filings=filings,
    dividendRows=dividend_rows,
    splitRows=split_rows,
)

emit_result(
    table=memo["tables"]["capitalActionMonitor"],
    values=memo["headline"],
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

dividend / split / capitalAction action table 단정. 예: "최근 12개월 capital action 8건 — 정기배당 4 (분기 5,500원) + 무상증자 1 + 자사주 매입 2 (총 1.2조) + 전환사채 1 (희석 +2.3%) → action mix 정기 + buyback 우세 (희석 1건 한정)."

### 2. 핵심 근거 수집

- Company.filings() filings — capitalAction category (배당결정·무상증자·유상증자·CB·자사주취득/소각)
- Company.gather('dividends') — 배당 시계열
- Company.gather('splits') — 분할 시계열
- buildEventRadarMemo() → action table 통합

### 3. 메커니즘 분석

```
3 source → action category 통합
   dividend rows → action="dividend" value=배당금
   split rows    → action="split"    value=비율
   filings       → action="filingCapitalAction" value=공시 제목
   ↓
12M action mix:
   buyback > issuance → 주주환원 우세
   issuance > buyback → 희석 우세 (유상증자 + CB)
   dividend 정기성 일관 → 안정 배당정책
   특별배당 / 자사주 소각 → 일회성 호재
   ↓
status="watch": 향후 12M 예상 action (인지 가능)
status="missing": disclosure 부재 row
```

action 자체는 호재/악재 판정 X — 정기성 분리 + 희석 vs 환원 비교가 핵심. CB/유상증자 = 희석. 자사주 매입/소각 + 배당 = 환원.

### 4. 반례·한계

- 유상증자와 무상증자 자본 영향 다름 (희석 vs 단순 분할).
- 자사주 *매입* vs *소각* 구분 — 매입은 자본 감소, 소각은 EPS 즉시 상승.
- CB 발행은 즉시 희석 아님 — 전환 시점에 발현 (5-10% 가정).
- 분기 정기배당 변동은 *변화* 만 신호 — 같은 금액 4회 반복은 baseline.

### 5. 후속 모니터링

- buyback 큰 규모 → `recipes.fundamental.dividend.buybackVsDividendMix` 로 환원 mix 변화 확인.
- CB/유상증자 → `recipes.fundamental.governance.relatedPartyTransactionShare` 로 거버넌스 risk.
- 정기배당 변동 → `recipes.fundamental.dividend.payoutFcfCoverage` 로 fcf 충당 점검.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `date` | 기준일 |
| `action` | dividend/split/filingCapitalAction |
| `value` | 배당금, 분할비율, filing title |
| `status` | watch/missing |
| `evidence` | 원자료 출처 |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.eventInbox - 자본 이벤트 공시 분류.
2. recipes.fundamental.disclosure.eventRadar.falsifierLedger - 정기성·희석 반증.

## 기본 검증

- 자본 이벤트는 호재·악재 결론이 아니라 action row로 둔다.
- value가 없으면 제목과 sourceRef를 근거로 둔다.
