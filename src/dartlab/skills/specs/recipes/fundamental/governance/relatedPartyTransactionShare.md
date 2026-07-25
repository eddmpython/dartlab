---
id: recipes.fundamental.governance.relatedPartyTransactionShare
title: 특수관계자 매출·매입 비중 추세
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 특수관계자 (대주주·계열사) 와의 매출 + 매입 + 자금대여 비중의 연도별 추세. 비중 > 30% 또는 *전체 매출보다 빠르게 성장* 시 일감몰아주기·이전가격 의심 후보. governance + forensics 결합. 트리거 — '특수관계자 매출·매입 비중 추세', 'related party transaction share', 'relatedPartyTransactionShare'.
whenToUse:
  - 특수관계자 거래 비중
  - 일감몰아주기 의심
  - related party transaction
  - 계열사 의존
examples:
  - 005930 특수관계자 매출 비중 연도별
  - 계열사 매출 의존 — 일감몰아주기 의심 신호
  - 대주주 자금대여 비중 추세
expectedOutputs:
  - 매출 / 매입 / 자금대여 특수관계자 비중 5y 시계열
  - 비중 vs 전체 매출 성장률 비교 단일값
  - 라벨 (의심 / 관찰 / 평상 — 30% 또는 전체보다 빠른 성장 임계)
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.quality.forensics.noteSignalExtractor
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
  - "engines.viz.tableBackedChart"
  - "engines.viz.evidenceCoverage"
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
    - gather
    - analysis
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
falsifier:
  description: "특수관계자 거래 raw 누락 (소규모 회사·미공시) 시 결론 X. 비중 단일값만 보고 의심 단정 금지 — 추세 + 매출 성장률 비교 필수."
lastUpdated: "2026-05-22"
validatedAt: '2026-05-27'
---

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

try:
    rpt_rows = c.gather("relatedPartyTransactions").to_dicts()
except Exception:
    rpt_rows = []

try:
    rev_rows = c.panel("revenue").to_dicts()
    rev_by_year = {str(r.get("year"))[:4]: float(r.get("revenue") or 0) for r in rev_rows}
except Exception:
    rev_by_year = {}

audit = []
for r in sorted(rpt_rows, key=lambda x: str(x.get("year") or "")):
    yr = str(r.get("year"))[:4]
    sales_to_rp = float(r.get("salesToRelated") or 0)
    purch_from_rp = float(r.get("purchasesFromRelated") or 0)
    total_rev = rev_by_year.get(yr, 0)
    audit.append({
        "year": yr,
        "salesToRpPct": sales_to_rp / total_rev if total_rev else None,
        "purchPct": purch_from_rp / total_rev if total_rev else None,
        "absoluteSales": sales_to_rp,
    })

table = pl.DataFrame(audit) if audit else pl.DataFrame(
    schema={"year": pl.Utf8, "salesToRpPct": pl.Float64, "purchPct": pl.Float64, "absoluteSales": pl.Float64}
)

emit_result(
    table=table,
    values={"years": table.height,
            "latestSalesPct": float(table["salesToRpPct"].drop_nulls().tail(1)[0]) if table["salesToRpPct"].drop_nulls().len() else None},
    date=str(table["year"].max()) if table.height else None,
    sources=["dartlab://gather/relatedPartyTransactions", "dartlab://panel/revenue"],
)
```

## 호출 동작

### 1. 결론 도출

salesToRpPct + purchPct 추세 단정. 예: "5y 추세: salesToRpPct 24% → 31% (+7%p), purchPct 18% → 22% (+4%p) → 매출 측 30% 임계 초과 + 5y 누적 +7%p — 일감몰아주기 *의심 후보* (전체 매출 +12% 성장 vs 특수관계자 매출 +45% 가속 — 5y 가속도 우월)."

### 2. 핵심 근거 수집

- Company.gather('relatedPartyTransactions') 연도별 (salesToRelated + purchasesFromRelated)
- Company.panel('revenue') 연도별 총매출
- salesToRpPct = salesToRelated / totalRevenue × 100
- purchPct = purchasesFromRelated / totalRevenue × 100

### 3. 메커니즘 분석

```
연도별 → 3 metric 추세
   salesToRpPct  → 특수관계자 매출 의존도
   purchPct      → 특수관계자 매입 의존도
   absoluteSales → 절대값 (성장 패턴 분리)
   ↓
의심 임계 (3 중 1 이상):
   ① salesToRpPct > 30% (절대 임계)
   ② 연도 간 ≥ +5%p 증가 (변화 임계)
   ③ 특수관계자 매출 성장률 > 전체 매출 성장률 × 2 (가속도 임계)
   ↓
라벨:
   3 임계 모두 미충족 → 평상
   1 임계 충족      → 관찰
   2-3 임계 충족    → 의심 (forensics 후속 필수)
```

비중 단일 시점만으로 의심 X — 추세 + 절대값 + 매출 가속도 3 axis 결합. 합법 그룹 내부거래도 있으므로 *의심 후보* 로만 표기.

### 4. 반례·한계

- 특수관계자 거래 raw 누락 (소규모·미공시) → 비적용.
- 비중 30% 임계는 KR 공정거래법 일감몰아주기 기준 (총수 일가 지분 30%+) 차용 — 회사별 적용 가능성 다름.
- 합법적 그룹 시너지 거래 (지주사 모델) vs 일감몰아주기 분리 어려움.
- 매입 측 (purchPct) 은 이전가격 의심 — 별도 가격 적정성 검증 필요.

### 5. 후속 모니터링

- 의심 라벨 → `recipes.fundamental.quality.forensics.noteSignalExtractor` 로 주석 본문에서 거래 상세 추출.
- absoluteSales 가속 → `recipes.fundamental.quality.forensics.controllingPowerJudgment` 로 실질지배력 변경 추적.
- purchPct ↑ → `recipes.fundamental.governance.audit` 으로 거버넌스 종합 + 이전가격 점검.

## 대표 반환 형태

| column | 의미 |
|---|---|
| `year` | 결산 연도 |
| `salesToRpPct` | 특수관계자 매출 / 총매출 |
| `purchPct` | 특수관계자 매입 / 총매출 |
| `absoluteSales` | 특수관계자 매출 절대값 |

## 연계 절차

1. recipes.fundamental.quality.forensics.noteSignalExtractor - 주석 본문에서 특수관계자 분리.
2. recipes.fundamental.quality.forensics.controllingPowerJudgment - 실질지배력 시점 변경 추적.
3. recipes.fundamental.governance.audit - 거버넌스 종합 audit.

## 기본 검증

- 특수관계자 거래 raw 누락 회사는 본 recipe 비적용.
- 비중 단일 시점만으로 의심 결론 X — 추세 + 매출 성장률 비교 필수.
- *합법적* 그룹 내부거래도 있으므로 *의심 후보* 로만 표기.
