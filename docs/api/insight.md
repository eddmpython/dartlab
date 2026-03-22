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
5. Detect anomalies (8 rules)
6. Calculate distress scorecard (4-axis composite)
7. Classify profile
8. Generate Korean-language summary

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
| `distress` | DistressResult | Distress prediction scorecard |
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

Detects financial anomaly signals using 8 rules.

| Category | Detection Target |
|----------|-----------------|
| `earningsQuality` | Operating income increasing but operating CF decreasing |
| `workingCapital` | Rapid increase in trade receivables / inventories |
| `balanceSheetShift` | Debt/borrowings/equity changed by more than +/-50%, capital erosion |
| `cashBurn` | Sharp cash decline, operating CF deficit + financing CF positive (debt-dependent) |
| `marginDivergence` | Operating margin changed by +/-5%p, non-operating income sharp change |
| `financialSector` | Financial sector debt ratio sharp change, net income sharp decline |
| `trendDeterioration` | Consecutive net losses, operating CF losses, ICR below 1, rising debt ratio |
| `cccDeterioration` | Cash conversion cycle expanding 3+ consecutive years |

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

## Distress Prediction Scorecard

The `distress` field provides a comprehensive distress prediction report with evidence-based formatting.

```python
result = analyze("005930")
print(result.distress)
# === 부실 예측 스코어카드 ===
# 종합: safe (2.1/100) | 신용등급: AAA (투자적격 최상위)
# ...
```

### DistressResult

| Field | Type | Description |
|-------|------|-------------|
| `level` | str | safe/watch/warning/danger/critical |
| `overall` | float | Composite score (0~100) |
| `creditGrade` | str | S&P-mapped credit grade (AAA~D) |
| `creditDescription` | str | Grade description in Korean |
| `axes` | list[DistressAxis] | 4 weighted axes with model details |
| `cashRunwayMonths` | float? | Estimated months of cash runway |
| `liquidityAlert` | str? | Liquidity alert level |
| `riskFactors` | list[str] | Structured risk factors |
| `modelCount` | int | Number of models used |
| `dataQuality` | str | 충분/보통/부족 |

### 4 Axes

| Axis | Weight | Models |
|------|--------|--------|
| 정량 분석 | 40% | Ohlson O-Score, Altman Z''-Score, Altman Z-Score |
| 이익 품질 | 20% | Beneish M-Score, Sloan Accrual, Piotroski F-Score |
| 추세 분석 | 30% | trendDeterioration, cccDeterioration anomalies |
| 감사 위험 | 10% | audit/governance anomalies |

### Credit Grade Mapping

| Overall Score | Grade | Description |
|---------------|-------|-------------|
| 5 미만 | AAA | 투자적격 최상위 |
| 10 미만 | AA | 투자적격 상위 |
| 15 미만 | A | 투자적격 |
| 25 미만 | BBB | 투자적격 하한 |
| 35 미만 | BB | 투기등급 |
| 50 미만 | B | 투기등급 하위 |
| 65 미만 | CCC | 상당한 부실 위험 |
| 80 미만 | CC | 부실 임박 |
| 90 미만 | C | 부도 직전 |
| 90 이상 | D | 부도 수준 |

### ModelScore

Each quantitative/quality model produces a `ModelScore`:

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Model name (e.g., "Ohlson O-Score") |
| `rawValue` | float | Raw computed value |
| `displayValue` | str | Human-readable value (e.g., "P(부도) 0.5%") |
| `zone` | str | safe / gray / distress |
| `interpretation` | str | Evidence-based interpretation |
| `reference` | str | Academic reference |

### DistressAxis

| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Axis name |
| `score` | float | Normalized score (0~100) |
| `weight` | float | Weight in composite (0.0~1.0) |
| `models` | list[ModelScore] | Individual model results |
| `summary` | str | Axis-level summary |

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
