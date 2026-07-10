---
id: recipes.news.eventVolatilityCheck
title: 이벤트 직전·직후 변동성 (ATR ratio)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 공시 이벤트 시점 ±10 거래일 ATR (Average True Range) ratio. T-10 baseline 대비 T+10 ATR 이 1.3x+ 이면 *이벤트 induced 변동성* 확대. 단일 가격 변동 X — *변동성 체제* 측정. 트리거 — '이벤트 직전·직후 변동성 (ATR ratio)', 'event volatility check', 'eventVolatilityCheck'.
whenToUse:
  - 이벤트 변동성
  - ATR ratio
  - 이벤트 induced vol
  - 공시 후 변동성 체제
examples:
  - 005930 공시 직후 변동성 확대했나
  - 이벤트 induced volatility 정량 측정
  - T+10 ATR이 baseline 대비 몇 배
expectedOutputs:
  - T-10 baseline ATR + T+10 ATR + ratio (단일값)
  - 변동성 확대 / 축소 / 무변화 라벨 (ratio 임계 1.3x)
  - 이벤트 시점 + 직전 / 직후 ATR 시계열
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.disclosure.eventRadar.eventInbox
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
  market: KR
  stockCodes:
    - "005930"
    - "000660"
falsifier:
  description: "ATR < 5 거래일 sample 이면 결론 X. 시장 전체 변동성 (KOSPI VKOSPI) 동시 확대 시 이벤트 induced 분리 불가."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import statistics
from datetime import datetime, timedelta

target = "005930"
c = dartlab.Company(target)

def parseDate(v):
    if isinstance(v, datetime): return v.date()
    s = str(v)[:10].replace(".","-")
    try: return datetime.strptime(s, "%Y-%m-%d").date()
    except: return None

try:
    px = c.gather("price").head(120).to_dicts()
except Exception:
    px = []
px.sort(key=lambda r: str(r.get("date") or r.get("tradeDate")))
px_by_date = {}
for p in px:
    d = parseDate(p.get("date") or p.get("tradeDate"))
    if d:
        px_by_date[d] = (float(p.get("high") or 0), float(p.get("low") or 0), float(p.get("close") or 0))

dates_sorted = sorted(px_by_date.keys())

def atr_window(start_d, end_d):
    """ATR (Average True Range) over [start_d, end_d]."""
    trs = []
    prev_close = None
    for d in dates_sorted:
        if d < start_d or d > end_d: continue
        h, l, c = px_by_date[d]
        if prev_close is None:
            tr = h - l
        else:
            tr = max(h - l, abs(h - prev_close), abs(l - prev_close))
        trs.append(tr)
        prev_close = c
    return statistics.mean(trs) if trs else None

try:
    events = c.gather("liveFilings").to_dicts()[:8]
except Exception:
    events = []

rows = []
for e in events:
    d = parseDate(e.get("date") or e.get("rcept_dt") or e.get("filedAt"))
    if not d: continue
    pre = atr_window(d - timedelta(days=20), d - timedelta(days=1))
    post = atr_window(d + timedelta(days=1), d + timedelta(days=20))
    if pre is None or post is None or pre == 0: continue
    rows.append({
        "eventDate": str(d),
        "title": (e.get("title") or e.get("report_nm") or "")[:60],
        "atrPre": pre,
        "atrPost": post,
        "atrRatio": post / pre,
        "regimeShift": "expand" if (post/pre) >= 1.3 else "contract" if (post/pre) <= 0.7 else "stable",
    })

table = pl.DataFrame(rows) if rows else pl.DataFrame(
    schema={"eventDate": pl.Utf8, "title": pl.Utf8, "atrPre": pl.Float64,
            "atrPost": pl.Float64, "atrRatio": pl.Float64, "regimeShift": pl.Utf8}
)

emit_result(
    table=table,
    values={"eventCount": table.height,
            "expandCount": int((table["regimeShift"] == "expand").sum()) if table.height else 0},
    date=None,
    sources=["dartlab://gather/liveFilings", "dartlab://gather/price"],
)
```

## 호출 동작

### 1. 결론 도출

이벤트 ±20거래일 ATR ratio phase 단정 (expand ≥ 1.3 / stable / contract ≤ 0.7). 예: "공시 직전 ATR 2.1%, 직후 ATR 3.2% → ratio 1.52 → expand phase (변동성 50% 확대)."

### 2. 핵심 근거 수집

- 이벤트 시점 (Company.filings 또는 liveFilings 의 rcept_dt)
- 가격 row ±20거래일 (Company.gather('price') high/low/close)
- ATR(N) = N일 평균 True Range = avg(max(H-L, |H-prevC|, |L-prevC|))

### 3. 메커니즘 분석

```
이벤트 시점 T
   ↓
직전 20 거래일 (T-20 ~ T-1): ATR_pre = avg(true_range)
직후 20 거래일 (T+1 ~ T+20): ATR_post = avg(true_range)
   ↓
ratio = ATR_post / ATR_pre
   ≥ 1.3   → expand (이벤트 변동성 확대 — 시장 반응 강함)
   0.7-1.3 → stable (반응 약함)
   ≤ 0.7   → contract (변동성 흡수 — 이벤트 해소)
```

이벤트 정보 큼직 → ATR ratio 1.3 이상 → 시장 가격 적응 중. ratio < 0.7 이면 시장이 이벤트를 이미 가격에 반영했거나 의미 약함.

### 4. 반례·한계

- 시장 전체 변동성 (KOSPI VIX) 동시 변동 보정 없음 — 시장 효과 vs 이벤트 효과 분리 X.
- 이벤트 ±20일 안 다른 이벤트 발생 시 ATR 혼합.
- 시장 휴장일 (설·추석) 으로 거래일 부족 시 직후 20일 계산 불가.
- ATR 은 magnitude 만 — 방향성 (상승/하락) 정보 X.

### 5. 후속 모니터링

- ratio ≥ 1.3 지속: `recipes.news.eventTimelineFusion` 으로 cluster 안 가격 leader 확인.
- ratio ≤ 0.7 + 이벤트 큼직: `recipes.fundamental.disclosure.eventRadar.priceFlowReaction` 으로 수급 반응 확인.
- 연쇄 이벤트 (30일 안 2+) 시 `recipes.news.calendarEventClock` 으로 다음 이벤트 사전 추적.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `eventDate` | 공시 시점 |
| `title` | 공시 제목 |
| `atrPre` / `atrPost` | 이벤트 ± 20 거래일 평균 ATR |
| `atrRatio` | post / pre |
| `regimeShift` | expand / contract / stable |

## 연계 절차

1. recipes.fundamental.disclosure.eventRadar.eventInbox - 이벤트 inbox 와 결합.
2. recipes.news.eventTimelineFusion - 변동성 확대 시점의 시간순 fusion.

## 기본 검증

- 거래일 sample < 5 이면 결론 X.
- 시장 변동성 (VKOSPI) 동시 확대 시 분리 불가 — 한계.
- 이벤트 *원인* 단정 금지 — 변동성 체제 변화 자체가 정량 신호.
