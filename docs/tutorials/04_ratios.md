---
title: "4. Ratios"
---

# 4. 재무비율 — 숫자에서 의미로

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb)

시계열 데이터가 있으면 재무비율을 계산할 수 있다. DartLab은 수익성, 안정성, 성장성, 현금흐름, 밸류에이션 지표를 자동으로 계산한다.

- 재무비율 객체 (`ratios` property)
- 수익성 지표 (ROE, ROA, 영업이익률, 순이익률)
- 안정성 지표 (부채비율, 유동비율)
- 현금흐름 지표 (FCF, 영업CF 마진)
- 성장성 지표 (매출성장률, 이익성장률)
- 밸류에이션 기초 데이터 (TTM 매출, 이익, 자본)
- 여러 기업 재무비율 비교

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

## 수익성 지표

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

---

## 안정성 지표

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

> 업종별로 적정 수준이 다르다. 건설업은 200%가 정상이고, IT업은 100%도 높은 편이다. [8. 기업 간 비교](./cross-company)에서 섹터 분류를 활용하면 같은 업종 내에서 비교할 수 있다.

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

---

## 현금흐름 지표

이익은 회계상 숫자이고, 현금흐름은 실제로 들어오고 나간 돈이다. 이익이 나도 현금이 부족하면 부도가 난다.

### FCF (Free Cash Flow, 잉여현금흐름)

**영업활동 현금흐름 - 자본적 지출(CAPEX)**

영업에서 벌어들인 현금 중 설비투자를 빼고 남은 돈이다. 배당을 줄 수도 있고, 부채를 갚을 수도 있고, 신규 투자에 쓸 수도 있다.

```python
if r.fcf:
    print(f"FCF: {r.fcf/1e8:,.0f}억원")
```

FCF가 지속적으로 마이너스라면 영업에서 버는 것보다 투자에 더 많이 쓰고 있다는 뜻이다. 성장기 기업은 정상일 수 있지만, 성숙기 기업이면 주의 신호다.

### 영업CF 마진

```python
if r.operatingCFMargin:
    print(f"영업CF 마진: {r.operatingCFMargin:.1f}%")
```

---

## 성장성 지표

```python
# TTM 기준 매출과 이익
if r.revenueTTM:
    print(f"TTM 매출: {r.revenueTTM/1e8:,.0f}억원")
if r.operatingIncomeTTM:
    print(f"TTM 영업이익: {r.operatingIncomeTTM/1e8:,.0f}억원")
if r.netIncomeTTM:
    print(f"TTM 순이익: {r.netIncomeTTM/1e8:,.0f}억원")
```

---

## 한눈에 보기

전체 재무비율을 한번에 출력하는 패턴:

```python
c = Company("005930")
r = c.ratios

if r:
    print(f"=== {c.corpName} 재무비율 ===")
    print()
    print("[ 수익성 ]")
    print(f"  ROE:        {r.roe:.1f}%")
    print(f"  ROA:        {r.roa:.1f}%")
    print(f"  영업이익률: {r.operatingMargin:.1f}%")
    print(f"  순이익률:   {r.netMargin:.1f}%")
    print()
    print("[ 안정성 ]")
    print(f"  부채비율:   {r.debtRatio:.1f}%")
    print(f"  유동비율:   {r.currentRatio:.1f}%")
    print()
    print("[ 현금흐름 ]")
    if r.fcf:
        print(f"  FCF:        {r.fcf/1e8:,.0f}억원")
    print()
    print("[ 규모 ]")
    if r.revenueTTM:
        print(f"  TTM 매출:   {r.revenueTTM/1e8:,.0f}억원")
    if r.operatingIncomeTTM:
        print(f"  TTM 영업이익: {r.operatingIncomeTTM/1e8:,.0f}억원")
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
    })

df = pl.DataFrame(rows)
print(df)
```

같은 코드 구조에서 `codes` 리스트만 바꾸면 어떤 기업이든 비교할 수 있다. 5개든 50개든 500개든 같은 코드다.

---

## 주의사항

### 업종별 비교

재무비율은 절대적인 기준이 없다. 반도체와 은행의 부채비율은 비교 자체가 의미 없다. 같은 업종 내에서 비교해야 한다. → [8. 기업 간 비교](./cross-company)에서 섹터 분류를 활용

### 일시적 왜곡

일회성 이익/손실이 큰 분기가 있으면 TTM 비율이 왜곡될 수 있다. 예를 들어 공장 매각으로 큰 이익이 발생한 분기가 TTM에 포함되면 ROE가 비정상적으로 높아진다.

### 금융업

은행, 보험, 증권은 재무 구조가 다르므로 부채비율, 유동비율 등의 의미가 일반 기업과 다르다. 은행의 부채비율이 1000%인 건 정상이다 (예금이 부채이므로).

---

## 다음 단계

- [5. 보고서 데이터](./report-data) — 배당, 직원, 주주, 감사 등
- [6. 공시 텍스트](./disclosure) — 사업의 내용, MD&A
