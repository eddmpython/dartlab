---
title: DartLab
---

# DartLab

DartLab is a Python library that turns disclosures into one company map.

The core of DartLab is `sections`. It horizontalizes annual and quarterly report sections across the time axis first, then layers stronger sources like `finance` and `report` on top.

```python
import dartlab

c = dartlab.Company("005930")

c.sections
c.show("companyOverview")
c.trace("BS")
```

## How It Works

- Start with a single `Company`
- `sections` is the canonical company board
- `show(topic)` opens the topic you need
- `trace(topic)` reveals the selected source and provenance

You don't need to memorize a list of parsers first. Instead, you view the entire company as one map and drill down into the topic you need.

## Why sections Matters

Disclosures are inherently vertical documents. Company overview, business description, financial matters, risk, and governance flow sequentially across time.

DartLab transforms these vertical documents:

1. Identifies section boundaries
2. Aligns matching structural units side by side across years/quarters
3. Consumes `finance`, `report`, and `docs` source-aware on top

This structure enables:

- Viewing the entire company structure at once
- Comparing the same topic across multiple periods
- AI interfaces consuming the same map directly

## Company Structure

- `c.sections`: public company board
- `c.docs.sections`: pure docs horizontalization source
- `c.finance`: authoritative numeric layer
- `c.report`: authoritative structured disclosure layer
- `c.profile`: merged company layer on top of docs spine

The public workflow is `sections → show → trace`.

## Get Started

- [Quick Start](getting-started/quickstart)
- [API Overview](api/overview)
- [Stability Policy](stability)
- [Changelog](changelog)
