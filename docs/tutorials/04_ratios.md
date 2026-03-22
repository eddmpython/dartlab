---
title: "4. Financial Ratios"
---

# 4. Financial Ratios — From Numbers to Meaning

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb)

With time series data, financial ratios can be calculated. DartLab automatically computes 30+ ratios across 6 categories.

**Two modes:**
1. `Company.ratios` — Financial ratios time-series DataFrame (metric × period, newest first)
2. `Company.finance.ratios` — Latest single-period RatioResult (TTM + latest balances)

**7 categories:**
- Profitability (8): ROE, ROA, operating margin, net margin, gross margin, EBITDA margin, COGS ratio, SG&A ratio
- Stability (7): Debt ratio, current ratio, quick ratio, equity ratio, interest coverage, net debt ratio, non-current ratio
- Growth (6): Revenue growth, operating income growth, net income growth, asset growth, equity growth, 3-year CAGR
- Efficiency (4): Total asset turnover, inventory turnover, receivables turnover, payables turnover
- Cash Flow (5): FCF, operating CF margin, operating CF/net income, CAPEX ratio, dividend payout ratio
- Valuation (5): PER, PBR, PSR, EV/EBITDA, market cap (requires market cap input)
- Composite (8): O-Score, Z''-Score, Springate, Zmijewski, Beneish M-Score, Sloan Accrual, Piotroski F-Score, Income Quality

---

## Setup

```python
import dartlab

c = dartlab.Company("005930")
```

---

## Ratios Time Series

`Company.ratios` returns a financial ratios time-series DataFrame. Rows are metrics, columns are periods, newest first.

```python
r = c.ratios  # DataFrame (ratio × period, newest first)
```

For the latest single-period `RatioResult`, use `c.finance.ratios`:

```python
rr = c.finance.ratios  # RatioResult (TTM + latest balances)
```

If `ratios` is `None`, the company lacks sufficient financial data.

```python
r = c.ratios
if r is None:
    print("Cannot calculate financial ratios")
```

---

## Profitability Metrics (8)

Measures how much the company keeps from what it earns.

### ROE (Return on Equity)

**Net Income ÷ Equity × 100**

Shows how much was earned relative to shareholder-invested capital. One of the most important profitability metrics for investors.

```python
print(f"ROE: {r.roe:.1f}%")
```

| ROE Range | General Interpretation |
|-----------|----------------------|
| 15%+ | Excellent |
| 10–15% | Good |
| 5–10% | Average |
| Below 5% | Underperforming |

> A high ROE isn't always good. If a company uses heavy debt to keep equity small, ROE can be artificially inflated. Always check alongside the debt ratio.

### ROA (Return on Assets)

**Net Income ÷ Total Assets × 100**

Shows how efficiently total assets are being utilized.

```python
print(f"ROA: {r.roa:.1f}%")
```

### Operating Margin

**Operating Income ÷ Revenue × 100**

Core business profitability. Shows pure operating performance excluding interest, taxes, and one-time items.

```python
print(f"Operating Margin: {r.operatingMargin:.1f}%")
```

| Industry | Reference Operating Margin |
|----------|---------------------------|
| Semiconductors | 20–40% (high cyclical variation) |
| Consumer goods | 5–15% |
| Construction | 3–8% |
| Retail | 1–5% |

### Net Margin

**Net Income ÷ Revenue × 100**

```python
print(f"Net Margin: {r.netMargin:.1f}%")
```

A large gap between operating and net margin suggests significant interest costs, FX losses, or one-time expenses.

### Gross Margin

**Gross Profit ÷ Revenue × 100**

Pure margin after deducting cost of goods. Higher means stronger pricing power.

```python
if r.grossMargin:
    print(f"Gross Margin: {r.grossMargin:.1f}%")
```

### EBITDA Margin

**(Operating Income + Estimated Depreciation) ÷ Revenue × 100**

Useful for comparing profitability of capital-intensive companies. Depreciation is estimated as tangible assets × 5% + intangible assets × 10%.

```python
if r.ebitdaMargin:
    print(f"EBITDA Margin: {r.ebitdaMargin:.1f}%")
```

### COGS Ratio

**Cost of Sales ÷ Revenue × 100**

```python
if r.costOfSalesRatio:
    print(f"COGS Ratio: {r.costOfSalesRatio:.1f}%")
```

