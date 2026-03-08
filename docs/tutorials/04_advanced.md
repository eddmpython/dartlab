---
title: "4. Advanced Analysis"
---

# 4. Advanced Analysis — 고급 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_advanced.ipynb)

주석 세부항목, 유형자산 변동표, 관계기업 분석 등 심화 모듈을 다룬다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- 주석 세부항목 (23개 키워드)
- 유형자산 변동표
- 관계기업·공동기업 투자
- 여러 종목 비교 분석

## 준비

```python
from dartlab import Company

samsung = Company("005930")
```

## 주석 세부항목

재무제표 주석에서 특정 항목의 상세 테이블을 추출한다. 23개 키워드를 지원한다.

```python
result = samsung.notesDetail("재고자산")

print(result.tableDf)  # 항목별 시계열
```

### 지원 키워드

| 키워드 | 설명 |
|--------|------|
| `재고자산` | 제품, 상품, 원재료, 재공품 등 |
| `주당이익` | 기본주당이익, 희석주당이익 |
| `충당부채` | 제품보증, 소송, 복구 등 |
| `차입금` | 단기·장기 차입금 상세 |
| `매출채권` | 매출채권, 대손충당금 |
| `리스` | 사용권자산, 리스부채 |
| `투자부동산` | 투자부동산 변동 |
| `무형자산` | 영업권, 소프트웨어, 특허 등 |

### 연도별 상세 테이블

```python
for year, periods in result.tables.items():
    for p in periods:
        print(f"[{year}] {p.period} (패턴: {p.pattern})")
        for item in p.items:
            print(f"  {item.name}: {item.values}")
```

### 분기별 분석

```python
result = samsung.notesDetail("재고자산", period="q")
print(result.tableDf)
```

## 유형자산 변동표

토지, 건물, 기계장치 등 카테고리별 취득·처분·감가상각을 추적한다.

```python
result = samsung.tangibleAsset()

result.reliability  # "high" 또는 "low"
result.warnings     # 신뢰도 관련 경고
```

### 변동 시계열

```python
print(result.movementDf)  # 카테고리별 기초/기말 시계열
```

### 연도별 상세 변동

```python
for year, movements in result.movements.items():
    for m in movements:
        print(f"[{year}] {m.period}")
        print(f"  카테고리: {m.categories}")
        for row in m.rows:
            print(f"  {row}")
```

## 관계기업·공동기업

관계기업의 지분율, 장부가, 변동내역을 분석한다.

```python
result = samsung.affiliates()

print(result.movementDf)  # 변동 시계열
```

### 연도별 프로필

```python
for year, profiles in result.profiles.items():
    for p in profiles:
        print(f"[{year}] {p.name}: {p.ratio}%, 장부가 {p.bookValue}")
```

### 분기별 분석

```python
result = samsung.affiliates(period="q")
```

## 여러 종목 비교

여러 종목을 분석해서 비교하는 패턴이다.

```python
import polars as pl

codes = ["005930", "000660", "035420"]
names = []
revenues = []

for code in codes:
    c = Company(code)
    result = c.fsSummary()
    if result and result.IS is not None:
        names.append(result.corpName)
        last_row = result.IS.row(-1, named=True)
        revenues.append(last_row.get("매출액") or last_row.get("수익(매출액)"))

comparison = pl.DataFrame({
    "기업": names,
    "최근 매출액": revenues
})
print(comparison)
```

### 배당 비교

```python
dividends = []
for code in codes:
    c = Company(code)
    result = c.dividend()
    if result and result.timeSeries is not None:
        last = result.timeSeries.row(-1, named=True)
        dividends.append({
            "기업": c.corpName,
            "DPS": last.get("dps"),
            "배당수익률": last.get("dividendYield"),
            "배당성향": last.get("payoutRatio")
        })

print(pl.DataFrame(dividends))
```

## 함수 직접 호출

Company 클래스를 거치지 않고 모듈 함수를 직접 호출할 수도 있다.

```python
from dartlab.finance.summary import fsSummary
from dartlab.finance.statements import statements
from dartlab.finance.dividend import dividend
from dartlab.finance.notesDetail import notesDetail

result = fsSummary("005930")
result = statements("005930", period="q")
result = dividend("005930")
result = notesDetail("005930", "재고자산")
```

## 다음 단계

- [API Overview](../api/overview) — 전체 메서드 목록과 파라미터 상세
- [Bridge Matching](../user-guide/bridge-matching) — 매칭 알고리즘 상세
