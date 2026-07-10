---
id: recipes.fundamental.quality.forensics.deepDive
title: Evidence Forensics Deep Dive
category: recipes
kind: recipe
scope: builtin
status: curated
entryHint: true
graphTier: L1.5
cluster: incubator.forensics
purpose: L2 분석엔진 없이 data coverage, account trace, revenue-cash bridge, working capital, note/event signal, falsifier, engine candidate memo를 한 번에 실행하는 깊은 포렌식 팩 최종 절차다. 트리거 — '포렌식 deep dive', 'analysis 없이 깊게 검증'.
whenToUse:
  - 포렌식 deep dive
  - analysis 없이 깊게 검증
  - L1.5 회계 포렌식 전체 실행
  - 원표와 공시만으로 깊이 분석
inputs:
  - 기업 코드 또는 ticker
  - Company.panel 원표
  - section text
  - disclosure events
  - optional scan primitive rows
outputs:
  - deepDive step ledger
  - headline risk score
  - falsifier ledger
  - engine candidate memo
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
knowledgeRefs:
  - operation.skillDevelopmentLoop
  - runtime.workbenchEvidenceFlow
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.deepDive
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 10단계 deepDive ledger
  - riskScore와 signalCount
  - open falsifier 수
  - engine candidate 수
visualRefs:
  - engines.viz.financialStructureCharts
  - engines.viz.evidenceCoverage
  - engines.viz.mermaidDiagram
visualGuidance:
  - "IS/BS/CF 원표가 같은 기간·같은 연결 기준으로 확보되고 evidenceBinding을 만들 수 있을 때만 engines.viz.financialStructureCharts를 사용한다."
  - "deepDive ledger와 falsifier 상태는 표가 1차 산출물이다. coverage 시각화가 필요할 때만 observed engines.viz.evidenceCoverage로 낮게 보조한다."
  - "원표→bridge→falsifier→engine candidate 흐름은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고, 근거 없는 edge는 금지한다."
linkedSkills:
  - recipes.fundamental.quality.forensics.dataCoverageAudit
  - recipes.fundamental.quality.forensics.accountTraceLedger
  - recipes.fundamental.quality.forensics.revenueToCashBridge
  - recipes.fundamental.quality.forensics.workingCapitalPressureMap
  - recipes.fundamental.quality.forensics.noteSignalExtractor
  - recipes.fundamental.quality.forensics.eventToStatementMatcher
  - recipes.fundamental.quality.forensics.crossSectionAnomalyRank
  - recipes.fundamental.quality.forensics.falsifierLedger
  - recipes.fundamental.quality.forensics.engineCandidateMemo
gap:
  primary:
    - synth
    - scan
  secondary:
    - frame
    - reference
testUniverse:
  market: KR+US
  stockCodes:
    - "005930"
    - "247540"
    - "AAPL"
  asOfPolicy: latest
falsifier:
  description: "deepDive가 riskScore만 말하고 open falsifier와 source trace를 누락하면 실패로 본다."
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
  - riskScore를 투자 결론으로 해석하지 않는다.
  - open falsifier를 숨기지 않는다.
failureModes:
  - ask가 기존 analysis skill을 선택해 L2로 우회
  - RunPython 결과는 있는데 답변이 근거 표 없이 요약만 제시
  - engineCandidateMemo를 실제 구현 완료처럼 표현
examples:
  - 삼성전자 포렌식 deep dive
  - analysis 없이 원표와 공시만으로 깊게 검증
  - L1.5 회계 포렌식 전체 실행
audiences:
  llm: 이 스킬은 L2 금지 조건이 핵심이다. capabilityRefs는 EngineCall로 우선 호출하고, 공개 호출 블록은 L1.5 memo builder용 RunPython fallback으로만 실행한다.
  agent: ReadSkill 결과에서 이 스킬이 상위에 오면 Company.panel, disclosure, scan primitive를 EngineCall로 실행하고 L2 capability를 쓰지 않는다. helper 결합이 필요할 때만 RunPython fallback을 쓴다.
  human: 깊은 분석처럼 보이는 결론보다, 어떤 원표와 공시 증거가 어떤 엔진 후보를 만들었는지 확인하는 절차다.
humanIntro: "deepDive는 포렌식 팩의 실제 사용 경로다. 여러 세부 ledger를 하나로 묶되, 결론은 항상 반증 조건과 함께 남긴다. 나중에 일부 신호가 L2 엔진으로 승격돼도 이 스킬은 원표 검산 절차로 계속 사용된다."
lastUpdated: "2026-05-17"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선이다. `Company.panel("IS"|"BS"|"CF")`, `Company.filings`, `scan.quality`, `scan.audit`, `scan.disclosureRisk` 는 엔진 호출로 근거를 먼저 확보한다. 아래 Python 블록은 확보한 L1/L1.5 근거를 `buildEvidenceForensicsMemo` 로 묶는 **RunPython fallback** 절차다.

