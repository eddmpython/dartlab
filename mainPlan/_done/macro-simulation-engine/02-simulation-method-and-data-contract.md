# 02 · Simulation Method & Data Contract

> 재조사 없이 구현 가능하도록 *방법·수식·시드·출력 스키마*를 못박는다.

## §1. 모델 핵심 — Reduced-form BVAR + MC propagation

### 1.1 왜 BVAR (DSGE 아님)
- 거시 forward 의 업계 표준 work-horse. 변수 간 *동적 상호작용*을 데이터에서 추정(IRF·조건부 예측 가능).
- **Minnesota prior(BVAR)** = 짧은 표본 정규화의 교과서적 해법. 내가 1라운드에서 깐 "연 12관측" 약점을 prior shrinkage 로 흡수(과적합 차단). KR GDP 분기·월 혼합 표본이 짧아 *필수*.
- DSGE는 비-목표(05 kill-list): 연 단위 캘리브레이션·취약.

### 1.2 변수셋 (시장별, 월 빈도 정렬)
- **US**: `INDPRO`(성장) · `CPIAUCSL`(물가) · `FEDFUNDS`(정책금리) · `DGS10`(장기금리) · `BAMLH0A0HYM2`(신용). 5변수.
- **KR**: `IPI`(성장) · `CPI`(물가) · `BASE_RATE`(정책금리) · `USDKRW`(환율) · `EXPORT`(교역). 5변수.
- 전부 기존 `observations.parquet`(`macro/{fred,ecos}`)에 존재(MACRO_SERIES 화이트리스트·transmission DRIVERS 와 정합). 추가 수집 0.
- 변환: 정상성(stationarity) 위해 레벨/로그차분/YoY 를 변수별 고정 매핑(spec). 비정상 변수는 차분 후 추정, 출력 시 누적 환산.

### 1.3 추정
- VAR(p), p=lag(기본 6개월, 정보기준 AIC/BIC 로 2~12 탐색). Minnesota prior 하이퍼파라미터(λ1 전체 tightness·λ2 cross-variable·λ3 lag decay) 고정 스펙(02 §6 부록).
- 추정 = 정규-역위샤트 켤레 사후(conjugate Normal-Inverse-Wishart) → 계수 사후 + 충격 공분산 Σ 사후. numpy/scipy 선형대수만(외부 무거운 라이브러리 없음 — Hamilton EM 패턴 계승).
- **결정론**: 추정은 parquet 결정 함수(난수 0). 사후 draw 만 seed.

## §2. Forward Fan (변수 분위 경로)

1. 사후에서 (계수, Σ) 를 M회 draw(파라미터 불확실성 포함 — 좁은 밴드 방지의 핵심).
2. 각 draw 마다 t=1..H 충격 ε_t ~ N(0, Σ) 샘플 → VAR 식 forward 반복 → 변수 경로 1개.
3. M개 경로 → 각 변수·각 h 의 분위(p5/p25/p50/p75/p95) = **fan**.
4. 비정상 변수는 차분 경로 누적 → 레벨/지수 환산(출력은 사용자가 읽는 단위).
- M 기본 2000(결정론·속도 타협). H 기본 12(월) / 24 옵션.
- **seed**: `np.random.default_rng(SEED)` *로컬 인스턴스*(전역 `np.random.seed` 금지 — scenario-simulator `random.Random` 교훈의 numpy 판). SEED 는 시장·빌드 고정 상수(예 20260624). 같은 parquet+seed = 동일 fan.

## §3. IRF (충격반응)

- 직교화 충격(Cholesky, 변수 순서 = 정책 변수 후행 표준 재귀식별; 순서는 spec 고정). 단위 = 1 표준편차 또는 라벨 충격(금리 +100bp).
- 각 변수의 h=0..H 반응 + 사후 draw 분위 밴드(68/90%).
- **부호 게이트**: transmission DRIVERS 의 정성 `sign` 과 IRF 부호가 충돌하면 "부호 이론충돌" 플래그(졸업 게이트 AC). 예: 금리↑→성장 반응이 +면 식별 의심.

## §4. Regime Path (국면경로 forward)

- 입력: `HamiltonResult.transitionMatrix` P(2×2) + 현재 평활확률 π_0 = `smoothedProbs[-1]`.
- forward: π_h = π_0 · P^h → 각 h 의 P(수축). 해석적(MC 불요) + 파라미터 불확실성은 GDP 표본 부트스트랩 재추정 K회로 밴드(선택).
- 출력 = `regimePath[h] = {h, pContraction, pBandLo, pBandHi}`, h=1..H.
- **기존 regime band(과거)와 한 SVG 로 이음**: 과거 `smoothedProbs[-24:]` + 미래 `regimePath` = 연속 곡선(현재 시점 = 경계선). 04 시각문법.

## §5. Scenario-Conditional Path

