---
id: recipes.fundamental.credit.distressFilter
title: Altman-lite 부도 위험 회피 필터 (역방향 블랙리스트)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Altman Z-Score (1968) 5 변수 중 dartlab 으로 가능한 4 변수 + 음수 영업CF 게이트 를 결합해 부도 위험 종목을 횡단으로 식별하고 다른 스크리너 결과의 블랙리스트로 사용하는 회피 절차. 트리거 — '부도 위험 필터', 'Altman Z 횡단', '블랙리스트', '회피 절차'.
whenToUse:
  - 부도 위험 회피
  - Altman Z-Score 근사
  - 재무 부실 종목 거름
  - 가치 함정 안전 가드
  - 블랙리스트 필터
  - distress signal
linkedSkills:
  - engines.scan
  - recipes.fundamental.valuation.qualityValueScreen
  - recipes.fundamental.valuation.garpScreen
  - recipes.fundamental.valuation.grahamDeepValue
  - engines.credit
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
  - "engines.viz.financialStructureCharts"
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.scenarioVisuals"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - Altman 5 변수 중 4 변수 + 음수 OCF 게이트 결과만으로 부도 단정 금지 — 학술 근사.
  - 1968 미국 표본 thresholds 를 KR 시장에 그대로 적용 금지.
  - 부도 위험 회피 필터를 매수 신호로 역해석 금지 — 회피용 블랙리스트.
  - 가치 함정 (value trap) 안전 가드 누락 시 다른 스크리너 결과 단정 금지.
failureModes:
  - X5 (Sales / TA) 변수 누락 (5 변수 중 4 변수 사용) 의 정확도 영향
  - 음수 OCF 가 일회성 (M&A) vs 반복 (영업 부실) 구분 어려움
  - 산업 (제조업 vs 비제조업) 별 Z-Score 적용성 차이
  - 분기 vs 연간 데이터 빈도 차이"
  - 외화 부채 비중 영향 미보정
examples:
  - KR 시장 Altman-lite 필터
  - 가치주 스크리너 + distress 필터 결합
  - 음수 OCF + 부채비율 + Altman 합의
  - 블랙리스트 회피 후속 검토
gap:
  primary:
    - scan
    - credit
  secondary:
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

Edward Altman, *"Financial Ratios, Discriminant Analysis and the Prediction of Corporate Bankruptcy"* (Journal of Finance, 1968): 5 변수 가중 합 Z-Score 모델. 1946-1965 미국 제조업 부도 1 년 전 80-90% 적중.

Z = 1.2·X₁ + 1.4·X₂ + 3.3·X₃ + 0.6·X₄ + 1.0·X₅

| 변수 | 정의 | dartlab 가능? |
|---|---|---|
| X₁ | working capital / total assets | ◯ (account 직접) |
| X₂ | retained earnings / total assets | ◯ (account 직접) |
| X₃ | EBIT / total assets | ◯ (operating_profit / total_assets) |
| X₄ | market value of equity / book value of total liabilities | ✗ (시총 시계열 결합 어려움) |
| X₅ | sales / total assets | ◯ (totalAssetTurnover) |

본 recipe 는 X₄ 제외 + 음수 영업CF 게이트 추가. 정확한 Z-Score 계산 대신 **회피용 블랙리스트** (역방향 스크리너) 로 사용.

해석:
- Z &gt; 2.99 = 안전 (Safe Zone)
- 1.81 ≤ Z ≤ 2.99 = 회색 (Grey Zone)
- Z &lt; 1.81 = 위험 (Distress Zone)

본 recipe 는 다른 스크리너 (qualityValue, garp, graham) 결과에서 distress 종목을 빼는 데 우선. 단독 사용 시 부도 위험 종목 식별 가능.

## 공개 호출 방식

```python
import dartlab
import polars as pl

# 1) 부도 위험 게이트 — 부채 200% 이상 + 유동성 1.0 이하 + CFO 음수
distress = dartlab.scan("screen", spec={"where": [
    {"field": "finance.ratio.debtRatio", "op": ">=", "value": 200},
    {"field": "finance.ratio.currentRatio", "op": "<=", "value": 1.0},
    {"field": "finance.ratio.operatingCfMargin", "op": "<", "value": 0},
]})

# 2) 추가 시그널 — 3 년 연속 순이익 적자 (Altman X₂ retained earnings 약화 신호)
ni = dartlab.scan("account").select(
    ["stockCode", "2025", "2024", "2023"]
)
loss3y = ni.with_columns(
    pl.all_horizontal([pl.col(y) < 0 for y in ["2025","2024","2023"]]).alias("loss3y")
).filter(pl.col("loss3y"))

# 3) 블랙리스트 = 게이트 OR 3 년 적자
blacklist = pl.concat([
    distress.select("stockCode"),
    loss3y.select("stockCode"),
]).unique()

# 4) 다른 스크리너 결과에서 빼기
def excludeDistress(df: pl.DataFrame, blacklist: pl.DataFrame) -> pl.DataFrame:
    return df.join(blacklist.with_columns(pl.lit(True).alias("_distress")), on="stockCode", how="left").filter(pl.col("_distress").is_null()).drop("_distress")
```

