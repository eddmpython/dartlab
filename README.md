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
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-120%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">Docs</a> · <a href="https://eddmpython.github.io/dartlab/blog/">Blog</a> · <a href="notebooks/marimo/">Marimo Notebooks</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/01_quickstart.ipynb">Open in Colab</a> · <a href="README_KR.md">한국어</a> · <a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
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

Install only what you need:

```bash
uv add "dartlab[ai]"              # web UI, server, streaming (FastAPI + uvicorn)
uv add "dartlab[llm]"             # LLM analysis (OpenAI)
uv add "dartlab[charts]"          # Plotly charts, network graphs (plotly + networkx + scipy)
uv add "dartlab[mcp]"             # MCP server for Claude Desktop / Code / Cursor
uv add "dartlab[channel]"         # web UI + cloudflared tunnel sharing
uv add "dartlab[channel-ngrok]"   # web UI + ngrok tunnel sharing
uv add "dartlab[channel-full]"    # all channels + Telegram / Slack / Discord bots
uv add "dartlab[all]"             # everything above (except channel bots)
```

**Common combinations:**

```bash
# financial analysis + AI chat
uv add "dartlab[ai,llm]"

# full analysis suite — charts, AI, LLM
uv add "dartlab[ai,llm,charts]"

# share analysis with team via tunnel
uv add "dartlab[channel]"
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

Pick any company. Get the whole picture.

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
dartlab.ask("Analyze Samsung Electronics financial health")
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

~97% mapping rate. Cross-company comparison requires zero manual work. Combined with `scanAccount` / `scanRatio`, you can compare a single metric across **2,700+ companies** in one call.

### Principles — Accessibility and Reliability

These two principles govern every public API:

**Accessibility** — One stock code is all you need. `import dartlab` provides access to every feature. No internal DTOs, no extra imports, no data setup. `Company("005930")` auto-downloads from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data).

**Reliability** — Numbers are raw originals from DART/EDGAR. Missing data returns `None`, never a guess. `trace(topic)` shows which source was chosen and why. Errors are never swallowed.

### Company — The Merged Map

`Company` uses `sections` as the spine, then overlays stronger data sources:

```
Layer         What it provides                   Priority
─────────────────────────────────────────────────────────
docs          Section text, tables, evidence      Base spine
finance       BS, IS, CF, ratios, time series     Replaces numeric topics
report        28 structured APIs (DART only)      Fills structured topics
─────────────────────────────────────────────────────────
profile       Merged view (default for users)     Highest
```

```python
c.docs.sections     # pure text source (sections spine)
c.finance.BS        # authoritative financial statements
c.report.extract()  # structured DART API data
c.profile.sections  # merged view — what users see by default
```

`c.sections` is the merged view. `c.trace("BS")` tells you which source was chosen and why.

### Architecture — Layered by Responsibility

DartLab follows a strict layered architecture where each layer only depends on layers below it:

```
L0  core/        Protocols, finance utils, docs utils, registry
L1  providers/   Country-specific data (DART, EDGAR, EDINET)
    gather/      External market data (Naver, Yahoo, FRED)
    market/      Market-wide scanning (2,700+ companies)
