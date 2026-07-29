# dartlab `tests/` 운영 방침 (SSOT)

> 본 파일은 `tests/` 디렉토리의 **실용 운영 매뉴얼** 이다. 근본 정책 SSOT 는 `src/dartlab/skills/specs/operation/testing.md` (Skill OS) — 본 파일은 그 운영판 (디렉토리 구조 · 마커 · 도구 사용법 · 6 트랙 운영 절차).
>
> 외부 기여자가 처음 `tests/` 를 열었을 때 **PR 마다 무엇을 추가해야 하는지** 가 5 분 안에 잡혀야 한다.

---

## A. 운영 철학 — 왜 6 트랙인가

dartlab 의 **모든 테스트는 한 가지 질문에 답한다: "다음 PR 이 본 동작을 깨면 자동으로 fail 하는가?"** "통과한다" 가 아니라 "잡는다" 가 기준. 본 질문을 5 층의 표면으로 분해해 각 트랙이 한 표면을 담당한다.

| 표면 | 묻는 질문 | 트랙 |
|---|---|---|
| **사용자 화면** | CLI 출력이 다르게 보이지 않나? | T1 syrupy snapshot |
| **데이터 계약** | raw frame 컬럼이 silent 하게 사라지지 않았나? | T2 Pandera schema |
| **에이전트 출력** | 같은 질문에 같은 품질 답을 내는가? | T3 6 신호 채점 |
| **수치 정확성** | 변환·스케일·부호 반전 후 속성이 보존되나? | T4 metamorphic |
| **테스트 품질 자체** | 코드를 깨면 테스트가 진짜 잡나? | T5 mutation |
| **새 코드 사각지대** | tests 없는 src 함수가 추가되나? | T6 강제 게이트 |
| **외부 IO 응답 변경** | DART/EDGAR API 가 컬럼을 바꿨나? | T7 VCR |

**왜 이 표면만**: ROI ★★★★★ 가능성 × dartlab 도메인 적합도 매트릭스 점수 상위 7. 8 번째 후보 (전체 mutation / formal verification / OSS-Fuzz / Devin) 는 §8 참조 — 검토 후 폐기.

**한 줄 원칙**:
1. **인프라보다 측정** — 도구 도입 ≠ 트랙 도입. mutmut 설치 vs mutation score 100% 는 완전히 다른 단계.
2. **회귀를 잡는 표면만 산다** — "통과율" 보고서가 아닌 "다음 PR 이 깰 수 있는 동작" 의 인벤토리.
3. **부채는 ledger** — baseline 부재 = 영원한 부채. 동결 후 quota 로 줄인다.
4. **CI 가 차단력의 마지막 수단** — 본 PC 통과 ≠ 차단됨. job 등록 + `continue-on-error` 제거 = 차단 활성.

---

## 0. 한눈에 — 새 코드 추가 시 PR 체크리스트

| 신규 코드 유형 | 필수 테스트 추가 위치 | 필수 마커 |
|---|---|---|
| `src/dartlab/core/**` pure 함수 | `tests/core/test_{module}.py` (oracle + property) | `unit` |
| `src/dartlab/gather/**` · `providers/**` raw 생산 | `tests/gather/...` · `tests/providers/.../` + fixture | `integration` 또는 `realData` |
| `src/dartlab/{scan,frame,synth,reference}/**` (L1.5) | `tests/{scan,frame,synth,reference}/` | `unit` 또는 `integration` |
| `src/dartlab/{analysis,credit,quant,macro,industry}/**` (L2) | 해당 엔진 폴더 | `unit` (mock_company) 또는 `integration` |
| `src/dartlab/story/**` (L3) | `tests/story/` | `integration` |
| `src/dartlab/ai/**` (L4) | `tests/ai/` + AI eval set (`tests/_evals/`) 갱신 | `unit` 또는 `eval` |
| `src/dartlab/cli/**` (L4) | `tests/cli/test_output_snapshots.py` snapshot 추가 | `unit` |
| `src/dartlab/mcp/**` (L4) | `tests/mcp/` + Schemathesis (Phase 3) | `unit` |
| Pandera schema 변경 (`gather/dart/schemas.py`) | `tests/gather/dart/test_schemas.py` fixture 통과 | `unit` |
| AI agent 동작 변경 (prompt/tool) | `tests/_evals/eval_set.jsonl` 항목 추가 + judge 통과 | `eval` |

**테스트 없이 src/ 만 바꾼 PR → CI fail** (Track 5 자동 게이트, 2026-Q3 활성화 예정).

---

## 1. 디렉토리 구조 — `src/dartlab/` 14 엔진 4 계층 mirror