- 입력: 충격 경로 고정(예 FEDFUNDS 를 향후 6개월 −25bp/월). 조건부 시뮬 = 고정 변수에 충격 주입 후 나머지 변수 forward(conditional forecast, Waggoner-Zha 스타일 단순화: 고정 경로를 달성하는 충격을 매 스텝 후진 풀이).
- 출력 = 각 변수 조건부 경로 + 밴드. baseline fan 과 *대비*(delta band).
- 기존 `runScenario` 프리셋(2008·금리충격 등)을 *충격 경로*로 재해석해 재사용(프리셋 overrides → 충격 경로 매핑 어댑터). **정적 스냅샷 → 동적 경로 승계**.
- 정직: "조건부 가정" 라벨 강제. scenario≠forecast.

## §6. 보정·검증 (Calibration — 기능보다 먼저)

`macroBacktest.walkForwardBacktest` 확장 또는 `simulate/calibration.py` 신설:
- rolling re-estimation 각 asOf 에서 fan 생성 → 실현값과 비교:
  - **coverage**: 80% 밴드가 실현값을 덮은 비율(명목 0.80 근방이어야 보정). 변수·horizon 별.
  - **CRPS**(연속 순위확률점수): fan 분포 vs 실현 점. 낮을수록 좋음. baseline(랜덤워크 fan) 대비 skill.
  - **PIT**(확률적분변환) 균등성: 분포 보정의 KS 검정(p>0.05 = 보정).
- regimePath 는 기존 precision/recall 계승 + Brier score(확률 보정).
- **게이트**: 미보정 모델은 터미널 표면에 안 올림("표시 보류"). 보정 메타를 sim JSON 에 동봉.

## §7. 출력 데이터 계약 — `macro/sim/{kr,us}.json`

`runMacroRegime` JSON 패턴 계승(축별 try/except·fail-closed·vintage·asOf). 스키마:

```jsonc
{
  "market": "US",
  "computedAt": "2026-06-24T...Z",
  "asOf": "2026-05-01",          // 추정에 쓴 최신 관측일(look-ahead 차단)
  "seed": 20260624,
  "horizon": 12,
  "model": {                      // 모델 스펙·정직 메타
    "kind": "BVAR",
    "lag": 6,
    "prior": "minnesota",
    "vars": ["INDPRO","CPIAUCSL","FEDFUNDS","DGS10","BAMLH0A0HYM2"],
    "nObs": 420,                  // 표본 N
    "draws": 2000,
    "status": "ok"               // ok | "표본 부족·표시 보류" | "미수렴" 등
  },
  "fan": {                        // 변수별 분위 경로
    "INDPRO": {
      "unit": "지수", "transform": "log-diff→cumulate",
      "months": ["2026-06", ...],          // h=1..H 라벨
      "p5":[...],"p25":[...],"p50":[...],"p75":[...],"p95":[...],
      "history": [...]            // 최근 N개월 실측(차트 연결용)
    }, ...
  },
  "irf": {                        // 충격별 변수 반응
    "FEDFUNDS+100bp": {
      "shockLabel": "정책금리 +100bp",
      "responses": { "INDPRO": {"h":[0,1,..],"mid":[...],"lo":[...],"hi":[...]}, ... },
      "signCheck": { "INDPRO": "ok", ... }   // transmission 부호 정합
    }, ...
  },
  "regimePath": {
    "history": [...],            // 과거 smoothedProbs[-24:] (band 재사용)
    "forward": [ {"h":1,"pContraction":0.31,"lo":0.22,"hi":0.41}, ... ],
    "separation": 0.83, "converged": true
  },
  "scenarios": [                  // 시나리오 조건부 경로
    { "name":"금리 인하 사이클", "shockPath": {"FEDFUNDS":[-0.25,...]},
      "fan": { "INDPRO": {"p50":[...],"p5":[...],"p95":[...]}, ... },
      "label":"조건부 가정" }
  ],
  "calibration": {               // §6 산출(빌드시 또는 주기 재측정)
    "coverage80": {"INDPRO": 0.79, ...}, "crpsSkill": {...},
    "pitKsP": {...}, "measuredOn": "2010-2024 walk-forward",
    "status": "calibrated" | "uncalibrated·표시 보류"
  },
  "missing": [ {"id":"...","status":"...","reason":"..."} ]
}
```

- **크기 가드**: fan/irf 경로는 분위만(전체 M draw 미저장). 예상 < 200KB/시장.
- **vintage**: BVAR/regimePath = 분기 GDP revision 영향 → `staleAfterDays` 동봉(regime build `_STALE_QUARTER=120` 패턴).
- **부재 처리**: 시장·축 실패는 `missing` + `status` "표시 보류"(절대 0 대체 금지).

## §8. 결정론·성능 요약
- 추정=결정(난수0) / draw=로컬 rng(seed 고정) → byte-동일 출력(수용기준 §8).
- 빌드: BVAR 추정 + 2000 draw forward = 시장당 수 초(numpy 벡터화). CI sync 에서 충분. → **계수·분위를 CI 에서 precompute → JSON ship**(터미널은 렌더만). 인터랙티브 커스텀 충격(사용자 슬라이더)은 Phase 후반 pyodide(계수 ship 후 클라이언트 forward) — v1은 프리셋 시나리오 discrete set.
