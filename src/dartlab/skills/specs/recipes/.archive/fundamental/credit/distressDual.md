---
id: recipes.fundamental.credit.distressDual
title: 부도 위험 2 모델 합의 (Altman Z″ + Ohlson O — L1 raw)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: 단일 회사 부도 위험을 Altman Z″-Score (1968 비제조업 변형) + Ohlson O-Score (1980 logit) 2 학술 모델 동시 적용으로 합의 평가. analysis axis 와 credit 엔진 미사용, L1 raw (`c.panel("BS"|"IS"|"CF")`) 만 사용. 트리거 — 'Altman + Ohlson', '부도 위험 2 모델 합의', 'Z-Score O-Score'.
whenToUse:
  - Altman Z-Score 부도 위험
  - Ohlson O-Score 부도 logit
  - 2 모델 합의 부도 위험
  - 비제조업 신용 위험
  - 재무 부실 단일 회사
  - 신용 위험 학술 검증
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.credit.distressFilter
  - recipes.fundamental.quality.earningsQualityTriad
  - recipes.fundamental.credit.leverageSensitivity
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

forbidden:
  - Altman Z″ 단일 지표만으로 부도 위험 단정 금지 — Ohlson O 합의 동반.
  - 1968 / 1980 미국 표본 thresholds 를 KR 시장에 그대로 적용 금지.
  - 제조업 Z-Score 와 비제조업 Z″-Score 혼용 금지.
  - 부도 확률 (probability) 점추정 단언 금지 — 신뢰구간 동반.
failureModes:
  - 산업 (제조업 / 비제조업 / 금융업) 별 모델 적합성 차이 무시
  - 1980 미국 logit (Ohlson) thresholds 의 KR reproducibility
  - 분기 vs 연간 데이터 빈도 차이"
  - 회계 정책 변경 (정책 자발적) 시점 영향 미보정
  - working capital 정의 (총 vs 영업) 차이
examples:
  - 삼성전자 Altman Z″ + Ohlson O 합의
  - 비제조업 신용 위험 평가
  - 2 모델 의견 일치 vs 불일치
  - 부도 확률 + 신뢰구간
gap:
  primary:
    - gather
    - credit
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

### 1. Altman Z″-Score (1995, 비제조업 / 신흥시장 변형)
Edward Altman, *"Predicting Financial Distress of Companies: Revisiting the Z-Score and ZETA Models"* — 원전 Z-Score (1968) 의 비제조업 / 신흥시장 변형:

Z″ = 6.56·X1 + 3.26·X2 + 6.72·X3 + 1.05·X4

| 변수 | 정의 |
|---|---|
| X1 | working capital / total assets |
| X2 | retained earnings / total assets |
| X3 | EBIT / total assets |
| X4 | book value of equity / total liabilities |

해석:
- Z″ &gt; 2.60 = 안전 (Safe Zone)
- 1.10 ≤ Z″ ≤ 2.60 = 회색 (Grey Zone)
- Z″ &lt; 1.10 = 위험 (Distress Zone)

원전 Z-Score 의 X5 (Sales/Assets) 제거 → 비제조업 (서비스·금융·플랫폼) 부적합 해소.

### 2. Ohlson O-Score (1980)
James Ohlson, *"Financial Ratios and the Probabilistic Prediction of Bankruptcy"* (Journal of Accounting Research):

O = −1.32 − 0.407·SIZE + 6.03·TLTA − 1.43·WCTA + 0.076·CLCA − 1.72·OENEG − 2.37·NITA − 1.83·FUTL + 0.285·INTWO − 0.521·CHIN

| 변수 | 정의 |
|---|---|
| SIZE | log(total assets / GNP price-level index) |
| TLTA | total liabilities / total assets |
| WCTA | working capital / total assets |
| CLCA | current liabilities / current assets |
| OENEG | 1 if total liabilities &gt; total assets else 0 |
| NITA | net income / total assets |
| FUTL | funds from operations / total liabilities |
| INTWO | 1 if net loss past 2 years else 0 |
| CHIN | (NIt − NIt−1) / (\|NIt\| + \|NIt−1\|) |

