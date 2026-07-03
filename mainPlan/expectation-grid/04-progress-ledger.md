# 04. 진행원장

## 상태 요약

| 항목 | 상태 |
|---|---|
| 완전 설계 (본 문서군 5종) | ✅ 2026-07-03 v0.1 |
| P0 개념확립 (_attempts) | ✅ 2026-07-03 GO |
| 승인 (운영자 "진행해 승인" 2026-07-03) | ✅ A1/A2/A3 일괄 |
| P1 계약+채점(synth)+원장(simulate) | ✅ 테스트 21 + 게이트 green |
| P2 macro 월 사이클 + HF `expectations/` 라이브 | ✅ 첫 라이브 발행 12행 공개 (2026-07-03) |
| P3 매출 연 사이클 + recordForecast(P9c) + redirect(P9b) | ✅ 표본 3사 라이브 9행 + 이중기록 |
| P4 손익 캐스케이드 (proforma 계보) | ✅ 3사 18행 (OP·NI, FCF=P4b defer) |
| P5 credit 유지확률 + 주가 방향확률 | ✅ 주가 3행 라이브, credit=census 대기(recordGrade 미축적) |
| P6 성적표 터미널 패널 + CI cron | 🔨 패널 구축 중 (UI push=눈검수 게이트) |

## 부산물: 엔진 소유권 버그 수리 (2026-07-03)

전상장사 sweep 실측이 즉시 잡아낸 선재 버그: `_fetchConsensusRevenue`·`Analyst` 가 공유 gather
싱글턴을 빌려 쓰고 close → 한 프로세스 두 번째 회사부터 "client has been closed" 전멸.
수리 + 회귀 테스트(`test_revenueForecastHelpers.py`). 격자가 검증척추로 작동한 첫 사례.

## 라이브 원장 현황 (2026-07-03 HF 공개분)

macro 12 (CPI·기준금리·USDKRW x h1/3/6/12) + revenue 9 (3사 x FY26~28) + earnings 18
(OP·NI x 3사 x 3FY, 매출 계보 봉인) + price 3 (12M 방향확률) = **42행 라이브 + 즉시채점 2행**.
전량 naive 동시 봉인·불변 원장. 첫 자동 채점 = 2026-08 cron (KST 8/6 06:00).

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

## P0 후속 : 졸업 게이트 ③~⑦ 선행 완료 (2026-07-03)

승인 대기 시간에 P1 이식 원본을 _attempts 안에서 완성: `spec.py`(ExpectationSpec/ExpectationScore frozen 계약 + pinball/PIT/coverage/skill 순수수학, stdlib-only) + `ledgerIo.py`(append-only parquet, 중복 id raise) + `demo.py` 전 항목 PASS(계약 가드 · 채점 골든값 · 원장 불변식 · 실데이터 미니 사이클 발행 12/채점 12/error 0, n<24 → verified=False 라벨 강제 확인). 승인 즉시 P1 = 이식 + 미러 테스트 + re-export 만 남음.

## NEXT

1. P6 성적표 패널: 빌드 + Playwright + **운영자 눈검수 후 push** (UI 자동 push 금지)
2. 분기 quarterly cron 첫 전상장사 sweep (workflow_dispatch cycle=quarterly, 실패율 census)
3. 완성 정의 잔여: 라이브 사이클의 "실제값 도착→성적표 갱신" = 2026-08 monthly cron 이 자동 수행
   (기계는 전부 배선됨. 사이클 자체는 backfill 로 실데이터 증명 완료 = P0 131행 채점)
