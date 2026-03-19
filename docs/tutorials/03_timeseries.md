---
title: "3. Time Series"
---

# 3. Time Series — Account Standardization and Standalone Quarterly Data

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/03_timeseries.ipynb)

As seen in [2. Financial Statements](./financial-statements), DART raw data has different account names across companies and quarterly data is cumulative. This tutorial covers DartLab's time series engine that solves both problems.

- Why account standardization is needed
- Generating time series (`timeseries` property)
- Understanding the return structure (dict + period list)
- Cumulative → standalone quarterly conversion logic
- Querying specific accounts
- TTM (Trailing Twelve Months)
- Annual time series
- Comparing time series across companies

---

## Setup

```python
import dartlab
```

---

## Why Account Standardization Is Needed

When fetching "revenue" from DART, each company uses a different name:

```
Samsung Electronics:  ifrs-full_Revenue      → 수익(매출액)
SK Hynix:            dart_OperatingRevenue  → 영업수익
Hyundai Motor:       ifrs-full_Revenue      → 매출액
Kakao:               dart_Revenue           → 수익(매출액)
KB Financial:        dart_OperatingRevenue  → 영업수익
```

Same "revenue" but different XBRL IDs and Korean names. Cross-company comparison is impossible in this state.

DartLab solves this with a **7-stage mapping pipeline**:

```
Original account_id, account_nm
  ↓ prefix removal (ifrs-full_, dart_, ifrs_, etc.)
  ↓ ID synonym unification (English variant cleanup)
  ↓ name synonym unification (Korean variant cleanup)
  ↓ core account override (50 highest-priority mappings)
  ↓ learned mapping lookup (34,000+ synonyms)
  ↓ bracket removal + re-lookup (fallback)
  ↓ standardized snakeId returned
```

As a result, every company's revenue becomes `revenue`, operating income becomes `operating_income`, and total assets becomes `total_assets` — all accessible with a single key.

Mapping rate across all 2,700 companies is **98.7%**, and the balance sheet identity check (assets = liabilities + equity) passes at **99.7%**.

---

## Generating Time Series

Use the `Company.timeseries` property to get quarterly time series.

```python
c = dartlab.Company("005930")
series, periods = c.timeseries
```

This single line internally:
1. Loads the raw financial parquet
2. Standardizes accounts using 34,000+ synonyms
3. Prioritizes consolidated (CFS), deduplicates row-by-row
4. IS/CF: converts cumulative → standalone quarterly
5. BS: keeps point-in-time balances as-is

---

## Return Structure

```python
series, periods = c.timeseries
```

`series` is a dict of dicts by financial statement:

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

`periods` is a list of quarterly labels:

```python
periods = ["2016_Q1", "2016_Q2", "2016_Q3", "2016_Q4",
           "2017_Q1", "2017_Q2", ...,
           "2024_Q3", "2024_Q4"]
```

The value lists in `series` correspond index-by-index with `periods`. `series["IS"]["revenue"][0]` is the revenue for `periods[0]` (2016_Q1).

### Basic Access Pattern

```python
# Samsung recent 4 quarters revenue
series, periods = c.timeseries

for i in range(-4, 0):
    period = periods[i]
    rev = series["IS"]["revenue"][i]
    if rev:
        print(f"{period}: {rev/1e12:,.1f}T KRW")
```

### Checking Available snakeIds

```python
# what accounts exist in the balance sheet
print(list(series["BS"].keys()))

# income statement
print(list(series["IS"].keys()))

# cash flow statement
print(list(series["CF"].keys()))
```

Key snakeIds:

| Statement | snakeId | Meaning |
|-----------|---------|---------|
| BS | `total_assets` | Total assets |
| BS | `current_assets` | Current assets |
| BS | `total_liabilities` | Total liabilities |
| BS | `total_equity` | Equity attributable to parent |
| BS | `equity_including_nci` | Total equity (including NCI) |
| IS | `revenue` | Revenue |
| IS | `operating_income` | Operating income |
| IS | `net_income` | Net income |
| IS | `cost_of_sales` | Cost of sales |
| IS | `gross_profit` | Gross profit |
| CF | `operating_cashflow` | Operating cash flow |
| CF | `investing_cashflow` | Investing cash flow |
| CF | `financing_cashflow` | Financing cash flow |

---

## Cumulative → Standalone Quarterly Conversion

DART quarterly reports are filed in a **cumulative structure**:

```
Q1 report:      Q1 revenue = 40B
Semi-annual:    Q1+Q2 revenue = 100B  (Q2 alone = 60B)
Q3 report:      Q1+Q2+Q3 revenue = 220B  (Q3 alone = 120B)
Annual report:  Q1+Q2+Q3+Q4 revenue = 300B  (Q4 alone = 80B)
```

The time series engine automatically converts cumulative values to standalone quarterly values:

