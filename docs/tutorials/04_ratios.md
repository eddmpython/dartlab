---
title: "4. Ratios"
---

# 4. 재무비율 — 숫자에서 의미로

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb)

시계열 데이터가 있으면 재무비율을 계산할 수 있다. DartLab은 6개 카테고리, 30+ 비율을 자동으로 계산한다.

**두 가지 모드:**
1. `Company.ratios` — 최신 단일 시점 (TTM + 최신 잔액)
2. `calcRatioSeries()` — 연도별 시계열 (추세 분석용)

**6개 카테고리:**
- 수익성 (8개): ROE, ROA, 영업이익률, 순이익률, 매출총이익률, EBITDA마진, 매출원가율, 판관비율
- 안정성 (7개): 부채비율, 유동비율, 당좌비율, 자기자본비율, 이자보상배율, 순차입금비율, 비유동비율
- 성장성 (6개): 매출성장률, 영업이익성장률, 순이익성장률, 자산성장률, 자본성장률, 3년 CAGR
- 효율성 (4개): 총자산회전율, 재고자산회전율, 매출채권회전율, 매입채무회전율
- 현금흐름 (5개): FCF, 영업CF마진, 영업CF/순이익, CAPEX비율, 배당성향
- 밸류에이션 (5개): PER, PBR, PSR, EV/EBITDA, 시가총액 (시가총액 필요)

---

## 준비

```python
from dartlab import Company

c = Company("005930")
```

---

## 재무비율 객체

`Company.ratios` property로 재무비율 객체를 받는다.

```python
r = c.ratios
```

내부적으로 `timeseries`에서 시계열을 가져와 TTM(최근 4분기 합산)과 최신 잔액으로 비율을 계산한다. property이므로 처음 접근할 때 계산하고 이후 캐싱된다.

`ratios`가 `None`이면 해당 기업의 재무 데이터가 부족한 것이다.

```python
r = c.ratios
if r is None:
    print("재무비율 계산 불가")
```

---

## 수익성 지표 (8개)

기업이 벌어들인 돈에서 얼마나 남겼는가를 측정한다.

### ROE (Return on Equity, 자기자본이익률)

**당기순이익 ÷ 자기자본 × 100**

주주가 투자한 자본 대비 얼마를 벌었는지 보여준다. 투자자 입장에서 가장 중요한 수익성 지표 중 하나다.

```python
print(f"ROE: {r.roe:.1f}%")
```

| ROE 범위 | 일반적 해석 |
|----------|------------|
| 15%+ | 우수 |
| 10~15% | 양호 |
| 5~10% | 보통 |
| 5% 미만 | 부진 |

> ROE가 높다고 무조건 좋은 건 아니다. 부채를 많이 써서 자본이 작으면 ROE가 인위적으로 높아질 수 있다. 반드시 부채비율과 함께 본다.

### ROA (Return on Assets, 총자산이익률)

**당기순이익 ÷ 총자산 × 100**

전체 자산을 얼마나 효율적으로 활용하는지 보여준다.

```python
print(f"ROA: {r.roa:.1f}%")
```

### 영업이익률

**영업이익 ÷ 매출액 × 100**

본업에서의 수익성이다. 이자, 세금, 일회성 항목을 제외한 순수 영업 성과를 보여준다.

```python
print(f"영업이익률: {r.operatingMargin:.1f}%")
```

| 업종 | 영업이익률 참고 |
|------|----------------|
| 반도체 | 20~40% (경기에 따라 변동 큼) |
| 소비재 | 5~15% |
| 건설 | 3~8% |
| 유통 | 1~5% |

### 순이익률

**당기순이익 ÷ 매출액 × 100**

```python
print(f"순이익률: {r.netMargin:.1f}%")
```

영업이익률과의 차이가 크면 이자비용, 환차손, 일회성 비용이 큰 것이다.

### 매출총이익률 (Gross Margin)

**매출총이익 ÷ 매출액 × 100**

원가를 제외한 순수 마진이다. 높을수록 가격결정력이 강하다.

```python
if r.grossMargin:
    print(f"매출총이익률: {r.grossMargin:.1f}%")
```

### EBITDA 마진

**(영업이익 + 감가상각비 추정) ÷ 매출액 × 100**

설비투자가 큰 기업의 수익성을 비교할 때 유용하다. 감가상각비는 유형자산×5% + 무형자산×10%으로 추정한다.

