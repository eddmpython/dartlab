<div align="center">

<br>

<img alt="DartLab" src=".github/assets/logo.png" width="180">

<h3>DartLab</h3>

<p><b>One company map from disclosure sections</b></p>

<p>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/v/dartlab?style=for-the-badge&color=ea4647&labelColor=050811&logo=pypi&logoColor=white" alt="PyPI"></a>
<a href="https://pypi.org/project/dartlab/"><img src="https://img.shields.io/pypi/pyversions/dartlab?style=for-the-badge&color=c83232&labelColor=050811&logo=python&logoColor=white" alt="Python"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-94a3b8?style=for-the-badge&labelColor=050811" alt="License"></a>
<a href="https://github.com/eddmpython/dartlab/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/eddmpython/dartlab/ci.yml?branch=master&style=for-the-badge&labelColor=050811&logo=github&logoColor=white&label=CI" alt="CI"></a>
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

## What DartLab Is

DartLab turns corporate filings into a single company map.

The center of that map is `sections`: a horizontalized board built from disclosure sections across periods. Instead of treating a filing as a pile of unrelated parsers, DartLab aligns the document structure first, then lets stronger sources fill in what they own:

- `docs` for section structure, narrative text, detail blocks, and evidence
- `finance` for authoritative numeric statements
- `report` for authoritative structured disclosure APIs
- `profile` for the merged company layer built on top of the same spine

The public workflow is now simple:

```python
import dartlab

c = dartlab.Company("005930")

c.sections
c.show("companyOverview")
c.trace("BS")
```

## Why It Changed

Older disclosure tooling often grew into a property zoo: many parsers, many entrypoints, and weak structural consistency.

DartLab is moving away from that. The current design goal is:

- one `Company`
- one canonical `sections` map
- one source-aware `show` / `trace` workflow
- one shared structure that Python, docs, and the upcoming AI GUI can all consume

This is where most of the recent quality and performance work went.

## Install

```bash
uv add dartlab
```

AI interface:

```bash
uv add "dartlab[ai]"
uv run dartlab ai
```

## Quick Start

```python
import dartlab

# KR: DART
c = dartlab.Company("005930")

c.sections                  # canonical company map
c.show("BS")                # one topic payload
c.show("companyOverview")   # sections-based disclosure payload
c.trace("BS")               # chosen source + provenance

# US: EDGAR
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
```

The key distinction is:

- `c.sections`: the public company board
- `c.docs.sections`: the pure docs source view
- `c.trace(...)`: why a topic came from `docs`, `finance`, or `report`

## OpenAPI

Use the source-native wrappers when you want raw public APIs directly.

```python
from dartlab import OpenDart, OpenEdgar

d = OpenDart()
e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

These wrappers keep the original source surface as intact as possible, while saved parquet stays compatible with DartLab's `Company` engine.

## Core Ideas

### 1. Sections First

`sections` is the backbone. A company is no longer documented as a loose set of outputs; it is described as one horizontalized map of disclosure units across periods.

### 2. Source-Aware Company

`Company` is not a raw source wrapper. It is a merged company object that knows when `finance` or `report` should override docs.

### 3. AI-Ready Structure

The same `sections -> show -> trace` contract is what the upcoming AI GUI will consume. The goal is not a different AI-only schema, but the same company map exposed through a different interface.

### 4. Raw Access Still Exists

You can still go deeper when needed:

```python
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices
c.finance.BS
c.report.audit
```

## Stability

- DART core `Company` flow is the stable center
- EDGAR is improving quickly, but still a lower stability tier
- Public messaging now favors `sections -> show -> trace`
See [docs/stability.md](docs/stability.md).

## Documentation

- Docs: https://eddmpython.github.io/dartlab/
- Quick start: https://eddmpython.github.io/dartlab/docs/getting-started/quickstart
- API overview: https://eddmpython.github.io/dartlab/docs/api/overview
- Blog: https://eddmpython.github.io/dartlab/blog/

## Data

DartLab uses centralized release config for downloadable datasets and keeps source-specific storage formats compatible with the runtime loaders.

Current public releases include:

- DART docs
- DART finance
- DART report
- EDGAR docs
- EDGAR finance

## Contributing

The project prefers experiments before engine changes. If you want to propose a parser or mapping change, validate it first and then bring the result back into the engine.

## License

MIT
