# DartLab 내부 아키텍처

이 문서는 기여자와 엔진 개발자를 위한 내부 구조 설명이다. 사용자는 내부 레이어를 알지 않아도 `Company`, 다섯 분석 렌즈, `Story`, `Simulate`, `Ask`로 전체 조사 흐름을 완료할 수 있다.

## 제품 구조와 코드 구조

제품은 다음 흐름으로 설명한다.

```text
비교 가능한 공시 데이터 -> 다섯 분석 렌즈 -> 판단 워크플로
```

코드는 순환 import와 책임 혼합을 막기 위해 단방향 레이어를 유지한다.

| 내부 구간 | 주요 폴더 | 책임 |
|---|---|---|
| L0 | `core` | 타입, 오류, 메모리, 공통 실행 규율 |
| L1 | `gather`, `providers` | DART, EDGAR, 가격, 매크로 원천 접근 |
| L1.5 | `scan`, `frame`, `synth`, `reference` | 횡단 비교, 정규화, 공유 계약과 레지스트리 |
| L2 | `analysis`, `credit`, `industry`, `quant`, `macro` | 서로 독립적인 다섯 분석 렌즈 |
| L2.5 | `dataHub` | L1부터 L2까지의 데이터 제품을 catalog, query, PIT와 원격 실행 계약으로 연합 |
| L3 | `story`, `simulate` | 하위 렌즈 결과 조립과 결정론 시나리오 실행 |
| L4 | `ai`, `mcp`, `channel` | 질문, 검증, 외부 전달 |

레이어 번호는 import 방향을 지키는 개발 규율이지 제품 등급이나 사용자 학습 순서가 아니다.

## 다섯 렌즈의 격리

`analysis`, `credit`, `industry`, `quant`, `macro`는 각자 계산과 의미 검증을 소유한다. 형제 렌즈를 직접 import해 종합 판단을 만들지 않는다. 다섯 렌즈는 대표 축 결과에 공통 `product` 외피를 추가하지만 엔진별 기존 결과와 세부 축은 그대로 보존한다.

공통 계약은 `src/dartlab/synth/lensContract.py`에 있다. 계약은 구조와 시간 경계만 검증하며 엔진별 점수나 의미를 대신 계산하지 않는다.

## 조립 책임

`story`는 필요한 렌즈의 `product`를 수집하고 같은 Company 세션의 원본 결과를 재사용한다. 공개 Story JSON과 ReportModel에는 제품 계약만 노출하며 원본 계산 결과는 내부 재사용용으로 남긴다. `simulate`는 렌즈 가정과 시나리오를 가정 원장에 보존하지만 결정론 DriverSheet를 몰래 덮어쓰지 않는다. AI는 제품 결론과 시간 경계를 `valueRef`, `dateRef`로 인용한다.

## 핵심 가드

- 형제 렌즈 간 비승인 import 금지
- Story 자체 숫자 계산 금지
- missing, blocked, stale을 0이나 정상으로 변환 금지
- 공통 종합점수 금지
- UI에서 Python 렌즈 의미 재구현 금지
- 같은 target과 period의 Company fetch 재사용

세부 규율과 검사 명령은 [CLAUDE.md](CLAUDE.md)와 [Skill OS](src/dartlab/skills/specs/)를 따른다.
