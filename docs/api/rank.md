---
title: Market Ranking
---

# Market Ranking

Calculates rankings across all listed companies based on revenue, assets, and growth rate. Provides both overall market rankings and within-sector rankings.

## Usage

```python
from dartlab.engines.rank import getRankOrBuild

rank = getRankOrBuild("005930")

rank.corpName              # "삼성전자"
rank.sector                # "IT"
rank.industryGroup         # "반도체"

# Revenue ranking
rank.revenueRank           # 3 (overall market)
rank.revenueTotal          # 2508 (total companies)
rank.revenueRankInSector   # 1 (within IT sector)
rank.revenueSectorTotal    # 122 (IT sector companies)

# Asset ranking
rank.assetRank             # 5
rank.assetRankInSector     # 2

# Growth ranking
rank.growthRank            # 320
rank.growthRankInSector    # 45

# Size class
rank.sizeClass             # "large"
```

## Functions

### getRankOrBuild()

```python
getRankOrBuild(stockCode: str, *, verbose: bool = True) -> RankInfo | None
```

Returns immediately from cache if available; otherwise builds a full snapshot first.

| Parameter | Type | Description |
|-----------|------|-------------|
| `stockCode` | str | Stock code |
| `verbose` | bool | Print progress during build |

### getRank()

```python
getRank(stockCode: str) -> RankInfo | None
```

Looks up from cache only. Returns `None` if cache does not exist.

### buildSnapshot()

```python
buildSnapshot(*, verbose: bool = True) -> dict[str, RankInfo]
```

Builds a full snapshot of all companies and saves to local cache. Takes approximately 2 minutes for 2,500+ companies.

Process:
1. Load full KRX company list
2. Classify sector + collect financial time series for each company
3. Sort by revenue/assets/growth across all companies
4. Calculate within-sector rankings separately
5. Determine size class
6. Save JSON cache (`{dataDir}/_cache/rank_snapshot.json`)

## RankInfo

| Field | Type | Description |
|-------|------|-------------|
| `stockCode` | str | Stock code |
| `corpName` | str | Company name |
| `sector` | str | Sector name (Korean) |
| `industryGroup` | str | Industry group name (Korean) |
| **Financial Metrics** | | |
| `revenue` | float (optional) | TTM revenue (KRW) |
| `totalAssets` | float (optional) | Total assets (KRW) |
| `revenueGrowth3Y` | float (optional) | 3-year revenue CAGR (%) |
| **Revenue Ranking** | | |
| `revenueRank` | int (optional) | Overall market rank |
| `revenueTotal` | int | Total ranked companies |
| `revenueRankInSector` | int (optional) | Within-sector rank |
| `revenueSectorTotal` | int | Companies in sector |
| **Asset Ranking** | | |
| `assetRank` | int (optional) | Overall market rank |
| `assetTotal` | int | Total ranked companies |
| `assetRankInSector` | int (optional) | Within-sector rank |
| `assetSectorTotal` | int | Companies in sector |
| **Growth Ranking** | | |
| `growthRank` | int (optional) | Overall market rank |
| `growthTotal` | int | Total ranked companies |
| `growthRankInSector` | int (optional) | Within-sector rank |
| `growthSectorTotal` | int | Companies in sector |
| **Classification** | | |
| `sizeClass` | str | Size class |

### Size Classes

| Class | Criteria |
|-------|----------|
| `large` | Top 10% by revenue |
| `mid` | Top 10~30% by revenue |
| `small` | Below top 30% by revenue |

## Examples

```python
from dartlab.engines.rank import getRankOrBuild, buildSnapshot

# Single company lookup
rank = getRankOrBuild("000660")
print(f"{rank.corpName}: Revenue {rank.revenueRank}/{rank.revenueTotal}")
print(f"  Sector ({rank.sector}): {rank.revenueRankInSector}/{rank.revenueSectorTotal}")
print(f"  Size: {rank.sizeClass}")

# Build full snapshot (first time)
snapshot = buildSnapshot()
print(f"Ranked {len(snapshot)} companies")

# Top 10 in a specific sector
it_stocks = [(k, v) for k, v in snapshot.items() if v.sector == "IT" and v.revenueRankInSector]
it_stocks.sort(key=lambda x: x[1].revenueRankInSector)
for code, r in it_stocks[:10]:
    print(f"  #{r.revenueRankInSector}: {r.corpName} ({code})")
```

## Cache

The snapshot is saved to `{dataDir}/_cache/rank_snapshot.json`. `getRankOrBuild()` loads from cache immediately if available; otherwise builds a new snapshot.

To refresh the cache, call `buildSnapshot()` directly.