```
tests/
├── core/                # L0 — Polars helpers · logger · types · naming · utils · cache
├── gather/              # L1 — DART/EDGAR/EDINET raw 생산
├── providers/           # L1 — provider 패키지 (dart, edgar, edinet)
├── scan/                # L1.5 — 횡단면
├── frame/               # L1.5 — raw 결합 → 분석 ready (현 0, 사각지대)
├── synth/               # L1.5 — 분석 후처리·매칭·시나리오
├── reference/           # L1.5 — 정적 JSON 룩업 + 매핑
├── analysis/            # L2 — 분석
├── credit/              # L2 — 신용
├── quant/               # L2 — quant factor / risk
├── macro/               # L2 — 거시
├── industry/            # L2 — 업종
├── finance/             # L2 — 재무 (analysis 하위 후보)
├── sections/            # L2 — DART docs sections
├── search/              # L2 — 검색
├── story/               # L3 — 조합기
├── ai/                  # L4 — AI agent + workbench + tools (45 파일)
├── cli/                 # L4 — CLI 출력 snapshot + e2e
├── server/              # L4 — HTTP API
├── channel/             # L4 — 메신저 어댑터
├── mcp/                 # L4 — MCP server
├── viz/                 # L4 — 차트 / 시각화
├── architecture/        # 계약 — 4 계층 import 룰 강제 (6 파일, 변경 금지)
├── realData/            # 실데이터 회귀 (HF parquet 필수)
├── benchmarks/          # 성능 (pytest-benchmark)
├── skills/              # Skill OS 검증
├── audit/               # 메타 검증 (AST · docstring · baseline)
├── _schemas/            # Pandera schema 회귀 (private)
├── _drafts/             # ghostwriter 자동 draft (default collection 제외)
├── _evals/              # AI agent eval set + judge (Track 3)
├── _fixtures/           # fixture 선언 분리
├── _helpers.py          # captureRichOutput · 공용 헬퍼
├── fixtures/            # 실 production parquet snapshot
└── conftest.py          # MockCompany · samsung/aapl module fixture · 메모리 가드
```

**경계 판정 룰**:
- 단일 엔진/모듈 검증 → 해당 엔진 폴더
- 2+ 엔진 cross-cutting → 최상단 또는 `tests/integration/` (별도 폴더 생성 시 본 SSOT 갱신)
- 메타 검증 (audit/ast/docstring) → `tests/audit/`
- 회귀 baseline 시나리오 → `tests/realData/`
- private (운영자 internal) → `tests/_{name}/` (언더스코어 prefix)

`__init__.py` 는 basename 충돌 방지용 (같은 이름 `test_engine.py` 가 여러 폴더에 존재 → pytest rootdir 해석 충돌). 신규 폴더 생성 시 **빈 `__init__.py` 필수**.

---

## 2. 마커 시스템 (pyproject `[tool.pytest.ini_options].markers`)

| 마커 | 의미 | CI 실행 시점 |
|---|---|---|
| `unit` | 순수 로직 / mock 만, 데이터 0, 병렬 안전 | Tier 1 (Fast, PR) |
| `integration` | Company 1 개 로드, 중간 무게 | Tier 2 (Full) |
| `heavy` | 대량 데이터, 단독 실행 필수 | Tier 3 (Nightly) |
| `requires_data` | 로컬 parquet 필수 (CI 에서 skip) | 자동 부착 |
| `realData` | 엔진별 실데이터 smoke (HF parquet + 실 파이프라인) | Tier 3 + 운영자 트리거 |
| `freshInstall` | 빈 캐시 → 자동 다운로드 검증 | Nightly |
| `network` | 외부 HTTP (HF/DART/EDGAR/FRED) | `realData` 자동 부착 |
| `slow` | ≥ 30 초 — PR fast path 제외 | Tier 2/3 |
| `flaky` | transient 실패 자동 재시도 (rerunfailures) | network 자동 |
| `draft` | ghostwriter 자동 생성 (review 전) | 명시 호출만 |
| `eval` | AI agent eval (LLM 호출 + judge) | 운영자 트리거 |
| `mutation` | mutmut 실행 대상 표시 (메타) | 주간 |
| `metamorphic` | 변환 후 속성 보존 검증 (quant/credit) | Tier 2 |
| `vcr` | record-replay 사용 (네트워크 mock) | Tier 1 |

**자동 부착 룰** (`tests/conftest.py::pytest_collection_modifyitems`):
- `skipif reason in 데이터 관련` → `requires_data`
- `realData` 마커 → `network` 자동
- `network` 마커 → `flaky(reruns=2)` 자동

---

## 3. 실행 — `tests/run.py` 단일 진입점

⛔ **`pytest tests/ -v` 전체 직접 실행 금지** — Polars 네이티브 메모리 (≈ 200~500MB / Company) 가 누적되면 OOM.

**모든 CI 게이트는 [tests/run.py](run.py) 의 `GATES` dict 가 SSOT**. CI YAML 은 matrix 디스패치만. 로컬도 CI 와 *바이트 단위 동일* 명령으로 실행. 게이트 개수·tier 분포는 [tests/audit/test_runEntrypoint.py](audit/test_runEntrypoint.py) 가 동결 — 현재값은 §4 자동 표 또는 `tests/run.py list`.

