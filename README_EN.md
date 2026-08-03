<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>One stock code. The full company story.</b></p>
<p>Korean DART + US SEC EDGAR filings, read and compared in one line of Python.</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci-fast.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci-fast.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-Read-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
<a href="https://music.youtube.com/playlist?list=PLVYhaasf1oNs&si=YLzmTO2M9oHHxsJY"><img src="https://img.shields.io/badge/Podcast-YouTube_Music-ff0000?style=for-the-badge&labelColor=050811&logo=youtubemusic&logoColor=white" alt="YouTube Music Podcast"></a>
</p>

<p>
</p>

<p>
<a href="https://huggingface.co/datasets/eddmpython/dartlab-data"><img src="https://img.shields.io/badge/Data-HuggingFace-ffd21e?style=for-the-badge&labelColor=050811&logo=huggingface&logoColor=white" alt="HuggingFace Data"></a>
<a href="https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe"><img src="https://img.shields.io/badge/Desktop-Windows-38bdf8?style=for-the-badge&labelColor=050811&logo=windows&logoColor=white" alt="Desktop Download"></a>
</p>

<a href="https://www.youtube.com/watch?v=-Y3kY1zs62I"><img src="https://img.youtube.com/vi/-Y3kY1zs62I/maxresdefault.jpg" alt="DartLab - turn filings into comparable data" width="900"></a>

<p>
<a href="https://eddmpython.github.io/dartlab/viewer"><img src=".github/assets/btn-viewer-en.svg" alt="Open the Viewer" height="52"></a>
&nbsp;&nbsp;
<a href="https://eddmpython.github.io/dartlab/"><img src=".github/assets/btn-site-en.svg" alt="Official Site" height="52"></a>
</p>

</div>

## Every Company Has a Story

Line up numbers and you get a dashboard. Connect their causes and you get a story. DartLab gives you two ways to read that story.

**Read it yourself** - pull financials, filings, and ratios with a single stock code, then trace "why is this company's margin at this level" through a six-act causal structure. One line of code, and the data tells a story.

**Let AI read it for you** - the same engines, orchestrated by AI to design an analysis flow tailored to your question, showing every line of code and every result. You don't just get an answer - you learn the method.

Both paths run on the same engines.

## Terminal - A Bloomberg-style Challenger

<div align="center">

<a href="https://eddmpython.github.io/dartlab/terminal"><img alt="DartLab Terminal" src=".github/assets/terminal-main.webp" width="900"></a>

</div>

Read financials, prices, filings, credit, industry, and macro for a single company on one screen - **the DartLab Terminal, a challenger to the Bloomberg-style terminal**. The comparable data the library produces is placed directly on the screen.

> This terminal began with inspiration from [@youngchangjo](https://www.threads.com/@youngchangjo)'s [thread](https://www.threads.com/@youngchangjo/post/DZC_jobCfO6).

## The Problem

Have you ever tried to compare Samsung's "Revenue" across five years?

Open a DART annual report and the same number appears as `ifrs-full_Revenue`, `dart_Revenue`, `매출액`, `영업수익` - four different names. Last year's table of contents doesn't match this year's. Comparing with SK Hynix means starting from scratch.

**The real problem isn't missing data. It's the same data existing under too many names.**

DartLab is built on one premise: **every period must be comparable, and every company must be comparable.** It normalizes disclosure sections into a topic-period grid (~95% mapping rate) and standardizes XBRL accounts into canonical names (~97% mapping rate) - so you compare companies, not filing formats.

## Quick Start

```bash
uv add dartlab
```

```python
import dartlab

c = dartlab.Company("005930")       # Samsung Electronics

c.panel()                           # every topic, every period, side by side
# shape: (41, 12) - 41 topics across 12 periods
#                     2025Q4  2024Q4  2024Q3  2023Q4  ...
# companyOverview       v       v       v       v
# businessOverview      v       v       v       v
# riskManagement        v       v       v       v
```

> Text and numbers on a single timeline - the core of cross-period comparability
>
> <img src=".github/assets/panel-grid.webp" alt="c.panel() output - Samsung Electronics, full disclosure grid (topics × periods)" width="720">

```python
c.panel("IS")                       # income statement - finance-normalized (quarterly by default)
c.panel("IS", freq="year")          # freq="year" for annual aggregation
```

> Finance-normalized - XBRL standard accounts (snakeId) + Korean labels, exact KRW figures
>
> <img src=".github/assets/panel-is-finance.webp" alt="c.panel('IS', freq='year') - Samsung Electronics annual income statement (finance-normalized)" width="720">

```python
c.panel("is", freq="year")          # native income statement - report line items as-filed (since 2013)
c.panel("ratios")                   # native financial ratios, computed from the five statements
```

> Lowercase = native - line items exactly as filed, deep history reaching pre-XBRL (since 2013)
>
> <img src=".github/assets/panel-is-native.webp" alt="c.panel('is', freq='year') - Samsung Electronics annual income statement (native, as-filed line items)" width="720">

```python
c.panel("business")                 # business overview etc. - search disclosure body rows
c.panel.search("inventory")         # full-text body search

c.filings()                         # all reports - direct links to DART viewer
```

> From annual reports to quarterly filings, dartUrl links straight to the original
>
> <img src=".github/assets/panel-filings.webp" alt="c.filings() - Samsung Electronics report list with DART viewer links" width="720">

```python
# Same interface, different country
us = dartlab.Company("AAPL")
us.show("business")
us.show("ratios")

# Ask in natural language
dartlab.ask("Analyze Samsung Electronics financial health")
# → your installed agent uses DartLab MCP and returns evidence-backed analysis
```

No data API key is needed. Data auto-downloads from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data) on first use. AI questions use a locally installed Codex CLI, Claude Code, or Cline account; DartLab never asks for the model API key or OAuth token.

