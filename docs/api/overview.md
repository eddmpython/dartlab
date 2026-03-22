---
title: API Overview
---

# API Overview

DartLab's current public Company flow is `sections -> show(topic) -> trace(topic)`.

The core idea is not a list of parsers but a company map. First look at the company structure with `sections`, open the topic you need, and finally check whether the value came from `docs`, `finance`, or `report`.

## Creating a Company

```python
import dartlab

# DART
c = dartlab.Company("005930")
c = dartlab.Company("삼성전자")

# EDGAR
us = dartlab.Company("AAPL")
```

## Current Public Surface

```python
c.sections
c.show("BS")
c.trace("overview")
```

- `c.sections`: The public company board
- `c.show(topic)`: Returns the topic payload
- `c.trace(topic)`: Returns the source provenance

## sections

`sections` is the canonical map of a company. It is a Polars DataFrame where each row is a disclosure block and period columns hold the original text.

```python
c.sections                  # topic x period matrix
c.sections.periods()        # Available period list
c.sections.ordered()        # Ordered newest-first
c.topics                    # topic summary DataFrame (source, blocks, periods)
```

Key columns:

| Column | Description |
|--------|-------------|
| `chapter` | Major classification (I~XII) |
| `topic` | Standardized topic snakeId |
| `blockType` | "text" or "table" |
| `blockOrder` | Order within topic |
| `textNodeType` | Text block subtype: "heading" or "body" |
| `textLevel` | Heading depth level |
| `textPath` | Heading structural path |
| Period columns | `2025Q4`, `2024Q4`, `2024Q3`, etc. — original text payload |

The intent of this board is:

- View a disclosure not as a vertical document but as a company map over a period axis
- Compare the same topic across multiple periods at a glance
- Share the same structure between AI, GUI, and Python

Use `c.docs.sections` when you need the pure docs source.

See the [Sections Guide](../getting-started/sections) for detailed structure.

## show(topic)

```python
c.show("BS")
c.show("overview")
c.show("audit")

us.show("BS")
us.show("10-K::item1Business")
```

`show(topic)` opens a single topic.

The approximate source priority is:

- Financial figures: `finance`
- Structured disclosures: `report`
- Narrative / sections / original structure: `docs`

In other words, `Company` is not a raw source wrapper but a source-aware merged company object.

## trace(topic)

```python
c.trace("BS")
c.trace("dividend")
c.trace("overview")
```

`trace(topic)` explains which source was actually selected for the same topic.

Typical information checked here:

- Selected source
- Provenance
- Whether fallback was used
- Period coverage

## diff()

`diff()` detects text changes between periods.

```python
c.diff()                                # Change rate by topic
c.diff("businessOverview")              # Change history by period
c.diff("businessOverview", "2023", "2024")  # Line-by-line comparison
```

Years with high change rates may indicate business structure changes, new business entries, or additional risk factors.

## Source Namespace

When you need to go deeper, use the source namespace directly.

```python
# DART
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices
c.finance.BS
c.report.audit

# EDGAR
us.docs.sections
us.finance.BS
```

## OpenAPI

Separate from `Company`, public API wrappers are also provided.

```python
from dartlab import OpenDart, OpenEdgar

d = OpenDart()
e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

The principle is:

- External interfaces are source-native
- Storage format is compatible with DartLab runtime
- The derived `Company` layer is a separate responsibility

## MCP Server

DartLab includes a built-in MCP server that exposes 60 tools for Claude Desktop, Claude Code, and Cursor.

```bash
dartlab mcp              # start MCP server (stdio)
dartlab mcp --config claude-desktop   # show config for Claude Desktop
```

See the [MCP Guide](mcp) for setup instructions and the full tool list.

## Stability

- DART core `Company` is centered on stable
- EDGAR is at a lower stability tier

See [Stability Guide](../stability) for detailed criteria.
