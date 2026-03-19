---
title: "10. Ownership Network"
---

# 10. Ownership Network — Listed Company Investment and Shareholding Map

Analyze investment and shareholding relationships among Korean listed companies, with group classification, circular ownership detection, and interactive network visualization.

## Key Concepts

- **Investment**: A company invests in another company (based on investedCompany disclosures)
- **Shareholding**: Major shareholder status of a company (based on majorHolder disclosures)
- **Group classification**: A 5-step balanced classification algorithm that automatically identifies groups such as Samsung, Hyundai Motor, SK, LG, etc.
- **Circular ownership**: Automatic detection of circular paths like A→B→C→A

## Basic Usage

### Browser Visualization

```python
import dartlab

c = dartlab.Company("005930")   # 삼성전자

# Ego view — relationship map centered on this company
c.network().show()              # 1-hop neighbors
c.network(hops=2).show()        # 2-hop neighbors

# Save as HTML file
c.network().save("삼성전자_네트워크.html")
```

Features available in the browser view:
- **Dark/light theme** toggle
- **Company search** — by name or stock code (`/` key to focus)
- **Group panel** — click a group on the left panel to highlight only that group
- **Node click** → highlights connected companies, dims the rest
- **Hover tooltip** — node: company info, edge: ownership ratio and investment purpose
- **Arrow direction** — indicates investment flow
- **ESC** — reset highlights

### DataFrame View

When you need data instead of visualization:

```python
# List of affiliates in the same group
c.network("members")
# → stock code, company name, market, industry, self flag

# Investment/shareholding edges
c.network("edges")
# → stock code, company name, type, direction, purpose, ownership ratio, group

# Circular ownership paths
c.network("cycles")
# → path, length, company list

# Ego subgraph (DataFrame)
c.network("peers")
# → stock code, company name, group, industry, connection count, self flag
```

### Full Market

```python
# Full relationship network of all Korean listed companies
dartlab.network().show()
```

A full market relationship map with 1,600+ nodes and 4,400+ edges. The vis.js forceAtlas2Based physics engine renders large graphs stably.

## Usage Examples

### Identifying Group Affiliates

```python
c = dartlab.Company("005930")
members = c.network("members")
print(f"Samsung Group listed affiliates: {len(members)}")
print(members)
```

### Checking Key Investment Relationships

```python
edges = c.network("edges")

# Filter for investment relationships only
investments = edges.filter(edges["유형"] == "investment")
print(investments.sort("지분율", descending=True))
```

### Detecting Circular Ownership

```python
cycles = c.network("cycles")
if len(cycles) > 0:
    print(f"Circular ownership: {len(cycles)} cases found!")
    print(cycles)
else:
    print("No circular ownership")
```

## Data Sources

Network data is extracted from two types of disclosures in DART annual reports:

| Disclosure | Description |
|------------|-------------|
| `investedCompany` | Investment in other corporations — where and how much was invested |
| `majorHolder` | Major shareholder status — who holds how much of this company |

This is combined with the raw disclosure text on affiliated companies (docs ground truth) to improve the accuracy of group classification.

## Classification Algorithm

5-step balanced classification:

1. **Disclosure text** — Groups directly confirmed from the affiliated companies disclosure
2. **Major conglomerates** — Seeds for Samsung, Hyundai Motor, SK, LG, Lotte, etc.
3. **Investment propagation** — Expanding groups by following investments with management participation purpose
4. **Corporate shareholders** — Absorbed if the major shareholder belongs to the same group
5. **Individual shareholders/keywords** — Final classification via shared individual shareholders and company name keywords

## Notes

- Data is based on DART annual reports, so unlisted companies without filings are not included
- Building the full market network takes ~20 seconds on the first call (cached afterwards)
- Requires an internet connection as vis.js CDN is used
