---
id: recipes.fundamental.valuation.usEquityDcfShortcut
title: 미국 equity DCF shortcut (US 10y rf + Damodaran ERP)
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 미국 종목 DCF 의 *축약 진입* — risk-free = US 10y treasury, ERP = Damodaran 마지막 implied ERP, beta = 5y monthly regression, growth = 5y EPS CAGR. 한국 KR rf/ERP 와 분리해 *US 시장 기본값* 사용.
whenToUse:
  - 미국 종목 DCF
  - US equity valuation
  - Damodaran ERP US
  - US rf 10y
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.macro
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
    - macro
    - analysis
testUniverse:
  market: US
  tickers:
    - "AAPL"
    - "MSFT"
falsifier:
  description: "ERP / rf raw 누락 시 결론 X. 단일 DCF 결과만 노출 X — base/bull/bear 3 path 또는 sensitivity 동행."
lastUpdated: "2026-05-22"
---

## 공개 호출 방식

```python
import dartlab
import polars as pl

ticker = "AAPL"
c = dartlab.Company(ticker, market="US")

try:
    rf = dartlab.macro.seriesFetch("DGS10").to_dicts()[-1]
    rf_value = float(rf.get("value") or 0) / 100  # percent → ratio
except Exception:
    rf_value = None

# Damodaran implied ERP (US, monthly)
try:
    erp = dartlab.macro.referenceFetch("damodaran_us_erp")
    erp_value = float(erp.get("erp", 0))
except Exception:
    erp_value = 0.05  # historical avg fallback

try:
    beta_meta = c.panel("riskMetrics").to_dicts()[0]
    beta = float(beta_meta.get("beta5y") or 1.0)
except Exception:
    beta = 1.0

try:
    eps_rows = c.panel("eps").to_dicts()
    if len(eps_rows) >= 5 and float(eps_rows[-5].get("eps") or 0) > 0:
        eps_growth_5y = (float(eps_rows[-1].get("eps") or 1) / float(eps_rows[-5].get("eps") or 1)) ** (1/5) - 1
    else:
        eps_growth_5y = None
except Exception:
    eps_growth_5y = None

cost_of_equity = (rf_value + beta * erp_value) if rf_value is not None else None
terminal_growth = min(rf_value, 0.03) if rf_value is not None else 0.025

# simple gordon growth as shortcut
try:
    latest_eps = float(c.panel("eps").to_dicts()[-1].get("eps") or 0)
except Exception:
    latest_eps = None

fair_value = None
if latest_eps and cost_of_equity and eps_growth_5y is not None:
    next_eps = latest_eps * (1 + eps_growth_5y)
    if cost_of_equity > terminal_growth:
        fair_value = next_eps / (cost_of_equity - terminal_growth)

table = pl.DataFrame([{
    "rf": rf_value,
    "erp": erp_value,
    "beta": beta,
    "costOfEquity": cost_of_equity,
    "eps5yGrowth": eps_growth_5y,
    "terminalGrowth": terminal_growth,
    "fairValueShortcut": fair_value,
}])

emit_result(
    table=table,
    values={"fairValue": fair_value, "costOfEquity": cost_of_equity},
    date=None,
    sources=["dartlab://macro/fred/DGS10", "dartlab://reference/damodaran_us_erp"],
)
```

## 호출 동작

US 10y treasury (rf) + Damodaran US implied ERP + 5y beta → cost of equity. EPS 5y CAGR → next EPS. Gordon growth shortcut (next_eps / (cost - g)) 로 fair value 산출. *축약* 임을 명시.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `rf` | US 10y rf |
| `erp` | Damodaran US ERP |
| `beta` | 5y monthly beta |
| `costOfEquity` | rf + beta·ERP |
| `eps5yGrowth` | EPS 5y CAGR |
| `fairValueShortcut` | Gordon 식 fair value |

## 연계 절차

1. recipes.fundamental.valuation.damodaran.fcffDcf - 풀 FCFF DCF 로 확장.
2. recipes.macro.usYieldCurveRegime - rf regime 변화 시 가치 재산출.

## 기본 검증

- rf / ERP raw 누락 시 결론 X.
- 단일 shortcut 결과만 노출 X — base/bull/bear 3 path 또는 sensitivity grid 동행 권장.
- *fair value* = 매수 매도 결정 단정 X — DCF 가정 sensitivity 와 함께 본다.
