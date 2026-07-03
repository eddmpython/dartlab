# 01. 아키텍처 확정 + ExpectationSpec 계약

## 1. 배치 확정 (import 방향 증명 포함)

```
L1.5 synth      : 계약(ExpectationSpec·ExpectationScore) + 채점 순수수학      ← 모든 L2 가 import 가능
L2   각 엔진    : 발행 verb 만 소유 (이미 존재, 원장 무지)                    ← 신설 코드 0 원칙
L2.5 simulate   : 수집자(collector) + 원장 IO + 채점 오케스트레이션 + 성적표   ← 유일한 기록자
CI   sync       : 사이클 트리거(월·분기) + HF 업로드                          ← online 전용
UI   terminal   : 성적표 뷰 (origins `hf` 직독)                              ← 공통배선
```

방향 증명: simulate(L2.5)→L2(macro·analysis·credit·quant) 호출 합법(시뮬 01:53), L2→synth(L1.5) 합법, L2→simulate 불법(`test_import_direction` downward-only). 따라서 "엔진이 원장에 쓴다"는 구조는 불가능하고, "simulate 가 엔진을 호출해 받아 적는다"만 성립한다. synth 는 4형제(scan/frame/reference) cross-import 없이 dataclass+순수함수만 가지므로 L1.5 계약 위반 없음.

## 2. 신설 파일 + 함수 (전량)

### 2.1 `src/dartlab/synth/expectationSpec.py` (신설, L1.5)

```python
@dataclass(frozen=True)
class ExpectationSpec:            # 발행 봉인 행. frozen = 불변 원칙의 코드 표현
    expectationId: str            # {domain}.{variable}.{freq}.{horizon}@{issuedAt:YYYYMMDDTHHMM}
    schemaVersion: int            # 1
    domain: str                   # "macro" | "revenue" | "earnings" | "credit" | "price"
    variable: str                 # 예 "KR.CPI.yoy" · "005930.revenue" · "005930.grade"
    unit: str                     # "%", "KRW", "grade", "prob"
    freq: str                     # "M" | "Q" | "Y"
    horizon: int                  # freq 단위 몇 기 앞
    targetPeriod: str             # 채점 대상 기 (예 "2026-08" · "2026Q3")
    issuedAt: str                 # UTC ISO. 봉인 시각 (원장의 심장)
    issuedLive: bool              # False = backfill (공개 성적 혼합 금지)
    asOf: str                     # 사용 데이터 vintage (시뮬 02 VintageRef.asOf 동형)
    engine: str                   # 공개 verb 경로 (예 "macro.simulate.simulateMacro")
    engineVersion: str            # 예 "bvar-v1" · "revenueForecast-v4"
    kind: str                     # "quantiles" | "direction"
    quantiles: dict | None        # {"p5":..,"p25":..,"p50":..,"p75":..,"p95":..}
    direction: dict | None        # {"prob": 0~1, "predicted": "up"|"down"}
    baselines: dict               # {"randomWalk": {...quantiles}, "persistence": {...}, "seasonalNaive": {...}|None}
    sourceRefs: tuple[str, ...]   # 근거 ref
    warnings: tuple[str, ...]     # 발행 시점 한계 라벨

@dataclass(frozen=True)
class ExpectationScore:           # 채점 행. 발행 행과 분리 append
    expectationId: str
    scoredAt: str                 # UTC ISO
    actual: float | str           # 실제값 (등급이면 str)
    actualAsOf: str               # 실제값 조회 vintage (revision 정직)
    revisionPolicy: str           # "latest" (현 HF macro surface 실태 명시)
    coverageHit90: bool | None    # actual ∈ [p5, p95]
    coverageHit50: bool | None    # actual ∈ [p25, p75]
    pit: float | None             # F(actual), 분위 보간
    crps: float | None            # 분위 기반 pinball 평균
    crpsBaseline: dict            # baseline 별 crps
    skill: float | None           # 1 - crps / min(crpsBaseline.values())  (가장 센 baseline)
    brier: float | None           # direction 전용
    error: str | None             # 실제값 조회 실패 사유 (실패도 기록)
```

