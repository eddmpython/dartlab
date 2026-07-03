# 00. Expectation Grid 제품 PRD

> 참조 축약: 시뮬 문서 = `mainPlan/scenario-simulator/` 하위 (00=product-prd, 01=engine-architecture, 02=assumption-method, 03=validation, 09=architecture-consolidation).

## 1. 판정

운영자 goal("모든 엔진이 작은 기대치를 공통 계약으로 발행 → 사후 자동 채점 → 성적표 축적 → 시뮬레이터 성능기준 확보")은 명확하고 타당하다. 시뮬 00 §8c 가 스스로 내린 처방(위협 C: 검증 루프 미빌드)과 정확히 일치하며, 09 §10.2 는 해당 write-end 티켓(P9a/b/c)을 이미 "지금 빌드 가능"으로 분류해 뒀다.

### 1b. goal 대비 정정 2건 (실측 근거, 승인 시 인지 필요)

**정정 1 : 원장 write 위치.** goal 은 "원장 read/write = simulate/" 로 확정했으나, import 방향 계약(시뮬 01:53 downward-only, `test_import_direction` `LAYER_OF["simulate"]=2.5`)상 L2 발행 엔진(macro·analysis·credit·quant)은 L2.5 simulate 의 writer 를 import 할 수 없다. 정공법 해소: **발행 엔진은 원장을 아예 모른다**(공개 예측 verb 만 제공, 이미 존재). simulate/ 의 수집자(collector)가 엔진 verb 를 호출해 ExpectationSpec 으로 래핑 후 **단독 기록**한다. simulate→L2 호출은 합법이라 방향 문제가 소멸하고, "원장의 유일한 기록자 = simulate" 라는 goal 의 취지는 오히려 강화된다.

**정정 2 : 채점 지표 정밀화.** goal 의 "Brier<0.25, calib MAE<0.1, skill>0" 은 시뮬 02:493~497 의 held-out acceptance threshold 로 실재하되, 시뮬 03:207 이 **Brier=이진(방향) 전용, 연속 분포는 별개 채점**으로 명시 분리했다. 연속 변수(물가·환율·매출)는 03 §4.4 정본대로 coverage(0.85~0.95) · PIT 균등성(KS p>0.1) · CRPS/pinball · skill(=1-CRPS/CRPS_baseline, 가장 센 naive 대비)로 채점한다. 상세 = 02 문서.

## 2. 제품 비전

기업에 대해 판단을 내리는 주체는 셋이다: 시장(가격에 기대를 박음), 회사(공시로 계획을 약속함), dartlab(등급·시그널·예측을 산출함). 현재 dartlab 은 셋 다 현재 시점 분석은 하지만, 어떤 판단도 발행 시점에 봉인해 사후 채점하지 않는다(유일한 부분 예외 = credit `recordGrade` 이력, revenue `forwardTest` 로컬 JSON). Expectation Grid 는 dartlab 자신의 판단부터 원장에 넣는다.

세 가지 가치가 한 인프라에서 나온다:

1. **시뮬레이터 성능기준**: "시뮬레이터가 가능한가"라는 큰 물음이 "물가 fan 이 random-walk 를 이기는가, 매출 예측 skill 이 양수인가" 같은 변수별 측정 문제로 분해된다. 게이트 미통과 변수는 시뮬레이터에서 예측이 아니라 가정 토글로 강등된다(실패도 성과다: 무엇을 예측할 수 없는지가 데이터로 확정된다).
2. **성적표(자기공개)**: 발행된 모든 기대치의 사후 성과를 공개하는 상시 화면. 시뮬 03 의 honesty 규율(미검증 라벨 강제)이 마케팅 문구가 아니라 타임스탬프 원장으로 증명된다.
3. **시간 해자**: 다른 모든 기능은 후발주자가 복제할 수 있으나, 라이브 발행 타임스탬프가 찍힌 트랙레코드는 소급 생성이 불가능하다. 원장은 매 사이클 길어질수록 격차가 벌어진다.

## 3. 제품 원칙

1. **점 예측 금지**: 모든 기대치는 분위 구간(p5/p25/p50/p75/p95) 또는 확률(이진 방향)로 발행한다. 시뮬 00 kill-list(목표주가·추천·예측기 표현 불가침)와 03 §10 실패 기준을 그대로 상속한다.
2. **발행 즉시 불변 봉인**: 발행 행은 수정·삭제 금지. 채점은 별도 행 append. 틀린 예측의 은폐·재작성은 원장 전체의 신뢰를 파괴한다.
3. **라이브/backfill 영구 구분**: `issuedLive=False` 행(과거 asOf 로 소급 생성)은 캘리브레이션 사전 점검 전용이며 공개 성적표에서 라이브 행과 절대 혼합 표기하지 않는다. 시간 해자 주장의 정직성이 이 필드 하나에 걸려 있다.
4. **naive 동시 봉인**: 발행 시점에 naive 기준선(random-walk·persistence·seasonal-naive) 예측도 같은 행에 봉인한다. 사후 "어떤 baseline 과 비교했나" 논란을 원천 차단한다.
5. **표본 미달 = 미검증 라벨**: 변수별 최소 표본(02 §4) 충족 전에는 성적을 주장하지 않고 '캘리브레이션 미검증'을 강제한다(시뮬 03:233 동형).
6. **A7 defer 준수**: det-vs-ai 공개 리더보드는 본 플랜 범위 밖(시뮬 03 §9.3 defer 게이트 유지). 성적표 v0 은 자기 예측(엔진)의 원장 공개 + 표본 충족 변수의 캘리브레이션만 다룬다.
7. **재사용 우선**: 예측 모델 신설 0. 기존 verb(simulateMacro·forecastRevenue·credit·proforma)와 기존 채점 코드(evaluate·evaluateCalibration·fanCalibration)를 계약으로 묶는 것이 전부다.

