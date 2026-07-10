---
id: recipes.meta.report.catalystCalendar
title: Catalyst Calendar — 향후 30/90 일 예정 이벤트
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 향후 30/90 일 예정 이벤트 단일 표 — 실적 발표 · 배당락 · MSCI rebalancing · 금통위 · FOMC · IPO · 주총 6 종 enum + dateRef 정렬. FSI 벤치마크 cadence recipe 3 의 2 호. 트리거 — '캘린더', 'catalyst calendar', '예정 이벤트', '실적 일정'.
whenToUse:
  - 캘린더
  - catalyst calendar
  - 예정 이벤트
  - 실적 일정
  - 배당락 일정
  - 금통위 일정
  - FOMC 일정
  - MSCI rebalancing
  - 주총 일정
linkedSkills:
  - engines.company
  - engines.scan
  - engines.macro
  - engines.search
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
  - engines.viz.tableBackedChart
visualGuidance:
  - "캘린더 표 단일 — engines.viz.tableBackedChart, dateRef 오름차순 정렬 + eventType 컬럼 색 enum."
gap:
  primary:
    - company
    - macro
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "035720"
    - "207940"
    - "035420"
  asOfPolicy: latest
falsifier:
  description: 30 일 window 안 0 이벤트 = 데이터 수집 실패 (정상 시장에서 KOSPI200 universe 30 일 0 이벤트 거의 불가능).
  pythonCheck: |
    assert n_events_30d > 0
expectedNovelty:
  - eventType
  - eventDate
  - priorityRank
forbidden:
  - 추측 일정 금지 — 공시 또는 공식 source (한은/Fed) 확인된 일정만.
  - dateRef 누락 시 표 0 의미 — 모든 이벤트 dateRef 강행.
  - 단순 "다음 분기" 같은 모호 시점 금지 — 정확 일자.
failureModes:
  - 보유 종목 universe 미정의 시 default KOSPI200 (이벤트 수 ↑↑, signal-to-noise 저하).
  - 비정기 이벤트 (M&A 발표 등) 사전 수집 불가능 — sched 이벤트 한정.
  - 해외 이벤트 (FOMC) 시간대 한국 시간 변환 필수.
examples:
  - 2026-06 KR 실적 발표 일정 + 6 월 금통위 + 6 월 FOMC
  - 보유 5 종목 다음 분기 실적 발표 일자
lastUpdated: '2026-05-28'
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
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
from datetime import date, timedelta

# universe + 기간
holdings = ["005930", "000660", "035720", "207940", "035420"]
asof = date.today()
horizon_30d = asof + timedelta(days=30)
horizon_90d = asof + timedelta(days=90)

events = []

# 1. 실적 발표 일정 (DART 공시 schedule + 분기말 +45/90 일 추정)
for c in holdings:
    company = dartlab.Company(c)
    earnings = rows(company.filings())  # 실적 공시 이력. 예정 일정 추정은 아래 cycle 로직
    events.extend([
        {"eventType": "earnings", "stockCode": c, "eventDate": e["date"], "detail": e["quarter"]}
        for e in earnings
    ])

# 2. 배당락일 (DART 배당결정 공시 추출)
for c in holdings:
    company = dartlab.Company(c)
    div = rows(company.filings())  # 배당 공시 이력
    events.extend([
        {"eventType": "exDividend", "stockCode": c, "eventDate": d["exDate"], "detail": f"₩{d['amount']}"}
        for d in div
    ])

# 3. 금통위 일정 (한은 공식 cron)
bok_meetings = dartlab.macro("rates", market="KR", upcoming=True, end=horizon_90d.isoformat())
events.extend([
    {"eventType": "bokRate", "stockCode": None, "eventDate": m["date"], "detail": "금통위"}
    for m in bok_meetings.get("upcoming", [])
])

