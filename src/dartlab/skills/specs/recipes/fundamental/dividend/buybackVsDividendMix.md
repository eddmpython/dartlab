---
id: recipes.fundamental.dividend.buybackVsDividendMix
title: 자사주 매입 vs 배당 환원 mix
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 회사의 주주환원이 배당 단독·자사주 단독·혼합 중 어느 modus 인지 + 시점별 mix shift 가 capital allocation 의 어떤 신호 (잉여현금 정점·EPS 부양·지배구조 강화) 인지 row 단위로 분리. 단일 dividend yield 만 보는 함정 회피. analysis 격리 메우는 조합. 트리거 — '자사주 vs 배당', 'buyback vs dividend', '환원 mix'.
whenToUse:
  - 자사주 vs 배당 환원
  - buyback vs dividend mix
  - 환원 정책 shift
  - 자사주 dilution 환원
linkedSkills:
  - engines.company
  - recipes.fundamental.dividend.capitalReturn
  - recipes.fundamental.quality.forensics.treasuryStockUsage
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
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.tableBackedChart"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."
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
    - analysis
    - synth
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
expectedOutputs:
  - 연도별 배당 / 자사주 / 총환원 / FCF 표
  - mix ratio (buyback / total return) 시계열
  - shift 시점 + 동시 발생 capex / leverage 변화
failureModes:
  - 자사주 매입 결의만 보고 실제 집행 누락
  - 자사주 소각 vs 자기주식 보유 구분 미반영
  - 외환 환산 후 양·음 부호 혼동
forbidden:
  - mix shift 의 의미를 추론 라벨 (EPS 부양·지배강화) 로 단정
  - 단일 연도 mix 로 정책 결론
examples:
  - 005930 5년 자사주 vs 배당 mix
  - 자사주 매입 정점 시점 동시 capex 변화
audiences:
  llm: c.show 또는 c.analysis("capitalAllocation") + 재무제표 cf row 에서 dividends_paid·treasury_stock_acquired 두 행을 EngineCall 로 받아 연도별 mix table 을 만든다.
  agent: shift 시점 row 에 동시 capex / leverage 변화도 표기.
  human: 환원 정책이 배당 중심인지 자사주 중심인지 시계열로 본다.
humanIntro: "buybackVsDividendMix 는 dividend yield 만 보면 안 보이는 *환원 modus* 변화를 1 차 출처 (현금흐름표) 에서 row 단위로 분리한다. 자사주 매입과 배당은 같은 환원이지만 신호 함의가 다르다."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

AI 도구 실행 순서는 `EngineCall` 우선. 아래 Python 블록은 회사 현금흐름표 row 에서 배당 / 자사주 / FCF / capex 를 묶는 **RunPython fallback** 절차다.

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

try:
    rows = c.analysis("capitalAllocation").to_dicts()
except Exception:
    rows = []

# fallback: cashflow row 에서 직접
if not rows:
    try:
        cf = c.panel("cf")
        rows = cf.to_dicts() if hasattr(cf, "to_dicts") else []
    except Exception:
        rows = []

audit = []
for r in rows:
    div = float(r.get("dividends_paid") or r.get("dividendsPaid") or 0)
    buy = float(r.get("treasury_stock_acquired") or r.get("treasuryStockAcquired") or 0)
    fcf = float(r.get("free_cash_flow") or r.get("freeCashFlow") or 0)
    capex = float(r.get("capex") or r.get("capitalExpenditure") or 0)
    total_return = abs(div) + abs(buy)
    buy_ratio = abs(buy) / total_return if total_return else None
    audit.append({
        "year": r.get("year") or r.get("period"),
        "dividends": div,
        "buyback": buy,
        "totalReturn": total_return,
        "buybackRatio": buy_ratio,
        "fcfCoverage": (total_return / fcf) if fcf else None,
        "capex": capex,
    })

table = pl.DataFrame(audit) if audit else pl.DataFrame(
    schema={"year": pl.Utf8, "dividends": pl.Float64, "buyback": pl.Float64,
            "totalReturn": pl.Float64, "buybackRatio": pl.Float64,
            "fcfCoverage": pl.Float64, "capex": pl.Float64}
)

