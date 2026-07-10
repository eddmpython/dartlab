---
id: recipes.fundamental.quality.workingCapitalQuality
title: 운전자본 quality (CCC + 회전율 추세 — L1 raw)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Cash Conversion Cycle (DSO + DIO − DPO) + 매출채권·재고·매입채무 회전율 5 년 추세를 L1 raw (`c.panel("BS"|"IS")`) 에서 직접 계산해 매출 신뢰도와 운전자본 효율을 정량화하는 절차. analysis axis 미사용. 트리거 — '운전자본 quality', '재고 매출채권', 'CCC 진단'.
whenToUse:
  - 운전자본 효율
  - Cash Conversion Cycle CCC
  - 매출채권 회전율
  - 재고 회전율
  - 매입채무 회전율
  - 매출 신뢰도 점검
  - 운전자본 늘어남 위험
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.quality.dupontDriver
  - recipes.fundamental.quality.earningsQualityTriad
  - recipes.fundamental.credit.distressFilter
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
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - CCC (DSO + DIO − DPO) 한 시점 결과로 영구 운전자본 efficiency 단정 금지.
  - DSO / DIO / DPO 정의 (분기 vs 연간 환산) 명시 없이 인용 금지.
  - 매출채권 회전율 단일 지표만으로 매출 신뢰도 단정 금지.
  - 산업별 정상 CCC 수준 (단순 평균) 무시한 비교 금지.
failureModes:
  - DSO 분모 (매출 / 매출원가) 정의 모호
  - 분기 환산 (×91 vs ×365 / 4) 차이
  - 매출채권 / 재고의 일회성 (M&A) 변동 미보정
  - 매입채무 (DPO) 의 국가 / 거래처 규약 차이
  - 운전자본 부채 (단기차입) 분리 누락
examples:
  - 삼성전자 CCC + 5 년 추세
  - DSO + DIO + DPO 시계열
  - 매출 신뢰도 + 운전자본 quality
  - 운전자본 + 분식 의심 결합
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

운전자본 (Working Capital) = 유동자산 − 유동부채. 그 안에서 **순운전자본 회전 사이클** 을 측정하는 framework:

- **DSO** (Days Sales Outstanding) = (매출채권 / 매출) × 365
- **DIO** (Days Inventory Outstanding) = (재고 / 매출원가) × 365
- **DPO** (Days Payables Outstanding) = (매입채무 / 매출원가) × 365
- **CCC** (Cash Conversion Cycle) = DSO + DIO − DPO. 현금이 운전자본에 묶여 있는 일수.

학술·실무 검증:
- Sloan (1996) 의 accruals anomaly — 매출채권·재고 급증이 미래 abnormal return 음(-) 예측. 본 recipe 의 변동률 분석이 그 신호.
- Dechow-Kothari-Watts (1998): CCC 단축 = 운전자본 효율 + 매출 신뢰도 동시 시그널.
- Damodaran (2007): 매출 성장보다 매출채권 성장 빠른 회사 = "매출 인식 의심" — 분식 회계 신호.

핵심 패턴:
- **DSO 급증** + 매출 성장 둔화 = 채권 미회수 누적 → 향후 손상 위험.
- **DIO 급증** + 매출 성장 둔화 = 재고 적체 → 평가손 위험.
- **DPO 급증** = 거래처 신용 활용 (현금 보전) 또는 지급 능력 약화.
- **CCC 음수** = 매입채무로 매출/재고 funding 가능 (Apple 모델, Amazon 모델).

## 공개 호출 방식

```python
import dartlab
import polars as pl

c = dartlab.Company("005930")

bs_df = c.panel("BS", freq="Y")
is_df = c.panel("IS", freq="Y")
years = ["2025", "2024", "2023", "2022", "2021"]

def fetchSeries(df: pl.DataFrame, snake: str, years: list[str]) -> list[float]:
    row = df.filter(pl.col("snakeId") == snake).select(years)
    return row.to_numpy()[0].tolist() if row.height > 0 else [0.0] * len(years)

ar = fetchSeries(bs_df, "trade_receivables", years)        # 매출채권
inv = fetchSeries(bs_df, "inventories", years)              # 재고
ap = fetchSeries(bs_df, "trade_payables", years)            # 매입채무
sales = fetchSeries(is_df, "sales", years)                  # 매출
cogs = fetchSeries(is_df, "cost_of_sales", years)           # 매출원가

rows = []
for i, y in enumerate(years):
    rows.append({
        "year": y,
        "dso": ar[i] / sales[i] * 365 if sales[i] > 0 else None,
        "dio": inv[i] / cogs[i] * 365 if cogs[i] > 0 else None,
        "dpo": ap[i] / cogs[i] * 365 if cogs[i] > 0 else None,
        "ccc": (
            (ar[i] / sales[i] * 365 if sales[i] > 0 else 0)
            + (inv[i] / cogs[i] * 365 if cogs[i] > 0 else 0)
            - (ap[i] / cogs[i] * 365 if cogs[i] > 0 else 0)
        ),
        "arGrowth": (ar[i] - ar[i+1]) / ar[i+1] * 100 if i < len(years)-1 and ar[i+1] > 0 else None,
        "salesGrowth": (sales[i] - sales[i+1]) / sales[i+1] * 100 if i < len(years)-1 and sales[i+1] > 0 else None,
        "invGrowth": (inv[i] - inv[i+1]) / inv[i+1] * 100 if i < len(years)-1 and inv[i+1] > 0 else None,
    })

quality = pl.DataFrame(rows)
quality = quality.with_columns(
    (pl.col("arGrowth") - pl.col("salesGrowth")).alias("arVsSalesGap"),
    (pl.col("invGrowth") - pl.col("salesGrowth")).alias("invVsSalesGap"),
)
```