```powershell
# Push 전 검증 — ci-fast 의 차단 게이트(fast·blocking) 전체
uv run python -X utf8 tests/run.py preflight

# 단일 게이트 — CI matrix 가 호출하는 것과 동일
uv run python -X utf8 tests/run.py gate format
uv run python -X utf8 tests/run.py gate test-fast
uv run python -X utf8 tests/run.py gate snapshot-regression --dry-run   # 명령만 보기

# Tier 전체
uv run python -X utf8 tests/run.py tier fast --blocking-only

# 정보
uv run python -X utf8 tests/run.py list           # 전체 게이트 표
uv run python -X utf8 tests/run.py audit-self     # dict 무결성
uv run python -X utf8 tests/run.py docs --write   # 본 문서 게이트 표 GATES 와 동기화

# pytest 직접 호출 (단일 파일·폴더 한정 — 본인이 OOM 안전 보장)
$env:DARTLAB_TEST_LOCKED="1"; uv run python -X utf8 -m pytest tests/cli/test_output_snapshots.py -v
```

`tests/run.py` 는 내부적으로 [test-lock.sh](test-lock.sh) 의 직렬화 + `DARTLAB_TEST_LOCKED=1` 와 동일 안전 보장을 한다. 메모리 안전 가드 (`conftest.py::_memory_guard_per_test`) — `PRESSURE_CRITICAL_MB=1500` 초과 시 `pytest.exit(returncode=99)`.

**신규 게이트 추가**: `tests/run.py` 의 `GATES` dict 항목 + `.github/workflows/ci-{fast,full,nightly}.yml` 의 `matrix.include` 항목 양쪽을 한 PR 에서 동시 추가. 한쪽만 추가하면 [tests/audit/test_runEntrypoint.py](audit/test_runEntrypoint.py) 가 fail.

**git push 자동 검증 (선택)**: `bash tests/installHooks.sh` 한 번 실행하면 `core.hooksPath = tests/hooks` 설정. 이후 `git push` 마다 [tests/hooks/pre-push](hooks/pre-push) 가 `tests/run.py preflight` 자동 호출 → fast 차단 게이트 통과 못 하면 push 중단. 일회 우회: `DARTLAB_SKIP_PREPUSH=1 git push`. 비활성화: `git config --unset core.hooksPath`.

---

## 4. 3-Tier CI 구조

| Tier | 파일 | 트리거 | 목표 시간 | 실행 marker |
|---|---|---|---|---|
| **Fast** | `.github/workflows/ci-fast.yml` | PR + master push | ≤ 3 분 | `unit and not requires_data` + smoke + format/lint/architecture + **snapshot + schema** |
| **Full** | `.github/workflows/ci-full.yml` | master push | ≤ 10 분 | `integration` + `metamorphic` + 부분 mutation |
| **Nightly** | `.github/workflows/ci-nightly.yml` | cron 15:00 UTC | ≤ 45 분 | `realData` + `heavy` + AI eval + full mutation |

### 파이프라인 흐름 — 로컬 → Fast → Full → Nightly → Release

```
로컬 preflight (fast·blocking)  ──통과만──▶  git push (master)
                                                │
                                        CI Fast (PR+push, ≤3분)
                                        ├─ fail ─▶ 작성자 수정 후 재push (loop back)
                                        └─ pass ─▶ CI Full (master push, ≤10분)
                                                        ├─ fail ─▶ 작성자 수정
                                                        └─ pass ─▶ Nightly 큐 (cron 15:00 UTC, ≤45분)
                                                                        ├─ fail ─▶ 알람 + 분석 (§15 플레이북)
                                                                        └─ pass ─▶ Release 준비 (release_gate)
```

### 전체 게이트 표 (자동 생성 — 손으로 적지 않음)

`tests/run.py` 의 `GATES` dict 가 SSOT. 아래 블록은 `uv run python -X utf8 tests/run.py docs --write` 가 렌더하며, 어긋나면 [tests/audit/test_runEntrypoint.py](audit/test_runEntrypoint.py)`::test_docsGatesBlockInSync` 가 CI Fast 에서 차단한다 (27↔34 류 드리프트 영구 0).

<!-- gates:auto:start — `tests/run.py docs --write` 가 생성. 손으로 편집 금지 -->
**합계 30 게이트 — fast 17 · full 6 · nightly 7. push 전 `preflight` 차단 게이트(fast·blocking) 14.**

