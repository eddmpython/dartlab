---
id: recipes.fundamental.quality.forensics.falsifierLedger
title: Forensics Falsifier Ledger
category: recipes
kind: recipe
scope: builtin
status: tested
graphTier: L1.5
cluster: incubator.forensics
purpose: revenue-to-cash, working capital, note signal, event match에서 나온 의심 신호마다 반대 설명과 추가 확인 항목을 열어 스킬이 과잉 결론으로 흐르지 않게 한다. 트리거 — '포렌식 반증 ledger', '의심 신호 반례'.
whenToUse:
  - 포렌식 반증 ledger
  - 의심 신호 반례
  - false positive 점검
  - counter evidence
inputs:
  - forensics memo tables
outputs:
  - claim
  - supportingEvidence
  - counterEvidenceNeeded
  - status
capabilityRefs:
  - Company.panel
  - Company.filings
toolRefs:
  - EngineCall
  - RunPython
sourceRefs:
  - dartlab://skills/recipes.fundamental.quality.forensics.falsifierLedger
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - sourceRef
  - executionRef
expectedOutputs:
  - 신호별 반증 조건
  - open/notTriggered 상태
  - 다음 확인 데이터
linkedSkills:
  - recipes.fundamental.quality.forensics.engineCandidateMemo
  - engines.company
  - engines.analysis
gap:
  primary:
    - synth
    - reference
falsifier:
  description: "반증 ledger가 비어 있으면 포렌식 팩의 모든 위험 결론은 미완성으로 본다."
forbidden:
  - supportingEvidence만 쓰고 counterEvidenceNeeded를 누락하지 않는다.
  - open falsifier가 있는데 결론을 확정하지 않는다.
failureModes:
  - 반증 조건이 추상적이라 다음 데이터 확인으로 이어지지 않음
  - false positive 사례가 누적되지 않음
examples:
  - 매출채권 괴리의 반증 조건 열어줘
  - 포렌식 신호 false positive 점검
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

memo = buildEvidenceForensicsMemo(
    target=target,
    market=str(getattr(c, "market", "KR")),
    companyName=str(getattr(c, "corpName", target)),
    statements=statements,
)

emit_result(
    table=memo["tables"]["falsifierLedger"],
    values={"target": target, "openFalsifiers": sum(1 for row in memo["tables"]["falsifierLedger"] if row["status"] == "open")},
    date=memo["asOf"],
    sources=memo["sources"],
)
```

## 호출 동작

### 1. 결론 도출

각 claim을 `open` 또는 `notTriggered`로 둔다. open은 위험 확정이 아니라 확인해야 할 반례가 있다는 뜻이다.

### 2. 핵심 근거 수집

revenue bridge, working capital, note signal, event match의 status를 모아 claim별 반증 요구사항을 만든다.

### 3. 메커니즘 분석

포렌식 신호의 핵심은 탐지보다 반증이다. 같은 수치라도 신규 고객, 수주잔고, 계절성, boilerplate 공시로 설명되면 엔진 후보에서 제외해야 한다.

### 4. 반례·한계

반증 조건은 완전 자동 판정이 아니다. ask 답변 품질 점검에서 사람이 반증 조건이 구체적인지 읽어야 한다.

### 5. 후속 모니터링

open falsifier가 2개 이상이면 다음 ask/selfRun에서 추가 데이터 또는 원문 본문 확인이 필요하다.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `claim` | 의심 신호 |
| `supportingEvidence` | 신호 status |
| `counterEvidenceNeeded` | 필요한 반증 데이터 |
| `status` | open/notTriggered |

## 연계 절차

1. recipes.fundamental.quality.forensics.eventToStatementMatcher - claim을 열 이벤트와 원표 신호를 확보한다.
2. recipes.fundamental.quality.forensics.engineCandidateMemo - 반증을 통과한 신호만 후보로 남김.
3. recipes.fundamental.quality.forensics.deepDive - 최종 ledger에 포함.

## 기본 검증

- open falsifier는 답변에 그대로 노출한다.
- 반증 조건이 없는 신호는 engineCandidateMemo에 승격하지 않는다.
