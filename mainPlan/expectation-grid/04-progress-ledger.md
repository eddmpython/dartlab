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
| P6 성적표 터미널 패널 + CI cron | ✅ 빌드·타입체크·배선감사 green, **push 는 운영자 눈검수 대기** (UI 자동 push 금지) |

## P6 상세 (2026-07-03)

- 계약: `ui/packages/contracts/src/expectations.ts` (ExpectationsPort, DartLabRuntime 필수 포트)
- 배선: public·local·test 런타임 3종 + `expectationSource.ts` (origin `hf` 직독, checkUiDataWiring PASS 위반 0)
- 패널: RightStack "기대치 성적표" (macro 변수별 + 도메인 rollup, verified=False 는 성과 숫자 0 · 미검증 라벨만, live 발행분만)
- 검증: contracts/runtime tsc 0 err · surfaces svelte-check 0 err · landing build 성공 · dev 5173/terminal 200
- CI red 수리: cleanupCalls 감사 위반 3건(Company 루프) → `with Company()` 컨텍스트 전환, 98 테스트 green

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

## E2b : 분기 E 발행 + 패널 밀도 테이블 (2026-07-04, 운영자 지적 2건 대응)

운영자 지적: ①성적표 패널 나열식 비효율 -> 테이블 ②재무제표 연간만 E, 분기 부재.

- **분기 E 발행 (`issueQuarterlyIs`)**: 봉인된 연간 분위행의 결정적 계절 분해(새 예측 아님, sourceRefs 계보 = 연간 부모). 계절성 = `scenarioSim.seasonalSharesFromYearQuarters` 코어(3년 Q1~Q4 |값| 비중 평균, 신규 공개 verb) x `_buildFinanceSeries(freq="Q")`. **panel("is") 는 분기창에 Q4 열이 없어 부적합(실측)** -> 첫 발행 12행(3사 2026Q3·Q4)은 flat 0.25 분해로 봉인됨(`flatSeasonalityFallback` 경고 동봉, append-only 원칙대로 유지·삭제 안 함). 소스 교체 후 2027Q1~Q4 24행은 실 계절성(005930 영업이익 [0.15,0.18,0.31,0.36] 하반기 편중 실측). 지표 = 매출·영업이익만(scenarioSim 전례, 순이익 분기 부호 요동). years=(1,2) 기본: 당해 잔여분기 + 차년 4분기. live 는 종료 분기 발행 금지(look-ahead 차단). horizon = FY 내 분기 위치(1~4).
- **분기 채점**: scoreDue freq=Q 브랜치(분기말 +2개월 due, grace 3개월 후 결측 error 봉인). 실적 = `quarterlyValues`(신규 공개 verb, 미발표 분기 = 키 부재).
- **오염 가드 2건 선제 수리**: ①issueEarnings 연간 캐스케이드에 freq=Y 필터(분기 행 혼입 시 horizon 맵 붕괴) ②buildScorecard 그룹 키에 freq 삽입(`revenue.*.Q1` vs `Y1` 혼입 차단, 키 형식 `{domain}.{variable}.{freq}{h}.{live}`).
- **뷰/UI**: estimateStatements 뷰에 `periodKind`(FY|Q, 분류 = 라이브러리 소유) -> 분기 탭 손익에만 E열(26Q3E~27Q4E), 연간 E열 라벨 버그 수정(slice(6) -> "FYE" 중복 키). 성적표 패널 = 밀도 테이블 3종(연간 기대 지표x FY / 분기 분해 근접 4분기 / 시장·채점 4열). 패널 표시 = 대상기간별 최신 발행(전역 최신 배치만 남기면 이시각 발행 target 소실 실측).
- 검증: pytest 34 green(신규 분기 발행·채점·계보·오염가드·계절성 코어) · dartlabGuard strict 7룰+6게이트 PASS · publicApiCoverage OK · svelte-check 0 err · checkUiDataWiring 0 · 스크린샷 눈검수 2장.
- 원장 현황: 발행 78 (연간 42 + 분기 36) · HF 4파일 재발행 완료.

### 알려진 정합 갭 (후속, 신규 아님)
- **proforma 매출 앵커 갭**: E-3표 연간 매출(예 005930 FY26E 427.6조)이 봉인 연간 기대(367.3조)와 어긋남. 원인 = issueEarnings 가 봉인 레벨을 성장률로 변환 후 buildProforma 가 자기 내부 베이스(최근 4분기 합)에 적용. 분기 E 는 봉인 연간을 직접 분해하므로 분기합 != 연간 E열. 정공법 = buildProforma 에 revenueLevelPath(절대 경로) 지원 추가 후 재발행분부터 앵커 일치 (L2 엔진 변경이라 별도 단위).

## E2c : look-ahead 게이트 데이터 기준 전환 (2026-07-04, 운영자 지적 "Q2 왜 건너뛰나")

