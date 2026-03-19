---
title: "2. Financial Statements"
---

# 2. Financial Statements

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial_statements.ipynb)

Financial statements are the starting point of company analysis. This tutorial covers how to query DART financial statements, understand the data structure, and extract specific items.

- Querying the 3 core statements (BS, IS, CF)
- Consolidated vs. separate financial statements
- Understanding the year column structure
- Filtering specific accounts
- Quarterly financial statements
- Limitations and caveats of the raw data

---

## Setup

```python
import dartlab

c = dartlab.Company("005930")
```

---

## The 3 Core Statements

Access the 3 core financial statements as properties on the `Company` object. These are property accesses, not method calls.

### Balance Sheet (BS)

```python
c.BS
```

The balance sheet shows the balances of assets, liabilities, and equity at a **specific point in time**. It answers: "As of December 31, what does the company own and owe?"

| Category | Meaning | Key Items |
|----------|---------|-----------|
| Assets | Economic resources held | Current assets, non-current assets, total assets |
| Liabilities | Obligations to repay | Current liabilities, non-current liabilities, total liabilities |
| Equity | Assets − Liabilities | Share capital, retained earnings, total equity |

Core identity: **Assets = Liabilities + Equity**. If this doesn't hold, there's a data issue.

```python
import polars as pl

bs = c.BS
if bs is not None:
    # rows are accounts, columns are years
    print(bs.columns)
    # ['account', '2015', '2016', '2017', ..., '2024']

    # filter for total assets only
    total_assets = bs.filter(pl.col("account") == "자산총계")
    print(total_assets)
```

### Income Statement (IS)

```python
c.IS
```

The income statement shows revenue and expenses over a **period of time**. It answers: "How much did the company earn and spend this year?"

| Category | Meaning | Key Items |
|----------|---------|-----------|
| Revenue | Money earned from operations | Sales/Revenue |
| Expenses | Money spent to generate revenue | Cost of sales, SG&A |
| Profit | Revenue − Expenses | Operating income, net income |

```python
is_df = c.IS
if is_df is not None:
    # filter for revenue and operating income
    key_items = is_df.filter(
        pl.col("account").is_in(["매출액", "수익(매출액)", "영업이익"])
    )
    print(key_items)
```

> The same "revenue" may have different account names across companies. Samsung uses "수익(매출액)", SK Hynix uses "영업수익". This problem is solved in [3. Time Series](./timeseries).

### Cash Flow Statement (CF)

```python
c.CF
```

The cash flow statement shows how much cash actually came in and went out over a **period of time**. Even profitable companies can go bankrupt if they lack cash, so this should be read alongside the income statement.

| Category | Meaning | Examples |
|----------|---------|---------|
| Operating | Cash from core business | Sales collection, salary payments |
| Investing | Cash for assets/equipment | Factory construction, equipment purchases |
| Financing | Cash from funding/repayment | Borrowing, dividend payments |

```python
cf = c.CF
if cf is not None:
    cash_items = cf.filter(
        pl.col("account").is_in([
            "영업활동으로인한현금흐름",
            "투자활동으로인한현금흐름",
            "재무활동으로인한현금흐름"
        ])
    )
    print(cash_items)
```

---

## Consolidated vs. Separate

DART has two types of financial statements:

| Type | Scope | Why View It |
|------|-------|-------------|
| **Consolidated** (CFS) | Parent + all subsidiaries | Actual scale and performance of the entire group |
| **Separate** (OFS) | Parent company only | Financial status of the parent alone |

Samsung Electronics' consolidated revenue includes subsidiaries like Samsung Display and Samsung SDI. Separate revenue is Samsung Electronics standalone only.

DartLab **prioritizes consolidated statements**. Only companies without subsidiaries (standalone entities) use separate statements.

```python
# BS, IS, CF automatically prioritize consolidated
c.BS   # consolidated BS (if available) or separate BS

# to check directly in raw data
result = c.fsSummary()
print(f"Consolidated data exists: {result.hasConsolidated}")
```

---

## Understanding Column Structure

The returned DataFrame columns are `account` + year columns.

```python
bs = c.BS
print(bs.columns)
# ['account', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']
```

- `account`: Account name (Korean)
- Year columns: Amount as of that fiscal year-end (in KRW)

### Getting Data for a Specific Year

```python
# 2024 total assets
bs = c.BS
row = bs.filter(pl.col("account") == "자산총계")
if row.height > 0:
    value = row["2024"][0]
    print(f"2024 Total Assets: {value:,.0f} KRW")
    print(f"                 = {value/1e12:,.1f} trillion KRW")
```

### Extracting Multiple Items at Once

```python
# extract key BS items
key_accounts = ["자산총계", "유동자산", "비유동자산", "부채총계", "자본총계"]
summary = bs.filter(pl.col("account").is_in(key_accounts))
print(summary)
```

---

## Quarterly Financial Statements

The default BS/IS/CF are annual data. For quarterly data, use `fsSummary()`.

```python
quarterly = c.fsSummary(period="q")

quarterly.BS   # quarterly balance sheet
quarterly.IS   # quarterly income statement
quarterly.CF   # quarterly cash flow statement
```

Quarterly column names use the format `2020Q1`, `2020Q2`, `2020Q3`, `2020Q4`.

```python
qbs = quarterly.BS
print(qbs.columns)
# ['account', '2020Q1', '2020Q2', '2020Q3', '2020Q4', '2021Q1', ...]
```

| period value | Reports included | Column format |
|-------------|-----------------|---------------|
| `"y"` (default) | Annual reports only | `2020`, `2021`, ... |
| `"q"` | Q1 + semi-annual + Q3 + annual | `2020Q1`, `2020Q2`, ... |
| `"h"` | Semi-annual + annual | `2020H1`, `2020H2`, ... |

> Quarterly income statement (IS) values are **cumulative**. The Q2 column for revenue is not "Q2 revenue" but "Q1+Q2 cumulative revenue". For standalone quarterly revenue, use the time series engine in [3. Time Series](./timeseries).

---

## Caveats

### Account names differ across companies

The same "revenue" may have different names at different companies. Filtering with `pl.col("account") == "매출액"` may return empty results for some companies.

```python
# this won't work for all companies
bs.filter(pl.col("account") == "매출액")   # may not find in some companies

# use the time series engine to solve this
# → see 3. Time Series
```

### Amount unit

DART raw data amounts are in **KRW (Korean Won)**. Values returned by BS/IS/CF properties are also in KRW.

```python
# Samsung total assets is 400 trillion, not 4 trillion
# → unit is KRW, so 400,000,000,000,000 (400T KRW)
```

### None return

Companies without data return `None`. Always check for `None`.

```python
bs = c.BS
if bs is not None:
    print(bs)
else:
    print("No balance sheet data available")
```

---

## Next Steps

- [3. Time Series](./timeseries) — Account standardization, standalone quarterly time series, TTM
- [4. Ratios](./ratios) — ROE, debt ratio, FCF, and more auto-calculated