## DataHub: One Data Entry Point Across Every Layer

`dartlab.data` is not a scanner-specific or AI-only tool. It is an independent data
platform that discovers L1 sources, L1.5 cross-sectional data, and L2 analytical
assets through one catalog and query contract shared by external Python, HTTP, and
the simulator. A factor store is one use of this workbench: a `factor` projection
combined with immutable materialization.

```python
import dartlab

catalog = dartlab.dataHub(
    "catalog",
    query={"layers": ["L1", "L1.5", "L2"], "search": "financialFeatures"},
)

first = dartlab.dataHub(
    "query",
    query={
        "requests": [
            {
                "assetId": "analysis.dartFinancialFeatures",
                "requestId": "krListed",
                "universe": {"markets": ["KR"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            },
            {
                "assetId": "analysis.edgarFinancialFeatures",
                "requestId": "usListed",
                "universe": {"markets": ["US"], "membership": "listed"},
                "projection": {
                    "kind": "factor",
                    "measures": [
                        "financial.revenue",
                        "financial.operatingMargin",
                    ],
                },
                "time": {"knownAt": "20260723"},
            },
        ],
        "budget": {
            "maxRows": 100000,
            "maxBytes": 64 * 1024 * 1024,
            "timeoutMs": 120000,
            "maxAssets": 4,
            "maxSubjects": 20000,
            "maxConcurrency": 2,
        },
        "materialization": {"mode": "refresh"},
    },
)

for page in first.iterPages():
    consume(page)
```

This single call registers work for the current 2,661 listed Korean companies and
7,669 listed US companies. The caller does not loop over per-company APIs or load
the entire universe into the first response. The workbench follows opaque
continuations within row, byte, and time bounds, while structured gaps and coverage
retain every unsuccessful entity.

