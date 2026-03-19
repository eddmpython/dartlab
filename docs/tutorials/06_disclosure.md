---
title: "6. Disclosure Text"
---

# 6. Disclosure Text — Reading Narrative Disclosures with sections

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/06_disclosure.ipynb)

Read the text hidden behind the numbers. DartLab horizontalizes all disclosure text into `sections`. Every section of an annual report is organized into a topic × period matrix, so you can compare any subject side by side across periods.

---

## Setup

```python
import dartlab
import polars as pl

c = dartlab.Company("005930")
```

---

## Viewing the Full Structure with sections

```python
c.sections
```

`sections` is the complete disclosure map of a company. All sections are horizontalized into a topic × period matrix. The `blockType` column distinguishes text from tables, and `blockOrder` preserves the original order.

```
│ chapter │ topic            │ blockType │ blockOrder │ 2024   │ 2023   │ ...
│ I       │ companyOverview  │ text      │ 0          │ 서술문 │ 서술문 │
│ I       │ companyOverview  │ table     │ 1          │ 테이블 │ 테이블 │
│ II      │ businessOverview │ text      │ 0          │ 서술문 │ 서술문 │
```

---

## Checking the Topic List

```python
c.topics
```

Key topic examples:

| topic | Description |
|-------|-------------|
| `companyOverview` | Company overview |
| `businessOverview` | Business description |
| `riskFactors` | Risk management |
| `mdna` | Management discussion & analysis |
| `salesOrder` | Sales and orders |
| `rawMaterial` | Raw materials |
| `segments` | Business segments |
| `companyHistory` | Company history |

Available topics vary by company. Use `c.topics` to check the full list for a given stock.

---

## Opening a Topic with show()

`show()` extracts the relevant topic from sections and presents it block by block.

```python
# Block index — see what blocks are available
c.show("businessOverview")
```

After checking the block numbers in the index, retrieve the desired block.

```python
# Block 0: Text DataFrame (original text by period)
c.show("businessOverview", 0)

# Block 1: Table DataFrame (items × periods matrix)
c.show("businessOverview", 1)
```

Text blocks display original text columns side by side for each period, and table blocks return a horizontalized DataFrame in an items × periods format.

---

## Filtering sections with Polars

Since sections is a Polars DataFrame, you can filter it freely.

```python
# Text blocks only for a specific topic
text_rows = c.sections.filter(
    (pl.col("topic") == "businessOverview") & (pl.col("blockType") == "text")
)

# Table blocks only for a specific topic
table_rows = c.sections.filter(
    (pl.col("topic") == "businessOverview") & (pl.col("blockType") == "table")
)

# Reading original text for a specific period
row = c.sections.filter(
    (pl.col("topic") == "companyOverview") & (pl.col("blockType") == "text")
)
print(row["2024"][0])  # 2024 text
```

---

## Exploring by Period

```python
# List of available periods
c.sections.periods()

# Sorted newest first
c.sections.ordered()
```

`periods()` returns the full list of periods available for the company. `ordered()` reorders the columns so the most recent period comes first.

---

## Detecting Changes with diff()

Track text changes between two periods. Quickly identify which years saw significant changes in disclosure text.

```python
# Change rate summary by topic
c.diff()

# Period-by-period change history for a specific topic
c.diff("businessOverview")

# Detailed line-by-line comparison between two periods
c.diff("businessOverview", "2023", "2024")
```

> Years with high change rates may indicate business restructuring, new business ventures, or added risk factors. An efficient analysis workflow is to first identify change points with `diff()`, then read the original text for that period with `show()`.

---

## Going Deeper with the source Namespace

`c.sections` is a merged view. To access the raw data at a deeper level, use the `c.docs` namespace.

```python
# Pure docs source view (before finance/report merge)
c.docs.sections

# Original block retrieval (for search and AI)
c.docs.retrievalBlocks

# LLM context slice
c.docs.contextSlices

# K-IFRS notes
c.docs.notes
```

---

## Practical Example: Tracking Risk Factor Changes

Risk factors are updated every year, so tracking changes helps you quickly spot new risks.

```python
# Risk factors block index
c.show("riskFactors")

# Open text block
c.show("riskFactors", 0)

# Check change rates by year
c.diff("riskFactors")

# Detailed comparison 2023→2024
c.diff("riskFactors", "2023", "2024")
```

---

## Source Tracking

Check where the data for a topic originated.

```python
c.trace("businessOverview")
```

`trace()` returns metadata such as the source (docs/finance/report), number of periods, and whether text or tables are present for that topic.

---

## Next Steps

- [Sections Guide](../getting-started/sections) — Detailed sections structure
- [7. Advanced Analysis](./advanced) — K-IFRS notes, tangible assets, affiliates
- [8. Cross-Company Comparison](./cross-company) — Sector, insight, ranking