```python
if r.ebitdaMargin:
    print(f"EBITDA 마진: {r.ebitdaMargin:.1f}%")
```

### 매출원가율

**매출원가 ÷ 매출액 × 100**

```python
if r.costOfSalesRatio:
    print(f"매출원가율: {r.costOfSalesRatio:.1f}%")
```

매출총이익률과 합치면 100%다. 원가율이 높으면 가격경쟁이 치열하거나 원자재 비중이 큰 업종이다.

### 판관비율

**판매관리비 ÷ 매출액 × 100**

```python
if r.sgaRatio:
    print(f"판관비율: {r.sgaRatio:.1f}%")
```

판관비에는 인건비, 마케팅비, 연구개발비, 감가상각비 등이 포함된다.

---

## 안정성 지표 (7개)

기업의 재무 건전성, 즉 "얼마나 안전한가"를 측정한다.

### 부채비율

**부채총계 ÷ 자기자본 × 100**

자기 돈 대비 빌린 돈의 비율이다.

```python
print(f"부채비율: {r.debtRatio:.1f}%")
```

| 부채비율 | 일반적 해석 |
|----------|------------|
| 100% 미만 | 안정적 |
| 100~200% | 보통 |
| 200% 초과 | 주의 필요 |

> 업종별로 적정 수준이 다르다. 건설업은 200%가 정상이고, IT업은 100%도 높은 편이다.

### 유동비율

**유동자산 ÷ 유동부채 × 100**

1년 이내에 갚아야 할 빚을 1년 이내에 현금화할 수 있는 자산으로 감당할 수 있는지 보여준다.

```python
print(f"유동비율: {r.currentRatio:.1f}%")
```

| 유동비율 | 의미 |
|----------|------|
| 200%+ | 여유로움 |
| 100~200% | 적정 |
| 100% 미만 | 단기 유동성 위험 |

### 당좌비율 (Quick Ratio)

**(유동자산 - 재고자산) ÷ 유동부채 × 100**

유동비율에서 재고자산을 제외한 보수적인 유동성 지표다. 재고를 바로 현금화하기 어려운 업종에서 유용하다.

```python
if r.quickRatio:
    print(f"당좌비율: {r.quickRatio:.1f}%")
```

### 자기자본비율

**자기자본 ÷ 총자산 × 100**

총자산 중 자기 돈이 차지하는 비율이다. 부채비율의 역(逆)개념.

```python
if r.equityRatio:
    print(f"자기자본비율: {r.equityRatio:.1f}%")
```

### 이자보상배율

**영업이익 ÷ 이자비용**

영업이익으로 이자를 몇 번 갚을 수 있는지 보여준다. 1배 미만이면 이자도 못 내는 상태다.

```python
if r.interestCoverage:
    print(f"이자보상배율: {r.interestCoverage:.1f}배")
```

| 이자보상배율 | 해석 |
|-------------|------|
| 3배+ | 안정적 |
| 1~3배 | 주의 |
| 1배 미만 | 위험 |

### 순차입금비율

**순차입금 ÷ 자기자본 × 100**

순차입금 = 단기차입금 + 장기차입금 + 사채 - 현금성자산. 음수면 보유 현금이 차입금보다 많다는 뜻 (무차입 경영).

```python
if r.netDebtRatio is not None:
    print(f"순차입금비율: {r.netDebtRatio:.1f}%")
```

### 비유동비율

**비유동자산 ÷ 자기자본 × 100**

장기자산을 자기 돈으로 얼마나 감당하는지 보여준다. 100% 초과면 비유동자산 취득에 타인 자본을 쓰고 있다는 뜻이다.

```python
if r.noncurrentRatio:
    print(f"비유동비율: {r.noncurrentRatio:.1f}%")
```

---

## 효율성 지표 (4개)

자산을 얼마나 효율적으로 활용하는지 보여준다.

### 총자산회전율

**매출액 ÷ 총자산**

자산 1원당 얼마의 매출을 올리는지 보여준다. 높을수록 자산 활용이 효율적이다.

```python
if r.totalAssetTurnover:
    print(f"총자산회전율: {r.totalAssetTurnover:.2f}회")
```

### 재고자산회전율

**매출액 ÷ 재고자산**

재고가 1년에 몇 번 회전하는지 보여준다. 높을수록 재고 관리가 효율적이다.

```python
if r.inventoryTurnover:
    print(f"재고자산회전율: {r.inventoryTurnover:.1f}회")
```

