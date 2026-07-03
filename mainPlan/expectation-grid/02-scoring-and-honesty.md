# 02. 채점 수학 + 정직 규약

> 정본 관계: 채점 명세의 원 SSOT 는 시뮬 03 §4.4 (G16). 본 문서는 그 명세를 Expectation Grid 원장에 적용하는 구속 규약이다. 수치 임계는 시뮬 02:493~497 잠정값을 상속하며, 여기서 재발명하지 않는다.

## 1. 연속 변수 채점 (macro·매출·손익)

발행 = 분위 5점 (p5/p25/p50/p75/p95). 채점 행마다:

- **coverageHit90** : actual ∈ [p5, p95]. 집계 목표 0.85~0.95 (미달=과신, 초과=과소확신, 시뮬 03:211 대칭 판정)
- **coverageHit50** : actual ∈ [p25, p75] (보조)
- **PIT** : u = F(actual), 분위 5점 선형보간. 집계 시 10-bin 히스토그램 + KS 균등성 p>0.1 (시뮬 03:213)
- **CRPS 근사** : pinball loss 를 5분위 평균 (시뮬 03:215)
- **skill** : 1 - CRPS_model / CRPS_baseline. baseline 은 봉인된 것 중 **가장 센 것**(min CRPS) 대비 (시뮬 03:265 불공정 비교 차단). skill≤0 = 예측력 없음

## 2. 이진 변수 채점 (방향·등급 이동)

- **Brier** : (prob - outcome)², 집계 = synth 승격된 calibrationMetrics (reliability bins·brierSkill)
- held-out 승격 임계(시뮬 02:494): direction Brier < 0.25

## 3. naive 기준선 (발행 시 동시 봉인)

시뮬 03 §4.4-baseline 표 상속:

| 대상 | baseline | 정의 |
|---|---|---|
| macro 시계열 | random-walk | x_{t+h} ~ x_t, 분산 = historical vol scaling |
| macro·펀더멘털 | persistence | x_{t+h} ~ x_t |
| 펀더멘털(분기) | seasonal-naive | x_{t+h} ~ x_{t-4+h} (T≥5분기, 미달 시 persistence 폴백) |

봉인 이유: baseline 은 결정론이라 사후 재구성이 가능하지만, 발행 행에 함께 넣어야 "비교 대상을 사후에 골랐다"는 의심 자체가 성립하지 않는다. 컨센서스 baseline(외부 데이터)은 v1 제외(수급 별도 판단).

## 4. 표본 게이트 (변수별 최소 N, 미달 = '미검증' 라벨 강제)

| 변수군 | 채점 주기 | 캘리브레이션 활성 최소 표본 | 근거 |
|---|---|---|---|
| macro 3변수 | 월 | 변수·horizon 별 N≥24 | 시뮬 03:233 (N≥8분기) 의 월 환산 + KS 최소 표본 |
| 매출·손익 | 분기 | 회사 단위 금지, **pooled-panel 섹터 횡단** N≥40 | 시뮬 03:231 (T<40 회사 단위 금지) 그대로 |
| credit·방향 | 분기 | pooled N≥40 | 동일 |

미달 기간의 성적표 표기 = "발행 n건 축적 중 · 캘리브레이션 미검증" 고정 문구. coverage/skill 숫자 자체를 렌더링하지 않는다(부분 표본 숫자가 곧 성과 주장으로 읽히는 것 차단).

## 5. vintage·backfill 정직 규약

1. **발행 봉인**: issuedAt(벽시계 UTC) 과 asOf(데이터 vintage) 를 분리 기록. 라이브 행은 issuedAt ≈ asOf, backfill 행은 issuedAt ≫ asOf.
2. **backfill 규약**: `issuedLive=False`. 용도 = 채점 파이프 검증과 사전 캘리브레이션 감각(P0)뿐. 공개 성적표에서 라이브 통계와 혼합 집계 금지, 표시하려면 별도 섹션 + "소급 생성(look-ahead 위험 잔존)" 라벨. backfill 생성 시에도 모델 입력은 asOf 봉인(`simulateMacro(asOf=)`) 강제하나, 코드·하이퍼파라미터가 미래 지식으로 조정됐을 가능성은 원리적으로 제거 불가하므로 라벨이 정직의 최후선이다.
3. **actual 봉인**: 채점 시점의 실제값 + actualAsOf + revisionPolicy="latest" 를 score 행에 기록. macro HF surface 는 latest-revised 라(첫 발표 vintage 미보유) CPI 등은 수정치 기준 채점임을 성적표에 상시 고지. 재채점(값 revision 후) = 새 score 행 append, 옛 행 불변.
4. **실패 봉인**: 실제값 조회 실패·상장폐지·회계기간 변경 등도 error 행으로 남긴다. 분모에서 조용히 빼는 순간 생존 편향이 시작된다(시뮬 03:186 survivorship 점검 동형).

## 6. G16·A7 정합 표

| 시뮬 게이트 | 본 플랜에서의 상태 |
|---|---|
| G16 (coverage·PIT·skill) | 채점기 자체를 P1 에서 빌드. active 조건(write-end 라이브 + N 누적)은 표본 게이트 §4 로 상속 |
| A7 공개 Brier 리더보드 defer | 유지. 성적표 v0 은 det-vs-ai 비교 없음. 원장 공개(무엇을 언제 발행했나)는 "예측 성과 주장"이 아니므로 defer 위반 아님. 성과 숫자는 §4 표본 게이트 뒤에서만 |
| 00 kill-list (목표주가·추천 표현) | 기대주가(P5)는 방향확률+구간, "목표가" 단어 금지, valuationPublishLint 대상 표면 준수 |
| DSR/PBO (09 R10) | 본 플랜 밖(전략 walk-forward 소관). 원장은 예측 채점만 |

## 7. 성적표가 시뮬레이터 성능기준이 되는 경로

1. 변수별 skill·coverage 가 표본 게이트를 넘으면 → 시뮬 DriverRegistry admission(02 §2B state 머신)의 실측 입력으로 전달 가능한 형태(`variable, horizon, skill, coverage, n, ci`)로 scorecard 에 병기.
2. skill≤0 확정 변수 = "예측 불가" 원장 = 시뮬레이터에서 해당 변수를 fan 이 아니라 사용자 가정 토글로 강등하는 결정의 데이터 근거.
3. 시뮬레이터 출시 게이트(03 §9.3)가 요구하는 "historical replay + 캘리브레이션" 증거가 원장에 자동 축적된다.
