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
  - scenario (프리셋 id 또는 사용자 시나리오 dict)
  - overrides (드라이버 override dict)
  - horizon
  - asOf
outputs:
  - SimulationResult
  - scenarioName
  - scenarioKind와 scenarioBase
  - macroPaths
  - revenuePath
  - marginPath
  - fcfPath
  - waccPath
  - dcfPerShare
  - node audit와 inputsHash
  - quality와 data gaps
  - StrategyComparison (strategies 축)
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
  - 사용자 시나리오가 바꾼 거시 경로와 override, 그 값이 가정 원장에 남았는지
  - strategies 축의 프리셋별 리더, 리더 역전, 취약 프리셋, 추천이 닫힌 이유
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
  - strategies 축의 프리셋 리더를 투자 추천이나 경영 권고로 표현함
  - partial 상태의 None을 0으로 바꿈
  - 서로 다른 asOf 실행의 inputsHash를 직접 비교함
  - 시나리오 가정과 실제 관측값을 구분하지 않음
  - 사용자 시나리오나 override를 프리셋 결과처럼 표현함
  - 금리를 소수(0.035)로 넣는 등 단위를 틀린 채 범위 오류를 우회하려 함
forbidden:
  - 조건부 시뮬레이션을 예측 확정값으로 표현하지 않는다.
  - partial과 data gap을 숨기거나 0으로 대체하지 않는다.
  - 시나리오, horizon, asOf, provenance 없는 수치를 답변하지 않는다.
examples:
  - 삼성전자 baseline과 adverse 시나리오 비교
  - 금리 충격이 매출과 FCF 경로에 미치는 영향
  - 2024년 기준 3년 조건부 DCF 스트레스 테스트
  - 삼성전자 유지, 증설, 부채 축소 전략이 프리셋마다 어떻게 갈리는지 비교
  - 기준금리를 5%로 올리면 삼성전자 WACC와 주당 DCF가 어떻게 바뀌는지
  - WACC를 12%로 두고 5년 저성장 경로를 직접 넣어 보기
procedure:
  - ReadSkill 결과의 simulate 또는 Company.simulate 실행 계약을 선택한다.
  - 단일 회사는 EngineCall의 simulate apiRef에 target, scenario, horizon, asOf를 전달한다.
  - 결과의 quality, gaps, latestAsOf, assumptionLedger, node audit를 먼저 확인한다.
  - 비교 질문은 같은 target과 asOf를 유지하고 scenario만 바꿔 각각 실행한다.
  - 사용자가 직접 가정을 말하면 프리셋에 끼워 맞추지 않고 scenario dict나 overrides로 넘긴다.
  - 값과 기간마다 valueRef, dateRef, executionRef를 답변 문장에 직접 연결한다.
linkedSkills:
  - engines.macro
  - engines.analysis
  - engines.company
  - engines.quant
source:
  type: manual_skill
  format: markdown
lastUpdated: '2026-09-30'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
visualRefs:
  - engines.viz.scenarioVisuals
  - engines.viz.tableBackedChart
---

## 엔진 역할

`simulate`는 회사 원자료와 매크로 시나리오를 결정론 드라이버 시트로 연결하는 L3 엔진이다. 난수를 쓰지 않으며 같은 target, scenario, asOf는 같은 노드별 `inputsHash`를 만든다. 결과는 미래 확정치가 아니라 입력 가정에 조건부인 변환 결과다.

드라이버 시트는 매크로 변수와 전달 채널마다 노드 하나를 둔다. 노드 감사에서 어느 입력이 어느 숫자를 움직였는지 그대로 읽힌다.

| 노드 | 의존 | 역할 |
|---|---|---|
| `macro.path`, `macro.rate`, `macro.fx` | 없음 | 프리셋 GDP, 기준금리, 원달러 경로 |
| `rev.path` | GDP, 환율 | 매출 채널 |
| `margin.path` | GDP, 금리 | 영업이익률 채널 (금리는 금융업 NIM만) |
| `wacc.path` | 금리 | 할인율 채널 (금리 변화의 절반) |
| `proforma` | 매출, 마진 | 성장 경로와 영업이익률 충격으로 3표 추정 |
| `dcf` | proforma, WACC | 연도별 시나리오 WACC로 FCFF 할인 |

