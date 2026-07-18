# 01 · Current State Audit — 이미 있는 것 vs 빠진 것 (코드 실측)

> 원칙: 추측 금지. 아래는 전부 `src/dartlab/macro/**` 실제 코드 Read 로 확인한 사실. file:line 은 점검 시점 기준(재개 시 재확인).

## §1. 이미 있는 것 (재사용 자산)

### 1.1 전향 통계 모델 — `forecast/forecast.py::analyzeForecast`
- **Hamilton Markov Regime Switching** (`cycles/_regimeSwitchingHamilton::hamiltonRegime`) — numpy EM + Kim smoother, 2-regime. 반환 `HamiltonResult`: `params`(mu/sigma per regime), `transitionMatrix`(추정 전이행렬 — **국면경로 forward 의 토대**), `smoothedProbs`(T×2), `currentRegime`, `converged`, `iterations`.
- **GDP Nowcasting** = Kalman Dynamic Factor Model (`forecast/nowcast.py::gdpNowcast`) — Banbura(2011). 공통요인 추출.
- **Cleveland Fed 프로빗** (`clevelandProbit`) — 10Y-3M → 12M 침체확률.
- **Conference Board LEI 복제**(10 구성요소) · **Sahm Rule** — 현재 신호.
- ⚠ 전부 *현재 시점 점추정/현재 확률*. forward 경로·분포는 산출 안 함.

### 1.2 분위 분포 — `crisis/growthAtRisk.py::growthAtRisk`
- FCI(NFCI) 조건부 GDP 성장 분위(gar5/25/median/75/95) + skewness + tailRisk. IMF Growth-at-Risk.
- ⚠ *해석적 분위*(분위수회귀), 단일 horizon. 시간축 fan(여러 h)·MC 경로는 없음. → 본 엔진의 변수 fan 과 상보(GaR=조건부 분위 닻, BVAR fan=동적 경로).

### 1.3 시나리오 — `scenarios/engine.py::runScenario` / `compareScenarios`
- 프리셋(2008·DFAST·금리충격·Dalio 48케이스) → overrides → `summary.analyzeSummary(overrides)` → baseline + delta(score/cycle/crisis/sentiment).
- ⚠ **정적 비교통계(comparative statics)**: override 를 *현재 입력*에 적용해 *현재 종합점수* 재계산. 시간축 forward 경로 아님. `meta.transmission` 은 프리셋 텍스트 라벨(계산된 동적 경로 아님). → 본 엔진이 *동적*으로 승계(시나리오 조건부 forward).

### 1.4 전파 — `transmission/transmission.py::analyzeTransmission`
- driver(USDKRW·BASE_RATE·CPI·EXPORT·DGS10·HY·WTI) → sector → financialLine → valuationLever 엣지 레지스트리. `sign`·`lagMonths`·`evidenceLevel`(OBS/PRIOR/TPL).
- ⚠ *정성 부호·시차 prior*(회귀계수 아님). → 본 엔진 IRF 의 **부호 prior** + Phase 4 "IRF→섹터/기업" 다리의 토대.

### 1.5 검증 척추 — `forecast/macroBacktest.py::walkForwardBacktest`
- rolling re-estimation(Fed 2019): startDate~endDate 를 stepMonths 순회 → 각 asOf 에서 `analyzeCycle`/`analyzeForecast` 재실행 → NBER 침체와 confusion matrix → precision/recall.
- ✅ **look-ahead 차단 규율·walk-forward 골격이 이미 있다**. → fan coverage/CRPS/PIT 로 *확장*(02 §4). KR 은 NBER 대체(BOK 경기순환) 필요.

### 1.6 빌드·배선 — `pipeline/stages/macro.py`
- `runMacro`(오케스트레이터): `runMacroData`(FRED/ECOS/customs → `data/macro/{fred,ecos,customs}/observations.parquet`) → `runMacroCycle`(→ `macro/cycle/{kr,us}.json`) → `runMacroRegime`(→ `macro/regime/{kr,us}.json`).
- `runMacroRegime` 가 이미 forecast 4모델 + rates 곡선 + GaR + **Hamilton band**(`smoothedProbs[-24:,1]` = *과거* 24분기 수축확률)를 JSON 으로 직렬화·HF push. vintage(staleAfterDays)·5%p 반올림·분리도 게이트·fail-closed("표시 보류") 패턴 확립.
- `runMacroJson`(prebuild, offline): `macro.json`(대시보드 v20) — transmission 등.
- → 본 엔진은 **`runMacroSim` 신설**(같은 패턴, `macro/sim/{kr,us}.json`). regime build 의 fail-closed·vintage·결정론 규율 그대로 계승.

### 1.7 공개 메타 — `macro/spec.py`
- 14축(cycle/rates/assets/sentiment/liquidity/forecast/crisis/inventory/corporate/trade/transmission/summary). `features.scenario`(overrides)·`features.backtest`(asOf)·`methods`(Hamilton/DFM/NS/...). → `simulate` 축/feature 추가 지점.

## §2. 빠진 것 (신설 대상)

| 빠진 기능 | 왜 없나 | 신설 위치 |
|---|---|---|
| **VAR/BVAR 다변량 동적 시스템** | forecast 는 단변량 모델 합산(probit·Sahm·LEI 독립). 변수 간 동적 상호작용·공동 forward 없음 | `macro/simulate/bvar.py` |
| **변수 forward fan(분위 경로)** | GaR=단일 horizon 분위, Hamilton=현재 확률. 여러 h 의 분위 경로 없음 | `macro/simulate/fan.py` |
| **충격반응 IRF** | 전혀 없음. transmission=정성 부호뿐 | `macro/simulate/irf.py` |
| **국면경로 forward(Markov)** | regime band=*과거* smoothedProbs. 전이행렬로 *미래* 굴리는 함수 없음 | `macro/simulate/regimePath.py` |
| **시나리오 조건부 forward** | runScenario=정적 스냅샷. 충격 고정 + 나머지 동적 시뮬 없음 | `macro/simulate/scenarioPath.py` |
| **fan 보정 측정** | macroBacktest=침체 precision/recall(이진). 분포 보정(coverage/CRPS/PIT) 없음 | `macro/simulate/calibration.py`(또는 macroBacktest 확장) |
| **sim 빌드 stage** | runMacroRegime=과거 band 만 | `pipeline/stages/macro.py::runMacroSim` |
| **터미널 forward 뷰** | macroLens 뷰모델=판정·과거. forward fan/IRF/국면경로 뷰 없음 | `terminal/lib/macroLens.ts` + 패널/다이얼로그(04) |

## §3. 핵심 통찰

- **신설은 "마지막 forward 층" 한 묶음**(BVAR + fan + IRF + regimePath + scenarioPath + calibration). 통계 엔진(Hamilton EM·DFM·GaR)·검증 골격(walkForward)·빌드 배선·fail-closed 규율은 *전부 재사용*.
- **regime band 의 미래 대칭**: 이미 `smoothedProbs[-24:]`(과거)를 ship 한다. 같은 `HamiltonResult.transitionMatrix` 로 forward Markov → `regimePath[1..H]`. Phase 1 = 거의 공짜.
- **GaR = fan 의 닻**: 변수 fan(BVAR)이 GaR 의 조건부 분위와 현재 시점에서 정합해야(GaR median ≈ fan p50 at h matching). 교차검증 포인트.
