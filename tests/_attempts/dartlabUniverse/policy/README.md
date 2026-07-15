# Policy attempts

> 상태: 계획 확정, 미실행
> 책임: public source별 재배포와 lens 가용성을 fail-closed receipt로 검증한다.

## 가설

source별 `RedistributionReceipt`와 환경별 `LensAvailability`를 projection admission에 넣으면 dataset 또는 engine 전체를 뭉뚱그린 공개 판단을 피할 수 있다.

## 실행 순서

1. U0-P02: source별 allowedFields, attribution, policyVersion을 센서스한다.
2. U0-L01: scalar, series, table, ranking, distribution, scenario archetype과 public, local 가용성을 센서스한다.
3. public projection fixture에 unknown, localOnly, expired receipt를 주입한다.

## 합격

- public mark의 redistribution receipt coverage 100%
- unknown 및 localOnly false accept 0
- lens별 unit, coverage, missing policy 100%
- public에서 unavailable lens가 실행된 것처럼 보이는 사례 0

## 기각

- dataset card 하나로 모든 upstream field를 승인
- 금지 source에서 나온 파생값을 lineage 검사 없이 public 승격
- client에서 unavailable engine을 임의 재계산
- missing lens 결과를 0 또는 빈 성공으로 표시

## 산출물 예정

- `redistributionReceiptProbe.py`
- `testRedistributionReceiptProbe.py`
- `lensAvailabilityProbe.py`
- `testLensAvailabilityProbe.py`
- source와 lens reviewed fixture

정책 결론은 법률 자문을 대체하지 않는다. 불명확하면 public에서 차단하고 운영자 검토 대상으로 남긴다.
