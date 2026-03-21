---
title: "7. Advanced Analysis"
---

# 7. Advanced Analysis

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/07_advanced.ipynb)

Covers deep source namespace access including K-IFRS Notes integration, tangible asset movement schedules, affiliate analysis, and governance analysis. The standard public flow is `sections -> show -> trace`, but this document explains the deep access layer beneath it.

- Notes integration (12 items)
- Direct lookup for unregistered keywords (23 keywords)
- Tangible asset movement schedule
- Associates and joint ventures
- Board of directors and audit system
- Governance and risk analysis
- Multi-company comparison
- Result objects and deep access patterns

---

## Setup

```python
import dartlab

c = dartlab.Company("005930")
```

---

## K-IFRS Notes

Access 12 K-IFRS note items through `c.notes`. Both English property names and Korean keys are supported.

### Access via English Properties

```python
c.notes.inventory          # 재고자산 DataFrame
c.notes.receivables        # 매출채권
c.notes.borrowings         # 차입금
c.notes.tangibleAsset      # 유형자산 변동표
c.notes.intangibleAsset    # 무형자산
c.notes.provisions         # 충당부채
c.notes.eps                # 주당이익
c.notes.lease              # 리스
c.notes.investmentProperty # 투자부동산
c.notes.affiliates         # 관계기업
c.notes.segments           # 부문정보
c.notes.costByNature       # 비용의 성격별 분류
```

### Access via Korean Keys

```python
c.notes["재고자산"]         # Same as c.notes.inventory
c.notes["차입금"]           # Same as c.notes.borrowings
c.notes["유형자산"]         # Same as c.notes.tangibleAsset
```

### Listing All Keys

```python
c.notes.keys()       # ['receivables', 'inventory', 'tangibleAsset', ...]
c.notes.keys_kr()    # ['매출채권', '재고자산', '유형자산', ...]
c.notes.keys()       # Available notes keys
```

---

## Direct Lookup for Unregistered Keywords

Beyond the 12 main keywords, 23 additional keywords are supported. Keywords not registered in Notes can be accessed directly via the `docs.notes` namespace.

```python
# Corporate tax
result = c.docs.notes.detail("법인세")
print(result.tableDf)

# Related parties
result = c.docs.notes.detail("특수관계자")
print(result.tableDf)
```

### All 23 Keywords

`재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`

### Year-by-Year Detail Tables

Notes returns only DataFrames, but year-by-year detail tables are also accessible through the raw Result object.

```python
result = c.docs.notes.detail("재고자산")
for year, periods in result.tables.items():
    for p in periods:
        print(f"[{year}] {p.period} (패턴: {p.pattern})")
        for item in p.items[:3]:
            print(f"  {item.name}: {item.values}")
```

---

## Tangible Asset Movement Schedule

Accessed through Notes. The full Result can also be obtained via `report.extract()`.

```python
# Via Notes
c.notes.tangibleAsset   # Opening/closing balance timeseries by category

# Full Result via report.extract()
result = c.report.extract("tangibleAsset")
print(f"Reliability: {result.reliability}")  # "high" or "low"
if result.warnings:
    print(f"Warnings: {result.warnings}")
print(result.movementDf)   # Opening/closing balance timeseries by category
```

### Year-by-Year Movement Details

```python
for year, movements in result.movements.items():
    for m in movements:
        print(f"[{year}] {m.period}")
        print(f"  Categories: {m.categories}")
        for row in m.rows:
            print(f"  {row}")
```

---

## Associates and Joint Ventures

Accessed through Notes.

```python
# Via Notes
c.notes.affiliates   # Movement timeseries DataFrame

# Full Result via report.extract()
result = c.report.extract("affiliates")
for year, profiles in result.profiles.items():
    for p in profiles:
        print(f"[{year}] {p.name}: {p.ratio}%, book value {p.bookValue}")
```

---

## Board of Directors

```python
c.show("board")   # alias for boardOfDirectors
# year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
```

Committee composition is also available.

```python
result = c.report.extract("boardOfDirectors")
print(result.boardDf)       # Board timeseries
print(result.committeeDf)   # Committee composition (committeeName, composition, members)
```

---

## Audit System

```python
c.show("auditSystem")
# name | role | detail
```

Audit activity details are also available.

```python
result = c.report.extract("auditSystem")
print(result.committeeDf)   # Audit committee composition
print(result.activityDf)    # Audit activities (date, agenda, result)
```

---

## Internal Controls

```python
c.show("control")   # alias for internalControl
# year | opinion | auditor | hasWeakness
```

---

## Governance and Risk Overview

```python
# Related party transactions
c.show("relatedParty")   # alias for relatedPartyTx
# year | entity | sales | purchases

# Contingent liabilities
c.show("contingent")     # alias for contingentLiability
# year | totalGuaranteeAmount

# Sanctions
c.show("sanction")
# year | date | agency | action | amount

# Risk management
c.show("risk")           # alias for riskDerivative
# currency | upImpact | downImpact
```

### Related Party Transaction Details

```python
result = c.report.extract("relatedPartyTx")
print(result.revenueTxDf)    # Revenue transactions
print(result.guaranteeDf)    # Debt guarantees
print(result.assetTxDf)      # Asset transactions
```

### Contingent Liability Details

```python
result = c.report.extract("contingentLiability")
print(result.guaranteeDf)    # Debt guarantees
print(result.lawsuitDf)      # Litigation status
```

---

## Multi-Company Comparison

You can call the same deep access payload across multiple companies for comparison.

### Financial Comparison

```python
import polars as pl

codes = ["005930", "000660", "035420"]
rows = []

for code in codes:
    c = dartlab.Company(code)
    bs = c.BS
    if bs is not None:
        # Check total assets for the latest year
        cols = [col for col in bs.columns if col != "account"]
        last_year = cols[-1]
        row = bs.filter(pl.col("account") == "자산총계")
        if row.height > 0:
            rows.append({
                "기업": c.corpName,
                "자산총계": row[last_year][0],
            })

print(pl.DataFrame(rows))
```

### Dividend Comparison

```python
dividends = []
for code in codes:
    c = dartlab.Company(code)
    div = c.dividend
    if div is not None:
        last = div.row(-1, named=True)
        dividends.append({
            "기업": c.corpName,
            "DPS": last.get("dps"),
            "배당수익률": last.get("dividendYield"),
            "배당성향": last.get("payoutRatio")
        })

print(pl.DataFrame(dividends))
```

---

## Result Object Access

Properties return a single representative DataFrame. When you need the full data from a module, use `report.extract()`.

```python
# Property → representative DataFrame
c.audit   # Returns opinionDf only

# report.extract() → full Result object
result = c.report.extract("audit")
result.opinionDf   # Audit opinion
result.feeDf       # Audit fees
```

> The standard path is `c.show("audit")`. Only use `c.report.extract()` when deep access is needed.

---

## Next Steps

- [8. Cross-Company Comparison](./cross-company) — Sector classification, insight grades, market ranking
- [API Overview](../api/overview) — Public surface and source namespaces
- [Account Standardization and Timeseries](../api/timeseries) — 7-step mapping, snakeId, normalization
