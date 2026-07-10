---
id: recipes.quant.sizeFactor
title: Size 팩터 (Fama-French SMB) — log market cap percentile
category: recipes
kind: recipe
scope: builtin
status: tested
purpose: Fama-French 1992 의 Size 팩터 — log(market cap) 의 peer 단면 percentile rank. small-cap premium 측면. 단순 시총이 아닌 log 변환 후 cross-section. 트리거 — 'Size 팩터 (Fama-French SMB)', 'size factor', 'sizeFactor'.
whenToUse:
  - size 팩터
  - SMB Fama-French
  - market cap rank
  - small-cap premium
examples:
  - 005930 시총 rank — small / mid / large 어디
  - Fama-French size 팩터 — small-cap premium 상위 종목
  - log market cap cross-section 분위
expectedOutputs:
  - log(market cap) 단일값 + peer percentile
  - quartile 라벨 (small / mid / mid-large / large)
  - universe quartile 경계값 + 자기 종목 위치
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
  description: "시총 데이터 누락 회사가 절반 이상이면 percentile 결론 X. KOSPI 전체가 아닌 산업 peer 단면이므로 산업 평균 size 따라 결론 변동 — 한계 명시."
lastUpdated: "2026-05-22"
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import math

target = "005930"
c = dartlab.Company(target)

# 시가총액은 전종목 밸류에이션 스캔에서 한 번에 받는다 (종목마다 Company 를 여는 것보다 싸다).
valuation = dartlab.scan("valuation")   # 종목코드 · 종목명 · 시가총액 · PER · PBR · PSR · 배당수익률

def market_cap(code):
    row = valuation.filter(pl.col("종목코드") == code)
    if row.height == 0:
        return None
    return float(row["시가총액"][0] or 0)

own_cap = market_cap(target)
own_log_cap = math.log(own_cap) if own_cap and own_cap > 0 else None

try:
    peers = c.industry()["peers"][:20]
except Exception:
    peers = []

peer_rows = []
for p in peers:
    code = p.get("code") or p.get("stockCode")
    if not code or code == target:
        continue
    cap = market_cap(code)
    if cap and cap > 0:
        peer_rows.append({"code": code, "marketCap": cap, "logCap": math.log(cap)})

def rank(my_log_cap):
    vals = sorted([r["logCap"] for r in peer_rows])
    if not vals or my_log_cap is None:
        return None
    below = sum(1 for v in vals if v < my_log_cap)
    return below / len(vals)

# small size premium: 작을수록 rank 1
own_rank = rank(own_log_cap)
own_size_rank = (1 - own_rank) if own_rank is not None else None

table = pl.DataFrame([{
    "ownMarketCap": own_cap,
    "ownLogCap": own_log_cap,
    "peerCount": len(peer_rows),
    "ownPercentileLargeToSmall": own_rank,
    "smbRankSmallIs1": own_size_rank,
}])

emit_result(
    table=table,
    values={"marketCap": own_cap, "smbRank": own_size_rank, "peerCount": len(peer_rows)},
    date=None,
    sources=["dartlab://scan/valuation", "dartlab://industry/peers"],
)
```

## 호출 동작

### 1. 결론 도출

logMarketCap + percentile rank 단정. 예: "005930 시총 460조 (logCap=33.5) peer 20개 중 percentile=0.95 (대비 95%가 작음) → smbRankSmallIs1=0.05 → large-cap quartile (SMB premium 측면에서 unfavored). 반도체 industry peer 평균 시총 12조 — 005930 은 industry leader (size dominance)."

### 2. 핵심 근거 수집

- target market_cap (`dartlab.scan("valuation")` 의 시가총액 컬럼)
- `Company.industry()["peers"]` 상위 20 종목 × market_cap
- logCap = ln(marketCap) 변환 후 peer 단면
- percentile rank: percentileLargeToSmall = below count / N

### 3. 메커니즘 분석

```
target market_cap → log 변환
   logCap = ln(marketCap)
   원래 시총 분포가 power-law 라 log 변환 필요 (Fama-French 1992)
   ↓
peer 단면 percentile:
   peer 20 종목 logCap 정렬
   own_rank = (target 보다 작은 peer 수) / N
   ↓
SMB invert 표기 (small premium 측면):
   smbRankSmallIs1 = 1 - own_rank
   → 0.05 = 가장 큰 quartile (large-cap unfavored)
   → 0.95 = 가장 작은 quartile (small-cap favored)
   ↓
quartile 분류:
   smbRank 0.75-1.0 → small (premium 후보)
   smbRank 0.5-0.75 → mid
   smbRank 0.25-0.5 → mid-large
   smbRank 0.0-0.25 → large (premium 미해당)
```

Fama-French SMB premium — 1926-2000 US 시장에서 small minus big = +3.5%/y annual. KR 시장에서도 일부 확인 (1990-2010 강함, 2010s 약화). 산업 peer 단면이라 산업 평균 size 따라 결론 변동.

### 4. 반례·한계

- peer < 10 → percentile 불안정.
- 산업 peer 단면이라 KOSPI 전체 단면 결과 다름 (병행 트랙 필요).
- small cap = high return 단정 금지 — 2010s anomaly 약화.
- IT 산업 시총 분포 right-skewed → log 변환 후에도 outlier 영향.

### 5. 후속 모니터링

- smbRank > 0.7 (small) → `recipes.quant.qualityFactor` 로 small × quality (junk 제거).
- smbRank > 0.7 + value factor 동조 → `recipes.quant.valueFactor` 로 double sort.
- smbRank > 0.7 → `recipes.meta.screen.smallCapDiscovery` 로 small cap 발굴 트랙.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `ownMarketCap` | 본 회사 시총 |
| `ownLogCap` | log(시총) |
| `ownPercentileLargeToSmall` | peer 단면 (1 = 가장 큰) |
| `smbRankSmallIs1` | invert (1 = 가장 작은) |

## 연계 절차

1. recipes.quant.valueFactor - small + value 결합 (Fama-French double sort).
2. recipes.quant.qualityFactor - small × quality (junk 제거 후).
3. recipes.meta.screen.smallCapDiscovery - small cap 발굴 트랙.

## 기본 검증

- peer < 10 이면 percentile 불안정.
- 산업 peer 단면이라 산업 평균 size 따라 결론 변동 — KOSPI 전체 단면 별 트랙으로 추가 가능.
- small cap = high return 단정 금지 — anomaly 약화 시기 (2010s) 다수.
