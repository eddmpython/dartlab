<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>One stock code. The whole story.</b></p>
<p>DART + EDGAR filings, structured and comparable — in one line of Python.</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
<a href="https://codecov.io/gh/eddmpython/dartlab"><img src="https://img.shields.io/codecov/c/github/eddmpython/dartlab?style=for-the-badge&labelColor=050811&logo=codecov&logoColor=white&label=Coverage" alt="Coverage"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-120%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">Docs</a> · <a href="https://eddmpython.github.io/dartlab/blog/">Blog</a> · <a href="https://huggingface.co/spaces/eddmpython/dartlab">Live Demo</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb">Open in Colab</a> · <a href="https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py">Open in Molab</a> · <a href="README_KR.md">한국어</a> · <a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

<p>
<a href="https://huggingface.co/datasets/eddmpython/dartlab-data"><img src="https://img.shields.io/badge/Data-HuggingFace-ffd21e?style=for-the-badge&labelColor=050811&logo=huggingface&logoColor=white" alt="HuggingFace Data"></a>
</p>

</div>

> **Note:** DartLab is under active development. APIs may change between versions, and documentation may lag behind the latest code.

## Install

Requires **Python 3.12+**.

```bash
# Core — financial statements, sections, Company
uv add dartlab

# or with pip
pip install dartlab
```

### Optional Extras

Core analysis, AI, charts, and LLM are all included in the base install. Optional extras add integrations:

```bash
uv add "dartlab[mcp]"             # MCP server for Claude Desktop / Code / Cursor
```

### From Source

```bash
git clone https://github.com/eddmpython/dartlab.git
cd dartlab && uv pip install -e ".[all]"

# or with pip
pip install -e ".[all]"
```

PyPI releases are published only when the core is stable. If you want the latest features (including experimental ones like audit, forecast, valuation), clone the repo directly — but expect occasional breaking changes.

### Desktop App (Alpha)

Skip all installation steps — download the standalone Windows launcher:

- **[Download DartLab.exe](https://github.com/eddmpython/dartlab-desktop/releases/latest/download/DartLab.exe)** from [dartlab-desktop](https://github.com/eddmpython/dartlab-desktop)
- Also available from the [DartLab landing page](https://eddmpython.github.io/dartlab/)

One-click launch — no Python, no terminal, no package manager required. The desktop app bundles the web UI with a built-in Python runtime.

> **Alpha** — functional but incomplete. The desktop app is a Windows-only `.exe` launcher. macOS/Linux are not yet supported.

---

**No data setup required.** When you create a `Company`, dartlab automatically downloads the required data from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data) (DART) or SEC API (EDGAR). The second run loads instantly from local cache.

## Quick Start

### Terminal — just type `dartlab`

```bash
dartlab                          # start the AI analysis REPL
dartlab chat 005930              # jump straight into Samsung Electronics
```

Inside the REPL, type questions in natural language or use skill commands:

```
삼성전자 > Analyze profitability trends and earnings quality

삼성전자 > /comprehensive        # full investment analysis
삼성전자 > /health               # financial health check
삼성전자 > /company SK하이닉스    # switch company
```

### Python — one stock code, the whole picture

```python
import dartlab

# Samsung Electronics — from raw filings to structured data
c = dartlab.Company("005930")
c.sections                      # every topic, every period, side by side
c.show("businessOverview")      # what this company actually does
c.diff("businessOverview")      # what changed since last year
c.BS                            # standardized balance sheet
c.ratios                        # 47 financial ratios, already calculated

# Apple — same interface, different country
us = dartlab.Company("AAPL")
us.show("business")
us.ratios

# No code needed — ask in natural language
dartlab.ask("Analyze Samsung Electronics financial health", stream=True)
```

## What DartLab Is

A public company files hundreds of pages every quarter. Inside those pages is everything — revenue trends, risk warnings, management strategy, competitive position. The complete truth about a company, written by the company itself.

Nobody reads it.

Not because they don't want to. Because the same information is named differently by every company, structured differently every year, and scattered across formats designed for regulators, not readers. The same "revenue" appears as `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`, or dozens of Korean variations.

DartLab changes who can access this information. Two engines turn raw filings into one comparable map:

### The Two Problems DartLab Solves

**1. The same company says different things differently every year.**

Sections horizontalization normalizes every disclosure section into a **topic × period** grid. Different titles across years and industries all resolve to the same canonical topic:

```
                    2025Q4    2024Q4    2024Q3    2023Q4    …
companyOverview       ✓         ✓         ✓         ✓
businessOverview      ✓         ✓         ✓         ✓
productService        ✓         ✓         ✓         ✓
salesOrder            ✓         ✓         —         ✓
employee              ✓         ✓         ✓         ✓
dividend              ✓         ✓         ✓         ✓
audit                 ✓         ✓         ✓         ✓
…                    (98 canonical topics)
```

```
Before (raw section titles):              After (canonical topic):
Samsung    "II. 사업의 내용"               → businessOverview
Hyundai    "II. 사업의 내용 [자동차부문]"   → businessOverview
Kakao      "2. 사업의 내용"               → businessOverview
```

The mapping pipeline: **text normalization** → **545 hardcoded title mappings** → **73 regex patterns** → canonical topic. ~95%+ mapping rate across all listed companies. Each cell keeps the full text with heading/body separation, tables, and original evidence. Comparing "what did the company say about risk last year vs. this year" becomes a single `diff()` call.

**2. Every company names the same number differently.**

Account standardization normalizes every XBRL account through a 4-step pipeline:

```
Raw XBRL account_id
  → Strip prefixes (ifrs-full_, dart_, ifrs_, ifrs-smes_)
  → English ID synonyms (59 rules)
  → Korean name synonyms (104 rules)
  → Learned mapping table (34,249 entries)
  → Result: revenue, operatingIncome, totalAssets, …
```

```
Before (raw XBRL):                          After (standardized):
Company     account_id          account_nm   →  snakeId    label
Samsung     ifrs-full_Revenue   수익(매출액)  →  revenue    매출액
SK Hynix    dart_Revenue        매출액       →  revenue    매출액
LG Energy   Revenue             매출         →  revenue    매출액
```

~97% mapping rate. Cross-company comparison requires zero manual work. Combined with `scan("account", ...)` / `scan("ratio", ...)`, you can compare a single metric across **2,700+ companies** in one call.

### Principles — Accessibility and Reliability

These two principles govern every public API:

**Accessibility** — One stock code is all you need. `import dartlab` provides access to every feature. No internal DTOs, no extra imports, no data setup. `Company("005930")` auto-downloads from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data).

