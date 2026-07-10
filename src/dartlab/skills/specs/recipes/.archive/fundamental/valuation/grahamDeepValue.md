---
id: recipes.fundamental.valuation.grahamDeepValue
title: Graham deep value 안전마진 스크리닝 (PBR + 유동성 + 저레버리지)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Benjamin Graham (1949) 안전마진 framework 을 ratio 4 게이트 + 5 년 흑자 후처리로 근사해 한국 chaebol discount 트랩을 회피한 deep value 후보를 횡단으로 발굴하는 절차. 트리거 — 'Graham deep value', '안전마진', 'chaebol discount 회피'.
whenToUse:
  - Graham deep value
  - 안전마진 스크리닝
  - PBR 1 이하 안전 종목
  - 저레버리지 가치주
  - 5 년 흑자 자산주
  - 가치 함정 회피
linkedSkills:
  - engines.scan
  - recipes.fundamental.valuation.qualityValueScreen
  - recipes.fundamental.credit.distressFilter
  - recipes.fundamental.quality.piotroskiLite
  - engines.analysis
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
  - "engines.viz.scenarioVisuals"
  - "engines.viz.tableBackedChart"
  - "engines.viz.priceChart"
visualGuidance:
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "가격·수급 반응은 engines.viz.priceChart로만 그리며 OHLCV 기간·벤치마크·latestAsOf가 맞지 않으면 본문 차트로 쓰지 않는다."

forbidden:
  - PBR ≤ 1 한 게이트만으로 가치 매력 단정 금지 — 4 게이트 + 5 년 흑자 동반.
  - chaebol discount 의 안전마진 trap 회피 누락 금지 — 지주사 / 자회사 평가 분리.
  - Graham 1949 미국 표본 thresholds 를 KR 시장에 그대로 적용 금지.
  - 회계상 청산가치 (PBR) 와 실제 청산가치의 차이 무시 금지.
failureModes:
  - 한국 지주사 (holding) 의 PBR 디스카운트 + 자회사 가치 합산 차이
  - Current Ratio 의 산업 (금융업 vs 제조업) 적합성 차이
  - 5 년 흑자 후처리의 사이클성 종목 부적합
  - 유동자산 - 부채 (NCAV) 음수일 때 deep value 정의 모호
  - 자기자본 비중 게이트의 산업별 정상 수준 차이
examples:
  - KR 시장 Graham deep value 후보
  - PBR ≤ 1 + 유동성 + 저레버리지
  - 5 년 흑자 + 안전마진
  - chaebol discount 회피 검증
gap:
  primary:
    - scan
    - analysis
lastUpdated: '2026-05-13'
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
---

## 학술 근거

Benjamin Graham, *The Intelligent Investor* (1949) + *Security Analysis* (1934, with Dodd): **Margin of Safety** — 시장가 &lt; 본질가치 와 자본구조 안전성 동시 요구. 핵심 게이트:

1. **PBR ≤ 1.0** — 시장가 ≤ 장부가 (회계상 청산가치 안전마진).
2. **Current Ratio ≥ 2.0** — 단기 부채 대비 유동자산 2 배 이상 (유동성 안전).
3. **Debt Ratio ≤ 50%** — 자본 대비 부채 1:1 이내 (레버리지 안전).
4. **5 년 흑자** — 사이클 전체 생존성 검증.

학술 검증:
- Lakonishok-Shleifer-Vishny (1994): 저-PBR 가치주 1968-90 미국 연 17.3% vs 성장주 9.3%.
- Chan-Hamao-Lakonishok (1991): 일본 시장 동일 효과 — 저-PBR + 높은 매출/주가 결합 우월.
- 한국: 단순 저-PBR 은 chaebol discount 함정 → Graham 의 4 게이트 결합으로 함정 회피.

dartlab 한계: 진정한 NCAV (Net Current Asset Value) 계산은 `(currentAssets - totalLiabilities) × 2/3` 가 marketCap 보다 커야 하는데 시가총액 시계열 직접 결합 어려움 → 본 recipe 는 PBR 게이트로 근사. NCAV 계산은 `engines.scan` 로 별도 후속 단계.

## 공개 호출 방식