### 매출채권회전율

**매출액 ÷ 매출채권**

외상 매출을 얼마나 빨리 회수하는지 보여준다.

```python
if r.receivablesTurnover:
    print(f"매출채권회전율: {r.receivablesTurnover:.1f}회")
```

### 매입채무회전율

**매출원가 ÷ 매입채무**

원재료 등의 외상 대금을 얼마나 빨리 지급하는지 보여준다.

```python
if r.payablesTurnover:
    print(f"매입채무회전율: {r.payablesTurnover:.1f}회")
```

---

## 현금흐름 지표 (5개)

이익은 회계상 숫자이고, 현금흐름은 실제로 들어오고 나간 돈이다. 이익이 나도 현금이 부족하면 부도가 난다.

### FCF (Free Cash Flow, 잉여현금흐름)

**영업활동 현금흐름 - CAPEX**

영업에서 벌어들인 현금 중 설비투자를 빼고 남은 돈이다.

```python
if r.fcf:
    print(f"FCF: {r.fcf/1e8:,.0f}억원")
```

FCF가 지속적으로 마이너스라면 영업에서 버는 것보다 투자에 더 많이 쓰고 있다는 뜻이다.

### 영업CF 마진

**영업활동 현금흐름 ÷ 매출액 × 100**

영업이익률과 비교하면 이익의 현금 전환 품질을 알 수 있다.

```python
if r.operatingCfMargin:
    print(f"영업CF 마진: {r.operatingCfMargin:.1f}%")
```

### 영업CF / 순이익

**영업활동 현금흐름 ÷ 당기순이익 × 100**

100%보다 높으면 이익 이상으로 현금이 들어오고 있다는 뜻이다. 감가상각비가 큰 기업은 200% 이상이 정상이다.

```python
if r.operatingCfToNetIncome:
    print(f"영업CF/순이익: {r.operatingCfToNetIncome:.1f}%")
```

### CAPEX 비율

**|CAPEX| ÷ 매출액 × 100**

매출 대비 설비투자 비중이다. 반도체처럼 장치산업은 20% 이상이 일반적이다.

```python
if r.capexRatio:
    print(f"CAPEX 비율: {r.capexRatio:.1f}%")
```

### 배당성향

**|배당금지급| ÷ 당기순이익 × 100**

순이익 중 몇 %를 배당으로 지급하는지 보여준다.

```python
if r.dividendPayoutRatio:
    print(f"배당성향: {r.dividendPayoutRatio:.1f}%")
```

---

## 성장성 지표 (6개)

```python
if r.revenueGrowth3Y:
    print(f"매출 3년 CAGR: {r.revenueGrowth3Y:.1f}%")
```

시계열 모드(`calcRatioSeries`)에서는 연도별 YoY 성장률도 제공한다:
- `revenueGrowth`: 매출 YoY 성장률
- `operatingProfitGrowth`: 영업이익 YoY 성장률
- `netProfitGrowth`: 순이익 YoY 성장률
- `assetGrowth`: 총자산 YoY 성장률
- `equityGrowthRate`: 자기자본 YoY 성장률

---

## 원시 데이터

비율 계산에 사용된 원시 값도 함께 제공한다.

```python
if r.revenueTTM:
    print(f"TTM 매출:     {r.revenueTTM/1e8:,.0f}억원")
if r.operatingIncomeTTM:
    print(f"TTM 영업이익: {r.operatingIncomeTTM/1e8:,.0f}억원")
if r.netIncomeTTM:
    print(f"TTM 순이익:   {r.netIncomeTTM/1e8:,.0f}억원")
if r.totalAssets:
    print(f"총자산:       {r.totalAssets/1e8:,.0f}억원")
if r.totalEquity:
    print(f"자기자본:     {r.totalEquity/1e8:,.0f}억원")
```

---

## 시계열 모드 — 추세 분석

단일 시점 비율만으로는 기업의 방향을 알 수 없다. 연도별 추세를 보면 "개선 중인지, 악화 중인지"를 판단할 수 있다.

```python
from dartlab.engines.dart.finance.pivot import buildAnnual
from dartlab.engines.common.finance.ratios import calcRatioSeries

annual = buildAnnual("005930")
if annual:
    aSeries, aYears = annual
    rs = calcRatioSeries(aSeries, aYears)

    print(f"연도: {rs.years}")
    print()
    for year, roe, margin in zip(rs.years, rs.roe, rs.operatingMargin):
        print(f"  {year}: ROE {roe or '-':>6}%  영업이익률 {margin or '-':>6}%")
```

