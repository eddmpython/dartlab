<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>Beyond the numbers</b> — Extract both financials and text from DART filings</p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
</p>

<p>
<a href="https://eddmpython.github.io/dartlab/">Docs</a> · <a href="README_KR.md">한국어</a> · <a href="https://buymeacoffee.com/eddmpython">Sponsor</a>
</p>

<p>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-docs"><img src="https://img.shields.io/badge/Docs-260%2B_Companies-f87171?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Docs Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-finance-1"><img src="https://img.shields.io/badge/Finance-2,700%2B_Companies-818cf8?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Finance Data"></a>
<a href="https://github.com/eddmpython/dartlab/releases/tag/data-report-1"><img src="https://img.shields.io/badge/Report-2,700%2B_Companies-34d399?style=for-the-badge&labelColor=050811&logo=databricks&logoColor=white" alt="Report Data"></a>
</p>

</div>

## What is DartLab?

DartLab is a Python library for parsing and analyzing [DART (Data Analysis, Retrieval and Transfer System)](https://dart.fss.or.kr/) — Korea's official electronic disclosure system. It extracts **both financial numbers and narrative text** from corporate filings.

### Account Standardization

Every listed company in Korea reports financials through XBRL, but each company uses **different account IDs and names** for the same economic concept. "Revenue" alone appears as dozens of variations across 2,700+ companies.

DartLab maintains its own **unified account schema** — built through a 7-stage mapping pipeline covering 34,000+ learned synonyms. The result: **98.7% of all financial statement rows** (15.8 million rows tested) across 2,700+ companies are successfully mapped to standardized accounts. This means you can directly compare Samsung Electronics' revenue with any other listed company using the same `revenue` key.

```
Raw XBRL (company-specific)          DartLab (standardized)
─────────────────────────────        ──────────────────────
ifrs-full_Revenue                 →  revenue
dart_OperatingIncomeLoss          →  operating_income
dart_ConstructionRevenue          →  revenue
ifrs_ProfitLoss                   →  net_income
매출액, 수익(매출액), 영업수익     →  revenue
```

### 40 Parsing Modules

One stock code is all you need. 40 modules extract structured DataFrames from disclosure filings — financial statements, notes, dividends, executives, governance, risk, and narrative text. All accessed through simple properties on a `Company` object, following the yfinance-style API.

## Installation

> **[uv](https://docs.astral.sh/uv/)** is required — a fast Python package manager written in Rust. It handles Python version management and virtual environments automatically.

```bash
# 1. Install uv (skip if already installed)
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create a project
uv init my-analysis && cd my-analysis

# 3. Install DartLab — pick the extras you need
uv add dartlab              # Core (financial statement parsing)
uv add dartlab[ai]          # + AI analysis web interface (dartlab ai)
uv add dartlab[llm]         # + OpenAI/Ollama LLM (CLI analysis)
uv add dartlab[charts]      # + Plotly charts
uv add dartlab[all]         # Everything

# 4. Verify
uv run python -c "from dartlab import Company; print(Company('005930').corpName)"
# → 삼성전자

# 5. Launch AI analysis (requires dartlab[ai])
uv run dartlab ai
# → http://localhost:8400
```

## Quick Start

```python
from dartlab import Company

c = Company("005930")       # by stock code
c = Company("삼성전자")      # by company name (Korean)
c.corpName                   # "삼성전자"
```

Creating a `Company` object prints a usage guide. For the full guide, call `c.guide()`.

Data is auto-downloaded from GitHub Releases when not found locally.

```python
from dartlab.core.dataLoader import downloadAll

downloadAll("docs")                        # 260+ companies — disclosure documents
downloadAll("finance")                     # 2,700+ companies — financial numbers
downloadAll("report")                      # 2,700+ companies — periodic reports
downloadAll("finance", forceUpdate=True)   # re-download if remote is newer
```

---

## Features

### Financial Statements

```python
c.BS    # Balance Sheet (DataFrame)
c.IS    # Income Statement (DataFrame)
c.CF    # Cash Flow Statement (DataFrame)
```

### Cross-Company Comparable Time Series

Every company's XBRL data is mapped through the unified account schema (98.7% coverage), then converted to **standalone quarterly time series**. Cumulative figures from semi-annual and annual reports are reverse-engineered into individual quarters.

```python
series, periods = c.timeseries
# periods = ["2016_Q1", "2016_Q2", ..., "2024_Q4"]
# series["IS"]["revenue"]            # quarterly revenue
# series["BS"]["total_assets"]       # quarterly total assets
# series["CF"]["operating_cashflow"] # quarterly operating cash flow

r = c.ratios
r.roe               # 8.29 (%)
r.operatingMargin   # 9.51 (%)
r.debtRatio         # 27.4 (%)
r.fcf               # Free Cash Flow (KRW)
```

2,700+ listed companies share the same snakeId schema. Compare any two companies directly — no manual mapping required.

### Summary Financials with Bridge Matching

Extracts summary financial time series, automatically tracking accounts even when names change due to K-IFRS revisions.

```python
result = c.fsSummary()

result.FS          # Full financial time series (Polars DataFrame)
result.BS          # Balance Sheet
result.IS          # Income Statement
result.allRate     # Overall match rate (e.g. 0.97)
result.breakpoints # List of detected breakpoints
```

### K-IFRS Notes (12 items)

```python
c.notes.inventory          # Inventories
c.notes["재고자산"]         # Korean key also works
c.notes.receivables        # Trade receivables
c.notes.tangibleAsset      # Property, plant & equipment
c.notes.intangibleAsset    # Intangible assets
c.notes.investmentProperty # Investment property
c.notes.affiliates         # Associates
c.notes.borrowings         # Borrowings
c.notes.provisions         # Provisions
c.notes.eps                # Earnings per share
c.notes.lease              # Leases
c.notes.segments           # Operating segments
c.notes.costByNature       # Expenses by nature
```

### Dividends

```python
c.dividend
# ┌──────┬───────────┬───────┬──────────────┬─────────────┬──────────────┬──────┐
# │ year ┆ netIncome ┆ eps   ┆ totalDividend┆ payoutRatio ┆ dividendYield┆ dps  │
# └──────┴───────────┴───────┴──────────────┴─────────────┴──────────────┴──────┘
```

### Major Shareholders

```python
c.majorHolder    # Largest shareholder + related parties ownership (time series)
```

For the full Result object: `c.get("majorHolder")`

```python
result = c.get("majorHolder")
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.timeSeries    # Ownership ratio time series
```

### Employees

```python
c.employee    # year, totalEmployees, avgSalary, avgTenure, ...
```

### Audit Opinion

```python
c.audit    # year, auditor, opinion, keyAuditMatters
```

### Executives

```python
c.executive      # year, totalRegistered, insideDirectors, outsideDirectors, ...
c.executivePay   # year, category, headcount, totalPay, avgPay
```

### Shares / Capital

```python
c.shareCapital     # Issued, treasury, outstanding shares
c.capitalChange    # Capital changes
c.fundraising      # Capital increases/decreases
```

### Subsidiaries / Associates

```python
c.subsidiary           # Investments in other corporations
c.affiliateGroup       # Affiliate group companies
c.investmentInOther    # Investee, ownership ratio, book value
```

### Board / Governance

```python
c.boardOfDirectors     # Board composition, attendance
c.shareholderMeeting   # Shareholder meeting agendas, resolutions
c.auditSystem          # Audit committee, audit activities
c.internalControl      # Internal control assessment
```

### Risk / Legal

```python
c.contingentLiability  # Contingent liabilities, lawsuits
c.relatedPartyTx       # Related party transactions
c.sanction             # Sanctions, penalties
c.riskDerivative       # FX sensitivity, derivatives
```

### Other Financials

```python
c.bond                 # Debt securities
c.rnd                  # R&D expenses
c.otherFinance         # Allowance for bad debt, etc.
c.productService       # Major products/services
c.salesOrder           # Sales performance, order backlog
c.articlesOfIncorporation  # Articles of incorporation amendments
```

### Company Info

```python
c.companyHistory         # Corporate history
c.companyOverviewDetail  # Incorporation date, listing date, CEO, address
```

### Disclosure Narratives

```python
c.business       # Business overview (sections + change detection)
c.overview       # Company overview (incorporation, address, credit rating)
c.mdna           # Management Discussion & Analysis
c.rawMaterial    # Raw materials, tangible assets, capex
```

### Raw Data Access

```python
c.rawDocs        # Original docs parquet (unprocessed)
c.rawFinance     # Original finance parquet (unprocessed)
c.rawReport      # Original periodic report parquet (unprocessed)
```

---

## AI Analysis (dartlab ai)

Chat with an LLM over DartLab's structured data to analyze companies interactively — `uv run dartlab ai` opens the web UI at `http://localhost:8400`.

All extracted data (financial statements, notes, dividends, executives, governance) is provided as context for natural-language Q&A with streaming responses.

> **Currently supported LLM: Ollama (local)**
>
> The current version supports **Ollama** for local LLM inference. No API key needed, and your data stays on your machine.
>
> - Install [Ollama](https://ollama.com/download), then `ollama pull gemma3` to download a model
> - Select and download models in the UI settings
> - GPU (NVIDIA/AMD) is auto-detected for acceleration
>
> **Coming soon**: Cloud LLM providers (OpenAI, Anthropic, etc.)

---

## Bulk Extraction

```python
d = c.all()    # All module data as dict (with progress bar)
# {"BS": df, "IS": df, "CF": df, "dividend": df, "notes": {...},
#  "timeseries": (series, periods), "ratios": RatioResult, ...}
```

```python
import dartlab
dartlab.verbose = False    # Suppress progress output

d = c.all()    # Silent extraction
```

---

## Result Object

Properties return the primary DataFrame. For the full Result object, use `c.get()`.

```python
# property — returns DataFrame directly
c.audit          # opinionDf (audit opinion DataFrame)

# get() — returns full Result object
result = c.get("audit")
result.opinionDf   # Audit opinion
result.feeDf       # Audit fees
```

---

## Company Search

```python
from dartlab import Company

Company.search("삼성")
# ┌──────────────┬──────────┬────────────────┐
# │ 회사명       ┆ 종목코드 ┆ 업종           │
# └──────────────┴──────────┴────────────────┘

Company.listing()   # Full KRX listed companies
Company.status()    # Local data index
c.docs()            # Filing list + DART viewer links
```

---

## Core Technology

### Horizontal Alignment of Filings

DART filings cover different periods depending on report type:

```
                           Q1         Q2         Q3         Q4
                          ┌──────┐
 Q1 Report                │  Q1  │
                          └──────┘
                          ┌──────────────┐
 Semi-Annual              │   Q1 + Q2    │
                          └──────────────┘
                          ┌─────────────────────┐
 Q3 Report                │    Q1 + Q2 + Q3     │
                          └─────────────────────┘
                          ┌──────────────────────────────┐
 Annual Report            │       Q1 + Q2 + Q3 + Q4      │
                          └──────────────────────────────┘
```

Q1 reports contain only Q1, semi-annual reports contain cumulative Q1+Q2, and annual reports contain the full year. DartLab reverse-engineers standalone quarterly figures from these cumulative structures, and tracks accounts even when names change between filings.

### Bridge Matching

K-IFRS revisions and internal restructuring frequently cause **account name changes within the same company**. Bridge Matching combines amount matching and name similarity across adjacent years to automatically link identical accounts.

```
             2022              2023              2024
             ──────            ──────            ──────
 매출액 ────────────── 매출액 ────────────── 수익(매출액)
                              ↑ name change              ↑ name change
 영업이익 ──────────── 영업이익 ──────────── 영업이익
 당기순이익 ────────── 당기순이익 ────────── 당기순이익(손실)
```

Four-stage matching process:

1. **Exact match** — identical amounts
2. **Restatement match** — within 0.5 tolerance
3. **Name change match** — amount error < 5% AND name similarity > 60%
4. **Special item match** — decimal-unit items like EPS

When match rate drops below 85%, a breakpoint is detected and the segment is split.

---

## Data

### Sources and Integrity

All data originates from **[OpenDART](https://opendart.fss.or.kr/)** and **[DART](https://dart.fss.or.kr/)**, Korea's official electronic disclosure system. The developer has **not modified a single number** — only metadata columns (stock code, year, report type, etc.) have been added for structural organization.

If you want to verify, you can cross-check any value against the original filings using the package's built-in DART viewer links (`c.docs()`).

Each Parquet file contains all filings for a single company:

- **Metadata**: stock code, company name, report type, filing date, business year
- **Quantitative**: summary financials, financial statement body, notes
- **Narrative**: business description, audit opinion, risk management, executive/shareholder status

### Data Releases

| Category | Release Tags | Description | Count |
|----------|-------------|-------------|-------|
| Disclosure | [`data-docs`](https://github.com/eddmpython/dartlab/releases/tag/data-docs) | Parsed annual report sections | 260+ |
| Finance | [`data-finance-1`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-1) [`2`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-2) [`3`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-3) [`4`](https://github.com/eddmpython/dartlab/releases/tag/data-finance-4) | XBRL financial statement numbers | 2,700+ |
| Report | [`data-report-1`](https://github.com/eddmpython/dartlab/releases/tag/data-report-1) [`2`](https://github.com/eddmpython/dartlab/releases/tag/data-report-2) [`3`](https://github.com/eddmpython/dartlab/releases/tag/data-report-3) [`4`](https://github.com/eddmpython/dartlab/releases/tag/data-report-4) | Periodic report data | 2,700+ |

Finance and Report data are split into 4 tags by stock code range (GitHub's 1000-asset-per-release limit). `loadData()` and `downloadAll()` handle this automatically.

### Bring Your Own Data

If you structure your own Parquet files to match DartLab's schema, all existing features work out of the box. Place files as `data/{category}/{stockCode}.parquet` and every property, extraction module, and analysis tool will function normally.

### Disclaimer

This project is licensed under MIT. While the data faithfully mirrors OpenDART public disclosures, **no guarantee of commercial reliability is provided**. Always verify against official sources for investment or compliance decisions.

> **Update frequency**
>
> Data is collected directly without paid proxies, so updates may be slow. Adding new companies or reflecting the latest filings may take time.

---

## Why DartLab?

DART filings contain far more than financial numbers — business descriptions, risk factors, audit opinions, litigation status, and governance changes are all embedded in the text. Most tools only extract the numbers. The rest is discarded.

DartLab extracts both. It aligns quarterly, semi-annual, and annual reports on a single time axis, and automatically tracks accounts even when K-IFRS revisions or restructuring changes their names.

> **Current scope**
>
> Bridge Matching tracks account name changes **within a single company** across years. The finance engine enables **cross-company comparison** by mapping XBRL accounts to standardized snakeIds. 2,700+ listed companies are normalized to the same structure.
>
> The insight engine grades each company across 7 areas (performance, profitability, financial health, cash flow, governance, risk), detects anomalies, and the rank engine computes market-wide size rankings.
>
> Text analysis capabilities are being developed in a **separate project** and will be integrated into DartLab.
>
> The ultimate goal is a tool that can analyze the **entire market** at once, not just one company.

## Roadmap

- [x] Summary financial time series (Bridge Matching)
- [x] Consolidated BS, IS, CF
- [x] Segment revenue, associates, dividends, employees, shareholders, subsidiaries
- [x] Debt securities, expenses by nature, raw materials/capex
- [x] Audit opinion, executive status, executive compensation
- [x] PPE movement, note details (23 keywords)
- [x] Board of directors, capital changes, contingent liabilities, related party tx, sanctions, R&D, internal control
- [x] Affiliate groups, capital raises, sales/orders, products, risk management/derivatives
- [x] MD&A, business description, company overview
- [x] Company property API + Notes integration + all()
- [x] Rich terminal output (avatar + usage guide)
- [x] Account standardization engine — 2,700+ companies cross-comparable
- [x] Quarterly time series + financial ratios (c.timeseries, c.ratios)
- [x] Periodic report data engine (dividend, employees, major holders, audit, executives)
- [x] Sector classification (WICS 11 sectors — KSIC + keyword + override)
- [x] Insight grading engine (7 areas: performance, profitability, health, cashflow, governance, risk + overall)
- [x] Anomaly detection (Z-score + domain rules across 30+ financial metrics)
- [x] Market-wide size ranking (revenue, assets, growth — total + within-sector)
- [x] AI analysis web interface (dartlab ai) — Ollama local LLM
- [ ] Cloud LLM providers (OpenAI, Anthropic, etc.)
- [ ] Text analysis module integration (from separate project)
- [ ] Quantitative + qualitative cross-validation
- [ ] Visualization

## Sponsor

<a href="https://buymeacoffee.com/eddmpython">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180"/>
</a>

## License

MIT License
