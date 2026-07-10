---
id: recipes.fundamental.credit.leverageSensitivity
title: 영업·재무 레버리지 민감도 (DOL/DFL/DCL — L1 raw)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 매출 변동이 영업이익·순이익에 얼마나 증폭되는지 영업레버리지 (DOL) · 재무레버리지 (DFL) · 결합레버리지 (DCL) 로 정량화하고 매크로 충격 시나리오에서 본 회사가 얼마나 민감한지 평가하는 절차. L1 raw (`c.panel("IS")`) 시계열만 사용. 트리거 — '영업레버리지', '재무레버리지', 'DOL DFL DCL', '매크로 충격 민감도'.
whenToUse:
  - DOL 영업레버리지
  - DFL 재무레버리지
  - DCL 결합레버리지
  - 매출 변동 민감도
  - 사이클 회사 위험
  - 매크로 충격 시나리오
  - 고정비 비중
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.quality.dupontDriver
  - recipes.fundamental.credit.distressFilter
  - recipes.fundamental.credit.distressDual
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
  - DOL / DFL / DCL 단일 시점 결과로 영구 민감도 단정 금지 — 시계열 + 사이클 위치 동반.
  - VC / FC 분리 추정 가정 명시 없이 DOL 단정 금지 — 회계 데이터 한계.
  - 매출 변동 시나리오 (10% / 20%) 명시 없이 결합레버리지 결과 인용 금지.
  - 적자 (음수 OP) 시점에 DCL 무한대 무시 금지.
failureModes:
  - VC vs FC 분리 (회계상 모호) 의 추정 의존성
  - 단년도 DOL 의 사이클성 종목 변동성"
  - 외화 부채 비중에 따른 DFL 환율 영향 미반영
  - 일회성 손익 (M&A) 영향 미보정
  - 사이클 위치 (호황 / 불황) 별 DOL 차이"
examples:
  - 삼성전자 DOL / DFL / DCL 시계열
  - 사이클 회사 (반도체) 레버리지 민감도
  - 매크로 충격 시나리오 + DCL
  - 매출 -20% 시 순이익 영향
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

레버리지 분석은 corporate finance 기본 — 매출 변동이 이익에 어떻게 증폭되는지 측정.

- **DOL** (Degree of Operating Leverage) = % ΔOP / % ΔSales = (Sales − VC) / (Sales − VC − FC). 고정비 비중 클수록 DOL 큼 — 매출 1% 변동 → 영업이익 N% 변동.
- **DFL** (Degree of Financial Leverage) = % ΔNI / % ΔOP = OP / (OP − Interest). 이자비용 비중 클수록 DFL 큼.
- **DCL** (Degree of Combined Leverage) = DOL × DFL = % ΔNI / % ΔSales. 매출 1% 변동 → 순이익 N% 변동.

학술 검증:
- Mandelker-Rhee (1984): DOL × DFL 가 stock beta 에 직접 영향. 고-DCL 회사가 system risk 높음.
- Dugan-Shriver (1992): DOL 표준 추정 — 5 년 회귀법 (% ΔOP = α + β × % ΔSales). 본 recipe 의 추정 방법.
- Faff-Brooks (1998): 사이클 회사 (조선·반도체·정유) 의 DCL 평균 3-5, 안정 회사 (통신·소비재) 1-1.5.

매크로 충격 시뮬레이션:
- 매출 −10% 충격 시 영업이익 = −10% × DOL, 순이익 = −10% × DCL.
- 침체 시나리오 (매출 -20%) 에서 ROE 가 어떻게 변할지 직접 추정.

## 공개 호출 방식

```python
import dartlab
import polars as pl
import numpy as np

c = dartlab.Company("005930")

is_df = c.panel("IS", freq="Y")
years = ["2025", "2024", "2023", "2022", "2021"]

def fetchSeries(df: pl.DataFrame, snake: str, years: list[str]) -> list[float]:
    row = df.filter(pl.col("snakeId") == snake).select(years)
    return row.to_numpy()[0].tolist() if row.height > 0 else [0.0] * len(years)

sales = fetchSeries(is_df, "sales", years)
op = fetchSeries(is_df, "operating_profit", years)
ni = fetchSeries(is_df, "net_income", years)
interest = fetchSeries(is_df, "interest_expense", years)

# 1) 회귀 추정 — % ΔOP / % ΔSales (5 년 시계열)
salesPct = [(sales[i] - sales[i+1]) / sales[i+1] for i in range(len(sales)-1) if sales[i+1] != 0]
opPct = [(op[i] - op[i+1]) / op[i+1] for i in range(len(op)-1) if op[i+1] != 0]
niPct = [(ni[i] - ni[i+1]) / ni[i+1] for i in range(len(ni)-1) if ni[i+1] != 0]

dolRegression = np.polyfit(salesPct, opPct, 1)[0] if len(salesPct) >= 2 else None
dclRegression = np.polyfit(salesPct, niPct, 1)[0] if len(salesPct) >= 2 else None

# 2) 단년도 algebraic (가장 최근)
dolAlgebraic = (op[0] / sales[0]) and ((op[0] - op[1]) / op[1]) / ((sales[0] - sales[1]) / sales[1]) if sales[1] != 0 and op[1] != 0 else None
dflAlgebraic = op[0] / (op[0] - abs(interest[0])) if (op[0] - abs(interest[0])) != 0 else None
dclAlgebraic = (dolAlgebraic or 0) * (dflAlgebraic or 0)

# 3) 매크로 충격 시나리오
shocks = [-0.20, -0.10, -0.05, 0.05, 0.10, 0.20]
scenarios = []
for shock in shocks:
    scenarios.append({
        "salesShockPct": shock * 100,
        "opChangePct": shock * (dolRegression or 0) * 100,
        "niChangePct": shock * (dclRegression or 0) * 100,
        "salesProjected": sales[0] * (1 + shock),
        "opProjected": op[0] * (1 + shock * (dolRegression or 0)),
        "niProjected": ni[0] * (1 + shock * (dclRegression or 0)),
    })

leverageTable = pl.DataFrame({
    "metric": ["DOL_regression", "DOL_algebraic", "DFL_algebraic", "DCL_regression", "DCL_algebraic"],
    "value": [dolRegression, dolAlgebraic, dflAlgebraic, dclRegression, dclAlgebraic],
})
scenarioTable = pl.DataFrame(scenarios)
```