emit_result(
    table=table,
    values={"years": table.height, "lastBuybackRatio": float(table["buybackRatio"].drop_nulls().tail(1)[0]) if table["buybackRatio"].drop_nulls().len() else None},
    date=str(table["year"].max()) if table.height else None,
    sources=["dartlab://analysis/capitalAllocation", "dartlab://panel/cf"],
)
```

## 호출 동작

### 1. 결론 도출

buyback vs dividend mix shift + FCF coverage 단정. 예: "2024 buybackRatio 0.32 → 2025 0.65 (mix shift +0.33), fcfCoverage 0.78 — buyback 우선 자본배분 전환 (배당 → 자사주)."

### 2. 핵심 근거 수집

- 5년 dividends / buyback / FCF / capex 시계열 (analysis.capitalAllocation + show CF)
- buybackRatio = abs(buyback) / abs(buyback + dividends)
- fcfCoverage = (dividends + buyback) / FCF — total return / 잉여 흐름
- shift 시점 = buybackRatio 전년 대비 ±0.2 이상 변화

### 3. 메커니즘 분석

```
연도별 4 row → buybackRatio + fcfCoverage 시계열
   ↓
연도별 buybackRatio 변화 산출
   |Δ| ≥ 0.2  → mix shift 시점
   ↓
shift 시점 row 의 capex 변화 + leverage (D/E) 변화 동반 분석
   ↓
buyback ↑ + capex ↑       → 자사주 + 재투자 동시 (강한 자본 보유)
buyback ↑ + capex ↓       → 자사주 우선 (재투자 기회 부재)
dividend ↑ + buyback ↓    → 안정 배당 정책 강화
fcfCoverage > 1           → FCF 초과 자본배분 (부채 또는 현금 사용)
```

mix shift 시점이 빈번 (≥ 2 회 / 5년) = 자본배분 정책 불안정. 1 회 = phase 전환. 0 회 = 일관 정책.

### 4. 반례·한계

- buyback 자체가 회계상 자기주식 취득과 다름 — 일부 회사 (취득 후 소각) 만 비교 가능.
- FCF 정의 차이 (자유현금흐름 직접 vs 영업CF - capex) peer 비교 노이즈.
- 분기·반기 dividend (특별배당) 가 연간 합계에 비대칭 영향.
- fcfCoverage > 1 일관 시 부채 누적 신호 — 별도 leverage 점검 필요.

### 5. 후속 모니터링

- mix shift 발생 (≥ 0.2): `recipes.fundamental.dividend.payoutShiftEvent` 로 변동 원인 추적.
- fcfCoverage > 1 + 부채 ↑: `recipes.fundamental.credit.usHighYieldSpread` regime 확인.
- buyback 우선 + 주가 하락: `recipes.fundamental.dividend.foreignOwnershipCorr` 로 외인 동행 검증.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `year` | 결산 연도 |
| `dividends` | 배당금 지급액 |
| `buyback` | 자사주 매입액 |
| `totalReturn` | 배당 + 자사주 |
| `buybackRatio` | 자사주 / 총환원 |
| `fcfCoverage` | 총환원 / FCF |
| `capex` | 같은 해 capex |

## 연계 절차

1. recipes.fundamental.dividend.capitalReturn - 환원 thesis 진입.
2. recipes.fundamental.quality.forensics.treasuryStockUsage - 자사주 modus (소각 vs 보유) 분류.
3. recipes.fundamental.dividend.stressTest - 매크로 침체 시 mix 어떻게 흔들리는지.

## 기본 검증

- `totalReturn` 또는 `fcfCoverage` 누락 row 는 결론 근거가 아닌 *coverage 한계* 로만 표기.
- `buybackRatio` 가 1 연도만 튄 경우 결의·발표만 있고 집행 누락 가능성 — 다음 연도 row 와 함께 본다.
- 자사주 소각 (감자) vs 단순 자기주식 보유 구분은 본 recipe 밖. treasuryStockUsage 로 연계.
