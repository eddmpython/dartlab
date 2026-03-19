---
title: "5. Report Data"
---

# 5. Report Data — Periodic Report Data

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/05_report_data.ipynb)

Deep analysis of non-financial data from periodic reports. Financial statements were covered in [2. Financial Statements](./financial-statements); here we cover data provided by periodic report APIs — dividends, employees, shareholders, audit, and more.

> **Canonical access path**: `c.show("dividend")`, `c.show("audit")`, etc. via `show(topic)` is the default. This tutorial also shows deep access patterns via the `report` namespace for detailed payloads.

- Dividend time series (DPS, dividend yield, payout ratio)
- Employee data (headcount, average salary, tenure)
- Largest shareholder and ownership structure
- Comprehensive shareholder overview
- Total shares and treasury stock
- Segment revenue
- Cost by nature breakdown
- Executive roster and compensation
- Audit opinion and audit fees
- Debt securities and subsidiary investments

---

## Setup

```python
import dartlab

c = dartlab.Company("005930")
```

---

## Dividends

```python
# canonical path
c.show("dividend")

# report namespace direct access
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

View DPS, dividend yield, and payout ratio as a time series. Easily track payout ratio trends relative to net income.

```python
# check latest dividend info
div = c.dividend
if div is not None:
    last = div.row(-1, named=True)
    print(f"DPS: {last['dps']} KRW")
    print(f"Dividend Yield: {last['dividendYield']}%")
    print(f"Payout Ratio: {last['payoutRatio']}%")
```

| Column | Meaning |
|--------|---------|
| `netIncome` | Net income |
| `eps` | Earnings per share |
| `totalDividend` | Total dividend amount |
| `payoutRatio` | Payout ratio (dividends / net income) |
| `dividendYield` | Dividend yield (DPS / share price) |
| `dps` | Common share dividend per share |
| `dpsPreferred` | Preferred share dividend per share |

---

## Employee Data

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

Time series of total headcount, average tenure, total annual salary, and average salary per employee.

Sharp changes in headcount may signal business expansion/contraction or restructuring. Comparing average salary against industry levels provides insight into talent competitiveness.

---

## Largest Shareholder

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

Time series of the largest shareholder's name and stake. For more detail, access via `report.extract()`:

```python
result = c.report.extract("majorHolder")

result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # total related-party stake

# individual shareholder list
for h in result.holders:
    print(f"{h.name} ({h.relation}): {h.ratioEnd}%")
```

A very low largest-shareholder stake may indicate management control risk. A high total related-party stake suggests management stability but may raise minority shareholder concerns.

---

## Comprehensive Shareholder Overview

Query 5%+ holders, minority shareholders, and voting rights comprehensively.

```python
result = c.holderOverview

for bh in result.bigHolders:
    print(f"{bh.name}: {bh.ratio}%")

if result.minority:
    print(f"Minority shareholder ratio: {result.minority.ratio}%")

if result.voting:
    print(f"Exercisable voting shares: {result.voting.exercisableShares}")
```

---

## Total Shares

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

Time series of issued shares, treasury stock, and outstanding shares. Individual fields accessible via `report.extract()`:

```python
result = c.report.extract("shareCapital")
print(f"Issued shares: {result.issuedShares:,.0f}")
print(f"Treasury shares: {result.treasuryShares:,.0f}")
print(f"Treasury ratio: {result.treasuryRatio:.2%}")
```

A high treasury stock ratio means fewer shares in circulation, potentially impacting share price. Buyback and cancellation trends are also worth monitoring.

---

## Segment Revenue

Extracts segment information from K-IFRS footnotes.

```python
c.notes.segments
# segment revenue time-series DataFrame
```

For detailed year-by-year tables, use `report.extract()`:

```python
result = c.report.extract("segments")
print(result.revenue)   # segment revenue time series

for year, tables in result.tables.items():
    for t in tables:
        print(f"[{year}] {t.tableType}: {t.columns}")
```

Revenue concentrated in a single segment means high sensitivity to that segment's business cycle. Segment diversification trends reveal business strategy.

---

## Cost by Nature

Time series of cost items: raw materials, labor, depreciation, etc.

```python
c.notes.costByNature
# cost-by-nature time-series DataFrame
```

Cost ratios and cross-validation also available:

```python
result = c.report.extract("costByNature")
print(result.timeSeries)  # cost time series
print(result.ratios)      # composition ratios
print(result.crossCheck)  # cross-validation results
```

High raw material costs indicate commodity price sensitivity. High labor costs indicate a labor-intensive business.

---

## Executive Roster

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | maleCount | femaleCount
```

Time series of registered executive composition. Tracks inside/outside director ratio, gender composition.

For unregistered executive compensation:

```python
result = c.report.extract("executive")
print(result.executiveDf)   # registered executive time series
print(result.unregPayDf)    # unregistered executive compensation
```

---

## Executive Compensation

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

Compensation time series by category. For individual compensation above 500M KRW:

```python
result = c.report.extract("executivePay")
print(result.payByTypeDf)   # compensation by type
print(result.topPayDf)      # individuals above 500M KRW
```

Excessive executive compensation relative to performance is a governance risk signal. The compensation structure (base vs. bonus vs. stock) of top-paid executives is also worth examining.

---

## Audit Opinion

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

Time series of audit firm, opinion, and key audit matters. For audit fees:

```python
result = c.report.extract("audit")
print(result.opinionDf)   # audit opinion time series
print(result.feeDf)        # audit fee time series
```

| Audit Opinion | Meaning |
|---------------|---------|
| Unqualified | Normal — financial statements are trustworthy |
| Qualified | Issues in some items — examine those items carefully |
| Adverse | Cannot trust the financial statements as a whole |
| Disclaimer | Audit could not be performed — most serious warning |

If the audit opinion is anything other than "Unqualified", all other analysis results should be re-examined.

---

## Debt Securities

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

Time series of corporate bonds, commercial paper, and other debt securities.

For individual issuance details via `report.extract()`:

```python
result = c.report.extract("bond")
for b in result.issuances[:5]:
    print(f"{b.bondType} | {b.amount}M KRW | {b.interestRate}")
```

---

## Subsidiary Investments

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

For individual investee details via `report.extract()`:

```python
result = c.report.extract("subsidiary")
for inv in result.investments[:5]:
    print(f"{inv.name}: {inv.endRatio}%, book value {inv.endBook}")
```

---

## Comparing Across Companies

The same report payload can be called repeatedly across companies for comparison.

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
            "Company": c.corpName,
            "DPS": last.get("dps"),
            "Dividend Yield": last.get("dividendYield"),
            "Payout Ratio": last.get("payoutRatio")
        })

print(pl.DataFrame(rows))
```

---

## Next Steps

- [6. Disclosure Text](./disclosure) — Business description, MD&A, company overview
- [7. Advanced Analysis](./advanced) — K-IFRS footnotes, tangible assets, cross-analysis

