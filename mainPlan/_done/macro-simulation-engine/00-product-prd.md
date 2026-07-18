# 00 · Product PRD — 거시 시뮬레이션 엔진

## §1. 한 문장

dartlab 거시 엔진이 *지금 어디인가(판정)·과거에 어땠나(재현)*에 멈추지 않고, **앞으로 어디로 갈 수 있나를 확률적으로 굴려 보여준다** — 거시 변수 팬차트, 충격반응(IRF), 국면경로(P(수축) 시간축), 시나리오 조건부 경로를, *보정 검증된 분포*로.

## §2. 왜 — 빠진 한 층

dartlab 거시 엔진은 이미 전문급이다(01 audit 참조). 그런데 산출은 전부 두 종류뿐:

1. **"지금"** — `analyzeForecast` 가 *현재* 침체확률·*현재* 국면확률. `analyzeCycle` 가 *현재* 4국면.
2. **"스냅샷 한 방 재계산"** — `runScenario` 가 override 넣고 *현재* 종합점수 delta. 앞으로의 *경로*가 아니다.

빠진 것 = **시간축을 따라 앞으로 굴러가는 동적 확률 시스템**. "금리 +100bp면 향후 24개월 성장·물가가 *어떤 경로·어떤 분포*로 가나", "6개월 뒤 수축확률은 몇 %이고 그 불확실성 밴드는", "현재 조건에서 GDP 성장의 5~95 분위 팬은" — 이걸 답하는 층이 없다.

이건 거시 시뮬레이션의 *교과서적 핵심*(중앙은행·IMF 표준: VAR/BVAR fan chart, IRF, 국면전환 forward)이고, dartlab은 그걸 만들 하드한 통계 기계(Hamilton EM·Kalman DFM·GaR 분위수)를 **이미 다 갖고 있다**. 0에서 만드는 게 아니라 *마지막 forward 층*만 얹는다.

## §3. 청중 (1차)

**"내 거시 판단을 확률 경로로 검증·확장하려는 분석가"** — 터미널 좌측 거시 패널을 보는 사용자. 팬차트(변수 미래 분포)·IRF(충격이 무엇을 어떤 부호·시차로 때리나)·국면경로(P(수축) 시간축)가 주력 산출.

명시적 비-청중(지금): "이 시나리오면 *내 포트폴리오 수익*이 어떻게 되나"는 quant/finance 영역(자산 총수익 시계열 데이터 벽 + 거짓확신 위험). 본 엔진은 *거시 변수·국면* 까지만. 포트폴리오 결과는 다른 엔진·나중 층(00 §7 비-목표).

## §4. 무엇 (산출물 4종)

1. **변수 팬차트(forward fan)** — 핵심 거시 변수(성장·물가·금리·환율 등) 각각의 향후 H개월 분위 경로(p5/p25/p50/p75/p95). BVAR 추정 → 충격 분포 draw → forward 반복 → 분위.
2. **충격반응(IRF)** — 단위 충격(예: 금리 +100bp)에 대한 각 변수의 H개월 반응 경로 + 신뢰밴드.
3. **국면경로(regime path)** — Hamilton 전이행렬 → Markov forward → h=1..H 각 시점 P(수축). (기존 regime band 가 *과거* `smoothedProbs[-24:]` 인 것의 *미래* 대칭.)
4. **시나리오 조건부 경로(scenario-conditional)** — 특정 충격 경로를 고정(예 "Fed 3%까지 인하")하고 나머지 변수를 조건부 시뮬 → 경로·밴드. 기존 *정적* `runScenario` 의 *동적* 승계.

각 산출물에 **보정·정직 메타** 동반: 표본 N, asOf, seed, 모델 스펙, held-out coverage/CRPS, 가정 라벨.

## §5. 정직 척추 (이 PRD의 헌법)

거시 미래 예측은 거짓확신 양산 1순위 지점이다. 운영자가 패널을 세 번 갈아엎은 이유가 거짓확신("쓰레기")이었다. 따라서:

- **보정이 기능보다 먼저.** 첫 빌드 = `macroBacktest` 확장으로 fan 의 *held-out coverage·CRPS·PIT* 측정. "예측한다"가 아니라 "**보정된 분포**를 낸다 — 그리고 그게 보정됐음을 out-of-sample로 증명한다"가 정직한 주장. 보정 안 된 모델은 표면에 안 올린다.
- **넓은 밴드가 정직.** 월 데이터 + 국면전환은 파라미터 불확실성이 시뮬 불확실성을 압도한다. 좁은 팬 = 거짓. 밴드는 *파라미터 불확실성 포함* 폭으로, 좁으면 캡션에 "조건부·파라미터 고정" 명시.
- **scenario ≠ forecast 명시.** 시나리오 조건부 경로는 "가정 하의 조건부"이지 "이렇게 된다"가 아니다. 라벨·footer 강제.
- **fail-closed.** 표본 부족·미수렴·분리 약함 → "표시 보류"(기존 regime build 의 `"status": "표본 부족·표시 보류"` 패턴 그대로). 결손 0 대체·환각 금지.
- **결정론.** seed 고정 → 같은 입력 같은 렌더. 새로고침마다 밴드 흔들리면 터미널 철학 붕괴.
- **look-ahead 차단.** 추정·시뮬은 asOf 이전 데이터만. macroBacktest 의 rolling re-estimation 규율 계승.

