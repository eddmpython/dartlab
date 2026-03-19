---
title: "8. Cross-Company Comparison"
---

# 8. Cross-Company Comparison — Sector, Insight, Ranking

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eddmpython/dartlab/blob/master/notebooks/tutorials/08_cross_company.ipynb)

Use DartLab's analysis engines to classify companies by sector, assign 7-area insight grades, and check market rankings.

- Sector classification (WICS 11 sectors)
- Sector-specific benchmark parameters
- Insight grades (7 areas, A–F)
- Anomaly detection
- Market ranking
- Comprehensive comparison table

Timeseries generation and financial ratio comparison were covered in [3. Timeseries Analysis](./timeseries) and [4. Financial Ratios](./ratios), so this tutorial focuses on the analysis engines.

---

## Setup

```python
import dartlab
```

---

## Sector Classification

DartLab automatically classifies companies using the WICS (WiseFn Industry Classification Standard) 11-sector system. Comparing companies within the same sector produces meaningful analysis — comparing the debt ratio of a semiconductor company with a bank is pointless.

```python
from dartlab.engines.sector import classify

for code in ["005930", "000660", "035420", "051910"]:
    info = classify(code)
    print(f"{info.corpName}: {info.sector} > {info.industryGroup} (confidence: {info.confidence})")
```

Classification follows three steps:
1. **Override mapping** — Manually assigned companies (e.g., 삼성전자 → Information Technology)
2. **Keyword matching** — Extracting keywords from company name and business description
3. **KSIC code mapping** — Based on the Korean Standard Industrial Classification code

### 11 Sectors

| Sector | Example Companies |
|--------|------------------|
| Energy | SK이노베이션, S-Oil |
| Materials | LG화학, POSCO |
| Industrials | 현대건설, 두산 |
| Consumer Discretionary | 현대차, 삼성물산 |
| Consumer Staples | 농심, CJ제일제당 |
| Health Care | 삼성바이오, 셀트리온 |
| Financials | KB금융, 삼성생명 |
| Information Technology | 삼성전자, SK하이닉스 |
| Communication Services | NAVER, 카카오 |
| Utilities | 한국전력, 한국가스 |
| Real Estate | 신한알파리츠 |

### Sector Benchmarks

Each sector has its own benchmark parameters. These are used when applying sector-appropriate discount rates, growth rates, and PER multiples in valuation models.

```python
from dartlab.engines.sector import getParams

params = getParams("005930")
print(f"Sector: {params.sector}")
print(f"Discount rate: {params.discountRate}%")
print(f"Growth rate: {params.growthRate}%")
print(f"PER multiple: {params.perMultiple}x")
```

---

## Insight Grades

Seven areas are graded A through F to quickly identify a company's strengths and weaknesses. Over 30 financial metrics are automatically analyzed.

```python
from dartlab.engines.insight import analyze

for code in ["005930", "000660", "035420"]:
    result = analyze(code)
    if result is None:
        continue
    grades = result.grades()
    grade_str = " / ".join(f"{k}:{v}" for k, v in grades.items())
    print(f"{result.company.corpName} [{result.profile}]: {grade_str}")
```

### 7 Grading Areas

| Area | Evaluation Criteria | A-Grade Standard (example) |
|------|---------------------|---------------------------|
| **performance** | Revenue/operating profit growth | Revenue 20%+ growth, profit 30%+ growth |
| **profitability** | Operating margin, ROE | Operating margin 15%+, ROE 15%+ |
| **health** | Debt ratio, current ratio | Debt ratio below 50%, current ratio 200%+ |
| **cashflow** | Operating CF, FCF | Stable operating CF, positive FCF |
| **governance** | Largest shareholder stake, audit opinion | Stable governance, unqualified audit opinion |
| **risk** | Anomalies, contingent liabilities, related party transactions | No anomalies, minor contingent liabilities |
| **opportunity** | Growth potential | Strong combination of growth and profitability |

Grades range from A (excellent) to F (severe issues) in 6 levels.

### Profile

Summarizes the company's overall character in a single word.

```python
result = analyze("005930")
print(result.profile)   # "안정형", "성장형", "위험형" etc.
```

### Anomaly Detection

Automatically detects statistical anomalies (Z-score based) in financial metrics.

```python
result = analyze("005930")
for anomaly in result.anomalies:
    print(f"  {anomaly.metric}: Z-score {anomaly.zscore:.1f} ({anomaly.direction})")
```

For example, a sudden drop in inventory turnover or an abnormally extended accounts receivable collection period would be detected as anomalies. These can be warning signs of accounting fraud, inventory buildup, or bad debts.

---

## Market Ranking

Check where a company stands among all listed companies. Both overall market ranking and within-sector ranking are provided for revenue and assets.

```python
from dartlab.engines.rank import getRankOrBuild

for code in ["005930", "000660", "035420"]:
    rank = getRankOrBuild(code)
    if rank is None:
        continue
    print(f"\n{rank.corpName} ({rank.sector})")
    print(f"  Revenue rank: {rank.revenueRank}/{rank.revenueTotal} (in sector: {rank.revenueRankInSector}/{rank.revenueSectorTotal})")
    print(f"  Asset rank: {rank.assetRank}/{rank.assetTotal}")
    print(f"  Size class: {rank.sizeClass}")
```

`sizeClass` categorizes company size as large, mid, or small. Using this to compare companies of "same sector, similar size" produces the most meaningful results.

---

## Comprehensive Comparison Example

A pattern for consolidating multiple metrics into a single table.

```python
import polars as pl
import dartlab
from dartlab.engines.dart.finance import getTTM, getLatest
from dartlab.engines.sector import classify

codes = ["005930", "000660", "035420", "051910", "006400"]
rows = []

for code in codes:
    c = dartlab.Company(code)
    r = c.ratios
    sector = classify(code)
    if r is None:
        continue
    rows.append({
        "기업": c.corpName,
        "섹터": sector.sector if sector else "",
        "매출(억)": round(r.revenueTTM / 1e8) if r.revenueTTM else None,
        "영업이익률(%)": round(r.operatingMargin, 1) if r.operatingMargin else None,
        "ROE(%)": round(r.roe, 1) if r.roe else None,
        "부채비율(%)": round(r.debtRatio, 1) if r.debtRatio else None,
        "FCF(억)": round(r.fcf / 1e8) if r.fcf else None,
    })

df = pl.DataFrame(rows)
print(df)
```

---

## Next Steps

- [Account Standardization and Timeseries](../api/timeseries) — 7-step mapping, snakeId list, normalization details
- [Sector Classification](../api/sector) — Classification criteria and benchmark parameters
- [Insight Grades](../api/insight) — 7-area grading criteria and anomaly detection
- [Market Ranking](../api/rank) — Overall and within-sector ranking calculation
