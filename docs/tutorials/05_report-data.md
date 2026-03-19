---
title: "5. Report Data"
---

# 5. Report Data — 정기보고서 데이터

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/05_report_data.ipynb)

정기보고서에 포함된 재무 외 데이터를 깊이 있게 분석한다. 재무제표는 [2. 재무제표 조회](./financial-statements)에서 다뤘고, 여기서는 배당, 직원, 주주, 감사 등 정기보고서 API가 제공하는 데이터를 다룬다.

> **canonical 접근 경로**: `c.show("dividend")`, `c.show("audit")` 등 `show(topic)`이 기본이다. 이 튜토리얼에서는 `report` namespace로 직접 내려가 세부 payload까지 확인하는 deep access 패턴도 함께 다룬다.

- 배당 시계열 (DPS, 배당수익률, 배당성향)
- 직원 현황 (인원, 평균연봉, 근속연수)
- 최대주주와 지분 구조
- 주주 종합 현황
- 주식의 총수와 자기주식
- 부문별 매출
- 비용의 성격별 분류
- 임원 현황과 보수
- 감사의견과 감사보수
- 채무증권과 타법인 출자

---

## 준비

```python
import dartlab

c = dartlab.Company("005930")
```

---

## 배당

```python
# canonical 경로
c.show("dividend")

# report namespace direct access
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

연도별 DPS, 배당수익률, 배당성향을 시계열로 확인한다. 당기순이익 대비 배당성향 추이를 한눈에 볼 수 있다.

```python
# 최근 배당 정보 확인
div = c.dividend
if div is not None:
    last = div.row(-1, named=True)
    print(f"DPS: {last['dps']}원")
    print(f"배당수익률: {last['dividendYield']}%")
    print(f"배당성향: {last['payoutRatio']}%")
```

| 컬럼 | 의미 |
|------|------|
| `netIncome` | 당기순이익 |
| `eps` | 주당순이익 |
| `totalDividend` | 배당금 총액 |
| `payoutRatio` | 배당성향 (배당금/순이익) |
| `dividendYield` | 배당수익률 (DPS/주가) |
| `dps` | 보통주 1주당 배당금 |
| `dpsPreferred` | 우선주 1주당 배당금 |

---

## 직원 현황

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

총 직원수, 평균 근속연수, 연간 급여 총액, 1인당 평균 연봉의 시계열이다.

직원수의 급격한 변화는 사업 확장/축소 또는 구조조정의 신호일 수 있다. 평균연봉 대비 업계 수준을 비교하면 인재 유치 경쟁력을 가늠할 수 있다.

---

## 최대주주

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

최대주주명과 지분율의 시계열이다. 더 상세한 정보가 필요하면 `report.extract()`로 접근한다.

```python
result = c.report.extract("majorHolder")

result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # 특수관계인 합계 지분율

# 개별 주주 목록
for h in result.holders:
    print(f"{h.name} ({h.relation}): {h.ratioEnd}%")
```

최대주주 지분율이 너무 낮으면 경영권 리스크가 있고, 특수관계인 합계 지분율이 높으면 경영 안정성은 좋지만 소액주주 권익 침해 가능성을 살펴야 한다.

---

## 주주 종합 현황

5% 이상 주주, 소액주주, 의결권 현황을 종합적으로 조회한다.

```python
result = c.holderOverview

for bh in result.bigHolders:
    print(f"{bh.name}: {bh.ratio}%")

if result.minority:
    print(f"소액주주 비율: {result.minority.ratio}%")

if result.voting:
    print(f"의결권 행사 가능: {result.voting.exercisableShares}")
```

---

## 주식의 총수

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

발행주식, 자기주식, 유통주식의 시계열이다. `report.extract()`로 개별 필드도 접근 가능하다.

```python
result = c.report.extract("shareCapital")
print(f"발행주식: {result.issuedShares:,.0f}")
print(f"자기주식: {result.treasuryShares:,.0f}")
print(f"자사주 비율: {result.treasuryRatio:.2%}")
```

자기주식 비율이 높으면 실질 유통주식이 적어 주가에 영향을 줄 수 있다. 자사주 매입/소각 추이도 확인해볼 만하다.

---

## 부문별 매출

K-IFRS 주석의 부문정보를 추출한다.

```python
c.notes.segments
# 부문별 매출 시계열 DataFrame
```

연도별 상세 테이블은 `report.extract()`로 접근한다.

```python
result = c.report.extract("segments")
print(result.revenue)   # 부문별 매출 시계열

