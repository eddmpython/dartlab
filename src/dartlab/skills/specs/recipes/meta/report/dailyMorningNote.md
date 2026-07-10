---
id: recipes.meta.report.dailyMorningNote
title: Daily Morning Note — 장 마감 후 시황 1 페이지
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 매 장 마감 후 자동 시황 1 페이지 작성 — 지수 mover + 자체 보유 종목 변동 + 신규 공시 catalyst + macro update 4 블록 단일 페이지. FSI 벤치마크 cadence recipe 3 의 1 호. 트리거 — '오늘 시황', '데일리 노트', 'morning note', 'morning brief'.
whenToUse:
  - 데일리 노트
  - 오늘 시황
  - morning note
  - morning brief
  - 장 마감
  - 일일 리뷰
  - 보유 종목 변동
linkedSkills:
  - engines.gather
  - engines.scan
  - engines.macro
  - engines.search
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
  - engines.viz.tableBackedChart
  - engines.viz.kpiRibbon
visualGuidance:
  - "지수 mover 표는 engines.viz.tableBackedChart 사용 — % change 컬럼 음수/양수 색."
  - "macro update 4 indicator 는 engines.viz.kpiRibbon — 단위/dateRef 동행."
gap:
  primary:
    - gather
    - scan
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
  description: 4 블록 (mover/holdings/catalyst/macro) 중 하나라도 0 건이면 시장 휴장 또는 데이터 수집 실패 — 재실행 또는 manual.
  pythonCheck: |
    assert n_movers > 0 and n_macro_updates > 0
expectedNovelty:
  - dailyMovers
  - newCatalysts
  - macroDelta
forbidden:
  - 인덱스 stale 시 search 결과만으로 신규 공시 답변 금지 (engines.search.disclosureSearch 4 강행 룰).
  - macro indicator 단위 (% / bp / index) 누락 금지.
  - 보유 종목 list 없이 generic mover 만 출력 시 본 recipe 가치 0 — universe 명시 강행.
failureModes:
  - 보유 종목 universe 미정의 시 default KOSPI top 30 사용.
  - 장 휴일 (주말/공휴일) 호출 시 직전 영업일 데이터.
  - 신규 공시 indexing 지연 (engines.search dataAsOf > 1) 시 liveFilings fallback.
examples:
  - 2026-05-28 KOSPI 마감 후 morning note (다음날 아침 발송용)
  - 보유 5 종목 + KOSPI200 mover top 10 + 신규 공시 + macro 4 축
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

# universe — 보유 종목 + 시장 mover universe
holdings = ["005930", "000660", "035720", "207940", "035420"]
asof = date.today() - timedelta(days=1)   # 직전 영업일

# 1. 지수 mover (KOSPI200 top 10 등락)
mover = dartlab.scan("priceMover", market="KR", date=asof.isoformat(), top=10)

# 2. 보유 종목 변동
holdings_change = [
    {
        "stockCode": c,
        "close": dartlab.Company(c).price(asof.isoformat()),
        "change": dartlab.Company(c).priceChange(asof.isoformat()),
    }
    for c in holdings
]

# 3. 신규 공시 (보유 종목 한정 — search 아닌 liveFilings 정공)
new_filings = []
for c in holdings:
    company = dartlab.Company(c)
    live = company.filings()
    new_filings.extend([f for f in live if f["rcept_dt"] == asof.strftime("%Y%m%d")])

# 4. macro update 4 indicator
macro_inflation = dartlab.macro("inflation", market="KR")
macro_cycle = dartlab.macro("cycle", market="KR")
macro_rates = dartlab.macro("rates", market="KR")
macro_exchange = dartlab.macro("exchange", market="KR")

emit_result(
    table=mover,
    values={"n_movers": len(mover), "n_macro_updates": 4, "n_new_filings": len(new_filings)},
    date=asof.isoformat(),
    sources=["dartlab://scan/priceMover", "dartlab://macro/*", "dartlab://company/liveFilings"],
)
```

## 호출 동작

### 1. 결론 도출

매 장 마감 후 4 블록 단일 페이지: 지수 mover top 10 + 보유 종목 변동 + 신규 공시 catalyst + macro update 4 indicator. 다음날 아침 발송용 cadence.

### 2. 핵심 근거 수집

- `dartlab.scan("priceMover")` — 시장 mover universe
- `dartlab.Company(c).price()` / `priceChange()` — 보유 종목 종가·변동
- `Company.filings()` — 신규 공시 (search 아닌 정공)
- `dartlab.macro("inflation"|"cycle"|"rates"|"exchange")` — 4 indicator 갱신

### 3. 메커니즘 분석

```
4 블록 단일 페이지 조립
   Block A: 지수 mover (시장 wide context)
   Block B: 보유 종목 변동 (own context)
   Block C: 신규 공시 catalyst (event 신호)
   Block D: macro update (cycle/inflation/rates/fx)
   ↓
narrative 1 page (≤ 400 단어)
```

### 4. 반례·한계

- 보유 종목 universe 미정의 시 default KOSPI top 30 사용 (own context 약함).
- 휴장일 호출 시 직전 영업일 데이터 — narrative 에 명시.
- liveFilings DART API 직접 호출 — rate limit 시 partial result.
- macro indicator 갱신 주기 (월/일) 차이 — 월 단위는 stale 가능.

### 5. 후속 모니터링

- mover top 10 중 보유 종목 ⊂ → `recipes.fundamental.*` 직접 deep dive.
- 신규 공시 catalyst 발생 → `Company.filings(rcept_no)` 본문 분석.
- macro indicator regime 전환 신호 → `recipes.macro.scenarioDiagram`.

## 대표 반환 형태

`pl.DataFrame` (mover 블록) + dict (holdings/filings/macro 블록):

- `stockCode : str` · `corpName : str` · `close : float` · `change : float (%)` (mover · holdings)
- `rcept_no : str` · `report_nm : str` · `rcept_dt : str` · `dartUrl : str` (filings)
- `axis : str` · `value : float` · `unit : str` · `dateRef : str` (macro)

## 연계 절차

1. 본 recipe → 일일 cadence 단일 페이지.
2. mover 상위 보유 종목 발견 → `recipes.fundamental.valuation.damodaran.deepDive` deep dive.
3. 신규 공시 catalyst → `Company.filings()` + `recipes.fundamental.disclosure.eventRadar`.
4. macro indicator regime 전환 → `recipes.macro.scenarioDiagram` 또는 `recipes.macro.qualityMacroBeta`.
5. 주간 합본 → `recipes.meta.report.weeklyDigest` (별 트랙).
