# 거시 시뮬레이션 엔진 PRD (macro-simulation-engine)

> **한 줄**: dartlab 거시 엔진을 *현재 판정·과거 재현*에서 **미래를 확률적으로 굴리는 동적 시뮬레이션**까지 확장한다 — BVAR 팬차트 + 충격반응(IRF) + 국면경로(Markov forward) + 시나리오 조건부 경로 + 보정(calibration) 검증 척추. 터미널 거시 패널·다이얼로그에 배선.

## 문서 지도

| # | 문서 | 내용 |
|---|---|---|
| 00 | [product-prd](00-product-prd.md) | 비전·목적·청중·"빠진 한 층"·정직/시그니처 프레이밍·수용기준 |
| 01 | [current-state-audit](01-current-state-audit.md) | 이미 있는 것(Hamilton·DFM·probit·Sahm·scenario·transmission·macroBacktest) vs 빠진 것(forward 확률 시뮬) — 코드 실측 |
| 02 | [simulation-method-and-data-contract](02-simulation-method-and-data-contract.md) | BVAR(Minnesota prior)·IRF·regime-path Markov·MC fan·결정론(seed)·출력 JSON 스키마·보정(CRPS/PIT/coverage) |
| 03 | [target-architecture](03-target-architecture.md) | `src/dartlab/macro/simulate/` 신설·공개 verb·레이어·scenario-simulator(`src/dartlab/simulate/`)와 단방향 브리지·빌드 stage |
| 04 | [ui-ux-wiring](04-ui-ux-wiring.md) | 터미널 패널/다이얼로그 확장·새 시뮬 섹션·MiniFinChart SSOT·데이터층 배선·정직 footer·팬/IRF/국면경로 시각문법 |
| 05 | [scope-phasing-guardrails](05-scope-phasing-guardrails.md) | 4 Phase·졸업 게이트(`_attempts`)·kill-list·정직 가드·롤백 |
| 06 | [progress-ledger](06-progress-ledger.md) | NEXT 포인터·결정 로그·커밋 규약 |

## ★ scenario-simulator 와의 관계 (중복 0 — 반드시 먼저 읽기)

`mainPlan/scenario-simulator/`(13문서 v0.5, 엔진 `src/dartlab/simulate/`)가 이미 있다. 그건 **회사 pro-forma → 밸류·신용 캐스케이드**용이고, 그 정직 척추 §5문서에 못박힌 결정이:

> **"거시 미래경로 예측 부재 — preset 가정으로 받는다. scenario ≠ forecast."**

즉 scenario-simulator는 거시 미래를 *사용자가 if-토글로 설정하는 외생축*으로 받는다. **본 PRD가 그 일부러 비워둔 상류 구멍을 메운다** — 거시 미래경로를 확률적으로 *생성*한다.

```
[본 PRD: macro/simulate]                    [기존: src/dartlab/simulate]
거시 변수·국면 forward 확률 생성    ──단방향──▶   회사 pro-forma·밸류·신용 캐스케이드
(BVAR fan · IRF · regime-path)      (Phase 4)    (외생 거시축을 preset 대신 본 엔진 분포로 채움)
```

- 경계: macro/simulate = **거시 변수/국면 레벨**(Company 미접촉). simulate/ = **회사 레벨**.
- import 방향: `macro/simulate` 는 `src/dartlab/simulate` 를 import 하지 않는다(L2↔L2.5 cross 금지). 브리지는 simulate/ 가 *나중에* macro/simulate 출력을 외생 driver prior 로 소비하는 한 방향뿐(Phase 4, 선택).
- 두 엔진의 정직 척추는 다르다: scenario-simulator = "예측 안 함(scenario)". macro-simulate = "예측하되 *보정된 분포 + held-out 검증*으로 정직하게". 섞으면 둘 다 흐려지므로 분리.

## 핵심 결정 요약

- **엔진 거처**: `src/dartlab/macro/simulate/` (forecast/·cycles/·crisis/ 형제, L2 macro 내부). 공개 verb `dartlab.macro.simulate(...)`.
- **재사용 우선**: Hamilton 전이행렬(`cycles/_regimeSwitchingHamilton`)·GaR(`crisis/growthAtRisk`)·forecast 4모델·macroBacktest 검증 척추 전부 재사용. 신설 = BVAR 추정 + forward MC 루프 + IRF 한 묶음.
- **배선**: 새 빌드 stage `runMacroSim` → `macro/sim/{kr,us}.json` → HF → 터미널 `rt.macro` 로드 → macroLens 뷰모델 → 패널/다이얼로그.
- **결정론**: `np.random.default_rng(SEED)` 로컬 인스턴스(전역 seed 금지 — scenario-simulator 교훈). 같은 parquet+seed = byte-동일 출력.
- **정직 우선**: 검증 척추(fan coverage·CRPS·PIT, macroBacktest 확장)를 **기능보다 먼저**. 넓은 밴드·가정 라벨·look-ahead 차단·fail-closed.
- **졸업 게이트**: `tests/_attempts/macroSimEngine/` 개념검증(IRF 부호 이론 일치·held-out coverage≈명목) 후에만 본진.

**상태**: 설계 초안 v0.1 (착수 전 운영자 go 대기). 재개 = [06-progress-ledger](06-progress-ledger.md) NEXT.
