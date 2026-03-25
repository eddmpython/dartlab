"""HuggingFace 데이터셋 README 업로드."""

import os
from huggingface_hub import HfApi

token = None
for line in open(".env", encoding="utf-8"):
    line = line.strip()
    if line.startswith("HF_TOKEN="):
        token = line.split("=", 1)[1].strip()
        break

README = r"""---
license: mit
task_categories:
  - table-question-answering
  - text-classification
language:
  - ko
  - en
tags:
  - finance
  - disclosure
  - dart
  - edgar
  - sec
  - xbrl
  - korea
  - financial-statements
  - corporate-filings
  - 전자공시
  - 재무제표
  - 사업보고서
  - 한국
pretty_name: DartLab 전자공시 데이터
size_categories:
  - 1K<n<10K
---

<div align="center">

<br>

<img alt="DartLab" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/logo.png" width="160">

<h3>DartLab Data</h3>

<p><b>Structured company data from DART & EDGAR disclosure filings</b></p>
<p>DART 전자공시 + EDGAR 공시 데이터 — 한국 2,700사 / 미국 970사</p>

<p>
<a href="https://github.com/eddmpython/dartlab"><img src="https://img.shields.io/badge/GitHub-dartlab-ea4647?style=for-the-badge&labelColor=050811&logo=github&logoColor=white" alt="GitHub"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://eddmpython.github.io/dartlab/"><img src="https://img.shields.io/badge/Docs-GitHub_Pages-38bdf8?style=for-the-badge&labelColor=050811&logo=github-pages&logoColor=white" alt="Docs"></a>
<a href="https://buymeacoffee.com/eddmpython"><img src="https://img.shields.io/badge/Sponsor-Buy_Me_A_Coffee-ffdd00?style=for-the-badge&labelColor=050811&logo=buy-me-a-coffee&logoColor=white" alt="Sponsor"></a>
</p>

</div>

## What is this?

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-study.png" width="120">

Pre-collected [Parquet](https://parquet.apache.org/) files from [DartLab](https://github.com/eddmpython/dartlab) — a Python library that turns DART (Korea) and EDGAR (US) disclosure filings into one structured company map.

한국 DART 전자공시 시스템과 미국 SEC EDGAR에서 수집한 기업 공시 데이터입니다.

This dataset is the **data layer** behind DartLab. When you run `dartlab.Company("005930")`, the library automatically downloads the relevant parquet from this repo.

## Dataset Structure

```
dart/
├── docs/          2,547 companies  ~8 GB      disclosure text (sections, tables, markdown)
├── finance/       2,744 companies  ~586 MB    financial statements (BS, IS, CF, XBRL)
└── report/        2,711 companies  ~319 MB    structured disclosure APIs (28 types)
```

Each file is one company: `{stockCode}.parquet`

### docs — Disclosure Text

Full-text sections from annual/quarterly reports, parsed into structured blocks.

| Column | Description |
|--------|------------|
| `rcept_no` | DART filing ID |
| `rcept_date` | Filing date |
| `stock_code` | Stock code |
| `corp_name` | Company name |
| `report_type` | Annual/quarterly report type |
| `section_title` | Original section title |
| `section_order` | Section ordering |
| `content` | Section text (markdown) |
| `blockType` | `text` / `table` / `heading` |
| `year` | Filing year |

### finance — Financial Statements

XBRL-based financial data from DART OpenAPI (`fnlttSinglAcntAll`).

| Column | Description |
|--------|------------|
| `bsns_year` | Business year |
| `reprt_code` | Report quarter code |
| `stock_code` | Stock code |
| `corp_name` | Company name |
| `fs_div` | `CFS` (consolidated) / `OFS` (separate) |
| `sj_div` | Statement type (BS/IS/CF/SCE) |
| `account_id` | XBRL account ID |
| `account_nm` | Account name (Korean) |
| `thstrm_amount` | Current period amount |
| `frmtrm_amount` | Prior period amount |
| `bfefrmtrm_amount` | Two periods prior amount |

### report — Structured Disclosure APIs

28 DART API categories covering governance, compensation, shareholding, and more.

| Column | Description |
|--------|------------|
| `apiType` | API category (e.g., `dividend`, `employee`, `executive`) |
| `year` | Year |
| `quarter` | Quarter |
| `stockCode` | Stock code |
| `corpCode` | DART corp code |
| *(varies)* | Category-specific columns |

**28 API types:** dividend, employee, executive, majorHolder, treasuryStock, capitalChange, auditOpinion, stockTotal, outsideDirector, corporateBond, and more.

## Usage

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-analyze.png" width="120">

### With DartLab (recommended)

```bash
pip install dartlab
```

```python
import dartlab

c = dartlab.Company("005930")   # Samsung Electronics
c.sections                      # full company map (topic x period)
c.BS                            # balance sheet
c.ratios                        # financial ratios
c.show("businessOverview")      # narrative text

# US companies work the same way
us = dartlab.Company("AAPL")
us.BS
us.ratios
```

DartLab auto-downloads from this dataset. No manual download needed.

### Direct download

```python
import polars as pl

# Single file
url = "https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/dart/finance/005930.parquet"
df = pl.read_parquet(url)
```

```bash
# wget
wget https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/dart/finance/005930.parquet
```

<img align="right" src="https://huggingface.co/datasets/eddmpython/dartlab-data/resolve/main/assets/avatar-discover.png" width="120">

## Data Source

- **DART** (Korea): [dart.fss.or.kr](https://dart.fss.or.kr) — Korea's electronic disclosure system operated by the Financial Supervisory Service
- **EDGAR** (US): [sec.gov/edgar](https://www.sec.gov/edgar) — SEC's Electronic Data Gathering, Analysis, and Retrieval system

All data is sourced from public government disclosure systems. Financial figures are preserved as-is from the original filings — no rounding, no estimation, no interpolation.

## Update Schedule

This dataset is updated automatically via GitHub Actions (daily). Recent filings (last 7 days) are checked and collected incrementally.

## License

MIT — same as [DartLab](https://github.com/eddmpython/dartlab).

## Support

If DartLab is useful for your work, consider supporting the project:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy_Me_A_Coffee-Support-ffdd00?style=for-the-badge&labelColor=050811&logo=buy-me-a-coffee&logoColor=white)](https://buymeacoffee.com/eddmpython)

- [GitHub Issues](https://github.com/eddmpython/dartlab/issues) — bug reports, feature requests
- [Blog](https://eddmpython.github.io/dartlab/blog/) — 120+ articles on Korean disclosure analysis
"""

api = HfApi(token=token)
api.upload_file(
    repo_id="eddmpython/dartlab-data",
    repo_type="dataset",
    path_or_fileobj=README.encode("utf-8"),
    path_in_repo="README.md",
    commit_message="fix center alignment with HTML tags",
)
print("README.md 업로드 완료")
