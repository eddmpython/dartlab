---
title: Insight Grades
---

# Insight Grades

Analyzes a company's financial health across 7 areas, assigns A~F grades, detects anomalies, and classifies an overall profile.

## Usage

```python
from dartlab.engines.insight import analyze

result = analyze("005930")

# 7-area grades
result.grades()
# {
#   "performance": "A",
#   "profitability": "A",
#   "health": "A",
#   "cashflow": "B",
#   "governance": "A",
#   "risk": "B",
#   "opportunity": "A"
# }

# Summary
result.profile   # "premium"
result.summary   # "삼성전자는 실적, 수익성, 재무건전성 등 대부분..."
result.anomalies # [] (no anomalies)
```

## analyze()

```python
analyze(stockCode: str, company: Company = None) -> AnalysisResult | None
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `stockCode` | str | Stock code (6 digits) |
| `company` | Company (optional) | Company instance. Created internally if None |

Returns `None` if data is insufficient.

### Analysis Process

1. Build quarterly/annual financial time series
2. Calculate financial ratios
3. Auto-detect financial sector (6 signals: debt ratio, interest income, etc.)
4. Grade 7 areas
5. Detect anomalies (6 rules)
6. Classify profile
7. Generate Korean-language summary

## 7 Analysis Areas

### performance (Earnings Growth)

Analyzes revenue and operating income growth rates and volatility.

| Grade | Criteria |
|-------|----------|
| A | Both revenue and operating income growing, low volatility |
| B | One growing or moderate volatility |
| C | Stagnant |
| D | Declining |
| F | Persistent decline |

### profitability (Profitability)

Analyzes operating margin, net margin, ROE, and ROA. Sector benchmark adjustments are applied.

| Grade | Criteria |
|-------|----------|
| A | Operating margin 10%+, ROE 15%+ |
| B | Operating margin 5%+, ROE 8%+ |
| C | Operating margin positive, ROE positive |
| D | Operating margin or ROE negative |
| F | Both significantly negative |

### health (Financial Health)

Analyzes debt ratio and current ratio. Separate criteria applied for financial sector.

| Grade | General Company Criteria |
|-------|--------------------------|
| A | Debt ratio below 50%, current ratio above 200% |
| B | Debt ratio below 100%, current ratio above 150% |
| C | Debt ratio below 200%, current ratio above 100% |
| D | Debt ratio below 400% |
| F | Debt ratio above 400% or capital erosion |

### cashflow (Cash Flow)

Analyzes operating cash flow, free cash flow (FCF), FCF margin, and trends.

| Grade | Criteria |
|-------|----------|
| A | Operating CF positive + FCF positive + improving trend |
| B | Operating CF positive + FCF positive |
| C | Operating CF positive, FCF negative |
| D | Operating CF negative |
| F | Persistently negative operating CF |

### governance (Governance)

Analyzes largest shareholder ownership ratio, audit opinion, and dividend status.

| Grade | Criteria |
|-------|----------|
| A | Unqualified opinion + stable ownership + dividend |
| B | Unqualified opinion + partially met |
| C | Unqualified opinion, rest unmet |
| D | Audit opinion warning |
| F | Adverse opinion / Disclaimer of opinion |

### risk (Overall Risk)

Synthesizes risk flags from the other 6 areas.

### opportunity (Investment Opportunity)

Synthesizes opportunity flags from the other 6 areas.

## AnalysisResult

| Field | Type | Description |
|-------|------|-------------|
| `corpName` | str | Company name |
| `stockCode` | str | Stock code |
| `isFinancial` | bool | Whether financial sector |
| `performance` | InsightResult | Earnings growth |
| `profitability` | InsightResult | Profitability |
| `health` | InsightResult | Financial health |
| `cashflow` | InsightResult | Cash flow |
| `governance` | InsightResult | Governance |
| `risk` | InsightResult | Overall risk |
| `opportunity` | InsightResult | Investment opportunity |
| `anomalies` | list[Anomaly] | List of anomalies |
| `summary` | str | Korean-language summary |
| `profile` | str | Company profile |

### grades() Method

```python
result.grades() -> dict[str, str]
```

Returns grades for all 7 areas as a dict.

## InsightResult

Analysis result for each area.

| Field | Type | Description |
|-------|------|-------------|
| `grade` | str | Grade (A/B/C/D/F, N=no data) |
| `summary` | str | Korean summary |
| `details` | list[str] | Detailed analysis items |
| `risks` | list[Flag] | Risk flags |
| `opportunities` | list[Flag] | Opportunity flags |

## Anomaly Detection

Detects financial anomaly signals using 6 rules.

| Category | Detection Target |
|----------|-----------------|
| `earningsQuality` | Operating income increasing but operating CF decreasing |
| `workingCapital` | Rapid increase in trade receivables / inventories |
| `balanceSheetShift` | Debt/borrowings/equity changed by more than +/-50%, capital erosion |
| `cashBurn` | Sharp cash decline, operating CF deficit + financing CF positive (debt-dependent) |
| `marginDivergence` | Operating margin changed by +/-5%p, non-operating income sharp change |
| `financialSector` | Financial sector debt ratio sharp change, net income sharp decline |

```python
for a in result.anomalies:
    print(f"[{a.severity}] {a.category}: {a.text}")
    # [warning] earningsQuality: 영업이익은 증가했으나 영업CF는 감소
```

## Anomaly

| Field | Type | Description |
|-------|------|-------------|
| `severity` | str | "danger", "warning", "info" |
| `category` | str | Anomaly type |
| `text` | str | Detailed description |
| `value` | float (optional) | Numeric value |

## Company Profiles

Classifies companies into one of 6 profiles based on grade combinations.

| Profile | Condition |
|---------|-----------|
| `premium` | High average grade + low risk |
| `growth` | Performance / profitability / opportunity all top-tier |
| `stable` | Health / risk / profitability all stable |
| `caution` | Risk D/F or health F |
| `distress` | Most areas low-grade |
| `mixed` | Does not match above conditions |

## Examples

```python
from dartlab.engines.insight import analyze

result = analyze("005930")

# Check grades
for area, grade in result.grades().items():
    print(f"{area}: {grade}")

# Profitability details
print(result.profitability.summary)
for d in result.profitability.details:
    print(f"  - {d}")

# Risk flags
for flag in result.risk.risks:
    print(f"[{flag.level}] {flag.category}: {flag.text}")

# Anomalies
if result.anomalies:
    print("=== Anomalies Detected ===")
    for a in result.anomalies:
        print(f"  [{a.severity}] {a.text}")

# Summary
print(f"Profile: {result.profile}")
print(result.summary)
```