순수함수 (numpy 불요, stdlib 만):
- `buildExpectationId(domain, variable, freq, horizon, issuedAt) -> str`
- `pinballLoss(quantiles: dict, actual: float) -> float` (p5~p95 분위 평균 = CRPS 근사, 시뮬 03:215)
- `pitValue(quantiles: dict, actual: float) -> float` (분위 선형보간)
- `scoreExpectation(spec: ExpectationSpec, actual, *, actualAsOf) -> ExpectationScore` (위 조합)
- `aggregateCalibration(scores: list[ExpectationScore]) -> dict` (coverage 비율·PIT 히스토그램·평균 skill·n)

### 2.2 `src/dartlab/synth/calibrationMetrics.py` (승격 이동)

현 `analysis/forecast/calibrationMetrics.py`(Brier + reliability bins) 본문을 이동, 원위치는 `from dartlab.synth.calibrationMetrics import *` re-export stub 로 대체(identity 보존, 기존 호출부 무변경). 승인 A3.

### 2.3 `src/dartlab/simulate/expectationLedger.py` (신설, L2.5)

- `LEDGER_SUBDIR = "expectations"` (data/expectations/, `DARTLAB_DATA_DIR` env resolver = 09 P9b 패턴)
- `appendExpectations(rows: list[ExpectationSpec]) -> Path` : 연도 shard parquet append (`expectations_{yyyy}.parquet`). 동일 expectationId 존재 시 ValueError(불변 강제)
- `appendScores(rows: list[ExpectationScore]) -> Path` : `scores_{yyyy}.parquet`
- `readExpectations(*, domain=None, variable=None, unscoredOnly=False) -> pl.DataFrame`
- `readScores(...) -> pl.DataFrame`

### 2.4 `src/dartlab/simulate/expectationCycle.py` (신설, L2.5 오케스트레이터)

- `issueMacro(*, market="KR", asOf=None, live=True) -> list[ExpectationSpec]`
  : `macro.simulate.simulateMacro(market, horizon=12, asOf)` 호출 → KR 3변수(CPI·BASE_RATE·USDKRW)의 h=1/3/6/12 분위 fan 을 ExpectationSpec 화. baseline 은 같은 시리즈의 random-walk·persistence·seasonal-naive 를 즉석 산출해 동시 봉인.
- `issueRevenue(codes: list[str], *, asOf=None, live=True) -> list[ExpectationSpec]`
  : `analysis.forecast.forecastRevenue` 호출 → 분기 매출 분위화(3-시나리오를 p25/p50/p75 근사 + 명시 warning) + direction(v4). 09 P9c `recordForecast` facade 경유로 기록 일원화.
- `issueEarnings(codes, ...)` (P4) : revenue 기대 + margin 경로를 `simulate.runScenario` proforma 로 전개 → 영업이익·순이익·FCF 행.
- `issueCredit(codes, ...)` (P5) : credit 등급 + `forwardPdLadder` 를 direction/quantiles 화. `recordGrade` 이력과 이중 기록 안 나게 adapter 로 흡수.
- `scoreDue(*, now=None) -> list[ExpectationScore]`
  : `readExpectations(unscoredOnly=True)` 중 targetPeriod 도래 행의 실제값 조회(macro=`seriesFetch`·revenue=panel) → `scoreExpectation` → append. 조회 실패 = error 봉인 행.
- `buildScorecard() -> dict` : 변수·도메인별 `aggregateCalibration` 집계 + 표본 게이트 라벨 부착 → `scorecard.json` (터미널 소비 산출물)

### 2.5 `.github/scripts/sync/buildExpectations.py` (신설, CI 전용)

`--cycle monthly|quarterly` : issue* + scoreDue + buildScorecard 실행 후 `uploadCategoryToHf("expectations")`. 기존 `buildMacroData.py`·`uploadData.py` 패턴 복제. cron 배선은 기존 sync workflow 에 job 추가.

### 2.6 `src/dartlab/core/dataConfig.py` (1줄 추가, 승인 A1)

```python
"expectations": {"dir": "expectations", "label": "기대치 격자 원장 (발행 봉인 + 사후 채점, append-only)", "public": True},
```
flat + tabular 이므로 다운로드 센터 자동 노출. `_PARQUET_KIND` 에 `"expectations": "series"` 추가.

### 2.7 UI (P6, 별도 눈검수 게이트)

