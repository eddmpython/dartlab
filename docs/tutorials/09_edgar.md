---
title: "9. US Stocks (EDGAR)"
---

# 9. US Stocks (EDGAR)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/09_edgar.ipynb)

DartLab supports not only Korean DART but also US SEC EDGAR through the same facade.

This tutorial covers:

- Creating an EDGAR `Company`
- Viewing 10-K / 10-Q structure with `sections`
- Opening financial and narrative topics with `show()`
- Checking sources with `trace()`
- Accessing raw public APIs with `OpenEdgar`

---

## Creating an EDGAR Company

```python
import dartlab

c = dartlab.Company("AAPL")
c.corpName
c.ticker
c.market
```

---

## Start with `sections`

```python
c.sections
c.docs.sections
```

EDGAR follows the same `sections`-centric flow as DART.

- `c.sections`: public company board
- `c.docs.sections`: pure docs source

---

## Financial Statements

```python
c.show("BS")
c.show("IS")
c.show("CF")
```

EDGAR's numeric topics are handled by the `finance` layer based on SEC XBRL.

---

## 10-K / 10-Q Narrative Sections

```python
c.show("10-K::item1Business")
c.show("10-K::item1ARiskFactors")
c.show("10-K::item7MDandA")
```

EDGAR narrative topics open on top of the docs structure. Rather than explaining text and tables as separate public contracts, think of it as opening the topic payload as-is.

---

## Source Tracking

```python
c.trace("BS")
c.trace("10-K::item1ARiskFactors")
```

`trace()` shows which source a topic came from and its provenance.

---

## OpenEdgar

Use `OpenEdgar` when you need a source-native public API wrapper.

```python
from dartlab import OpenEdgar

e = OpenEdgar()

e.company("AAPL")
e.filings("AAPL", forms=["10-K"])
e.companyFactsJson("AAPL")
```

This layer preserves the SEC public API surface as closely as possible.

---

## Current Status

EDGAR Company is continuously being improved.

- The `sections -> show -> trace` flow is already shared
- `report` is limited, unlike DART's rich official API layer
- OpenAPI and stored parquet are aligned for compatibility with the DartLab runtime

---

## Next Steps

- [1. Quickstart](./quickstart)
- [API Overview](../api/overview)
