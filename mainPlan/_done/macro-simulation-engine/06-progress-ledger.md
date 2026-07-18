# 06 · Progress Ledger

> 재개 = 아래 **NEXT** 부터. 커밋 규약 `거시시뮬(Phase-N): ...`. 착수 전 운영자 go.

## 상태

- **2026-06-24 · v0.1 설계 초안** — PRD 7문서 작성. 거시 엔진 audit 후 "빠진 forward 층" 정의. scenario-simulator 중복 0.
- **2026-06-25 · 구현 (운영자 go: "정공법·클린코드·덕지덕지 금지로 완성")** — Phase 0~2 본진 완료. Phase 3~4 의도적 후순위.

### ✅ Phase 0 — 개념검증 (`tests/_attempts/macroSimEngine/`, gitignore 스크래치)
- 자연켤레 Minnesota BVAR(dummy-obs) + forward fan + Cholesky IRF. 졸업 AC 3종 PASS:
  결정론(seed byte-동일)·held-out 80% coverage **0.85**(US 5변수 1986~)·IRF 안정(companion eig 0.997<1).
- 정직 발견 박제: ① 재귀식별 IRF *방향부호*는 표본/식별 취약(price/output puzzle) → fan/regimePath 척추·IRF caveat.
  ② HY스프레드 로컬이력 부족(2023-06~) → 원유로 대체(물가퍼즐 해소+장기이력)·HY 백필 후 편입.

### ✅ Phase 1+2 — 본진 엔진 + 빌드 + UI (커밋)
- **엔진** `src/dartlab/macro/simulate/`(`afO`): bvar·fan·irf·regimePath·calibration·_panel·_types·simulate.
  공개 verb `dartlab.macro('시뮬레이션', market=)`. US/KR 양시장 fan 작동(US nObs483·KR 315).
  regimePath = Hamilton 전이행렬 forward Markov(약분리/표본부족 시 fail-closed "표시 보류" — 정직).
  IRF caveat="recursive-identification·illustrative". 결정론·안정성 게이트·look-ahead 차단.
- **보정 척추** `calibration.py::fanCalibration` — held-out coverage **US 0.84 calibrated**(probe 재현). measureCoverage 순수·테스트.
- **빌드** `pipeline/stages/macro.py::runMacroSim` → `macro/sim/{kr,us}.json`(15-17KB) → HF. runMacro 독립 합류 + StageSpec.
- **UI** 거시 다이얼로그 **현황|전망 토글** + BVAR 팬 2×2(과거 실선+미래 밴드, MiniFinChart SSOT, 원유 control 제외)
  + 국면경로 연속 SVG(조건부) + 정직 footer. 배선 `rt.macro.getSim`→`macro/sim` JSON(loadHfJson 단일진입). 무스크롤.
- **테스트**: 엔진 9 unit + macroLens vitest 53 + architecture/camelCase/svelte-check 0err/tsc 0. 시각 눈검수(KR/US 전망 팬 렌더 확인).

### ★2026-06-25 (이어서) — 런타임 전환 (운영자: "별도 데이터 배선 금지·런타임으로")
- **거부**: CI precompute → `macro/sim/{kr,us}.json` HF publish → `getSim`(loadHfJson) 방식이 운영자가 막아둔
  *별도 데이터 배선/아티팩트*. publish 게이트도 거부.
- **정정 = 브라우저 런타임 계산**(커밋 백엔드 `74671ee25`·UI `d7453dccc`):
  ① **fan MC → 해석적 예측오차 분산**(Lütkepohl §2.2) — 난수 0 → 결정론·byte 재현 → TS 포팅 가능. seed/draws 제거. 보정 US 0.85 유지.
  ② `runMacroSim` 빌드 stage·`macroSim` StageSpec·`getSim` HF origin·`loadMacroSim`(loadHfJson) **제거**. macro/sim 아티팩트 폐기.
  ③ `ui/.../terminal/lib/macroSimCompute.ts` — Python 엔진 *동일수식 mirror*(matInv/cholesky/Minnesota dummies/companion/해석적 분산/_Z).
     `rt.macro.getSeriesRaw`(yoy 미적용 원시 index = Python 입력 일치, 같은 observations.parquet)로 런타임 계산.
  ④ `macroSimCompute.test.ts` **golden parity** — 고정 패널서 Python forwardFan 값 byte 일치(drift 차단). loadSource null→0 오변환 수정.
  ⑤ pyodide 기각 — 휠 재발행(=발행) 필요 + 16MB 로드. 해석적 TS 가 발행 0·즉시.
