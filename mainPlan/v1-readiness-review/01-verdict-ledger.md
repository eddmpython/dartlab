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

## L0 core 판정 (2026-07-27)

전문 에이전트 둘이 구조와 코드품질을 나눠 훑었다. **둘 다 미달 판정**이다.

구조 쪽 근거는 이 계층이 자기 기반 추상의 두 번째 사본을 만들고 첫 번째를 끝내 지우지
않았다는 것이다. `SecretStore` 가 둘, plugin 발견 체계가 둘(같은 entry point group 을
각자 읽는다), `getDefaultProvider` 가 둘, `CredentialStatus` 가 둘, Altman Z 가 둘이었다.
호출자 0 인 코드가 약 2,000 줄로 계층의 9% 다.

코드품질 쪽 근거는 L0 이 "값 없음" 을 그럴듯한 숫자로 바꿔 내보낸다는 것이다. 예외가
아니라 잘못된 값으로 나타나기 때문에 위층에서는 원인을 볼 수 없다.

### 닫은 것

| 결함 | 증상 | 상태 |
|---|---|---|
| `resolveLatestPeriod` | 이 모듈이 만드는 표준형 '2024-Q1' 을 못 읽어 최신 기간이 실행마다 달랐다 | 수정 |
| `isClose` | NaN, None, 문자열이 전부 통과. 값 빠진 대차대조표가 항등식 검증을 통과 | 수정 |
| `toDecimal` | 문서는 ValueError 를 약속하는데 다른 예외가 샜다 | 수정 |
| `vsma` 결측 오염 | %D, KDJ 세 출력, stochRsi %D 가 전 구간 NaN. 계산이 죽어 있었다 | 수정 |
| 자본잠식 비율 | 적자 기업 ROE 가 +200% 로 수익성 랭킹 상단에 올랐다 | 수정 |
| CCC 판정 | 재고 0 인 회사가 미산출로 떨어지고, 시점과 시계열 경로가 서로 다른 답 | 수정 |
| 신선도 확인 실패 | 실패를 "확인했고 최신" 으로 기록해 침묵이 스스로 연장 | 수정 |
| plugin 메타 | 보강한 kind, schema 가 버려져 조회 표면이 언제나 비어 있었다 | 수정 |
| `help` 안내 경로 | `dartlab.plugins.listPlugins` 가 실재하지 않아 AttributeError | 수정 |
| `core/secrets.py` | 구현체와 끝내 만나지 못한 추상. 호출자 0 | 삭제 |

미테스트였던 L0 모듈 여섯에 회귀를 세웠다. 거래량 지표 11 함수, 가격 지표 3, DataFrame
판정 2, TTL 캐시, 기간 표기, 십진 변환이다.

### 남긴 것과 이유

`financeDocAccessor` seam 은 등록 호출이 0 이라 영원히 None 을 돌려주고 소비자 여섯의
첫 분기가 죽어 있다. 동작은 이미 동일하므로 정리 대상이지 결함이 아니다.

두 plugin 체계가 같은 entry point group 을 각자 읽는 문제는 외부 플러그인 계약을 바꾸는
일이라 운영자 결정 사안이다.

`core/schemas.py` 의 Pandera 클래스 47 개(약 700 줄)가 호출자 0 이지만, 삭제하지 않기로
한 기존 결정이 `mainPlan/innovation-stack-research/tech/pandera.md` 에 있다.

`.dartlab.yml` 프로젝트 설정은 `loadProjectConfig` 호출자가 0 이라 문서화된 기능이 아예
동작하지 않는다. 배선하든 지우든 사용자에게 보이는 변화라 운영자 결정 사안이다.

### 정량 재측정

수정 뒤에도 Q2 헬퍼 16(기준 6), Q3 F 등급 163(기준 150)은 그대로다. 이번에 닫은 것은
정확성 결함이지 복잡도나 헬퍼 정리가 아니다.

**L0 판정: 미달.** 정확성 결함 열 건을 닫았으나 구조 기준(SSOT 중복, 호출자 0 코드)과
정량 기준 둘이 남아 있다.