COGS ratio + gross margin = 100%. A high COGS ratio indicates intense price competition or high raw material dependency.

### SG&A Ratio

**Selling, General & Administrative Expenses ÷ Revenue × 100**

```python
if r.sgaRatio:
    print(f"SG&A Ratio: {r.sgaRatio:.1f}%")
```

SG&A includes labor, marketing, R&D, and depreciation costs.

---

## Stability Metrics (7)

Measures a company's financial soundness — "how safe is it?"

### Debt Ratio

**Total Liabilities ÷ Equity × 100**

The ratio of borrowed money to own money.

```python
print(f"Debt Ratio: {r.debtRatio:.1f}%")
```

| Debt Ratio | General Interpretation |
|------------|----------------------|
| Below 100% | Stable |
| 100–200% | Moderate |
| Over 200% | Caution needed |

> Appropriate levels vary by industry. 200% is normal for construction; 100% is high for IT.

### Current Ratio

**Current Assets ÷ Current Liabilities × 100**

Shows whether debts due within 1 year can be covered by assets convertible to cash within 1 year.

```python
print(f"Current Ratio: {r.currentRatio:.1f}%")
```

| Current Ratio | Meaning |
|---------------|---------|
| 200%+ | Comfortable |
| 100–200% | Adequate |
| Below 100% | Short-term liquidity risk |

### Quick Ratio

**(Current Assets − Inventory) ÷ Current Liabilities × 100**

A more conservative liquidity measure that excludes inventory. Useful for industries where inventory is hard to liquidate quickly.

```python
if r.quickRatio:
    print(f"Quick Ratio: {r.quickRatio:.1f}%")
```

### Equity Ratio

**Equity ÷ Total Assets × 100**

The proportion of total assets funded by own capital. Inverse concept of debt ratio.

```python
if r.equityRatio:
    print(f"Equity Ratio: {r.equityRatio:.1f}%")
```

### Interest Coverage Ratio

**Operating Income ÷ Interest Expense**

Shows how many times operating income can cover interest payments. Below 1x means the company can't even pay interest.

```python
if r.interestCoverage:
    print(f"Interest Coverage: {r.interestCoverage:.1f}x")
```

| Interest Coverage | Interpretation |
|-------------------|---------------|
| 3x+ | Stable |
| 1–3x | Caution |
| Below 1x | Danger |

### Net Debt Ratio

**Net Debt ÷ Equity × 100**

Net debt = short-term borrowings + long-term borrowings + bonds − cash equivalents. Negative means cash exceeds borrowings (debt-free management).

```python
if r.netDebtRatio is not None:
    print(f"Net Debt Ratio: {r.netDebtRatio:.1f}%")
```

### Non-Current Ratio

**Non-Current Assets ÷ Equity × 100**

Shows how much of long-term assets are funded by own capital. Over 100% means external capital is used for long-term asset acquisition.

```python
if r.noncurrentRatio:
    print(f"Non-Current Ratio: {r.noncurrentRatio:.1f}%")
```

---

## Efficiency Metrics (4)

Measures how efficiently assets are utilized.

### Total Asset Turnover

**Revenue ÷ Total Assets**

How much revenue is generated per unit of assets. Higher = more efficient asset utilization.

```python
if r.totalAssetTurnover:
    print(f"Total Asset Turnover: {r.totalAssetTurnover:.2f}x")
```

### Inventory Turnover

**Revenue ÷ Inventory**

How many times inventory turns over in a year. Higher = more efficient inventory management.

```python
if r.inventoryTurnover:
    print(f"Inventory Turnover: {r.inventoryTurnover:.1f}x")
```

### Receivables Turnover

**Revenue ÷ Trade Receivables**

How quickly credit sales are collected.

```python
if r.receivablesTurnover:
    print(f"Receivables Turnover: {r.receivablesTurnover:.1f}x")
```

### Payables Turnover

**Cost of Sales ÷ Trade Payables**

How quickly trade payables are settled.

```python
if r.payablesTurnover:
    print(f"Payables Turnover: {r.payablesTurnover:.1f}x")
```

---

## Cash Flow Metrics (5)

Profit is an accounting number; cash flow is real money in and out. Profitable companies can still go bankrupt without cash.

### FCF (Free Cash Flow)

**Operating Cash Flow − CAPEX**

Cash remaining after subtracting capital expenditure from operating cash.