확률 = 1 / (1 + exp(−O)). &gt; 0.5 = 부도 의심.

학술 검증:
- 원전 검증: Altman Z 1 년 전 80-90%, 2 년 전 72%. Ohlson O 96% (1970s).
- Begley-Ming-Watts (1996): 시간 경과로 두 모델 모두 정확도 70-80% 로 하락. *합의* 사용 시 false positive 감소.
- Hillegeist 등 (2004): Z + O + Merton 동시 사용 가장 우월.

## 공개 호출 방식

```python
import dartlab
import polars as pl
import math

c = dartlab.Company("005930")

bs_df = c.panel("BS", freq="Y")
is_df = c.panel("IS", freq="Y")
cf_df = c.panel("CF", freq="Y")
years = ["2025", "2024", "2023", "2022", "2021"]

def fetchSeries(df: pl.DataFrame, snake: str, years: list[str]) -> list[float]:
    row = df.filter(pl.col("snakeId") == snake).select(years)
    return row.to_numpy()[0].tolist() if row.height > 0 else [0.0] * len(years)

ca = fetchSeries(bs_df, "current_assets", years)
cl = fetchSeries(bs_df, "current_liabilities", years)
ta = fetchSeries(bs_df, "total_assets", years)
re = fetchSeries(bs_df, "retained_earnings", years)
liab = fetchSeries(bs_df, "total_liabilities", years)
equity = fetchSeries(bs_df, "total_stockholders_equity", years)
op = fetchSeries(is_df, "operating_profit", years)
ni = fetchSeries(is_df, "net_income", years)
cfo = fetchSeries(cf_df, "cash_flow_from_operations", years)

# Altman Z″
def altmanZpp(i: int) -> float:
    wc = ca[i] - cl[i]
    return 6.56 * (wc / ta[i]) + 3.26 * (re[i] / ta[i]) + 6.72 * (op[i] / ta[i]) + 1.05 * (equity[i] / liab[i])

zpp = [altmanZpp(i) for i in range(len(years))]

# Ohlson O
def ohlsonO(i: int) -> float:
    if i + 1 >= len(years):
        return None
    size = math.log(ta[i] / 1.0)  # GNP deflator 단순화 — 절대 수치 비교용
    tlta = liab[i] / ta[i]
    wcta = (ca[i] - cl[i]) / ta[i]
    clca = cl[i] / ca[i] if ca[i] > 0 else 99
    oeneg = 1 if liab[i] > ta[i] else 0
    nita = ni[i] / ta[i]
    futl = cfo[i] / liab[i] if liab[i] > 0 else 0
    intwo = 1 if (ni[i] < 0 and ni[i+1] < 0) else 0
    chin = (ni[i] - ni[i+1]) / (abs(ni[i]) + abs(ni[i+1])) if (abs(ni[i]) + abs(ni[i+1])) > 0 else 0
    return (-1.32 - 0.407 * size + 6.03 * tlta - 1.43 * wcta + 0.076 * clca
            - 1.72 * oeneg - 2.37 * nita - 1.83 * futl + 0.285 * intwo - 0.521 * chin)

oScores = [ohlsonO(i) for i in range(len(years)-1)]
oProbs = [1 / (1 + math.exp(-o)) if o is not None else None for o in oScores]

dual = pl.DataFrame({
    "year": years[:-1],
    "altmanZpp": zpp[:-1],
    "altmanZone": ["Safe" if z > 2.6 else "Grey" if z > 1.1 else "Distress" for z in zpp[:-1]],
    "ohlsonO": oScores,
    "ohlsonProb": oProbs,
    "ohlsonFlag": [(p > 0.5) if p is not None else None for p in oProbs],
}).with_columns(
    pl.when((pl.col("altmanZone") == "Distress") & pl.col("ohlsonFlag"))
    .then(pl.lit("HighRisk"))
    .when((pl.col("altmanZone") == "Distress") | pl.col("ohlsonFlag"))
    .then(pl.lit("OneModelRisk"))
    .otherwise(pl.lit("Safe"))
    .alias("consensus")
)
```