| 게이트 | tier | 차단 | matrix | timeout |
|---|---|---|---|---|
| `format` | fast | ✅ | - | 20m |
| `lint` | fast | ✅ | - | 20m |
| `architecture-l0-l15` | fast | ✅ | - | 20m |
| `typecheck` | fast | — | - | 20m |
| `smoke` | fast | ✅ | - | 20m |
| `test-fast` | fast | ✅ | - | 30m |
| `wheel-smoke` | fast | ✅ | - | 20m |
| `quality-gate` | fast | ✅ | - | 20m |
| `security` | fast | — | - | 20m |
| `deps-check` | fast | — | - | 20m |
| `notebooks` | fast | ✅ | - | 20m |
| `snapshot-regression` | fast | ✅ | - | 5m |
| `schema-drift` | fast | ✅ | - | 5m |
| `eval-rule` | fast | ✅ | - | 5m |
| `eval-full` | nightly | — | - | 30m |
| `mutation-smoke` | fast | ✅ | - | 5m |
| `test-coverage-gate` | fast | ✅ | - | 5m |
| `test-full` | full | ✅ | python | 60m |
| `fixture-integration` | full | ✅ | - | 15m |
| `cross-os-smoke` | full | ✅ | os | 20m |
| `product-smoke-wheel` | full | ✅ | - | 30m |
| `realdata-plan` | full | ✅ | - | 20m |
| `realdata-suite` | full | ✅ | test | 30m |
| `guard-full-census` | nightly | ✅ | - | 15m |
| `realdata-suite-full` | nightly | ✅ | test | 30m |
| `external-venv-smoke` | nightly | ✅ | - | 45m |
| `freshInstall` | nightly | ✅ | - | 30m |
| `mutation-testing` | nightly | — | - | 90m |
| `dart-panel-only` | fast | ✅ | - | 5m |
| `benchmark-weekly` | nightly | — | - | 30m |
<!-- gates:auto:end -->

**차단(✅) = PR 머지 fail gate, `차단=—` = blocking=False (리포트만, push 가능)**. baseline 회귀 (Guard Index `strict --scope l0-l15`) 는 본 표와 별개로 차단.

---

## 5. 6 트랙 운영 방침 — 훌륭 수준까지

> 이번에 도입된 syrupy snapshot + Pandera schema + ghostwriter draft 는 **시작점** 일 뿐. 잘하는 라이브러리 (ruff/polars/pydantic/FastAPI/ripgrep) 수준에 도달하려면 아래 6 트랙 모두 운영해야 한다.

### Track 1 — Snapshot 회귀 (syrupy) — ★★★★★ **도입 완료**

| 항목 | 위치 |
|---|---|
| 헬퍼 | `tests/_helpers.py::captureRichOutput()` |
| 케이스 | `tests/cli/test_output_snapshots.py` (5 case) |
| 동결 | `tests/cli/__snapshots__/test_output_snapshots.ambr` |

**언제 추가**:
- 새 CLI 명령
- Rich Progress / Live / Table 출력 변경
- HF 다운로드 마커 변경
- warning routing 변경 (RichHandler 흡수)

**갱신**:
```powershell
$env:DARTLAB_TEST_LOCKED="1"; uv run python -X utf8 -m pytest tests/cli/test_output_snapshots.py --snapshot-update
```
사람 눈으로 diff 확인 후 commit. 무조건 `--snapshot-update` 금지 — 회귀를 의도된 변경으로 위장하는 거짓 동결.

### Track 2 — Schema 계약 (Pandera) — ★★★★★ **도입 완료**

| 항목 | 위치 |
|---|---|
| 스키마 | `src/dartlab/gather/dart/schemas.py` (FinanceSchema · ReportSchema) |
| 회귀 | `tests/gather/dart/test_schemas.py` (fixture 10 종 + report + drift reject) |
| Production 게이트 | `DARTLAB_VALIDATE_SCHEMA=1` 환경변수 (production default OFF) |

**언제 추가**:
- DART/EDGAR API 가 응답 컬럼 변경
- finance/report/docs frame 의 필수 컬럼 추가/삭제
- 새 raw 생산 endpoint

**Production 부작용 정책**: `_maybeValidateFinance()` 는 `DARTLAB_VALIDATE_SCHEMA=1` 일 때만 동작. 실패 시 raise 대신 `logger.warning` 으로 drift 기록 → 사용자 호출 깨뜨리지 않음. CI nightly 에서 `=1` 설정해 정기 검사.

### Track 3 — AI Agent eval — ★★★★★ **도입 예정 (2026-Q2)**

dartlab 정체성 = 자가개선 루프 → LLM 출력 회귀 못 잡으면 다른 모든 테스트가 무의미.

| 항목 | 위치 |
|---|---|
| Eval set | `tests/_evals/eval_set.jsonl` (질문 + 기대 평가 항목 30-50) |
| Judge | `tests/_evals/judge.py` (LLM-as-judge, 6 신호 채점) |
| 실행 | `pytest tests/_evals/ -m eval` (외부 LLM 호출, $0.01~0.05 / case) |

**6 채점 신호**: factual_correctness · evidence_citation · tool_use_appropriate · format_compliance · reasoning_depth · no_hallucination.

**언제 실행**: AI agent 코드 변경 PR + nightly. 점수 < baseline 시 fail.

