---
id: engines.viz.scenarioVisuals
title: Viz - 시나리오·민감도 시각화
kind: curated
scope: builtin
status: observed
category: engines
purpose: 매크로 충격, valuation 민감도, stress test 결과를 `heatmap`, Mermaid graph 로 표현해 충격 전파와 민감도를 분리해서 보여준다.
whenToUse:
  - 시나리오 분석
  - stress matrix
  - 민감도 heatmap
  - 충격 전파 diagram
inputs:
  - scenario score
  - sensitivity grid
  - shock/transmission/company impact nodes
  - evidenceBinding
outputs:
  - chartType heatmap ChartSpec
  - Mermaid graph LR
toolRefs:
  - EngineCall
  - RunPython
  - CompileVisual
knowledgeRefs:
  - engines.viz
  - engines.macro
  - engines.analysis.valuationBand
sourceRefs:
  - dartlab://skills/engines.viz.scenarioVisuals
requiredEvidence:
  - scenario
  - assumption
  - metric
  - evidenceBinding
  - executionRef
  - sourceRef
expectedOutputs:
  - scenario visual spec
  - stress matrix
  - mechanism diagram
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
failureModes:
  - 단일 숫자 결론을 heatmap 으로 과장함
  - Mermaid 노드가 많아져 인과가 읽히지 않음
  - 가정 grid 없이 민감도 chart 를 만듦
forbidden:
  - assumption 없는 scenario chart 금지
  - Mermaid 8노드 초과 금지
  - 충격 방향과 회사 영향의 부호를 검산하지 않은 diagram 금지
examples:
  - 금리 +100bp valuation sensitivity
  - 환율 충격 → 매출/마진 전파 Mermaid
linkedSkills:
  - engines.viz
  - engines.macro
  - engines.analysis.valuationBand
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-11-27'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## 절차

1. 충격 변수, 전파 경로, 회사 metric 을 분리한다.
2. grid 가 있으면 `specSensitivityHeatmap(grid)` 를 우선한다.
3. 인과 설명은 Mermaid `graph LR` 로 6~8노드 이하만 작성한다.
4. 가정이 부족하면 chart 대신 scenario table 로 낮춘다.

6막 radar generator(`specSixActRadar`)는 2026-07-10 에 지웠다. 6막 점수 차트는 지금 만들 수 없다.

## 공개 호출 방식

```python
from dartlab.viz.generators import specSensitivityHeatmap

heatmap = specSensitivityHeatmap(grid)
```

## 호출 동작

- 입력 view 또는 rows 를 검산 가능한 ChartSpec 으로 변환한다.
- `evidenceBinding` 또는 `evidenceIds` 가 없으면 emit 하지 않는다.
- 데이터가 부족하면 값을 추정하지 않고 표, coverage note, 또는 bullet path 로 낮춘다.

## 대표 반환 형태

- `dict` ChartSpec: `chartType`, `title`, `series` 또는 `data`, `categories`, `evidenceBinding`, `meta`.
- Mermaid 계열은 diagram source 와 node/edge evidence refs 를 함께 남긴다.

## 기본 검증

- 모든 scenario visual 은 가정값과 결과값을 함께 노출한다.
- Mermaid diagram 은 수치 임계 또는 방향성을 노드 라벨에 넣는다.
