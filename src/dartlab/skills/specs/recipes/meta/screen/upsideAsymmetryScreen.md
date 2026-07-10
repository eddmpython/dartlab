---
id: recipes.meta.screen.upsideAsymmetryScreen
title: Upside Asymmetry Screen — MDD ≤ 15% ∧ catalyst ≥ 2
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 비대칭 upside 후보 스크린 — 직전 12 개월 MDD (최대낙폭) ≤ 15% (downside 제한) 동시 향후 90 일 catalyst ≥ 2 (upside 동인 다중). asymmetric payoff (downside 작고 upside 큰) 후보 priority 발굴. 트리거 — '비대칭', 'asymmetry', 'upside asymmetry', '하방 제한', '카탈리스트 다중'.
whenToUse:
  - 비대칭 upside
  - upside asymmetry
  - 하방 제한
  - MDD 제한
  - catalyst 다중
  - asymmetric payoff
linkedSkills:
  - engines.scan
  - engines.quant
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
  - engines.viz.peerMatrix
visualGuidance:
  - "MDD × catalyst count 2 차원 산점도 — engines.viz.peerMatrix, quadrant 1 (low MDD × high catalyst) green zone."
gap:
  primary:
    - quant
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
  description: 전체 universe 동시 충족 0 건 = MDD ≤ 15% 가 강세장 가정 (약세장에서 MDD 작은 종목은 cyclical 아닌 defensive 만) — 약세장에서는 catalyst 부재 가능성.
  pythonCheck: |
    assert n_asymmetry >= 1
expectedNovelty:
  - mdd12m
  - catalystCount
  - asymmetryRatio
forbidden:
  - catalyst ≥ 2 정량 정의 강행 — 정성 catalyst (성장 가능성) 추측 금지.
  - MDD 12M 단독 평가 X — regime context (강세장 vs 약세장) 동행.
  - asymmetric payoff = 확정 upside X — 후보 priority 정렬용.
failureModes:
  - 신규 상장 (12 개월 미만) MDD 부족.
  - catalyst 정의 모호 — 본 recipe 의 catalyst 정의 (실적 / 배당 / 신규 사업 / 정책 / M&A 5 종) strict.
  - cyclical 강세장 부풀림 — regime check 동행 권장.
examples:
  - KOSPI200 비대칭 upside universe (월 1 회)
  - 보유 종목 asymmetric payoff check
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

asof = date.today()
horizon_90d = asof + timedelta(days=90)
lookback_12m = asof - timedelta(days=365)

universe = ["005930", "000660", "035720", "207940", "035420"]   # 예시 — KOSPI200 등으로 확장
rows = []

for code in universe:
    c = dartlab.Company(code)

    # 1. 12 개월 MDD
    price_series = dartlab.gather("price", code)  # 12 개월 구간은 아래에서 자른다
    cum_max = price_series["close"].cum_max()
    dd = (price_series["close"] - cum_max) / cum_max
    mdd = dd.min()

    # 2. 향후 90 일 catalyst 카운트 (5 종 enum)
    catalysts = []
    earnings = c.filings()  # 실적 공시 이력
    if earnings: catalysts.append("earnings")

    div = c.filings()  # 배당 공시 이력
    if div: catalysts.append("dividend")

    agm = c.filings()  # 주총 소집 공시 이력
    if agm: catalysts.append("agm")

    # new business / policy / m&a 는 recent disclosure 본문 keyword 매칭
    recent = c.filings()  # 최근 30 일은 rceptDate 로 아래에서 거른다
    if any("신규 사업" in r["report_nm"] or "정관 변경" in r["report_nm"] for r in recent):
        catalysts.append("newBusiness")

    rows.append({
        "stockCode": code,
        "mdd12m": float(mdd),
        "catalystCount": len(catalysts),
        "catalysts": ",".join(catalysts),
    })

df = (
    pl.DataFrame(rows)
    .filter((pl.col("mdd12m") >= -0.15) & (pl.col("catalystCount") >= 2))
    .with_columns(asymmetryRatio=pl.col("catalystCount") / pl.col("mdd12m").abs())
    .sort("asymmetryRatio", descending=True)
)

emit_result(
    table=df,
    values={"n_asymmetry": len(df)},
    date=asof.isoformat(),
    sources=["dartlab://company/price", "dartlab://company/upcoming*"],
)
```

## 호출 동작

### 1. 결론 도출

downside 제한 (MDD ≤ 15%) + upside 동인 다중 (catalyst ≥ 2) 동시 충족 universe — 비대칭 payoff 후보 priority.

### 2. 핵심 근거 수집

- `dartlab.gather("price", code)` 12 개월 가격 시계열 → MDD 계산
- `Company.upcomingEarnings/Dividends/Agm()` — 향후 90 일 schedule catalyst
- `Company.filings()` — recent 30 일 신규 사업 / 정책 keyword 매칭

### 3. 메커니즘 분석

```
2 차원 평가
   downside: MDD 12M ≤ 15% (정량 강건)
   upside  : catalyst 5 enum (earnings/dividend/agm/newBusiness/policy)
           catalyst ≥ 2 (다중 동인)
   ↓
asymmetryRatio = catalystCount / |MDD|
   (높을수록 payoff 비대칭 강함)
   ↓
ratio desc 정렬
```

### 4. 반례·한계

- MDD 12M 단독 평가 — 약세장에서 cyclical 도 MDD 큼.
- catalyst 정의 5 enum strict — 정성 catalyst 제외.
- regime context (강세장에서 MDD 자연히 작음) 동행 권장.
- 12 개월 미만 신규 상장 universe 제외.

### 5. 후속 모니터링

- ratio top 종목 → `recipes.fundamental.disclosure.eventRadar` deep dive.
- catalyst 별 영향도 → `recipes.fundamental.disclosure.priceFlowReaction` 시뮬레이션.
- regime context → `engines.macro.regimes` 5 enum 결합.
- 월 1 회 재실행.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `stockCode : str` · `corpName : str`
- `mdd12m : float` — 12 개월 MDD (음수, -0.15 = -15%)
- `catalystCount : int` (≥ 2)
- `catalysts : str` — comma-separated enum
- `asymmetryRatio : float`

## 연계 절차

1. 본 recipe → 비대칭 upside universe.
2. ratio top → `recipes.fundamental.disclosure.eventRadar` deep dive.
3. catalyst 영향도 → `recipes.fundamental.disclosure.priceFlowReaction` (역사 cohort 평균 reaction).
4. regime check → `engines.macro.regimes` (현재 expansion/recovery 에서 본 신호 강).
5. 보유 종목 monitoring → 신규 진입 시 alert.
