---
title: "Sections — Company Map"
---

# Sections — Company Map

In DartLab, `sections` is the entire map of a company. It takes disclosure documents filed each reporting period, splits them by topic, and aligns them side by side across time into a single horizontalized board. Instead of opening individual annual reports one at a time, you can compare every disclosure section chronologically at a glance.

## What is sections

Korean DART annual reports contain dozens of sections — from Chapter I (Company Overview) to Chapter XII (Detailed Schedules). The problem is that each report exists as a separate file per quarter/year. The same topic ("Business Overview") is scattered across 2025, 2024, 2024Q3, and so on.

`sections` restructures these scattered originals into a **topic × period matrix**. Each row is one topic-block, and each column is a period. Text and tables are preserved as-is from the original, just aligned on the time axis.

```python
import dartlab

c = dartlab.Company("005930")  # Samsung Electronics
c.sections
```

The returned DataFrame looks like this:

```
chapter │ topic            │ blockType │ textNodeType │ 2025Q4 │ 2024Q4 │ 2024Q3 │ …
I       │ companyOverview  │ text      │ heading      │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ text      │ body         │ "…"    │ "…"    │ "…"    │
I       │ companyOverview  │ table     │ null         │ "…"    │ "…"    │ null   │
II      │ businessOverview │ text      │ heading      │ "…"    │ "…"    │ "…"    │
```

## Key Columns

### Structure Columns

| Column | Description |
|---|---|
| `chapter` | Top-level chapter number. I through XII matching the annual report structure |
| `topic` | Standardized topic identifier. snakeCase names like `companyOverview`, `businessOverview`, `BS`, `IS`, `CF` |
| `blockType` | `"text"` or `"table"`. Distinguishes narrative blocks from table blocks within the same topic |
| `blockOrder` | Block order within a topic. Preserves the original document sequence |
| `textNodeType` | Sub-type for text blocks: `"heading"` (section title) or `"body"` (narrative text). null for tables |
| `textLevel` | Heading depth level (1, 2, 3, ...). null for body and table blocks |
| `textPath` | Structural path of the heading. Indicates position within the section |

### Period Columns

Columns like `2025Q4`, `2024Q4`, `2024Q3`, `2024Q2`, `2024Q1`, ... follow in order. Newest period comes first. Annual reports are labeled as Q4.

- Each cell contains the original payload for that period
- Text blocks contain narrative text; table blocks contain markdown tables
- `null` means no data exists for that period

## show(topic) — Open a Topic

After exploring `sections`, use `show()` when you want to dive deeper into a specific topic.

```python
c.show("companyOverview")       # block index DataFrame (block, type, source, preview)
c.show("companyOverview", 0)    # actual data for block 0
c.show("BS")                    # balance sheet (finance source)
```

`show()` always operates on top of `sections`, with source priority:

1. **finance** (BS, IS, CF, CIS, SCE) — numbers are authoritative, so they override docs text
2. **report** — DART structured disclosure data
3. **docs** — original narrative text/tables

Finance topics return normalized numeric DataFrames from the finance engine. Narrative topics return the original text aligned by period.

## trace(topic) — Check Source

To see which source was actually selected, use `trace()`.

```python
c.trace("BS")               # finance source, per-period coverage
c.trace("companyOverview")  # docs source
```

The result includes:

- Selected source (docs / finance / report)
- Per-period data availability (coverage)
- Metadata like chapter, label

## Filtering sections

`sections` is a Polars DataFrame, so you can filter freely with Polars syntax.

```python
import polars as pl

# specific topic only
df = c.sections.filter(pl.col("topic") == "companyOverview")

# text blocks only
df = c.sections.filter(pl.col("blockType") == "text")

# table blocks only
df = c.sections.filter(pl.col("blockType") == "table")
```

`sections` also provides convenience methods:

```python
c.sections.periods()    # list of periods
c.sections.ordered()    # sorted newest first
c.sections.coverage()   # per-topic period coverage summary
```

## docs.sections vs sections

Currently `c.sections` and `c.docs.sections` are identical. Both point to the pure docs source view.

```python
c.sections              # shortcut
c.docs.sections         # explicit path (same result)
```

`show(topic)` applies source priority (finance > report > docs) to return a merged result, so for practical use, just use `show()`.

## Same for EDGAR

US SEC EDGAR companies use the same structure and same API.

```python
us = dartlab.Company("AAPL")
us.sections
us.show("10-K::item1Business")
us.show("BS")
```

Only the topic names differ, following SEC form conventions. 10-K Item 1 is `10-K::item1Business`, Item 7 is `10-K::item7MDA`, and so on. Financial statement topics (BS, IS, CF) use the same names as DART.

## Next Steps

- [Quick Start](./quickstart) — From Company creation to show() in one go
- [API Overview](../api/overview) — Full API reference
- [Disclosure Text Tutorial](../tutorials/06_disclosure) — Working with narrative disclosure data
- [EDGAR Tutorial](../tutorials/09_edgar) — US company analysis
