---
id: recipes.fundamental.governance.chaebolEntityNetwork
title: 재벌 계열사 망 (지분율·이사 동시재직)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 한국 재벌 그룹 안 회사들의 지분율 cross-holding + 임원/이사 동시재직 (interlocking directorate) network 매핑. 지주사·순환출자·차등의결권의 정량 진입점. governance ↔ scan 결합. 트리거 — '재벌 계열사 망 (지분율·이사 동시재직)', 'chaebol entity network', 'chaebolEntityNetwork'.
whenToUse:
  - 재벌 계열사 망
  - chaebol network
  - 지분율 cross-holding
  - 임원 동시재직
examples:
  - 삼성 그룹 계열사 망 지분율 cross-holding
  - 재벌 그룹 안 임원 동시재직 (interlocking)
  - 005930 속한 그룹 지주사 / 순환출자 구조
expectedOutputs:
  - 그룹 안 회사 list + 지분율 cross-holding 표
  - interlocking directorate 카운트 (회사 × 임원)
  - 지주사 / 순환출자 / 차등의결권 라벨 (구조 분류)
linkedSkills:
  - engines.company
  - engines.scan
  - engines.analysis
toolRefs:
  - EngineCall
  - RunPython
requiredEvidence:
  - skillRef
  - tableRef
  - valueRef
  - dateRef
  - executionRef
  - sourceRef
visualRefs:
  - "engines.viz.mermaidDiagram"
  - "engines.viz.peerMatrix"
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: limited
  pyodide:
    status: limited
gap:
  primary:
    - analysis
    - scan
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "005380"
falsifier:
  description: "그룹 식별 reference 누락 시 결론 X. 단일 회사만 보고 *재벌 network* 결론 금지 — 그룹 전체 universe 필수."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

# 그룹 식별 (reference)
try:
    group_info = c.panel("groupAffiliation").to_dicts()
    group_name = group_info[0].get("groupName") if group_info else None
except Exception:
    group_name = None

try:
    net = dartlab.scan("network")   # dict: corp_edges · code_to_group · invest_edges
    affiliates = net["corp_edges"] if group_name else []
except Exception:
    affiliates = []

# 각 affiliate 와 cross-holding 비율
network = []
for a in affiliates[:15]:
    code = a.get("code") or a.get("stockCode")
    if not code:
        continue
    holding = float(a.get("ownershipPct") or 0)  # target → affiliate
    reverse = float(a.get("reverseOwnershipPct") or 0)  # affiliate → target
    shared_directors = int(a.get("sharedDirectorCount") or 0)
    network.append({
        "affiliate": code,
        "name": a.get("name"),
        "outwardPct": holding,
        "inwardPct": reverse,
        "crossHolding": holding > 0 and reverse > 0,
        "sharedDirectors": shared_directors,
    })

table = pl.DataFrame(network) if network else pl.DataFrame(
    schema={"affiliate": pl.Utf8, "name": pl.Utf8, "outwardPct": pl.Float64,
            "inwardPct": pl.Float64, "crossHolding": pl.Boolean, "sharedDirectors": pl.Int64}
)

cross_n = int(table["crossHolding"].sum()) if table.height else 0
emit_result(
    table=table,
    values={"groupName": group_name, "affiliates": table.height, "crossHoldings": cross_n},
    date=None,
    sources=["dartlab://panel/groupAffiliation", "dartlab://scan/groupAffiliates"],
)
```

## 호출 동작

### 1. 결론 도출

그룹 affiliate × crossHolding × sharedDirectors 단정. 예: "005930 그룹='삼성' / affiliates=15 / crossHoldings=3 (양방향 지분 동시 보유 — 005930↔028260, 005930↔010140 등) / 평균 sharedDirectors=1.2 / 최대 sharedDirectors=4 (특정 계열사 임원 중첩) → cross 구조 + 임원 network 동조 — 그룹 결속력 강."

### 2. 핵심 근거 수집

- Company.panel('groupAffiliation') → groupName 식별
- `dartlab.scan("network")` → dict (corp_edges · invest_edges · code_to_group · cycles). 출자 사슬과 계열 관계
- 각 affiliate × (ownershipPct + reverseOwnershipPct + sharedDirectorCount) 3 metric
- crossHolding = outwardPct > 0 AND inwardPct > 0

### 3. 메커니즘 분석

```
그룹 universe (≤ 15 affiliate) → 3 metric 매트릭스
   outwardPct (target → affiliate)
   inwardPct  (affiliate → target)
   sharedDirectors (공유 이사 수)
   ↓
crossHolding 카운트:
   crossHolding True 다수 → 순환출자 구조 의심 (2014 개정 이후 신규는 위법)
   sharedDirectors 평균 ≥ 2 → interlocking directorate 강
   outward 큼 + inward 0 → 단방향 지배 (지주사 구조)
   outward 0 + inward 큼 → 단방향 피지배
   ↓
구조 분류:
   지주사    → 1 affiliate 가 다수 outward (peak 30%+)
   순환출자  → cross 3+ (예: A→B→C→A)
   차등의결권 → 별 metric (본 recipe 미커버)
```

KR 재벌 — 공정거래위원회 발표 그룹 (대규모기업집단 = 자산 5조+). IFRS 연결범위 ≠ 공정위 그룹 (지배구조 vs 회계 기준 차이).

### 4. 반례·한계

- 그룹 식별 reference 누락 회사 (비재벌·소규모) 비적용.
- 공정위 그룹 ≠ IFRS 연결범위 → 분리 표기 필수.
- 순환출자 자체 위법 X (2014 이후 신규만 금지) — *의심 후보* 표기.
- 우회 cross-holding (재단/사모펀드 경유) → 미커버.

### 5. 후속 모니터링

- crossHolding 3+ → `recipes.fundamental.quality.forensics.ownershipDisparityMap` 으로 지배 vs 의결 괴리.
- sharedDirectors 평균 ≥ 2 → `recipes.fundamental.governance.boardIndependenceTrend` 로 이사회 multiSeat 추세.
- outward 단방향 큼 (지주사 의심) → `recipes.fundamental.quality.forensics.controllingPowerJudgment` 로 실질지배력 판정.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `affiliate` | 계열사 코드 |
| `outwardPct` | 본 회사 → 계열사 지분율 |
| `inwardPct` | 계열사 → 본 회사 지분율 |
| `crossHolding` | 양방향 지분 동시 보유 |
| `sharedDirectors` | 공유 이사 수 |

## 연계 절차

1. recipes.fundamental.quality.forensics.ownershipDisparityMap - 지배지분 vs 의결지분 괴리.
2. recipes.fundamental.quality.forensics.controllingPowerJudgment - 실질지배력 판정.
3. recipes.fundamental.governance.audit - 거버넌스 종합.

## 기본 검증

- 그룹 식별 reference 누락 회사 (비재벌·소규모) 는 본 recipe 비적용.
- 공정거래위원회 발표 그룹과 IFRS 연결범위 불일치 가능 — 분리 표기.
- 순환출자 자체가 위법 X (2014 개정 이후 신규만 금지) — *의심 후보* 표기.
