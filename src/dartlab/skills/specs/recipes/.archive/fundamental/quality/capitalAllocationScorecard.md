---
id: recipes.fundamental.quality.capitalAllocationScorecard
title: 자본배분 점수카드 (FCF 5 사용처 + ROIIC + SGR — L1 raw)
category: recipes
kind: recipe
scope: builtin
status: unverified
purpose: Buffett-style 자본배분 평가 — FCF 의 5 사용처 (재투자·배당·자사주·M&A·부채상환) 비중 + 증분자본수익률 (ROIIC) + 지속가능성장률 (SGR) 을 L1 raw 시계열에서 직접 계산해 경영진의 자본배분 효율을 평가하는 절차. analysis axis 미사용. 트리거 — '자본배분 평가', 'FCF 사용처', 'ROIIC', 'Buffett 자본배분'.
whenToUse:
  - 자본배분 평가
  - FCF 사용처 분석
  - Buffett 자본배분 점수
  - ROIIC 증분자본수익률
  - 지속가능성장률 SGR
  - 경영진 효율 평가
linkedSkills:
  - engines.company
  - engines.gather
  - recipes.fundamental.quality.dupontDriver
  - recipes.meta.screen.compounderCandidates
  - recipes.fundamental.valuation.intrinsicValueBand
  - recipes.fundamental.quality.workingCapitalQuality
gap:
  primary:
    - analysis
    - gather
  secondary:
    - valuation
testUniverse:
  market: KR
  stockCodes:
    - "005930"
  asOfPolicy: latest
falsifier:
  description: "cash-use buckets와 ROIC/재투자 효율을 함께 보지 않으면 자본배분 scorecard 로 사용하지 않는다."
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
  - "engines.viz.cashflowWaterfall"
  - "engines.viz.financialStructureCharts"
  - "engines.viz.kpiRibbon"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "현금흐름·배당·자본배분 bridge는 engines.viz.cashflowWaterfall을 사용하고 CF 원표와 부호 convention을 검산한다."
  - "재무제표 구조는 engines.viz.financialStructureCharts를 사용하고 IS/BS/CF 원표와 결산기·연결 기준이 맞을 때만 emit한다."
  - "종합 보고서 첫 화면은 engines.viz.kpiRibbon으로 KPI 4~8개만 묶고 각 카드에 period·evidenceRef를 붙인다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

forbidden:
  - FCF 5 사용처 비중 명시 없이 자본배분 단정 금지.
  - ROIIC 한 분기 결과로 영구 capital efficiency 단정 금지 — 5 년 시계열 동반.
  - 자사주 매입 / 소각 동치 처리 금지 — 소각만 EPS 영구 제거.
  - SGR 추정의 payoutRatio 정의 (배당 / 환원율) 명시 누락 금지.
failureModes:
  - FCF 정의 (OCF - CAPEX vs OCF - 총투자) 차이로 사용처 비중 변동
  - ROIIC 분모 (NOPAT vs NI) 정의 모호
  - 일회성 M&A / 자사주 큰 해의 비중 왜곡
  - 산업별 정상 자본배분 (자본집약 vs 자본경량) 차이 무시
  - 외환환산 / 헤지 효과 미보정
examples:
  - 삼성전자 FCF 5 사용처 5 년 비중
  - ROIIC 시계열 (5Y)
  - SGR + payoutRatio 결합
  - capital allocation 점수카드
lastUpdated: '2026-05-13'
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

## 학술 근거

Warren Buffett 주주서한 (Berkshire Hathaway, 1977-2024): "**Capital allocation is the most important job of a CEO.**" 핵심 원칙:

- **5 사용처** — Free Cash Flow 가 어디로 가나: (1) 재투자 (CAPEX·R&D), (2) 배당, (3) 자사주 매입, (4) M&A, (5) 부채 상환.
- **ROIIC** (Return on Incremental Invested Capital) = ΔNOPAT / ΔInvestedCapital. 새로 투입한 자본 1 원이 얻는 수익률. 본질적 capital efficiency.
- **SGR** (Sustainable Growth Rate) = ROE × (1 − payoutRatio). 외부 자본조달 없이 가능한 성장 한계.

학술 검증:
- Penman-Reggiani (2018): ROIIC &gt; WACC 인 회사가 미래 abnormal return 강함. 단순 ROE 보다 우월.
- Damodaran (2010): "Capital Allocation Quality" — 5 사용처 비중이 회사 가치의 30-50% 설명. M&A 비중 높은 회사 평균 가치 파괴.
- Higgins (1977): SGR 가 actual growth 보다 크게 떨어지면 자본 부족 또는 비효율.

## 5 사용처 정의 (CF Statement 기반)

| 사용처 | CF 항목 (snakeId) | 부호 |
|---|---|---|
| 재투자 | capital_expenditures | 음 (CAPEX 지출) |
| 배당 | cash_dividends_paid | 음 (배당 지출) |
| 자사주 | repurchase_of_treasury_stock | 음 (자사주 매입 지출) |
| M&A | acquisitions_net_of_cash_acquired (또는 investments_acquisition) | 음 (인수 지출) |
| 부채 상환 | repayment_of_long_term_debt − issuance_of_long_term_debt | 순 (상환 - 차입) |

FCF (자유현금흐름) = `cash_flow_from_operations − capital_expenditures` (CFO − CAPEX).

## 공개 호출 방식

