---
title: "1. Quickstart"
---

# 1. Quickstart — 첫 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/01_quickstart.ipynb)

종목코드 하나로 DART 전자공시 분석을 시작한다. 이 튜토리얼에서 다루는 내용은 다음과 같다.

- Company 클래스 생성과 기본 정보 조회
- 요약재무정보 시계열 분석 (Bridge Matching)
- 연결재무제표 BS/IS/CF 추출
- 분기별·반기별 분석
- 보유 데이터 확인

## Company 생성

모든 분석의 시작점이다. 종목코드 또는 회사명으로 생성한다.

```python
from dartlab import Company

samsung = Company("005930")
samsung.corpName   # "삼성전자"
samsung.stockCode  # "005930"
```

회사명으로도 가능하다.

```python
kakao = Company("카카오")
kakao.stockCode    # "035720"
```

## 공시 목록 확인

해당 종목의 공시 목록과 DART 뷰어 링크를 조회한다.

```python
docs = samsung.docs()
print(docs)
# year, reportType, rceptDate, rceptNo, dartUrl
```

## 요약재무정보 분석

`fsSummary()`는 Bridge Matching으로 계정명 변경을 추적하면서 시계열을 생성한다.

```python
result = samsung.fsSummary()

result.corpName      # "삼성전자"
result.nYears        # 분석 연도 수
result.allRate       # 전체 매칭률 (0.0~1.0)
result.nBreakpoints  # 변경점 수
```

### 재무제표 DataFrame

```python
result.FS   # 전체 재무제표 시계열 (Polars DataFrame)
result.BS   # 재무상태표
result.IS   # 손익계산서
```

### Bridge Matching 결과

연도별 매칭 결과를 확인한다.

```python
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%} ({pair.matched}/{pair.total})")
```

변경점(breakpoint)은 계정 구조가 크게 바뀐 지점이다.

```python
for bp in result.breakpoints:
    print(f"변경점: {bp.prevYear} → {bp.curYear}")
```

연속 구간(segment)은 변경점 사이의 안정적인 구간이다.

```python
for seg in result.segments:
    print(f"{seg.startYear}~{seg.endYear} ({seg.nYears}년, 매칭률 {seg.rate:.1%})")
```

## 연결재무제표

`statements()`는 재무상태표, 손익계산서, 현금흐름표를 상세 항목 수준으로 추출한다.

```python
result = samsung.statements()

print(result.BS)  # 재무상태표 — 자산, 부채, 자본 상세
print(result.IS)  # 손익계산서 — 매출, 비용, 이익 상세
print(result.CF)  # 현금흐름표 — 영업/투자/재무
```

## 분기별·반기별 분석

`period` 파라미터로 분석 단위를 변경한다.

```python
quarterly = samsung.fsSummary(period="q")   # 분기별
semiannual = samsung.fsSummary(period="h")  # 반기별
annual = samsung.fsSummary(period="y")      # 연간 (기본값)
```

| 값 | 의미 | 포함 보고서 |
|-----|------|------------|
| `"y"` | 연간 (기본값) | 사업보고서 |
| `"q"` | 분기별 | 1분기 + 반기 + 3분기 + 사업 |
| `"h"` | 반기별 | 반기 + 사업 |

## 보유 데이터 확인

로컬에 있는 전체 종목 인덱스를 조회한다.

```python
index = Company.status()
print(index)
# stockCode, corpName, rows, yearFrom, yearTo, nDocs
```

종목 검색도 가능하다.

```python
results = Company.search("삼성")
print(results)
```

## 다음 단계

- [2. Financial Deep Dive](./financial) — 배당, 직원, 최대주주, 부문별 매출
- [API Overview](../api/overview) — 전체 메서드 목록
