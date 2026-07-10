---
id: recipes.fundamental.disclosure.sec8kMaterialEvents
title: SEC 8-K material event burst (30 day 윈도우 카운트)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 미국 8-K material event filing 의 30 일 윈도우 카운트 + Item 분류 분포. ≥ 5 건 또는 Item 5.02 (임원 변동) ≥ 2 건 = *전환점 burst* 후보. EDGAR raw. 트리거 — 'SEC 8-K material event burst (30 day 윈도우 카운트)', 'sec 8 k material events', 'sec8kMaterialEvents'.
whenToUse:
  - 8-K burst
  - SEC material event
  - 임원 변동 cluster
  - 미국 이벤트 burst
examples:
  - AAPL 8-K 30일 안 burst 카운트
  - SEC material event 폭증 종목
  - Item 5.02 임원 변동 cluster
expectedOutputs:
  - 30d 안 8-K 총 건수 + Item 분류 분포
  - Item 5.02 (임원 변동) 카운트
  - burst 라벨 (≥ 5 건 OR Item 5.02 ≥ 2 = 전환점 후보)
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
    - gather
    - synth
testUniverse:
  market: US
  tickers:
    - "AAPL"
    - "MSFT"
falsifier:
  description: "8-K filing < 3 이면 burst 결론 X. 정기 (Item 8.01 disclosure) 만 burst 처리하면 false positive."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
from collections import Counter
from datetime import datetime, timedelta

ticker = "AAPL"

try:
    filings = dartlab.Company(ticker).filings()
except Exception:
    filings = []

def parseDate(v):
    if isinstance(v, datetime): return v.date()
    s = str(v)[:10].replace(".","-")
    try: return datetime.strptime(s, "%Y-%m-%d").date()
    except: return None

events = []
for f in filings:
    d = parseDate(f.get("filingDate"))
    item = (f.get("item") or "").strip()
    if d:
        events.append({"date": d, "item": item, "title": (f.get("title") or "")[:60]})
events.sort(key=lambda e: e["date"])

# 30 day window count
WINDOW = timedelta(days=30)
clusters = []
for e in events:
    start = e["date"] - WINDOW
    same_window = [x for x in events if start <= x["date"] <= e["date"]]
    if len(same_window) >= 5:
        item_counts = Counter(x["item"] for x in same_window)
        clusters.append({
            "windowEnd": str(e["date"]),
            "filingCount": len(same_window),
            "items": dict(item_counts),
            "execEvents": item_counts.get("5.02", 0),
        })
        break  # first cluster

if not clusters:
    item_counts = Counter(e["item"] for e in events)
    clusters = [{
        "windowEnd": str(events[-1]["date"]) if events else None,
        "filingCount": len(events),
        "items": dict(item_counts),
        "execEvents": item_counts.get("5.02", 0),
    }] if events else []

table = pl.DataFrame(clusters) if clusters else pl.DataFrame(
    schema={"windowEnd": pl.Utf8, "filingCount": pl.Int64, "items": pl.Object, "execEvents": pl.Int64}
)

emit_result(
    table=table,
    values={"latestCount": clusters[-1]["filingCount"] if clusters else 0,
            "execEvents": clusters[-1]["execEvents"] if clusters else 0},
    date=clusters[-1]["windowEnd"] if clusters else None,
    sources=["dartlab://edgar/8k"],
)
```

## 호출 동작

### 1. 결론 도출

filingCount + execEvents burst 단정. 예: "AAPL 직전 60일 8-K 12건 → 30일 윈도우 안 7건 cluster (≥ 5 임계 통과) — Item 분포: 1.01 신규계약 2 + 2.02 실적 1 + 5.02 임원변동 3 (≥ 2 임계 통과) + 8.01 기타 1 → 양 임계 동시 통과 — 전환점 burst phase (임원 cluster + 계약 동행)."

### 2. 핵심 근거 수집

- EDGAR provider fetch8kFilings(ticker, days=60) — 직전 60일 8-K filing
- 각 filing 의 filingDate + item (SEC Item code) + title
- 30일 sliding window cluster 검출
- Item 5.02 (임원/이사 변동) 카운트 (별도 임계)

### 3. 메커니즘 분석

```
60일 8-K 시계열 → 30일 window cluster
   각 시점 → 직전 30일 안 filing 수 카운트
   ≥ 5 건 → burst 후보
   ↓
Item 분류 분포 (SEC Item code):
   1.01 신규/만료계약   → 사업 변경
   2.01 자산 취득/매각  → 구조조정
   2.02 실적 release    → 정기 (burst 제외)
   5.02 임원/이사 변동  → 거버넌스 변경 (≥ 2 = 별도 임계)
   5.07 의결 결과       → 주주 의결
   8.01 기타            → 의무 공시 (큰 의미 약)
   ↓
burst 판정 (OR):
   filingCount ≥ 5         → 양적 burst
   execEvents ≥ 2          → 임원 cluster (질적 burst)
   둘 다                    → 강한 전환점 후보
   ↓
정기성 분리:
   8.01 정기 disclosure 만으로 burst → false positive (제외 필요)
   비정기 Item (5.02 / 2.01 / 1.01) 중심 burst → 진성 신호
```

8-K burst 자체 = recession 단정 X — 정량 사실 표기. 회사 단위 *전환점 후보* 표지. 정기 (Item 8.01 routine disclosure) 가중치 낮춰야 false positive 방지.

### 4. 반례·한계

- 8-K filing < 3 → burst 결론 X.
- Item 8.01 만 burst 처리 시 false positive (routine disclosure 다수).
- 60일 window 너무 길면 다른 catalyst 와 overlap.
- 미국 한정 — KR 공시 (분기보고서 + 임원 변동) 별도 recipe 필요.

### 5. 후속 모니터링

- filingCount ≥ 5 + 가격 변동 → `recipes.fundamental.disclosure.eventRadar.priceFlowReaction` 으로 시장 반응 정량화.
- execEvents ≥ 2 → `recipes.fundamental.quality.forensics.executiveCompensationAudit` 으로 임원 보상 변화 cross-check.
- 1.01 신규계약 burst → `recipes.news.eventTimelineFusion` 으로 deal cluster 분류.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `windowEnd` | window 끝 일자 |
| `filingCount` | 30 일 안 8-K 수 |
| `items` | Item 분류 dict |
| `execEvents` | Item 5.02 (임원변동) 카운트 |

## 연계 절차

1. recipes.fundamental.disclosure.event - 사건 inbox 와 결합.
2. recipes.fundamental.quality.forensics.executiveCompensationAudit - 임원 변동 + 보상 변화.

## 기본 검증

- 8-K < 3 이면 burst 결론 X.
- Item 8.01 정기성만 burst 처리하지 않도록 Item 별 가중치.
- *burst* = recession 단정 X — 정량 사실 표기.