```python
if r.fcf:
    print(f"FCF: {r.fcf/1e12:,.1f}T KRW")
```

Persistently negative FCF means the company spends more on investment than it earns from operations.

### Operating CF Margin

**Operating Cash Flow ÷ Revenue × 100**

Comparing this with operating margin reveals the cash conversion quality of earnings.

```python
if r.operatingCfMargin:
    print(f"Operating CF Margin: {r.operatingCfMargin:.1f}%")
```

### Operating CF / Net Income

**Operating Cash Flow ÷ Net Income × 100**

Above 100% means more cash is coming in than reported profit. Capital-intensive companies normally show 200%+ (due to depreciation).

```python
if r.operatingCfToNetIncome:
    print(f"Operating CF / Net Income: {r.operatingCfToNetIncome:.1f}%")
```

### CAPEX Ratio

**|CAPEX| ÷ Revenue × 100**

Capital expenditure as a proportion of revenue. Equipment-heavy industries like semiconductors typically show 20%+.

```python
if r.capexRatio:
    print(f"CAPEX Ratio: {r.capexRatio:.1f}%")
```

### Dividend Payout Ratio

**|Dividends Paid| ÷ Net Income × 100**

What percentage of net income is distributed as dividends.

```python
if r.dividendPayoutRatio:
    print(f"Dividend Payout Ratio: {r.dividendPayoutRatio:.1f}%")
```

---

## Growth Metrics (6)

```python
if r.revenueGrowth3Y:
    print(f"Revenue 3Y CAGR: {r.revenueGrowth3Y:.1f}%")
```

In time-series mode (`calcRatioSeries`), YoY growth rates are also available:
- `revenueGrowth`: Revenue YoY growth
- `operatingProfitGrowth`: Operating income YoY growth
- `netProfitGrowth`: Net income YoY growth
- `assetGrowth`: Total assets YoY growth
- `equityGrowthRate`: Equity YoY growth

---

## Raw Data

Raw values used in ratio calculations are also provided:

```python
if r.revenueTTM:
    print(f"TTM Revenue:          {r.revenueTTM/1e12:,.1f}T KRW")
if r.operatingIncomeTTM:
    print(f"TTM Operating Income: {r.operatingIncomeTTM/1e12:,.1f}T KRW")
if r.netIncomeTTM:
    print(f"TTM Net Income:       {r.netIncomeTTM/1e12:,.1f}T KRW")
if r.totalAssets:
    print(f"Total Assets:         {r.totalAssets/1e12:,.1f}T KRW")
if r.totalEquity:
    print(f"Total Equity:         {r.totalEquity/1e12:,.1f}T KRW")
```

---

## Time-Series Mode — Trend Analysis

Single-period ratios can't reveal direction. Year-over-year trends show "improving or deteriorating."

```python
import dartlab

c = dartlab.Company("005930")
rs = c.finance.ratioSeries  # (series_dict, years) tuple

if rs:
    series, years = rs
    ratio_data = series.get("RATIO", {})
    roe_vals = ratio_data.get("roe", [])
    margin_vals = ratio_data.get("operatingMargin", [])

    print(f"Years: {years}")
    print()
    for year, roe, margin in zip(years, roe_vals, margin_vals):
        roe_str = f"{roe:.1f}" if roe is not None else "-"
        margin_str = f"{margin:.1f}" if margin is not None else "-"
        print(f"  {year}: ROE {roe_str:>6}%  OpMargin {margin_str:>6}%")
```

All 29 ratios available in time-series mode:

