---
title: Quick Start
---

# Quick Start

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb)

Everything in DartLab starts with `c.sections`. The rest (`show`, `trace`, `diff`, `BS`, `ratios`) are all views on top of sections.

## Installation

```bash
uv add dartlab
```

For the AI interface:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## Auto Data Download

When you create a `Company` for the first time, required data is downloaded automatically. No setup needed.

```
[dartlab] 005930 (DART docs data) → first use: auto-downloading from GitHub...
[dartlab] ✓ DART docs data download complete (542KB)
[dartlab] 005930 (finance data) → first use: auto-downloading from GitHub...
[dartlab] ✓ finance data download complete (38KB)
```

From the second run onward, local cache is used for instant loading.

## sections = The Entire Company

```python
import dartlab

c = dartlab.Company("005930")  # Samsung Electronics
c.sections
```

`sections` is a Polars DataFrame. Every disclosure section is laid out as a topic × period matrix.

```
chapter │ topic            │ blockType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ "…"    │ "…"    │ "…"    │
```

This alone shows the entire disclosure structure of a company — topic list, period range, text/table breakdown.

```python
c.topics              # topic summary DataFrame (source, blocks, periods)
c.sections.periods()  # list of periods
c.sections.ordered()  # sorted newest first
```

## Views on Top of sections

When you want to drill into a single topic instead of viewing all sections:

```python
c.show("companyOverview")       # block index
c.show("companyOverview", 0)    # actual data for block 0
c.show("BS")                    # balance sheet (finance source)
c.show("dividend")              # dividend (report source)
```

Detect when text changed:

```python
c.diff()                                    # overall change rates
c.diff("businessOverview")                  # topic history
c.diff("businessOverview", "2024", "2025")  # line-by-line comparison
```

Check which source was selected:

```python
c.trace("BS")               # finance source
c.trace("companyOverview")  # docs source
```

## Financial Statements and Ratios

Financial statements are also views on top of sections via the finance engine:

```python
c.BS                    # balance sheet (newest first)
c.IS                    # income statement
c.CF                    # cash flow statement
c.ratios                # financial ratios time-series DataFrame
c.finance.ratios        # latest single-period RatioResult
c.finance.ratioSeries   # ratio time-series (raw)
```

## Insights

Grading across 7 areas (performance, profitability, stability, cash flow, governance, risk, opportunity):

```python
c.insights                      # 7-area analysis
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["Revenue high growth +8.3%", …]
c.insights.anomalies            # → outliers, risk signals
```

## Same Interface for EDGAR

```python
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
us.BS
us.ratios
```

Same `sections`, same `show`, same `diff`. Only the topic names follow SEC form conventions.

## Source Namespaces

When you need to go deeper:

```python
c.docs.sections          # pure docs source
c.finance.BS             # finance engine directly
c.report.extract("배당")  # report engine directly
```

But for most analysis, `c.sections` and `c.show()` are all you need.

## Try It Now

Explore interactively without writing code:

```bash
uv add dartlab marimo
marimo edit startMarimo/dartCompany.py    # Korean companies (DART)
marimo edit startMarimo/edgarCompany.py   # US companies (EDGAR)
```

Or open the [Colab quickstart notebook](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb) directly in your browser.

## Next Steps

- [Sections Guide](./sections) — sections structure, columns, filtering
- [API Overview](../api/overview) — full API reference
- [Disclosure Text Tutorial](../tutorials/06_disclosure) — working with text/table blocks
- [Stability Policy](../stability)
