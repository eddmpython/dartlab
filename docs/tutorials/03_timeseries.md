---
title: "3. Timeseries"
---

# 3. 시계열 분석 — 계정 표준화와 분기별 독립 데이터

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/03_timeseries.ipynb)

[2. 재무제표 조회](./financial-statements)에서 본 것처럼, DART 원본 데이터는 회사마다 계정명이 다르고 분기 데이터는 누적값이다. 이 튜토리얼에서는 이 두 문제를 해결하는 DartLab의 시계열 엔진을 다룬다.

- 왜 계정 표준화가 필요한가
- 시계열 생성 (`timeseries` property)
- 반환 구조 이해 (dict + period list)
- 누적 → 독립 분기 변환 원리
- 특정 계정 조회
- TTM (Trailing Twelve Months)
- 연간 시계열
- 여러 기업 시계열 비교

---

## 준비

```python
import dartlab
```

---

## 왜 계정 표준화가 필요한가

DART에서 "매출"을 가져오면 회사마다 이름이 다르다.

```
삼성전자:  ifrs-full_Revenue      → 수익(매출액)
SK하이닉스: dart_OperatingRevenue  → 영업수익
현대차:    ifrs-full_Revenue      → 매출액
카카오:    dart_Revenue           → 수익(매출액)
KB금융:    dart_OperatingRevenue  → 영업수익
```

같은 "매출"인데 XBRL ID도 다르고 한글 이름도 다르다. 이 상태에서는 기업 간 비교가 불가능하다.

DartLab은 이 문제를 **7단계 매핑 파이프라인**으로 해결한다.

```
원본 account_id, account_nm
  ↓ prefix 제거 (ifrs-full_, dart_, ifrs_ 등)
  ↓ ID 동의어 통합 (영문 변형 정리)
  ↓ 이름 동의어 통합 (한글 변형 정리)
  ↓ 핵심 계정 오버라이드 (50개 최우선 매핑)
  ↓ 학습된 매핑 조회 (34,000+ 동의어)
  ↓ 괄호 제거 후 재조회 (fallback)
  ↓ 표준 snakeId 반환
```

결과적으로 모든 기업의 매출은 `revenue`, 영업이익은 `operating_income`, 자산총계는 `total_assets`라는 하나의 키로 접근할 수 있다.

전체 2,700개 기업에서의 매핑률은 **98.7%**이고, 재무상태표 등식(자산 = 부채 + 자본) 검증은 **99.7%** 통과한다.

---

## 시계열 생성

`Company.timeseries` property로 분기별 시계열을 받는다.

```python
c = dartlab.Company("005930")
series, periods = c.timeseries
```

이 한 줄이 내부에서 하는 일:
1. 원본 재무 parquet 로드
2. 34,000+ 동의어 기반 계정 표준화
3. 연결(CFS) 우선, 행 단위 중복 제거
4. 손익계산서/현금흐름표: 누적 → 독립 분기 변환
5. 재무상태표: 시점 잔액 그대로 유지

---

## 반환 구조

```python
series, periods = c.timeseries
```

`series`는 재무제표별 dict의 dict이다.

```python
series = {
    "BS": {
        "total_assets": [v1, v2, v3, ...],
        "current_assets": [v1, v2, v3, ...],
        "total_equity": [v1, v2, v3, ...],
        "total_liabilities": [v1, v2, v3, ...],
        ...
    },
    "IS": {
        "revenue": [v1, v2, v3, ...],
        "operating_income": [v1, v2, v3, ...],
        "net_income": [v1, v2, v3, ...],
        ...
    },
    "CF": {
        "operating_cashflow": [v1, v2, v3, ...],
        "investing_cashflow": [v1, v2, v3, ...],
        "financing_cashflow": [v1, v2, v3, ...],
        ...
    }
}
```

`periods`는 분기 레이블 리스트다.

