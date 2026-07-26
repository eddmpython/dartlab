# v1.0.0 준비도 전수 검토. 판정 원장

> 이 문서는 판정과 근거만 담는다. 선언은 다루지 않는다.
> 게이트 정의 SSOT = memory `release_gate`. 그 규칙대로 본 체크리스트는 **불가 판정 도구**이고
> 가능 선언 트리거가 아니다. 전부 통과해도 "기준 충족, 선언 대기" 이상은 적지 않는다.

## 진행 방식

계층 아래에서 위로 순차 검토한다. L0 core -> L1 gather, providers -> L1.5 scan, frame, synth,
reference -> L2 analysis, macro, quant, industry, credit -> L2.5 data -> L3 story, simulate ->
L4 ai, mcp. 아래층 결함이 위층 전부를 오염시키므로 순서를 지킨다.

각 계층은 네 기준으로 본다. 혁신성, 완성도, 모듈화와 구조화, 클린코드. 미달이면 리팩터링을
검토하고 추진한다.

## 정량 판정 (2026-07-27 실측)

체크리스트 여섯 중 셋을 지금 잴 수 있다. 셋 다 미달이다.

| 항목 | 기준 | 실측 | 판정 |
|---|---|---|---|
| Q2 헬퍼 파일 수 | 6 이하 | **16** | 미달 |
| Q3 F 등급 함수 (복잡도 31+) | 150 이하 | **163** | 미달 |
| Q5 공개 함수가 전부 미테스트인 파일 | 0 | **193** | 미달 |

Q5 는 원래 "0% coverage 파일 0 개" 다. 커버리지 실행 대신 공개 함수 전부가 테스트 참조 0 인
파일로 근사했다. 실제 0% 보다 좁은 집합이라 실제 미달 폭은 이 숫자보다 크다.

Q1(routing SSOT 통합), Q4(realData 30% 단축), Q6(외부 venv 종합 smoke)은 별도 실행이 필요해
아직 재지 않았다.

### 세부

**Q2 헬퍼 16 개.** analysis 다섯, valuation 둘, credit, gather, macro 둘, forecast, insight 등.
게이트가 요구하는 것은 개수 줄이기가 아니라 소비자가 하나뿐인 헬퍼를 소비 파일로 흡수하고
중복 formatter, validator 를 한 곳으로 모으는 것이다.

**Q3 F 등급 163 개.** 최악은 `synth/strategyRules.py::evaluateStrategies` 164,
`analysis/forecast/_revenueForecastCore.py::forecastRevenue` 149, `simulate/world.py::_checkInputs`
124 다. E 등급(21~30)이 296 개, C~D(11~20)가 1,216 개다.

**Q5 미테스트 파일 193 개.** quant 49, analysis 28, scan 19, macro 19, ai 18, core 14 다.
공개 함수가 가장 많은 미테스트 파일은 `core/indicators/volume.py` 11 개다. 여기가 L0 라서
가장 먼저 닫아야 할 자리다.

## 계층별 판정

| 계층 | 상태 |
|---|---|
| L0 core | 검토 착수 |
| L1 gather, providers | 대기 |
| L1.5 scan, frame, synth, reference | 대기 |
| L2 analysis, macro, quant, industry, credit | 대기 |
| L2.5 data | 대기 |
| L3 story, simulate | 대기 |
| L4 ai, mcp | 대기 |

## 현재 판정

**v1.0.0 선언 불가.** 정량 세 항목이 미달이고 계층 검토는 L0 부터 이제 시작한다.