## 호출 동작

1. `c.panel("IS", freq="Y")` — 5 년 손익계산서.
2. snakeId 로 4 항목 추출 (sales, operating_profit, net_income, interest_expense).
3. DOL / DCL — 5 년 회귀 추정 (`np.polyfit` 1 차).
4. DFL — 단년도 algebraic (OP / (OP − |Interest|)).
5. 매크로 충격 시나리오 — 매출 ±5%, ±10%, ±20% 시 OP / NI 추정.

## 대표 반환 형태

`leverageTable : pl.DataFrame`:
- `metric : str` — 5 metric 이름
- `value : float`

`scenarioTable : pl.DataFrame`:
- `salesShockPct : float` — −20% ~ +20%
- `opChangePct`, `niChangePct : float` — DOL/DCL 곱한 추정 변화율
- `salesProjected`, `opProjected`, `niProjected : float` — 절대값 추정

## 한계

- **`interest_expense` snakeId 가용성** — 한국 일부 회사 IS 에서 영업외비용 통합 표기. 별도 추출 필요.
- **회귀 5 점** — 5 년 시계열로 1 차 회귀 신뢰성 약함. 분기 시계열 (20 점) 권장하나 본 recipe 는 연간 표준.
- **단년도 algebraic 노이즈** — 단년도 % ΔOP/% ΔSales 가 1 회 사이클 시 무한대. 회귀 추정 우선.
- **DOL 정의 변형** — `(Sales − VC) / (Sales − VC − FC)` 정의는 변동비/고정비 분리 필요. dartlab 에서 직접 X — 회귀 + algebraic 으로만 추정.
- **시나리오 선형성 가정** — DOL 큰 회사도 매출 −50% 같은 극단 충격에서는 비선형 (적자 전환). 본 recipe 시나리오 ±20% 한정.

## 한국 / 미국 시장 차이

- **한국**: 사이클 산업 (조선·반도체·정유·해운) 비중 큼. KOSPI 200 평균 DCL 약 2.5 (S&P 500 의 1.5 대비). 본 recipe 가 한국 시장에서 특히 의미.
- **미국**: 서비스·플랫폼 회사 비중 커 평균 DCL 낮음. 다만 IT (반도체·하드웨어) 회사 사이클 효과 강함.

## 연계 절차

1. 본 recipe → DOL/DFL/DCL + 시나리오 표.
2. DCL &gt; 3 = 사이클 회사 → 매크로 시나리오 (`recipes.fundamental.credit.distressDual` 의 침체 가정) 와 결합.
3. DOL 변동 → 고정비 구조 변화 (CAPEX 사이클·M&A 효과) 점검.
4. DFL 큰 회사 → `recipes.fundamental.credit.distressFilter` 의 부채비율·유동성 게이트 강화.
5. ROE 변동의 5 동인 (`recipes.fundamental.quality.dupontDriver`) 중 financialLeverage 변화와 DFL 변화 일치 검증.

## 기본 검증

- DOL × DFL ≈ DCL 항등식 (algebraic) 5%p 이내 일치 확인.
- 회귀 R² 점검 — 0.7 이하면 5 년 회귀 신뢰성 낮음 (회사 사이클 큼 또는 외부 충격).
- DOL 5 이상 + DFL 2 이상 → DCL 10 이상 — 매출 −10% 시 NI −100% (적자 전환) 위험.
- 시나리오는 *추정* — 실제 충격 시 비선형 효과 (적자 시 세금 환급, 운영 효율 변화 등) 별도.
- "DCL 1.5 = 안전" 단정 X — 산업 평균 (회사가 속한 산업 평균 DCL) 대비로 해석.
