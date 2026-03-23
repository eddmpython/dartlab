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
<a href="https://eddmpython.github.io/dartlab/blog/"><img src="https://img.shields.io/badge/Blog-120%2B_Articles-fbbf24?style=for-the-badge&labelColor=050811&logo=rss&logoColor=white" alt="Blog"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">Docs</a> · <a href="https://eddmpython.github.io/dartlab/blog/">Blog</a> · <a href="notebooks/marimo/">Marimo Notebooks</a> · <a href="https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/01_quickstart.ipynb">Open in Colab</a> · <a href="README_KR.md">한국어</a> · <a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-320%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

> **Note:** DartLab is under active development. APIs may change between versions, and documentation may lag behind the latest code.

## Install

```bash
# Stable release (PyPI)
uv add dartlab

# Bleeding edge — latest features, but breaking changes possible
git clone https://github.com/eddmpython/dartlab.git
cd dartlab && uv pip install -e .
```

PyPI releases are published only when the core is stable. If you want the latest features (including experimental ones like audit, forecast, valuation), clone the repo directly — but expect occasional breaking changes.

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
c.filings()                     # disclosure document list

us = dartlab.Company("AAPL")    # Apple (EDGAR)
us.sections
us.show("business")
us.BS
us.ratios

# No code needed — ask in natural language
dartlab.ask("Analyze Samsung Electronics financial health")
```

## What DartLab Is

DartLab analyzes corporate disclosure filings — both the **numbers** (financial statements) and the **text** (business descriptions, risk factors, audit reports). It covers Korea (DART), the United States (EDGAR), and is researching Japan (EDINET).

Every company files differently. The same "revenue" can appear as `ifrs-full_Revenue`, `dart_Revenue`, `SalesRevenue`, or dozens of Korean variations. Section titles change by company, year, and industry. Comparing two companies manually means hours of realignment.

DartLab solves this with two standardization engines that turn raw filings into a single, comparable company map.

### Account Standardization

Financial statements use XBRL, but account IDs vary wildly across companies. DartLab normalizes them through a 4-step pipeline:

```
Raw XBRL account_id
  → Step 1: Strip prefixes (ifrs-full_, dart_, ifrs_, ifrs-smes_)
  → Step 2: English ID synonyms (59 rules)
            e.g. NetIncome, Profit, NetProfit → ProfitLoss
  → Step 3: Korean name synonyms (104 rules)
            e.g. 매출, 수익, 영업수익, 매출액합계 → 매출액
  → Step 4: Learned mapping table (34,249 entries)
            AccountMapper resolves to a standardized snakeId
  → Result: revenue, operatingIncome, totalAssets, …
```

Here's what this looks like in practice — the same "revenue" account from three companies:

```
Before (raw XBRL):                          After (standardized):
Company     account_id          account_nm   →  snakeId    label
Samsung     ifrs-full_Revenue   수익(매출액)  →  revenue    매출액
SK Hynix    dart_Revenue        매출액       →  revenue    매출액
LG Energy   Revenue             매출         →  revenue    매출액
```

Every account across every company resolves to the same `snakeId`. Cross-company comparison requires zero manual work.

The mapping table covers ~97% of all listed companies. The remaining edge cases (novel XBRL taxonomies, non-standard filings) fall through gracefully with the original ID preserved.

### Sections Horizontalization

Annual reports have structured sections (business overview, risk factors, dividend policy, etc.), but section titles differ by company, year, and industry. DartLab normalizes every section into a **topic × period** grid:

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

The same section content appears under different titles across companies:

```
Before (raw section titles):              After (canonical topic):
Samsung    "II. 사업의 내용"               → businessOverview
Hyundai    "II. 사업의 내용 [자동차부문]"   → businessOverview
Kakao      "2. 사업의 내용"               → businessOverview
```

The mapping pipeline: **text normalization** (strip industry prefixes, numbering, punctuation) → **545 hardcoded title mappings** → **73 regex patterns** → canonical topic assignment. This achieves ~95%+ mapping rate across all listed companies.

Each cell in the grid contains the full text with heading/body separation, tables, and original evidence. Comparing "what did the company say about risk last year vs. this year" becomes a single `diff()` call.

### Company — The Merged Map

`Company` is where everything comes together. It uses `sections` (the text structure from docs) as the spine, then overlays stronger data sources on top:

```
Layer         What it provides                   Priority
─────────────────────────────────────────────────────────
docs          Section text, tables, evidence      Base spine
finance       BS, IS, CF, ratios, time series     Replaces numeric topics
report        28 structured APIs (DART only)      Fills structured topics
─────────────────────────────────────────────────────────
profile       Merged view (default for users)     Highest
```

- **`docs`** owns narrative text — business descriptions, risk factors, audit opinions
- **`finance`** replaces docs where numbers are stronger — BS, IS, CF become authoritative financial DataFrames
- **`report`** fills in DART-specific structured data — dividend policy, executive compensation, governance details

Four namespaces expose different views:

```python
c.docs.sections     # pure text source (sections spine)
c.finance.BS        # authoritative financial statements
c.report.extract()  # structured DART API data
c.profile.sections  # merged view — what users see by default
```

`c.sections` is the merged view. `c.trace("BS")` tells you which source was chosen and why.

### Core Principles

1. **Sections First** — A company is one horizontalized map, not a loose set of parser outputs
2. **Source-Aware** — When `finance` or `report` is more authoritative, it overrides automatically. `trace()` tells you which source was chosen
3. **Text + Numbers** — Both narrative text (heading/body with metadata) and financial numbers (standardized accounts) live in the same structure
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

### Insights (beta)

> **Beta** — API may change after a warning. See [stability](docs/stability.md).

```python
c.insights                      # 7-area analysis
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
us.insights                         # 7-area grades (A~F)

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