**도구 선택**: `inspect-ai` (Anthropic 권장) 또는 자체 경량 구현. dartlab 같은 도메인 깊은 라이브러리는 자체 구현이 적합 (외부 의존 추가 회피).

### Track 4 — Property-based 50%+ (ghostwriter sweep) — ★★★★ **시범 → sweep 예정**

| 단계 | 위치 |
|---|---|
| 1 (현) | `tests/_drafts/test_formatting_draft.py` — 시범 3 함수 |
| 2 (sweep) | `core/{naming,formatting,utils}`, `synth/*`, `reference/*` pure 함수 전체 |
| 3 (oracle 보강) | draft → `tests/core/test_{module}.py` 정식 위치 이동 + oracle assertion |

**Draft → Oracle 사다리**:
```powershell
# 1) ghostwriter 생성
uv run python -X utf8 -m hypothesis write dartlab.core.naming > tests/_drafts/test_naming_draft.py

# 2) 사람이 oracle 보강 — 예: parsePeriod("2024Q4") == ("2024", "Q4")
# 3) 검증된 케이스만 tests/core/test_naming.py 로 이동
# 4) draft 삭제
```

**ROI 표적**: `typing.Any` 시그니처는 약함 (raise 안 함만 검증). 구체 타입 (`int`, `str`, `Decimal`) 인자가 ROI 높음.

### Track 5 — Mutation testing — ★★★★★ **도입 완료 (mutation score 100%)**

"테스트가 통과한다" 가 아니라 "테스트가 깨진 코드를 잡는다" 를 측정.

| 항목 | 위치 |
|---|---|
| **PR 차단 게이트** | `tests/audit/mutationSmoke.py` (Windows + Linux 자작 7 패턴) |
| Self-test | `tests/audit/test_mutationSmoke.py` (7 종 — pattern 존재 · score 계산) |
| CI Fast job | `.github/workflows/ci-fast.yml` `mutation-smoke` (~35 초, 100% killed 강제) |
| Nightly 확장 sweep | `mutmut` Linux runner — `.github/workflows/ci-nightly.yml` `mutation-testing` job |
| 자작 mutmut 설정 | `pyproject.toml [tool.mutmut]` (대상 = `src/dartlab/core/{formatting, cache, naming}`) |
| Oracle 테스트 표면 | `tests/core/test_formatting.py` (60 종) + `tests/core/test_ratios_metamorphic.py` (19 종) |
| 결과 artifact | CI nightly `mutation-results` (mutation-results.txt) — 30 일 보관 |
| 본 PR baseline | **7/7 killed (100% mutation score)** |

**Windows 호환** — `mutationSmoke.py` 가 직접 AST 텍스트 replace 후 `sys.executable` 로 pytest 호출. mutmut Linux 의존 회피.

**현재 잡는 7 패턴** (회귀 빈도 높은 변형):
1. `formatKr` 조 임계 off-by-one (`>=` → `>`)
2. `formatKr` 억 임계 off-by-one
3. `formatKr` 만 임계 off-by-one
4. `formatComma` int collapse 조건 부정
5. `yoyPct` 양수 분기 부호 변형 (`-` → `+`)
6. `yoyPct` 부호 분기 `>=` → `>` (cur=0 케이스 누락)
7. `yoyPct` None 가드 `==` → `!=`

**확장 정책**: 새 `core/*.py` pure 함수 추가 시 mutationSmoke.py 의 `_MUTATIONS` 에 패턴 추가. 부분 적용 (Polars/numpy native 호출 비중 큰 `analysis/`, `quant/` 는 mutant 무의미).

**survived 발견 시**: oracle test 보강 → 패턴 재실행 → 100% 회복. 절대 mutation 자체 제거 금지.

### Track 6 — Test 강제 게이트 (CI fail when src/ adds without tests/) — ★★★★ **도입 완료 (warning-only)**

| 항목 | 위치 |
|---|---|
| 게이트 스크립트 | `tests/audit/testCoverageGate.py` |
| Baseline 동결 | `tests/audit/_baselines/testCoverage.json` — **1097 / 3134 (35%) 부채** |
| CI 호출 | `.github/workflows/ci-fast.yml` job `test-coverage-gate` (`continue-on-error: true`) |
| Self-test | `tests/audit/test_testCoverageGate.py` — 12 종 |
| 룰 | PR diff 에서 `src/dartlab/**/*.py` 의 새 공개 함수 (def, non-private) 추가 → `tests/**/test_*.py` 에 해당 함수명 등장해야 함 (substring 휴리스틱) |
| 예외 | `_private`, abstract method (ellipsis 본문), `@abstractmethod`, `@overload`, `__init__.py`, `cli/main.py` 진입점, `server/api/`, `providers/*/openapi/`, `viz/charts/`, `mcp/` |

**Baseline 정책**: 본 PR 시점 1097 누락은 부채 ledger 로 동결 (`_baselines/testCoverage.json`). 향후 PR 은 *신규 누락만 fail 대상*.

