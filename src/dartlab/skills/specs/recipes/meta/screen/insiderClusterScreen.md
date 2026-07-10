---
id: recipes.meta.screen.insiderClusterScreen
title: Insider Cluster Screen — 180 일 ≥ 3 명 매수
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 내부자 매수 cluster 스크린 — 직전 180 일 동안 ≥ 3 명 임원/주요주주 매수 신고 종목. Cohen-Malloy-Pomorski 2012 + Lakonishok-Lee 2001 학술. 트리거 — '내부자 매수', 'insider cluster', '임원 매수', '주요주주 매수', 'insider buying'.
whenToUse:
  - 내부자 매수
  - insider cluster
  - 임원 매수
  - 주요주주 매수
  - insider buying
  - 5% 보고
  - insider signal
linkedSkills:
  - engines.scan
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
  - engines.viz.tableBackedChart
visualGuidance:
  - "insider 매수 list 는 engines.viz.tableBackedChart — buyer 컬럼 + 매수일 시계열 정렬."
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
  description: KOSPI 전체 universe 180 일 동안 cluster ≥ 3 종목 0 건 = 데이터 수집 실패 (정상 시장에서 월 평균 5~15 종목 expectable).
  pythonCheck: |
    assert n_cluster >= 3
expectedNovelty:
  - buyerCount
  - totalShares
  - clusterDate
forbidden:
  - 내부자 매수 = 절대 매수 신호 X — 학술 alpha 는 평균 ~3-6%/연 (lag 큼).
  - 단일 매수 (1 명) 신호 약함 — cluster (≥ 3 명) 신호만 본 recipe 대상.
  - insider 매도 cluster 는 noise 큼 (옵션 행사 / 상속 / 분산 매도) — 별 recipe 트랙.
failureModes:
  - DART 임원/주요주주 5% 보고 timing lag (D+5).
  - 단일 주주의 다회 매수가 cluster 로 잘못 분류 — buyer unique 강행.
  - 자사주 매입 / 분리과세 / 옵션 행사는 자율 매수 아님 — 사유 필터.
examples:
  - KOSPI 180 일 cluster ≥ 3 종목 (주 1 회)
  - 보유 종목 cluster 매수 알람
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
lookback = asof - timedelta(days=180)

# 1. 임원/주요주주 매수 전수 수집 (DART 5% 보고 + 임원변동)
insider_buys = dartlab.gather("insiderTrade",
                              market="KR",
                              direction="buy",
                              start=lookback.isoformat(),
                              end=asof.isoformat())
# → DataFrame: stockCode · buyer · shares · price · date · reason

# 2. 자율 매수 필터 (옵션 행사 / 상속 / 자사주 매입 제외)
filtered = insider_buys.filter(
    pl.col("reason").is_in(["voluntary_purchase", "open_market"])
)

# 3. cluster 집계 (unique buyer ≥ 3)
cluster = (
    filtered.group_by("stockCode")
    .agg([
        pl.col("buyer").n_unique().alias("buyerCount"),
        pl.col("shares").sum().alias("totalShares"),
        pl.col("date").max().alias("lastBuyDate"),
    ])
    .filter(pl.col("buyerCount") >= 3)
    .sort("buyerCount", descending=True)
)

emit_result(
    table=cluster,
    values={"n_cluster": len(cluster)},
    date=asof.isoformat(),
    sources=["dartlab://gather/insiderTrade", "DART 5% 보고"],
)
```

## 호출 동작

### 1. 결론 도출

180 일 동안 ≥ 3 명 임원/주요주주 자율 매수 발생 종목 universe — 내부자 정보 비대칭 signal.

### 2. 핵심 근거 수집

- `dartlab.gather("insiderTrade", direction="buy")` — DART 5% 보고 + 임원변동 collect
- buyer unique 카운트 (1 명 다회 ≠ cluster)
- 자율 매수 필터 (옵션/상속/자사주 제외)

### 3. 메커니즘 분석

```
DART 5% 보고 + 임원변동 collect
   ↓
direction=buy 필터
   ↓
reason 필터 (voluntary_purchase / open_market 만)
   ↓
group_by stockCode → buyer.n_unique()
   ↓
buyerCount ≥ 3 filter
   ↓
buyerCount desc 정렬 (강한 cluster 먼저)
```

### 4. 반례·한계

- DART 보고 timing lag (D+5).
- 학술 alpha ~3-6%/연 — 절대 매수 신호 아님.
- buyer 정의 차이 (배우자/특수관계인 포함 시 cluster 인플레이션).
- short-term return 부재 (lag 평균 6-12 개월).

### 5. 후속 모니터링

- cluster universe → `recipes.fundamental.disclosure.insiderEarningsLeading` (실적 예고 결합).
- buyer 분석 → 임원 직급 (CEO/CFO/사외이사) 별 신호 강도.
- 매수 가격 분석 → 평균 매수가 vs 현재 가격 (margin of safety).

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `stockCode : str` · `corpName : str`
- `buyerCount : int` (≥ 3)
- `totalShares : int`
- `lastBuyDate : str` — YYYY-MM-DD

## 연계 절차

1. 본 recipe → 180 일 cluster ≥ 3 universe.
2. cluster 종목 → `recipes.fundamental.disclosure.insiderEarningsLeading` (Q+1 실적 surprise 결합).
3. 매수 사유 분석 → `Company.filings()` 필터 (5% 보고 본문).
4. 산업 cluster 패턴 → `recipes.industry.sectorMomentumLeadership` 결합.
5. 주 1 회 재실행 → 신규 cluster 진입 종목 알람.
