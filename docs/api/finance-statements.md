---
title: finance.statements
---

# finance.statements

Extracts consolidated financial statements into time series separated by Balance Sheet (BS), Income Statement (IS), and Cash Flow Statement (CF). While `Company`'s default public flow is `sections -> show -> trace`, drop down to the `finance.statements` layer when you need to work with detailed financial accounts directly. Provides **detailed line items** (50~200) from the original statements, more granular than the financial summary.

## Usage

### Company Shortcut

```python
c = dartlab.Company("005930")

c.BS   # Balance Sheet
c.IS   # Income Statement
c.CF   # Cash Flow Statement
```

### Full Access via `get()`

```python
result = c.get("statements")

result.BS    # Balance Sheet — detailed asset, liability, and equity items
result.IS    # Income Statement — detailed revenue, expense, and profit items
result.CF    # Cash Flow Statement — operating/investing/financing activities
```

### Quarterly / Semi-Annual

```python
result = c.get("statements", period="q")   # Quarterly
result = c.get("statements", period="h")   # Semi-annual
```

---

## Parameters

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `period` | `str` | `"y"` | `"y"` annual, `"q"` quarterly, `"h"` semi-annual |
| `ifrsOnly` | `bool` | `True` | K-IFRS periods only |

---

## StatementsResult

| Attribute | Type | Description |
|-----------|------|-------------|
| `corpName` | `str \| None` | Company name |
| `period` | `str` | Analysis period |
| `nYears` | `int` | Number of years |
| `BS` | `pl.DataFrame \| None` | Balance Sheet |
| `IS` | `pl.DataFrame \| None` | Income Statement |
| `CF` | `pl.DataFrame \| None` | Cash Flow Statement |

---

## fsSummary vs statements Comparison

These two modules extract the same financial statements from different sources. Choose based on your use case.

| | fsSummary (`c.fsSummary()`) | statements (`c.get("statements")`) |
|-----|------------------------|------------|
| **Source** | Financial summary | Consolidated statement body |
| **Item count** | 20~30 core items | 50~200 detailed items |
| **Bridge Matching** | Applied (auto-tracks account name changes) | Not applied (original as-is) |
| **Cash Flow Statement** | Not included | Included (CF) |
| **Time series continuity** | Excellent (auto-tracking) | Depends on original |
| **Use case** | Long-term trend analysis | Detailed line item inspection |

> **General rule**: Start with `c.show("BS")` on the public board. Drop down to the finance layer with `c.BS`, `c.CF`, `c.get("statements")`, or `c.fsSummary()` when you need more detailed account breakdowns.

---

## Usage Examples

### Balance Sheet — Key Items

```python
import dartlab

c = dartlab.Company("005930")

print(c.BS)
# account         | 2015       | 2016       | ... | 2024
# 자산총계        | 262,174,324| 261,381,064| ... | ...
# 유동자산        | 124,140,661| 134,506,949| ... | ...
#   현금및현금성자산| 22,636,744| 32,111,442| ... | ...
#   매출채권       | 25,168,026| 24,348,622| ... | ...
# 비유동자산      | 138,033,663| 126,874,115| ... | ...
# 부채총계        | 63,119,716| 54,704,095| ... | ...
# 자본총계        | 199,054,608| 206,676,969| ... | ...
```

### Cash Flow Statement

```python
print(c.CF)
# account                 | 2015        | 2016        | ...
# 영업활동 현금흐름        | 40,061,761 | 47,386,037  | ...
# 투자활동 현금흐름        | -28,017,281| -26,252,505 | ...
# 재무활동 현금흐름        | -10,740,937| -9,756,700  | ...
```

### Quarterly Detail

```python
result = c.get("statements", period="q")
print(result.IS)
# account  | 2023Q1 | 2023Q2 | 2023Q3 | 2023Q4 | 2024Q1 | ...

print(result.CF)
# account  | 2023Q1 | 2023Q2 | 2023Q3 | 2023Q4 | 2024Q1 | ...
```

### Checking Missing Statement Items

```python
result = c.get("statements")
print(f"BS items: {result.BS.height if result.BS is not None else 0}")
print(f"IS items: {result.IS.height if result.IS is not None else 0}")
print(f"CF items: {result.CF.height if result.CF is not None else 0}")
```
