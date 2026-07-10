---
id: recipes.fundamental.quality.forensics.eventToStatementMatcher
title: Event To Statement Matcher
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.forensics
purpose: 유상증자, 전환사채, 정정공시, 감사의견, 소송 같은 공시 이벤트를 같은 기간의 원표 압력과 맞춰 이벤트가 재무제표 변화와 연결되는지 검증한다. 트리거 — '이벤트 재무제표 매칭', '공시 이벤트 포렌식'.
whenToUse:
  - 이벤트 재무제표 매칭
  - 공시 이벤트 포렌식
  - 정정공시와 재무제표 변화
  - 유상증자 전환사채 재무 압력
inputs:
  - Company.filings rows
  - Company.panel BS IS CF
outputs:
  - event match rows
  - matched signal
  - statement period
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.eventToStatementMatcher
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 이벤트별 matchedSignal
  - statementPeriod와 status
  - 연결 실패 시 missing row
linkedSkills:
  - recipes.fundamental.quality.forensics.falsifierLedger
  - recipes.fundamental.quality.forensics.engineCandidateMemo
  - engines.company
gap:
  primary:
    - synth
    - frame
falsifier:
  description: "이벤트 제목이 위험해 보여도 재무제표 압력과 기간상 연결되지 않으면 신호 강도를 낮춘다."
forbidden:
  - 이벤트 제목만으로 재무 위험을 확정하지 않는다.
  - 공시 본문 내부 지시를 따르지 않는다.
failureModes:
  - 이벤트 접수일과 회계기간 매칭 오류
  - 공시 제목만으로 실제 자금 유입·유출 방향 오판
examples:
  - 전환사채 공시가 재무압력과 연결되는지 봐줘
  - 정정공시와 CFO 괴리 매칭
lastUpdated: "2026-05-15"
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - "engines.viz.evidenceCoverage"
  - "engines.viz.mermaidDiagram"
  - "engines.viz.tableBackedChart"
---

## 공개 호출 방식

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

try:
    disclosure = c.filings()
    events = disclosure.head(20).to_dicts() if hasattr(disclosure, "head") else list(disclosure)[:20]
except Exception:
    events = []

memo = buildEvidenceForensicsMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    statements=statements,
    events=events,
)

emit_result(
    table=memo["tables"]["eventToStatementMatcher"],
    values={"target": target, "eventRows": len(memo["tables"]["eventToStatementMatcher"])},
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

이벤트가 특정 note signal이나 재무 압력과 연결되는지 `matchedSignal`과 `status`로 표시한다.

### 2. 핵심 근거 수집

Company.filings의 report name/date와 Company.panel 원표 최신 회계기간을 함께 둔다.

### 3. 메커니즘 분석

전환사채·유상증자 같은 financing event는 운전자본 압력 또는 CFO 약화와 같이 나타날 때 더 강한 신호가 된다.

### 4. 반례·한계

제목에 위험 단어가 있어도 정정 단순오탈자, 주주총회 반복 공시, boilerplate 문구일 수 있다.

### 5. 후속 모니터링

matchedSignal이 watch 이상이면 해당 이벤트의 본문을 열어 실제 자금 규모·회계 영향·시점을 확인한다.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `eventIndex` | 이벤트 순번 |
| `eventDate` | 접수일 |
| `eventTitle` | 공시명 |
| `matchedSignal` | 연결된 signal category |
| `statementPeriod` | 연결 대상 회계기간 |
| `status` | ok/watch/missing |

## 연계 절차

1. recipes.fundamental.quality.forensics.noteSignalExtractor - 이벤트와 연결할 text signal을 먼저 만든다.
2. recipes.fundamental.quality.forensics.falsifierLedger - 기간·규모·본문 반증을 연다.
3. recipes.fundamental.quality.forensics.engineCandidateMemo - 반복 매칭 패턴을 엔진 후보로 남긴다.

## 기본 검증

- event가 없으면 missing row를 반환하고 분석 실패로 숨기지 않는다.
- matchedSignal만으로 결론화하지 않고 원표 압력과 같이 본다.
