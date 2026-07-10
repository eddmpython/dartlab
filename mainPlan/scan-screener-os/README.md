# scan 스크리너 OS

> scan 을 데이터 공급기에서 **스크리너로 완전히 세우는** 프로그램. 폴더 SSOT.
> 옛 이름 `scan-composable-query` 승계 (2026-07-10). 컴포저블 쿼리는 이 프로그램의 첫 세 단계였다.

## 라우팅

| 문서 | 내용 | 상태 |
|---|---|---|
| **`04-screener-os-prd.md`** | **현행 SSOT 머리.** 판정격자 개념 + universe/asOf/rank/explain + walk 백테스트. P1~P5 | 설계 완료, 승인 대기 |
| `00-prd.md` | 컴포저블 쿼리 (define AST, 시계열, 업종상대, screens/*.json, 왓처 구독) | Phase 1~3 완료. Phase 4 는 04 의 P5 로 흡수 |
| `01-phase4-ui-plan.md` | 프론트가 spec 을 소비하는 계획 | 04 의 P5 입력 |
| `02-coverage-audit.md` | providers/gather/panel 대비 scan 필드 커버리지 감사. 27 갭 3 버킷 | 04 의 P2 (축 전수 등재) 입력 |
| `03-narrative-grid-invention.md` | 서술표 전천후 격자 추출기 (수주잔고/가동률) | 별도 트랙. `narrativeMetric` 축으로 착지 |

## 한 줄

스크리너는 필터의 곱이 아니라 **조건 x 종목 판정격자**다. 통과 목록은 그 격자의 요약 하나일 뿐이고, 근접후보 / 깔때기 / 결측정직 / 랭킹 / 백테스트는 전부 같은 격자의 파생이다.

## 실측 기반 (2026-07-10)

- `universe` 인자를 받는 scan 축: **0 / 27** (SKILL.md 는 계약이라 문서화. 호출하면 TypeError)
- screen 에 노출된 데이터축: **5 / 22** (`_COMPOSITE_AXIS_FIELDS` 11 필드, 손 선별)
- 연간보고서 공시 지연 중앙값: **78 일** (오늘 데이터로 과거를 판정하면 look-ahead)
- 정정공시 판본 중복: **0 %** (8,686,240 그룹 전수. `filedAt <= asOf` 에 예외 없음)
- 프론트 스크리닝 중복 구현: 약 **2,800 LOC** (python spec 을 아무도 소비하지 않음)
