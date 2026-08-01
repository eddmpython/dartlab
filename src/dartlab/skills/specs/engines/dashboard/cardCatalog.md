---
id: engines.dashboard.cardCatalog
title: 대시보드 카드 카탈로그 (종류·5-tier·variance·adapter SSOT)
kind: curated
scope: builtin
status: observed
category: engines
purpose: viz dashboard 의 카드 종류 + 5-tier 규격 + variance 한도 + dataSpec adapter 의 SSOT. catalog entry 의 layout 산출과 변형 한도 검증의 단일 근거. P-DASH-V1 통합.
whenToUse:
  - dashboard
  - card catalog
  - layout
  - tier
  - colSpan
  - rowSpan
  - bento
  - regsize
  - variance
inputs:
  - tab (financial/portfolio/valuation/governance/peer/lifecycle/macro/viewer)
  - sub view (performance/capitalStructure/cashflow/risk)
  - kind 필터 (kpiTile/trend/gauge/...)
outputs:
  - list[(cardKey, CatalogEntry)] from queryCards
  - (colSpan, rowSpan) from resolveLayout
  - packed grid from packSkyline / planTabLayout
capabilityRefs: []
knowledgeRefs:
  - engines.dashboard
  - engines.viz
  - operation.dashboardDesign
sourceRefs:
  - dartlab://skills/engines.dashboard.cardCatalog
requiredEvidence:
  - cardKey
  - executionRef
  - sourceRef
expectedOutputs:
  - layoutTuple
  - packedGrid
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

# 대시보드 카드 카탈로그 SSOT

본 spec 은 `src/dartlab/viz/layout.py` 의 동작 계약을 객관 서술한다. catalog
entry (`src/dartlab/viz/catalog/*.py`) 는 본 spec 의 규격을 따라야 하고,
`src/dartlab/viz/lintDashboardLayout.py` 가 PR gate 로 검증한다.

## 공개 호출 방식

```python
from dartlab.viz import (
    queryCards, resolveLayout, packSkyline, planTabLayout,
    listBlocks, KIND_DEFAULT_TIER, BLOCKS,
)

# 1. 카탈로그 검색
cards = queryCards(tab='financial', sub='performance')
# → [(cardKey, entry), ...]

# 2. 단일 카드 layout 산출
cs, rs = resolveLayout(entry)
# → (2, 3) — variance 위반 시 ValueError

# 3. 탭 전체 packed grid
placed = planTabLayout('financial', sub='performance')
# → [{cardKey, kind, title, x, y, w, h}, ...]

# 4. Semantic 묶음 호출
keys = listBlocks('performanceCore')
# → ['kpiOpMarginPerf', ..., 'growthYoy']
```

## 호출 동작

1. **queryCards** — `CATALOG` (dict) 를 순회하며 `tab`/`sub`/`kinds`/`topic`
   다중 필터. catalog dict 의 삽입 순서 보존 (Python 3.7+ 표준).
2. **resolveLayout** — entry.layout 명시 우선 → kind=trend 자동 보정 (1~3=2×2,
   4~5=2×3, 6+=4×4) → KIND_DEFAULT_TIER 의 (cs, rs). 명시 layout 이 variance
   한도 밖이면 ValueError.
3. **packSkyline** — First-Fit-Decreasing skyline 알고리즘. 4 col 기준, 각 col
   의 다음 빈 row 추적. 큐에서 width ≤ availWidth 인 첫 카드 선택 → 배치 →
   skyline 갱신. 모든 카드가 availWidth 초과 시 다음 row 진입.
4. **planTabLayout** — queryCards + packSkyline 결합. 한 호출로 페이지 전체
   배치 산출.
5. **listBlocks** — 의미 단위 카드 묶음 (Looker-style). `performanceCore` 등.

## 대표 반환 형태

```python
# queryCards
[
    ('kpiOpMarginPerf', {'kind': 'kpiTile', 'title': '영업이익률', 'tab': 'financial',
                          'subCategory': 'performance', ...}),
    ('marginTrend', {'kind': 'trend', 'title': '이익률 추세', ...}),
    ...
]

# planTabLayout
[
    {'cardKey': 'kpiOpMarginPerf', 'kind': 'kpiTile', 'title': '영업이익률',
     'x': 0, 'y': 0, 'w': 1, 'h': 1},
    {'cardKey': 'kpiNetMarginPerf', 'kind': 'kpiTile', 'title': '순이익률',
     'x': 1, 'y': 0, 'w': 1, 'h': 1},
    {'cardKey': 'marginTrend', 'kind': 'trend', 'title': '이익률 추세',
     'x': 0, 'y': 1, 'w': 2, 'h': 3},
    ...
]
```

## 카드 5-tier 매트릭스