## §6. 시그니처 정직 (scenario-simulator 교훈 계승)

scenario-simulator 운영자 결정(`project_terminal_simulation_prd` §8c, 2026-06-20): **"planScore를 시그니처 proxy로 쓰지 마라. 억지로 점수 넘기지 마라. 전부 부정적 검토. 진짜 핵심은 빌드·증명 가능한가."** 본 PRD도 동일 규율:

- planScore(설계 완전성) ≠ systemScore(실빌드) ≠ signature(증명·방어). 세 축 분리 표기.
- 본 엔진의 시그니처 가능성은 **"보정된 거시 forward + transmission 으로 기업까지 잇는 폭"** 에 있다(블룸버그도 잘 못 잇는 거시→펀더멘털 다리). 단 그건 *증명*(held-out 보정 + 실제 transmission 커버리지)이 서야 시그니처지, 미빌드 점수로 주장하지 않는다.
- 미빌드 기능에 전문가-패널 uplift로 점수 인플레 금지(`feedback_plan_score_not_signature`). 검증 척추를 *먼저* 빌드해 재정박.

## §7. 비-목표 (kill-list 요약, 상세 05)

- **DSGE 금지** — 연 단위 캘리브레이션·취약·리테일 과잉. BVAR이 90% 값을 5% 노력으로.
- **naive bootstrap 금지** — 월 원시계열 1만 회 리샘플 = 모델 없는 숫자 연극. 반드시 *추정된 시스템*의 충격 propagation.
- **포트폴리오 수익 MC 금지(지금)** — 자산 총수익 시계열 데이터 벽 + 거짓확신. 다른 엔진·나중.
- **전역 seed 금지** — `np.random.default_rng(SEED)` 로컬 인스턴스만.
- **새 거대 surface 금지(지금)** — 기존 패널/다이얼로그 확장 우선(declutter). 전용 시뮬 surface는 Phase 후반.
- **scenario-simulator 와 import cross 금지** — 단방향 브리지만.

## §8. 수용 기준 (acceptance)

| 영역 | 기준 |
|---|---|
| 정확성/보정 | held-out walk-forward 에서 fan 80% 밴드의 실제 coverage ∈ [0.72, 0.88](명목 0.80 근방). PIT 균등성 KS p>0.05. IRF 부호가 경제이론과 일치(금리↑→성장↓ 등). |
| 결정론 | 같은 parquet+seed → `macro/sim/{kr,us}.json` byte-동일(2회 빌드 diff 0). |
| 정직 | 모든 산출물에 보정 메타·가정 라벨·표본 N 동반. 미보정/미수렴 = "표시 보류". footer = scenario≠forecast. |
| 배선 | 터미널이 추가 fetch·직접 URL 0으로 `rt.macro` 단일 진입점으로 sim JSON 로드(`checkUiDataWiring` 통과). dev=퍼블릭 기준 렌더. |
| 회귀 | 기존 macro/regime/cycle 빌드·테스트·Guard Index 신규 위반 0. import 4계층·L1.5 cross 0. |
| 시각 | 팬/IRF/국면경로가 MiniFinChart SSOT(손수 차트 0)로 렌더. 푸시 전 스크린샷 전수 눈검수. |

## §9. ROI / 우선순위

- **즉시 가치**: 방금 만든 거시 패널/다이얼로그에 "미래" 축이 붙어 *판정→전망* 완결. Phase 1(국면경로)은 Hamilton 재사용이라 추가 모델 0·즉시 가시.
- **복리 가치**: BVAR fan/IRF 가 transmission 과 만나면 "금리 충격 → 6개월 경로 → 반도체·은행·화학 부호별 타격"까지(dartlab 고유 거시→펀더멘털 다리). scenario-simulator 외생축도 본 엔진 분포로 격상(Phase 4).
- **리스크**: 거짓확신(→ 보정 척추로 차단). 데이터 충분성(KR GDP 분기 표본 짧음 → BVAR Minnesota prior + fail-closed). 두 시뮬 엔진 혼동(→ 명명·import 가드).