시계열로 볼 수 있는 비율 목록 (29개):

| 카테고리 | 비율 | 필드명 |
|----------|------|--------|
| 수익성 | ROE | `roe` |
| 수익성 | ROA | `roa` |
| 수익성 | 영업이익률 | `operatingMargin` |
| 수익성 | 순이익률 | `netMargin` |
| 수익성 | 매출총이익률 | `grossMargin` |
| 수익성 | EBITDA 마진 | `ebitdaMargin` |
| 수익성 | 매출원가율 | `costOfSalesRatio` |
| 수익성 | 판관비율 | `sgaRatio` |
| 안정성 | 부채비율 | `debtRatio` |
| 안정성 | 유동비율 | `currentRatio` |
| 안정성 | 당좌비율 | `quickRatio` |
| 안정성 | 자기자본비율 | `equityRatio` |
| 안정성 | 이자보상배율 | `interestCoverage` |
| 안정성 | 순차입금비율 | `netDebtRatio` |
| 안정성 | 비유동비율 | `noncurrentRatio` |
| 성장성 | 매출 YoY | `revenueGrowth` |
| 성장성 | 영업이익 YoY | `operatingProfitGrowth` |
| 성장성 | 순이익 YoY | `netProfitGrowth` |
| 성장성 | 자산 YoY | `assetGrowth` |
| 성장성 | 자본 YoY | `equityGrowthRate` |
| 효율성 | 총자산회전율 | `totalAssetTurnover` |
| 효율성 | 재고자산회전율 | `inventoryTurnover` |
| 효율성 | 매출채권회전율 | `receivablesTurnover` |
| 효율성 | 매입채무회전율 | `payablesTurnover` |
| 현금흐름 | FCF | `fcf` |
| 현금흐름 | 영업CF 마진 | `operatingCfMargin` |
| 현금흐름 | 영업CF/순이익 | `operatingCfToNetIncome` |
| 현금흐름 | CAPEX 비율 | `capexRatio` |
| 현금흐름 | 배당성향 | `dividendPayoutRatio` |

시계열 결과에는 원시 값 리스트도 포함된다: `revenue`, `operatingProfit`, `netProfit`, `totalAssets`, `totalEquity`, `operatingCashflow`

---

## 한눈에 보기

전체 재무비율을 한번에 출력하는 패턴:

```python
c = Company("005930")
r = c.ratios

if r:
    def p(label, val, unit="%", fmt=".1f"):
        if val is not None:
            print(f"  {label:16s} {val:{fmt}}{unit}")
        else:
            print(f"  {label:16s} -")

    print(f"=== {c.corpName} 재무비율 ===")
    print()
    print("[ 수익성 ]")
    p("ROE", r.roe)
    p("ROA", r.roa)
    p("영업이익률", r.operatingMargin)
    p("순이익률", r.netMargin)
    p("매출총이익률", r.grossMargin)
    p("EBITDA마진", r.ebitdaMargin)
    p("매출원가율", r.costOfSalesRatio)
    p("판관비율", r.sgaRatio)
    print()
    print("[ 안정성 ]")
    p("부채비율", r.debtRatio)
    p("유동비율", r.currentRatio)
    p("당좌비율", r.quickRatio)
    p("자기자본비율", r.equityRatio)
    p("이자보상배율", r.interestCoverage, "배")
    p("순차입금비율", r.netDebtRatio)
    p("비유동비율", r.noncurrentRatio)
    print()
    print("[ 효율성 ]")
    p("총자산회전율", r.totalAssetTurnover, "회", ".2f")
    p("재고자산회전율", r.inventoryTurnover, "회", ".1f")
    p("매출채권회전율", r.receivablesTurnover, "회", ".1f")
    p("매입채무회전율", r.payablesTurnover, "회", ".1f")
    print()
    print("[ 현금흐름 ]")
    if r.fcf:
        p("FCF", r.fcf / 1e8, "억원", ",.0f")
    p("영업CF 마진", r.operatingCfMargin)
    p("영업CF/순이익", r.operatingCfToNetIncome)
    p("CAPEX 비율", r.capexRatio)
    p("배당성향", r.dividendPayoutRatio)
    print()
    print("[ 성장성 ]")
    p("매출 3Y CAGR", r.revenueGrowth3Y)
```