L2  analysis/    8 analytical domains (see below)
L3  ai/          LLM-powered analysis (9 providers)
```

Import direction is enforced by CI — no reverse dependencies allowed.

### Analysis — Eight Domains of Corporate Analysis

DartLab's analysis engine is structured around eight academic domains, adapted from Palepu-Healy's framework and cross-referenced with CFA, McKinsey, and S&P methodologies:

| # | Domain | What it covers |
|---|--------|---------------|
| 1 | **Strategy** | Business model, competitive advantage, ESG, governance |
| 2 | **Accounting** | Earnings quality, disclosure analysis, red flags |
| 3 | **Financial** | Ratios, DuPont, trend, cash flow, distress prediction |
| 4 | **Forecast** | Financial projections, scenarios, Monte Carlo |
| 5 | **Valuation** | DCF, multiples, analyst synthesis |
| 6 | **Risk** | Financial / business / market risk, credit assessment |
| 7 | **Comparative** | Peer, sector, ranking, event study |
| 8 | **Macro** | Macroeconomic cycles, industry analysis |

Each domain maps to a package under `analysis/` and can be consumed independently or through the AI layer.

### Extensibility — Zero Core Modification

Adding a new country requires zero changes to core code:

1. Create a provider package under `providers/`
2. Implement `canHandle(code) -> bool` and `priority() -> int`
3. Register via `entry_points` in `pyproject.toml`

```python
dartlab.Company("005930")  # → DART provider (priority 10)
dartlab.Company("AAPL")    # → EDGAR provider (priority 20)
```

The facade iterates providers by priority — first match wins. This follows the same pattern as OpenBB's provider system and scikit-learn's estimator registration.

## Core Features

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

What the output looks like:

```
>>> c.show("businessOverview")
shape: (12, 5)
┌───────────┬──────────┬──────────────────────────────┬──────────────────────────────┐
│ blockType │ nodeType │ 2024                         │ 2023                         │
├───────────┼──────────┼──────────────────────────────┼──────────────────────────────┤
│ text      │ heading  │ 1. 산업의 특성                │ 1. 산업의 특성                │
│ text      │ body     │ 반도체 산업은 기술 집약적 …   │ 반도체 산업은 기술 집약적 …    │
│ table     │ null     │ DataFrame(5×3)               │ DataFrame(5×3)               │
└───────────┴──────────┴──────────────────────────────┴──────────────────────────────┘

>>> c.diff("businessOverview", "2023", "2024")
┌──────────┬─────────────────────────────────────────────┐
│ status   │ text                                        │
├──────────┼─────────────────────────────────────────────┤
│ added    │ AI 반도체 수요 급증에 따른 HBM 매출 확대 …   │
│ modified │ 매출액 258.9조원 → 300.9조원                 │
│ removed  │ 반도체 부문 수익성 악화 우려 …               │
└──────────┴─────────────────────────────────────────────┘
```

### Finance

```python
c.BS                    # balance sheet (account × period, newest first)
c.IS                    # income statement
c.CF                    # cash flow
c.ratios                # ratio time series DataFrame (6 categories × period)
c.finance.ratioSeries   # ratio time series across years
c.finance.timeseries    # raw account time series
c.annual                # annual time series
c.filings()             # disclosure document list (Tier 1 Stable)
```

All accounts are normalized through the 4-step standardization pipeline — Samsung's `revenue` and LG's `revenue` are the same `snakeId`. Ratios cover 6 categories: profitability, stability, growth, efficiency, cashflow, and valuation.

### Market-wide Financial Screening

Scan a single account or ratio across **all listed companies** in one call — 2,700+ DART firms or 500+ EDGAR firms. Returns a wide Polars DataFrame (rows = companies, columns = periods, newest first).

```python
import dartlab

# scan a single account across all listed companies
dartlab.scanAccount("매출액")                         # revenue, quarterly standalone
dartlab.scanAccount("operating_profit", annual=True)  # annual basis
dartlab.scanAccount("total_assets", market="edgar")   # US EDGAR

# scan a ratio across all listed companies
dartlab.scanRatio("roe")                              # quarterly ROE for all firms
dartlab.scanRatio("debtRatio", annual=True)           # annual debt-to-equity

# list available ratios (13 ratios: profitability, stability, growth, efficiency, cashflow)
dartlab.scanRatioList()
```

Accepts both Korean names (`매출액`) and English snakeIds (`sales`) — same 4-step normalization as Company finance. Reads 2,700+ parquet files in parallel via ThreadPool, typically completes in ~3 seconds.

> **Requires pre-downloaded data.** Market-wide functions (`scanAccount`, `screen`, `digest`, etc.) operate on local data — individual `Company()` calls only download one firm at a time. Download all data first:
> ```python
> pip install dartlab[hf]
> dartlab.downloadAll("finance")   # ~600 MB, 2,700+ firms
> dartlab.downloadAll("report")    # ~320 MB (governance/workforce/capital/debt)
> dartlab.downloadAll("docs")      # ~8 GB (digest/signal — large)
> ```

## Review — Structured Company Analysis

DartLab's review system assembles financial data into structured, readable reports.

### Templates

Pre-built block combinations that cover key analysis areas:

```python
c = dartlab.Company("005930")

