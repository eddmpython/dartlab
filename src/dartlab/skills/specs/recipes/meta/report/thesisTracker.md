---
id: recipes.meta.report.thesisTracker
title: Thesis Tracker — falsifier × 신규 evidence diff
category: recipes
kind: recipe
scope: builtin
status: drafted
purpose: 보유 thesis 의 falsifier 게이트 자동화 — 각 thesis 의 falsifier 조건 vs 새 evidence (공시 · 가격 · macro update) diff 단일 표. "반증 불가능 = thesis 아님" 원칙 강행. FSI 벤치마크 cadence recipe 3 의 3 호 + memory benchmark_fsi_repo P0 #2. 트리거 — 'thesis tracker', '논거 점검', 'falsifier check', 'thesis 추적'.
whenToUse:
  - thesis tracker
  - 논거 점검
  - falsifier check
  - thesis 추적
  - 보유 thesis 점검
  - 반증 신호
  - thesis falsifier
linkedSkills:
  - engines.company
  - engines.scan
  - engines.search
  - engines.story
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
  - engines.viz.tableBackedChart
  - engines.viz.evidenceCoverage
visualGuidance:
  - "thesis × falsifier × evidence 표는 engines.viz.tableBackedChart, falsifier 상태 (intact/violated/pending) 색 enum."
  - "thesis 별 evidence coverage 는 engines.viz.evidenceCoverage — coverage < 50% = thesis 점검 권고."
gap:
  primary:
    - company
    - scan
    - search
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "035720"
    - "207940"
    - "035420"
  asOfPolicy: latest
falsifier:
  description: 본 recipe 자체의 falsifier — thesis 입력 0 건이면 trackable 대상 없음. 또한 모든 thesis 의 falsifier 가 null 이면 본 recipe 가치 0 (FSI 원칙 "반증 불가능 = thesis 아님" 위반).
  pythonCheck: |
    assert n_theses > 0 and all(t.get("falsifier") for t in theses)
expectedNovelty:
  - falsifierStatus
  - evidenceDelta
  - thesisHealth
forbidden:
  - falsifier 없는 thesis 등록 금지 — "반증 불가능 = thesis 아님" 원칙 강행 (FSI 벤치마크 + memory benchmark_fsi_repo P1 falsifiable).
  - thesis 폐기 자동 결정 금지 — falsifier 위반 신호 발생 시 운영자 review 후 폐기.
  - 같은 thesis 의 falsifier 재정의로 evidence 회피 금지 (post-hoc 합리화).
failureModes:
  - thesis JSON 외부 저장 — repo 안 위치 미정 (사용자 선택).
  - falsifier 조건이 정량 아닌 정성 ("성장 둔화") 시 자동 판정 불가.
  - 새 evidence 수집 주기 (일/주/월) 따라 lag.
examples:
  - 보유 thesis 5 종 falsifier 게이트 일일 점검
  - thesis "삼성전자 HBM leadership" × Q3 매출 가이던스 + 경쟁사 발표 diff
lastUpdated: '2026-05-28'
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
---

## 공개 호출 방식