```
Cumulative                  Standalone
Q1:         40B     →    Q1:   40B  (as-is)
Q1+Q2:     100B     →    Q2:   60B  (100B - 40B)
Q1+Q2+Q3:  220B     →    Q3:  120B  (220B - 100B)
Annual:    300B     →    Q4:   80B  (300B - 220B)
```

This conversion applies only to **Income Statement (IS)** and **Cash Flow Statement (CF)**. Balance Sheet (BS) values are point-in-time balances and are not converted.

```python
# already standalone quarterly values
series["IS"]["revenue"]  # [Q1 rev, Q2 rev, Q3 rev, Q4 rev, ...]

# BS is point-in-time balance as-is
series["BS"]["total_assets"]  # [Q1-end balance, Q2-end balance, ...]
```

---

## Account Query Functions

Helper functions for easily extracting specific values from the time series:

```python
from dartlab.engines.dart.finance import getTTM, getLatest
```

### getLatest — Most Recent Value

```python
series, periods = c.timeseries

# most recent quarter total assets
assets = getLatest(series, "BS", "total_assets")
print(f"Total Assets: {assets/1e12:,.1f}T KRW")

# most recent quarter cash
cash = getLatest(series, "BS", "cash_and_equivalents")
```

### getTTM — Trailing Twelve Months Sum

TTM sums the most recent 4 quarters. It's the most current approximation of annual performance, with seasonality effects removed.

```python
# annual revenue (sum of last 4 quarters)
rev_ttm = getTTM(series, "IS", "revenue")
print(f"TTM Revenue: {rev_ttm/1e12:,.1f}T KRW")

# annual operating income (sum of last 4 quarters)
oi_ttm = getTTM(series, "IS", "operating_income")
print(f"TTM Operating Income: {oi_ttm/1e12:,.1f}T KRW")

# operating margin
if rev_ttm and oi_ttm:
    margin = oi_ttm / rev_ttm * 100
    print(f"Operating Margin: {margin:.1f}%")
```

> TTM is only meaningful for IS and CF. For BS, use `getLatest` since values are point-in-time balances.

---

## Annual Time Series

When you need yearly aggregated time series instead of quarterly:

```python
from dartlab.engines.dart.finance import buildAnnual

annual_series, years = buildAnnual("005930")

# years = ["2016", "2017", ..., "2024"]
# annual_series structure is identical to quarterly time series

for i, year in enumerate(years[-5:], len(years)-5):
    rev = annual_series["IS"]["revenue"][i]
    if rev:
        print(f"{year}: Revenue {rev/1e12:,.1f}T KRW")
```

---

## Comparing Time Series Across Companies

Since accounts are standardized, you can compare any company using the same key.

```python
companies = [
    dartlab.Company("005930"),   # Samsung Electronics
    dartlab.Company("000660"),   # SK Hynix
    dartlab.Company("035420"),   # NAVER
]

for comp in companies:
    s, p = comp.timeseries
    rev = getTTM(s, "IS", "revenue")
    oi = getTTM(s, "IS", "operating_income")
    assets = getLatest(s, "BS", "total_assets")

    rev_str = f"{rev/1e12:,.1f}T" if rev else "N/A"
    oi_str = f"{oi/1e12:,.1f}T" if oi else "N/A"
    asset_str = f"{assets/1e12:,.1f}T" if assets else "N/A"

    print(f"{comp.corpName}: Revenue {rev_str} / OpIncome {oi_str} / Assets {asset_str}")
```

### Side-by-Side Revenue Comparison

```python
samsung = dartlab.Company("005930")
sk = dartlab.Company("000660")

s1, p1 = samsung.timeseries
s2, p2 = sk.timeseries

# compare last 8 quarters revenue
for i in range(-8, 0):
    period = p1[i]
    r1 = s1["IS"]["revenue"][i]
    r2 = s2["IS"]["revenue"][i] if abs(i) <= len(s2["IS"]["revenue"]) else None

    r1_str = f"{r1/1e12:,.1f}T" if r1 else "N/A"
    r2_str = f"{r2/1e12:,.1f}T" if r2 else "N/A"
    print(f"{period}: Samsung {r1_str} / SK Hynix {r2_str}")
```

---

## Caveats

### None Values

Quarters without data are `None`. Always check for `None` in calculations.

```python
rev = series["IS"]["revenue"]
# [None, None, 40B, 60B, ...]  ← early quarters may lack data
```

### Banks and Financial Companies

Banks, insurance, and securities firms have different financial statement structures. `revenue`, `current_assets`, etc. may not exist. Instead, financial-industry-specific accounts like `interest_income`, `fee_income` are present.

### Data Start Date

Each company has a different data start date depending on when it was listed. Some start from 2016, others from 2020.

---

## Next Steps

- [4. Ratios](./ratios) — Financial ratios auto-calculated from time series
- [5. Report Data](./report-data) — Dividends, employees, shareholders, audit, and more