- **검증**: Python 10 · parity 4 · macroLens 53 · runtime 53 · svelte-check 0err · tsc 0. 시각 확인(US 483·KR 315행 팬 2×2 렌더·무스크롤·footer "런타임 계산").

### ✅ Phase 3 — 시나리오 조건부 forward (커밋 백엔드 `90200b2f4`·UI `627206673`)
- **방법 = Gaussian 조건부 예측**(Doan-Litterman-Sims 1984·Bańbura-Giannone-Lenza 2015): 무조건 예측분포
  N(μ,Ω)에 정책금리 경로 하드제약 → 조건부 평균·밴드 닫힌형. **MC 아님·해석적·결정론**(런타임 전환 정합).
  μ̃ = μ + ΩR'(RΩR')⁻¹δ, Ω̃ = Ω − ΩR'(RΩR')⁻¹RΩ. Ω = Ψ(I⊗Σ)Ψ'(`companionMA` 공유닻으로 fan·scenario drift 0).
- **엔진** `scenarioPath.py`: `conditionalPath`·`_stackedCov`·`buildScenarios` + `SCENARIO_PRESETS`(긴축 +100bp held·완화 −25bp/월, 6M).
  `MacroSimResult.scenarios` 배선(`_types`·`simulate`·`__init__`). `dartlab.macro('시뮬레이션')` 결과에 동봉.
- **런타임 TS** `macroSimCompute.ts` 동일수식 mirror(companionMA·stackedCov·conditionalPath·buildScenarios) → `computeMacroSim` scenarios 합류.
  contract `MacroSimScenario`. **golden parity 2종**(자유변수 A·조건변수 C byte 일치, 조건 horizon 밴드 붕괴 검증).
- **UI** 다이얼로그 전망 팬에 **기준|긴축|완화 칩**(`mrScenTabs`) + 활성 시 변수별 조건부 q50 **별색(주황) overlay** + **'조건부 가정 · 정책금리 ±…' 배지**.
  MiniFinChart SSOT 불변(별색 1라인, fill 변경 0). `buildMacroSimView(sim, lang, activeScenarioKey)`.
- **정직**: 조건 변수는 조건 horizon 에서 baseline+δ 로 정확 고정 + 밴드≈0(하드 제약 가시). scenario≠forecast 배지·footer.
- **검증**: Python 14(신규 4) · TS parity 6(신규 2) · macroLens 53 · svelte-check 0err · tsc(contracts·runtime) 0.

### ✅ 신용축 편입 — 5→6변수 (커밋 백엔드 `<pending>`·UI `<pending>`)
- **★HY 데이터벽 실측·확정**: `BAMLH0A0HYM2`(ICE BofA US HY OAS)는 FRED meta `observation_start=2023-06-26`
  — **ICE BofA 라이선스로 FRED 가 과거를 truncation**(BAMLC0A0CM 회사채 OAS 도 동일). 대조군 DGS10(1962~)·VIXCLS(1990~)는 full.
  → HY 백필은 *원천 불가*(HF 게이트 아님, 데이터가 FRED 에 없음). **미래 세션 HY 재시도 금지.**