```python
periods = ["2016_Q1", "2016_Q2", "2016_Q3", "2016_Q4",
           "2017_Q1", "2017_Q2", ...,
           "2024_Q3", "2024_Q4"]
```

`series`의 각 값 리스트와 `periods`는 인덱스가 대응한다. `series["IS"]["revenue"][0]`은 `periods[0]` (2016_Q1)의 매출이다.

### 기본 접근 패턴

```python
# 삼성전자 최근 4분기 매출 확인
series, periods = c.timeseries

for i in range(-4, 0):
    period = periods[i]
    rev = series["IS"]["revenue"][i]
    if rev:
        print(f"{period}: {rev/1e8:,.0f}억원")
```

### 사용 가능한 snakeId 확인

```python
# 재무상태표에 어떤 계정이 있는지
print(list(series["BS"].keys()))

# 손익계산서
print(list(series["IS"].keys()))

# 현금흐름표
print(list(series["CF"].keys()))
```

주요 snakeId:

| 재무제표 | snakeId | 의미 |
|---------|---------|------|
| BS | `total_assets` | 자산총계 |
| BS | `current_assets` | 유동자산 |
| BS | `total_liabilities` | 부채총계 |
| BS | `total_equity` | 지배기업 귀속 자본 |
| BS | `equity_including_nci` | 자본총계 (비지배지분 포함) |
| IS | `revenue` | 매출액 |
| IS | `operating_income` | 영업이익 |
| IS | `net_income` | 당기순이익 |
| IS | `cost_of_sales` | 매출원가 |
| IS | `gross_profit` | 매출총이익 |
| CF | `operating_cashflow` | 영업활동 현금흐름 |
| CF | `investing_cashflow` | 투자활동 현금흐름 |
| CF | `financing_cashflow` | 재무활동 현금흐름 |

---

## 누적 → 독립 분기 변환

DART의 분기 보고서는 **누적 구조**로 제출된다.

```
1분기 보고서:  Q1 매출 = 400억
반기 보고서:   Q1+Q2 매출 = 1,000억  (Q2만의 매출은 600억)
3분기 보고서:  Q1+Q2+Q3 매출 = 2,200억  (Q3만의 매출은 1,200억)
사업 보고서:   Q1+Q2+Q3+Q4 매출 = 3,000억  (Q4만의 매출은 800억)
```

시계열 엔진은 이 누적값을 자동으로 독립 분기값으로 변환한다.

```
누적                    독립 분기
Q1:         400    →    Q1:  400  (그대로)
Q1+Q2:    1,000    →    Q2:  600  (1,000 - 400)
Q1+Q2+Q3: 2,200    →    Q3: 1,200 (2,200 - 1,000)
연간:     3,000    →    Q4:  800  (3,000 - 2,200)
```

이 변환은 **손익계산서(IS)**와 **현금흐름표(CF)**에만 적용된다. 재무상태표(BS)는 시점 잔액이므로 변환하지 않는다.

```python
# 이미 독립 분기 값이다
series["IS"]["revenue"]  # [Q1매출, Q2매출, Q3매출, Q4매출, ...]

# BS는 시점 잔액 그대로
series["BS"]["total_assets"]  # [Q1말잔액, Q2말잔액, Q3말잔액, Q4말잔액, ...]
```

---

## 특정 계정 조회 함수

시계열에서 특정 값을 쉽게 꺼내는 함수들이 있다.

```python
from dartlab.engines.dart.finance import getTTM, getLatest
```

### getLatest — 가장 최근 값

```python
series, periods = c.timeseries

# 가장 최근 분기의 자산총계
assets = getLatest(series, "BS", "total_assets")
print(f"자산총계: {assets/1e8:,.0f}억원")

# 가장 최근 분기의 현금
cash = getLatest(series, "BS", "cash_and_equivalents")
```

### getTTM — 최근 4분기 합산

TTM(Trailing Twelve Months)은 최근 4개 분기의 합산이다. 연간 실적의 가장 최신 근사치이며, 계절성 효과가 제거된다.

