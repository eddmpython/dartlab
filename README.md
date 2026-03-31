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

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [What DartLab Is](#what-dartlab-is)
  - [Data — Everything Is Ready](#data--everything-is-ready)
  - [Company — The Two Problems](#company--the-two-problems)
  - [Scan — The Whole Market in One Call](#scan--the-whole-market-in-one-call)
  - [Analysis — From Numbers to Story](#analysis--from-numbers-to-story)
  - [Gather — External Market Data](#gather--external-market-data)
  - [Review — Analysis to Report](#review--analysis-to-report)
  - [AI — Your Active Analyst](#ai--your-active-analyst)
- [EDGAR (US)](#edgar-us)
- [MCP — AI Assistant Integration](#mcp--ai-assistant-integration)
- [OpenAPI — Raw Public APIs](#openapi--raw-public-apis)
- [Data](#data)
- [Try It Now](#try-it-now)
- [Documentation](#documentation)
- [Stability](#stability)
- [Contributing](#contributing)

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

---

**No data setup required.** When you create a `Company`, dartlab automatically downloads the required data from [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data) (DART) or SEC API (EDGAR). The second run loads instantly from local cache.

## Quick Start

```python
import dartlab

# Samsung Electronics — from raw filings to structured data
c = dartlab.Company("005930")
c.sections                      # every topic, every period, side by side
c.show("businessOverview")      # what this company actually does
c.diff("businessOverview")      # what changed since last year
c.BS                            # standardized balance sheet
c.ratios                        # financial ratios, already calculated

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

DartLab is built on one premise: **every period must be comparable, and every company must be comparable.** Without this, no analysis is possible — you're comparing filing formats, not companies. Every feature in DartLab exists to make this premise real.

Two engines turn raw filings into one comparable map.

### Data — Everything Is Ready

> Design: [ops/data.md](ops/data.md)

All data is pre-built on [HuggingFace](https://huggingface.co/datasets/eddmpython/dartlab-data). `pip install dartlab` and `Company("005930")` — that's it. No API key, no manual download, no data pipeline to configure.

Why HuggingFace? Because raw DART filings are scattered across thousands of ZIP files and XML fragments. Parsing, normalizing, and structuring all of this from scratch takes hours per company. DartLab pre-builds this entire pipeline and publishes the result so you never have to.

| Dataset | Coverage | Size |
|---------|----------|------|
| DART docs | 2,500+ companies | ~8 GB |
| DART finance | 2,700+ companies | ~600 MB |
| DART report | 2,700+ companies | ~320 MB |
| DART scan | Pre-built cross-company | ~271 MB |
| EDGAR | On-demand | SEC API (auto-fetched) |

The data pipeline has three layers: local cache (instant) → HuggingFace (auto-download, no key) → DART API (direct collection with your own key). Most users never leave the first two.

### Company — The Two Problems

> Design: [ops/company.md](ops/company.md)

If every period and every company must be comparable, two obstacles stand in the way:

**1. The same company says different things differently every year.**

Sections horizontalization normalizes every disclosure section into a **topic x period** grid. Different titles across years and industries all resolve to the same canonical topic:

```
                    2025Q4    2024Q4    2024Q3    2023Q4    ...
companyOverview       v         v         v         v
businessOverview      v         v         v         v
productService        v         v         v         v
employee              v         v         v         v
dividend              v         v         v         v
```

```
Before (raw section titles):              After (canonical topic):
Samsung    "II. 사업의 내용"               -> businessOverview
Hyundai    "II. 사업의 내용 [자동차부문]"   -> businessOverview
Kakao      "2. 사업의 내용"               -> businessOverview
```

~95%+ mapping rate across all listed companies. Each cell keeps the full text with heading/body separation, tables, and original evidence.

**2. Every company names the same number differently.**

Account standardization normalizes every XBRL account into a single canonical name:

```
Before (raw XBRL):                          After (standardized):
Company     account_id          account_nm   ->  snakeId    label
Samsung     ifrs-full_Revenue   수익(매출액)  ->  revenue    매출액
SK Hynix    dart_Revenue        매출액       ->  revenue    매출액
LG Energy   Revenue             매출         ->  revenue    매출액
```

~97% mapping rate. Cross-company comparison requires zero manual work.

`Company` merges three data sources — docs (full-text disclosures), finance (XBRL financial statements), and report (structured DART API data) — into one object:

```python
c = dartlab.Company("005930")

c.index                         # what's available -- topic list + periods
c.show("BS")                    # view data -- DataFrame per topic
c.select("IS", ["매출액"])       # extract data -- finance or docs, same pattern
c.trace("BS")                   # where it came from -- source provenance
c.diff()                        # what changed -- text changes across periods

c.analysis("수익성")             # analyze -- financial analysis
c.review()                      # report -- structured full report
```

`select()` works on any topic — `"IS"`, `"BS"`, `"CF"` for financial statements, or any docs topic like `"productService"`, `"salesOrder"` for disclosure tables. Same pattern, single entry point.

### Scan — The Whole Market in One Call

> Design: [ops/scan.md](ops/scan.md)

If every company is comparable, the next question is natural: compare them.

Company looks at one firm deeply. Scan looks at all firms horizontally. When you want to know "which companies have the highest ROE" or "who changed auditors this year," you need cross-sectional analysis across the entire market.

`scan()` is the single entry point.

```python
dartlab.scan()                        # guide: list all axes + usage
dartlab.scan("governance")            # governance structure across all firms
dartlab.scan("governance", "005930")  # filter to one company
dartlab.scan("ratio", "roe")          # ROE across all firms
dartlab.scan("account", "매출액")     # revenue across all firms
dartlab.scan("cashflow")              # OCF/ICF/FCF + 8-pattern classification
```

| Axis | Label | What it does |
|------|-------|--------------|
| governance | Governance | Ownership, outside directors, pay ratio, audit opinion |
| workforce | Workforce | Headcount, avg salary, labor cost ratio, value added per employee |
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

Adding a new axis means one module — no other code changes needed.

### Analysis — From Numbers to Story

> Design: [ops/analysis.md](ops/analysis.md)

Every company has a story. Revenue structure explains what it does; profitability reveals how well; cash flow shows whether earnings are real; stability tells if it can survive; capital allocation shows where the money goes; and the outlook connects past to future. These six acts form a causal chain — each act explains the next.

Raw financial statements are numbers. Knowing that revenue is 302 trillion KRW tells you nothing about whether this company is healthy, growing, or at risk. Analysis bridges this gap — not with a dashboard of disconnected ratios, but with a narrative where each number earns its place in the story.

`analysis()` transforms financial statements into structured, story-ready data. It is the middle layer between raw data and every consumer — Review (reports), AI (interpretation), and humans (direct reading). When analysis quality improves, all three benefit simultaneously.

```
All Company Data (finance + docs + report)
    |  Company.select()  <- single access point for everything
analysis()  ->  14-axis structured data (amounts + ratios + YoY + flags)
    |              |              |
 review()       AI(ask)        human
 reports        interpret      interpret
```

Same 3-step call pattern as scan.

```python
dartlab.analysis()                    # guide: list all axes
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

### Gather — External Market Data

> Design: [ops/gather.md](ops/gather.md)

Company and Scan work with disclosure data — what the company filed. But investors also need market data: stock prices, institutional flows, macro indicators, news. Gather bridges the gap between filings and the market.

`gather()` collects external market data — all as **Polars DataFrames**.

```python
dartlab.gather()                              # guide -- 4 axes
dartlab.gather("price", "005930")             # KR OHLCV timeseries (1-year default)
dartlab.gather("price", "AAPL", market="US")  # US stock
dartlab.gather("flow", "005930")              # foreign/institutional flow (KR)
dartlab.gather("macro")                       # KR macro indicators
dartlab.gather("macro", "FEDFUNDS")           # single indicator (auto-detects US)
dartlab.gather("news", "삼성전자")             # Google News RSS
```

Company-bound: `c.gather("price")` — no need to pass the stock code again.

### Review — Analysis to Report

> Design: [ops/review.md](ops/review.md)

Analysis produces structured data. Review assembles it into a human-readable report that follows the six-act narrative — from "what does this company do" to "what is it worth." Each analysis axis becomes a report section with tables, flags, and narrative context, connected by causal transitions between acts.

```python
c.review()              # all sections, full report
c.review("수익구조")     # single section
```

4 output formats: `rich` (terminal), `html`, `markdown`, `json`.

**Sample reports** (generated by `c.review().toMarkdown()`):

| Company | Sector | Key characteristics |
|---------|--------|-------------------|
| [Samsung Electronics](docs/samples/005930.md) | Semiconductor | Mid-cycle FCF normalization, cycle-adjusted DCF |
| [SK Hynix](docs/samples/000660.md) | Semiconductor | HBM structural growth vs DRAM/NAND cycle |
| [Kia](docs/samples/000270.md) | Auto | EV transition capex impact, dividend policy |
| [HD Hyundai Heavy Industries](docs/samples/042660.md) | Shipbuilding | Loss-making turnaround, backlog-driven valuation gap |
| [SK Telecom](docs/samples/017670.md) | Telecom | Stable dividend, holding-like subsidiary structure |
| [LG Chem](docs/samples/051910.md) | Chemical/Battery | EBITDA-negative EV/Sales fallback, segment divergence |
| [SK](docs/samples/034730.md) | Holding | Conglomerate discount, NAV/SOTP gap |
| [NCSoft](docs/samples/036570.md) | Game | Pipeline-dependent, R&D-driven valuation |
| [Amorepacific](docs/samples/090430.md) | Consumer | Brand value, channel shift (duty-free to e-commerce) |
| [Hyundai Steel](docs/samples/004020.md) | Steel/Cyclical | Mid-cycle normalization, China overcapacity |

Each report ends with an **Analysis Limitations** section documenting known model constraints.

**Reviewer** adds AI opinions on top of review:

```python
c.reviewer()                                    # full + AI
c.reviewer(guide="Evaluate from semiconductor cycle perspective")
```

### Search — Find Filings by Meaning *(alpha)*

> Design: [ops/search.md](ops/search.md)

Listed companies file thousands of disclosures — capital raises, lawsuits, CEO changes, M&A. DartLab collects filing texts and makes them searchable by meaning, not just title.

```python
import dartlab

dartlab.search("유상증자 결정")                     # semantic search across all filings
dartlab.search("대표이사 변경", corp="005930")       # filter by company
dartlab.search("전환사채 발행", start="20240101")    # filter by date
```

Behind the scenes: daily filing lists → full-text parsing (99.4% success) → ngram index + synonym expansion. No model loading, no GPU required. Search latency: **~1ms**, precision **95%**.

Two-phase collection — metadata first (lightweight), then full text (one API call per filing):

```python
from dartlab.core.search import collectMeta, fillContent, buildIndex  # advanced

collectMeta("20210401", "20260330")    # phase 1: filing list (fast)
fillContent()                          # phase 2: full text (incremental)
buildIndex()                           # phase 3: vector embedding (GPU)
```

All steps are incremental — already-collected dates, texts, and vectors are skipped on re-run.

> **Status:** alpha — pre-built vector index available on HuggingFace. Requires `pip install dartlab[vector]`.

### AI — Your Active Analyst

> Design: [ops/ai.md](ops/ai.md)

The AI in DartLab is not a passive narrator. It is an active analyst that uses dartlab as its toolkit — calling functions, writing code, running analysis, and building its own workflow to answer your question.

When you ask a question, the AI writes and executes Python code using dartlab's full API. You see every line of code it runs and every result it produces. This means you don't just get answers — you learn how to analyze companies yourself. The AI can combine any dartlab function — `analysis()`, `scan()`, `gather()`, `review()` — in whatever sequence the question demands.

```python
import dartlab

answer = dartlab.ask("Analyze Samsung Electronics financial health")

# provider + model override
answer = dartlab.ask("Samsung analysis", provider="openai", model="gpt-4o")

# agent mode — LLM selects tools for deeper analysis
answer = dartlab.chat("005930", "Analyze dividend trends and find anomalies")
```

### Providers

**Free API key providers** — sign up, paste the key, start analyzing:

| Provider | Free Tier | Model |
|----------|-----------|-------|
| `gemini` | Gemini 2.5 Pro/Flash free | Gemini 2.5 |
| `groq` | 6K-30K TPM free | LLaMA 3.3 70B |
| `cerebras` | 1M tokens/day permanent | LLaMA 3.3 70B |
| `mistral` | 1B tokens/month free | Mistral Small |

**Other providers:**

| Provider | Auth | Cost | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT subscription (Plus/Team/Enterprise) | Included in subscription | Yes |
| `openai` | API key (`OPENAI_API_KEY`) | Pay-per-token | Yes |
| `ollama` | Local install, no account needed | Free | Depends on model |
| `codex` | Codex CLI installed locally | Free (uses your Codex session) | Yes |
| `custom` | Any OpenAI-compatible endpoint | Varies | Varies |

**Auto-fallback:** Set multiple free API keys and DartLab automatically switches to the next provider when one hits its rate limit. Use `provider="free"` to enable the fallback chain.

**Why no Claude provider?** Anthropic does not offer OAuth-based access. Without OAuth, there is no way to let users authenticate with their existing subscription. If Anthropic adds OAuth support in the future, we will add a Claude provider. For now, Claude works through **MCP** (see below).

**`oauth-codex`** is the recommended provider — if you have a ChatGPT subscription, it works out of the box with no API keys.

### Project Settings (`.dartlab.yml`)

```yaml
company: 005930         # default company
provider: openai        # default LLM provider
model: gpt-4o           # default model
verbose: false
```

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
L2  analysis/    Financial analysis + forecast + valuation
    review/      Block-template report assembly
L3  ai/          Active analyst — LLM with full API access (5 providers)
```

Import direction is enforced by CI — no reverse dependencies allowed.

### Extensibility — Zero Core Modification

Adding a new country requires zero changes to core code:

1. Create a provider package under `providers/`
2. Implement `canHandle(code) -> bool` and `priority() -> int`
3. Register via `entry_points` in `pyproject.toml`

```python
dartlab.Company("005930")  # -> DART provider (priority 10)
dartlab.Company("AAPL")    # -> EDGAR provider (priority 20)
```

The facade iterates providers by priority — first match wins.

## EDGAR (US)

Same `Company` interface, same account standardization pipeline, different data source. EDGAR data is auto-fetched from the SEC API — no pre-download needed:

```python
us = dartlab.Company("AAPL")

us.sections                         # 10-K/10-Q sections with heading/body
us.show("business")                 # business description
us.show("10-K::item1ARiskFactors")  # risk factors
us.BS                               # SEC XBRL balance sheet
us.ratios                           # same ratios
us.diff("10-K::item7Mdna")          # MD&A text changes
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
```

### DART vs EDGAR Namespaces

|               | DART           | EDGAR          |
|---------------|:--------------:|:--------------:|
| `docs`        | v              | v              |
| `finance`     | v              | v              |
| `report`      | v (28 API types) | x (not applicable) |
| `profile`     | v              | v              |

DART has a `report` namespace with structured disclosure APIs (dividend, governance, executive compensation, etc.). This does not exist in EDGAR — SEC filings are structured differently.

**EDGAR topic naming**: Topics use `{formType}::{itemId}` format. Short aliases also work:

```python
us.show("10-K::item1Business")     # full form
us.show("business")                # short alias
us.show("risk")                    # -> 10-K::item1ARiskFactors
us.show("mdna")                    # -> 10-K::item7Mdna
```

## MCP — AI Assistant Integration

DartLab includes a built-in [MCP](https://modelcontextprotocol.io/) server for Claude Desktop, Claude Code, Cursor, and any MCP-compatible client.

### Quick Setup — Copy & Paste

**Claude Code:**

```bash
pip install "dartlab[mcp]" && claude mcp add dartlab -- uv run dartlab mcp
```

**OpenAI Codex CLI:**

```bash
pip install "dartlab[mcp]" && codex mcp add dartlab -- uv run dartlab mcp
```

One line. Install + register in a single command.

**Claude Desktop** — add to `claude_desktop_config.json`:

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

**Cursor** — add to `.cursor/mcp.json` with the same format as above.

Auto-generate config if you're not sure where the file is:

```bash
dartlab mcp --config claude-desktop
dartlab mcp --config claude-code
dartlab mcp --config cursor
```

### What's Available

Once connected, your AI assistant can:

- **Search** — find companies by name or code (`searchCompany`)
- **Profile** — company overview, governance, sector (`companyProfile`, `companyGovernance`)
- **Financials** — balance sheet, income statement, cash flow, ratios (`companyFinancials`, `companyRatios`)
- **Analysis** — insights, valuation, forecast (`companyInsights`, `companyValuation`, `companyForecast`)
- **Disclosure** — read any topic, diff across periods (`companyShow`, `companyTopics`, `companyDiff`)
- **Review** — full analysis report (`companyReview`, `companyAudit`)
- **Market** — sector screening, peer comparison (`marketScan`)

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
  |
  +- 1. Local cache ------ already have it? done (instant)
  |
  +- 2. HuggingFace ------ auto-download (~seconds, no key needed)
  |
  +- 3. DART API ---------- collect with your API key (needs key)
```

If a company is not in HuggingFace, dartlab collects data directly from DART — this requires an API key:

```bash
dartlab setup dart-key
```

### Freshness — Automatic Update Detection

DartLab uses a 3-layer freshness system to keep your local data current:

| Layer | Method | Cost |
|-------|--------|------|
| L1 | HTTP HEAD -> ETag comparison with HuggingFace | ~0.5s, few hundred bytes |
| L2 | Local file age (90-day TTL fallback) | instant (local) |
| L3 | DART API -> `rcept_no` diff (requires API key) | 1 API call, ~1s |

When you open a `Company`, dartlab checks if newer data exists. If a new disclosure was filed:

```python
c = dartlab.Company("005930")
# [dartlab] 005930 -- new filings detected (사업보고서 (2024.12))

c.update()  # incremental collect -- only missing filings
```

## Try It Now

### Live Demo

**[Open Live Demo](https://huggingface.co/spaces/eddmpython/dartlab)** -- no install, no Python

### Notebooks

| Feature | Description | Colab | Molab |
|---------|-------------|-------|-------|
| **Company** | `Company("005930")` -- index, show, select, trace, diff + finance shortcuts | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/01_company.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/01_company.py) |
| **Scan** | `scan()` -- cross-market scan, 2,700+ companies | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/02_scan.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/02_scan.py) |
| **Review** | `c.review()` -- structured report + `c.reviewer()` AI interpretation | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/03_review.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/03_review.py) |
| **Gather** | `gather()` -- price, flow, macro, news in one call | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/04_gather.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/04_gather.py) |
| **Analysis** | `c.analysis()` -- 14-axis analysis, insights, forecast, valuation | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/05_analysis.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/05_analysis.py) |
| **Ask (AI)** | `ask("...")` -- natural language analysis with LLM | [![Open in Colab](https://img.shields.io/badge/Open_in_Colab-Google-ea4647?style=for-the-badge&labelColor=050811&logo=googlecolab&logoColor=white)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/colab/06_ask.ipynb) | [![Open in Molab](https://img.shields.io/badge/Open_in_Molab-marimo-38bdf8?style=for-the-badge&labelColor=050811)](https://molab.marimo.io/github/eddmpython/dartlab/blob/master/notebooks/marimo/06_ask.py) |

<details>
<summary>Run locally with Marimo</summary>

```bash
uv add dartlab marimo
marimo edit notebooks/marimo/01_company.py
marimo edit notebooks/marimo/02_scan.py
marimo edit notebooks/marimo/03_review.py
marimo edit notebooks/marimo/04_gather.py
marimo edit notebooks/marimo/05_analysis.py
marimo edit notebooks/marimo/06_ask.py
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
| **Beta** | EDGAR power-user (SCE, notes, freq, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text tools, ask/chat, OpenDart, OpenEdgar, Server API, MCP |
| **Experimental** | AI tool calling, export |

See [docs/stability.md](docs/stability.md).

## Contributing

The project prefers **experiments before engine changes**. If you want to propose a parser or mapping change, validate it in `experiments/` first and bring the verified result back into the engine.

- **Experiment folder**: `experiments/XXX_camelCaseName/` — each file must be independently runnable with actual results in its docstring
- **Data contributions** (e.g. `accountMappings.json`, `sectionMappings.json`): only accepted when backed by experiment evidence — no manual bulk edits
- Issues and PRs in Korean or English are both welcome

## License

MIT
