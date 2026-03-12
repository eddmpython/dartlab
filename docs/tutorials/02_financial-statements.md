---
title: "2. Financial Statements"
---

# 2. Financial Statements — 재무제표 조회

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial_statements.ipynb)

재무제표는 기업 분석의 출발점이다. 이 튜토리얼에서는 DART 원본 재무제표를 조회하고, 데이터 구조를 이해하고, 원하는 항목을 추출하는 방법을 다룬다.

- 3대 재무제표 조회 (BS, IS, CF)
- 연결 vs 별도 재무제표
- 연도별 열 구조 이해
- 특정 계정항목 필터링
- 분기별 재무제표
- 원본 데이터의 한계와 주의사항

---

## 준비

```python
import dartlab

c = dartlab.Company("005930")
```

---

## 3대 재무제표

`Company` 객체의 property로 3대 재무제표에 접근한다. 메서드 호출(`()`)이 아니라 속성 접근이다.

### 재무상태표 (Balance Sheet)

```python
c.BS
```

재무상태표는 **특정 시점**의 자산, 부채, 자본 잔액을 보여준다. "12월 31일 기준으로 회사가 뭘 갖고 있고, 뭘 빚지고 있는가"라는 질문에 대한 답이다.

| 구분 | 의미 | 주요 항목 |
|------|------|----------|
| 자산 | 회사가 보유한 경제적 자원 | 유동자산, 비유동자산, 자산총계 |
| 부채 | 갚아야 할 의무 | 유동부채, 비유동부채, 부채총계 |
| 자본 | 자산 - 부채 | 자본금, 이익잉여금, 자본총계 |

핵심 등식: **자산 = 부채 + 자본**. 이 등식이 맞지 않으면 데이터에 문제가 있는 것이다.

```python
import polars as pl

bs = c.BS
if bs is not None:
    # 행은 계정항목, 열은 연도
    print(bs.columns)
    # ['account', '2015', '2016', '2017', ..., '2024']

    # 자산총계 행만 필터링
    total_assets = bs.filter(pl.col("account") == "자산총계")
    print(total_assets)
```

### 손익계산서 (Income Statement)

```python
c.IS
```

손익계산서는 **일정 기간** 동안의 수익과 비용을 보여준다. "올해 얼마 벌고 얼마 썼는가"라는 질문에 대한 답이다.

| 구분 | 의미 | 주요 항목 |
|------|------|----------|
| 수익 | 영업활동으로 벌어들인 돈 | 매출액(수익) |
| 비용 | 수익 창출에 쓴 돈 | 매출원가, 판관비 |
| 이익 | 수익 - 비용 | 영업이익, 당기순이익 |

```python
is_df = c.IS
if is_df is not None:
    # 매출과 영업이익 행만 필터링
    key_items = is_df.filter(
        pl.col("account").is_in(["매출액", "수익(매출액)", "영업이익"])
    )
    print(key_items)
```

> 같은 "매출"이라도 회사마다 계정명이 다르다. 삼성전자는 "수익(매출액)", SK하이닉스는 "영업수익"이다. 이 문제는 [3. 시계열 분석](./timeseries)에서 해결한다.

### 현금흐름표 (Cash Flow Statement)

```python
c.CF
```

현금흐름표는 **일정 기간** 동안 실제로 현금이 얼마나 들어오고 나갔는지를 보여준다. 이익이 나도 현금이 부족하면 부도가 나기 때문에, 손익계산서와 함께 봐야 한다.

| 구분 | 의미 | 예시 |
|------|------|------|
| 영업활동 | 본업에서 벌어들인 현금 | 매출 수금, 급여 지급 |
| 투자활동 | 설비·자산 관련 현금 | 공장 건설, 장비 구매 |
| 재무활동 | 자금조달·상환 현금 | 차입, 배당 지급 |

```python
cf = c.CF
if cf is not None:
    cash_items = cf.filter(
        pl.col("account").is_in([
            "영업활동으로인한현금흐름",
            "투자활동으로인한현금흐름",
            "재무활동으로인한현금흐름"
        ])
    )
    print(cash_items)
```

---

## 연결 vs 별도

DART에는 두 종류의 재무제표가 있다.

| 구분 | 포함 범위 | 보는 이유 |
|------|----------|----------|
| **연결** (CFS) | 모회사 + 자회사 전체 | 그룹 전체의 실질적 규모와 성과 |
| **별도** (OFS) | 모회사만 | 모회사 자체의 재무 상태 |

