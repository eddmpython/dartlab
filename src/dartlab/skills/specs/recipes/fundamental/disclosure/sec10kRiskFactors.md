---
id: recipes.fundamental.disclosure.sec10kRiskFactors
title: SEC 10-K Item 1A 위험 요인 변화 (YoY 신규/삭제 항목 수)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 미국 10-K Item 1A "Risk Factors" 의 직전 연도 대비 *신규 추가* / *삭제* 항목 수. 신규 risk factor ≥ 3 = 경영진의 위험 인식 전환 신호. EDGAR provider raw. 트리거 — 'SEC 10-K Item 1A 위험 요인 변화 (YoY 신규/삭제 항목 수)', 'sec 10 k risk factors', 'sec10kRiskFactors'.
whenToUse:
  - 10-K risk factor YoY
  - SEC 위험 요인 변화
  - 미국 공시 risk
  - Item 1A 신규 위험
examples:
  - AAPL 10-K 위험 요인 작년 대비 신규 / 삭제
  - SEC Item 1A risk factor YoY 변화
  - 미국 종목 경영진 위험 인식 전환 신호
expectedOutputs:
  - 신규 추가 risk factor list + count
  - 삭제 risk factor list + count
  - 라벨 (신규 ≥ 3 = 전환 신호 / 미만 = 평상)
linkedSkills:
  - engines.edgar
  - engines.gather
  - engines.company
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.evidenceCoverage"
  - "engines.viz.tableBackedChart"
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
gap:
  primary:
    - search
    - analysis
testUniverse:
  market: US
  tickers:
    - "AAPL"
    - "MSFT"
falsifier:
  description: "10-K 본문 raw 누락 또는 직전 연도 없음 → 결론 X. 단순 wording 변경을 신규 위험으로 카운트하면 false positive."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import re

ticker = "AAPL"

try:
    filings = dartlab.Company(ticker).filings()
except Exception:
    filings = []

def extract_risk_items(text):
    """Item 1A 안 bullet 또는 paragraph 단위 항목 추출."""
    # heuristic: 6 어 이상 새 paragraph 시작
    return [re.sub(r"\s+", " ", p)[:120] for p in re.split(r"\n\s*\n", text) if len(p.split()) >= 6][:50]

if len(filings) < 2:
    table = pl.DataFrame(schema={"current": pl.Int64, "previous": pl.Int64, "added": pl.Int64, "removed": pl.Int64})
    emit_result(table=table, values={"insufficient": True}, date=None, sources=["dartlab://edgar/10k"])
else:
    cur_items = set(extract_risk_items(filings[0].get("item1aText", "")))
    prev_items = set(extract_risk_items(filings[1].get("item1aText", "")))
    added = len(cur_items - prev_items)
    removed = len(prev_items - cur_items)
    table = pl.DataFrame([{
        "current": len(cur_items),
        "previous": len(prev_items),
        "added": added,
        "removed": removed,
        "filingDate": filings[0].get("filingDate"),
    }])
    emit_result(
        table=table,
        values={"added": added, "removed": removed, "current": len(cur_items)},
        date=filings[0].get("filingDate"),
        sources=["dartlab://edgar/10k"],
    )
```

## 호출 동작

### 1. 결론 도출

added + removed risk factor 단정. 예: "AAPL 10-K FY2024 vs FY2023: current=42 / previous=39 항목 / added=5 (AI 규제·반독점·중국 의존·data privacy 신규·기후) / removed=2 → 신규 ≥ 3 임계 통과 — 경영진 위험 인식 *transition* phase (regulatory + AI 신규 인식)."

### 2. 핵심 근거 수집

- EDGAR provider fetch10kFilings(ticker, limit=2) — 최근 + 직전 10-K
- 각 filing 의 Item 1A "Risk Factors" 본문 text
- paragraph 단위 분할 (6 어 이상) → risk item set
- set diff: added = current - previous, removed = previous - current

### 3. 메커니즘 분석

```
2 개 10-K Item 1A → risk item set diff
   set(current) - set(previous) = added
   set(previous) - set(current) = removed
   ↓
임계 판정:
   added ≥ 3 또는 removed ≥ 3 → transition 후보 (위험 인식 전환)
   added < 3 + removed < 3   → 평상 (위험 인식 유지)
   ↓
added 의 의미 해석:
   regulatory / litigation 신규 → 법적 risk 가중
   technology / cyber 신규     → tech disruption 인식
   geopolitical 신규           → 외부 환경 변화
   removed 의 의미:
   risk 해소 (긍정) 또는 *공시 회피* (부정 — forensic risk)
```

10-K Risk Factors 는 *경영진 자기 인식* — 객관 risk 아님. 신규 추가 ≥ 3 = 인식 전환 신호. 단순 wording 변경 (의미 동일) 은 paragraph 매칭으로 분리 필수.

### 4. 반례·한계

- 직전 연도 10-K 없음 → 결론 X.
- 단순 wording 변경 (의미 동일) 을 신규로 카운트 시 false positive.
- paragraph 분할 heuristic — bullet vs paragraph 회사별 format 다름.
- removed 가 *공시 회피* 인지 *실제 해소* 인지 구분 어려움.

### 5. 후속 모니터링

- added ≥ 3 → `recipes.fundamental.disclosure.sec8kMaterialEvents` 로 8-K 사후 이벤트 확인.
- regulatory 신규 risk → `recipes.fundamental.quality.forensics.disclosureTimingAnomaly` 로 공시 timing 점검.
- removed ≥ 3 + 가격 하락 → forensic risk 가중 (`recipes.fundamental.quality.forensics.fairDisclosureBreach`).

## 대표 반환 형태

| column | 의미 |
|---|---|
| `current` | 최근 10-K 항목 수 |
| `previous` | 직전 10-K 항목 수 |
| `added` | 신규 추가 |
| `removed` | 삭제 |

## 연계 절차

1. recipes.fundamental.disclosure.filingTextSignal - 위험 키워드 frequency 결합.
2. recipes.fundamental.quality.forensics.disclosureTimingAnomaly - 위험 추가 시점과 가격 변동 비교.

## 기본 검증

- 10-K raw 누락 또는 직전 연도 없음 → 결론 X.
- *wording* 변경 (의미 동일, 표현만 변경) 을 신규로 카운트하지 않도록 paragraph 매칭 임계 적절히.
- *innovation lead* 결론은 R&D 강도만으로 단정 X.
