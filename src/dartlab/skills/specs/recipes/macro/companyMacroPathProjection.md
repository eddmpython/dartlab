---
id: recipes.macro.companyMacroPathProjection
title: 회사 P&L × 매크로 시나리오 grid → 적정가치 분포 (p25/50/75)
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: 기존 base/bull/bear 3 path DCF 가 아니라 매크로 146 시나리오 (rate × FX × 사이클 × 침체) grid × 회사 elasticity → 146 P&L path → 146 fair value → 분포 (p25/p50/p75 + 현재가 대비 확률) 산출. 단일 점추정의 한계 보완. company ↔ macro ↔ analysis 격리 메우는 조합. 트리거 — '시나리오 적정가치 분포', 'fair value distribution', '146 시나리오 valuation'.
whenToUse:
  - 시나리오 적정가치 분포
  - fair value distribution
  - 146 macro path
  - DCF 분포
linkedSkills:
  - engines.company
  - engines.analysis
  - engines.macro
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
  - "engines.viz.scenarioVisuals"
  - "engines.viz.tableBackedChart"
  - "engines.viz.mermaidDiagram"
visualGuidance:
  - "stress·민감도·충격 전파는 engines.viz.scenarioVisuals를 사용하고 assumption grid 또는 수치 임계가 없으면 scenario table로 낮춘다."
  - "표 기반 순위·추세는 engines.viz.tableBackedChart만 사용하고 tableRef/evidenceBinding이 없으면 차트 대신 검산 표로 낮춘다."
  - "메커니즘 diagram은 engines.viz.mermaidDiagram으로 8노드 이하만 만들고 모든 edge에 문장·수치·sourceRef 근거를 둔다."

gap:
  primary:
    - analysis
    - macro
testUniverse:
  market: KR
  stockCodes:
    - "005930"
    - "000660"
    - "035420"
    - "051910"
    - "055550"
  asOfPolicy: latest
falsifier:
  description: "fair value 분포 std-dev 가 base price 의 5% 미만이면 시나리오들이 collapse 한 것 (sensitivity 무효)"
  pythonCheck: |
    assert fv_distribution_std / current_price >= 0.05
expectedNovelty:
  - p25FairValue
  - p50FairValue
  - p75FairValue
  - probAboveCurrent
forbidden:
  - 단일 시나리오 (base) 만으로 적정가치 단정 금지 — 분포 필수.
  - elasticity 가 산업 평균만 사용 — 회사별 추정 신뢰도 차이 무시 금지.
failureModes:
  - 146 시나리오가 너무 corner case 지향이면 분포 fat-tail 으로 왜곡.
  - DCF discount rate (WACC) 가 시나리오 별 변동 — 단순 일정 가정 시 분포 좁아짐.
examples:
  - 삼성전자 146 시나리오 fair value 분포
  - 현대차 시나리오 적정가치 p25/p50/p75
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
validatedAt: '2026-05-27'
---

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

forecast = c.analysis("growth")
macro_sensitivity = c.analysis("macroSensitivity")
valuation_band = c.analysis("valuationBand")
scenario = dartlab.macro("scenario", market="KR")
bs = c.panel("BS", freq="Y")

emit_result(
    table=[
        {"step": "companyGrowth", "result": compact(forecast)},
        {"step": "macroSensitivity", "result": compact(macro_sensitivity)},
        {"step": "scenario", "result": compact(scenario)},
        {"step": "valuationBand", "result": compact(valuation_band)},
    ],
    values={"target": target, "pathSteps": 4, "scenarioReady": compact(scenario)["type"] != "NoneType"},
    date=latest_period(bs),
    sources=["dartlab://company/panel", "dartlab://company/forecast", "dartlab://macro/scenario"],
)
```

## 호출 동작

### 1. 결론 도출

146 시나리오 fair value 분포 + probAboveCurrent 단정. 예: "005930 현재가 78,000 / p25 fair=72,500 / p50=82,300 / p75=94,100 / probAboveCurrent=0.62 → median fair value > 현재가 (5.5% 상회) + 62% 시나리오에서 상회 — 중장기 우상향 분포 우세."

### 2. 핵심 근거 수집

- c.analysis('growth') — base revenue forecast
- c.analysis('macroSensitivity') — rate / FX elasticity 계수
- macro('scenario', market='KR') — 146 시나리오 grid (rate × FX × cyclePhase × 침체)
- c.analysis('valuationBand') — 적정 multiple band
- c.panel('BS') — 기준 balance + 발행주식

### 3. 메커니즘 분석

```
146 시나리오 (rate × FX × phase × 침체)
   각 시나리오 → revenue elasticity 적용 → P&L path
   ↓