**부드러운 도입 단계**:
1. **Phase 1 (현재, 2026-Q2)** — `continue-on-error: true` warning-only. PR diff 보고만, 머지 차단 X.
2. **Phase 2 (2026-Q3)** — `--fail-on-missing` 추가, `continue-on-error` 제거. 신규 누락 PR 머지 차단.
3. **Phase 3 (2026-Q4)** — baseline 부채 quota 감소 (분기당 10% 씩 감축) 추가 트랙.

**갱신 절차**:
```powershell
# baseline 재측정 (분기별 quota 측정)
uv run python -X utf8 tests/audit/testCoverageGate.py --all --json | Out-File -Encoding utf8 tests/audit/_baselines/testCoverage.json

# diff 검토 후 commit
git diff tests/audit/_baselines/testCoverage.json
```

### Track 7 — Record-Replay (VCR) — ★★★ **인프라 도입 완료 (카세트 record 운영자 트리거)**

| 항목 | 위치 |
|---|---|
| 카세트 | `tests/_cassettes/` (gitignored 가 아닌 commit — production HTTP 응답 동결) |
| 대상 | `providers/dart/openapi/dart.py` · `providers/edgar/openapi/sec.py` 외부 호출 |
| 도구 | `vcrpy` 또는 자체 경량 (HTTPS body hash → parquet) |
| 마커 | `vcr` |

**언제 record**: 외부 API 응답 변경 시 한 번. 이후 CI 는 카세트만 replay → 네트워크 없이 회귀 검증.

### Track 8 — Metamorphic test — ★★ **도입 예정 (2026-Q4)**

수치 분석에서 결정적 oracle 없을 때 **변환 후 보존되는 속성** 으로 검증.

| 대상 | 변환 | 보존 속성 |
|---|---|---|
| `quant/factor/calcRanking` | 입력 +1 (전체 shift) | ranking 동일 |
| `credit/scoring/calcGrade` | 통화 환산 | 등급 동일 |
| `analysis/ratios/calcDebtRatio` | 단위 변환 (원 → 백만원) | 비율 동일 |
| `macro/scenarios/applyShock` | 0 충격 | 결과 = 기준선 |

**위치**: `tests/{quant,credit,analysis,macro}/test_*_metamorphic.py`. 마커 `metamorphic`.

---

## 6. 디렉토리 신설 시 절차

1. **빈 폴더 + `__init__.py`** 만들기 (basename 충돌 방지)
2. **본 SSOT 의 1 절 트리 그림 갱신** + 6 절 (있다면) 갱신
3. **`testing.md` Skill OS 갱신** 은 운영자 트리거 시에만 (개별 PR 자동 갱신 금지 — Skill OS 는 운영자 수동 SSOT)
4. **첫 테스트 1 개 추가** — 빈 폴더 commit 금지 (`__init__.py` 만 있는 폴더는 의미 없음)

---

## 7. 사각지대 (의식적 부채 + 향후 트랙)

| 영역 | 현재 | 부채 이유 | 해결 트리거 |
|---|---|---|---|
| `tests/frame/` | 0 테스트 | L1.5 frame 엔진이 분석 ready 결합기 — 회귀 가드 자동 우선순위 낮음 | 운영자 트리거 |
| 노트북 실행 | 0 | `notebooks/` 가 marketing/demo 중심 | nbmake 또는 papermill 도입 시 |
| MCP server contract | 0 | MCP 자체가 0.x 단계 | Schemathesis 도입 (Phase 3) |
| Pyodide wasm 빌드 | 0 | dartlab-pyodide 별도 repo | wasm 호환성 회귀 발견 시 |
| 전체 flow demo | 0 | 마케팅 자산 영역 | VHS .tape 도입 (출시 직전) |
| 외부 입력 fuzz | 0 | parser 한정 보안 영역 | Atheris (보안 단계) |
| OpenTelemetry replay | 0 | 서버 운영 시점 | 서버 운영 단계 |

---

## 8. 적용 *안* 함 (ROI 검토 결과 폐기)

- **Formal verification** (TLA+, deal) — Python 라이브러리에 비싸기만. Pandera + Hypothesis 가 80% 보장을 1/100 비용에.
- **전체 repo mutation** — Polars/Rust native 호출 비중 → mutant 가 의미 없음. `core/` 한정만.
- **Devin 류 autonomous test agent** — SWE-EVO 2026: long-horizon multi-commit 평가에서 실패. 도메인 깊은 라이브러리에 부적합.
- **Diffblue Cover** — Java 전용.
- **Great Expectations** — SQL+Spark audit 용. Pandera 가 dartlab 에 적합.

---

## 9. 도구 버전 (`pyproject.toml [dependency-groups].dev`)

