---
title: Sector Classification
---

# Sector Classification

Classifies companies into investment sectors based on the WICS (Wise Industry Classification Standard). Uses a 3-tier priority system and provides sector-specific valuation parameters.

## Usage

```python
from dartlab.engines.sector import classify, getParams

info = classify("삼성전자", kindIndustry="통신 및 방송 장비 제조업")
info.sector          # Sector.IT
info.industryGroup   # IndustryGroup.SEMICONDUCTOR
info.confidence      # 1.0
info.source          # "override"

params = getParams(info)
params.discountRate  # 13.0 (%)
params.perMultiple   # 15
params.label         # "반도체"
```

## classify()

```python
classify(companyName: str, kindIndustry: str = None, mainProducts: str = None) -> SectorInfo
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `companyName` | str | Company name |
| `kindIndustry` | str (optional) | KIND industry name (KSIC-based) |
| `mainProducts` | str (optional) | Main products text |

### 3-Tier Classification Priority

| Tier | Method | Confidence | Target |
|------|--------|------------|--------|
| 1 | Manual override | 0.95~1.0 | ~100 large caps (삼성전자, SK하이닉스, etc.) |
| 2 | Keyword analysis | 0.6~0.9 | Keyword matching from main products text |
| 3 | KSIC mapping | 0.7 | KIND industry name to WICS mapping (200+ items) |

If no match is found at any tier, returns `Sector.UNKNOWN` (confidence 0.0).

## SectorInfo

| Field | Type | Description |
|-------|------|-------------|
| `sector` | Sector | WICS major classification (11 sectors) |
| `industryGroup` | IndustryGroup | WICS mid-level classification (47 groups) |
| `confidence` | float | Confidence score (0.0~1.0) |
| `source` | str | Classification basis ("override", "keyword", "ksic", "unknown") |

## Sector (11 Major Classifications)

| Value | Korean | English |
|-------|--------|---------|
| `ENERGY` | 에너지 | Energy |
| `MATERIALS` | 소재 | Materials |
| `INDUSTRIALS` | 산업재 | Industrials |
| `CONSUMER_DISC` | 경기관련소비재 | Consumer Discretionary |
| `CONSUMER_STAPLES` | 필수소비재 | Consumer Staples |
| `HEALTHCARE` | 건강관리 | Healthcare |
| `FINANCIALS` | 금융 | Financials |
| `IT` | IT | IT |
| `COMMUNICATION` | 커뮤니케이션서비스 | Communication Services |
| `UTILITIES` | 유틸리티 | Utilities |
| `REAL_ESTATE` | 부동산 | Real Estate |

## getParams()

```python
getParams(sectorInfo: SectorInfo) -> SectorParams
```

Uses mid-level parameters if available; otherwise falls back to major classification parameters.

## SectorParams

| Field | Type | Description |
|-------|------|-------------|
| `discountRate` | float | Discount rate (%) |
| `growthRate` | float | Growth rate (%) |
| `perMultiple` | float | PER multiple |
| `pbrMultiple` | float | PBR multiple |
| `evEbitdaMultiple` | float | EV/EBITDA multiple |
| `label` | str | Sector label (Korean) |

Sector parameters are benchmark values reflecting industry characteristics. Used in DCF, PER/PBR band analysis, etc.

## Examples

```python
from dartlab.engines.sector import classify, getParams, Sector

# Large cap — Immediately classified via manual override
info = classify("SK하이닉스")
print(info)  # SectorInfo(IT/반도체, conf=1.00, src=override)

# Mid/small cap — Keyword-based classification
info = classify("에코프로비엠", mainProducts="양극재, 이차전지 소재")
print(info)  # SectorInfo(IT/2차전지, conf=0.90, src=keyword)

# KSIC-based classification
info = classify("미래에셋증권", kindIndustry="증권 중개업")
print(info)  # SectorInfo(FINANCIALS/증권, conf=0.70, src=ksic)

# Valuation parameters
params = getParams(info)
print(f"PER: {params.perMultiple}, Discount rate: {params.discountRate}%")
```
