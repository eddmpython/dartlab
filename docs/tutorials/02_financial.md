---
title: "2. Financial Deep Dive"
---

# 2. Financial Deep Dive — 재무 심화 분석

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial.ipynb)

정기보고서에 포함된 재무 데이터를 깊이 있게 분석한다. 모든 데이터는 property 한 줄로 접근한다.

- 배당 시계열 (DPS, 배당수익률, 배당성향)
- 직원 현황 (인원, 평균연봉, 근속연수)
- 최대주주와 지분 구조
- 부문별 매출
- 비용의 성격별 분류
- 주식의 총수와 자기주식
- 임원 현황과 보수
- 채무증권과 타법인 출자

## 준비

```python
from dartlab import Company

c = Company("005930")
```

## 배당

```python
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

연도별 DPS, 배당수익률, 배당성향을 시계열로 확인한다. 당기순이익 대비 배당성향 추이를 한눈에 볼 수 있다.

## 직원 현황

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

총 직원수, 평균 근속연수, 연간 급여 총액, 1인당 평균 연봉의 시계열이다.

## 최대주주

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

최대주주명과 지분율의 시계열이다. 더 상세한 정보가 필요하면 `get()`으로 접근한다.

```python
result = c.get("majorHolder")

result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 합계 지분율

# 개별 주주 목록
for h in result.holders:
    print(f"{h.name} ({h.relation}): {h.ratioEnd}%")
```

## 주주 종합 현황

5% 이상 주주, 소액주주, 의결권 현황을 종합적으로 조회한다.

```python
result = c.holderOverview

for bh in result.bigHolders:
    print(f"{bh.name}: {bh.ratio}%")

print(f"소액주주 비율: {result.minority.ratio}%")
print(f"의결권 행사 가능: {result.voting.exercisableShares}")
```

## 주식의 총수

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

발행주식, 자기주식, 유통주식의 시계열이다. `get()`으로 개별 필드도 접근 가능하다.

```python
result = c.get("shareCapital")
result.authorizedShares    # 발행할 주식의 총수
result.treasuryRatio       # 자사주 비율
```

## 부문별 매출

K-IFRS 주석의 부문정보를 추출한다.

```python
c.notes.segments
# 부문별 매출 시계열 DataFrame
```

연도별 상세 테이블은 `get()`으로 접근한다.

```python
result = c.get("segments")
for year, tables in result.tables.items():
    for t in tables:
        print(f"[{year}] {t.tableType}: {t.columns}")
```

## 비용의 성격별 분류

원재료비, 인건비, 감가상각비 등 비용 항목별 시계열이다.

```python
c.notes.costByNature
# 비용 항목별 시계열 DataFrame
```

비용 비율과 교차 검증도 확인 가능하다.

```python
result = c.get("costByNature")
print(result.ratios)      # 구성비
print(result.crossCheck)  # 교차 검증 결과
```

## 임원 현황

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | maleCount | femaleCount
```

등기임원 구성의 시계열이다. 사내이사/사외이사 비율, 성별 구성 등을 추적한다.

## 임원 보수

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

유형별 보수 시계열이다. 5억 초과 개인별 보수는 `get()`으로 접근한다.

```python
result = c.get("executivePay")
print(result.topPayDf)   # 5억 초과 개인별 보수
```

## 감사의견

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

감사법인, 감사의견, 핵심감사사항의 시계열이다. 감사보수는 `get()`으로 접근한다.

```python
result = c.get("audit")
print(result.feeDf)   # 감사보수 시계열
```

## 채무증권

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

회사채, 기업어음 등 채무증권 발행 현황의 시계열이다.

## 자회사

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

## 여러 종목 비교

property 접근으로 간결하게 비교 분석할 수 있다.

```python
import polars as pl

codes = ["005930", "000660", "035420"]
rows = []

for code in codes:
    c = Company(code)
    div = c.dividend
    if div is not None:
        last = div.row(-1, named=True)
        rows.append({
            "기업": c.corpName,
            "DPS": last.get("dps"),
            "배당수익률": last.get("dividendYield"),
            "배당성향": last.get("payoutRatio")
        })

print(pl.DataFrame(rows))
```

## 다음 단계

- [3. Disclosure Text](./disclosure) — 사업의 내용, MD&A, 회사의 개요
- [4. Advanced Analysis](./advanced) — K-IFRS 주석, 유형자산, 교차 분석
