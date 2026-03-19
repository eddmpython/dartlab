<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>One company map from disclosure filings — DART + EDGAR</b></p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-90%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">Docs</a> · <a href="https://eddmpython.github.io/dartlab/blog/">Blog</a> · <a href="startMarimo/">Marimo Notebooks</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb">Open in Colab</a> · <a href="README_KR.md">한국어</a> · <a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

## What DartLab Is

DartLab turns corporate filings into a single company map — for both Korean DART and US EDGAR.

The center of that map is `sections`: a horizontalized matrix built from disclosure sections across periods. Instead of treating a filing as a pile of unrelated parsers, DartLab aligns the document structure first, then lets stronger sources fill in what they own:

- **`docs`** — section structure, narrative text with heading/body separation, tables, and evidence
- **`finance`** — authoritative numeric statements (BS, IS, CF) and financial ratios
- **`report`** — authoritative structured disclosure APIs (DART only)

```python
import dartlab

c = dartlab.Company("005930")   # Samsung Electronics (DART)
c.sections                      # full company map (topic × period)
c.topics                        # topic list with source, blocks, periods
c.show("companyOverview")       # open one topic
c.show("IS", period=["2024Q4", "2023Q4"])  # compare specific periods
c.BS                            # balance sheet
c.ratios                        # ratio time series
c.insights                      # 7-area grades (A~F)

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("10-K::item1Business")
us.BS
us.ratios
```

## Install

```bash
uv add dartlab
```

**No data setup required.** When you create a `Company` for the first time, dartlab automatically downloads the required data from GitHub Releases (DART) or SEC API (EDGAR finance). The second run loads instantly from local cache.

```
[dartlab] 005930 (DART 공시 문서 데이터) → 첫 사용: GitHub에서 자동 다운로드 중...
[dartlab] ✓ DART 공시 문서 데이터 다운로드 완료 (542KB)
[dartlab] 005930 (재무 숫자 데이터) → 첫 사용: GitHub에서 자동 다운로드 중...
[dartlab] ✓ 재무 숫자 데이터 다운로드 완료 (38KB)
```

AI interface:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## Try It Now

Interactive Marimo notebooks let you explore real company data immediately — no code to write:

```bash
uv add dartlab marimo
marimo edit startMarimo/dartCompany.py    # Korean company (DART)
marimo edit startMarimo/edgarCompany.py   # US company (EDGAR)
```

Or open the [Colab quickstart notebook](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb) in your browser.

## Quick Start

### Sections — The Company Map

`sections` is a Polars DataFrame where each row is a disclosure block and each period column holds the raw payload. Periods are sorted newest-first, and annual reports appear as Q4:

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ null         │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
III     │ BS               │ table     │ null         │ —      │ —      │ —      │ (finance)
VII     │ dividend         │ table     │ null         │ —      │ —      │ —      │ (report)
```

Text blocks carry structural metadata — `textNodeType` (heading/body), `textLevel`, and `textPath` — so you can distinguish section headers from narrative content.

### Show, Trace, Diff

```python
c = dartlab.Company("005930")

# show — open any topic with source-aware priority
c.show("BS")                # → finance DataFrame
c.show("companyOverview")   # → sections-based text + tables
c.show("dividend")          # → report DataFrame (all quarters)

# compare specific periods
c.show("IS", period=["2024Q4", "2023Q4"])

# trace — why a topic came from docs, finance, or report
c.trace("BS")               # → {"primarySource": "finance", ...}

# diff — text change detection (3 modes)
c.diff()                                    # full summary
c.diff("businessOverview")                  # topic history
c.diff("businessOverview", "2024", "2025")  # line-by-line diff
```

### Finance

```python
c.BS                    # balance sheet (account × period, newest first)
c.IS                    # income statement
c.CF                    # cash flow
c.ratios                # ratio time series DataFrame (6 categories × period)
c.finance.ratios        # latest single-point RatioResult
c.finance.ratioSeries   # ratio time series across years
c.finance.timeseries    # raw account time series
```

Financial ratios cover 6 categories: profitability, stability, growth, efficiency, cashflow, and valuation.

### Insights

```python
c.insights                      # 7-area analysis
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["Revenue growth +8.3%", …]
c.insights.anomalies            # → outliers and red flags
```

7 analysis areas: performance, profitability, health, cashflow, governance, risk, opportunity.

### EDGAR (US)

Same `Company` interface, different data source:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections with heading/body
us.show("10-K::item1Business")      # business description
us.show("10-K::item1ARiskFactors")  # risk factors
us.BS                               # SEC XBRL balance sheet
us.ratios                           # same 47 ratios
us.diff("10-K::item7Mdna")          # MD&A text changes
```

