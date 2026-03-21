---
title: finance.summary
---

# finance.summary

Extracts financial summary data as time series. While `Company`'s default public flow is `sections -> show -> trace`, drop down to the `finance.summary` layer when you want a deeper look at financial time series. **Bridge Matching** automatically tracks account name changes to ensure time series continuity.

## Usage

### Company Shortcut

```python
c = dartlab.Company("005930")

c.BS   # Balance Sheet DataFrame
c.IS   # Income Statement DataFrame
```

> The default public flow is `c.show("BS")`, but come here when you need Bridge Matching analysis results or quarterly/semi-annual financial summaries.

### Public API

```python
c.BS    # Balance Sheet DataFrame
c.IS    # Income Statement DataFrame
c.CF    # Cash Flow Statement DataFrame
c.ratios  # Financial ratios time-series DataFrame
```

> `fsSummary()` is an internal pipeline function used by Bridge Matching. Use the public properties above for general access.

---

## AnalysisResult

Object containing the full Bridge Matching analysis results.

### Key Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `corpName` | `str \| None` | Company name |
| `nYears` | `int` | Number of analysis years |
| `period` | `str` | Analysis period (`"y"`, `"q"`, `"h"`) |

### Financial Statement DataFrames

| Attribute | Type | Description |
|-----------|------|-------------|
| `FS` | `pl.DataFrame \| None` | BS + IS combined time series |
| `BS` | `pl.DataFrame \| None` | Balance Sheet |
| `IS` | `pl.DataFrame \| None` | Income Statement |

### Bridge Matching Statistics

| Attribute | Type | Description |
|-----------|------|-------------|
| `allRate` | `float \| None` | Overall match rate (0.0~1.0) |
| `allMatched` | `int` | Number of matched accounts |
| `allTotal` | `int` | Total number of accounts |
| `contRate` | `float \| None` | Longest continuous segment match rate |
| `nPairs` | `int` | Number of bridge pairs |
| `nBreakpoints` | `int` | Number of breakpoints |
| `nSegments` | `int` | Number of continuous segments |

### Detailed Data

| Attribute | Type | Description |
|-----------|------|-------------|
| `segments` | `list[Segment]` | Continuous segment list |
| `breakpoints` | `list[BridgeResult]` | Breakpoint list |
| `pairResults` | `list[BridgeResult]` | Year-by-year matching results |
| `yearAccounts` | `dict[str, YearAccounts]` | Year-by-year account data |

---

## BridgeResult

Account matching result between two adjacent years. Shows how accounts were linked across years.

| Attribute | Type | Description |
|-----------|------|-------------|
| `curYear` | `str` | Current year (e.g., `"2024"`) |
| `prevYear` | `str` | Previous year (e.g., `"2023"`) |
| `rate` | `float` | Match rate |
| `matched` | `int` | Number of matched accounts |
| `total` | `int` | Total number of accounts |
| `yearGap` | `int` | Year gap |
| `pairs` | `dict[str, str]` | Matched pairs (current account name -> previous account name) |

---

## Segment

A stable continuous segment between breakpoints. Represents the period during which the account system was maintained consistently.

| Attribute | Type | Description |
|-----------|------|-------------|
| `startYear` | `str` | Start year |
| `endYear` | `str` | End year |
| `nYears` | `int` | Number of years |
| `rate` | `float \| None` | Segment average match rate |

---

## Understanding Bridge Matching

DART disclosure financial summaries may have subtle account name changes from year to year. Bridge Matching automatically tracks the same account by combining amount matching and name similarity.

### 4-Step Matching Process

```
2022                    2023                    2024
매출액 ──────────────── 매출액 ──────────────── 수익(매출액)
영업이익 ────────────── 영업이익 ────────────── 영업이익
당기순이익 ──────────── 당기순이익 ──────────── 당기순이익(손실)
```

1. **Exact match**: Link accounts with identical amounts (tolerance within 0.5)
2. **Rewrite match**: Amount error within 5% + name similarity 80%+
3. **Name change match**: Amount error within 5% + name similarity 60%+
4. **Special item match**: Decimal-unit items like EPS

### Breakpoint Detection

When the match rate drops below 85%, it is identified as a breakpoint and the segment is split. This automatically finds the point at which corporate mergers, consolidated/separate transitions, or major structural changes occurred.

> The Bridge Matching algorithm applies these 4 steps sequentially to attempt account linkage.

---

## Usage Examples

### Basic Usage

```python
import dartlab

c = dartlab.Company("005930")

# Company shortcut
print(c.BS)   # Balance Sheet
print(c.IS)   # Income Statement
```

### Bridge Matching Details

Bridge Matching statistics are available through the internal `finance.summary` pipeline. For most users, the public properties (`c.BS`, `c.IS`, `c.CF`) are sufficient.

```python
# Internal usage (advanced):
result = c.finance.summary

# Overall statistics
print(f"Analysis years: {result.nYears}")
print(f"Match rate: {result.allRate:.1%}")
print(f"Breakpoints: {result.nBreakpoints}")
print(f"Continuous segments: {result.nSegments}")
```

### Year-by-Year Matching Results

```python
for pair in result.pairResults:
    print(f"{pair.prevYear} → {pair.curYear}: {pair.rate:.1%} ({pair.matched}/{pair.total})")
```

### Checking Breakpoints

```python
for bp in result.breakpoints:
    print(f"Breakpoint: {bp.prevYear} → {bp.curYear} (match rate {bp.rate:.1%})")
    # Which accounts changed
    for cur, prev in bp.pairs.items():
        if cur != prev:
            print(f"  {prev} → {cur}")
```

### Continuous Segments

```python
for seg in result.segments:
    print(f"{seg.startYear}~{seg.endYear} ({seg.nYears} years, match rate {seg.rate:.1%})")
```

### Financial Statements

```python
c = dartlab.Company("005930")

print(c.BS)   # Balance Sheet (annual time series)
print(c.IS)   # Income Statement (annual time series)
print(c.CF)   # Cash Flow Statement (annual time series)
```