금리 충격은 WACC 경로를 통해 주당 DCF를 움직인다. 마진 경로는 proforma 영업이익에 충격으로 반영되어 FCF를 움직인다.

## 사용자 가정: 시나리오 경로와 드라이버 override

프리셋 다섯 개 밖의 가정은 사용자가 직접 넣는다. `scenario`, `strategies` 두 축 모두 경로와 드라이버 변경을 받으며, 각 축에서 실제 계산에 쓰는 값만 허용한다.

- 사용자 시나리오: `scenario`에 dict를 넘긴다. 키는 `name`, `base`, `gdp`, `rate`, `fx`다. `base` 프리셋(기본 `baseline`)의 경로 중 준 변수만 바꾼다. GDP 성장률과 기준금리는 %, 환율은 원달러 수준이다. 세 경로를 모두 주면 프리셋 길이 3년을 넘어 10년까지 펼칠 수 있다.
- 드라이버 override: `overrides`에 dict를 넘긴다. `baseWacc`, `terminalGrowth`, `baseMargin`은 %, `revenueToGdp`, `revenueToFx`, `marginToGdp`, `nimToRate`는 업종 탄성 단위다. 정한 값이 대신한 기본값 가정은 `assumptions`에서 빠진다.
- 검증: 모르는 키, 숫자가 아닌 값, 범위 밖 값(금리 0~30%, GDP -30~30%, 환율 100~10,000 등), horizon보다 짧은 경로, 프리셋과 같은 `name`은 실행 전에 `AssumptionInputError`로 실패한다. 조용히 자르거나 보정하지 않는다.
- 추적: 결과의 `scenarioKind`는 `user`, `scenarioBase`는 바꾸지 않은 경로의 출처 프리셋이다. `macroPaths`는 실제로 쓴 세 경로다. 바꾼 root node는 provenance `user:{name}`, ref `user:scenario/{name}#{variable}`을 남기고, `assumptionLedger`에 `source="user"` 행이 `appliedToDriverSheet=True`로 남는다. 바꾸지 않은 root는 같은 프리셋 node와 inputsHash가 같다.

```python
shock = dartlab.simulate("005930", scenario={"name": "rateShock", "rate": [5.0, 5.5, 5.5]})
shock.scenarioKind, shock.macroPaths["rate"], shock.waccPath, shock.dcfPerShare

slow = dartlab.simulate(
    "005930",
    scenario={"name": "slowDecade", "gdp": [1.0] * 5, "rate": [3.0] * 5, "fx": [1450.0] * 5},
    horizon=5,
    overrides={"baseWacc": 12.0, "terminalGrowth": 2.0},
)
```

2026-09-29 삼성전자 실측에서 baseline은 WACC 13%, 주당 DCF 79,783원이었다. 기준금리를 5.0, 5.5, 5.5%로 올린 사용자 시나리오는 매출 경로를 그대로 두고 WACC를 14.25~14.5%로 올려 주당 DCF를 71,240원으로 낮췄다. 모두 가정에 조건부인 계산값이다.

## strategies 축: 조건부 전략 비교

`dartlab.simulate("strategies", code)` 또는 `Company.simulate("strategies")`는 회사의 현재 재무 상태에서 전략 세 개를 모든 KR 프리셋의 같은 경로 위에 굴려 비교한다.

`scenario`를 지정하면 해당 프리셋 또는 사용자 시나리오 하나에서 전략을 비교한다. 사용자 경로 세 개를 모두 주면 최대 10년까지 실행한다. `overrides`는 기준 영업이익률과 업종 탄성을 바꾸며, 할인 계산에만 쓰는 `baseWacc`, `terminalGrowth`는 이 축에서 거부한다. 비교 기준은 마지막 해 순현금이기 때문이다. 각 case는 `scenarioKind`, `scenarioBase`, `macroPaths`를 보존하고, 사용자 입력은 `assumptionLedger`에 `source="user"`, `appliedToFinancialWorld=True`로 남는다.