---

## 여러 기업 재무비율 비교

```python
import polars as pl

codes = ["005930", "000660", "035420", "035720", "051910"]
rows = []

for code in codes:
    c = Company(code)
    r = c.ratios
    if r is None:
        continue
    rows.append({
        "기업": c.corpName,
        "ROE(%)": round(r.roe, 1) if r.roe else None,
        "영업이익률(%)": round(r.operatingMargin, 1) if r.operatingMargin else None,
        "부채비율(%)": round(r.debtRatio, 1) if r.debtRatio else None,
        "유동비율(%)": round(r.currentRatio, 1) if r.currentRatio else None,
        "FCF(억)": round(r.fcf / 1e8) if r.fcf else None,
        "총자산회전율": round(r.totalAssetTurnover, 2) if r.totalAssetTurnover else None,
    })

df = pl.DataFrame(rows)
print(df)
```

같은 코드 구조에서 `codes` 리스트만 바꾸면 어떤 기업이든 비교할 수 있다. 5개든 50개든 500개든 같은 코드다.

---

## 공식 레퍼런스

### 수익성 (Profitability)

| 비율 | 공식 | 단위 |
|------|------|------|
| ROE | 순이익(TTM) ÷ 자기자본 × 100 | % |
| ROA | 순이익(TTM) ÷ 총자산 × 100 | % |
| 영업이익률 | 영업이익(TTM) ÷ 매출(TTM) × 100 | % |
| 순이익률 | 순이익(TTM) ÷ 매출(TTM) × 100 | % |
| 매출총이익률 | 매출총이익(TTM) ÷ 매출(TTM) × 100 | % |
| EBITDA 마진 | (영업이익 + 감가상각추정) ÷ 매출(TTM) × 100 | % |
| 매출원가율 | 매출원가(TTM) ÷ 매출(TTM) × 100 | % |
| 판관비율 | 판매관리비(TTM) ÷ 매출(TTM) × 100 | % |

> EBITDA 감가상각 추정: 유형자산 × 5% + 무형자산 × 10% (현금흐름표의 감가상각비 추출이 어려워 근사치 사용)

### 안정성 (Stability)

| 비율 | 공식 | 단위 |
|------|------|------|
| 부채비율 | 부채총계 ÷ 자기자본 × 100 | % |
| 유동비율 | 유동자산 ÷ 유동부채 × 100 | % |
| 당좌비율 | (유동자산 - 재고자산) ÷ 유동부채 × 100 | % |
| 자기자본비율 | 자기자본 ÷ 총자산 × 100 | % |
| 이자보상배율 | 영업이익(TTM) ÷ 금융비용(TTM) | 배 |
| 순차입금비율 | (단기차입금 + 장기차입금 + 사채 - 현금) ÷ 자기자본 × 100 | % |
| 비유동비율 | 비유동자산 ÷ 자기자본 × 100 | % |

### 효율성 (Efficiency)

| 비율 | 공식 | 단위 |
|------|------|------|
| 총자산회전율 | 매출(TTM) ÷ 총자산 | 회 |
| 재고자산회전율 | 매출(TTM) ÷ 재고자산 | 회 |
| 매출채권회전율 | 매출(TTM) ÷ 매출채권 | 회 |
| 매입채무회전율 | 매출원가(TTM) ÷ 매입채무 | 회 |

### 현금흐름 (Cash Flow)

| 비율 | 공식 | 단위 |
|------|------|------|
| FCF | 영업CF(TTM) - \|CAPEX\| | 원 |
| 영업CF 마진 | 영업CF(TTM) ÷ 매출(TTM) × 100 | % |
| 영업CF/순이익 | 영업CF(TTM) ÷ 순이익(TTM) × 100 | % |
| CAPEX 비율 | \|CAPEX\|(TTM) ÷ 매출(TTM) × 100 | % |
| 배당성향 | \|배당금지급\|(TTM) ÷ 순이익(TTM) × 100 | % |

### 성장성 (Growth)

