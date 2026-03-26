# Marimo Notebooks

Interactive [Marimo](https://marimo.io/) notebooks for exploring DartLab's core features — no code to write, just run and interact.

## Notebooks

| Notebook | What it shows |
|----------|--------------|
| **dartCompany.py** | DART Company — sections, show, diff, finance, insights |
| **dartReview.py** | Analysis report — c.review() rich text + DataFrame |
| **edgarCompany.py** | EDGAR Company — US 10-K/10-Q, XBRL financials |
| **marketScan.py** | Market-wide scan — scanAccount, scanRatio (2,700+ companies) |
| **aiAnalysis.py** | AI analysis — ask, patterns, streaming |

### dartCompany.py

Full DART company exploration — sections, financial statements, analysis engines, and more.

- `dartlab.Company("005930")` — Samsung Electronics
- `c.sections` — full topic × period map
- `c.show("overview")` — open a topic
- `c.show("IS")` — financial time series
- `c.BS`, `c.CF`, `c.ratios` — financial data shortcuts
- `c.trace("stock")` — data source provenance
- `c.diff()` — text change detection

### dartReview.py

Corporate analysis report — rich text + DataFrame interleaved output.

- `c.review()` — full analysis report (all sections)
- `c.review("수익구조")` — single section only

### edgarCompany.py

US company exploration — 10-K/10-Q sections, XBRL financials.

- `dartlab.Company("AAPL")` — Apple
- `c.sections` — full topic × period map
- `c.show("riskFactors")` — 10-K narrative sections
- `c.show("IS")` — financial time series

### marketScan.py

Market-wide scanning — query a single account or ratio across all listed companies.

- `dartlab.scanAccount("매출액")` — revenue across 2,700+ companies
- `dartlab.scanRatio("roe")` — ROE across all companies
- `dartlab.scanRatioList()` — available ratio list

### aiAnalysis.py

LLM-powered company analysis with multiple providers.

- `dartlab.ask("삼성전자 분석해줘")` — auto-streams to stdout
- `dartlab.ask(..., pattern="valuation")` — analysis frameworks
- **Prerequisite**: run `dartlab setup` to configure a provider

## Running

```bash
uv add marimo
uv run marimo edit notebooks/marimo/dartCompany.py
```