- origins: 기존 `hf` origin 재사용 (신규 origin 불요, `originUrl("hf", "expectations/scorecard.json")`)
- `ui/packages/surfaces/src/terminal/` 에 성적표 패널 1개. fetch 단일 진입점(`data/fetch/request.ts`) 경유. **UI 변경은 자동 push 금지 규칙 적용(운영자 눈검수 후 push)**.

## 3. 기존 자산 매핑 (재사용 vs 신설)

| 필요 능력 | 기존 자산 (실측) | 처리 |
|---|---|---|
| macro 분위 fan (asOf 지원) | `macro/simulate/simulateMacro` KR 6변수, `fan.py::forwardFan` p5~p95 | 그대로 호출 |
| macro rolling 캘리브레이션 | `macro/simulate/calibration.py::fanCalibration` | P0 backfill 사전점검에 재사용 |
| 매출 예측 | `analysis/forecast/forecastRevenue` v3/v4 | 그대로 호출 |
| 매출 기록/채점 | `forwardTest.py` ForwardTestRecord·saveForecast·evaluate·evaluateCalibration | P3 에서 원장 backend 로 redirect (A2), 시그니처 유지 |
| 이진 캘리브레이션 | `analysis/forecast/calibrationMetrics.py` | synth 승격 (A3) |
| 손익 전개 | `simulate/` 4노드 DAG (`runScenario`, proforma-FCFF) | P4 에서 호출 |
| 신용 이력 | `credit/monitoring/history.py::recordGrade` + `scoring/migration.py` | P5 adapter |
| 주가 방향확률 | `analysis/forecast/_simMonteCarlo` upsideProbability + `_signalsDirection` | P5, 방향+구간만 |
| HF 업로드 | `pipeline/hfUpload.py::uploadCategoryToHf` (CommitOperationAdd 배치) | 그대로 호출 |
| look-ahead 봉인 | `Company.panel(asOf=)` + `ai/tools/lookAheadGuard.py` 패턴 | asOf 규약 상속 |

신설 순수 신규 = 계약 dataclass 2 + 순수함수 5 + 원장 IO 4 + 오케스트레이터 6 + CI 스크립트 1 + DATA_RELEASES 1줄. 예측 알고리즘 신설 0.

## 4. 저장 설계

- 로컬 SSOT: `data/expectations/expectations_{yyyy}.parquet` + `scores_{yyyy}.parquet` + `scorecard.json`
- HF: `eddmpython/dartlab-data` 하위 `expectations/` (public). 쓰기 = CI(sync online)만, 읽기 = 런타임 직독(터미널·로컬 공통배선). `sync=online / prebuild=offline` 3가드 규율 그대로.
- append-only 강제: appendExpectations 가 기존 id 충돌 시 raise + parquet 는 행 추가만. 정정이 필요한 경우 = 새 행 + `supersedes` 필드가 아니라 **불허** (발행 실수도 이력이다. warning 행으로만 주석).

## 5. 이중 기록 방지 (사일로 3개의 수렴)

1. `forwardTest` `~/.dartlab` JSON → P3 에서 backend 를 원장으로 redirect (함수 시그니처 유지, 09 P9b 이행). 옛 로컬 파일은 마이그레이션하지 않는다(라이브 원장 오염 방지, backfill 규약 02 §5 로만 흡수 가능).
2. `credit` history JSON → 유지(엔진 내부 SSOT) + P5 adapter 가 등급 발행 시점에 ExpectationSpec 행을 병행 발행. 원장은 "기대"만 담고 이력 원본은 credit 소유 유지.
3. `driverPanel.json`(models, 시뮬 admission 소관) → 본 플랜 범위 밖. DATA_RELEASES `"models"` 키는 시뮬 fatal③ 진행 시 별도.

## 6. 공개 API 방침 (v1)

`dartlab.__all__` 신규 심볼 0 (publicApiCoverage 게이트 무접촉). 성적표 소비는 HF 직독. 공개 verb 승격(`dartlab.simulate` 하위 노출)은 원장 N 축적 후 별도 판단. 신규 src 모듈이므로 push 전 CI 선제 2종(src↔tests 미러 + productSmoke quick) 실행 규약 준수.