146 P&L path → multiple 적용 → 146 fair value
   ↓
분포 산출:
   p25 = 하위 25% fair value (보수적 valuation)
   p50 = median (중앙값)
   p75 = 상위 25% (낙관 valuation)
   probAboveCurrent = (fair > current price) 비율
   ↓
single point estimate 보완:
   p50 > current + probAboveCurrent > 60% → 상승 분포 우세
   p25 < current < p50 + probAbove ~ 50% → 양면 분포
   p75 < current                     → 하락 분포 우세
```

분포 std-dev 가 base price 의 5% 이상 → sensitivity 유효. < 5% → 시나리오 collapse (가정 무효 — pythonCheck falsifier 발동).

### 4. 반례·한계

- elasticity 가 회사별 추정 vs 산업 평균 — 산업 평균 사용 시 회사 고유성 무시.
- WACC (discount rate) 가 시나리오별 변동 — 일정 가정 시 분포 좁아짐 (보수적).
- 146 시나리오는 historical pattern 기반 — black swan 미커버.
- multiple 기반 fair value — multiple regime shift 시 분포 위치 이동.

### 5. 후속 모니터링

- probAboveCurrent > 70% → `recipes.quant.qualityFactor` 로 quality cross-check.
- distribution std-dev 큼 (sensitive) → `recipes.macro.qualityMacroBeta` 로 phase 정합 확인.
- p25 < 현재가 < p50 → `recipes.macro.tailRiskScenarioScan` 으로 하방 시나리오 매칭.

## 대표 반환 형태

`pl.DataFrame` — 단일 row:
- `scenarioCount : int`
- `currentPrice : float`
- `p25FairValue : float` · `p50FairValue : float` · `p75FairValue : float`
- `probAboveCurrent : float`
- `distributionStd : float`

## 연계 절차

1. 본 recipe → 적정가치 분포.
2. probAboveCurrent > 0.7 → strong buy / < 0.3 → strong sell signal.
3. distribution std-dev 큰 종목 → sensitivity 큰 회사. `recipes.macro.betaPeerScreen` 와 결합.

## 기본 검증

- `ValidateRecipe(..., capture=False)` 기준으로 공개 호출 블록이 실행되어야 한다.
- `requiredEvidence`의 근거 종류가 모두 반환되어야 한다.
- target을 바꿔도 `Company("005930")` 하드코딩 가정이 남지 않아야 한다.

## AI 직접 사용 방식

1. `ReadSkill` 에서 사용자 질문과 `whenToUse`를 맞춰 이 recipe를 고른다.
2. `GetSkillBody` 로 본문 전체를 읽고 `linkedSkills` 순서대로 먼저 필요한 엔진 skill을 확인한다.
3. `## 공개 호출 방식`의 첫 Python 블록을 target만 바꿔 `ValidateRecipe(..., capture=False)`로 smoke 실행한다.
4. 실행 결과의 `skillRef`, `tableRef`, `valueRef`, `dateRef`, `executionRef` 중 누락된 근거가 있으면 답변을 작성하지 말고 호출 또는 근거 요구를 보강한다.
5. 답변은 결론, 핵심 근거, 메커니즘, 반례·한계, 후속 모니터링 순서로 작성하고 `falsifier.description`이 있으면 반례 단락에서 반드시 확인한다.