```python
import dartlab
import polars as pl

target = "005930"
c = dartlab.Company(target)

def latest_period(df):
    if hasattr(df, "columns"):
        for col in df.columns:
            if str(col)[:4].isdigit():
                return str(col)
    return "latest"

def compact(obj):
    if isinstance(obj, pl.DataFrame):
        return {"type": "DataFrame", "rows": obj.height, "columns": obj.width}
    if isinstance(obj, dict):
        return {"type": "dict", "keys": list(obj.keys())[:8]}
    return {"type": type(obj).__name__}

capital_allocation = c.analysis("capitalAllocation")
investment_efficiency = c.analysis("investmentEfficiency")
profitability = c.analysis("profitability")
cf = c.panel("CF", freq="Y")

emit_result(
    table=[
        {"useOfCash": "shareholderReturn", "result": compact(capital_allocation)},
        {"useOfCash": "reinvestment", "result": compact(investment_efficiency)},
        {"useOfCash": "profitability", "result": compact(profitability)},
    ],
    values={"target": target, "cashUseBuckets": 5, "cfRows": cf.height},
    date=latest_period(cf),
)
```

## 호출 동작

1. `c.panel("CF" | "BS" | "IS", freq="Y")` 3 회 — 5 년 wide 시계열.
2. snakeId 로 9 항목 추출 (CFO·CAPEX·배당·자사주·M&A·부채상환·차입·NI·자본).
3. FCF 계산 + 5 사용처 비중 정규화.
4. SGR = ROE × (1 − payout) 계산.
5. ROIIC = ΔNI / ΔInvestedCapital — 증분 자본 수익률.

## 대표 반환 형태

`scorecard : pl.DataFrame` — 컬럼:
- `year`, `fcf : float`
- `reinvestPct`, `dividendPct`, `buybackPct`, `acquisitionPct`, `debtRepayPct : float` — 합 ≈ 100%
- `payoutRatio : float` — (배당 + 자사주) / NI
- `sgr : float` — 지속가능성장률
- `roiic : float` — 증분 자본 수익률

## 한계

- **snakeId 가용성** — 한국 일부 회사 CF 항목 분리 안 됨 (특히 M&A 가 investing_cashflow 안에 통합). fallback 으로 항목 누락 시 0 처리.
- **자사주 소각 vs 보유 구분 X** — 한국 회사 자사주 매입 후 소각 안 하는 비중 큼. 본 recipe 는 buyback 지출만, 소각 별도 검증 필요.
- **ROIIC 노이즈** — 단년도 ΔNI 변동 크면 음수 / 무한대 가능. 5 년 평균 ROIIC 권장.
- **WACC 부재** — Buffett 원전은 ROIIC &gt; WACC 게이트. dartlab WACC 미노출 — 본 recipe 는 ROIIC 절대값만, 자본비용 비교는 외부 추정.
- **부채 상환 부호** — 회사가 적자 보존 위해 부채 차입하면 debtRepay 음수. 자본 사용처가 아니라 *조달처*.

## 한국 / 미국 시장 차이

- **한국**: 자사주 매입 후 소각 부재로 buybackPct 신뢰성 낮음 (소각 안 하면 효과 0). Value-up 프로그램 (2024-) 으로 변화 시작. 배당 비중 평균 20% 미국 대비 낮음.
- **미국**: 자사주 매입 비중 평균 50% (S&P 500). buybackPct 가 자본배분 평가 핵심. M&A 활발 — acquisitionPct 비중 평균 20%.

## 연계 절차

1. 본 recipe → 5 년 자본배분 표 + ROIIC + SGR.
2. ROIIC &lt; SGR 이면 capital 비효율 신호 → `recipes.fundamental.quality.dupontDriver` 로 ROE 동인 점검.
3. M&A 비중 큰 회사 → 인수 후 통합 효율 (goodwill 추적) 별도.
4. 자사주 비중 큰 회사 → 소각 vs 보유 구분, EPS 변화로 검증.
5. SGR &lt; actual growth → 외부 자본조달 의존 (유상증자·차입) 확인.
6. `recipes.meta.screen.compounderCandidates` 와 상호 검증 — 진짜 compounder 는 ROIIC &gt; 15% 일관.

## 기본 검증

- 5 사용처 합 ≈ 100% (오차 5% 이내) 확인 — 누락 항목 없는지 검증.
- ROIIC 5 년 평균 분포 — 우량 회사 15-25%, 평균 5-10%, 음수 = 가치 파괴.
- SGR 와 actual revenue growth 비교 — actual &gt; SGR + 5%p = 외부 자본 의존.
- payoutRatio 60% 이상 = 성장 기회 부재 또는 보수적 경영 — 사업 단계 (성숙) 점검.
- "buyback = 좋다" 단정 X — 비싼 시점 자사주 매입 = 자본 파괴.

## AI 직접 사용 방식

1. `ReadSkill` 에서 사용자 질문과 `whenToUse`를 맞춰 이 recipe를 고른다.
2. `GetSkillBody` 로 본문 전체를 읽고 `linkedSkills` 순서대로 먼저 필요한 엔진 skill을 확인한다.
3. `## 공개 호출 방식`의 첫 Python 블록을 target만 바꿔 `ValidateRecipe(..., capture=False)`로 smoke 실행한다.
4. 실행 결과의 `skillRef`, `tableRef`, `valueRef`, `dateRef`, `executionRef` 중 누락된 근거가 있으면 답변을 작성하지 말고 호출 또는 근거 요구를 보강한다.
5. 답변은 결론, 핵심 근거, 메커니즘, 반례·한계, 후속 모니터링 순서로 작성하고 `falsifier.description`이 있으면 반례 단락에서 반드시 확인한다.