- 전략: `hold`(감가상각만큼 유지 투자), `expand`(유지 투자의 1.5배), `deleverage`(현재 부채의 절반을 기간에 나눠 상환). 모두 명시 가정이다.
- 경로: 프리셋의 GDP, 금리, 환율을 시나리오 축과 같은 업종 탄성으로 연간 수요, 마진, 차입금리 충격으로 옮긴다.
- 실행: 감사된 재무 세계 실행기가 매년 회계 항등식을 닫으며 전개한다. 현금 음수와 부채 한도는 제약 위반으로 기록한다.
- 판정: 프리셋마다 마지막 해 순현금이 가장 큰 실행 가능 전략을 리더로 두고, 2위와의 격차, 순현금과 부채의 Pareto 집합을 함께 낸다. `leaderReversal`, `reversalCases`, `fragileCase`가 리더가 뒤집히는 곳과 결정이 가장 쉽게 뒤집히는 프리셋을 가리킨다.
- 한계: 결과는 항상 `conditionalOnly`, `recommendation`은 None이다. 전이 계수와 전략이 명시 가정이고 정책 평가 인증서가 없기 때문이며 `blockedReasons`에 그대로 남는다. AI 런타임 EngineCall 연결은 아직 없고 Python과 Company 경로에서 먼저 연다.

```python
comparison = dartlab.simulate("strategies", "005930", horizon=3)
comparison.leaderByCase, comparison.fragileCase, comparison.blockedReasons

custom = dartlab.simulate(
    "strategies", "005930",
    scenario={"name": "highRate", "rate": [5.0, 5.5, 5.5]},
    overrides={"baseMargin": 20.0},
)
custom.cases[0].outcomes, custom.assumptionLedger
```

## 내부 재무 이력 검증의 경계

EDGAR 검증은 최초 공시에서 확인되는 분기 재무 상태와 그때 알려진 비율을 고정하고, 다음 분기의 공시된 투자·차입·상환과 실제 재무 결과를 기존 재무 실행기와 모델 비교기로 연결한다. 공시 누계는 같은 태그·회계연도 시작·인접 기간을 확인한 뒤 차감하며, 관측된 0과 항목 부재를 구분한다. 성공·결손 시점과 항목별 공시 근거는 표로 보존한다.

이 경로는 공개 축에 포함되지 않은 내부 검증이다. 실제 매출을 수요 대용값으로 쓰고 공시된 행동을 사후 주입하므로 예측 성과나 투자 전략 백테스트가 아니다. 감가상각·상각 합계를 설비 감가상각의 대용값으로 쓰며, 장기차입과 순기업어음 이외의 자금 조달, 자사주·유가증권·환율 효과는 현재 모델 밖이다. 차이는 오차로 남기고 잔액을 맞추는 값으로 메우지 않는다. 모델 비교는 직전 상태 유지 기준을 포함하며, 표본 부족이나 기준 대비 열세를 숨기지 않고 인증·추천으로 승격하지 않는다.

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

사용자 가정도 같은 계약에 JSON 객체로 넘긴다.

```json
{
  "apiRef": "simulate",
  "args": {
    "target": "005930",
    "scenario": {"name": "rateShock", "base": "baseline", "rate": [5.0, 5.5, 5.5]},
    "overrides": {"baseWacc": 12.0},
    "horizon": 3
  }
}
```

## 호출 동작

1. target을 KR Company로 해소하고 지원하지 않는 시장과 시나리오를 차단한다.
2. 회사 snapshot과 매크로 preset을 같은 asOf 경계에 고정한다.
3. DriverSheet를 위상 순서로 평가해 매크로, 매출, 마진, WACC, proforma, DCF 노드를 계산한다.
4. 각 노드에 provenance, refs, inputsHash, 품질 상태와 gap을 남긴다.
5. base와 stress 비교는 target, horizon, asOf를 동일하게 유지하고 scenario만 변경한다.

`partial`은 실패 값을 0으로 채운 상태가 아니다. 필요한 leaf가 없어서 해당 값이 `None`인 정직한 결손 상태다.

## 대표 반환 형태

```text
SimulationResult
  scenarioName: str
  scenarioKind: preset | user
  scenarioBase: str
  macroPaths: dict[gdp | rate | fx, list[float]]
  horizon: int
  latestAsOf: str | None
  revenuePath: list[float | None]
  marginPath: list[float | None]
  fcfPath: list[float | None]
  waccPath: list[float | None]
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