- **대체 = `BAA10Y`**(Moody's Baa 회사채−10Y 스프레드, 1986~ 일별, **이미 SSOT 10119개·MACRO_SERIES 화이트리스트 有**).
  정통 신용스프레드 → **백필·HF 쓰기 0·게이트 0, 순수 코드**(스펙 2곳). `_US_SPECS`·`_KR_SPECS` 6번째 `VarSpec("BAA10Y","신용스프레드","level")`.
- **실측 안정**: US nObs483 eig0.9981·KR nObs315 eig0.9956 (둘 다 <1, fan 유한). 긴축 +100bp 조건부 → 신용스프레드 q50 1.45→1.86 **확대**(긴축→신용경색 정통 전이 포착).
- fan 자동 5장(원유 control 제외, 신용스프레드 포함) + 시나리오 overlay 에 신용 반응. macroLens·contract 무변경(자동). 검증 green(Python14·parity6·lens53·svelte0·tsc0).

### 게이트 (운영자 승인 대기)
- **UI git push 보류** — 공개 터미널 시각 변경(칩·overlay·배지·신용 fan 카드)이라 운영자 눈검수 후 push("푸시해"). commit 완료(백엔드 동반 보류).
- **데이터 publish 불요** — 런타임 계산 + BAA10Y 가 이미 SSOT 에 있어 별도 배선·HF 쓰기 0.

### 🚫 Phase 4 — transmission 정량 브리지: held-out 측정 → **데이터벽 확정(빌드 안 함)**
- **측정**(대표 6社·정유/화학/반도체/자동차/건설, 분기 YoY 매출 vs 거시동인 walk-forward, 스크래치 측정·코드 0):
  - ① 낙관(full-sample 선택 3변수): r2vsPers **+0.31**, 지속성 이김 5/6 — 좋아 보임.
  - ② 엄격(window별 동인 재선택, look-ahead 제거): r2vsPers **−0.28**, 2/6(유가직결 S-Oil·롯데케미칼만 +0.4~0.57).
  - ③ 고정 이론동인 1개(브리지 실제 설계): r2vsPers **−0.74**, **0/6**.
- **판정**: in-sample R²0.73·sign0.85 는 **선택 look-ahead + 매출YoY 자기상관 인플레**. 선택을 honest 하게 할수록 스킬 소멸 →
  회사단 거시→재무 전이는 **표본외에서 지속성(전분기 YoY)도 못 이김**(~37분기 과적합). 유가→정유/화학만 좁게 살아있으나 그조차 단변량선 붕괴.
- **결정**: **정량 브리지 빌드 안 함**(`feedback_plan_score_not_signature` — 검증 실패한 기능 표면화 금지). PRD 05 §5 예견 데이터벽 실측 확정.
  기존 **정성 transmission**(엣지·sign·lag·falsifier·requiredCompanyEvidence·evidence-gate)이 올바른 레벨 — 정량 정밀 참칭 안 함. scenario-simulator 외생축 격상도 동일 사유 보류.
- **은행(금융사)** — *외부데이터 아님(정정)*: 은행 재무는 dartlab 내부에 있음(`interest_income`·`operating_profit` 10/11 분기 채워짐). calcMacroRegression None 의 1차 원인은 매출액 하드코딩(은행은 비표준)이나, **진짜 블로커 = 금융사 패널 깊이 ~3년**(KB·신한 분기 11개 2023Q3~, vs 제조업 41개 2016Q1~). held-out(18분기+ 필요) *측정 자체 불가*. 금융업 XBRL 표준화가 최근만 = **내부 커버리지 갭(이론상 fixable)**, 외부벽 아님. 금리→이자수익은 인과 강해 깊이 확보 시 held-out 통과 가능성 有 — 미측정.

## 결론 — 거시 시뮬레이션 엔진 **완결**
Phase 0~3(BVAR 팬·IRF·국면경로·시나리오 조건부) + 신용축(BAA10Y) 빌드·배포·검증 완료. Phase 4 는 held-out 측정으로 정량 브리지 데이터벽 확정 → 미빌드(정공). 잔여 = ① 금융사 패널 깊이(2023Q3 컷, 금융업 XBRL 표준화 — 내부 fixable) ② HY FRED 라이선스(외부). 둘은 성격이 다르다(①내부 ②외부).

## 결정 로그

- 엔진 거처 = `src/dartlab/macro/simulate/`(L2 macro 내부, scenario-simulator `src/dartlab/simulate/` 와 별개·단방향 브리지). (03)
- 모델 = reduced-form BVAR + Minnesota prior + MC propagation. DSGE·naive bootstrap·포트폴리오 MC 기각. (02·05)
- 검증 척추(보정) = 기능보다 먼저. macroBacktest walk-forward 확장(coverage/CRPS/PIT). (02 §6)
- 배선 = `runMacroSim` → `macro/sim/{kr,us}.json` → HF → `rt.macro.getSim` → macroLens 뷰모델 → 패널/다이얼로그(신규 surface 0). (03·04)
- 결정론 = `np.random.default_rng(SEED)` 로컬. 정직 = fail-closed·넓은밴드·scenario≠forecast·미보정 배지. (05 §7)

## 미결 OQ (착수 시 결정)

- OQ1: BVAR 변수셋 5개 고정 vs 시장별 가변(KR 교역 추가 등). → Phase 0 데모로 coverage 최적 셋 확정.
- OQ2: sim 빌드 cadence — regime 와 동일 주기(sync cron) vs 분기(GDP revision 후만). → 분기 GDP 의존 축은 분기, regimePath 는 regime 주기.
- OQ3: 인터랙티브 커스텀 충격(사용자 슬라이더) pyodide 클라이언트 forward — Phase 3 후 별 트랙(계수 ship 필요). v1 프리셋 discrete.
- OQ4: KR 보정 미달 시 KR fan 영구 holdback vs 단변량 축소. → Phase 0 측정 후.