## 호출 동작

1. `scan("screen", spec=...)` — 부채 200% + 유동성 1.0 이하 + CFO 음수 (3 게이트 동시 통과 = 위험).
2. `scanAccount("net_income", freq="Y")` — 3 기간 (2023-2025) 컬럼.
3. `pl.all_horizontal` — 3 년 모두 음수만 필터.
4. union — 게이트 OR 3 년 적자 = 블랙리스트.
5. `excludeDistress()` 헬퍼 — 다른 스크리너 결과에서 anti-join.

## 대표 반환 형태

`distress : pl.DataFrame` — 부도 위험 후보:
- `stockCode`, `corpName`
- `finance.ratio.debtRatio : float` (≥ 200%)
- `finance.ratio.currentRatio : float` (≤ 1.0)
- `finance.ratio.operatingCfMargin : float` (음수)

`loss3y : pl.DataFrame` — 3 년 연속 적자:
- `stockCode`, 3 기간 net_income (모두 음수)

`blacklist : pl.DataFrame` — `stockCode` 단일 컬럼.

## 한계

- **X₄ 부재 (시총/총부채)** — 정확한 Z-Score 직접 X. 본 recipe 는 4/5 변수 근사 + CFO 추가.
- **금융업 부적합** — 은행·보험 부채비율 자연히 높음 (수신·보험금). 본 recipe 결과에서 금융업 별도 제외 필요 (`scan("fields")` 의 industry 필터 활용).
- **사이클 산업 일시 적자** — 조선·반도체 다운사이클 1-2 년 적자 정상. 3 년 연속 적자만 가져와서 일시 적자 회피.
- **임계값 (200% / 1.0 / 음수) 은 보수적 절대치** — 산업별 분포 차이 큼. 산업 percentile 기반 게이트 확장 가능.
- **Altman Z 자체 한계** — 1968 미국 제조업 모델. 한국 KOSPI 적용 검증 적음. 본 recipe 는 회피 신호 강도만 신뢰, 점수 절대값 X.

## 한국 / 미국 시장 차이

- **한국**: chaebol 계열사 상호지급보증·연결 회계로 단순 부채비율 200% 가 항상 위험 X. 단 비계열 중소 제조업에서는 강한 시그널.
- **미국**: 원전 검증 시장. 부채비율 평균 낮음 (S&P 500 약 80%). 200% 임계는 한국 보다 강한 시그널.

## 연계 절차

1. 본 recipe 로 블랙리스트 생성 — `blacklist` DataFrame.
2. 다른 스크리너 (`qualityValueScreen`, `garpScreen`, `grahamDeepValue`, `piotroskiLite`) 결과에서 `excludeDistress()` 호출.
3. 단독 사용 시 — 위험 종목 명단 자체로 `engines.credit` 신용 위험 심층 분석 input.
4. `engines.analysis` — CFO·FCF·이자보상배율 시계열로 위험 강도 정량화.
5. `engines.story` 로 위험 narrative — 단순 "위험" X, 어떤 사이클·산업 구조·자본정책 으로 부도 시나리오 까지.

## 기본 검증

- 블랙리스트 종목 수 — 30-100 개가 정상 (KOSPI 1-4%). 200 개 초과 = 게이트 너무 강함 (200% → 250% 등 완화).
- 외부 신용평가 비교 — KIS·NICE 등급 BB 이하 종목과 본 블랙리스트 교집합 80% 이상이어야 검증.
- 게이트 통과 (3 게이트) 와 3 년 적자 후보가 분리될 수 있음 — union 시 두 집합 합집합.
- 일시 충격 (코로나·금융위기 등 매크로 사이클) 영향 종목은 본 recipe 통과 시 별도 회복 시나리오 검토.
- "Altman Z 0.5 = 부도 확정" 단정 X — 위험 신호이지 부도 예측 X.
