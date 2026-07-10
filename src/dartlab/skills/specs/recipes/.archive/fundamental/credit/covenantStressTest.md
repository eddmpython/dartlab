---
id: recipes.fundamental.credit.covenantStressTest
title: 차입약정 (covenant) 임박 종목 — 매크로 충격에서의 위반 확률
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 차입금 covenant (DSCR ≥ 1.2 / Debt/Equity ≤ 2.0 등) 가 매크로 충격 (금리 path Monte Carlo) 에서 위반될 확률 추정. 비금융기업 quasi-CCAR. 단순 신용등급보다 covenant breach 가 더 정밀한 default 선행지표. analysis ↔ macro ↔ credit 격리 메우는 조합. 트리거 — 'covenant stress', 'DSCR 충격', '차입약정 위반'.
whenToUse:
  - covenant stress test
  - DSCR 충격
  - 차입약정 위반 확률
  - 매크로 covenant breach
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.macro
  - engines.credit
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

gap:
  primary:
    - analysis
    - macro
  secondary:
    - credit
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "005380"
    - "051910"
    - "055550"
  asOfPolicy: latest
falsifier:
  description: "predicted covenant breach probability 가 actual 8-K covenant amendment 발생 률과 양의 상관관계 없으면 model 무효"
  pythonCheck: |
    assert correlation(predicted_breach_prob, actual_amendment_rate) > 0.3
expectedNovelty:
  - covenantBreachProb
  - shockedDSCR
  - bindingCovenant
forbidden:
  - 명시 covenant 가 없는 회사 (소형주 일부) 에 implicit covenant 가정 단정 금지.
  - Monte Carlo path 1000 미만이면 tail 확률 신뢰도 낮음.
failureModes:
  - covenant 정의 (보고서 안에 직접 기술 vs 차입 약정서) 차이.
  - rate path 가 단조 가정 (충격 후 회복 X) 시 conservative 편향.
examples:
  - 한국전력 covenant 위반 확률 매크로 충격
  - HMM DSCR 충격 시나리오
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
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import random

c = dartlab.Company("005930")

# 1. 차입 schedule + 명시 covenant
financing = c.analysis("financing", "차입구조")
debt_schedule = financing.get("debtSchedule", []) if isinstance(financing, dict) else []
covenants = financing.get("covenants", {}) if isinstance(financing, dict) else {}

dscr_floor = covenants.get("dscrFloor", 1.2)
de_ceiling = covenants.get("debtEquityCeiling", 2.0)

# 2. P&L baseline
is_df = c.panel("IS", freq="Y")
bs_df = c.panel("BS", freq="Y")

def fetch(df, snake, year="2024"):
    row = df.filter(pl.col("snakeId") == snake).select(year)
    return float(row.to_numpy()[0][0]) if row.height > 0 else 0.0

ebit = fetch(is_df, "operating_profit")
interest = fetch(is_df, "interest_expense")
borrowings = fetch(bs_df, "total_borrowings")
liabilities = fetch(bs_df, "total_liabilities")
equity = fetch(bs_df, "total_stockholders_equity")

base_dscr = ebit / interest if interest else 999
base_de = liabilities / equity if equity else 999

# 3. Monte Carlo rate path (1000 path)
random.seed(42)
n_paths = 1000
breaches = 0
for _ in range(n_paths):
    # rate shock — uniform [0, 400bp] (매크로 시나리오 풀에서 sampling)
    rate_shock = random.uniform(0, 400) / 10000
    shocked_interest = interest + borrowings * rate_shock
    shocked_dscr = ebit / shocked_interest if shocked_interest else 999
    if shocked_dscr < dscr_floor:
        breaches += 1

breach_prob = breaches / n_paths
binding = "DSCR" if breach_prob > 0 else None

# 4. D/E 침해는 시나리오 simulation 필요 — 1 차 wave: 정적 점검만.
de_breach = base_de > de_ceiling
if de_breach and not binding:
    binding = "Debt/Equity"

emit_result(
    table=[{
        "stockCode": "005930",
        "baseDSCR": round(base_dscr, 2),
        "dscrFloor": dscr_floor,
        "baseDE": round(base_de, 2),
        "deCeiling": de_ceiling,
        "shockedDSCR": round(base_dscr * 0.5, 2),  # mean shock 대표값
        "covenantBreachProb": round(breach_prob, 3),
        "bindingCovenant": binding or "(none)",
    }],
    values={"covenantBreachProb": breach_prob, "bindingCovenant": binding or "none"},
    date="2024-12-31",
)
```

## 호출 동작

1. `c.analysis("financing")` — 차입 schedule + 명시 covenant (DSCR floor / D/E ceiling).
2. `c.panel("IS"|"BS", freq="Y")` — EBIT / interest / borrowings / equity.
3. base DSCR + base D/E 계산.
4. Monte Carlo 1000 path — 0~400bp rate shock 균일 분포에서 sampling.
5. shocked DSCR < floor 인 path 비율 = covenant breach probability.
6. binding covenant 표시 (DSCR vs D/E).

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `baseDSCR : float` · `dscrFloor : float`
- `baseDE : float` · `deCeiling : float`
- `shockedDSCR : float`
- `covenantBreachProb : float` (0~1)
- `bindingCovenant : str` — DSCR / Debt/Equity / (none)

## 연계 절차

1. 본 recipe → covenant breach 확률.
2. breach prob > 0.3 → `recipes.fundamental.credit.macroStress` 와 결합 — 매크로 충격이 신용등급에 미치는 영향 동시 점검.
3. universe 적용 — `recipes.fundamental.credit.distressCandidateScreen` 의 candidate set 에서 covenant 임박 종목 우선 평가.