c.review("수익구조")    # revenue structure — segments, growth, concentration
c.review("자금조달")    # capital structure — debt, liquidity, interest burden
c.review()             # all templates
```

### Block Assembly

Every review is built from reusable blocks. Get the full block dictionary and assemble your own:

```python
from dartlab.review import blocks, Review

b = blocks(c)          # dict of 16 pre-built blocks
list(b.keys())         # → ["profile", "segmentComposition", "growth", ...]

# pick what you need
Review([
    b["segmentComposition"],
    b["growth"],
    c.select("IS", ["매출액"]),   # mix with raw data
])
```

### Reviewer — AI Layer

Add LLM-powered opinions on top of data blocks. Works with any provider:

```python
c.reviewer()                                    # all sections + AI opinion
c.reviewer("수익구조")                           # single section + AI
c.reviewer(guide="Evaluate from semiconductor cycle perspective")  # custom guide
```

**Free AI providers** — no paid API key required:

| Provider | Setup |
|----------|-------|
| Gemini | `dartlab setup gemini` |
| Groq | `dartlab setup groq` |
| Cerebras | `dartlab setup cerebras` |
| Mistral | `dartlab setup mistral` |

Or use any OpenAI-compatible endpoint:
```bash
dartlab setup custom --base-url http://localhost:11434/v1   # Ollama local
```

### Customization

- **Templates**: Pre-defined block combinations (`수익구조`, `자금조달`)
- **Free assembly**: Mix any blocks + raw DataFrames in `Review([...])`
- **Guide**: Pass `guide="..."` to `c.reviewer()` for domain-specific AI analysis
- **Layout**: `ReviewLayout(indentH1=2, gapAfterH1=1, ...)` for rendering control
- **Render formats**: `review.render("rich" | "html" | "markdown" | "json")`

See [notebooks/marimo/sampleReview.py](notebooks/marimo/sampleReview.py) for interactive examples.

## Additional Features

> Features below are **beta** or **experimental** — APIs may change. See [stability](docs/stability.md).

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

Install chart dependencies: `uv add "dartlab[charts]"`

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

```python
c = dartlab.Company("005930")

# one company → market-wide
c.governance()           # single company
c.governance("all")      # full market DataFrame
dartlab.governance()     # module-level scan
dartlab.workforce()
dartlab.capital()
dartlab.debt()

# screening & benchmarking
dartlab.screen()         # multi-factor screening
dartlab.benchmark()      # peer comparison
dartlab.signal()         # change detection signals
```

### Market Data Collection (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

The Gather engine collects external market data as **Polars DataFrames** — timeseries by default. Every request goes through automatic fallback chains, circuit breaker isolation, and TTL caching. All methods are synchronous — async parallel execution is handled internally.

```python
import dartlab

# OHLCV timeseries — adjusted prices, 6000+ trading days in a single request
dartlab.price("005930")                         # KR: 1-year default, Polars DataFrame
dartlab.price("005930", start="2015-01-01")     # custom range
dartlab.price("AAPL", market="US")              # US via Yahoo Finance chart API
dartlab.price("005930", snapshot=True)          # opt-in: current price snapshot

# supply/demand flow timeseries (KR only)
dartlab.flow("005930")                          # DataFrame (date, foreignNet, institutionNet, ...)

# macro indicators — full wide DataFrame
dartlab.macro()                                 # KR 12 indicators (CPI, rates, FX, production, ...)
dartlab.macro("US")                             # US 25 indicators (GDP, CPI, Fed Funds, S&P500, ...)
dartlab.macro("CPI")                            # single indicator (auto-detects KR)
dartlab.macro("FEDFUNDS")                       # single indicator (auto-detects US)

