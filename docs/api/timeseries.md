---
title: Account Standardization & Time Series
---

# Account Standardization & Time Series

An engine that **normalizes** raw OpenDART financial statement data into **standardized accounts**, producing comparable time series across companies.

## Why It's Needed

Over 2,700 Korean listed companies file financial statements in XBRL, but the same concept of "revenue" exists under different IDs and names depending on the company.

```
ifrs-full_Revenue          → 삼성전자
dart_OperatingIncomeLoss   → LG화학
dart_ConstructionRevenue   → 현대건설
수익(매출액)               → 카카오
영업수익                   → KB금융
```

DartLab unifies these into **a single `revenue`** through a 7-step mapping pipeline. Out of 15.85 million rows across 2,564 companies, **98.7%** are mapped to standardized accounts.

## 7-Step Mapping Pipeline

| Step | Processing | Item Count |
|------|-----------|------------|
| 1 | Remove account_id prefix (ifrs-full_, dart_, ifrs_, ifrs-smes_) | - |
| 2 | Apply ID_SYNONYMS (English XBRL ID synonyms) | 70+ |
| 3 | Apply ACCOUNT_NAME_SYNONYMS (Korean account name synonyms) | 150+ |
| 4 | CORE_MAP lookup (core account priority mapping) | ~50 |
| 5 | accountMappings.json lookup (learned mappings) | 34,171 |
| 6 | Retry after removing parentheses (fallback) | - |
| 7 | Unmapped → None (excluded from time series) | - |

## Time Series Generation

### Quarterly Time Series

```python
series, periods = c.timeseries

# periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
# series["IS"]["revenue"]            → Quarterly revenue list
# series["BS"]["total_assets"]       → Quarterly total assets list
# series["CF"]["operating_cashflow"] → Quarterly operating cash flow list
```

Return structure:

```python
series = {
    "BS": {"total_assets": [v1, v2, ...], "current_assets": [...], ...},
    "IS": {"revenue": [...], "operating_income": [...], "net_income": [...], ...},
    "CF": {"operating_cashflow": [...], "investing_cashflow": [...], ...},
}
periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
```

Periods with no data are represented as `None`. `0` and `None` have different meanings.

### Normalization Method

| Statement | Raw Form | Conversion |
|-----------|----------|------------|
| BS (Balance Sheet) | Point-in-time balance | As-is |
| IS (Income Statement) | Cumulative (Q1, Q1+Q2, Q1+Q2+Q3, Q1~Q4) | Reverse-calculated to quarterly standalone |
| CF (Cash Flow Statement) | Cumulative | Reverse-calculated to standalone via prior quarter differencing |

Consolidated financial statements (CFS) are used preferentially; if unavailable, separate financial statements (OFS) are used as automatic fallback.

### Direct Calls

```python
from dartlab.engines.dart.finance import buildTimeseries, buildAnnual, buildCumulative

series, periods = buildTimeseries("005930")              # Quarterly standalone
series, years   = buildAnnual("005930")                  # Annual aggregated
series, periods = buildCumulative("005930")              # Quarterly cumulative
series, periods = buildTimeseries("005930", fsDivPref="OFS")  # Force separate statements
```

| Function | periods Example | IS/CF Handling | BS Handling |
|----------|----------------|---------------|-------------|
| `buildTimeseries` | `["2016_Q1", ...]` | Quarterly standalone | Point-in-time balance |
| `buildAnnual` | `["2016", "2017", ...]` | Sum of quarters for the year | Q4 point-in-time balance |
| `buildCumulative` | `["2016_Q1", ...]` | Year-to-date cumulative | Point-in-time balance |

## Value Extraction Utilities

```python
from dartlab.engines.dart.finance import getTTM, getLatest, getAnnualValues, getRevenueGrowth3Y

series, periods = c.timeseries

# TTM (trailing 4 quarters sum) — IS, CF only
getTTM(series, "IS", "revenue")            # TTM revenue
getTTM(series, "CF", "operating_cashflow") # TTM operating CF

# Latest value — BS, IS, CF
getLatest(series, "BS", "total_assets")    # Latest total assets
getLatest(series, "IS", "net_income")      # Latest quarter net income

# Full time series list
getAnnualValues(series, "IS", "revenue")   # All-year revenue

# Revenue 3-year CAGR
getRevenueGrowth3Y(series)                 # 3-year revenue growth rate (%)
```

## Financial Ratios (RatioResult)