## 호출 동작

1. `c.panel("BS" | "IS", freq="Y")` 2 회 — 5 년 wide 시계열.
2. snakeId 로 5 항목 추출 (매출채권·재고·매입채무·매출·매출원가).
3. DSO / DIO / DPO / CCC 5 기간 계산.
4. AR Growth − Sales Growth gap 계산 — 매출 신뢰도 시그널.
5. Inventory Growth − Sales Growth gap 계산 — 재고 적체 시그널.

## 대표 반환 형태

`quality : pl.DataFrame` — 컬럼:
- `year : str`
- `dso`, `dio`, `dpo : float` — 일수
- `ccc : float` — Cash Conversion Cycle
- `arGrowth`, `salesGrowth`, `invGrowth : float` — YoY %
- `arVsSalesGap : float` — AR Growth − Sales Growth (양수 = 매출보다 채권 빨리 늘어남)
- `invVsSalesGap : float` — Inventory Growth − Sales Growth (양수 = 매출보다 재고 빨리 늘어남)

## 한계

- **snakeId 가용성** — `trade_receivables`, `trade_payables` 명칭 회사별 다름. 세부 항목 (단기·장기 채권 분리) 별 처리 필요할 수 있음. fallback 으로 receivables 또는 accounts_receivable 시도.
- **금융업 부적합** — 은행·보험 BS 구조 다름 (대출채권은 trade_receivables 아님). 본 recipe 는 제조·유통·서비스 한정.
- **계절성** — 일부 산업 (의류·여행) 분기 변동 크나 본 recipe 는 연간만. 분기 시계열 분석은 별도.
- **연결 vs 별도** — 자회사 운전자본 포함 (연결). 본업 외 효과 큰 지주회사 주의.

## 한국 / 미국 시장 차이

- **한국**: 한국 제조업 평균 DSO 60-90 일, DIO 40-70 일, DPO 50-80 일 → CCC 평균 50-100 일. 자동차·반도체는 DIO 짧음 (회전율 빠름).
- **미국**: 평균 CCC 짧음 (Wal-Mart·Amazon·Costco 등 음수). 결제 사이클 더 빠르고 retail 효율 우월.

## 연계 절차

1. 본 recipe → CCC + 회전율 + AR/Inv vs Sales gap 5 년.
2. arVsSalesGap 양수 + 누적 → `recipes.fundamental.quality.earningsQualityTriad` 의 Sloan accruals 신호 점검.
3. CCC 추세 확장 → 운전자본 자금 부담 증가 → `recipes.fundamental.credit.distressFilter` 와 상호 검증.
4. DSO·DIO·DPO 동인별 변화 → `recipes.fundamental.quality.dupontDriver` 의 AssetTurnover 변동과 일치 확인.
5. 산업 평균 (반도체·소비재·통신 등) 과 비교 — 절대값 절대 직접 비교 X.

## 기본 검증

- DSO + DIO − DPO = CCC 항등식 만족 확인.
- 5 년 CCC 추세 — 안정 또는 단축 = 효율, 확장 = 위험.
- arVsSalesGap 5 년 평균 +5%p 이상 → 채권 미회수 누적 의심 신호.
- invVsSalesGap 5 년 평균 +10%p 이상 → 재고 적체 의심 신호.
- 단년도 변동 크면 사업 모델 변화 (M&A·신사업) 점검 — 비교 가능성 검증 필수.
- "CCC 음수 = 무조건 좋다" 단정 X — Walmart 모델은 plus, 일반 제조업 음수는 거래처 압박.
