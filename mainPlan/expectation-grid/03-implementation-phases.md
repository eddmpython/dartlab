# 03. 구현 페이즈 (P0~P6 : 파일 · 함수 · 테스트 · AC · 롤백)

> 공통 규율: 신규 능력은 `tests/_attempts/expectationGrid/` 졸업 게이트 통과 후 본진. 각 P 는 additive(기존 경로 무변경 원칙)라 롤백 = 신설 모듈 제거. 신규 src 모듈 push 전 로컬 blocking + CI 선제 2종(dartlabGuard l0-l15 미러 + productSmoke quick) 실행. UI(P6)는 자동 push 금지·운영자 눈검수.

## P0. 개념확립 (_attempts, 승인 불요 · src/HF 미접촉)

- 위치: `tests/_attempts/expectationGrid/` (probe.py + README.md)
- 내용: KR macro 3변수(CPI·BASE_RATE·USDKRW)에 대해 ①과거 asOf(예: 12~18개월 전 매월)로 `simulateMacro(market="KR", asOf=...)` fan 발행 ②ExpectationSpec 시제품 dataclass 로 봉인 ③실제값(seriesFetch)과 join ④pinball/PIT/coverage/skill 채점 ⑤random-walk·persistence 대비 skill 산출
- AC: 사이클(발행→채점→집계)이 실데이터로 1회 완주 + 결과 수치(변수·horizon 별 coverage/skill)가 README 에 박제. skill 부호는 AC 가 아니다(음수여도 개념확립 성공 : "무엇이 예측 불가한가"의 첫 실측).
- 주의: `issuedLive=False` 규약 그대로(전량 backfill). asOf 봉인 강제. 메모리 가드(Polars OOM)상 회사 로드 없음(macro 만이라 경량).

## P1. 계약 + 채점수학(synth) + 원장 IO(simulate) 본진 배치

- 파일: `synth/expectationSpec.py`(신설) · `synth/calibrationMetrics.py`(승격 이동, A3) · `analysis/forecast/calibrationMetrics.py`(re-export stub 로 축소) · `simulate/expectationLedger.py`(신설)
- 함수: 01 §2.1·§2.3 전량
- 테스트(미러): `tests/synth/test_expectationSpec.py`(스키마·pinball·PIT·skill 골든값) · `tests/synth/test_calibrationMetrics.py`(승격 후 identity: 기존 테스트 이동) · `tests/simulate/test_expectationLedger.py`(append-only 불변: 중복 id raise · 행 수정 경로 부재 · roundtrip)
- AC: 전 테스트 green + `dartlabGuard --scope l0-l15` 신규 위반 0 + import-linter 방향 무위반
- 롤백: 신설 2파일 제거 + calibrationMetrics 원위치 복원(re-export stub 삭제, git revert 1커밋)

## P2. macro 3변수 월 사이클

- 파일: `simulate/expectationCycle.py` 신설(`issueMacro`·`scoreDue`·`buildScorecard` 골격) · `.github/scripts/sync/buildExpectations.py` 신설 · `dataConfig.py` 1줄(A1) · sync workflow 에 monthly job
- 명세: h=1/3/6/12, 발행 시 baseline 동시 봉인(02 §3). scoreDue 는 targetPeriod 도래분만, 실제값 = `seriesFetch`(CPI/기준금리/USDKRW, ECOS·FRED). 실패 행 봉인(02 §5.4)
- 테스트: `tests/simulate/test_expectationCycle.py` (issueMacro 가 spec 계약 충족 · baseline 3종 봉인 · scoreDue 가 미도래 행 스킵 · 실패 봉인 경로). CI 스크립트는 `--dry-run` 플래그로 smoke
- AC: 로컬 1회 라이브 발행 + HF `expectations/` 첫 커밋 + 다음 달 사이클에서 자동 채점 확인(완성 정의의 "최소 1회 라이브 사이클"의 시계 시작)
- 롤백: workflow job 제거 + DATA_RELEASES 키 제거. HF 에 이미 쓴 원장 파일은 **남긴다**(발행 이력 은폐 금지 원칙. 실험 중단 사실을 scorecard 에 기록)

## P3. 매출 분기 사이클 (전상장사)

