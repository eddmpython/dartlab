---
id: recipes.quant.qualityFactor
title: Quality 팩터 — QMJ (Frazzini-Pedersen-Asness 2014)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: Frazzini-Pedersen-Asness 2014 "Quality Minus Junk" 의 4 축 — Profitability (ROE/ROA) + Growth (5y CAGR) + Safety (low leverage·low earnings vol) + Payout (FCF / NI) — composite z-score. junk 회사 회피용 quality screen. 트리거 — 'Quality 팩터', 'quality factor', 'qualityFactor'.
whenToUse:
  - quality 팩터
  - QMJ Asness
  - quality minus junk
  - 4 축 composite quality
examples:
  - 005930 quality 팩터 4 축 점수 (ROE / 성장 / 안정성 / 배당)
  - QMJ 상위 종목 — junk 회피 screen
  - 005930 이 quality vs junk 어디
expectedOutputs:
  - 4 축 (Profitability·Growth·Safety·Payout) 개별 z-score
  - composite QMJ z-score 단일값
  - peer percentile rank + 상위 / 하위 quartile 종목 list
linkedSkills:
  - engines.company
  - engines.quant
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
  - "engines.viz.peerMatrix"
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
    - quant
    - analysis
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
falsifier:
  description: "4 축 중 측정 가능한 게 ≤ 2 개면 composite 결론 X. peer < 8 이면 z-score 불안정."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import statistics

target = "005930"
c = dartlab.Company(target)

# 네 갈래를 전종목 스캔으로 한 번에 받는다. 종목마다 Company 를 여는 것보다 싸고, 같은 기준으로 줄 세운다.
prof = dartlab.scan("profitability")   # 종목코드 · 영업이익률 · 순이익률 · ROE · ROA · 등급
grow = dartlab.scan("growth")          # 종목코드 · 매출CAGR · 영업이익CAGR · 순이익CAGR · years
debt = dartlab.scan("debt")            # 종목코드 · 총부채 · 부채비율 · ICR · 위험등급
cash = dartlab.scan("cashflow")        # 종목코드 · 영업CF · 투자CF · 재무CF · fcf

def _one(df, code, col):
    row = df.filter(pl.col("종목코드") == code)
    return None if row.height == 0 else row[col][0]

def quality_metrics(code):
    roe = _one(prof, code, "ROE")
    roa = _one(prof, code, "ROA")
    if roe is None or roa is None:
        return None
    growth = _one(grow, code, "매출CAGR")
    de = _one(debt, code, "부채비율")           # safety: 낮을수록 좋다
    fcf = _one(cash, code, "fcf")
    return {
        "roeRoa": (float(roe) + float(roa)) / 2,
        "growth": float(growth) if growth is not None else None,
        "safety": -float(de) if de is not None else None,
        "payout": float(fcf) if fcf is not None else None,
    }

own = quality_metrics(target)
try:
    peers = c.industry()["peers"][:15]
except Exception:
    peers = []

peer_rows = []
for p in peers:
    code = p.get("code") or p.get("stockCode")
    if not code or code == target:
        continue
    m = quality_metrics(code)
    if m:
        peer_rows.append({"code": code, **m})

def z_score(metric, my_val):
    vals = [r[metric] for r in peer_rows if r[metric] is not None]
    if len(vals) < 4 or my_val is None:
        return None
    mu, sd = statistics.mean(vals), statistics.stdev(vals) if len(vals) > 1 else 0
    return (my_val - mu) / sd if sd > 0 else None

if own:
    zs = {k: z_score(k, own[k]) for k in ("roeRoa", "growth", "safety", "payout")}
    valid = [v for v in zs.values() if v is not None]
    composite = sum(valid) / len(valid) if valid else None
else:
    zs = {}
    composite = None

table = pl.DataFrame([{
    "axis": k, "ownValue": own[k] if own else None, "zScore": zs.get(k)
} for k in ("roeRoa", "growth", "safety", "payout")])

emit_result(
    table=table,
    values={"qmjComposite": composite, "peerCount": len(peer_rows)},
    date=None,
    sources=["dartlab://scan/profitability", "dartlab://scan/growth", "dartlab://scan/debt", "dartlab://scan/cashflow"],
)
```

## 호출 동작

### 1. 결론 도출

QMJ composite z-score 단일값 + 4 축 개별 z-score 단정 + peer 분위. 예: "QMJ composite z=+1.2 (top 15%) — Profit z=+0.9 / Growth z=+1.5 / Safety z=+0.3 / Payout z=+2.0 → quality 후보 confirmed."

### 2. 핵심 근거 수집

- Profitability — ROE / ROA (`dartlab.scan("profitability")`)
- Growth — 매출 CAGR (`dartlab.scan("growth")`)
- Safety — 부채비율 (`dartlab.scan("debt")`, 낮을수록 좋아 부호 반전)
- Payout — FCF (`dartlab.scan("cashflow")`)
- peer set — `Company.industry()["peers"]` (산업 cross-section)

### 3. 메커니즘 분석

```
4 축 raw 산출
   ↓
각 축 peer 단면 z-score = (own - peer_mean) / peer_std
   ↓
composite z = avg(measurable axis z-scores)
   ↓
composite z ≥ +1.0  → quality 후보 (QMJ Q1)
composite z 0 ~ +1  → mid quality
composite z < 0     → junk 후보 (QMJ Q5)
측정 가능 축 ≤ 2    → composite X (한계 표기)
```

4 축 모두 양수면 가장 강한 quality 신호. Payout z 만 높고 다른 축 낮으면 거짓 quality (배당만 높은 junk 위장).

### 4. 반례·한계

- 회계 정책 차이 (revenue recognition · depreciation) peer 비교 시 raw 비교 노이즈.
- 신규 상장 (history < 5y) Growth 측정 불가.
- 금융사 (은행·증권·보험) 의 debt/equity 정의 다름 — Safety 축 비교 의미 X.
- 일회성 이익 (자산매각 · 충당금환입) peer mean inflated.

### 5. 후속 모니터링

- composite z ≥ +1 시: `recipes.fundamental.valuation.damodaran.relativeCheck` 로 가격 검증.
- Safety z < -1 시: `recipes.fundamental.credit.usHighYieldSpread` regime 확인.
- Payout z 높음 + Growth z 낮음: `recipes.fundamental.dividend.foreignOwnershipCorr` 외인 매수 정합 확인.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `axis` | roeRoa / growth / safety / payout |
| `ownValue` | 본 회사 값 |
| `zScore` | peer 단면 z-score |

## 연계 절차

1. recipes.quant.valueFactor - QMJ junk 제거 후 value rank.
2. recipes.industry.industryStagePhase - phase 와 quality 정합.
3. recipes.fundamental.valuation.damodaran.reinvestmentRoc - quality 깊이 분석.

## 기본 검증

- peer < 8 이면 z-score 불안정 — 한계 명시.
- 4 축 중 측정 가능 ≤ 2 이면 composite X.
- 단일 ROE 로 quality 결론 금지 — 4 축 분리 표기.