## 호출 동작

1. `c.panel("BS" | "IS" | "CF", freq="Y")` 3 회.
2. snakeId 로 9 raw 항목 추출.
3. Altman Z″ — 4 변수 가중합, 5 점 시계열.
4. Ohlson O — 9 변수 logit, 5 점 중 4 점 시계열 (CHIN 변수가 전년 NI 필요).
5. 합의 — Altman Distress + Ohlson Flag 둘 다 = HighRisk, 하나만 = OneModelRisk, 둘 다 통과 = Safe.

## 대표 반환 형태

`dual : pl.DataFrame` — 컬럼:
- `year : str`
- `altmanZpp : float` — Z″-Score
- `altmanZone : str` — Safe / Grey / Distress
- `ohlsonO : float` — O-Score
- `ohlsonProb : float` — 부도 확률 0~1
- `ohlsonFlag : bool` — 확률 &gt; 0.5
- `consensus : str` — HighRisk / OneModelRisk / Safe

## 한계

- **Ohlson SIZE 변수의 GNP 디플레이터** — 원전은 미국 GNP price-level. 한국 적용 시 GDP 디플레이터 또는 절대 수치 비교 (본 recipe 단순화).
- **Z″ 임계 (2.6 / 1.1)** — 원전 미국 검증. 한국 KOSPI 분포는 평균 Z″ 약 3.0 — 임계 조정 가능.
- **두 모델 모두 1960-1980 미국 데이터 검증** — 시간 경과로 정확도 하락 (현재 70-80%). 절대값 신호 약함.
- **금융업 부적합** — 은행·보험·증권 BS 구조 다름 (수신·보험금 = 부채). 본 recipe 결과 별 해석.
- **`retained_earnings` snakeId 가용성** — 일부 회사 BS 에서 자본 항목 분리 안 됨.

## 한국 / 미국 시장 차이

- **한국**: chaebol 상호지급보증·연결 회계 영향. 단순 BS 부채비율 큰 회사도 위험 X. 한국 KIS·NICE 신용평가와 본 모델 합의 검증 필요.
- **미국**: 학술 검증 본 시장. SOX 이후 분식 통제 강화로 부도 1 년 전 신호 정확도 하락. 사기 회피 (Enron 외) 보다 사이클 부도 (자동차·소매) 더 잘 잡음.

## 연계 절차

1. 본 recipe → 5 년 Z″ + O-Score + consensus.
2. consensus = HighRisk 회사 → `engines.credit` (L2 분석 엔진) 와 비교 — 본 recipe 는 raw 직접 계산, credit 엔진은 7 축 종합.
3. `recipes.fundamental.quality.earningsQualityTriad` 와 결합 — 분식 의심 + 부도 위험 = 강한 회피.
4. `recipes.fundamental.credit.leverageSensitivity` 와 결합 — DCL 큰 회사가 distressed 면 매크로 충격 시 적자 전환 임박.
5. `recipes.fundamental.credit.distressFilter` 의 횡단 블랙리스트와 본 recipe 의 단일 회사 결과 교차 검증.

## 기본 검증

- 5 년 시계열 추세 — 단년도 위험보다 추세 변화 (Safe → Grey → Distress) 가 강한 신호.
- Altman + Ohlson 합의 시 false positive 줄어듦. 단독 사용 시 70-80%, 합의 시 90% 이상.
- 외부 신용평가 (KIS·NICE) 등급 BB- 이하와 본 consensus = HighRisk 교집합 80% 이상이어야 검증.
- 단년도 일시 충격 (코로나·금융위기) 종목은 본 recipe 통과해도 회복 시나리오 별 점검.
- "Z″ = 0.5 = 부도 확정" 단정 X — 통계적 신호. 정성 정보 (산업 사이클·경영진 교체·M&A 가능성) 결합 필수.
