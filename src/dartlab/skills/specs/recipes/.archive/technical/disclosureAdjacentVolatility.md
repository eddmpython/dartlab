---
id: recipes.technical.disclosureAdjacentVolatility
title: 공시 인접 변동성 (ATR jump)
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 다가오는 정기공시 (horizon 30 일) 가 있는 종목의 최근 ATR14 가 평소 윈도우 대비 얼마나 상승했는지 측정 — 시장이 공시 전 변동성으로 미리 반응하는지 확인. 트리거 — '공시 인접 변동성', 'ATR jump', '실적 발표 전 변동성', 'pre-earnings drift'.
whenToUse:
  - 정기공시 임박 종목의 변동성 점검
  - pre-earnings volatility expansion 감지
  - 단기 entry timing 변동성 측면 보조 신호
inputs:
  - stockCode (KR)
outputs:
  - tableRef (code · upcomingEventCount · nextEventDays · atrRatio · atrRecent · atrNormal)
  - dateRef (마지막 거래일)
linkedSkills:
  - engines.gather
  - engines.company
  - engines.quant
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - tableRef
  - dateRef
  - executionRef
  - sourceRef
expectedNovelty:
  - atrRatio
  - upcomingEventCount
  - nextEventDays
testUniverse:
  stockCodes:
    - "005930"
    - "000660"
    - "035420"
    - "051910"
    - "207940"
  market: KR
falsifier:
  description: |
    5 종목 모두 atrRatio ≈ 1.0 (±0.05) 면 ATR 의 의미 있는 변화 없음 — 신호 변별력
    0. 또한 upcomingEventCount 0 인 종목이 4 개 이상이면 본 윈도우에서 공시 시즌
    아닐 가능성 — 결과 인용 자제.
  pythonCheck: |
    atrs = [r.get("atrRatio", 0.0) for r in result["table"]]
    flat = sum(1 for r in atrs if 0.95 <= r <= 1.05)
    no_event = sum(1 for r in result["table"] if r.get("upcomingEventCount", 0) == 0)
    assert flat < len(atrs), "atrRatio 모두 평탄 — 변별력 0"
    assert no_event < len(result["table"]) - 1, "공시 0 인 종목 다수 — 시즌 아님"
failureModes:
  - 신규 상장 종목 disclosure history 부재 → upcomingEventCount 0
  - 60 거래일 ATR 표본 부족 (저유동 종목) → atrRatio 무의미
  - horizon 안 다중 catalyst → atrRatio 가 어느 이벤트 반응인지 분리 불가
forbidden:
  - atrRatio > 1.2 만으로 매수 결정 — variance ≠ direction
  - upcomingEventCount 미공개로 atrRatio 단독 인용
  - 미국/일본 종목 입력 (KR DART 한정)
examples:
  - "삼성전자 다가오는 공시 변동성"
  - "공시 전 ATR jump 점검"
  - "pre-earnings drift KR"
lastUpdated: '2026-05-21'
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
visualRefs:
  - "engines.viz.tableBackedChart"
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
from datetime import datetime, date

code = "005930"
c = dartlab.Company(code)
upcoming = c.filings()
px = dartlab.gather("price", code)

px_sorted = px.sort("date")
n = px_sorted.height

# ATR 비교 — 최근 5 거래일 vs 그 이전 30 거래일
atr_series = px_sorted["atr14"].drop_nulls()
if atr_series.len() >= 35:
    atr_recent = float(atr_series.tail(5).mean())
    atr_normal = float(atr_series.tail(35).head(30).mean())
    atrRatio = atr_recent / atr_normal if atr_normal > 0 else 0.0
else:
    atr_recent = 0.0
    atr_normal = 0.0
    atrRatio = 0.0

# 다가오는 공시 카운트 + 가장 가까운 이벤트 D-day
upcomingEventCount = upcoming.height
nextEventDays = -1
if upcomingEventCount > 0 and "expectedDate" in upcoming.columns:
    today = date.today()
    try:
        first = upcoming.sort("expectedDate")["expectedDate"][0]
        first_str = str(first)[:10]
        first_date = datetime.strptime(first_str, "%Y-%m-%d").date()
        nextEventDays = (first_date - today).days
    except (ValueError, TypeError):
        nextEventDays = -1

emit_result(
    table=[{
        "code": code,
        "upcomingEventCount": upcomingEventCount,
        "nextEventDays": nextEventDays,
        "atrRatio": round(atrRatio, 4),
        "atrRecent": round(atr_recent, 2),
        "atrNormal": round(atr_normal, 2),
    }],
    date=str(px_sorted["date"].max()),
    headline={"metric": "atrRatio", "value": round(atrRatio, 4)},
)
```

## 호출 동작

1. `Company(code).calendar(horizonDays=30)` — 정기공시 cycle 추론, 향후 30 일 expectedDate.
2. `gather("price", code)` — OHLCV + atr14 시계열 (1 년 default).
3. 최근 5 거래일 ATR 평균 ÷ 그 이전 30 거래일 ATR 평균 = atrRatio.
4. 가장 가까운 공시까지 D-day = nextEventDays.
5. headline = atrRatio (수치).

## 대표 반환 형태

- `tableRef` — 1 row (atrRatio · upcomingEventCount · nextEventDays).
- `dateRef` — 마지막 거래일.

## 연계 절차

1. `engines.company` — Company(code) 진입.
2. `engines.company` — `Company.calendar(horizonDays=30)` 정기공시 cycle 추론.
3. `engines.gather` — `gather("price", code)` OHLCV + atr14 시계열.
4. `runPython` — ATR ratio + D-day 인라인 산출.
5. `recipes.technical.quantTechnicalReview` — 같은 종목 기술적 verdict 와 본 atrRatio 결합.

## 기본 검증

- atrRatio ≥ 1.20 + nextEventDays ≤ 7 동시일 때만 "공시 임박 변동성 고조" 표현.
- atrRatio 단독 > 1.20 은 다른 이벤트 (지정학 · 매크로 · 섹터) 반응일 수 있음.
- upcomingEventCount 0 이면 "공시 기반 신호 적용 불가" 명시.

## 한계

- KR DART 정기공시 cycle 추론만 (분기/반기/사업보고서). 임시공시 미포함.
- ATR14 는 표준 파라미터 — 변형 (ATR7/ATR21) 별 recipe.
- 5 vs 30 윈도우는 default — 다른 윈도우는 변형 recipe.
