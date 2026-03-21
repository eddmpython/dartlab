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
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-115%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
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

## Install

```bash
uv add dartlab
```

**No data setup required.** When you create a `Company`, dartlab automatically downloads the required data from GitHub Releases (DART) or SEC API (EDGAR). The second run loads instantly from local cache.

## Quick Start

```python
import dartlab

c = dartlab.Company("005930")   # Samsung Electronics (DART)
c.sections                      # full company map (topic × period)
c.show("overview")              # open one topic
c.BS                            # balance sheet
c.ratios                        # financial ratio time series
c.insights                      # 7-area grades (A~F)

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("business")
us.BS
us.ratios
```

## What DartLab Is

DartLab turns corporate filings into a single company map — for both Korean DART and US EDGAR.

The center of that map is `sections`: a horizontalized matrix built from disclosure sections across periods. Instead of treating a filing as a pile of unrelated parsers, DartLab aligns the document structure first, then lets stronger sources fill in what they own:

- **`docs`** — section structure, narrative text with heading/body separation, tables, and evidence
- **`finance`** — authoritative numeric statements (BS, IS, CF) and financial ratios
- **`report`** — authoritative structured disclosure APIs (DART only)

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
III     │ BS               │ table     │ null         │ —      │ —      │ —      │ (finance)
VII     │ dividend         │ table     │ null         │ —      │ —      │ —      │ (report)
```

### Core Principles

1. **Sections First** — A company is one horizontalized map, not a loose set of parser outputs
2. **Source-Aware** — When `finance` or `report` is more authoritative, it overrides automatically. `trace()` tells you which source was chosen
3. **Text Structure** — Narrative text is split into heading/body rows with level and path metadata, for both DART and EDGAR
4. **Raw Access** — Go deeper when needed: `c.docs.sections`, `c.finance.BS`, `c.report.extract("배당")`

## Features

### Show, Trace, Diff

```python
c = dartlab.Company("005930")

# show — open any topic with source-aware priority
c.show("BS")                # → finance DataFrame
c.show("overview")          # → sections-based text + tables
c.show("dividend")          # → report DataFrame (all quarters)
c.show("IS", period=["2024Q4", "2023Q4"])  # compare specific periods

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

### Modules

DartLab exposes 100+ modules across 6 categories:

```bash
dartlab modules                      # list all modules
dartlab modules --category finance   # filter by category
dartlab modules --search dividend    # search by keyword
```

```python
c.topics    # list all available topics for this company
```

Categories: `finance` (statements, ratios), `report` (dividend, governance, audit), `notes` (K-IFRS annotations), `disclosure` (narrative text), `analysis` (insights, rankings), `raw` (original parquets).

### Charts & Visualization

```python
c = dartlab.Company("005930")

# one-liner Plotly charts
dartlab.chart.revenue(c).show()          # revenue + operating margin combo
dartlab.chart.cashflow(c).show()         # operating/investing/financing CF
dartlab.chart.dividend(c).show()         # DPS + yield + payout ratio
dartlab.chart.profitability(c).show()    # ROE, operating margin, net margin

# auto-detect all available charts
specs = dartlab.chart.auto_chart(c)
dartlab.chart.chart_from_spec(specs[0]).show()

# generic charts from any DataFrame
dartlab.chart.line(c.dividend, y=["dps"])
dartlab.chart.bar(df, x="year", y=["revenue", "operating_income"], stacked=True)
```

Data tools:

```python
dartlab.table.yoy_change(c.dividend, value_cols=["dps"])       # add YoY% columns
dartlab.table.format_korean(c.BS, unit="백만원")                # 1.2조원, 350억원
dartlab.table.summary_stats(c.dividend, value_cols=["dps"])     # mean/CAGR/trend
dartlab.text.extract_keywords(narrative)                        # frequency-based keywords
dartlab.text.sentiment_indicators(narrative)                     # positive/negative/risk
```

Install chart dependencies: `uv add "dartlab[charts]"`

### Network — Affiliate Map

```python
c = dartlab.Company("005930")

# interactive vis.js graph in browser
c.network().show()           # ego view (1 hop)
c.network(hops=2).show()     # 2-hop neighborhood

# DataFrame views
c.network("members")     # group affiliates
c.network("edges")       # investment/shareholder connections
c.network("cycles")      # circular ownership paths

# full market network
dartlab.network().show()
```

### Market Scan

```python
c = dartlab.Company("005930")

# one company → market-wide
c.governance()           # single company
c.governance("all")      # full market DataFrame
dartlab.governance()     # module-level scan
dartlab.workforce()
dartlab.capital()
dartlab.debt()
```

## EDGAR (US)

Same `Company` interface, different data source:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections with heading/body
us.show("business")                 # business description
us.show("10-K::item1ARiskFactors")  # risk factors
us.BS                               # SEC XBRL balance sheet
us.ratios                           # same 47 ratios
us.diff("10-K::item7Mdna")          # MD&A text changes
```

## AI Analysis

DartLab includes a built-in AI analysis layer that feeds structured company data to LLMs. The system automatically selects relevant data based on your question.

### Python API

```python
import dartlab