```python
import dartlab
from dartlab.synth.evidenceForensics import buildEvidenceForensicsMemo

target = "005930"
c = dartlab.Company(target)
statements = {}
for topic in ("IS", "BS", "CF"):
    try:
        statements[topic] = c.panel(topic, freq="Y")
    except TypeError:
        statements[topic] = c.panel(topic)
    except Exception:
        pass

sectionTexts = {}
for topic in ("businessOverview", "riskFactors", "mdna", "notesDetail"):
    try:
        sectionTexts[topic] = str(c.panel(topic))[:20000]
    except Exception:
        pass

try:
    disclosure = c.filings()
    events = disclosure.head(20).to_dicts() if hasattr(disclosure, "head") else list(disclosure)[:20]
except Exception:
    events = []

scanRows = []
for axis in ("quality", "audit", "disclosureRisk"):
    try:
        df = dartlab.scan(axis)
        rows = df.head(3).to_dicts() if hasattr(df, "head") else []
        for row in rows:
            row["axis"] = axis
        scanRows.extend(rows)
    except Exception:
        pass

memo = buildEvidenceForensicsMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    statements=statements,
    sectionTexts=sectionTexts,
    events=events,
    scanRows=scanRows,
)

emit_result(
    table=memo["tables"]["deepDive"],
    values={
        "target": target,
        "riskScore": memo["headline"]["riskScore"],
        "signalCount": memo["headline"]["signalCount"],
        "candidateCount": memo["headline"]["candidateCount"],
        "openFalsifiers": sum(1 for row in memo["tables"]["falsifierLedger"] if row["status"] == "open"),
    },
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

`riskScore`, `signalCount`, `candidateCount`, `openFalsifiers`를 한 번에 반환한다. 이 수치는 깊은 원표 검산의 현재 상태이지 투자 결론이 아니다.

### 2. 핵심 근거 수집

IS/BS/CF 원표, section text, disclosure events, scan primitive rows를 모으지만 L2/L3 엔진은 호출하지 않는다.
가능한 입력은 EngineCall 결과를 우선 사용하고, RunPython 은 memo builder 결합과 `emit_result(...)` 발급에만 사용한다.

### 3. 메커니즘 분석

원표 coverage와 trace가 먼저이고, 그 다음 매출-현금 괴리와 운전자본 압력을 본다. 공시 text와 event는 이 신호를 설명하거나 반증하는 보조층이다.

### 4. 반례·한계

open falsifier가 있으면 결론은 확정되지 않는다. 특히 신규 고객, 수주잔고, 계절성, M&A, 표준 감사 문구, 금융업 계정 구조는 주요 반례다.

### 5. 후속 모니터링

같은 신호가 여러 target selfRun과 ask 품질 점검에서 반복될 때만 engineCandidateMemo를 근거로 L2 엔진 환류를 제안한다.

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

1. recipes.fundamental.quality.forensics.dataCoverageAudit - 원표 coverage.
2. recipes.fundamental.quality.forensics.accountTraceLedger - 계정 trace.
3. recipes.fundamental.quality.forensics.revenueToCashBridge - 매출-현금 bridge.
4. recipes.fundamental.quality.forensics.workingCapitalPressureMap - 운전자본 pressure.
5. recipes.fundamental.quality.forensics.noteSignalExtractor - 공시 text signal.
6. recipes.fundamental.quality.forensics.eventToStatementMatcher - 이벤트 매칭.
7. recipes.fundamental.quality.forensics.crossSectionAnomalyRank - scan 후보.
8. recipes.fundamental.quality.forensics.falsifierLedger - 반증 ledger.
9. recipes.fundamental.quality.forensics.engineCandidateMemo - 엔진 후보 memo.

## 기본 검증

- 공개 호출 블록은 AST parse가 되어야 한다.
- 공개 호출 블록은 L2/L3 호출 문자열을 포함하면 실패다.
- EngineCall 가능한 Company/scan 입력을 RunPython 내부 계산으로 재구현하지 않는다.
- visualRefs 는 observed viz skill 만 포함해야 하며, 원표 기간·evidenceBinding 이 없으면 차트 대신 ledger 표로 답한다.
- selfRun 결과에 `deepDive`, `falsifierLedger`, `engineCandidateMemo`가 모두 있어야 한다.
- ask 답변은 riskScore만 말하지 않고 open falsifier와 candidate memo를 함께 설명해야 한다.
