---
id: recipes.quant.valueFactor
title: Value 팩터 composite (Fama-French B/M + E/P + CF/P)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: Fama-French 1992 의 Value 팩터를 B/M (Book/Market) + E/P (Earnings yield) + CF/P (Cash flow yield) 3 정의 평균으로 composite 산출. 단일 회사 + peer set percentile rank. 단일 지표 (PER 단독) 함정 회피. 트리거 — 'Value 팩터 composite (Fama-French B/M + E/P + CF/P)', 'value factor', 'valueFactor'.
whenToUse:
  - value 팩터
  - B/M E/P CF/P composite
  - Fama-French value
  - 가치주 rank
examples:
  - 005930 value 팩터 composite 어디
  - Fama-French value 상위 종목 (B/M + E/P + CF/P)
  - 가치주 cross-section rank — PER 단독 함정 회피
expectedOutputs:
  - B/M · E/P · CF/P 각각 단일값
  - composite z-score (3 정의 평균) + percentile rank
  - peer 상위 quartile 종목 list
linkedSkills:
  - engines.company
  - engines.quant
  - engines.scan
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
    - company
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
falsifier:
  description: "3 정의 부호가 갈리면 (B/M 높은데 E/P 음수) composite 결론 X. peer < 10 이면 percentile rank 불안정."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

# 밸류 지표는 전종목 스캔에서 한 번에 받는다. PER·PBR 의 역수가 각각 earnings yield · book-to-market.
valuation = dartlab.scan("valuation")   # 종목코드 · 종목명 · 시가총액 · PER · PBR · PSR · 배당수익률

def value_metrics(code):
    row = valuation.filter(pl.col("종목코드") == code)
    if row.height == 0:
        return None
    per = float(row["PER"][0] or 0)
    pbr = float(row["PBR"][0] or 0)
    psr = float(row["PSR"][0] or 0)
    return {
        "bm": 1 / pbr if pbr > 0 else 0,    # book-to-market
        "ep": 1 / per if per > 0 else 0,    # earnings yield
        "sp": 1 / psr if psr > 0 else 0,    # sales yield
    }

own = value_metrics(target)
try:
    peers = c.industry()["peers"][:20]
except Exception:
    peers = []

peer_rows = []
for p in peers:
    code = p.get("code") or p.get("stockCode")
    if not code or code == target:
        continue
    m = value_metrics(code)
    if m:
        peer_rows.append({"code": code, **m})

# percentile rank — 각 정의별로
def rank(metric, my_val):
    vals = sorted([r[metric] for r in peer_rows if r[metric] is not None])
    if not vals or my_val is None:
        return None
    below = sum(1 for v in vals if v < my_val)
    return below / len(vals)

if own:
    rank_bm = rank("bm", own["bm"])
    rank_ep = rank("ep", own["ep"])
    rank_sp = rank("sp", own["sp"])
    ranks = [r for r in (rank_bm, rank_ep, rank_sp) if r is not None]
    composite = sum(ranks) / len(ranks) if ranks else None
else:
    rank_bm = rank_ep = rank_sp = composite = None

table = pl.DataFrame([{
    "metric": "valueComposite",
    "ownBm": own["bm"] if own else None,
    "ownEp": own["ep"] if own else None,
    "ownSp": own["sp"] if own else None,
    "rankBm": rank_bm,
    "rankEp": rank_ep,
    "rankSp": rank_sp,
    "composite": composite,
    "peerCount": len(peer_rows),
}])

emit_result(
    table=table,
    values={"composite": composite, "peerCount": len(peer_rows)},
    date=None,
    sources=["dartlab://scan/valuation", "dartlab://industry/peers"],
)
```

## 호출 동작

### 1. 결론 도출

value composite rank 단정 (0~1, 1 = 가장 cheap). 예: "B/M peer rank 0.82, E/P 0.78, CF/P 0.65 → composite 0.75 (top quartile) → value 후보 강함."

### 2. 핵심 근거 수집

- 회사 market cap + 재무 BS·IS·CF (Company.panel)
- B/M (Book/Market) = 자본 / 시총
- E/P (Earnings yield) = 순이익 / 시총
- CF/P (Cash flow yield) = 영업CF / 시총
- peer set 단면 분포

### 3. 메커니즘 분석

```
재무제표 → 3 yield 정의
   B/M = totalEquity / marketCap
   E/P = netIncome / marketCap
   CF/P = operatingCF / marketCap
   ↓
peer 단면 분포에서 percentile rank (오름차순)
   rank_BM = (own_BM > peer_BM 카운트) / peer_count   (1=가장 cheap)
   rank_EP = (own_EP > peer_EP 카운트) / peer_count
   rank_CFP = (own_CFP > peer_CFP 카운트) / peer_count
   ↓
composite = (rank_BM + rank_EP + rank_CFP) / 3
   composite ≥ 0.75  → cheap value 후보 (top quartile)
   0.25-0.75         → fair value
   composite < 0.25  → expensive (bottom quartile)
```

3 정의 동시 cheap = 강한 value 신호 (단일 지표 PER 함정 회피). E/P 만 높고 B/M·CF/P 낮으면 일회성 이익 (value trap) 위험.

### 4. 반례·한계

- 적자 회사 (E/P 음수) 의 E/P 분위 의미 X — earnings normalized 필요.
- 자본잠식 회사 B/M 음수 — peer 비교에서 outlier.
- 금융사 valuation 정의 다름 (P/PreProvisionPPnR 등) — 비교 무의미.
- IFRS / GAAP 차이로 자본 raw 비교 노이즈.

### 5. 후속 모니터링

- composite ≥ 0.75: `recipes.quant.qualityFactor` 로 quality 동행 확인 (cheap + high quality = value 후보).
- composite ≥ 0.75 + Quality z < 0: value trap 후보 — `recipes.fundamental.quality.forensics.deepDive` 회계 fact check.
- composite < 0.25 + momentum 강함: growth 후보 — `recipes.fundamental.valuation.damodaran.growthFeasibility` 로 성장 정합 확인.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `ownBm/Ep/Cfp` | 본 회사 3 정의 값 |
| `rankBm/Ep/Cfp` | peer 단면 percentile (0~1) |
| `composite` | 3 rank 평균 |
| `peerCount` | peer 표본 |

## 연계 절차

1. recipes.quant.qualityFactor - value × quality 결합 (Asness QMJ junk 제거).
2. recipes.fundamental.valuation.damodaran.peerMultipleDecomposition - 단순 multiple 함정 검증.
3. recipes.industry.industryStagePhase - phase 와 value rank 정합.

## 기본 검증

- peer < 10 이면 percentile rank 불안정 — 한계 명시.
- E/P < 0 (적자) 회사는 EP 정의 제외, 나머지 2 로만 composite.
- 단일 정의 (PER 단독) 결론 금지 — 3 정의 분리 표기.