| Category | Ratio | Field Name |
|----------|-------|------------|
| Profitability | ROE | `roe` |
| Profitability | ROA | `roa` |
| Profitability | Operating Margin | `operatingMargin` |
| Profitability | Net Margin | `netMargin` |
| Profitability | Gross Margin | `grossMargin` |
| Profitability | EBITDA Margin | `ebitdaMargin` |
| Profitability | COGS Ratio | `costOfSalesRatio` |
| Profitability | SG&A Ratio | `sgaRatio` |
| Stability | Debt Ratio | `debtRatio` |
| Stability | Current Ratio | `currentRatio` |
| Stability | Quick Ratio | `quickRatio` |
| Stability | Equity Ratio | `equityRatio` |
| Stability | Interest Coverage | `interestCoverage` |
| Stability | Net Debt Ratio | `netDebtRatio` |
| Stability | Non-Current Ratio | `noncurrentRatio` |
| Growth | Revenue YoY | `revenueGrowth` |
| Growth | Operating Income YoY | `operatingProfitGrowth` |
| Growth | Net Income YoY | `netProfitGrowth` |
| Growth | Asset YoY | `assetGrowth` |
| Growth | Equity YoY | `equityGrowthRate` |
| Efficiency | Total Asset Turnover | `totalAssetTurnover` |
| Efficiency | Inventory Turnover | `inventoryTurnover` |
| Efficiency | Receivables Turnover | `receivablesTurnover` |
| Efficiency | Payables Turnover | `payablesTurnover` |
| Cash Flow | FCF | `fcf` |
| Cash Flow | Operating CF Margin | `operatingCfMargin` |
| Cash Flow | Operating CF / Net Income | `operatingCfToNetIncome` |
| Cash Flow | CAPEX Ratio | `capexRatio` |
| Cash Flow | Dividend Payout Ratio | `dividendPayoutRatio` |

Time-series results also include raw value lists: `revenue`, `operatingProfit`, `netProfit`, `totalAssets`, `totalEquity`, `operatingCashflow`

---

## At a Glance

Pattern for printing all financial ratios at once:

```python
c = dartlab.Company("005930")
r = c.ratios

if r:
    def p(label, val, unit="%", fmt=".1f"):
        if val is not None:
            print(f"  {label:20s} {val:{fmt}}{unit}")
        else:
            print(f"  {label:20s} -")

    print(f"=== {c.corpName} Financial Ratios ===")
    print()
    print("[ Profitability ]")
    p("ROE", r.roe)
    p("ROA", r.roa)
    p("Operating Margin", r.operatingMargin)
    p("Net Margin", r.netMargin)
    p("Gross Margin", r.grossMargin)
    p("EBITDA Margin", r.ebitdaMargin)
    p("COGS Ratio", r.costOfSalesRatio)
    p("SG&A Ratio", r.sgaRatio)
    print()
    print("[ Stability ]")
    p("Debt Ratio", r.debtRatio)
    p("Current Ratio", r.currentRatio)
    p("Quick Ratio", r.quickRatio)
    p("Equity Ratio", r.equityRatio)
    p("Interest Coverage", r.interestCoverage, "x")
    p("Net Debt Ratio", r.netDebtRatio)
    p("Non-Current Ratio", r.noncurrentRatio)
    print()
    print("[ Efficiency ]")
    p("Asset Turnover", r.totalAssetTurnover, "x", ".2f")
    p("Inventory Turnover", r.inventoryTurnover, "x", ".1f")
    p("Receivables Turnover", r.receivablesTurnover, "x", ".1f")
    p("Payables Turnover", r.payablesTurnover, "x", ".1f")
    print()
    print("[ Cash Flow ]")
    if r.fcf:
        p("FCF", r.fcf / 1e12, "T KRW", ",.1f")
    p("Op CF Margin", r.operatingCfMargin)
    p("Op CF / Net Income", r.operatingCfToNetIncome)
    p("CAPEX Ratio", r.capexRatio)
    p("Dividend Payout", r.dividendPayoutRatio)
    print()
    print("[ Growth ]")
    p("Revenue 3Y CAGR", r.revenueGrowth3Y)
```

---

## Comparing Ratios Across Companies

```python
import polars as pl

codes = ["005930", "000660", "035420", "035720", "051910"]
rows = []

for code in codes:
    c = dartlab.Company(code)
    r = c.ratios
    if r is None:
        continue
    rows.append({
        "Company": c.corpName,
        "ROE(%)": round(r.roe, 1) if r.roe else None,
        "OpMargin(%)": round(r.operatingMargin, 1) if r.operatingMargin else None,
        "DebtRatio(%)": round(r.debtRatio, 1) if r.debtRatio else None,
        "CurrentRatio(%)": round(r.currentRatio, 1) if r.currentRatio else None,
        "FCF(T)": round(r.fcf / 1e12, 1) if r.fcf else None,
        "AssetTurnover": round(r.totalAssetTurnover, 2) if r.totalAssetTurnover else None,
    })

df = pl.DataFrame(rows)
print(df)
```

Same code structure — just change the `codes` list to compare any companies. 5, 50, or 500, same code.

---

## Formula Reference

### Profitability