```python
r = c.ratios

# Profitability
r.roe               # ROE (%)
r.roa               # ROA (%)
r.operatingMargin   # Operating margin (%)
r.netMargin         # Net margin (%)

# Stability
r.debtRatio         # Debt ratio (%)
r.currentRatio      # Current ratio (%)
r.netDebt           # Net debt (KRW)
r.netDebtRatio      # Net debt ratio (%)
r.equityRatio       # Equity ratio (%)

# Cash Flow / Growth
r.fcf               # Free cash flow (KRW)
r.revenueGrowth3Y   # Revenue 3-year CAGR (%)

# TTM Values
r.revenueTTM            # Revenue TTM (KRW)
r.operatingIncomeTTM    # Operating income TTM (KRW)
r.netIncomeTTM          # Net income TTM (KRW)
r.operatingCashflowTTM  # Operating CF TTM (KRW)

# Latest BS Values
r.totalAssets       # Total assets (KRW)
r.totalEquity       # Equity attributable to owners of parent (KRW)
r.totalLiabilities  # Total liabilities (KRW)
r.cash              # Cash (KRW)

# Valuation (when market cap is provided)
r.per               # PER
r.pbr               # PBR
r.psr               # PSR
r.evEbitda          # EV/EBITDA
```

Direct call:

```python
from dartlab.engines.dart.finance import calcRatios, buildTimeseries

series, _ = buildTimeseries("005930")
r = calcRatios(series, marketCap=400_000_000_000_000)  # Includes valuation when market cap is provided
```

## Key snakeId Reference

### BS (Balance Sheet)

| snakeId | Korean | English |
|---------|--------|---------|
| `total_assets` | 자산총계 | Total assets |
| `current_assets` | 유동자산 | Current assets |
| `non_current_assets` | 비유동자산 | Non-current assets |
| `cash_and_equivalents` | 현금및현금성자산 | Cash and cash equivalents |
| `inventories` | 재고자산 | Inventories |
| `trade_receivables` | 매출채권 | Trade receivables |
| `ppe` | 유형자산 | Property, plant and equipment |
| `intangible_assets` | 무형자산 | Intangible assets |
| `total_liabilities` | 부채총계 | Total liabilities |
| `current_liabilities` | 유동부채 | Current liabilities |
| `short_term_borrowings` | 단기차입금 | Short-term borrowings |
| `long_term_borrowings` | 장기차입금 | Long-term borrowings |
| `bonds` | 사채 | Bonds |
| `total_equity` | 지배기업 자본 | Equity attributable to owners of parent |

### IS (Income Statement)

| snakeId | Korean | English |
|---------|--------|---------|
| `revenue` | 매출액 | Revenue |
| `cost_of_sales` | 매출원가 | Cost of sales |
| `gross_profit` | 매출총이익 | Gross profit |
| `operating_income` | 영업이익 | Operating income |
| `profit_before_tax` | 법인세비용차감전순이익 | Profit before tax |
| `income_tax_expense` | 법인세비용 | Income tax expense |
| `net_income` | 당기순이익 | Net income |
| `basic_eps` | 기본주당이익 | Basic EPS |
| `diluted_eps` | 희석주당이익 | Diluted EPS |

### CF (Cash Flow Statement)

| snakeId | Korean | English |
|---------|--------|---------|
| `operating_cashflow` | 영업활동현금흐름 | Cash flows from operating activities |
| `investing_cashflow` | 투자활동현금흐름 | Cash flows from investing activities |
| `financing_cashflow` | 재무활동현금흐름 | Cash flows from financing activities |
| `dividend_paid` | 배당금 지급 | Dividends paid |

The actual mapped snakeIds can number in the hundreds or thousands depending on the company. The tables above list only the most commonly used core accounts.

## Cross-Company Comparison

Example comparing the revenue time series of two companies:

```python
import dartlab

samsung = dartlab.Company("005930")
sk = dartlab.Company("000660")

s1, p1 = samsung.timeseries
s2, p2 = sk.timeseries

# Both companies accessed via the same "revenue" key
samsung_rev = s1["IS"]["revenue"]
sk_rev = s2["IS"]["revenue"]
```

Since the same snakeId system is used, any two companies can be compared using the same keys.

## Financial Sector Specifics

Banks, insurance companies, securities firms, and other financial institutions have different financial statement structures from general manufacturers.

- `revenue`, `cost_of_sales`, `current_assets`, etc. may not exist
- A debt ratio exceeding 500% is normal
- Financial sector-specific accounts like `interest_income`, `insurance_revenue` exist

The insight engine automatically detects financial sector companies and applies separate criteria for analysis.
