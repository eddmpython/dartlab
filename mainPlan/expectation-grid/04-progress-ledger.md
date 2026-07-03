# 04. 진행원장

## 상태 요약

| 항목 | 상태 |
|---|---|
| 완전 설계 (본 문서군 5종) | ✅ 2026-07-03 v0.1 |
| P0 개념확립 (_attempts) | ✅ 2026-07-03 GO (아래 실측) |
| 승인 3건 (00 §9 A1/A2/A3) | ⏳ 운영자 대기 |
| P1~P6 | ⏳ 승인 후 무중단 |

## P0 실측 결과 (2026-07-03, `tests/_attempts/expectationGrid/probe.py`)

KR macro 3변수 x h=1/3/6, 2025-01~2026-04 매월 asOf backfill(issuedLive=False). 발행 144 · 채점 131 · skip 0. 사이클(발행→봉인→join→채점→집계) 실데이터 1회 완주 = **GO**.

| 변수 | h=1 skill | h=3 skill | h=6 skill | cov90 (h1/3/6) |
|---|---|---|---|---|
| 소비자물가 | +0.099 | -0.035 | +0.107 | 1.00/1.00/1.00 |
| 기준금리 | -0.275 | -0.144 | -0.333 | 0.88/1.00/1.00 |
| 원/달러 | -0.358 | -0.752 | -0.934 | 0.88/1.00/1.00 |

판독: ①채점기 건전성 방증 = 교과서 재현(환율·정책금리는 RW 를 못 이김, Meese-Rogoff) ②물가만 소폭 양의 skill = "예측 가능 변수 선별"이 실제로 작동 ③cov90≈1.00 = fan over-dispersed(과소확신) 실측 ④n<24 라 전량 '미검증' 라벨 대상, 성과 주장 아님. 시사점: 시뮬레이터에서 환율·기준금리는 예측이 아니라 가정 토글이 정직한 기본값이라는 첫 데이터 근거.

## 결정 기록

- 2026-07-03: 운영자 goal 접수. scenario-simulator 문서군(00/01/02/03/09/04) + 코드 자산(simulate·macro/simulate·analysis/forecast·credit·hfUpload·origins) 실측 정찰 완료.
- 2026-07-03: goal 대비 정정 2건 확정(00 §1b) : ①원장 기록자 = simulate 수집형(L2→L2.5 import 불가 실측) ②연속 채점 = 03 §4.4 정본(coverage/PIT/CRPS/skill), Brier 는 이진 전용.
- 2026-07-03: 이중 기록 방지 결정(01 §5) : forwardTest redirect(A2) · credit adapter 병행 발행 · driverPanel(models)은 범위 밖.
- 2026-07-03: backfill 정직 규약 확정(02 §5) : `issuedLive=False` 영구 구분, 공개 성적 혼합 금지.

## NEXT

1. P0 데모 실측 → 결과 수치 본 원장 + _attempts README 박제
2. 운영자 승인(A1/A2/A3) → P1 착수