| 비율 | 공식 | 단위 |
|------|------|------|
| 매출 3Y CAGR | (최신매출 ÷ 3년전매출)^(1/N) - 1 | % |
| 매출 YoY | (당기매출 - 전기매출) ÷ \|전기매출\| × 100 | % |
| 영업이익 YoY | (당기영업이익 - 전기영업이익) ÷ \|전기영업이익\| × 100 | % |
| 순이익 YoY | (당기순이익 - 전기순이익) ÷ \|전기순이익\| × 100 | % |
| 자산 YoY | (당기자산 - 전기자산) ÷ \|전기자산\| × 100 | % |
| 자본 YoY | (당기자본 - 전기자본) ÷ \|전기자본\| × 100 | % |

### 밸류에이션 (시가총액 필요)

| 비율 | 공식 | 단위 |
|------|------|------|
| PER | 시가총액 ÷ 순이익(TTM) | 배 |
| PBR | 시가총액 ÷ 자기자본 | 배 |
| PSR | 시가총액 ÷ 매출(TTM) | 배 |
| EV/EBITDA | (시가총액 + 순차입금) ÷ EBITDA | 배 |

> 밸류에이션은 `calcRatios(series, marketCap=시가총액)` 처럼 시가총액을 전달해야 계산된다.

---

## 사용하는 계정 매핑 (snakeId)

| 계정 | 재무제표 | snakeId |
|------|---------|---------|
| 매출액 | IS | `sales` |
| 매출원가 | IS | `cost_of_sales` |
| 매출총이익 | IS | `gross_profit` |
| 영업이익 | IS | `operating_profit` |
| 당기순이익 | IS | `net_profit` |
| 판매관리비 | IS | `selling_and_administrative_expenses` |
| 금융수익 | IS | `finance_income` |
| 금융비용 | IS | `finance_costs` |
| 총자산 | BS | `total_assets` |
| 자기자본 | BS | `owners_of_parent_equity` |
| 부채총계 | BS | `total_liabilities` |
| 유동자산 | BS | `current_assets` |
| 유동부채 | BS | `current_liabilities` |
| 현금성자산 | BS | `cash_and_cash_equivalents` |
| 단기차입금 | BS | `shortterm_borrowings` |
| 장기차입금 | BS | `longterm_borrowings` |
| 사채 | BS | `debentures` |
| 재고자산 | BS | `inventories` |
| 매출채권 | BS | `trade_and_other_receivables` |
| 매입채무 | BS | `trade_and_other_payables` |
| 유형자산 | BS | `tangible_assets` |
| 무형자산 | BS | `intangible_assets` |
| 이익잉여금 | BS | `retained_earnings` |
| 비유동자산 | BS | `noncurrent_assets` |
| 비유동부채 | BS | `noncurrent_liabilities` |
| 영업CF | CF | `operating_cashflow` |
| 투자CF | CF | `investing_cashflow` |
| CAPEX | CF | `purchase_of_property_plant_and_equipment` |
| 배당금지급 | CF | `dividends_paid` |

---

## 주의사항

### 업종별 비교

재무비율은 절대적인 기준이 없다. 반도체와 은행의 부채비율은 비교 자체가 의미 없다. 같은 업종 내에서 비교해야 한다. → [8. 기업 간 비교](./cross-company)에서 섹터 분류를 활용

### 금융업

은행, 보험, 증권은 재무 구조가 다르므로 부채비율, 유동비율 등의 의미가 일반 기업과 다르다. 은행의 부채비율이 1000%인 건 정상이다 (예금이 부채이므로). 금융업은 매출, 유동자산, 재고자산 등의 계정이 아예 없을 수 있다.

### 일시적 왜곡

일회성 이익/손실이 큰 분기가 있으면 TTM 비율이 왜곡될 수 있다. 예를 들어 공장 매각으로 큰 이익이 발생한 분기가 TTM에 포함되면 ROE가 비정상적으로 높아진다.

### 이상치 필터링

극단적인 값은 자동으로 필터링된다:
- ROE: ±500% 초과 시 `None` 처리
- ROA: ±200% 초과 시 `None` 처리
- 부채비율: 5000% 초과 시 `None` 처리
- 유동비율: 10000% 초과 시 `None` 처리

### EBITDA 추정

DART 데이터에서 감가상각비를 개별 계정으로 분리하기 어려워, 유형자산×5% + 무형자산×10%으로 근사 추정한다. 실제 감가상각비가 이 범위와 크게 다른 기업(예: 항공사)은 EBITDA 마진이 부정확할 수 있다.

---

## 다음 단계

- [5. 보고서 데이터](./report-data) — 배당, 직원, 주주, 감사 등
- [6. 공시 텍스트](./disclosure) — 사업의 내용, MD&A