삼성전자의 연결 매출에는 삼성디스플레이, 삼성SDI 등 자회사의 매출이 포함된다. 별도 매출은 삼성전자 단독 매출만이다.

DartLab은 **연결 재무제표를 우선** 사용한다. 연결이 없는 기업(자회사가 없는 단독 기업)만 별도 재무제표를 사용한다.

```python
# BS, IS, CF는 자동으로 연결 우선
c.BS   # 연결재무상태표 (있으면) 또는 별도재무상태표

# 원본 데이터에서 직접 확인하고 싶다면
result = c.fsSummary()
print(f"연결 데이터 존재: {result.hasConsolidated}")
```

---

## 열 구조 이해

반환되는 DataFrame의 열은 `account` + 연도들이다.

```python
bs = c.BS
print(bs.columns)
# ['account', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']
```

- `account`: 계정항목명 (한글)
- 연도 열: 해당 연도 결산 기준 금액 (백만원)

### 특정 연도 데이터 가져오기

```python
# 2024년 자산총계
bs = c.BS
row = bs.filter(pl.col("account") == "자산총계")
if row.height > 0:
    value = row["2024"][0]
    print(f"2024년 자산총계: {value:,.0f} 백만원")
    print(f"                = {value/1e6:,.1f} 조원")
```

### 여러 항목 한번에 추출

```python
# 핵심 BS 항목만 뽑기
key_accounts = ["자산총계", "유동자산", "비유동자산", "부채총계", "자본총계"]
summary = bs.filter(pl.col("account").is_in(key_accounts))
print(summary)
```

---

## 분기별 재무제표

기본 BS/IS/CF는 연간 데이터다. 분기별 데이터가 필요하면 `fsSummary()`를 사용한다.

```python
quarterly = c.fsSummary(period="q")

quarterly.BS   # 분기별 재무상태표
quarterly.IS   # 분기별 손익계산서
quarterly.CF   # 분기별 현금흐름표
```

분기별 열 이름은 `2020Q1`, `2020Q2`, `2020Q3`, `2020Q4` 형식이다.

```python
qbs = quarterly.BS
print(qbs.columns)
# ['account', '2020Q1', '2020Q2', '2020Q3', '2020Q4', '2021Q1', ...]
```

| period 값 | 포함 보고서 | 열 형식 |
|-----------|------------|---------|
| `"y"` (기본값) | 사업보고서만 | `2020`, `2021`, ... |
| `"q"` | 1분기 + 반기 + 3분기 + 사업 | `2020Q1`, `2020Q2`, ... |
| `"h"` | 반기 + 사업 | `2020H1`, `2020H2`, ... |

> 분기별 손익계산서(IS)의 수치는 **누적값**이다. Q2 열의 매출은 "2분기 매출"이 아니라 "1~2분기 누적 매출"이다. 독립 분기 매출이 필요하면 [3. 시계열 분석](./timeseries)의 시계열 엔진을 사용한다.

---

## 주의사항

### 계정명이 회사마다 다르다

같은 "매출"이라도 회사마다 다른 이름을 쓴다. `pl.col("account") == "매출액"`으로 필터링하면 일부 기업에서 빈 결과가 나올 수 있다.

```python
# 이렇게 하면 안 된다
bs.filter(pl.col("account") == "매출액")   # 일부 기업에서 못 찾음

# 이 문제를 해결하려면 시계열 엔진을 사용한다
# → 3. 시계열 분석 참조
```

### 금액 단위

DART 원본 데이터의 금액 단위는 **원(KRW)**이다. BS/IS/CF property에서 반환하는 값도 원 단위다.

```python
# 삼성전자 자산총계가 4조가 아니라 400조인 이유
# → 단위가 원이므로 400,000,000,000,000 (400조원)
```

### None 반환

데이터가 없는 기업은 `None`을 반환한다. 항상 `None` 체크를 해야 한다.

```python
bs = c.BS
if bs is not None:
    print(bs)
else:
    print("재무상태표 데이터 없음")
```

---

## 다음 단계

- [3. 시계열 분석](./timeseries) — 계정 표준화, 분기별 독립 시계열, TTM
- [4. 재무비율](./ratios) — ROE, 부채비율, FCF 등 자동 계산

