---
title: "1. Quickstart"
---

# 1. Quickstart

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/01_quickstart.ipynb)

DartLab's core analysis flow is `sections → show → trace`.

This tutorial covers:

- Creating a `Company`
- Viewing the company map with `sections`
- Opening payloads with `show("topic")`
- Checking sources with `trace("topic")`
- Direct access to source namespaces

---

## Creating a Company

```python
import dartlab

c = dartlab.Company("005930")
c.corpName
c.stockCode
```

You can also use a company name:

```python
c = dartlab.Company("카카오")
```

---

## Start with `sections`

```python
c.sections
```

`sections` is the company's canonical board. Columns are periods, rows are the topic structure aligned from disclosures.

For the pure docs source:

```python
c.docs.sections
```

---

## Open a Topic

```python
c.show("BS")
c.show("overview")
c.show("audit")
```

Common source interpretation:

- Numeric topics like `BS`, `IS`, `CF` come from `finance`
- Structured disclosure topics like `audit`, `dividend` come from `report`
- Narrative/section topics like `overview`, `business` come from `docs`

---

## Trace the Source

```python
c.trace("BS")
c.trace("overview")
c.trace("audit")
```

`trace(...)` explains which source the topic actually came from.

---

## Filing List

```python
c.filings()
```

View the filings linked to the company and their basic metadata.

---

## Source Namespaces

When needed, drill down directly to a source:

```python
c.docs.sections
c.docs.retrievalBlocks
c.docs.contextSlices

c.finance.BS
c.report.audit
```

But the default public flow is still `sections → show → trace`.

---

## Status and Search

```python
dartlab.Company.status()
dartlab.Company.search("반도체")
dartlab.Company.listing()
```

---

## Disable Progress Display

```python
import dartlab

dartlab.verbose = False
c = dartlab.Company("005930")
```

---

## Next Steps

- [2. Financial Statements](./financial-statements)
- [API Overview](../api/overview)
