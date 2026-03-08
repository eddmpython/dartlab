---
title: 빠른 시작
---

# 빠른 시작

## Company 클래스

모든 분석의 진입점이다. 종목코드를 넣으면 데이터를 자동으로 로드한다.

```python
from dartlab import Company

samsung = Company("005930")
samsung.corpName  # "삼성전자"
```

## 요약 재무정보

Bridge Matching으로 계정명 변경을 추적하면서 시계열을 생성한다.

```python
result = samsung.fsSummary()

result.FS    # 전체 재무제표 시계열 (Polars DataFrame)
result.BS    # 재무상태표
result.IS    # 손익계산서
```

분기별 데이터도 가능하다.

```python
result = samsung.fsSummary(period="q")  # 분기별
result = samsung.fsSummary(period="h")  # 반기별
```

## 연결 재무제표

재무상태표, 손익계산서, 현금흐름표 상세 항목을 추출한다.

```python
result = samsung.statements()

result.BS    # 재무상태표
result.IS    # 손익계산서
result.CF    # 현금흐름표
```

## 배당

```python
result = samsung.dividend()
result.timeSeries
# year, netIncome, eps, totalDividend, payoutRatio, dividendYield, dps
```

## 직원 현황

```python
result = samsung.employee()
result.timeSeries
# year, totalEmployees, avgTenure, totalSalary, avgSalary
```

## 최대주주

```python
result = samsung.majorHolder()
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.timeSeries    # 지분율 시계열
```

## 함수 직접 호출

Company를 거치지 않고 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements

result = fsSummary("005930")
result = statements("005930")
```

## 보유 데이터 확인

```python
# 로컬에 있는 전체 종목 인덱스
index = Company.status()
print(index)
# stockCode, corpName, rows, yearFrom, yearTo, nDocs

# 특정 종목의 공시 목록
docs = samsung.docs()
print(docs)
```

## 다음 단계

- [Bridge Matching](../user-guide/bridge-matching.md)
- [전체 API Reference](../api/overview.md)