| 도구 | 버전 | 역할 |
|---|---|---|
| pytest | ≥ 9.0.2 | base runner |
| pytest-asyncio | ≥ 0.24.0 | async test |
| pytest-benchmark | ≥ 5.0.0 | 성능 회귀 (`tests/benchmarks/`) |
| pytest-cov | ≥ 6.0.0 | coverage (`fail_under=40`, omit policy) |
| hypothesis | ≥ 6.100.0 | property-based + ghostwriter |
| syrupy | ≥ 4.7.0 | CLI 출력 snapshot |
| pandera[polars] | ≥ 0.29.0, < 0.32 | DataFrame schema 계약 (0.32.0 isin 빌트인 회귀로 상한) |
| mutmut | (도입 예정 2026-Q3) | mutation testing |
| vcrpy | (도입 예정 2026-Q3) | record-replay |
| inspect-ai | (도입 예정 2026-Q2) | AI eval framework |

---

## 10. 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `pytest.exit(returncode=99) 메모리 안전 종료` | Company 누적 → 1500MB 초과 | 마커별 분리 실행 또는 `PYTEST_MEMORY_LIMIT_MB=2000` |
| `PytestUnknownMarkWarning: draft` | `tests/_drafts/` 가 norecursedirs 우회 | `pyproject.toml [tool.pytest.ini_options].markers` 에 등록 확인 |
| `same basename test_engine.py duplicate` | `__init__.py` 누락 | 신규 폴더에 빈 `__init__.py` 추가 |
| syrupy `snapshot does not exist` | 첫 실행 | `--snapshot-update` 1 회 + 사람 눈 diff 검토 |
| Pandera `SchemaErrors` in production | `DARTLAB_VALIDATE_SCHEMA=1` 켜진 상태 | 끄거나 warning 로그 확인 후 schema 갱신 |
| ghostwriter `Resolved typing.Any to st.nothing()` | 시그니처 weak | `typing.Any` 대신 구체 타입으로 시그니처 좁히거나 oracle test 로 이동 |

---

## 12. 회귀 사이클 — 발견 → 보강 → 측정 → 차단

본 PR 의 mutationSmoke 첫 실행이 *살아있는 사례*:

```
1. mutationSmoke 실행 (첫 측정)
   ↓
2. 7 mutation 중 3 survived 발견 (score 57%)
   ↓
3. survived 분석 — formatKr withWon 분기 + yoyPct cur=0 oracle 누락
   ↓
4. tests/core/test_formatting.py + test_ratios_metamorphic.py 에 oracle 6 추가
   ↓
5. mutationSmoke 재실행 → 7/7 killed (100%)
   ↓
6. CI Fast mutation-smoke job 등록 → 다음 PR 이 본 oracle 깨면 즉시 fail
```

**모든 트랙이 같은 사이클**:

| 트랙 | 발견 | 보강 | 차단 |
|---|---|---|---|
| T1 snapshot | `--snapshot-update` 후 diff 검토 | snapshot 동결 | CI `snapshot-regression` job |
| T2 schema | 새 fixture parquet 추가 | `gather/dart/schemas.py` 컬럼 갱신 | CI `schema-drift` job |
| T3 eval | live 호출 점수 baseline 미달 | prompt/tool 수정 | nightly + baseline_score 갱신 |
| T4 metamorphic | 새 수치 함수 추가 | 변환 속성 검증 추가 | CI `test-fast` (unit 마커) |
| T5 mutation | mutationSmoke survived | oracle test 추가 | CI `mutation-smoke` job |
| T6 게이트 | new_missing > 0 | tests/ 에 함수 참조 추가 | CI `test-coverage-gate` job |
| T7 VCR | DART API 응답 변경 → replay fail | 카세트 re-record | CI replay (네트워크 0) |

**금지** — 사이클 단축:
- mutation survived 발견 시 mutation 자체 제거 (X) — oracle 보강 (O)
- snapshot diff 무조건 `--snapshot-update` (X) — 사람 눈 diff 검토 후 동결 (O)
- VCR replay fail 시 `record_mode='all'` 로 재record (X) — 응답 변경 분석 후 의도 확인 (O)
- 게이트 new_missing fail 시 함수에 `_` prefix 붙여 회피 (X) — tests/ 에 참조 추가 (O)

---

## 13. 부채 관리 + 분기 quota

baseline 동결은 *부채 ledger* 다. 부채 자체는 잡지 못한 회귀이지만, 신규 부채만 fail 시키면 *부채가 영구화* 된다. 분기 quota 로 줄여나간다.

**부채 인벤토리** (2026-05 시점):

| 트랙 | baseline | 비고 |
|---|---|---|
| T6 강제 게이트 | 1097 (35% 함수 무참조) | `_baselines/testCoverage.json` |
| 9-section docstring | gather 183 · providers ~30 | `_baselines/gatherDocstring9Section.json` 등 |
| import cycle | warn-only (P3 까지) | `cycleScan.py` |
| docstring 4 section | scope 별 baseline | `_baselines/{scope}Docstring4Section.json` |

**감축 quota**:

| 분기 | T6 quota | docstring quota |
|---|---|---|
| 2026-Q2 | 1097 → 950 (-147, 13%) | 본 PR 시작 |
| 2026-Q3 | 950 → 800 (-150, 16%) | strict 전환 트리거 |
| 2026-Q4 | 800 → 600 (-200, 25%) | cycle scan strict 활성 |
| 2027-Q1 | 600 → 400 | docstring P3 strict |

**측정 도구**:
```powershell
# 분기 측정 (분기 첫 PR)
uv run python -X utf8 src/dartlab/skills/measureProgress.py --record

# baseline 재측정 (감축 commit 직전)
uv run python -X utf8 tests/audit/testCoverageGate.py --all --json > tests/audit/_baselines/testCoverage.json
```

**감축 commit 형식**: `정리: testCoverage baseline 1097→950 (Q2 quota 달성)`. PR 본문에 *어느 모듈 함수에 어떤 테스트 추가했는지* 표 첨부.

---

## 14. 운영 리듬 — 의식의 시간표

| 빈도 | 의식 | 자동 / 수동 |
|---|---|---|
| **PR 마다** | 5 CI job (snapshot · schema · eval-rule · mutation-smoke · gate) 통과 | 자동 |
| **PR 마다** | §0 체크리스트 — 새 코드에 테스트 추가 | 수동 |
| **매일 nightly** | mutmut Linux 전체 sweep + realdata 20 shard + freshInstall | 자동 (KST 00:00) |
| **주간** | mutationSmoke artifact 검토 — 새 survived 생겼나 | 수동 (월요일 권장) |
| **주간** | eval `live` 1 회 실행 (운영자) — baseline 점수 추이 | 수동 + 비용 ($1~3) |
| **월간** | VCR 카세트 stale 검토 — ≥ 6 개월 카세트 re-record | 수동 |
| **분기** | baseline quota 측정 + 감축 commit | 수동 (분기 첫 PR) |
| **분기** | 적용 안 한 도구 재검토 (§8) — ROI 매트릭스 갱신 | 수동 |
| **신규 트랙 도입 시** | POLICY §5 항목 추가 + §A 매트릭스 갱신 + CI 통합 + self-test | 수동 |

**운영자 알람 채널**: CI 실패 시 GitHub email + Slack #dartlab-ci. nightly artifact 다운로드는 GitHub Actions UI.

---

## 15. 장애 대응 플레이북

| 증상 | 1 차 진단 | 2 차 조치 |
|---|---|---|
| **mutation-smoke job fail (survived 발견)** | `mutationSmoke` 출력 detail 확인 — 어느 패턴 살아남았나 | oracle test 추가 → 재실행 100% 회복 |
| **VCR replay fail (CannotOverwriteExistingCassette)** | DART 응답이 카세트와 다름 → API 변경 가능성 | 분석 후 의도된 변경이면 카세트 re-record + commit |
| **schema-drift fail** | Pandera schema 가 fixture 거부 | DART API 응답 변경 → `gather/dart/schemas.py` 컬럼 갱신 + fixture 재캡처 |
| **snapshot-regression fail** | Rich 출력 diff 발견 | 사람 눈 검토 → 의도된 변경이면 `--snapshot-update` |
| **test-coverage-gate fail (new_missing > 0)** | 새 함수 + tests 누락 | tests/ 에 함수 참조 추가 또는 `_` prefix 의도 확인 |
| **eval-rule fail** | mock 출력이 6 신호 통과 못 함 | 채점 룰 변경 vs 테스트 데이터 정합 — judge.py 확인 |
| **eval-live 점수 하락 (운영자 트리거)** | LLM 모델 변경 / prompt 변경 | baseline_score 일시 하향 → 원인 분석 → 회복 후 baseline 복귀 |
| **baseline 부채 폭증 (1097 → 1500)** | 대규모 src 분할 commit | baseline 재측정 + quota 재조정 |
| **mutmut nightly job fail (Linux 만)** | mutmut 자체 버그 / cache 손상 | `.mutmut-cache` 삭제 후 재실행 (nightly artifact 재트리거) |
| **카세트 stale (6 개월+)** | API 응답 신선도 부족 | `Remove-Item ... ; pytest -v` 으로 re-record + diff 검토 |

**근본 원인 추적 순서**: 1) CI job 로그 / 2) 본 PC 재현 (`test-lock.sh`) / 3) 관련 트랙의 self-test 실행 (mutationSmoke / testCoverageGate 자체 회귀) / 4) git bisect (회귀가 언제 들어왔나).

---

## 11. 관련 SSOT

- 정책 근본 — `src/dartlab/skills/specs/operation/testing.md`
- 강행규칙 — `CLAUDE.md` "메모리 안전" · "변경 단위"
- 도구 SSOT (운영자↔AI 메모리) — `memory/testing_stack.md`
- 4 계층 import — `src/dartlab/skills/specs/operation/architecture.md` · `memory/core_boundary.md`
- 회귀 가드 — `tests/audit/dartlabGuard.py strict --scope l0-l15`
