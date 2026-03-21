# startMarimo

Interactive [Marimo](https://marimo.io/) notebooks for exploring `dartlab.Company` — no code to write, just run and interact.

## Examples

- **dartCompany.py** — Korean listed company (DART)
- **edgarCompany.py** — US listed company (EDGAR)
- **aiAnalysis.py** — AI-powered company analysis (LLM-based)

### dartCompany.py

Full DART company exploration — sections, financial statements, analysis engines, and more.

- `dartlab.Company("005930")` — Samsung Electronics
- `c.sections` — full topic × period map
- `c.topics` — topic list
- `c.show("overview")` — open a topic
- `c.show("IS")` — financial time series
- `c.BS`, `c.CF`, `c.ratios` — financial data shortcuts
- `c.show("IS", period=["2024Q4", "2023Q4"])` — period comparison
- `c.show("dividend")` — report data
- `c.trace("stock")` — data source provenance
- `c.diff()` — text change detection
- `c.notes.inventory` — K-IFRS notes (12 items)
- `c.sector`, `c.insights`, `c.rank` — analysis engines
- `c.network("members")` — affiliate network
- `c.governance()` — governance analysis
- `c.table("employee")` — structured table parsing
- `c.filings()` — filing list
- `dartlab.chart.revenue(c)` — plotly charts

### edgarCompany.py

US company exploration — 10-K/10-Q sections, XBRL financials, analysis engines.

- `dartlab.Company("AAPL")` — Apple
- `c.sections` — full topic × period map
- `c.show("riskFactors")` — 10-K narrative sections
- `c.show("IS")` — financial time series
- `c.BS`, `c.IS`, `c.CF`, `c.ratios` — financial data
- `c.trace("riskFactors")` — data source provenance
- `c.diff()` — text change detection
- `c.sector`, `c.insights` — analysis engines
- `c.filings()` — SEC filing list

### aiAnalysis.py

LLM-powered company analysis with multiple providers and analysis patterns.

- `dartlab.ask("삼성전자 분석해줘")` — one-stop AI analysis
- `dartlab.ask(..., pattern="valuation")` — analysis framework: `financial`, `risk`, `valuation`, `dividend`
- `c.ask("배당 정책을 분석해줘")` — ask directly on a Company
- Streaming: `stream=True` (default) returns a generator
- Provider selection: `provider="ollama"`, `provider="openai"`, `provider="claude"`
- Data filtering: `include=["BS", "IS"]`, `exclude=["dividend"]`
- **Prerequisite**: run `dartlab setup` to configure a provider

## Running

Install Marimo if you haven't:

```bash
uv add marimo
```

Open an example:

```bash
uv run marimo edit startMarimo/dartCompany.py
uv run marimo edit startMarimo/edgarCompany.py
uv run marimo edit startMarimo/aiAnalysis.py
```

Add your own `.py` files to the same folder and open them the same way.