**Reliability** — Numbers are raw originals from DART/EDGAR. Missing data returns `None`, never a guess. `trace(topic)` shows which source was chosen and why. Errors are never swallowed.

### Data — Everything Is Ready

All data is pre-built on [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data). When you create a `Company`, dartlab auto-downloads what it needs — **no setup, no API key, no manual download.**

| Dataset | Coverage | Size |
|---------|----------|------|
| DART docs | 2,500+ companies | ~8 GB |
| DART finance | 2,700+ companies | ~600 MB |
| DART report | 2,700+ companies | ~320 MB |
| DART scan | Pre-built cross-company | ~271 MB |
| EDGAR | On-demand | SEC API (auto-fetched) |

Want to collect directly from the source? Use the raw public APIs:

```python
from dartlab import OpenDart           # Korea DART (requires free API key)
d = OpenDart()
d.filings("삼성전자", "2024")

from dartlab import OpenEdgar          # US SEC (no key required)
e = OpenEdgar()
e.filings("AAPL", forms=["10-K"])
```

See [Data](#data) for the full pipeline (cache, freshness, batch collection).

### Company — 7 Things to Remember

`Company` merges docs/finance/report into one object. You only need 7 methods:

```python
c = dartlab.Company("005930")

c.index                         # what's available -- topic list + periods
c.show("BS")                    # view data -- DataFrame per topic
c.select("IS", ["매출액"])       # extract data -- for analysis
c.trace("BS")                   # where it came from -- source provenance
c.diff()                        # what changed -- text changes across periods

c.analysis("수익성")             # analyze -- 14-axis financial analysis
c.review()                      # report -- structured full report
```

BS/IS/CF/ratios are convenience shortcuts for `show`. Three namespaces (`c.docs`, `c.finance`, `c.report`) are for direct source access when needed.

### Scan — The Whole Market in One Call

`scan()` is the single entry point for all market-wide cross-sectional analysis. No extra methods to remember — just `scan()`.

```python
dartlab.scan()                        # guide: list all axes + usage
dartlab.scan("governance")            # governance structure across all firms
dartlab.scan("governance", "005930")  # filter to one company
dartlab.scan("ratio")                 # list available ratios
dartlab.scan("ratio", "roe")          # ROE across all firms
dartlab.scan("account", "매출액")     # revenue across all firms
dartlab.scan("cashflow")              # OCF/ICF/FCF + 8-pattern classification
```

13 axes, two patterns:

| Axis | Label | What it does |
|------|-------|--------------|
| governance | Governance | Ownership, outside directors, pay ratio, audit opinion |
| workforce | Workforce | Headcount, avg salary, growth rate, top earners |
| capital | Shareholder Return | Dividends, buybacks, cancellations, equity changes |
| debt | Debt Structure | Bond maturity, CP/short-term bonds, debt ratio, ICR, risk grade |
| cashflow | Cash Flow | OCF/ICF/FCF + 8-type lifecycle pattern |
| audit | Audit Risk | Opinion, auditor change, special matters, independence ratio |
| insider | Insider Holdings | Major holder change, treasury stock, stability |
| quality | Earnings Quality | Accrual ratio + CF/NI — is profit backed by cash? |
| liquidity | Liquidity | Current ratio + quick ratio — can it pay tomorrow? |
| digest | Digest | Market-wide disclosure change digest |
| network | Network | Corporate relationship graph (investment/ownership) |
| account | Account | Single account time-series (target required) |
| ratio | Ratio | Single ratio time-series (target required) |

Each axis is a lazy-loaded module registered in `_AXIS_REGISTRY`. Adding a new axis means one entry in the registry and one module — no other code changes.

### Analysis — Full Financial Statement Analysis

`analysis()` provides access to 14 analytical axes. Same 3-step call pattern as scan.

```python
dartlab.analysis()                    # 14-axis guide
dartlab.analysis("수익구조")           # list calc functions for revenue structure
dartlab.analysis("수익구조", c)        # run revenue structure analysis -> dict

c.analysis()                          # guide
c.analysis("수익성")                   # profitability analysis
```

| Part | Axis | Description | Items |
|------|------|-------------|-------|
| 1-1 | 수익구조 | How does the company make money | 8 |
| 1-2 | 자금조달 | Where does funding come from | 9 |
| 1-3 | 자산구조 | What assets were acquired | 4 |
| 1-4 | 현금흐름 | How did cash actually flow | 3 |
| 2-1 | 수익성 | How well does it earn | 4 |
| 2-2 | 성장성 | How fast is it growing | 3 |
| 2-3 | 안정성 | Can it survive | 4 |
| 2-4 | 효율성 | Does it use assets well | 3 |
| 2-5 | 종합평가 | Financial health in one word | 3 |
| 3-1 | 이익품질 | Are earnings real | 4 |
| 3-2 | 비용구조 | How do costs behave | 4 |
| 3-3 | 자본배분 | Where does earned cash go | 5 |
| 3-4 | 투자효율 | Does investment create value | 4 |
| 3-5 | 재무정합성 | Do statements reconcile | 5 |

Each axis is a set of `calc*(company) -> dict` pure functions. No rendering, no side effects.

### Review — analysis to Report

Review consumes analysis() output and assembles structured reports:

```
calc*(company) -> dict -> block builders -> BlockMap -> templates -> sections -> render
```

```python
c.review()              # all 14 sections, full report
c.review("수익구조")     # single section

b = blocks(c)           # 60+ blocks as a dict (Korean/English keys)
b["growth"]             # English key
b["매출 성장률"]         # Korean label -- same block
```

4 output formats: `rich` (terminal), `html`, `markdown`, `json`. Cross-section narrative threads (e.g., "revenue decline -> margin pressure -> cash deterioration") are auto-detected and injected.

### Reviewer — review + AI Interpretation

Adds AI opinions on top of review:

```python
c.reviewer()                                    # full + AI
c.reviewer(guide="Evaluate from semiconductor cycle perspective")
```

### Gather — External Market Data in One Call

`gather()` collects external market data — price, flow, macro, news — all as **Polars DataFrames**.

```python
dartlab.gather()                              # guide -- 4 axes
dartlab.gather("price", "005930")             # KR OHLCV timeseries (1-year default)
dartlab.gather("price", "AAPL", market="US")  # US stock
dartlab.gather("flow", "005930")              # foreign/institutional flow (KR)
dartlab.gather("macro")                       # KR 12 macro indicators
dartlab.gather("macro", "FEDFUNDS")           # single indicator (auto-detects US)
dartlab.gather("news", "삼성전자")             # Google News RSS
```

Company-bound: `c.gather("price")` — no need to pass the stock code again.

### Five-Layer Relationship

```
gather()     External market data (4 axes)        -- price, flow, macro, news
scan()       Market-wide cross-section (13 axes)  -- screening across firms
analysis()   Single-firm deep analysis (14 axes)  -- full financial analysis
c.review()   analysis -> structured report         -- block-template pipeline
c.reviewer() review + AI interpretation            -- per-section AI opinions
```

### Architecture — Layered by Responsibility

```
L0  core/        Protocols, finance utils, docs utils, registry
L1  providers/   Country-specific data (DART, EDGAR, EDINET)
    gather/      External market data (Naver, Yahoo, FRED)
    scan/        Market-wide cross-sectional analysis (13 axes)
L2  analysis/    8 analytical domains (strategy → macro)
    review/      Block-template report assembly
L3  ai/          LLM-powered analysis (5 providers, 8 super tools)
```

Import direction is enforced by CI — no reverse dependencies allowed. The four axes compose naturally: **Company** (one firm, deep) → **Analysis** (judgment) → **Review** (presentation) → **Scan** (all firms, wide).

### Extensibility — Zero Core Modification

Adding a new country requires zero changes to core code:

1. Create a provider package under `providers/`
2. Implement `canHandle(code) -> bool` and `priority() -> int`
3. Register via `entry_points` in `pyproject.toml`

```python
dartlab.Company("005930")  # → DART provider (priority 10)
dartlab.Company("AAPL")    # → EDGAR provider (priority 20)
```

The facade iterates providers by priority — first match wins.

## Features

### Show, Trace, Diff -- Detailed Examples

```python
c = dartlab.Company("005930")

# show -- open any topic with source-aware priority
c.show("BS")                # finance DataFrame
c.show("overview")          # sections-based text + tables
c.show("dividend")          # report DataFrame (all quarters)
c.show("IS", period=["2024Q4", "2023Q4"])  # compare specific periods

# trace -- why a topic came from docs, finance, or report
c.trace("BS")               # {"primarySource": "finance", ...}

# diff -- text change detection (3 modes)
c.diff()                                    # full summary
c.diff("businessOverview")                  # topic history
c.diff("businessOverview", "2024", "2025")  # line-by-line diff
```

### Finance Shortcuts

Convenience shortcuts for `c.show("BS")` etc.:

```python
c.BS                    # balance sheet (account x period, newest first)
c.IS                    # income statement
c.CF                    # cash flow
c.ratios                # ratio time series (6 categories x period)
c.filings()             # disclosure document list
```

All accounts are normalized through the 4-step standardization pipeline -- Samsung's `revenue` and LG's `revenue` are the same `snakeId`.

### Market-wide Financial Screening

Scan a single account or ratio across **all listed companies** in one call — 2,700+ DART firms or 500+ EDGAR firms. Returns a wide Polars DataFrame (rows = companies, columns = periods, newest first).

```python
import dartlab

# scan a single account across all listed companies
dartlab.scan("account", "매출액")                        # revenue, quarterly standalone
dartlab.scan("account", "operating_profit", annual=True) # annual basis
dartlab.scan("account", "total_assets", market="edgar")  # US EDGAR

# scan a ratio across all listed companies
dartlab.scan("ratio", "roe")                             # quarterly ROE for all firms
dartlab.scan("ratio", "debtRatio", annual=True)          # annual debt-to-equity

# list available ratios
dartlab.scan("ratio")
```

Accepts both Korean names (`매출액`) and English snakeIds (`sales`) — same 4-step normalization as Company finance.

> **Requires pre-downloaded data.** Market-wide functions (`scan("account")`, `scan("digest")`, etc.) operate on local data — individual `Company()` calls only download one firm at a time. See the [Data](#data) section for batch collection.

### Review — Detailed Usage

> **Experimental** — the review system is under active development.

Block assembly and customization details for the review/reviewer pipeline described above.

```python
from dartlab.review import blocks, Review

b = blocks(c)          # dict of 60+ pre-built blocks
list(b.keys())         # -> ["profile", "segmentComposition", "growth", ...]

# pick what you need -- free assembly
Review([
    b["segmentComposition"],
    b["growth"],
    c.select("IS", ["매출액"]),   # mix with raw data
])
```

**Free AI providers** for `c.reviewer()` -- no paid API key required:

| Provider | Setup |
|----------|-------|
| Gemini | `dartlab setup gemini` |
| Groq | `dartlab setup groq` |
| Cerebras | `dartlab setup cerebras` |
| Mistral | `dartlab setup mistral` |

```bash
dartlab setup custom --base-url http://localhost:11434/v1   # Ollama local
```

- **Templates**: Pre-defined block combinations (`수익구조`, `자금조달`)
- **Guide**: Pass `guide="..."` to `c.reviewer()` for domain-specific AI analysis
- **Render formats**: `review.render("rich" | "html" | "markdown" | "json")`

### Insights (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

```python
c.insights                      # 10-area analysis
c.insights.grades()             # → {"performance": "A", "profitability": "B", …}
c.insights.performance.grade    # → "A"
c.insights.performance.details  # → ["Revenue growth +8.3%", …]
c.insights.anomalies            # → outliers and red flags

# distress scorecard — 6-model bankruptcy/fraud prediction
c.insights.distress             # Altman Z-Score, Beneish M-Score, Ohlson O-Score,
                                # Merton Distance-to-Default, Piotroski F-Score, Sloan Ratio
```

### Valuation, Forecast & Simulation

```python
dartlab.valuation("005930")           # DCF + DDM + relative valuation
dartlab.forecast("005930")            # revenue forecast (4-source ensemble)
dartlab.simulation("005930")          # scenario simulation (macro presets)

# also available as Company methods
c.valuation()
c.forecast(horizon=3)
c.simulation(scenarios=["adverse", "rate_hike"])
```

Auto-detects currency — KRW for DART companies, USD for EDGAR. Works with both `dartlab.valuation("AAPL")` and `dartlab.valuation("005930")`.

### Audit (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

```python
dartlab.audit("005930")               # 11 red flag detectors

# Benford's Law (digit distribution), auditor change (PCAOB AS 3101),
# going concern (ISA 570), internal control (SOX 302/404),
# revenue quality (Dechow & Dichev), Merton default probability, ...
```

### Market Intelligence (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

```python
dartlab.digest()                      # market-wide disclosure change digest
dartlab.digest(sector="반도체")        # sector filter
dartlab.groupHealth()                 # group health: network × financial ratios
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

### Charts & Visualization (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

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

### Network — Affiliate Map (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

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

### Market Scan (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

13-axis cross-market analysis. Everything goes through `dartlab.scan()` — one function to remember.

```python
dartlab.scan()                           # guide: all axes + usage
dartlab.scan("governance")               # full market governance
dartlab.scan("governance", "005930")     # single company filter
dartlab.scan("ratio")                    # list available ratios
dartlab.scan("ratio", "roe")             # market-wide ROE
dartlab.scan("account", "매출액")        # market-wide revenue
dartlab.scan("cashflow")                 # OCF/ICF/FCF + 8-pattern classification
dartlab.scan("audit")                    # audit opinion, auditor changes, risk flags
dartlab.scan("insider")                  # largest shareholder changes, treasury stock
```

### Market Data Collection (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

`gather()` collects all external market data as **Polars DataFrames**. Every request goes through automatic fallback chains, circuit breaker isolation, and TTL caching. All methods are synchronous — async parallel execution is handled internally.

```python
import dartlab

dartlab.gather()                                # guide -- 4 axes with descriptions

# OHLCV timeseries — adjusted prices, 6000+ trading days in a single request
dartlab.gather("price", "005930")               # KR: 1-year default
dartlab.gather("price", "005930", start="2015-01-01")  # custom range
dartlab.gather("price", "AAPL", market="US")    # US via Yahoo Finance chart API

# supply/demand flow timeseries (KR only)
dartlab.gather("flow", "005930")                # DataFrame (date, foreignNet, institutionNet, ...)

# macro indicators — full wide DataFrame
dartlab.gather("macro")                         # KR 12 indicators (CPI, rates, FX, production, ...)
dartlab.gather("macro", market="US")            # US 25 indicators (GDP, CPI, Fed Funds, S&P500, ...)
dartlab.gather("macro", "CPI")                  # single indicator (auto-detects KR)
dartlab.gather("macro", "FEDFUNDS")             # single indicator (auto-detects US)

# news
dartlab.gather("news", "삼성전자")               # Google News RSS → DataFrame

# company-bound -- no need to pass stock code
c = dartlab.Company("005930")
c.gather("price")                               # same as gather("price", "005930")
```

**How data is collected — don't worry, it's safe:**

| Source | Data | Method |
|--------|------|--------|
| Naver Chart API | KR OHLCV (adjusted prices) | `fchart.stock.naver.com` — 1 request per stock, max 6000 days |
| Yahoo Finance v8 | US/Global OHLCV | `query2.finance.yahoo.com/v8/finance/chart` — public chart API |
| ECOS (Bank of Korea) | KR macro indicators | Official API with user's own key |
| FRED (St. Louis Fed) | US macro indicators | Official API with user's own key |
| Naver Mobile API | Flow, sector PER | `m.stock.naver.com/api` — JSON endpoints |
| FMP | Fallback for US history | Financial Modeling Prep API (optional) |

**Safety infrastructure:**

- **Rate limiting** — per-domain RPM caps (Naver 30, ECOS 30, FRED 120) with async queue
- **Circuit breaker** — 3 consecutive failures → source disabled for 60s, half-open retry
- **Fallback chains** — KR: naver → yahoo_direct → yahoo / US: yahoo_direct → fmp → yahoo
- **Stale-while-revalidate** — returns cached data on failure, warns via `log.warning`
- **User-Agent rotation** — randomized per request to avoid fingerprinting
- **No silent failures** — all API errors logged at warning level, never swallowed
- **No scraping** — all sources are public APIs or official data endpoints

### Cross-Border Analysis (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

```python
c = dartlab.Company("005930")

# keyword frequency across disclosure periods
c.keywordTrend(keyword="AI")          # topic × period × keyword count
c.keywordTrend()                      # all 54 built-in keywords

# news headlines
c.gather("news")                      # recent 30 days
dartlab.gather("news", "AAPL", market="US")  # US company news

# global peer mapping (WICS → GICS sector)
dartlab.crossBorderPeers("005930")    # → ["AAPL", "MSFT", "NVDA", "TSM", "AVGO"]

# currency is auto-detected per company (KRW for DART, USD for EDGAR)
```

Disclosure gap detection runs automatically inside `c.insights` — flags mismatches between text changes and financial health (e.g. risk text surges while financials are stable).

### Export (experimental)

> **Experimental** — Breaking changes possible. Not for production.

```bash
dartlab excel "005930" -o samsung.xlsx
```

### Plugins

```python
dartlab.plugins()               # list loaded plugins
dartlab.reload_plugins()        # rescan after installing a plugin
```

Plugins can extend DartLab with custom data sources, tools, or analysis engines. See `dartlab plugin create --help` for scaffolding.

## EDGAR (US)

Same `Company` interface, same account standardization pipeline, different data source. EDGAR data is auto-fetched from the SEC API — no pre-download needed:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections with heading/body
us.show("business")                 # business description
us.show("10-K::item1ARiskFactors")  # risk factors
us.BS                               # SEC XBRL balance sheet
us.ratios                           # same 47 ratios
us.diff("10-K::item7Mdna")          # MD&A text changes
us.insights                         # 10-area grades (A~F)

# analyst functions — auto-detect USD
dartlab.valuation("AAPL")           # DCF + DDM + relative (USD)
dartlab.forecast("AAPL")            # revenue forecast (USD)
dartlab.simulation("AAPL")          # scenario simulation (US macro presets)
```

The interface is identical — same methods, same structure:

```python
# Korea (DART)                          # US (EDGAR)
c = dartlab.Company("005930")           c = dartlab.Company("AAPL")
c.sections                              c.sections
c.show("businessOverview")              c.show("business")
c.BS                                    c.BS
c.ratios                                c.ratios
c.diff("businessOverview")              c.diff("10-K::item7Mdna")
c.insights.grades()                     c.insights.grades()
```

### DART vs EDGAR Namespaces

|               | DART           | EDGAR          |
|---------------|:--------------:|:--------------:|
| `docs`        | ✓              | ✓              |
| `finance`     | ✓              | ✓              |
| `report`      | ✓ (28 API types) | ✗ (not applicable) |
| `profile`     | ✓              | ✓              |

DART has a `report` namespace with 28 structured disclosure APIs (dividend, governance, executive compensation, etc.). This does not exist in EDGAR — SEC filings are structured differently.

**EDGAR topic naming**: Topics use `{formType}::{itemId}` format. Short aliases also work:

```python
us.show("10-K::item1Business")     # full form
us.show("business")                # short alias
us.show("risk")                    # → 10-K::item1ARiskFactors
us.show("mdna")                    # → 10-K::item7Mdna
```

## AI Analysis

> **Experimental** — the AI analysis layer and `analysis/` engines are under active development. APIs, output formats, and available tools may change between versions.

> **Tip:** New to financial analysis or prefer natural language? Use `dartlab.ask()` — the AI assistant handles everything from data download to analysis. No coding knowledge required.

DartLab's AI interprets period-comparable, cross-company data that the engine already computed — the LLM explains *why*, not *what*. **No code required** — ask questions in plain language and DartLab handles everything: data selection, context assembly, and streaming the answer.

```bash
# terminal one-liner — no Python needed
dartlab ask "삼성전자 재무건전성 분석해줘"
```

DartLab structures the data, selects relevant context (financials, insights, sector benchmarks), and lets the LLM explain:

```
$ dartlab ask "삼성전자 재무건전성 분석해줘"

삼성전자의 재무건전성은 A등급입니다.

▸ 부채비율 31.8% — 업종 평균(45.2%) 대비 양호
▸ 유동비율 258.6% — 200% 안전 기준 상회
▸ 이자보상배수 22.1배 — 이자 부담 매우 낮음
▸ ROE 회복세: 1.6% → 10.2% (4분기 연속 개선)

[데이터 출처: 2024Q4 사업보고서, dartlab insights 엔진]
```

For real-time market-wide disclosure questions (e.g. "최근 7일 수주공시 알려줘"), the AI uses your `OpenDART API key` to search recent filings directly. Store the key in project `.env` or via UI Settings.

The 2-tier architecture means basic analysis works with any provider, while tool-calling providers (OpenAI, Claude) can go deeper by requesting additional data mid-conversation.

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
# provider setup — free providers first
dartlab setup              # list all providers
dartlab setup gemini       # Google Gemini (free)
dartlab setup groq         # Groq (free)

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
dartlab --help             # show all commands
```

<details>
<summary>All CLI commands (16)</summary>

| Category | Command | Description |
|----------|---------|-------------|
| Data | `show` | Open any topic by name |
| Data | `search` | Find companies by name or code |
| Data | `statement` | BS / IS / CF / SCE output |
| Data | `sections` | Raw docs sections |
| Data | `profile` | Company index and facts |
| Data | `modules` | List all available modules |
| AI | `ask` | Natural language question |
| AI | `report` | Auto-generate analysis report |
| Export | `excel` | Export to Excel (experimental) |
| Collect | `collect` | Download / refresh / batch collect |
| Collect | `collect --check` | Check freshness (new filings) |
| Collect | `collect --incremental` | Incremental collect (missing only) |
| Server | `ai` | Launch web UI (localhost:8400) |
| Server | `share` | Tunnel sharing (ngrok / cloudflared) |
| Server | `status` | Provider connection status |
| Server | `setup` | Provider setup wizard |
| MCP | `mcp` | Start MCP stdio server |
| Plugin | `plugin` | Create / list plugins |

</details>

### Providers

**Free API key providers** — sign up, paste the key, start analyzing:

| Provider | Free Tier | Model | Setup |
|----------|-----------|-------|-------|
| `gemini` | Gemini 2.5 Pro/Flash free | Gemini 2.5 | `dartlab setup gemini` |
| `groq` | 6K–30K TPM free | LLaMA 3.3 70B | `dartlab setup groq` |
| `cerebras` | 1M tokens/day permanent | LLaMA 3.3 70B | `dartlab setup cerebras` |
| `mistral` | 1B tokens/month free | Mistral Small | `dartlab setup mistral` |

**Other providers:**

| Provider | Auth | Cost | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT subscription (Plus/Team/Enterprise) | Included in subscription | Yes |
| `openai` | API key (`OPENAI_API_KEY`) | Pay-per-token | Yes |
| `ollama` | Local install, no account needed | Free | Depends on model |
| `codex` | Codex CLI installed locally | Free (uses your Codex session) | Yes |
| `custom` | Any OpenAI-compatible endpoint | Varies | Varies |

**Auto-fallback:** Set multiple free API keys and DartLab automatically switches to the next provider when one hits its rate limit. Use `provider="free"` to enable the fallback chain:

```python
dartlab.ask("삼성전자 분석", provider="free")
```

**Why no Claude provider?** Anthropic does not offer OAuth-based access. Without OAuth, there is no way to let users authenticate with their existing subscription — we would have to ask users to paste API keys, which goes against DartLab's frictionless design. If Anthropic adds OAuth support in the future, we will add a Claude provider. For now, Claude works through **MCP** (see below) — Claude Desktop, Claude Code, and Cursor can call DartLab's 60 tools directly.

**`oauth-codex`** is the recommended provider — if you have a ChatGPT subscription, it works out of the box with no API keys. Run `dartlab setup oauth-codex` to authenticate.

**Web UI (`dartlab`)** launches a browser-based chat interface for interactive analysis. This feature is currently **experimental** — we are evaluating the right scope and UX for visualization and collaborative features.

### Project Settings (`.dartlab.yml`)

```yaml
company: 005930         # default company
provider: openai        # default LLM provider
model: gpt-4o           # default model
verbose: false
```

## MCP — AI Assistant Integration

DartLab includes a built-in [MCP](https://modelcontextprotocol.io/) server that exposes 60 tools (16 global + 44 per-company) to Claude Desktop, Claude Code, Cursor, and any MCP-compatible client.

```bash
uv add "dartlab[mcp]"
```

### Claude Desktop

Add to `claude_desktop_config.json`:

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

### Claude Code

```bash
claude mcp add dartlab -- uv run dartlab mcp
```

Or add to `~/.claude/settings.json`:

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

### Cursor

Add to `.cursor/mcp.json` with the same config format as Claude Desktop.

### What's Available

Once connected, your AI assistant can:

- **Search** — find companies by name or code (`search_company`)
- **Show** — read any disclosure topic (`show_topic`, `list_topics`, `diff_topic`)
- **Finance** — balance sheet, income statement, cash flow, ratios (`get_financial_statements`, `get_ratios`)
- **Analysis** — insights, sector ranking, valuation (`get_insight`, `get_ranking`)
- **EDGAR** — same tools work for US companies (`stock_code: "AAPL"`)

Auto-generate config for your platform:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

## OpenAPI — Raw Public APIs

Use source-native wrappers when you want raw disclosure APIs directly.

### OpenDart (Korea)

> **Note:** `Company` does **not** require an API key — it uses pre-built datasets.
> `OpenDart` uses the raw DART API and requires a key from [opendart.fss.or.kr](https://opendart.fss.or.kr) (free).
> Recent filing-list AI questions across the whole market also use this key. In the UI, open Settings and manage `OpenDART API key` there.

```python
from dartlab import OpenDart

d = OpenDart()
d.search("카카오", listed=True)
d.filings("삼성전자", "2024")
d.finstate("삼성전자", 2024)
d.report("삼성전자", "배당", 2024)
```

### OpenEdgar (US)

> **No API key required.** SEC EDGAR is a public API — no registration needed.

```python
from dartlab import OpenEdgar

e = OpenEdgar()
e.search("Apple")
e.filings("AAPL", forms=["10-K", "10-Q"])
e.companyFactsJson("AAPL")
```

## Data

**No manual setup required.** When you create a `Company`, dartlab automatically downloads the required data.

| Dataset | Coverage | Size | Source |
|---------|----------|------|--------|
| DART docs | 2,500+ companies | ~8 GB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/docs) |
| DART finance | 2,700+ companies | ~600 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/finance) |
| DART report | 2,700+ companies | ~320 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/report) |
| DART scan | Pre-built cross-company | ~271 MB | [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data/tree/main/dart/scan) |
| EDGAR | On-demand | — | SEC API (auto-fetched) |

### 3-Step Data Pipeline

```
dartlab.Company("005930")
  │
  ├─ 1. Local cache ──── already have it? done (instant)
  │
  ├─ 2. HuggingFace ──── auto-download (~seconds, no key needed)
  │
  └─ 3. DART API ──────── collect with your API key (needs key)
```

If a company is not in HuggingFace, dartlab collects data directly from DART — this requires an API key:

```bash
dartlab setup dart-key
```

### Freshness — Automatic Update Detection

DartLab uses a 3-layer freshness system to keep your local data current:

| Layer | Method | Cost |
|-------|--------|------|
| L1 | HTTP HEAD → ETag comparison with HuggingFace | ~0.5s, few hundred bytes |
| L2 | Local file age (90-day TTL fallback) | instant (local) |
| L3 | DART API → `rcept_no` diff (requires API key) | 1 API call, ~1s |

When you open a `Company`, dartlab checks if newer data exists. If a new disclosure was filed:

```python
c = dartlab.Company("005930")
# [dartlab] ⚠ 005930 — 새 공시 2건 발견 (사업보고서 (2024.12))
#   • 증분 수집: dartlab collect --incremental 005930
#   • 또는 Python: c.update()

c.update()  # incremental collect — only missing filings
```

```bash
# CLI freshness check
dartlab collect --check 005930         # single company
dartlab collect --check                # scan all local companies (7 days)

# incremental collect — only missing filings
dartlab collect --incremental 005930   # single company
dartlab collect --incremental          # all local companies with new filings
```

### Batch Collection (DART API)

```bash
dartlab collect --batch                    # all listed, missing only
dartlab collect --batch -c finance 005930  # specific category + company
dartlab collect --batch --mode all         # re-collect everything
```

## Try It Now

### Live Demo

**[Open Live Demo](https://huggingface.co/spaces/eddmpython/dartlab)** -- no install, no Python

### Notebooks

| Feature | Description | Colab | Molab |
|---------|-------------|-------|-------|
| **Company** | `Company("005930")` -- index, show, select, trace, diff + finance shortcuts | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- 13-axis cross-market scan, 2,700+ companies | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Review** | `c.review()` -- 14-section structured report + `c.reviewer()` AI interpretation | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_review.py) |
| **Gather** | `price()`, `macro()`, `consensus()` -- market data with fallback chains | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/04_gather.py) |

<details>
<summary>Run locally with Marimo</summary>

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
marimo edit notebooks/marimo/02_scan.py
marimo edit notebooks/marimo/03_review.py
marimo edit notebooks/marimo/04_gather.py
```

</details>

## Documentation

- Docs: https://eddmpython.github.io/dartlab/
- Sections guide: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- Quick start: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API overview: https://eddmpython.github.io/dartlab/docs/api/overview
- Beginner guide (Korean): https://eddmpython.github.io/dartlab/blog/dartlab-easy-start/

### Blog

The [DartLab Blog](https://eddmpython.github.io/dartlab/blog/) covers practical disclosure analysis — how to read reports, interpret patterns, and spot risk signals. 120+ articles across three categories:

- **Disclosure Systems** — structure and mechanics of DART/EDGAR filings
- **Report Reading** — practical guide to audit reports, preliminary earnings, restatements
- **Financial Interpretation** — financial statements, ratios, and disclosure signals

## Stability

| Tier | Scope |
|------|-------|
| **Stable** | DART Company (sections, show, trace, diff, BS/IS/CF, CIS, index, filings, profile), EDGAR Company core, valuation, forecast, simulation |
| **Beta** | EDGAR power-user (SCE, notes, freq, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text tools, ask/chat, OpenDart, OpenEdgar, Server API, MCP, CLI subcommands |
| **Experimental** | AI tool calling, export |
| **Alpha** | Desktop App (Windows .exe) — functional but incomplete, Sections Viewer — not yet fully structured |

See [docs/stability.md](docs/stability.md).

## Contributing

The project prefers **experiments before engine changes**. If you want to propose a parser or mapping change, validate it in `experiments/` first and bring the verified result back into the engine.

- **Experiment folder**: `experiments/XXX_camelCaseName/` — each file must be independently runnable with actual results in its docstring
- **Data contributions** (e.g. `accountMappings.json`, `sectionMappings.json`): only accepted when backed by experiment evidence — no manual bulk edits
- Issues and PRs in Korean or English are both welcome

## License

MIT