EDGAR sections include the same text structure metadata (heading/body separation, textLevel, textPath) as DART.

## OpenAPI — Raw Public APIs

Use source-native wrappers when you want raw disclosure APIs directly.

### OpenDart (Korea)

```python
from dartlab import OpenDart

d = OpenDart()                                  # auto-detect API key
d = OpenDart(["key1", "key2"])                  # multi-key rotation

d.search("카카오", listed=True)                  # company search
d.filings("삼성전자", "2024")                    # filing list
d.company("삼성전자")                            # corporate profile
d.finstate("삼성전자", 2024)                     # financial statements
d.report("삼성전자", "배당", 2024)                # 56 report categories

# convenience proxy
s = d("삼성전자")
s.finance(2024)
s.report("배당", 2024)
s.filings("2024")
```

### OpenEdgar (US)

```python
from dartlab import OpenEdgar

e = OpenEdgar()

e.search("Apple")                               # ticker search
e.company("AAPL")                               # company info
e.filings("AAPL", forms=["10-K", "10-Q"])       # filing list
e.companyFactsJson("AAPL")                      # XBRL facts
e.companyConceptJson("AAPL", "us-gaap", "Revenue")  # single tag series
```

These wrappers keep the original source surface intact, while saved parquet stays compatible with DartLab's `Company` engine.

## Core Ideas

### 1. Sections First

`sections` is the backbone. A company is described as one horizontalized map of disclosure units across periods — not a loose set of parser outputs.

### 2. Source-Aware Company

`Company` is a merged company object. When `finance` or `report` is more authoritative than docs for a given topic, it overrides automatically. `trace()` tells you which source was chosen and why.

### 3. Text Structure

Narrative text is not a flat string. DartLab splits it into heading/body rows with level and path metadata, enabling structural comparison across periods. This works for both Korean DART and English EDGAR filings.

### 4. Raw Access

You can always go deeper:

```python
c.docs.sections          # pure docs horizontalization
c.finance.BS             # finance engine directly
c.report.extract("배당")  # report engine directly
```

## Stability

| Tier | Scope |
|------|-------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, ratios, insights) |
| **Beta** | EDGAR Company, OpenDart, OpenEdgar, Server API |
| **Experimental** | AI tools, export |

See [docs/stability.md](docs/stability.md).

## Data

DartLab ships with pre-built datasets via GitHub Releases. Data is continuously updated as new filings are collected.

| Dataset | Coverage | Source |
|---------|----------|--------|
| DART docs | 260+ companies | Korean disclosure text + tables |
| DART finance | 2,700+ companies | XBRL financial statements |
| DART report | 2,700+ companies | Structured disclosure APIs |
| EDGAR docs | 970+ companies | 10-K/10-Q sections |
| EDGAR finance | On-demand | SEC XBRL facts (auto-fetched from SEC API) |

```python
# Bulk download (optional — downloads all companies at once)
from dartlab.core.dataLoader import downloadAll
downloadAll("docs")       # DART disclosure documents
downloadAll("finance")    # DART financial statements
downloadAll("report")     # DART structured reports
```

## Documentation

Docs are continuously updated with new content.

- Docs: https://eddmpython.github.io/dartlab/
- Sections guide: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- Quick start: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API overview: https://eddmpython.github.io/dartlab/docs/api/overview

### Blog

The [DartLab Blog](https://eddmpython.github.io/dartlab/blog/) covers practical disclosure analysis topics — how to read financial reports, interpret disclosure patterns, and spot risk signals. 90+ articles across three categories:

- **Disclosure Systems** — structure and mechanics of DART/EDGAR filings
- **Report Reading** — practical guide to reading audit reports, preliminary earnings, restatements
- **Financial Interpretation** — interpreting financial statements, ratios, and disclosure signals

## Contributing

The project prefers experiments before engine changes. If you want to propose a parser or mapping change, validate it first and then bring the result back into the engine.

## License

MIT