- 파일: `expectationCycle.py` 에 `issueRevenue` 추가 · `analysis/forecast/forwardTest.py` backend redirect(A2: `_FORWARD_TEST_DIR` → `DARTLAB_DATA_DIR` resolver, 시그니처 유지) · 09 P9c `recordForecast` facade 신설(`analysis/forecast/forwardTest.py` 내, 시뮬 09:239 시그니처 그대로)
- 명세: 분기보고 시즌 종료 후(캘린더 트리거) 전상장사 sweep. **OOM 가드**: CI job 에서 종목 단위 순차 스트림(Company 1개 로드→발행→해제, BoundedCache, 병렬 금지), 로컬 전수 실행 금지(테스트는 표본 3종목). 결손·실패 회사도 행으로 기록(커버리지 census = 정직)
- 3-시나리오→분위 근사(Base/Bull/Bear → p50/p75·p25 매핑)는 근사임을 warnings 에 상시 라벨
- 테스트: `tests/analysis/forecast/test_forwardTestWrite.py`(09 티켓 게이트명 `test_forwardTestWrite_roundtrip` 그대로) · cycle 테스트에 revenue 경로 추가
- AC: 표본 종목 발행·채점 roundtrip green + 전상장사 CI run 1회 완주(실패율 census 산출)
- 롤백: issueRevenue 제거 + forwardTest env 미설정 시 기존 경로 유지(redirect 는 env 부재 시 무동작이라 안전)

## P4. 손익 전개 (매출+마진 → 영업이익·순이익·FCF)

- 파일: `expectationCycle.py` 에 `issueEarnings` 추가
- 명세: 자유 예측 아님. P3 매출 기대 + `simulate.runScenario`(proforma-FCFF 결정론 코어) 전개로 파생 행 발행. 파생 행은 `sourceRefs` 에 모체 expectationId 연결(항등식 계보). BS 풀 전개는 P4b defer(00 §5)
- 테스트: 파생 행 계보 검증 + proforma 결과와 행 값 일치 골든
- AC: 표본 종목에서 매출 1행 → 손익 3행 파생이 결정론 재현(동일 입력 byte-identical)
- 롤백: issueEarnings 제거(파생 행뿐이라 원장 정합 영향 0)

## P5. credit 편입 + 주가 방향확률 (마지막)

- 파일: `expectationCycle.py` 에 `issueCredit`·`issuePriceDirection` 추가
- 명세: credit = `recordGrade` 시점에 adapter 가 기대 행(다음 분기 등급 유지/이동 확률 = `forwardPdLadder`·transition 기반) 병행 발행. 주가 = direction(prob) + 분위 구간만, "목표주가" 표현 금지(valuationPublishLint 표면 준수), upsideProbability 재사용
- 테스트: adapter 이중기록 부재 · kill-list 문구 lint 통과
- AC: 두 도메인 행이 원장·성적표에 합류
- 롤백: 두 함수 제거

## P6. 성적표 v0 + CI 완결

- 파일: 터미널 성적표 패널 1개(`ui/packages/surfaces/src/terminal/`, origins `hf` 직독) · `buildScorecard` 완성(표본 게이트 라벨 02 §4 강제)
- 명세: v0 화면 = ①원장 뷰(발행 이력 타임라인, live/backfill 구분) ②표본 충족 변수의 캘리브레이션(coverage bar·PIT 히스토그램·skill) ③미검증 변수는 고정 문구만. det-vs-ai 없음(A7 defer)
- 테스트: scorecard.json 계약 스냅샷 + UI 는 Playwright 정량 + **푸시 전 스크린샷 전수 눈검수(운영자)**
- AC: 공개 터미널에서 성적표가 HF 직독으로 뜨고(:8400 없이), CI 월·분기 cron 이 사람 개입 없이 발행·채점·업로드 완주
- 롤백: 패널 미배선 커밋 분리(공개 터미널 무중단 규율), scorecard 산출만 남기고 UI revert 가능

## 완성 게이트 (goal 원문)

P6 + 최소 1회 **라이브** 사이클(발행→실제값 도착→성적표 갱신) 실데이터 증명. macro 월 주기 특성상 P2 첫 발행 후 다음 월 데이터 도착이 최단 경로다(P2 를 최대한 앞당기는 이유).