| Ratio | Formula | Unit |
|-------|---------|------|
| ROE | Net Income (TTM) ÷ Equity × 100 | % |
| ROA | Net Income (TTM) ÷ Total Assets × 100 | % |
| Operating Margin | Operating Income (TTM) ÷ Revenue (TTM) × 100 | % |
| Net Margin | Net Income (TTM) ÷ Revenue (TTM) × 100 | % |
| Gross Margin | Gross Profit (TTM) ÷ Revenue (TTM) × 100 | % |
| EBITDA Margin | (Operating Income + Est. D&A) ÷ Revenue (TTM) × 100 | % |
| COGS Ratio | Cost of Sales (TTM) ÷ Revenue (TTM) × 100 | % |
| SG&A Ratio | SG&A (TTM) ÷ Revenue (TTM) × 100 | % |

> EBITDA D&A estimation: Tangible Assets × 5% + Intangible Assets × 10% (approximation due to difficulty extracting depreciation from cash flow statements)

### Stability

| Ratio | Formula | Unit |
|-------|---------|------|
| Debt Ratio | Total Liabilities ÷ Equity × 100 | % |
| Current Ratio | Current Assets ÷ Current Liabilities × 100 | % |
| Quick Ratio | (Current Assets − Inventory) ÷ Current Liabilities × 100 | % |
| Equity Ratio | Equity ÷ Total Assets × 100 | % |
| Interest Coverage | Operating Income (TTM) ÷ Finance Costs (TTM) | x |
| Net Debt Ratio | (Short Borrowings + Long Borrowings + Bonds − Cash) ÷ Equity × 100 | % |
| Non-Current Ratio | Non-Current Assets ÷ Equity × 100 | % |

### Efficiency

| Ratio | Formula | Unit |
|-------|---------|------|
| Total Asset Turnover | Revenue (TTM) ÷ Total Assets | x |
| Inventory Turnover | Revenue (TTM) ÷ Inventory | x |
| Receivables Turnover | Revenue (TTM) ÷ Trade Receivables | x |
| Payables Turnover | COGS (TTM) ÷ Trade Payables | x |

### Cash Flow

| Ratio | Formula | Unit |
|-------|---------|------|
| FCF | Operating CF (TTM) − \|CAPEX\| | KRW |
| Operating CF Margin | Operating CF (TTM) ÷ Revenue (TTM) × 100 | % |
| Operating CF / Net Income | Operating CF (TTM) ÷ Net Income (TTM) × 100 | % |
| CAPEX Ratio | \|CAPEX\| (TTM) ÷ Revenue (TTM) × 100 | % |
| Dividend Payout | \|Dividends Paid\| (TTM) ÷ Net Income (TTM) × 100 | % |

### Growth

| Ratio | Formula | Unit |
|-------|---------|------|
| Revenue 3Y CAGR | (Latest Revenue ÷ 3Y Ago Revenue)^(1/N) − 1 | % |
| Revenue YoY | (Current − Prior) ÷ \|Prior\| × 100 | % |
| Operating Income YoY | (Current − Prior) ÷ \|Prior\| × 100 | % |
| Net Income YoY | (Current − Prior) ÷ \|Prior\| × 100 | % |
| Asset YoY | (Current − Prior) ÷ \|Prior\| × 100 | % |
| Equity YoY | (Current − Prior) ÷ \|Prior\| × 100 | % |

### Valuation (requires market cap)

| Ratio | Formula | Unit |
|-------|---------|------|
| PER | Market Cap ÷ Net Income (TTM) | x |
| PBR | Market Cap ÷ Equity | x |
| PSR | Market Cap ÷ Revenue (TTM) | x |
| EV/EBITDA | (Market Cap + Net Debt) ÷ EBITDA | x |

> Valuation ratios require passing market cap: `calcRatios(series, marketCap=market_cap)`

---

## Composite Indicators (Distress & Quality)

Beyond traditional ratios, DartLab computes academic-grade composite indicators for distress prediction and earnings quality assessment.

### Distress Prediction Models

| Indicator | Field | Description |
|-----------|-------|-------------|
| Ohlson O-Score | `ohlsonOScore` | 9-variable logistic bankruptcy probability (Ohlson, 1980) |
| Ohlson P(bankruptcy) | `ohlsonProbability` | O-Score converted to probability (%) |
| Altman Z''-Score | `altmanZppScore` | Non-manufacturing/emerging market variant (Altman, 1995) |
| Springate S-Score | `springateSScore` | 4-variable Canadian variant (Springate, 1978). S below 0.862 = distress |
| Zmijewski X-Score | `zmijewskiXScore` | 3-variable probit model (Zmijewski, 1984). X above 0 = distress |