# 4. FOMC 일정 (Fed 공식 cron)
fomc_meetings = dartlab.macro("rates", market="US", upcoming=True, end=horizon_90d.isoformat())
events.extend([
    {"eventType": "fomc", "stockCode": None, "eventDate": m["date"], "detail": "FOMC"}
    for m in fomc_meetings.get("upcoming", [])
])

# 5. MSCI rebalancing (분기 cycle — 2/5/8/11 월 last working day)
# (구현: MSCI 공식 schedule)

# 6. 주총 (DART 주주총회 공시)
for c in holdings:
    company = dartlab.Company(c)
    agm = rows(company.filings())  # 주총 소집 공시 이력
    events.extend([
        {"eventType": "agm", "stockCode": c, "eventDate": a["date"], "detail": "주총"}
        for a in agm
    ])

# 정렬 + 우선순위 rank
df = pl.DataFrame(events).sort("eventDate").with_columns(
    priorityRank=pl.col("eventType").map_dict({
        "earnings": 1, "fomc": 2, "bokRate": 2, "exDividend": 3, "agm": 4, "msciRebal": 5,
    })
)

events_30d = df.filter(pl.col("eventDate") <= horizon_30d.isoformat())

emit_result(
    table=df,
    values={"n_events_30d": len(events_30d), "n_events_90d": len(df)},
    date=asof.isoformat(),
    sources=["dartlab://company/upcoming*", "dartlab://macro/rates"],
)
```

## 호출 동작

### 1. 결론 도출

향후 30/90 일 예정 이벤트 단일 표 — 6 enum (earnings/exDividend/bokRate/fomc/msciRebal/agm) × dateRef 정렬 + priorityRank.

### 2. 핵심 근거 수집

- `Company.filings()` 공시 이력 + 분기 cycle 추정 (예정 일정 전용 계약 호출은 없다)
- `dartlab.macro("rates", upcoming=True)` — 한은/Fed 공식 cron
- MSCI rebalancing 분기 cycle (구현 별도)

### 3. 메커니즘 분석

```
6 source → 단일 표 + 정렬 + rank
   earnings (priority 1)   → 분기 cycle, 변동성 최고
   fomc/bokRate (2)        → macro regime 영향
   exDividend (3)          → 보유 종목 cash flow
   agm (4)                 → 거버넌스 이벤트
   msciRebal (5)           → 패시브 flow
   ↓
df.sort(eventDate) + priorityRank
```

### 4. 반례·한계

- 비정기 이벤트 (M&A / 행정처분 / 위기) 사전 수집 불가능.
- 해외 이벤트 시간대 변환 (FOMC 한국 시간 새벽 4 시 기준).
- 분기 cycle 추정 — 실제 발표일은 공시 후 확정 (오차 ±7 일).
- 보유 종목 universe 외 종목 영향 사건 (대형주 실적) 누락.

### 5. 후속 모니터링

- 30 일 안 보유 종목 실적 → `recipes.fundamental.disclosure.eventRadar` deep dive 사전 준비.
- 금통위/FOMC → `recipes.macro.scenarioDiagram` 사전 시나리오.
- 배당락 → 보유 종목 현금 흐름 영향 시뮬레이션.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `eventType : str` — earnings / exDividend / bokRate / fomc / msciRebal / agm
- `stockCode : str | None` — None = 시장 wide 이벤트 (FOMC/금통위)
- `eventDate : str` — YYYY-MM-DD
- `detail : str` — 분기 ID / 배당액 / 이벤트 명
- `priorityRank : int` — 1~5

## 연계 절차

1. 본 recipe → 향후 30/90 일 이벤트 단일 표.
2. earnings 임박 → `recipes.fundamental.disclosure.eventRadar` 사전 분석.
3. fomc/bokRate → `recipes.macro.usFedDotPlotGap` 또는 `recipes.macro.qualityMacroBeta` 사전 시나리오.
4. exDividend → 보유 포트폴리오 현금 흐름 모델 갱신.
5. 일일 cadence 결합 → `recipes.meta.report.dailyMorningNote`.
