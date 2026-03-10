---
title: "1. Quickstart"
---

# 1. Quickstart — 첫 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/01_quickstart.ipynb)

종목코드 하나로 DART 전자공시 분석을 시작한다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- Company 생성과 property 접근
- 재무제표 조회 (BS, IS, CF)
- Bridge Matching 결과 확인
- 분기별·반기별 분석
- 전체 일괄 조회 (all)
- 가이드와 보유 데이터 확인

---

## Company 생성

모든 분석의 시작점이다. 종목코드 또는 회사명으로 생성한다.

```python
from dartlab import Company

c = Company("005930")
c.corpName   # "삼성전자"
c.stockCode  # "005930"
```

회사명으로도 가능하다.

```python
c = Company("카카오")
c.stockCode    # "035720"
```

생성하면 아바타와 함께 기업 정보가 터미널에 표시된다.

---

## 재무제표 — property 접근

property 한 줄로 DataFrame을 받는다. 메서드 호출이 아니라 속성 접근이다.

```python
c.BS   # 재무상태표 (Balance Sheet)
c.IS   # 손익계산서 (Income Statement)
c.CF   # 현금흐름표 (Cash Flow)
```

행은 계정항목, 열은 연도다. Polars DataFrame으로 반환된다.

```python
print(c.BS)
# account      | 2015       | 2016       | ... | 2024
# 자산총계     | 262,174,324| 261,381,064| ... | ...
# 유동자산     | ...        | ...        | ... | ...
# 비유동자산   | ...        | ...        | ... | ...
# 부채총계     | ...        | ...        | ... | ...
# 자본총계     | ...        | ...        | ... | ...
```

> property는 lazy loading + caching이다. 처음 접근할 때만 파싱하고 이후 캐싱한다. 두 번째 접근부터는 즉시 반환된다.

---

## Bridge Matching 상세

`fsSummary()` 메서드는 Bridge Matching으로 계정명 변경을 자동 추적한다. 분석 결과를 확인하려면 직접 호출한다.

```python
result = c.fsSummary()

# 전체 통계
print(f"분석 연도: {result.nYears}년")
print(f"전체 매칭률: {result.allRate:.1%}")
print(f"변경점 수: {result.nBreakpoints}")
print(f"연속 구간: {result.nSegments}개")
```

### 연도별 매칭 결과

```python
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%} ({pair.matched}/{pair.total})")
```

### 변경점과 연속 구간

변경점(breakpoint)은 계정 구조가 크게 바뀐 지점이다. 연속 구간(segment)은 변경점 사이의 안정적인 구간이다.

```python
# 변경점
for bp in result.breakpoints:
    print(f"변경점: {bp.prevYear} → {bp.curYear} (매칭률 {bp.rate:.1%})")

# 연속 구간
for seg in result.segments:
    print(f"{seg.startYear}~{seg.endYear} ({seg.nYears}년, 매칭률 {seg.rate:.1%})")
```

---

## 분기별·반기별 분석

`fsSummary()`의 `period` 파라미터로 분석 단위를 변경한다.

```python
quarterly = c.fsSummary(period="q")   # 분기별
semiannual = c.fsSummary(period="h")  # 반기별
annual = c.fsSummary(period="y")      # 연간 (기본값)
```

| 값 | 의미 | 포함 보고서 |
|-----|------|------------|
| `"y"` | 연간 (기본값) | 사업보고서 |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 |
| `"h"` | 반기별 | 반기 + 사업 |

```python
# 분기별 재무제표
print(quarterly.BS)   # 분기별 재무상태표
# account | 2020Q1 | 2020Q2 | 2020Q3 | 2020Q4 | 2021Q1 | ...
```

---

## 공시 목록 확인

해당 종목의 공시 목록과 DART 뷰어 링크를 조회한다.

```python
c.docs()
# year | reportType | rceptDate | rceptNo | dartUrl
```

---

## 전체 일괄 조회

`all()`을 호출하면 40개 모듈을 순회하면서 전체 데이터를 dict로 반환한다. progress bar가 표시된다.

```python
d = c.all()

print(list(d.keys()))
# ['BS', 'IS', 'CF', 'dividend', 'majorHolder', 'employee', ..., 'notes']

d["BS"]                  # 재무상태표
d["dividend"]            # 배당 시계열
d["notes"]["inventory"]  # 재고자산
```

---

## 가이드 출력

`guide()`를 호출하면 사용 가능한 모든 property 목록이 터미널에 출력된다.

```python
c.guide()
```

---

## 보유 데이터 확인

```python
# 로컬에 있는 전체 종목 인덱스
Company.status()
# stockCode | corpName | rows | yearFrom | yearTo | nDocs

# 종목 검색
Company.search("반도체")

# 전체 상장기업 목록
Company.listing()
```

---

## 진행 표시 끄기

```python
import dartlab

dartlab.verbose = False
c = Company("005930")   # 조용히 생성
d = c.all()              # progress bar 없이 실행
```

---

## 다음 단계

- [2. 재무제표 조회](./financial-statements) — BS, IS, CF 상세 조회와 데이터 구조
- [3. 시계열 분석](./timeseries) — 계정 표준화, 분기별 독립 시계열, TTM
- [API Overview](../api/overview) — property 전체 목록