```python
# 연간 매출 (최근 4분기 합)
rev_ttm = getTTM(series, "IS", "revenue")
print(f"TTM 매출: {rev_ttm/1e8:,.0f}억원")

# 연간 영업이익 (최근 4분기 합)
oi_ttm = getTTM(series, "IS", "operating_income")
print(f"TTM 영업이익: {oi_ttm/1e8:,.0f}억원")

# 영업이익률
if rev_ttm and oi_ttm:
    margin = oi_ttm / rev_ttm * 100
    print(f"영업이익률: {margin:.1f}%")
```

> TTM은 IS와 CF에만 의미가 있다. BS는 시점 잔액이므로 TTM이 아니라 `getLatest`를 사용한다.

---

## 연간 시계열

분기 대신 연도별 합산 시계열이 필요할 때 사용한다.

```python
from dartlab.engines.dart.finance import buildAnnual

annual_series, years = buildAnnual("005930")

# years = ["2016", "2017", ..., "2024"]
# annual_series 구조는 분기 시계열과 동일

for i, year in enumerate(years[-5:], len(years)-5):
    rev = annual_series["IS"]["revenue"][i]
    if rev:
        print(f"{year}: 매출 {rev/1e8:,.0f}억원")
```

---

## 여러 기업 시계열 비교

계정이 표준화되어 있으므로 동일한 키로 어떤 기업이든 비교할 수 있다.

```python
companies = [
    dartlab.Company("005930"),   # 삼성전자
    dartlab.Company("000660"),   # SK하이닉스
    dartlab.Company("035420"),   # NAVER
]

for comp in companies:
    s, p = comp.timeseries
    rev = getTTM(s, "IS", "revenue")
    oi = getTTM(s, "IS", "operating_income")
    assets = getLatest(s, "BS", "total_assets")

    rev_str = f"{rev/1e8:,.0f}억" if rev else "N/A"
    oi_str = f"{oi/1e8:,.0f}억" if oi else "N/A"
    asset_str = f"{assets/1e8:,.0f}억" if assets else "N/A"

    print(f"{comp.corpName}: 매출 {rev_str} / 영업이익 {oi_str} / 자산 {asset_str}")
```

### 매출 시계열 나란히 보기

```python
samsung = dartlab.Company("005930")
sk = dartlab.Company("000660")

s1, p1 = samsung.timeseries
s2, p2 = sk.timeseries

# 최근 8분기 매출 비교
for i in range(-8, 0):
    period = p1[i]
    r1 = s1["IS"]["revenue"][i]
    r2 = s2["IS"]["revenue"][i] if abs(i) <= len(s2["IS"]["revenue"]) else None

    r1_str = f"{r1/1e8:,.0f}억" if r1 else "N/A"
    r2_str = f"{r2/1e8:,.0f}억" if r2 else "N/A"
    print(f"{period}: 삼성전자 {r1_str} / SK하이닉스 {r2_str}")
```

---

## 주의사항

### None 값

데이터가 없는 분기는 `None`이다. 계산 시 항상 `None` 체크를 해야 한다.

```python
rev = series["IS"]["revenue"]
# [None, None, 400억, 600억, ...]  ← 초기 분기는 데이터 없을 수 있음
```

### 은행/금융업

은행, 보험, 증권 등 금융업은 일반 제조업과 재무제표 구조가 다르다. `revenue`, `current_assets` 등이 없을 수 있다. 대신 `interest_income`, `fee_income` 등 금융업 고유 계정이 존재한다.

### 최초 데이터 시점

기업마다 데이터 시작 시점이 다르다. 상장 시기에 따라 2016년부터 있는 기업도 있고, 2020년부터인 기업도 있다.

---

## 다음 단계

- [4. 재무비율](./ratios) — 시계열에서 자동 계산되는 재무비율
- [5. 보고서 데이터](./report-data) — 배당, 직원, 주주, 감사 등 정기보고서 데이터