# streams to stdout, returns full text
answer = dartlab.ask("삼성전자 재무건전성 분석해줘")

# provider + model override
answer = dartlab.ask("삼성전자 분석", provider="openai", model="gpt-4o")

# data filtering
answer = dartlab.ask("삼성전자 핵심 포인트", include=["BS", "IS"])

# analysis pattern (framework-guided)
answer = dartlab.ask("삼성전자 분석", pattern="financial")

# agent mode — LLM selects tools for deeper analysis
answer = dartlab.chat("005930", "배당 추세를 분석하고 이상 징후를 찾아줘")
```

### CLI

```bash
# provider setup
dartlab setup              # list all providers
dartlab setup ollama       # local LLM (free)
dartlab setup openai       # OpenAI API

# status
dartlab status             # all providers (table view)
dartlab status --cost      # cumulative token/cost stats

# ask questions (streaming by default)
dartlab ask "삼성전자 재무건전성 분석해줘"
dartlab ask "AAPL risk analysis" -p ollama
dartlab ask --continue "배당 추세는?"

# auto-generate report
dartlab report "삼성전자" -o report.md

# web UI
dartlab                    # open browser UI
```

5 providers: `oauth-codex` (ChatGPT subscription), `codex` (Codex CLI), `ollama` (local, free), `openai` (API key), `custom` (OpenAI-compatible).

Install AI dependencies: `uv add "dartlab[ai]"`

### Project Settings (`.dartlab.yml`)

```yaml
company: 005930         # default company
provider: openai        # default LLM provider
model: gpt-4o           # default model
verbose: false
```

## MCP — AI Assistant Integration

DartLab includes a built-in [MCP](https://modelcontextprotocol.io/) server for Claude Desktop, Cursor, and other MCP-compatible assistants.

```bash
uv add "dartlab[mcp]"
```

Add to Claude Desktop config (`claude_desktop_config.json`):

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

45+ tools are automatically available through the MCP bridge — search, show topics, compare periods, calculate ratios, grade companies, across both DART and EDGAR.

## OpenAPI — Raw Public APIs

Use source-native wrappers when you want raw disclosure APIs directly.

### OpenDart (Korea)

> **Note:** `Company` does **not** require an API key — it uses pre-built datasets.
> `OpenDart` uses the raw DART API and requires a key from [opendart.fss.or.kr](https://opendart.fss.or.kr) (free).

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (US)

```python
from dartlab import OpenEdgar

e = OpenEdgar()
e.search("Apple")
e.filings("AAPL", forms=["10-K", "10-Q"])
e.companyFactsJson("AAPL")
```

## Data

**No manual setup required.** When you create a `Company`, dartlab automatically downloads the required data per company. DART data comes from GitHub Releases, EDGAR data from the SEC API.

| Dataset | Coverage | Source |
|---------|----------|--------|
| DART docs | 320+ companies (growing) | Korean disclosure text + tables |
| DART finance | 2,700+ companies | XBRL financial statements |
| DART report | 2,700+ companies | Structured disclosure APIs |
| EDGAR | On-demand | SEC XBRL + 10-K/10-Q (auto-fetched) |

## Try It Now

### Marimo Notebooks

```bash
uv add dartlab marimo
marimo edit startMarimo/dartCompany.py    # Korean company (DART)
marimo edit startMarimo/edgarCompany.py   # US company (EDGAR)
marimo edit startMarimo/aiAnalysis.py     # AI analysis examples
```

### Colab Tutorials

| Notebook | Topic |
|---|---|
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb) | **Quick Start** — sections, show, trace, diff |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial_statements.ipynb) | **Financial Statements** — BS, IS, CF |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb) | **Ratios** — 47 financial ratios |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb) | **Disclosure** — sections, text parsing |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb) | **EDGAR** — US SEC filings |

## Documentation

- Docs: https://eddmpython.github.io/dartlab/
- Sections guide: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- Quick start: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API overview: https://eddmpython.github.io/dartlab/docs/api/overview

### Blog

The [DartLab Blog](https://eddmpython.github.io/dartlab/blog/) covers practical disclosure analysis — how to read reports, interpret patterns, and spot risk signals. 115+ articles across three categories:

- **Disclosure Systems** — structure and mechanics of DART/EDGAR filings
- **Report Reading** — practical guide to audit reports, preliminary earnings, restatements
- **Financial Interpretation** — financial statements, ratios, and disclosure signals

## Stability

| Tier | Scope |
|------|-------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, ratios, insights) |
| **Beta** | EDGAR Company, OpenDart, OpenEdgar, Server API |
| **Experimental** | AI tools, export |

See [docs/stability.md](docs/stability.md).

## Contributing

The project prefers experiments before engine changes. If you want to propose a parser or mapping change, validate it first and then bring the result back into the engine.

## License

MIT
