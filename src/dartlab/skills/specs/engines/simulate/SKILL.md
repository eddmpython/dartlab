---
id: engines.simulate
title: Simulate
kind: curated
scope: builtin
status: observed
category: engines
purpose: Simulate 엔진은 회사 재무와 매크로 프리셋을 결정론 드라이버 시트로 연결해 시나리오별 매출, 마진, FCF, DCF 경로와 근거 감사를 만든다. 트리거 - '시나리오', '스트레스 테스트', '금리 충격', 'what if'.
whenToUse:
  - 시나리오
  - 스트레스 테스트
  - 충격 분석
  - adverse scenario
  - what if
  - 매출 경로
  - 조건부 DCF
inputs:
  - stockCode 또는 회사명
  - scenario
  - horizon
  - asOf
outputs:
  - SimulationResult
  - scenarioName
  - revenuePath
  - marginPath
  - fcfPath
  - dcfPerShare
  - node audit와 inputsHash
  - quality와 data gaps
capabilityRefs:
  - simulate
  - Company.simulate
knowledgeRefs:
  - start.dartlabSkillOs
  - engines.company
  - engines.macro
  - engines.analysis
sourceRefs:
  - dartlab://skills/engines.simulate
requiredEvidence:
  - target
  - scenario
  - assumptions
  - period
  - dateRef
  - valueRef
  - executionRef
  - provenance
expectedOutputs:
  - 선택한 시나리오와 horizon
  - 기준 재무 기간과 데이터 품질
  - base와 stress의 조건부 경로 차이
  - 노드별 provenance와 gap
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
    status: limited
failureModes:
  - dcfPerShare를 목표주가나 미래 보장으로 표현함
  - partial 상태의 None을 0으로 바꿈
  - 서로 다른 asOf 실행의 inputsHash를 직접 비교함
  - 시나리오 가정과 실제 관측값을 구분하지 않음
forbidden:
  - 조건부 시뮬레이션을 예측 확정값으로 표현하지 않는다.
  - partial과 data gap을 숨기거나 0으로 대체하지 않는다.
  - 시나리오, horizon, asOf, provenance 없는 수치를 답변하지 않는다.
examples:
  - 삼성전자 baseline과 adverse 시나리오 비교
  - 금리 충격이 매출과 FCF 경로에 미치는 영향
  - 2024년 기준 3년 조건부 DCF 스트레스 테스트
procedure:
  - ReadSkill 결과의 simulate 또는 Company.simulate 실행 계약을 선택한다.
  - 단일 회사는 EngineCall의 simulate apiRef에 target, scenario, horizon, asOf를 전달한다.
  - 결과의 quality, gaps, latestAsOf, assumptionLedger, node audit를 먼저 확인한다.
  - 비교 질문은 같은 target과 asOf를 유지하고 scenario만 바꿔 각각 실행한다.
  - 값과 기간마다 valueRef, dateRef, executionRef를 답변 문장에 직접 연결한다.
linkedSkills:
  - engines.macro
  - engines.analysis
  - engines.company
  - engines.quant
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-08-03'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - engines.viz.scenarioVisuals
  - engines.viz.tableBackedChart
---

## 엔진 역할

`simulate`는 회사 원자료와 매크로 시나리오를 `macro.path -> rev.path -> proforma -> dcf` 결정론 드라이버 시트로 연결하는 L3 엔진이다. 난수를 쓰지 않으며 같은 target, scenario, asOf는 같은 노드별 `inputsHash`를 만든다. 결과는 미래 확정치가 아니라 입력 가정에 조건부인 변환 결과다.

## 공개 호출 방식

```python
import dartlab

baseline = dartlab.simulate(
    "005930",
    scenario="baseline",
    horizon=3,
    asOf="2024",
)
adverse = dartlab.simulate(
    "005930",
    scenario="adverse",
    horizon=3,
    asOf="2024",
)

c = dartlab.Company("005930")
company_result = c.simulate(scenario="adverse", horizon=3, asOf="2024")
```

설치형 AI 런타임은 다음 canonical 계약을 쓴다.

```json
{
  "apiRef": "simulate",
  "args": {
    "target": "005930",
    "scenario": "adverse",
    "horizon": 3,
    "asOf": "2024"
  }
}
```

## 호출 동작

1. target을 KR Company로 해소하고 지원하지 않는 시장과 시나리오를 차단한다.
2. 회사 snapshot과 매크로 preset을 같은 asOf 경계에 고정한다.
3. DriverSheet를 위상 순서로 평가해 매출, 마진, proforma, FCF, DCF 노드를 계산한다.
4. 각 노드에 provenance, refs, inputsHash, 품질 상태와 gap을 남긴다.
5. base와 stress 비교는 target, horizon, asOf를 동일하게 유지하고 scenario만 변경한다.

`partial`은 실패 값을 0으로 채운 상태가 아니다. 필요한 leaf가 없어서 해당 값이 `None`인 정직한 결손 상태다.

## 대표 반환 형태

```text
SimulationResult
  scenarioName: str
  horizon: int
  latestAsOf: str | None
  revenuePath: list[float | None]
  marginPath: list[float | None]
  fcfPath: list[float | None]
  dcfPerShare: float | None
  quality: ok | partial
  gaps: list
  audit: list[NodeAudit]
  assumptionLedger: dict
  lensProducts: dict
```

답변은 시나리오 이름과 가정, 기준 기간, 조건부 값, 노드 근거를 함께 제시한다. `dcfPerShare`는 해당 시나리오 가정 아래의 계산값이며 목표주가나 성과 보장이 아니다.

## 기본 검증

- `quality`, `gaps`, `latestAsOf`, `inputsHash`가 함께 존재하는지 확인한다.
- 답변에 인용한 경로와 DCF 수치는 해당 `valueRef`, `dateRef`, `executionRef`와 직접 연결한다.
- base와 stress 비교는 target, horizon, asOf가 동일한지 확인한다.
- `partial`의 결손값을 0으로 바꾸지 않고 제한과 필요한 입력을 명시한다.

## 기대 원장과 거시 상태

- expectation ledger (`dartlab.simulate.expectationCycle`, 주기 실행 `.github/workflows/expectationCycle.yml`) 는 관측값, prior, 검증 상태를 분리 보관한다. 표본이 부족하면 검증된 것처럼 표시하지 않는다.
- 거시 시뮬레이션은 regime transition 과 결과 container 를 공통 타입으로 유지한다. 시나리오 가정과 실제 관측값을 같은 필드에 섞지 않는다.