for year, tables in result.tables.items():
    for t in tables:
        print(f"[{year}] {t.tableType}: {t.columns}")
```

매출이 특정 부문에 집중되어 있으면 해당 부문의 경기에 민감하다. 부문 다각화 추이를 보면 사업 전략을 읽을 수 있다.

---

## 비용의 성격별 분류

원재료비, 인건비, 감가상각비 등 비용 항목별 시계열이다.

```python
c.notes.costByNature
# 비용 항목별 시계열 DataFrame
```

비용 비율과 교차 검증도 확인 가능하다.

```python
result = c.report.extract("costByNature")
print(result.timeSeries)  # 비용 시계열
print(result.ratios)      # 구성비
print(result.crossCheck)  # 교차 검증 결과
```

원재료비 비중이 높으면 원자재 가격에 민감하고, 인건비 비중이 높으면 인력 집약적 사업이다.

---

## 임원 현황

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | maleCount | femaleCount
```

등기임원 구성의 시계열이다. 사내이사/사외이사 비율, 성별 구성 등을 추적한다.

미등기임원 보수는 `report.extract()`로:

```python
result = c.report.extract("executive")
print(result.executiveDf)   # 등기임원 시계열
print(result.unregPayDf)    # 미등기임원 보수
```

---

## 임원 보수

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

유형별 보수 시계열이다. 5억 초과 개인별 보수는 `report.extract()`로 접근한다.

```python
result = c.report.extract("executivePay")
print(result.payByTypeDf)   # 유형별 보수
print(result.topPayDf)      # 5억 초과 개인별 보수
```

임원 보수가 실적 대비 과도하면 지배구조 리스크 신호다. 5억 초과 공시 대상 임원의 보수 구조(급여 vs 상여 vs 주식보상)도 확인해볼 만하다.

---

## 감사의견

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

감사법인, 감사의견, 핵심감사사항의 시계열이다. 감사보수는 `report.extract()`로 접근한다.

```python
result = c.report.extract("audit")
print(result.opinionDf)   # 감사의견 시계열
print(result.feeDf)        # 감사보수 시계열
```

| 감사의견 | 의미 |
|----------|------|
| 적정 | 정상 — 재무제표를 신뢰할 수 있다 |
| 한정 | 일부 항목에 문제 — 해당 항목을 주의깊게 봐야 한다 |
| 부적정 | 재무제표 전체를 신뢰할 수 없다 |
| 의견거절 | 감사를 수행할 수 없었다 — 가장 심각한 경고 |

감사의견이 "적정"이 아니면 다른 분석 결과를 모두 재검토해야 한다.

---

## 채무증권

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

회사채, 기업어음 등 채무증권 발행 현황의 시계열이다.

`report.extract()`로 개별 발행 내역:

```python
result = c.report.extract("bond")
for b in result.issuances[:5]:
    print(f"{b.bondType} | {b.amount}백만원 | {b.interestRate}")
```

---

## 자회사

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

`report.extract()`로 개별 투자법인:

```python
result = c.report.extract("subsidiary")
for inv in result.investments[:5]:
    print(f"{inv.name}: {inv.endRatio}%, 장부가 {inv.endBook}")
```

---

## 여러 종목 비교

같은 report payload를 여러 회사에서 반복 호출해 비교할 수 있다.

```python
import polars as pl

codes = ["005930", "000660", "035420"]
rows = []

for code in codes:
    c = dartlab.Company(code)
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

---

## 다음 단계

- [6. 공시 텍스트](./disclosure) — 사업의 내용, MD&A, 회사의 개요
- [7. 고급 분석](./advanced) — K-IFRS 주석, 유형자산, 교차 분석