## 4. 주요 산출물

1. **원장 2테이블** (append-only parquet, 연도 flat shard):
   - `expectations` : 발행 봉인 행 (스키마 = 01 §3)
   - `scores` : 채점 행 (expectationId 참조, 실제값·actualAsOf 봉인 포함)
2. **성적표(scorecard)** : 원장을 변수·도메인·기간으로 집계한 읽기 뷰. v0 = 터미널 패널 1개 + HF 직독.
3. **시뮬레이터 성능기준 표** : 변수별 skill/coverage 게이트 통과 여부 = 시뮬 DriverRegistry admission(02 §2B)의 실측 입력.

## 5. 범위 (v1)

포함: P0 개념확립(_attempts) → P1 계약+원장 → P2 macro KR 3변수(CPI·기준금리·USDKRW, 월) → P3 매출(분기, 전상장사) → P4 항등식 전개(매출+마진 → 영업이익·순이익·FCF 행) → P5 credit 편입 + 주가 방향확률 → P6 성적표 v0 + CI 자동 사이클.

명시 제외 (v1 밖):
- det-vs-ai 리더보드(A7 defer), AI lens 채점(시뮬 fatal③ 소관)
- 기대 재무상태표 풀 전개(P4b 로 defer: 현행 proforma 는 손익·FCF 중심, BS 는 운전자본 근사만)
- 물가→기업 캐스케이드(현행 `transfer.py` 는 gdp/rate/fx 3채널만. CPI 채널 신설은 DriverRegistry G게이트 소관이라 본 플랜에서 확장 금지)
- US 시장(KR 가드 해제는 시뮬 fatal④ 소관), 회사의 공시 약속 추출(promise tracker 는 후속 플랜)

## 6. 성공 기준

1. 발행 행은 발행 후 어떤 코드 경로로도 수정되지 않는다(불변 테스트).
2. 채점 사이클이 사람 개입 없이 돈다(CI cron: 월=macro, 분기=fundamental).
3. 성적표의 모든 숫자는 원장 행 참조로 역추적된다(ref 없는 숫자 0).
4. 표본 미달 변수는 화면에서 '미검증' 라벨 외 어떤 성과 주장도 하지 않는다.
5. skill≤0 변수가 나오면 은폐 없이 표기되고, 시뮬레이터 가정 토글 강등 목록에 오른다.
6. 완성 정의: P6 + 최소 1회 라이브 사이클(발행→실제값 도착→성적표 갱신) 실데이터 증명.

## 7. 렌즈 이중 평가

**개발자 렌즈**: 신설 코드는 계약 dataclass + 파일 IO + 오케스트레이션 + 집계 뷰로, 수치 알고리즘 신설이 0 이다(채점 수학도 03 §4.4 명세 이식). 리스크는 알고리즘이 아니라 배선(DATA_RELEASES·CI cron·OOM 가드)에 있고, 전부 기존 패턴(hfUpload·buildMacroData·BoundedCache)이 있다. 구현 난도 중하, 회귀 리스크 낮음(전 phase additive).

**PM 렌즈**: 첫 사이클부터 사용자 가치가 나온다(P2 완료 시점에 "dartlab 이 이번 달 물가를 이렇게 봤고, 지난 발행은 이랬다"가 화면에 선다). 최대 리스크는 초기 성적이 나쁠 가능성인데, 이는 제품 사상("정직은 시각으로")상 실패가 아니라 콘텐츠다. 단 라벨 규율(미검증·표본부족·backfill 구분)이 무너지면 역풍이므로 02 문서의 honesty 규약을 기계 게이트로 강제한다.

## 8. 실패 기준 (하나라도 발생 시 중단·재설계)

1. 발행 행이 사후 수정되는 경로가 발견됨.
2. backfill 행이 라이브 성적에 혼입 표기됨.
3. 표본 미달 변수가 성과 문구를 노출함.
4. 원장 없는 숫자가 성적표에 등장함.
5. 예측 모델을 새로 만들기 시작함(범위 이탈 신호).

## 9. 승인 필요 3건 (착수 게이트)

| # | 항목 | 근거 규칙 | 비고 |
|---|---|---|---|
| A1 | HF 신규 surface `expectations/` (DATA_RELEASES 키 + CI 쓰기) | 런타임-SSOT: 신규 산출물 사전 승인 | 런타임 재계산 불가 실측 근거 = "발행 시점 봉인"은 시간을 되돌릴 수 없어 원리적으로 런타임 재현 불가. append-only 원장은 allFilings 와 동류 |
| A2 | forwardTest `~/.dartlab` 저장 폐기 → `data/` redirect (09 P9b 티켓 이행) | 시뮬 09 §10.2 계획 그대로 | 함수 시그니처 하위호환 유지 |
| A3 | calibrationMetrics 를 synth 로 승격 (analysis 에서 re-export, identity 보존) | L2 cross-import 금지 해소 | credit·quant 가 채점 수학 공유 가능해짐 |

승인 전 허용 작업 = P0(_attempts 개념확립, src·HF 미접촉)와 본 설계 문서뿐. 승인 후 P1~P6 무중단.