```python
r = c.ratios
if r and r.ohlsonProbability is not None:
    print(f"O-Score P(bankruptcy): {r.ohlsonProbability:.1f}%")
if r and r.altmanZppScore is not None:
    print(f"Z''-Score: {r.altmanZppScore:.2f}")
```

### Earnings Quality Models

| Indicator | Field | Description |
|-----------|-------|-------------|
| Beneish M-Score | `beneishMScore` | 8-variable manipulation detection (Beneish, 1999). M > -2.22 = suspect |
| Sloan Accrual Ratio | `sloanAccrualRatio` | Accrual-based earnings proportion (Sloan, 1996). \|ratio\| > 10% = suspect |
| Piotroski F-Score | `piotroskiFScore` | 9-point fundamental strength (Piotroski, 2000). F >= 7 = strong |

These composite indicators feed into the **distress prediction scorecard** available via `Company.insights.distress`. See [Insight Grades](../api/insight) for details.

---

## Account Mappings (snakeId) Used

| Account | Statement | snakeId |
|---------|-----------|---------|
| Revenue | IS | `sales` |
| Cost of Sales | IS | `cost_of_sales` |
| Gross Profit | IS | `gross_profit` |
| Operating Income | IS | `operating_profit` |
| Net Income | IS | `net_profit` |
| SG&A Expenses | IS | `selling_and_administrative_expenses` |
| Finance Income | IS | `finance_income` |
| Finance Costs | IS | `finance_costs` |
| Total Assets | BS | `total_assets` |
| Equity | BS | `owners_of_parent_equity` |
| Total Liabilities | BS | `total_liabilities` |
| Current Assets | BS | `current_assets` |
| Current Liabilities | BS | `current_liabilities` |
| Cash Equivalents | BS | `cash_and_cash_equivalents` |
| Short-term Borrowings | BS | `shortterm_borrowings` |
| Long-term Borrowings | BS | `longterm_borrowings` |
| Bonds | BS | `debentures` |
| Inventory | BS | `inventories` |
| Trade Receivables | BS | `trade_and_other_receivables` |
| Trade Payables | BS | `trade_and_other_payables` |
| Tangible Assets | BS | `tangible_assets` |
| Intangible Assets | BS | `intangible_assets` |
| Retained Earnings | BS | `retained_earnings` |
| Non-Current Assets | BS | `noncurrent_assets` |
| Non-Current Liabilities | BS | `noncurrent_liabilities` |
| Operating CF | CF | `operating_cashflow` |
| Investing CF | CF | `investing_cashflow` |
| CAPEX | CF | `purchase_of_property_plant_and_equipment` |
| Dividends Paid | CF | `dividends_paid` |

---

## Caveats

### Industry Comparisons

Financial ratios have no absolute benchmarks. Comparing semiconductor and bank debt ratios is meaningless. Compare within the same industry. → Use sector classification in [8. Cross-Company Comparison](./cross-company)

### Financial Companies

Banks, insurance, and securities firms have different financial structures, so debt ratio, current ratio, etc. have different meanings. A bank's 1000% debt ratio is normal (deposits are liabilities). Financial companies may not have revenue, current assets, or inventory accounts at all.

### Temporary Distortions

Quarters with large one-time gains/losses can distort TTM ratios. For example, if a quarter with a factory sale gain is included in TTM, ROE will appear abnormally high.

### Outlier Filtering

Extreme values are automatically filtered:
- ROE: `None` if exceeds ±500%
- ROA: `None` if exceeds ±200%
- Debt Ratio: `None` if exceeds 5000%
- Current Ratio: `None` if exceeds 10000%

### EBITDA Estimation

Since extracting depreciation as a separate account from DART data is difficult, it's estimated as tangible assets × 5% + intangible assets × 10%. EBITDA margin may be inaccurate for companies where actual depreciation significantly differs from this range (e.g., airlines).

---

## Next Steps

- [5. Report Data](./report-data) — Dividends, employees, shareholders, audit, etc.
- [6. Disclosure Text](./disclosure) — Business description, MD&A