| tier | colSpan × rowSpan | aspect | 용도 | kind |
|---|---|---|---|---|
| **XS** | 1 × 1 | 1:1 square | 단일 KPI | `kpiTile`, `diffView` (단일) |
| **S** | 1 × 2 | 1:2 tall | gauge, narrow list | `gauge` (default), `topList` |
| **M** | 2 × 2 | 1:1 square | trend (1~3 시리즈), scatter, matrix, radar, breakdown, waterfall | 7 kind default |
| **L** | 2 × 3 | 2:3 tall-square | trend (4~5 시리즈), comparisonTable | trend 자동 / comparisonTable default |
| **XL** | 4 × 4 | 1:1 square hero | dual-stack 9 시리즈, scoreBadge | `trend` 6+, `scoreBadge` |
| **W** (변형) | 4 × 1 | 4:1 wide strip | phaseIndicator 6 단계 | `phaseIndicator` default |
| **WIDE** (변형) | 4 × 3 | 4:3 wide | comparisonTable (peer wide), narrativeBridge | `comparisonTable` variance, `narrativeBridge` default |

## 변형 한도 (variance) 표

| kind | default | 허용 변형 |
|---|---|---|
| `kpiTile` | 1×1 | (없음 — 고정) |
| `diffView` | 1×1 | 2×2, 2×3 |
| `gauge` | 1×2 | 2×2 |
| `topList` | 1×2 | 1×3, 2×3 |
| `phaseIndicator` | 4×1 | 2×1 |
| `comparisonTable` | 2×3 | 4×3 |
| `radar` | 2×2 | 3×3 |
| `scatter` | 2×2 | 3×3, 2×3 |
| `matrix` | 2×2 | 3×3 |
| `trend` | 2×2 | 1×3, 2×3, 3×3, 4×4, 4×2, 4×3 |
| `breakdown` | 2×2 | 1×2 |
| `waterfall` | 2×2 | 3×3 |
| `scoreBadge` | 4×4 | 2×2 |
| `narrativeBridge` | 4×3 | (없음) |
| `sankey` (deprecated) | 3×3 | 2×3, 4×3 |

## dataSpec adapter 목록

catalog entry 의 `dataSpec.adapter` 가 builder dispatch 의 key.

| adapter | 입력 | 출력 |
|---|---|---|
| `kpiFromNorm` | tilePlans (label/account/ratio/compose) | KpiTile (value, prev, unit, intent) |
| `diffFromNorm` | tilePlans + periodLabel | tiles + periodLabel |
| `flagsTopList` | module + fn | items (label/value/delta) |
| `peerComparison` | (analysisCall: peerBenchmark) | rows (self/peerMedian/p25/p75/percentile) |
| `peerScatter` | (analysisCall: peerBenchmark.scatter) | points (x, y, label, self) |
| `distressGauge` | analysis `calcDistressScore`의 비금융 Z'' | value + bands |
| `beneishGauge` | canonical 입력 계약 복구 전 비발행 | 빈 결과 |
| `lifeCyclePhase` | (계산: CF 부호 + 매출 성장) | phases + current + confidence |
| `cashflowSankey` (deprecated) | norm | nodes + links |
| `capitalAllocationBars` (신설) | norm | stacked series over time |
| `capitalAllocationWaterfall` (신설) | norm | single-year waterfall |

## Semantic Block library

```python
BLOCKS = {
    'performanceCore': [kpi 4 + trend 3],
    'capitalStructureCore': [kpi 4 + hero + 분해 4],
    'cashflowCore': [kpi 4 + trend 2 + allocation 2],
    'riskCore': [gauge 4 + heatmap + topList + lifeCycle],
}
```

블록 호출 = AI agent 또는 frontend 가 "수익성 분석" 한 마디로 카드 N 묶음
획득. catalog cardKey 가 실제 존재해야 한다 (loose coupling — caller 검증).

## 카드 종류 = 11 + 신설 4

- 기존 11: `kpiTile · trend · gauge · topList · phaseIndicator · scatter ·
  comparisonTable · matrix · radar · diffView · breakdown · waterfall · sankey
  (deprecated)`.
- 신설 4 (P-DASH-V1): `scoreBadge` (snowflake 종합) · `narrativeBridge` (Damodaran
  5-step) · `referenceBand` (trend overlay 옵션) · `decompositionPanel` (gauge
  input 분해).

## 변형 한도 위반 검증

`src/dartlab/viz/lintDashboardLayout.py` 가 catalog 전수 검증. 위반 시 PR gate
거부. 새 변형 필요 시 본 spec 의 variance 표 + `KIND_DEFAULT_TIER` 동시 갱신.

## Anti-Patterns

- ❌ catalog entry 에 `layout: {colSpan: 5}` (5 col 미지원, 4 col grid 한도).
- ❌ `kpiTile` 의 layout 명시 (XS 고정, variance 없음).
- ❌ packSkyline 결과의 빈 cell — packing 알고리즘 보장 안 되면 입력 카드
  조합이 잘못된 것 (catalog 의 layout 명시가 grid 맞춤 깨는지 검토).

## 기본 검증

catalog 변경 시 동기화 경로:

- `src/dartlab/viz/lintDashboardLayout.py` 가 catalog 전수 검증 (variance 한도 · grid 위반 · packing 결손) — PR `lint` 게이트.
- 새 카드 종류 추가 = catalog entry + `KIND_DEFAULT_TIER` + 본 sub-spec 의 variance 표 3 곳 동시 갱신. 누락 시 lint 거부.
- 누락/결손 표시: `lintDashboardLayout.py` 가 `exit 2` + 위반 카드 id list 출력. 빈 cell 은 silent drop 금지.
