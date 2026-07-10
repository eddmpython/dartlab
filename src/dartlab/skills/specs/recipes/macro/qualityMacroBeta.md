---
id: recipes.macro.qualityMacroBeta
title: 퀄리티 (QMJ) × 매크로 사이클 — phase 의존 우량주
category: recipes
kind: recipe
scope: builtin
status: curated
purpose: quality 팩터 (QMJ — Asness/Frazzini/Pedersen) 점수가 매크로 사이클 phase (early-recovery / mid-expansion / late-cycle / contraction) 별로 다르게 작동한다는 검증된 패턴을 단일 회사에 적용. quant ↔ macro 격리 메우는 조합. 트리거 — '퀄리티 사이클', 'QMJ 매크로', 'quality phase'.
whenToUse:
  - 퀄리티 사이클
  - QMJ 매크로
  - quality phase
  - 후행 우량주
linkedSkills:
  - engines.company
  - engines.quant
  - engines.scan
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
    - quant
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
  description: quality decile 1 (낮은 퀄리티) 가 early-recovery 에서 decile 10 (높은 퀄리티) 보다 outperform 하면 factor inversion
  pythonCheck: |
    assert decile10_return_in_early_recovery > decile1_return_in_early_recovery
expectedNovelty:
  - cyclePhase
  - expectedReturn
  - phaseAlignment
forbidden:
  - 단일 phase 결과만으로 일반화 금지 — 4 phase 모두 검토.
  - QMJ 점수 ≥ 80 ≠ 절대 매수 신호 — phase context 필수.
failureModes:
  - 사이클 phase 분류가 60-month rolling 등 lookback window 의존.
  - quality 측정 → ROE / 부채비율 / 매출 안정성 weighting 차이.
examples:
  - 삼성전자 QMJ + 사이클 phase
  - 현대차 quality late-cycle 적합도
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

c = dartlab.Company("005930")

# 1. QMJ quality score
qmj = c.quant("qmj")
quality_score = qmj["score"] if isinstance(qmj, dict) else 0
quality_decile = qmj.get("decile", 5) if isinstance(qmj, dict) else 5

# 2. macro cycle phase (early-recovery / mid-expansion / late-cycle / contraction)
cycle = dartlab.macro("cycle", market="KR")
phase = cycle.get("phase", "unknown") if isinstance(cycle, dict) else "unknown"

# 3. macro beta — 회사 sensitivity 60M rolling
beta = dartlab.scan("macroBeta")
rate_beta = beta.get("rateBeta") if isinstance(beta, dict) else 0
fx_beta = beta.get("fxBeta") if isinstance(beta, dict) else 0

# 4. phase-quality alignment 매핑 (학술적 sweep — Frazzini-Pedersen 2014)
PHASE_QUALITY_FIT = {
    "early-recovery": "low",      # low quality outperform
    "mid-expansion": "balanced",
    "late-cycle": "high",         # quality outperform
    "contraction": "high",        # flight to quality
}
expected_winner = PHASE_QUALITY_FIT.get(phase, "balanced")
high_quality = quality_decile >= 8
phase_alignment = (
    (high_quality and expected_winner == "high")
    or (not high_quality and expected_winner == "low")
)

emit_result(
    table=[{
        "stockCode": "005930",
        "qualityScore": round(quality_score, 2),
        "qualityDecile": quality_decile,
        "cyclePhase": phase,
        "rateBeta": round(rate_beta, 3),
        "fxBeta": round(fx_beta, 3),
        "expectedWinner": expected_winner,
        "phaseAlignment": phase_alignment,
    }],
    values={"qualityDecile": quality_decile, "cyclePhase": phase, "phaseAlignment": phase_alignment},
    date="2024-12-31",
    sources=["dartlab://company/scan/quality", "dartlab://company/scan/macroBeta", "dartlab://macro/cycle"],
)
```

## 호출 동작

### 1. 결론 도출

QMJ × 매크로 사이클 phase 적합도 + macroBeta 단정. 예: "QMJ decile 8 + 매크로 phase=확장중반 + macroBeta 0.8 → phaseAlignment=True → quality 후보 outperform 기대 (FPA 2014 학술 결과 기반)."

### 2. 핵심 근거 수집

- QMJ 종합 점수 + decile (Company.quant('qmj'))
- 매크로 cycle phase (dartlab.macro('cycle', market='KR'))
- macroBeta 60M rolling rate / FX (`dartlab.scan("macroBeta")`)
- 학술 매핑: FPA 2014 phase ↔ quality 적합도

### 3. 메커니즘 분석

```
4 source → 결합 판정
   QMJ decile (1~10, 10=top quality)
   cycle phase (저점/회복/확장 초입/확장 중반/정점/하강 enum 5단계)
   macroBeta (low 0~0.5 / mid 0.5~1.0 / high > 1.0)
   ↓
phase ↔ quality 학술 적합 매핑 (FPA 2014)
   확장 초입 + QMJ decile ≥ 8  → outperform 후보 (quality 작동)
   정점/하강 + QMJ decile ≤ 3  → underperform (junk 노출)
   회복 + macroBeta high       → cyclical 후보 (quality 신호 약함)
   ↓
phaseAlignment = True/False
```

QMJ 만으로는 모든 phase 작동 X — 사이클과 결합해야 outperform 신호 신뢰도 ↑. FPA 학술 결과는 정점/하강 phase 의 QMJ 가장 강함.

### 4. 반례·한계

- 매크로 phase 분류 자체 불확실 (현재 측정 신뢰도 60~70%).
- macroBeta 60M rolling — regime shift (COVID/금리 급변) 시 후행.
- QMJ decile 산업별 base 차이 (금융 vs 제조) 보정 없음.
- 학술 결과는 US 시장 1956-2012 — KR 시장 일치성 검증 추가 필요.

### 5. 후속 모니터링

- phaseAlignment True 지속: `recipes.quant.qualityFactor` 로 quality 축 세부 점검.
- macroBeta 급변 (+0.5/-0.5): `recipes.quant.macroBetaFactor` 로 universe 비교 위치 확인.
- phase 전환 (예: 확장 중반 → 정점): `recipes.macro.scenarioDiagram` 으로 시나리오 결합.

## 대표 반환 형태

`pl.DataFrame` — 컬럼:
- `qualityScore : float` · `qualityDecile : int (1~10)`
- `cyclePhase : str` — early-recovery / mid-expansion / late-cycle / contraction
- `rateBeta : float` · `fxBeta : float`
- `expectedWinner : str` — high / low / balanced
- `phaseAlignment : bool`

## 연계 절차

1. 본 recipe → 회사 quality + 사이클 phase 정합성.
2. phaseAlignment = True → `recipes.meta.screen.industryStageScreen` 으로 같은 산업 stage 후행기 종목 추가 발굴.
3. phaseAlignment = False → 다음 phase 전환까지 대기 (timing 신호).
4. universe 검증은 `recipes.macro.quantScenarioBacktest` 로 backtest.
