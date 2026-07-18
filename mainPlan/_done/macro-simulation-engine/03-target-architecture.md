# 03 · Target Architecture — 모듈·verb·레이어·배선

## §1. 엔진 거처 — `src/dartlab/macro/simulate/`

forecast/·cycles/·crisis/·rates/ 와 **형제**(L2 macro 내부 submodule). 새 L2.5 (scenario-simulator 의 `src/dartlab/simulate/`)와 *별개*.

```
src/dartlab/macro/simulate/
  __init__.py          # 공개 심볼 SSOT (__all__)
  simulate.py          # 진입 — simulateMacro(market, horizon, ...) → MacroSimResult
  bvar.py              # estimateBvar(panel, lag, prior) → BvarFit  (Minnesota 사후)
  fan.py               # forwardFan(fit, horizon, draws, rng) → dict[var→분위경로]
  irf.py               # impulseResponse(fit, shock, horizon) → dict[var→반응]
  regimePath.py        # simulateRegimePath(hamiltonResult, horizon) → forward Markov
  scenarioPath.py      # conditionalPath(fit, shockPath, horizon, rng) → 조건부 경로
  calibration.py       # fanCalibration(market, window) → coverage/CRPS/PIT
  _types.py            # BvarFit, MacroSimResult 등 frozen dataclass
```

- **leaf 수학 재사용**: regimePath 는 `cycles.regimeSwitching.hamiltonRegime` 의 `HamiltonResult`(transitionMatrix·smoothedProbs) 를 입력으로 받기만(재추정 금지·SSOT 호출). fan 의 정합검증 닻 = `crisis.growthAtRisk`. 시나리오 프리셋 = `scenarios.presets` 재사용(충격경로 어댑터).
- **import 방향**(4계층 단방향 준수): `macro/simulate` 는 macro 내부(cycles/crisis/scenarios/seriesFetch)만 import. `src/dartlab/simulate`(scenario-simulator)·Company·analysis 를 **import 안 함**.

## §2. 공개 verb

- 1차: **`dartlab.macro.simulate(market="US", horizon=12, ...)`** → `MacroSimResult`. (forecast 가 `analyzeForecast` 인 것과 동형. `__init__` 에서 `macro.simulate` 로 노출.)
- 명명 충돌 가드: 최상위 `dartlab.simulate(...)`(회사 캐스케이드)와 다르다. `dartlab.macro.simulate` = 거시 변수/국면. docstring·SCHEMA 에 1줄 명시. capability 카탈로그(builder.py)가 둘을 별 ref 로 노출.
- spec.py: `axes` 에 추가 안 함(forecast 축이 이미 "예측"). 대신 `features.simulate` 1줄 + `methods["BVAR"]`·`methods["Minnesota prior"]` 추가.
- EngineCall allowlist: `macro.simulate` 추가(단일 호출 안전 경로).

## §3. 빌드 stage — `pipeline/stages/macro.py::runMacroSim`

`runMacroRegime` 패턴 복제:

```python
def runMacroSim(*, upload=True, token=None) -> StageResult:
    # data/macro/sim/{kr,us}.json  ← simulateMacro(market) 직렬화
    # HF macro/sim/{kr,us}.json push (_deployJson(subdir="sim"))
```

- `runMacro` 오케스트레이터에 합류: data(rc1) 성공 시 cycle·regime·**sim** 빌드(셋 다 FRED bulk 캐시 공유, 상호 독립 — sim 실패가 regime 막지 않음).
- 온라인(API 키 필요) — observations 최신 fetch 후 추정. (offline prebuild 경로는 불요 — sim 은 관측 parquet 만 필요하나 sync 직후가 자연.)
- DATA_RELEASES 에 `macroSim`(dir `macro/sim`) 1줄 등록(regime build 가 `_deployJson` 직접 쓰는 패턴이면 동일 경로). **models/계수 영구 배포 누락 가드**(scenario-simulator 치명교훈 ①: 산출이 ephemeral 에만 남으면 소비처 None) — sim JSON 은 HF push 필수.

## §4. UI 데이터 배선 — 단일 작업대 SSOT

CLAUDE.md "UI 데이터 호출 단일 진입점" 강행 준수:
- 터미널은 `ui/.../runtime/src/data/fetch` + `data/origins` 레지스트리 경유로만 `macro/sim/{kr,us}.json` 로드. 직접 URL·자체 캐시 Map 금지(`checkUiDataWiring` 강제).
- origins 레지스트리에 `macroSim` origin 추가(기존 `macroRegime`/`macroCycle` 패턴). `rt.macro.getSim(market)` 같은 런타임 포트로 노출(기존 `rt.macro.getSeries`·regime 로드와 동형).
- 퍼블릭=로컬 상위집합: dev(:5173 landing)에서 `:8400` 없이 떠야 정상(공개 HF JSON 직독).

## §5. 레이어·회귀 가드

- 4계층: macro=L2. simulate submodule = L2 내부. ✅ 단방향.
- `tests/architecture/test_l15_no_cross_import.py`·import graph census 신규 위반 0.
- 신규 capability docstring = 9섹션 표준(`docstring4Section.py` hook). _attempts 졸업 후 본진(05).
- camelCase/PascalCase: `simulateMacro`·`estimateBvar`·`forwardFan`·`impulseResponse`·`simulateRegimePath`·`conditionalPath`·`fanCalibration`·`runMacroSim` / `BvarFit`·`MacroSimResult`.

## §6. 브리지 — scenario-simulator (Phase 4, 단방향)

- scenario-simulator(`src/dartlab/simulate/`)의 외생 거시축은 현재 *preset 가정*. Phase 4 에서 그 외생축을 **본 엔진 fan 분포로 격상**(preset 한 점 → 분포/시나리오 경로).
- 방향: `src/dartlab/simulate` 가 `dartlab.macro.simulate(...)` 출력을 *소비*(driver prior). `macro/simulate` 는 simulate/ 를 모름. cross-import 0.
- 이 다리는 *선택적·후순위*. v1~v3 는 거시 엔진 자체 + 터미널 거시 표면으로 완결.
