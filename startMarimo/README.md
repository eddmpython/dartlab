# startMarimo

Interactive [Marimo](https://marimo.io/) notebooks for exploring `dartlab.Company` — no code to write, just run and interact.

## Examples

- **dartCompany.py** — Korean listed company (DART)
- **edgarCompany.py** — US listed company (EDGAR)
- **aiAnalysis.py** — AI-powered company analysis (LLM-based)

### dartCompany.py

- `dartlab.Company("005930")` — Samsung Electronics
- `c.sections` — full topic x period map
- `c.topics` — topic list
- `c.show("companyOverview")` — open a topic
- `c.show("IS")` — financial time series
- `c.trace("stockTotal")` — data source provenance
- `c.diff()` — text change detection

### edgarCompany.py

- `dartlab.Company("AAPL")` — Apple
- `c.sections` — full topic x period map
- `c.show("riskFactors")` — docs topic
- `c.show("IS")` — financial time series
- `c.ratios` — financial ratios
- `c.filings()` — filing list
- `c.trace("riskFactors")` — data source provenance

### aiAnalysis.py

- `dartlab.ask("삼성전자 분석해줘")` — one-stop AI analysis
- Provider selection: `provider="ollama"`, `provider="openai"`
- Streaming: enabled by default
- Data filtering: `include=["BS", "IS"]`, `exclude=["dividend"]`
- Analysis patterns: `pattern="financial"`, `pattern="risk"`
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
