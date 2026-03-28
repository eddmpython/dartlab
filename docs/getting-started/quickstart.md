---
title: Quick Start
---

# Quick Start

DartLab does three things: **Company**, **Scan**, **Ask**.

## Install

```bash
pip install dartlab
```

## 1. Company -- read any company

```python
import dartlab

c = dartlab.Company("005930")  # Samsung Electronics
```

Data is downloaded automatically on first use. No setup needed.

## 2. See the whole company

```python
c.sections   # topic x period company map
c.topics     # what topics are available
```

## 3. Open any topic

```python
c.show("businessOverview")   # narrative text
c.show("companyOverview")    # company overview
```

## 4. Financial statements

```python
c.IS      # Income Statement
c.BS      # Balance Sheet
c.CF      # Cash Flow
c.ratios  # 47 financial ratios
```

## 5. Detect what changed

```python
c.diff()                    # which topics changed most
c.diff("businessOverview")  # drill into one topic
```

## 6. US companies -- same API

```python
apple = dartlab.Company("AAPL")
apple.IS
apple.show("10-K::item1ARiskFactors")
```

## 7. Scan the market

```python
dartlab.search("삼성전자")              # find companies
dartlab.scan("ratio", "roe")           # ROE across 2,700+ companies
dartlab.scan("account", "매출액")       # revenue across all companies
```

## 8. Ask AI

```bash
pip install "dartlab[llm]"
```

```python
dartlab.ask("Analyze Samsung Electronics financial health")
```

Requires a provider. Run `dartlab setup` for options (OpenAI, Ollama, ChatGPT OAuth).

## Next

- [Sections guide](./sections) -- how the company map works
- [Notebooks](../tutorials/) -- interactive Colab and Marimo notebooks
- [API Reference](../api/overview)
- [Installation details](./installation)