# consensus, news
dartlab.consensus("005930")                     # target price & analyst opinion
dartlab.news("삼성전자")                         # Google News RSS → DataFrame
```

**How data is collected — don't worry, it's safe:**

| Source | Data | Method |
|--------|------|--------|
| Naver Chart API | KR OHLCV (adjusted prices) | `fchart.stock.naver.com` — 1 request per stock, max 6000 days |
| Yahoo Finance v8 | US/Global OHLCV | `query2.finance.yahoo.com/v8/finance/chart` — public chart API |
| ECOS (Bank of Korea) | KR macro indicators | Official API with user's own key |
| FRED (St. Louis Fed) | US macro indicators | Official API with user's own key |
| Naver Mobile API | Consensus, flow, sector PER | `m.stock.naver.com/api` — JSON endpoints |
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
c.news()                              # recent 30 days
dartlab.news("AAPL", market="US")     # US company news

# global peer mapping (WICS → GICS sector)
dartlab.crossBorderPeers("005930")    # → ["AAPL", "MSFT", "NVDA", "TSM", "AVGO"]

# currency conversion (FRED-based)
from dartlab.engines.common.finance import getExchangeRate, convertValue
getExchangeRate("KRW")                # KRW/USD rate
convertValue(1_000_000, "KRW", "USD") # → ~730.0

# audit opinion normalization (KR/EN/JP → canonical code)
from dartlab.engines.common.audit import normalizeAuditOpinion
normalizeAuditOpinion("적정")          # → "unqualified"
normalizeAuditOpinion("Qualified")     # → "qualified"
```

Disclosure gap detection runs automatically inside `c.insights` — flags mismatches between text changes and financial health (e.g. risk text surges while financials are stable).

### Export (experimental)

> **Experimental** — Breaking changes possible. Not for production.

```bash
dartlab excel "005930" -o samsung.xlsx
```

Install: `uv add "dartlab[ai]"` (Excel export is included in the AI extras).

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

> **Tip:** New to financial analysis or prefer natural language? Use `dartlab.ask()` — the AI assistant handles everything from data download to analysis. No coding knowledge required.

DartLab includes a built-in AI analysis layer that feeds structured company data to LLMs. **No code required** — you can ask questions in plain language and DartLab handles everything: data selection, context assembly, and streaming the answer.

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

Install AI dependencies: `uv add "dartlab[ai]"`

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

### Marimo Notebooks

> Data is automatically downloaded on first use. No setup required unless collecting new companies directly from DART.

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/dartCompany.py    # Korean company (DART)
marimo edit notebooks/marimo/edgarCompany.py   # US company (EDGAR)
marimo edit notebooks/marimo/aiAnalysis.py     # AI analysis examples
```

### Colab Notebooks

**Showcase** (English — global audience):

| Notebook | Topic |
|---|---|
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/01_quickstart.ipynb) | **Quick Start** — analyze any company in 3 lines |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/02_financial_analysis.ipynb) | **Financial Analysis** — statements, time series, ratios |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/03_kr_us_compare.ipynb) | **Korea vs US** — Samsung vs Apple side-by-side |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/04_risk_diff.ipynb) | **Risk Diff** — track disclosure changes (Bloomberg can't) |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/05_sector_screening.ipynb) | **Sector Screening** — 8 presets, sector benchmarks |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/06_insight_anomaly.ipynb) | **Insight & Anomaly** — 10-area grading, 6 anomaly rules |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/07_network_governance.ipynb) | **Network & Governance** — corporate relationship graph |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/08_signal_trend.ipynb) | **Signal Trends** — 48-keyword disclosure monitoring |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/09_ai_analysis.ipynb) | **AI Analysis** — `dartlab.ask()` with 9 LLM providers |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/10_disclosure_deep_dive.ipynb) | **Disclosure Deep Dive** — sections architecture |

<details>
<summary>한국어 Tutorials</summary>

| Notebook | Topic |
|---|---|
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/getting-started/quickstart.ipynb) | **빠른 시작** — sections, show, trace, diff |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/02_financial_statements.ipynb) | **재무제표** — BS, IS, CF |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/04_ratios.ipynb) | **재무비율** — 47개 비율 |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb) | **공시 텍스트** — sections 파싱 |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb) | **EDGAR** — 미국 SEC |

</details>

## Documentation

- Docs: https://eddmpython.github.io/dartlab/
- Sections guide: https://eddmpython.github.io/dartlab/docs/getting-started/sections
- Quick start: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API overview: https://eddmpython.github.io/dartlab/docs/api/overview

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