```python
import dartlab
import polars as pl
import json
from datetime import date, timedelta

# thesis JSON 외부 저장 — 예시 schema
theses = [
    {
        "thesisId": "th-005930-hbm-2026",
        "stockCode": "005930",
        "title": "삼성전자 HBM4 양산 leadership",
        "claim": "2026 하반기 HBM4 양산 안정화 + 매출 비중 30% 도달",
        "falsifier": {
            "description": "Q3/Q4 HBM 매출 가이던스 +20% YoY 미달 OR 경쟁사 (SK하이닉스) HBM4 양산 6 개월 선행",
            "pythonCheck": "hbm_yoy >= 0.20 and not competitor_lead_6m",
        },
        "createdAt": "2026-01-15",
    },
    {
        "thesisId": "th-035720-ai-2026",
        "stockCode": "035720",
        "title": "카카오 AI 수익화 turning point",
        "claim": "2026 하반기 AI 광고 매출 본격화 + 영업이익률 회복",
        "falsifier": {
            "description": "Q3 영업이익률 5% 미달 또는 AI 광고 매출 100억 미만",
            "pythonCheck": "op_margin >= 0.05 and ai_ad_revenue >= 10_000_000_000",
        },
        "createdAt": "2026-02-01",
    },
]

asof = date.today()
lookback = asof - timedelta(days=30)

rows = []
for th in theses:
    c = dartlab.Company(th["stockCode"])

    # 신규 evidence 수집 (공시 + 가격 + macro)
    new_filings = [
        f for f in c.filings()
        if lookback.strftime("%Y%m%d") <= f["rcept_dt"] <= asof.strftime("%Y%m%d")
    ]
    price_change = dartlab.gather("price", target)  # 기간 필터는 아래에서

    # falsifier 조건 평가 (간이 — 실 평가는 pythonCheck eval)
    status = "intact"   # intact / violated / pending
    evidence_delta = {
        "newFilings": len(new_filings),
        "priceChange30d": price_change,
    }

    rows.append({
        "thesisId": th["thesisId"],
        "stockCode": th["stockCode"],
        "title": th["title"],
        "falsifierStatus": status,
        "evidenceDelta": json.dumps(evidence_delta, ensure_ascii=False),
        "lastCheck": asof.isoformat(),
    })

df = pl.DataFrame(rows)

emit_result(
    table=df,
    values={"n_theses": len(theses), "n_intact": (df["falsifierStatus"] == "intact").sum()},
    date=asof.isoformat(),
    sources=["thesis-json://local", "dartlab://company/liveFilings", "dartlab://company/price"],
)
```

## 호출 동작

### 1. 결론 도출

보유 thesis × falsifier × 신규 evidence diff 단일 표. falsifier 위반 신호 → 운영자 review → thesis 폐기 또는 강화 결정.

### 2. 핵심 근거 수집

- thesis JSON 외부 저장 (사용자 선택 — repo 안 또는 외부 storage)
- `Company.filings()` — 신규 공시 (lookback 기간)
- `dartlab.gather("price", code)` 가격 시계열
- macro update (regime 변화) — `dartlab.macro("cycle"|"rates")`

### 3. 메커니즘 분석

```
thesis JSON 입력 (claim + falsifier)
   ↓
신규 evidence 수집 (공시 + 가격 + macro)
   ↓
falsifier 조건 평가 (pythonCheck eval — 안전 sandbox)
   ↓
status 분류:
   intact     — falsifier 조건 유지 (thesis 살아있음)
   violated   — falsifier 위반 (운영자 review 트리거)
   pending    — evidence 부족 (다음 check 까지 대기)
   ↓
단일 표 + thesisHealth score (intact 일수 / 총 일수)
```

### 4. 반례·한계

- thesis 정성 ("성장 둔화") 시 자동 판정 불가 — 정량 falsifier 강행.
- pythonCheck eval 보안 — 안전 sandbox (RunPython 측 가드) 강행.
- 신규 evidence lag — 공시 indexing 1~3 일.
- thesis 자체 편향 (confirmation bias) — falsifier 외부 검증자 review 권장.

### 5. 후속 모니터링

- status="violated" → 운영자 review → thesis 폐기 또는 재정의 (재정의는 별 thesisId, 회피 가드).
- status="intact" 지속 → `recipes.meta.thesisKillChain.tripwireMonitor` 결합.
- thesisHealth score < 0.5 → thesis 자체 점검.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `thesisId : str`
- `stockCode : str`
- `title : str`
- `falsifierStatus : str` — intact / violated / pending
- `evidenceDelta : str (JSON)`
- `lastCheck : str` — YYYY-MM-DD
- `thesisHealth : float` (선택)

## 연계 절차

1. 본 recipe → 보유 thesis 일일 falsifier 게이트.
2. status="violated" → `recipes.meta.thesisKillChain.falsifierLedger` 운영자 review.
3. status="intact" + 신규 catalyst → `recipes.meta.thesisKillChain.tripwireMonitor`.
4. thesis 정성 → 정량 falsifier 재정의 시 → `recipes.meta.thesisKillChain.thesisIntake`.
5. 일일 cadence 결합 → `recipes.meta.report.dailyMorningNote` Block C (신규 공시 catalyst).
