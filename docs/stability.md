---
title: API Stability Policy
description: dartlab API stability tiers and change policy
---

# API Stability Policy

dartlab is currently **stable for DART core**. This document defines API stability tiers and compatibility policies for changes.

## Tier Classification

### Tier 1: Stable

Changes include a deprecation period with a migration guide.

| API | Description |
|-----|-------------|
| `dartlab.Company(code)` | Company object creation facade |
| `Company.sections` | Canonical company map (topic × period Polars DataFrame) |
| `Company.show()` | Topic payload query (source-aware) |
| `Company.trace()` | Source provenance query |
| `Company.diff()` | Cross-period text change detection |
| `Company.topics` | Available topic list |
| `Company.docs` | Docs source namespace |
| `Company.finance` | Financial statement time-series and statement namespace |
| `Company.report` | Structured disclosure namespace (28 API types) |
| `dartlab.search()` | Company search |
| `dartlab.listing()` | Full listed company directory |
| `Company.IS/BS/CF` | Authoritative statement shortcuts |
| `Company.CIS` | Comprehensive income statement shortcut |
| `Company.index` | Canonical topic × period board DataFrame |
| `Company.filings()` | Filing document list |
| `Company.profile` | Merged canonical company namespace |
| `dartlab` CLI entrypoint | Public CLI command entry point |

### Tier 2: Beta

May change after a warning. Recorded in CHANGELOG.

| API | Description |
|-----|-------------|
| `dartlab.Company("AAPL")` | EDGAR Company facade (US stocks) |
| `engines.edgar.docs` | EDGAR 10-K/10-Q/20-F sections horizontalization |
| `engines.edgar.docs.retrievalBlocks` | EDGAR block-level retrieval for LLM |
| `engines.edgar.docs.contextSlices` | EDGAR context slicing for LLM windows |
| `engines.edgar.finance` | SEC XBRL financial statements |
| `engines.edgar.finance.SCE` | Statement of Changes in Equity (BS delta + CF) |
| `engines.edgar.finance.explore()` | XBRL Fact Explorer (tag-level history) |
| `engines.edgar.finance.listTags()` | XBRL tag inventory |
| `engines.edgar.docs.notes()` | XBRL TextBlock note extraction |
| `engines.edgar.docs.cadence()` | Topic × period distribution matrix |
| `engines.edgar.docs.coverage()` | Topic coverage summary |
| `engines.edgar.profile` | EDGAR docs + finance merge layer |
| `Company.insights` | Insight grading (7 areas) |
| `Company.insights.distress` | Distress prediction scorecard (4-axis, credit grade, cash runway) |
| `Company.rank` | Market size ranking |
| `Company.docs.retrievalBlocks` | Original block retrieval |
| `Company.docs.contextSlices` | LLM/context slice view |
| `Company.ask()` | LLM-based analysis |
| `dartlab` subcommands/options | `ask`, `status`, `setup`, `ai`, `excel` command UX |
| Server API `/api/*` | Web server endpoints |
| `engines.ai.*` | AI/LLM engines |
| `Company.SCE` | Statement of changes in equity (DART) |
| `Company.sceMatrix` | SCE matrix view (DART) |
| `Company.timeseries` | Quarterly standalone time-series |
| `Company.annual` | Annual time-series |
| `Company.ratios` | Financial ratio calculation |
| `Company.ratioSeries` | Ratio time-series |
| `Company.network()` | Affiliate network graph |
| `Company.governance()` | Corporate governance data |
| `Company.workforce()` | Workforce data |
| `Company.capital()` | Capital structure |
| `Company.debt()` | Debt details |
| `Company.table()` | Inline table extraction |
| `dartlab.chart` | Chart tool module |
| `dartlab.table` | Table tool module |
| `dartlab.text` | Text tool module |
| MCP server | MCP protocol server (60 tools, stdio) |
| `dartlab mcp` | MCP CLI command |

### Tier 3: Experimental

Breaking changes are allowed. Not recommended for production use.

| API | Description |
|-----|-------------|
| `export.*` | Excel export |
| `engines.ai.tools.*` | LLM tool calling |

## Deprecation Policy

| Tier | Notice | Removal |
|------|--------|---------|
| Tier 1 | 2 minor versions ahead | Deprecated warning → removed in next minor |
| Tier 2 | 1 minor version ahead | Changed after CHANGELOG entry |
| Tier 3 | Immediate | CHANGELOG entry only |

Deprecation warning example:

```python
import warnings
warnings.warn(
    "Company.oldMethod() will be removed in v0.5.0. "
    "Use Company.newMethod() instead.",
    DeprecationWarning,
    stacklevel=2,
)
```

## Stability Criteria

DART core stable criteria:

- [ ] CI test coverage 80%+ (core engines)
- [ ] API Tier 1 tests 100% passing
- [ ] sections raw residual 0 maintained (representative company set)
- [ ] BS identity check 95%+ passing
- [ ] No Tier 1 breaking changes for 3 months
- [ ] Stable PyPI download growth trend
- [ ] External user feedback converged (2+ cases)

## Version Policy

- **semver compliant**: major = breaking, minor = feature, patch = bugfix
- DART core stable scope prioritizes compatibility within minor versions
- EDGAR and some AI features may change faster per their tier policy
- `Company.profile` is a merge layer on top of docs spine, used internally. `c.sections` and `c.show()` are the official consumption paths

## CLI Compatibility Rules

- Top-level `dartlab` entrypoint is treated as Tier 1.
- Public subcommand and major option changes require at least 1 minor version of deprecated warning.
- Exit codes are treated as contracts: `0` success, `1` runtime error, `2` usage error, `130` user interrupt.
- Deprecated aliases may be hidden from help but must remain executable until removal.

## EDGAR Topic Naming Convention

EDGAR topics use `{formType}::{itemId}` format:

- `10-K::item1Business` — Business description
- `10-K::item1ARiskFactors` — Risk factors
- `10-K::item7Mdna` — Management Discussion & Analysis

Short aliases also work: `business`, `risk`, `mdna`, `governance`

## DART / EDGAR Namespace Differences

> EDGAR now has accessor separation (_DocsAccessor, _FinanceAccessor,
> _ProfileAccessor), retrievalBlocks, contextSlices, and server API
> support — matching the DART architecture for core functionality.
>
> DART `docs` namespace includes additional sections analysis methods
> (coverage, cadence, semanticRegistry, structureRegistry, etc.)
> not yet available for EDGAR. These are Tier 2 (Beta).
>
> DART has a `report` namespace (28 structured disclosure API types)
> that does not exist in EDGAR — this reflects the structural difference
> between DART and SEC filing systems.