- 종전 게이트(달력: 분기말 경과 = 발행 금지)가 미공시 분기(Q2, 분기보고서 8월)를 부당하게 제외. 전환: **실제값이 SSOT 시계열에 존재하는 분기만 제외** (발행 시점 정보집합 기준). 분기말 경과·미공시 = nowcast 로 발행하되 `quarterEndedAtIssue` 경고 봉인 + 성적표 그룹 `.nowcast` 접미사로 일반 예측과 혼합 집계 금지 (정보우위 오염 차단).
- 잠복 결함 동시 수리: 분기 채점 실제값 소스가 panel("is") 였는데 분기창에 Q4 열이 없어 Q4 채점이 전부 grace 후 error 봉인될 운명이었음. `_seriesQuarterValues`(_buildFinanceSeries freq=Q) 로 교체, 발행 게이트와 채점이 같은 실제값 소스 공유.
- 검증: pytest 28 green (데이터 게이트·nowcast 라벨·분리 그룹·Q2 채점) · guard strict PASS. 2026Q2 nowcast 6행(3사) 봉인·HF 재발행 (원장 84행).

## E3 연구 + D1 수리 + UI 재구성 (2026-07-04, 운영자 goal: 전문가 토론 연구 + 테이블 추정 분리 + 추정 패널/상세보기)

- **전문가 5-패널 연구**: 셀사이드·계량·3표정합·매크로크레딧 4관점 + 코드 실측지도. 5개 독립 관점이 최상류 결함을 교차확인. 종합 = [06-estimation-techniques.md](06-estimation-techniques.md). 검증된 결함 6종(D1~D6)·기법 랭킹·착수순서.
- **D1 버그 수리(검증)**: `_revenueForecastCore.py` 앙상블 다년 경로 루프 본문이 for 밖으로 dedent 돼 있어 1년차만 성장·2·3년차 복제(운영자가 본 367.3 flat의 정체). 재인덴트 수리 + 회귀 3테스트(`tests/analysis/forecast/test_revenueForecastCore.py`: 복리 단조·시나리오 base 비flat·override BC). 다운스트림 19테스트·guard strict 7룰+6게이트 무손상. **봉인 원장은 append-only라 기존 flat 행은 불변 유지(생존편향 금지), 수리 효과는 go-forward 신규 발행분부터**.
- **UI 재구성**: ①재무제표 표에서 E열 전량 제거(실적 전용, 운영자 규율) ②재무 패널 바로 아래에 밀도 높은 "추정·기대" 패널 신설(연간/분기 봉인 추정 + 시장 팬 + 채점 도착) ③상세보기 다이얼로그 `ExpectationDetailDialog.svelte`(추정 3표 IS/BS/CF 탭 + 연간/분기 + 보수/기준/낙관 시나리오 토글 + 채점 트랙레코드 + 매크로 팬 + 방법·계보). 옛 하단 성적표 패널 삭제. svelte-check 0 err·배선감사 0·스크린샷 눈검수 3장.
- **연구가 UI로 가시화**: 상세 다이얼로그가 D2(매출액 428 vs 봉인 367.3)·D3(자본총계=이익잉여금)·D5(마진 대칭)를 화면에서 직접 노출 = 검증척추가 결함을 보이게 만듦.

## E4 도약 기법 구현 #2·#4 (2026-07-04, 운영자 "끝까지 완료")

06 로드맵을 정공법으로 구현. pure-engine 개선(입력 불변·독트린 준수):

- **#2 revenueLevelPath 앵커 (D2 해소)**: `buildProforma`에 `revenueLevelPath` 인자 추가. 주어지면 base 상대성장 대신 봉인된 절대 매출레벨을 매출로 직접 사용(BS 기초잔액은 base 유지). `issueEarnings`가 봉인 매출분위 절대값을 그대로 전달. 결과: E-3표 매출 == 봉인 매출기대 정확 일치.
- **#4 영업레버리지 마진 브릿지 (D5 해소)**: `HistoricalRatios`에 고정/변동 분해 필드 + `_ehrOperatingLeverage`(원가·판관비를 매출에 OLS 회귀, `cost=fixed+var*rev`). 신뢰 게이트(표본>=4·기울기(0,1]·고정비>=0·R2>0.7) 통과 시만 적용, 아니면 순변동비 폴백(무회귀 안전). dep_in_sga면 비활성. buildProforma가 매출 급변 시 고정비 희석으로 마진 비대칭 반응.
- **D3(cash 죽은문장 `base["cash"]`) 제거**. #3 CF 절합 본체는 CF 실적 채점(P4b) 선행 + 리볼버 재작성 리스크라 별도 단위로 보류.
- **검증**: proforma+기대치 80 + 다운스트림(l2_splits·pricetarget·run·sheet·scenarioSim) 89 green, guard strict 7룰+6게이트, ruff clean. 신규 회귀: revenueLevelPath 앵커·OLS 분해·영업레버리지 탐지·순비례 안전 폴백.
- **재발행 증명(D1+D2)**: 첫사이클 pre-rollout·미채점 dev 원장을 정정 엔진으로 재봉인(생존편향 아님: actual 대조 채점 전, look-ahead 미발생). 실측: 005930 매출 p50 flat 367.3 → 복리 559→621→684조(D1 소멸), E-3표 매출 == 봉인 매출 anchorMatch=True 전원(D2 소멸). HF 재push(force_download 확인). 화면 반영은 HF 엣지캐시 TTL 만료 후(데이터·로컬 검증은 즉시 일치).
