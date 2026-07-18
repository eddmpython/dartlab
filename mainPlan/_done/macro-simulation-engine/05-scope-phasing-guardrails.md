# 05 · Scope · Phasing · Guardrails

## §1. Phase 0 — 졸업 게이트 개념검증 (`tests/_attempts/macroSimEngine/`)

CLAUDE.md 강행: 신규 능력은 `_attempts` 에서 개념확립 후에만 `src/dartlab/`. 본진 직행 금지.

- **데모 실측**: observations.parquet 로 US 5변수 BVAR 추정 → fan/IRF/regimePath 산출. README + 결과 docstring.
- **go/no-go AC**:
  1. IRF 부호가 경제이론·transmission `sign` 과 일치(금리↑→성장↓, 금리↑→물가 시차후↓). 충돌 시 식별 재검.
  2. held-out walk-forward 에서 80% 밴드 coverage ∈ [0.72,0.88]. PIT KS p>0.05.
  3. 결정론: 2회 실행 byte-동일.
  4. KR 표본 충분성: KR 5변수 BVAR 이 미수렴/분리약함이면 KR 은 fail-closed("표시 보류")로 출시, US 먼저.
- **no-go 시**: BVAR 대신 단변량 fan(GaR 시간축 확장)으로 축소 — 단 그것도 보정 게이트 통과해야. 억지 출시 금지(`feedback_plan_score_not_signature`).

## §2. Phase 1 — 국면경로 forward (최소·즉시 가시)
- `simulate/regimePath.py` + sim JSON `regimePath.forward` + 좌측 패널 1줄(04 §2) + 다이얼로그 3a.
- Hamilton 전이행렬 재사용 → 추가 모델 0. 가장 싼 윈. 보정 = Brier/precision-recall(기존 척추).
- **출시 단위**: regimePath 만 담은 sim JSON + 패널/다이얼로그 국면경로. 팬/IRF 미포함 섹션은 피처게이트 미렌더.

## §3. Phase 2 — BVAR 변수 팬 + IRF
- `bvar.py`·`fan.py`·`irf.py`·`calibration.py` + sim JSON `fan`/`irf`/`calibration` + 다이얼로그 3b/3c + footer.
- **보정 먼저**: calibration.py + held-out 측정이 fan 표면화의 전제. 미보정이면 "참고용" 배지.

## §4. Phase 3 — 시나리오 조건부 forward
- `scenarioPath.py` + sim JSON `scenarios` + 다이얼로그 3d overlay. 기존 `runScenario` 프리셋→충격경로 어댑터. 정적 스냅샷 엔진은 유지(BC), 동적은 추가.

## §5. Phase 4 — 브리지 (선택·후순위)
- IRF→transmission→섹터/기업 타격(transmission edges 정량화 시작). + scenario-simulator 외생축을 본 엔진 분포로 격상(03 §6, 단방향).
- 데이터 벽 정직: transmission 회사단 커버리지는 segmentRnd 류 벽 가능 → held-out 측정 후 점진.

## §6. Kill-list (안티패턴 — 절대 금지)
- DSGE / naive bootstrap MC / 포트폴리오 수익 MC(지금) / 전역 seed / 새 거대 surface(지금) / MiniFinChart 즉흥 변경(밴드 fill은 Phase2 신중) / scenario-simulator cross-import / 결손 0 대체 / look-ahead / 점추정 가짜정밀(밴드 없는 단일 경로 표면화).
- **점수 인플레 금지**: 미빌드 기능에 패널 uplift 로 planScore 올려 시그니처 주장 금지. 검증 척추(보정) 먼저.

## §7. 정직 가드 (코드 강제 포인트)
- fail-closed: 미수렴/표본부족/미보정 → `status:"...표시 보류"` + `missing[]`. regime build 패턴 계승.
- 결정론: `np.random.default_rng(SEED)` 로컬만. 전역 seed grep 가드(scenario-simulator kill-test 패턴).
- look-ahead: 추정·시뮬 asOf 이전만. walk-forward 규율.
- 라벨: scenario≠forecast footer. 미보정 배지. 표본 N·seed 노출.

## §8. 회귀·테스트 롤백
- 신규 테스트: `tests/macro/test_macro_simulate.py`(BVAR 추정·fan 분위 단조·IRF 부호·결정론) + `macroLens.test.ts`(뷰모델). 실행 = `bash tests/test-lock.sh tests/macro/test_macro_simulate.py -v`(메모리 가드).
- 기존 영향: `pipeline/test_macro_stage.py`(runMacro 에 sim 합류 — sim 실패가 regime 안 막음 검증). Guard Index·import census 신규 위반 0.
- 롤백: Phase 단위 commit. sim stage·JSON·UI 섹션 각각 피처게이트라 `git revert <sha>` + sim JSON 미배포면 터미널 자동 미렌더(무중단). DATA_RELEASES 등록 별도 revert.

## §9. 메모리 OOM 가드 (CLAUDE.md)
- BVAR 추정은 numpy(작은 5×5 시스템) — Polars 힙 무관. 단 빌드 stage 가 observations.parquet 읽을 때 module-scope fixture·BoundedCache 준수. 병렬 agent ≤2.