A cold `refresh` synchronously completes a terminal generation, so it is not an
instant-return path. Other processes using the same `DARTLAB_HOME` can use warm
`reuse` or receipt-based `offline` mode to read stored Arrow pages without calling
the owners or sources again. Remote multi-node serving and authentication remain
the versioned `/api/dataHub/v1` contract through `DataHubClient` or
`AsyncDataHubClient`, while pull workers consume the same durable job ledger.
See [engines.dataHub](https://eddmpython.github.io/dartlab/skills/engines.dataHub)
and the [data workbench contract](docs/handbook/architecture/dataWorkbench.md) for
the full contract.

## Three Layers of Analysis

Company prepares data with one stock code. Three layers analyze it.

1. **Analysis engines** - produce numbers. Margin trends, cash flow patterns, default probability, peer comparison, macro cycles. No interpretation - numbers and evidence only.
2. **story** - assembles engine data into reports by combining blocks. 11 report types × 7 company templates. No interpretation - systematically arranges evidence from diverse perspectives.
3. **AI** - calls engines directly and makes judgments. Questions results, verifies against raw data, recalculates with adjusted assumptions when something looks wrong. dartlab's active analyst.

## What DartLab Is

One calling convention. Each engine: `dartlab.engine()` for the guide, `dartlab.engine("axis")` to run.

> **New here?** Start with `Company` → `Story` → `Ask`. Load data, generate a report, then ask AI.

| Layer | Engine | What it does | Entry point | Notebook |
|-------|--------|--------------|-------------|:--------:|
| Data | [Data](/skills) | Pre-built HuggingFace datasets, auto-download | `Company("005930")` | - |
| L0/L1 | [Company](/skills) | Filings + financials + structured data unified by ticker | `c.show()`, `c.select()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| L1 | [Gather](/skills) | External market data (price, flow, macro, news) | `dartlab.gather()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_gather.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/02_gather.py) |
| L1 | [Scan](/skills) | Cross-company comparison (governance, ratios, cashflow, ...) | `dartlab.scan()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_scan.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/03_scan.py) |
| L1 | [Quant](/skills) | Technical & quantitative analysis (momentum/factor/pattern) | `c.quant()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_quant.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/04_quant.py) |
| L2 | [Analysis](/skills) | Profitability/stability/cashflow causal analysis + valuation + forecast | `c.analysis("financial", "수익성")` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/05_analysis.py) |
| L2 | [Macro](/skills) | Market-level macro (cycle/rates/liquidity/sentiment/assets) | `dartlab.macro("사이클")` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_macro.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/06_macro.py) |
| L2 | [Credit](/skills) | Independent credit rating (dCR grade, default probability, health) | `c.credit("등급")` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/07_credit.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/07_credit.py) |
| L2 | [Industry](/skills) | Industry mapper - all listed companies × stage/role/stream + supply-chain edges (atlas at `/map`) | `c.industry()`, `dartlab.industry("semiconductor")` | - |
| L2 | [Story](/skills) | Report builder - 6-engine block composition (analysis/quant/credit/macro/scan/**industry**), 11 types × 7 templates (no interpretation) | `c.story("수익성")` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/08_review.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/08_review.py) |
| L3 | [AI/Skills](/skills) | Skill search + DartLab execution + ref verification workbench | `dartlab.ask()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/09_ai.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/09_ai.py) |
| L4 | [Channel](/skills) | External sharing - `dartlab channel` brings PC dartlab to your phone | `dartlab channel` | - |
| core | [Search](/skills) | Semantic filing search *(alpha)* | `dartlab.search()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/10_search.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/10_search.py) |
| facade | [Listing](/skills) | Catalog API (companies, filings, topics) | `dartlab.listing()` | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/11_listing.ipynb) [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/11_listing.py) |
| viz | [Viz](/skills) | Charts and diagrams (`emit_chart`) | `emit_chart({...})` | - |

> All notebooks: [marimo](notebooks/marimo/) · [colab](notebooks/colab/) · [![Open in marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo)

### Company

> Design: [engines.company](/skills)

Three data sources - docs (full-text disclosures), finance (XBRL statements), report (DART API) - merged into one object. Data auto-downloads from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data), no setup needed.

```python
c = dartlab.Company("005930")

c.index                         # what's available -- topic list + periods
c.show("BS")                    # view data -- DataFrame per topic
c.select("IS", ["매출액"])       # extract data -- finance or docs, same pattern
c.trace("BS")                   # where it came from -- source provenance
c.diff()                        # what changed -- text changes across periods
```

**Notes** - line items behind BS/IS totals. Access via `c.show("topic")`, same pattern as finance topics. Works for both DART (K-IFRS HTML parsing) and EDGAR (US-GAAP XBRL tags).

| `c.show(...)` | What it shows | DART | EDGAR |
|---------------|---------------|:----:|:-----:|
| `"inventory"` | Raw materials / work-in-progress / finished goods | ✅ | ✅ |
| `"borrowings"` | Short-term / long-term debt breakdown | ✅ | ✅ |
| `"tangibleAsset"` | PPE gross / net / depreciation | ✅ | ✅ |
| `"intangibleAsset"` | Goodwill / development costs | ✅ | ✅ |
| `"receivables"` | Trade receivables + allowance | ✅ | ✅ |
| `"provisions"` | Warranty / litigation / restructuring | ✅ | ✅ |
| `"eps"` | Basic / diluted EPS | ✅ | ✅ |
| `"segments"` | Revenue / profit by segment | ✅ | ✅ |
| `"costByNature"` | Raw materials / wages / depreciation | ✅ | ✅ |
| `"lease"` | Right-of-use assets / lease liabilities | ✅ | ✅ |
| `"affiliates"` | Equity method investments | ✅ | ✅ |
| `"investmentProperty"` | Fair value / carrying amount | ✅ | ✅ |

> [![marimo](https://marimo.io/shield.svg)](https://marimo.app/github.com/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb)

### Scan - Cross-Company Comparison

> Design: [engines.scan](/skills)

Cross-company analysis across all listed firms. Governance, workforce, capital, debt, cashflow, audit, insider, quality, liquidity, network, account/ratio comparison, and more.

```python
dartlab.scan("governance")            # governance across all firms
dartlab.scan("ratio", "roe")          # ROE across all firms
dartlab.scan("account", "매출액")      # revenue time-series across all firms
```

> All listed companies at a glance - quarterly revenue side by side
>
> <img src=".github/assets/scan-account.webp" alt="dartlab.scan('account', '매출액') - cross-company revenue comparison" width="720">

### Compare - N Companies Side by Side

> Design: [engines.panel](https://eddmpython.github.io/dartlab/skills/engines.panel)

Where `Company.panel` horizontalizes one company into topic × period, `dartlab.compare` aligns **2-6 companies** onto the same topic/period grid. Like `scan`, it is a single-word top-level verb - the canonical surface for cross-company comparison.

```python
import dartlab

# Notes / narrative comparison - aligned by (disclosureKey, scope, leafType)
dartlab.compare(["005930", "000660"], topic="inventory")

# Financial-statement cell comparison - acode-level, values converted to KRW
dartlab.compare(["005930", "000660"], topic="is", freq="year")

# Multi-period - cell columns become {code}␟{period}
dartlab.compare(["005930", "000660"], topic="tangibleAsset", period=["2025Q4", "2024Q4"])
```

- **Label-drift resolved automatically** - the same line item under a different section number per company (Samsung "7. PP&E" ↔ SK "11. PP&E") still aligns to one row.
- **No confident misalignment** - consolidated↔standalone (scope) and table↔narrative (leafType) never share a row.
- **Gaps stay NaN** - no zero-fill or forward-fill, so missing cells stay blank (honest-gap, no trend distortion).
- **Market boundary** - KO↔US mixing is blocked. US (EDGAR) currently supports row comparison only; financial-cell comparison is KR (DART, KRW-converted) only.

### Gather - External Market Data

> Design: [engines.gather](/skills)

Price, flow, macro, news - all as Polars DataFrames.

```python
dartlab.gather("price", "005930")             # KR OHLCV
dartlab.gather("price", "AAPL", market="US")  # US stock
dartlab.gather("macro", "FEDFUNDS")           # auto-detects US
dartlab.gather("news", "삼성전자")             # Google News RSS
```

### Analysis - 14-Axis Financial Analysis

> Design: [engines.analysis](/skills)

Revenue structure → profitability → growth → stability → cash flow → capital allocation → valuation → forecast. Turns raw statements into a causal narrative that feeds Review, AI, and direct human reading.

```python
c.analysis("financial", "수익성")       # profitability analysis
c.analysis("financial", "현금흐름")    # cash flow analysis

print(c.credit())                           # available-axes guide DataFrame (self-discovery)
c.credit("등급")                            # dCR-AA, healthScore 93/100
c.credit("등급", detail=True)               # grade + narrative + metrics
```

### Credit - Independent Credit Rating

> Design: [engines.credit](/skills) | Reports: [dartlab.pages.dev/blog/credit-reports](https://dartlab.pages.dev/blog/credit-reports)

Independent credit analysis with 3-Track model (general/financial/holding), Notch Adjustment, CHS market correction, and separate financial statement blending.

**79-company validation: large-cap 87% (26/30), mid-cap 82% (41/50), full sample 70% (55/79, re-measurement pending after v5.0 overvaluation fix). Samsung AA+ exact match.** See [methodology](https://eddmpython.github.io/dartlab/skills/operation.methodology) for validation details.

```python
print(c.credit())           # self-discovery - available axes + grade

cr = c.credit("등급")        # main grade
print(cr["grade"])          # dCR-AA+
print(cr["healthScore"])    # 96 (0-100, higher is better)
print(cr["pdEstimate"])     # 0.01% default probability

cr = c.credit("등급", detail=True)  # grade + narrative + metrics + divergence explanation
print(cr["divergenceExplanation"])  # why it differs from agencies
```

Publish reports (credit narrative + audit are auto-included in story's 5막):

```python
from dartlab.story.publisher import publishReport
publishReport("005930")               # 6막 report including credit narrative + audit
```

### Macro - Economy Without a Ticker

> Design: [engines.macro](/skills)

Analyze the economic environment without a Company. Just `import dartlab`.

```python
dartlab.macro("사이클")          # business cycle - 4 phases
dartlab.macro("금리")            # rates + Nelson-Siegel yield curve
dartlab.macro("예측")            # LEI + recession prob + Hamilton RS + GDP Nowcast
dartlab.macro("종합")            # macro synthesis + strategy + portfolio mapping
```

Market cycle, rates, liquidity, sentiment, and asset signals with global macro methodologies (Hamilton EM, Kalman DFM, Nelson-Siegel, Cleveland Fed probit, Sahm Rule, BIS Credit-to-GDP) - **pure numpy, zero statsmodels/scipy**.

Backtest (2000-2024, FRED): Cleveland Fed probit **detected all 3/3 US recessions 2-16 months ahead**, recall 90%.

### Story - Analysis to Report

> Design: [engines.story](/skills)

Assembles analysis into a structured report. 4 output formats: rich (terminal), html, markdown, json.

```python
c.story()              # full report
dartlab.ask()            # report + AI interpretation
```

> Samsung report preview: *"Revenue +23.8%, operating margin 8.6%→21.4%. FCF turned positive, ROIC > WACC - reinvestment is creating value."*

### Storyteller - Numbers Tell Stories

> Design: [engines.story](/skills) · Series: [Company Stories](https://eddmpython.github.io/dartlab/blog/series/company-reports)

Financial analysis isn't ratio tables. DartLab combines 5 engines (analysis, credit, scan, quant, macro) into a **6-act storytelling structure** that auto-generates publishable company stories.

```python
from dartlab.story.publisher import publishReport
publishReport("068270")    # Celltrion - auto-publish 6-act company story
```

**Published stories:**

| Company | Story |
|---------|-------|
| [SK Hynix](https://eddmpython.github.io/dartlab/blog/000660-skhynix) | 30-year Korean semiconductor mystery, 58% operating margin |
| [Samyang Foods](https://eddmpython.github.io/dartlab/blog/003230-samyang-foods) | From last place in Korea's ramen Big 3 to a ₩2.3T global food giant |
| [Doosan Enerbility](https://eddmpython.github.io/dartlab/blog/034020-doosan-enerbility) | Debt ratio from 305% to 129% - the real story of a 9-year diet |
| [Alteogen](https://eddmpython.github.io/dartlab/blog/196170-alteogen) | 9 years of losses, then one license deal turned ₩106.9B operating profit |
| [HMM](https://eddmpython.github.io/dartlab/blog/011200-hmm) | The company where cycles, not markets, decide the stock price |
| [Celltrion](https://eddmpython.github.io/dartlab/blog/068270-celltrion) | Laid off at 41 during IMF crisis, started with $50K - 25 years later, ₩13.78T in intangibles |
| [Hanwha Aerospace](https://eddmpython.github.io/dartlab/blog/012450-hanwha-aerospace) | Samsung dumped it for ₩840B - now it has ₩37T in order backlog |
| [HD Hyundai Electric](https://eddmpython.github.io/dartlab/blog/267260-hd-hyundai-electric) | ₩100.6B loss 7 years ago became ₩1T this year - with one product: transformers |
| [Korea Zinc](https://eddmpython.github.io/dartlab/blog/010130-korea-zinc) | First net loss in 50 years at ₩245.7B, yet operating profit hit all-time high |
| [APR](https://eddmpython.github.io/dartlab/blog/278470-apr) | A cosmetics company sold ₩407B in home appliances - that was just the start |

<div align="center">
<a href="https://www.youtube.com/watch?v=d7RUQIlimVM"><img src="https://img.youtube.com/vi/d7RUQIlimVM/maxresdefault.jpg" alt="Celltrion Company Story" width="100%"></a>

[Watch Celltrion Story](https://www.youtube.com/watch?v=d7RUQIlimVM) · [DartLab 30s Demo](https://www.youtube.com/shorts/97lYLWMWzvA) · [YouTube Channel](https://www.youtube.com/@eddmpython) · [Podcast (YouTube Music)](https://music.youtube.com/playlist?list=PLVYhaasf1oNs&si=YLzmTO2M9oHHxsJY)
</div>

### Search - Find Filings by Meaning *(alpha)*

> Design: [engines.search](/skills)

No model, no GPU, no cold start. 95% precision on 4M documents - better than neural embeddings at 1/100th the cost. See [methodology](https://eddmpython.github.io/dartlab/skills/operation.methodology) for benchmark details.

```python
dartlab.search("유상증자 결정")                     # find capital raise filings
dartlab.search("대표이사 변경", corp="005930")       # filter by company
dartlab.search("회사가 돈을 빌렸다")                 # natural language works too
```

### AI - Bring Your Agent Runtime

> Design: [operation.opsAsSkills](/skills)

Your installed agent searches skills and capabilities through DartLab MCP, executes DartLab APIs, and ties answers to result refs. Authentication, model selection, native sessions, and transcripts remain owned by the agent CLI.

```python
dartlab.ask("Analyze Samsung Electronics financial health")
dartlab.ask("Samsung analysis", runtimeId="claude")
```

```powershell
dartlab setup codex --yes
dartlab invest 005930 --runtime codex
```

Supported runtimes are `codex`, `claude`, and `cline`. `dartlab setup` completes installation, official login, DartLab MCP connection, and default runtime selection as one approved flow, skipping steps that are already complete. Use `dartlab agent status --refresh` to inspect them. Only a `groundedReady` runtime with both its CLI and DartLab MCP connection available can run; a disconnected runtime fails closed instead of producing an ungrounded answer. `dartlab invest` produces an evidence-bound decision brief with the core thesis, strongest counterthesis, valuation, scenarios, catalysts, risks, and monitoring tripwires.

### Channel - Use your PC dartlab from anywhere

> Design: [runtime.channel](/skills)

One command on your PC and dartlab UI works on your phone. Microsoft DevTunnels auto-setup.

```bash
dartlab channel
```

Flow:
1. winget auto-installs the devtunnel CLI (one-time)
2. GitHub OAuth (one-time, browser opens automatically)
3. Permanent URL + QR code (`https://<id>-8400.<region>.devtunnels.ms`)
4. Open the URL/QR on your phone Chrome → dartlab UI just works

Zero domains, zero token tricks. Same infrastructure as VS Code Remote Tunnels - verified mobile compatibility. Optional messaging bots: `--telegram/slack/discord`.

### Architecture

```
L0  core/        Protocols, finance utils, docs utils, registry
L1  providers/   Country-specific data (DART, EDGAR, EDINET)
    gather/      External market data (Naver, Yahoo, FRED)
    scan/        Market-wide analysis - scan("group", "axis")
    quant/       Technical analysis - c.quant()
L2  analysis/    Financial + forecast + valuation - analysis("group", "axis")
    credit/      Independent credit rating - c.credit()
    macro/       Market-level macro - dartlab.macro()
    story/       5-engine composition (analysis + credit + scan + quant + macro)
L3  ai/          Active analyst - dartlab.ask()
L4  ui/apps/local/  Web interface (SvelteKit, shared @dartlab/ui-surfaces; ui/web = legacy fallback)
```

Import direction enforced by CI. Adding a new country means one provider package - zero core changes.

#### Layer consumption flow

Who consumes whom across the stack:

```mermaid
flowchart TB
    subgraph L4["L4 · User interface"]
        UI["CLI / web"]
    end
    subgraph L3["L3 · LLM analyst"]
        AI["ai<br/>dartlab.ask()"]
    end
    subgraph L2["L2 · Analysis"]
        ANA["analysis<br/>causal financial + forecast + valuation"]
        CRD["credit<br/>independent rating"]
        MAC["macro<br/>market reading"]
        REV["story<br/>block-composed report"]
    end
    subgraph L1["L1 · Data ingestion"]
        PRV["providers<br/>DART / EDGAR / EDINET"]
        GAT["gather<br/>FRED / ECOS / Naver / Yahoo"]
        SCN["scan<br/>cross-market"]
        QNT["quant<br/>25 technical indicators"]
    end
    subgraph L0["L0 · Infrastructure"]
        CORE["core<br/>protocols + finance + docs + search"]
    end

    UI --> AI
    AI --> REV
    AI --> ANA
    AI --> MAC
    AI --> SCN
    REV --> ANA
    REV --> CRD
    REV --> SCN
    REV --> QNT
    REV --> MAC
    ANA --> PRV
    ANA --> GAT
    CRD --> PRV
    MAC --> GAT
    SCN --> PRV
    QNT --> GAT
    PRV --> CORE
    GAT --> CORE
    SCN --> CORE
    QNT --> CORE

    classDef l0 fill:#f5f5f5,stroke:#999
    classDef l1 fill:#e8f4ff,stroke:#4a90e2
    classDef l2 fill:#fff4e6,stroke:#e67e22
    classDef l3 fill:#f0e6ff,stroke:#8e44ad
    classDef l4 fill:#e6ffe6,stroke:#27ae60
    class CORE l0
    class PRV,GAT,SCN,QNT l1
    class ANA,CRD,MAC,REV l2
    class AI l3
    class UI l4
```

**Core rules**:
- Arrows always flow top → bottom (L4→L3→L2→L1→L0). Reverse imports forbidden (CI-enforced)
- L2 engines never import each other - analysis ↛ credit, macro ↛ analysis. Composition is story's or ai's job
- When adding a feature, pick the right layer first and let data flow in one direction only

## EDGAR (US)

Same interface, different data source. Auto-fetched from SEC API - no pre-download needed.

```python
# Korea (DART)                          # US (EDGAR)
c = dartlab.Company("005930")           c = dartlab.Company("AAPL")
c.panel()                               c.panel()
c.show("businessOverview")              c.show("business")
c.show("BS")                            c.show("BS")
c.show("ratios")                        c.show("ratios")
c.diff("businessOverview")              c.diff("10-K::item7Mdna")
```

## MCP - AI Assistant Integration

Built-in [MCP](https://modelcontextprotocol.io/) server with 25 tools covering all dartlab engines.

### No Install Required (Remote MCP)

No need to install dartlab. Add to Claude Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dartlab": {
      "url": "https://eddmpython-dartlab.hf.space/mcp/sse"
    }
  }
}
```

Hosted on HuggingFace Spaces. No DART API key needed. → [Details](/skills)

### Local Install (stdio MCP)

```bash
# Claude Code - one line setup
claude mcp add dartlab -- uv run dartlab mcp

# Codex CLI
codex mcp add dartlab -- uv run dartlab mcp
```

<details>
<summary>Claude Desktop / Cursor config</summary>

Add to `claude_desktop_config.json` or `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dartlab": {
      "command": "uv",
      "args": ["run", "dartlab", "mcp"]
    }
  }
}
```

Or auto-generate: `dartlab mcp --config claude-desktop`

</details>

### 25 Tools

| Category | Tools |
|----------|-------|
| Analysis | companyInsights, companyAnalysis, companyStory, companyValuation, companyForecast, companyCredit |
| Data | companyFinancials, companyRatios, companyShow, companyTopics, companyDiff, companyFilings |
| Company | companyGovernance, companyAudit, companyProfile, companySections, companyGather, companyQuant |
| Market | macroAnalysis, marketScan, gatherData, quantAnalysis, topdownScreen |
| Search | searchCompany, dartlabSearch, dartlabListing |

## Skill OS & Skill Market

DartLab has two skill layers.

| Layer | Location | Role |
|---|---|---|
| **builtin Skill OS** | `src/dartlab/skills/specs/**` · `/skills` | Official operating, engine, and analysis procedures. Ships with the package; AI searches it first. |
| **community Skill Market** | GitHub Discussions · `/skills/market` · static `marketIndex.json` | Community skills where DartLab Forge structures the analysis questions users share. Not bundled into the package builtin. |

A skill here is not a card but a contract for a repeatable analysis act. Users post analysis questions in GitHub Discussions; DartLab Forge reads the thread and structures `intent`, `inputs`, `dataSources`, `procedure`, `executionPlan`, `outputs`, `criteria`, and `completionCriteria`. Only when a maintainer confirms the completion criteria (`/market runnable | curated | builtin-candidate`) does a GitHub Action produce an accepted `items/{id}.json` snapshot. The landing [Skill Market](https://eddmpython.github.io/dartlab/skills/market) and the AI tool `ReadSkillMarket` search these static artifacts. A finished shared skill must declare which DartLab engines/recipes it calls, and in what order, in its `executionPlan` - without one, no final snapshot is produced.

## dartlab-lite - Browser & Excel, No Install (Pyodide)

> Deep dive: [Blog - Run dartlab in Excel, browser, and notebooks without install (Pyodide)](https://eddmpython.github.io/dartlab/blog/pyodide-dartlab-lite)

[Pyodide](https://pyodide.org/) ports CPython to WebAssembly, so dartlab runs in environments **without Python installed**. Same API, same data.

**Supported hosts**: [xlwings Lite](https://lite.xlwings.org/) (Excel) · [Anaconda Code](https://www.anaconda.com/products/code-for-excel) (Excel) · [JupyterLite](https://jupyterlite.readthedocs.io/) · Google Colab WASM runtime · marimo (pyodide) · plain HTML embed.

**[👉 Open the demo workbook in Web Excel (OneDrive)](https://1drv.ms/x/c/4e17617bfea66347/IQB9zW91TaD4TJvHM8LRQTh4ARj0gHMapx4LVhCCSbBz92Q?e=HQ4E7d)** - xlwings Lite + dartlab pre-wired. Click the button, or type `=GETFINANCE("005930")` in any cell.

### Two modes - script vs. func

xlwings Lite provides two decorators. **`@script` is imperative (sidebar button writes into sheet)**, **`@func` is declarative (the cell calls it like a formula)**. dartlab supports both; **`@func` is the most Excel-native way** to use dartlab.

**1. `@script` - sidebar button fills the sheet**

```python
import dartlab
import xlwings as xw
from xlwings import arg, func, script

@script(name="isTest")
def finance(book: xw.Book):
    c = dartlab.Company('000020')
    df = c.show('IS')
    data = [list(df.columns)] + [list(r) for r in df.iter_rows()]
    sheet = book.sheets.active
    sheet["A3"].value = data
```

<img src=".github/assets/xlwings-lite-script.webp" alt="xlwings Lite - @script mode, button fills the IS into the sheet" width="720">

**2. `@func` - call it like a formula: `=GETFINANCE("005930")`**

```python
@func
def getFinance(code: str):
    c = dartlab.Company(code)
    df = c.show('IS')
    data = [list(df.columns)] + [list(r) for r in df.iter_rows()]
    return data
```

<img src=".github/assets/xlwings-lite-func.webp" alt="xlwings Lite - @func mode, =GETFINANCE(\"005930\") spills 5 quarterly IS rows automatically" width="720">

`=GETFINANCE` becomes a native Excel UDF, sitting next to VLOOKUP. Change the ticker, Excel recalculates.

### Install (xlwings Lite - one line)

```python
import micropip
# One line. micropip resolves deps (diff-match-patch, openpyxl) and built-in C extensions from the wheel's metadata markers.
await micropip.install("https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/pyodide/dartlab-0.10.7-py3-none-any.whl")

import dartlab
c = dartlab.Company("005930")
c.panel("IS")
```

Or add `dartlab` as a single line to the `requirements.txt` tab in the xlwings Lite sidebar - done. **No local Python, no uv, no venv.**

### Limits (what the browser runtime can't do)

| Feature | Pyodide | Note |
|---|:---:|---|
| `Company()` · `c.show()` · `analysis` · `story` · `credit` | ✅ | HF parquet auto-download |
| `dartlab.ask()` | ❌ | Requires a local agent CLI and process access |
| `dartlab.scan()` | ❌ | Pre-built parquet 271MB (not practical in browser) |
| `dartlab.gather()` | ❌ | Naver·Yahoo·Google News block CORS |

Three fundamentals: no threads, MEMFS is volatile, no access to CORS-blocked APIs. Build pipeline in [pyodide/README.md](pyodide/README.md); step-by-step install screenshots in the [blog post](https://eddmpython.github.io/dartlab/blog/pyodide-dartlab-lite).

## OpenAPI - Raw Public APIs

```python
from dartlab import OpenDart, OpenEdgar

# Korea (requires free API key from opendart.fss.or.kr)
d = OpenDart()
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)

# US (no API key needed)
e = OpenEdgar()
e.filings("AAPL", forms=["10-K", "10-Q"])
```

## Data

All data is pre-built on [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data) - auto-downloads on first use. EDGAR data comes directly from the SEC API.

| Dataset | Size |
|---------|------|
| DART docs | ~8 GB |
| DART finance | ~600 MB |
| DART report | ~320 MB |
| EDGAR | SEC API (on-demand) |

Pipeline: local cache (instant) → HuggingFace (auto-download) → DART API (with your key). Most users never leave the first two.

## Try It Now


**Notebooks:** [Company](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) · [Scan](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) · [Story](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) · [Gather](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) · [Analysis](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) · [Ask (AI)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_ask.ipynb)

## Documentation

[Docs](https://eddmpython.github.io/dartlab/) · [Quick Start](https://eddmpython.github.io/dartlab/skills/start.quickStart) · [Skills](https://eddmpython.github.io/dartlab/skills)

**Blog:** [All](https://eddmpython.github.io/dartlab/blog/) · [Company Stories](https://eddmpython.github.io/dartlab/blog/series/company-reports) · [Credit Reports](https://eddmpython.github.io/dartlab/blog/credit-reports)

## Stability

| Tier | Scope |
|------|-------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR power-user (SCE, notes, freq, coverage), credit, insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text tools, ask/chat, OpenDart, OpenEdgar, Server API, MCP |
| **Experimental** | AI tool calling, export, viz (charts) |

See [operation.stability](https://eddmpython.github.io/dartlab/skills/operation.stability).

## Design Choices

Conscious decisions that differ from other financial libraries - surface them up front so you know what you're installing.

| Decision | What it means | Why |
|---|---|---|
| **Single base install - no `[extras]`** | `pip install dartlab` ships analysis · server · MCP · viz · the Agent Runtime host together | Model execution stays in the user's agent CLI; the DartLab wheel ships only runtime adapters and financial capabilities. |
| **Prebuilt data, zero API keys to start** | `Company("005930")` auto-downloads from HuggingFace into a local cache; DART API keys are only needed for *recollection* | Key provisioning is moved off the first-use path. Keys appear only in `dartlab collect` style raw-recollection flows. |
| **External content is data, not instructions** | Serialized external bodies are wrapped with an `[EXTERNAL CONTENT START - untrusted ...]` marker | "Ignore previous instructions" patterns inside DART/EDGAR/news bodies cannot steer the agent. Numbers, dates, and proper nouns inside the marker must be re-verified against primary sources before citing. |
| **AI engine = Bring Your Agent Runtime** | Codex app-server, Claude stream-json, and ACP are normalized into provider-neutral `AgentEvent` records. No fixed graph is forced. | Authentication, models, and native sessions stay in the CLI while DartLab focuses on financial capabilities, evidence, permissions, and process safety. |
| **L0~L4 one-way imports (no L1.5 cross-import)** | core ← gather/providers ← scan/frame/synth/reference ← 5 analysis engines ← story ← ai/mcp | `import-linter` plus `dartlabGuard.py strict --scope l0-l15` gate every PR. New contributors can decide where to add code from a single picture. |
| **Serialized tests (Polars OOM guard)** | `pytest -v` against the whole suite is forbidden; use `tests/test-lock.sh tests/ -m "<marker>"` | One Company is 200-500 MB of native Polars heap that `gc.collect()` cannot reclaim. Local and CI share the exact same lock wrapper command. |
| **Korean-first messages, English API surface** | Symbols (`Company`, `pastInsight`, `analysis`) are English. CLI errors and progress messages are Korean | `Natural Language :: Korean / English` are both declared. English users get a separate track via this `README_EN.md` and English docstrings. |
| **Single SSOT - Skill OS** | `capabilities()` exposes 304 specs as a queryable catalogue | Code, docs, and contracts live in `src/dartlab/skills/specs/**`. Drift between README, docs, and code is prevented at the source. |
| **Public debt time-series** | `uv run python -X utf8 src/dartlab/skills/measureProgress.py` reports trends across baseline debt, docstring backlog, and pytest marker coverage. Each master push appends a row to [`_progress/measureHistory.jsonl`](src/dartlab/skills/_progress/measureHistory.jsonl) | The "no new violations" guard is complemented by a *repayment* signal. External contributors can verify whether debt is shrinking from a single file. |

### First result in 30 seconds

```bash
pip install dartlab
```

```python
import dartlab
c = dartlab.Company("005930")   # auto-download from HuggingFace (a few tens of MB on first run, cached locally)
c.show("IS")                    # income statement, quarterly by default
```

Three lines - zero API keys, zero environment variables. Korean readers: see [README.md](README.md). Other entry points (CLI · AI · MCP) are documented in the [Quick Start](#quick-start) section above.

## Contributing

**Contributors are very welcome.** Whether it's a bug report, a new analysis axis, a mapping fix, or a documentation improvement - every contribution makes dartlab better for everyone.

- **Data contributions** (e.g. `accountMappings.json`, `sectionMappings.json`): accepted when backed by reproducible evidence in the PR description
- Issues and PRs in Korean or English are both welcome
- Not sure where to start? Open an issue and we'll help you find the right place

## License

Code is [Apache License 2.0](LICENSE); the dataset is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Use it, modify it, fork it, redistribute it, cite it. All fair game.

One ask: keep the credit. If you build on dartlab, carry the [NOTICE](NOTICE) line `Built with dartlab (https://github.com/eddmpython/dartlab)`; if you cite it in writing, use [CITATION.cff](CITATION.cff). That is all we ask.