For real-time market-wide disclosure questions such as `최근 7일 수주공시 알려줘` or `이번 주 삼성전자 공시 뭐 있었어`, the UI can store an `OpenDART API key` in project `.env` and the AI will search recent filing lists directly.
▸ ROE 회복세: 1.6% → 10.2% (4분기 연속 개선)

[데이터 출처: 2024Q4 사업보고서, dartlab insights 엔진]
```

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
| Collect | `collect` | Download / refresh data |
| Server | `ai` | Launch web UI (localhost:8400) |
| Server | `share` | Tunnel sharing (ngrok / cloudflared) |
| Server | `status` | Provider connection status |
| Server | `setup` | Provider setup wizard |
| MCP | `mcp` | Start MCP stdio server |
| Plugin | `plugin` | Create / list plugins |

</details>

### Providers

| Provider | Auth | Cost | Tool Calling |
|----------|------|------|:---:|
| `oauth-codex` | ChatGPT subscription (Plus/Team/Enterprise) | Included in subscription | Yes |
| `codex` | Codex CLI installed locally | Free (uses your Codex session) | Yes |
| `ollama` | Local install, no account needed | Free | Depends on model |
| `openai` | API key (`OPENAI_API_KEY`) | Pay-per-token | Yes |
| `custom` | Any OpenAI-compatible endpoint | Varies | Varies |

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

**No manual setup required.** When you create a `Company`, dartlab automatically downloads the required data. DART data comes from [GitHub Releases](https://github.com/eddmpython/dartlab/releases), EDGAR data from the SEC API.

| Dataset | Coverage | Status | Source |
|---------|----------|--------|--------|
| DART docs | 320+ companies | Actively collecting | [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-docs) |
| DART finance | 2,700+ companies | Complete | [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-finance-1) (4 shards) |
| DART report | 2,700+ companies | Complete | [GitHub Releases](https://github.com/eddmpython/dartlab/releases/tag/data-report-1) (4 shards) |
| EDGAR docs | On-demand | Auto-fetched | SEC 10-K/10-Q API |
| EDGAR finance | On-demand | Auto-fetched | SEC XBRL API |
| EDINET (Japan) | Researching | In development | EDINET API |

DART docs are pre-built on GitHub Releases for 320+ companies. If a company is not in the release, dartlab fetches individual disclosure sections from DART — this can be **very slow**. EDGAR data is fetched in real-time from the SEC API on first `Company` creation, which may take a moment due to rate limits. See [Installation — Data](https://eddmpython.github.io/dartlab/docs/getting-started/installation#data) for pre-download options.

## Try It Now

### Marimo Notebooks

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
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/06_insight_anomaly.ipynb) | **Insight & Anomaly** — 7-area grading, 6 anomaly rules |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/07_network_governance.ipynb) | **Network & Governance** — corporate relationship graph |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/08_signal_trend.ipynb) | **Signal Trends** — 48-keyword disclosure monitoring |
| [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/showcase/09_ai_analysis.ipynb) | **AI Analysis** — `dartlab.ask()` with 7 LLM providers |
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
| **Beta** | EDGAR power-user (SCE, notes, cadence, coverage), insights, distress, ratios, timeseries, network, governance, workforce, capital, debt, chart/table/text tools, ask/chat, OpenDart, OpenEdgar, Server API, MCP, CLI subcommands |
| **Experimental** | AI tool calling, export |
| **Alpha** | Desktop App (Windows .exe) — functional but incomplete, Sections Viewer — not yet fully structured |

See [docs/stability.md](docs/stability.md).

## Contributing

The project prefers experiments before engine changes. If you want to propose a parser or mapping change, validate it first and then bring the result back into the engine.

## License

MIT