```python
import dartlab
import polars as pl

# 1) 4 게이트 동시 통과
safe = dartlab.scan("screen", spec={"where": [
    {"field": "valuation.pbr", "op": "<=", "value": 1.0},
    {"field": "finance.ratio.currentRatio", "op": ">=", "value": 2.0},
    {"field": "finance.ratio.debtRatio", "op": "<=", "value": 50},
    {"field": "finance.ratio.netMargin", "op": ">", "value": 0},
]})

# 2) 5 년 흑자 후처리 — net_income freq="Y" 5 기간 모두 양수
ni = dartlab.scan("account").select(
    ["stockCode", "2025", "2024", "2023", "2022", "2021"]
)
profit5y = ni.with_columns(
    pl.all_horizontal([pl.col(y) > 0 for y in ["2025","2024","2023","2022","2021"]]).alias("profit5y")
).filter(pl.col("profit5y"))

# 3) Join → 4 게이트 + 5 년 흑자 동시 통과 deep value
candidates = (
    safe.join(profit5y.select(["stockCode"]), on="stockCode")
    .sort("valuation.pbr")
)
```

## 호출 동작

1. `scan("screen", spec=...)` — PBR 1.0 + currentRatio 2.0 + debtRatio 50% + netMargin 양수 4 게이트.
2. `scanAccount("net_income", freq="Y")` — 5 기간 (2021-2025) 컬럼 wide 테이블.
3. `pl.all_horizontal` — 5 년 모두 양수만 필터.
4. join — 4 게이트 통과 + 5 년 흑자 교집합.
5. PBR 오름차순 정렬 — 가장 저평가 우선.

## 대표 반환 형태

`candidates : pl.DataFrame` — 컬럼:
- `stockCode`, `corpName`
- `valuation.pbr : float` — PBR (≤ 1.0)
- `valuation.per : float`
- `finance.ratio.currentRatio : float` — 유동비율
- `finance.ratio.debtRatio : float` — 부채비율
- `finance.ratio.netMargin : float` — 순이익률
- 별도 5 년 net_income 컬럼은 후처리 join 시 보존 가능

## 한계

- **NCAV 직접 계산 X** — Graham 원전 net-net 공식은 `(cash + 0.75·AR + 0.5·Inv − totalLiab) × 2/3` 가 marketCap 보다 커야 한다. 본 recipe 는 PBR 게이트로 근사. 정확한 NCAV 는 `scanAccount` 4 항목 (현금·매출채권·재고·총부채) 결합 + 시가총액 join 별 단계.
- **PBR 1.0 임계는 한국 시장 평균 부근** — 너무 느슨. 진정 deep value 는 PBR 0.7 이하 가능. 단계적 임계 (PBR 0.7 / 0.8 / 1.0) 권장.
- **5 년 흑자만 봄** — 사이클 회사 (조선·반도체) 부분 적자도 정상 가능. 산업별 적용 한계 명시.
- **금융업 부채비율 게이트 부적합** — 은행·보험·증권은 부채비율 1000% 일상. 본 recipe 결과에서 금융업 별도 분리 권장.

## 한국 / 미국 시장 차이

- **한국**: KOSPI 평균 PBR ≈ 1.0, KOSDAQ ≈ 1.5. 본 게이트 (PBR 1.0) 통과 종목 풀 약 800-1000 개. 그중 chaebol governance discount 종목 다수 → 실제 deep value 식별 어려움. 4 게이트 + 5 년 흑자 결합으로 약 50-150 개 후보 좁힘.
- **미국**: S&P 500 평균 PBR ≈ 4. PBR 1.0 통과 종목 풀 매우 작음. Russell 2000 (소형주) 에서 본 framework 효과 강함 — 1968-90 백테스트의 본 시장.

## 연계 절차

1. 본 recipe 로 후보 발굴 → `tableRef` 에 4 게이트 + 5 년 흑자 분포.
2. 상위 후보에 대해 NCAV 정확 계산 — `scanAccount` 로 cash·AR·inventory·totalLiabilities 가져와서 시가총액 join.
3. `recipes.fundamental.quality.piotroskiLite` 의 F-Score 추가 검증 (가치 함정 회피 강화).
4. `recipes.fundamental.credit.distressFilter` 로 부도 위험 거름.
5. `engines.analysis` 의 DCF + valuation band — 본질가치 산출.
6. `engines.story` 로 narrative — 사이클 위치, 산업 구조, 자본정책 (배당·자사주) 까지.

## 기본 검증

- 후보 수 — 4 게이트 + 5 년 흑자 모두 통과 50-150 개가 정상.
- 산업 분포 — 한 산업 (제조업·금융) 80% 이상 = 산업 편향. 게이트 조정 또는 산업별 별도 적용.
- PBR 분포 — 중앙값 0.7-0.85 면 진짜 deep value 풀.
- 흑자 일관성 외에 영업이익 일관성 추가 점검 권장 (본 recipe 는 net_income 만).
- 회사가 PBR 낮은 *이유* 검증 필수 — chaebol 계열 deep discount, 사업부 매각 가치 등 정성 분석 필수.
