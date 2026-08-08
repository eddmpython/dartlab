---
id: operation.testing
title: dartlab 테스트 · CI 운영 규칙
kind: curated
scope: builtin
status: observed
category: operation
purpose: dartlab 테스트 · CI 운영 규칙 운영 규칙을 Skill OS에서 확인하고 변경 전후 검증 게이트로 사용한다.
whenToUse:
  - dartlab 테스트 · CI 운영 규칙
  - testing
  - 1. 핵심 원칙 — 4 개로 간다
  - 2. 3-Tier CI 구조
  - Tier 1 — `ci-fast.yml` (PR + master push, 목표 ≤ 3 분)
  - Tier 2 — `ci-full.yml` (master push only, 목표 ≤ 10 분)
  - Tier 3 — `ci-nightly.yml` (cron 15:00 UTC = KST 00:00, 목표 ≤ 45 분)
inputs:
  - 작업 목적
  - 대상 엔진 또는 실행 환경
  - 검증 범위
outputs:
  - selected skill
  - capability/docstring handoff
  - verification gate
capabilityRefs: []
toolRefs:
  - search_reference
knowledgeRefs:
  - start.dartlabSkillOs
  - operation.architecture
  - operation.docstringStandard
  - operation.performanceProfile
sourceRefs:
  - dartlab://skills/operation.testing
procedure:
  - 1. 핵심 원칙 — 4 개로 간다 기준을 확인한다.
  - 2. 3-Tier CI 구조 기준을 확인한다.
  - Tier 1 — `ci-fast.yml` (PR + master push, 목표 ≤ 3 분) 기준을 확인한다.
  - Tier 2 — `ci-full.yml` (master push only, 목표 ≤ 10 분) 기준을 확인한다.
  - Tier 3 — `ci-nightly.yml` (cron 15:00 UTC = KST 00:00, 목표 ≤ 45 분) 기준을 확인한다.
  - '**module scope 권장** — 파일 단위 로드·해제.'
  - '**session scope 지양** — Company 여러 개 로드 누적 시 OOM.'
  - '**function scope** — 필요하면 사용, `gc.collect()` 권장.'
  - root `dartlab` logger 에 stderr `StreamHandler` 자동 부착 (최초 1 회).
requiredEvidence:
  - skillRef
  - executionRef
  - sourceRef
expectedOutputs:
  - 작업 경로
  - 확인한 근거
  - 검증 결과
runtimeCompatibility:
  server:
    status: supported
  localPython:
    status: supported
  mcp:
    status: supported
  webAi:
    status: supported
  pyodide:
    status: supported
    notes: []
failureModes:
  - Skill OS 검색 없이 과거 문서 경로를 직접 찾음
  - API schema를 skill 본문에 중복해 docstring/capability와 어긋남
  - 검증 게이트 없이 변경 또는 답변을 완료 처리함
forbidden:
  - 삭제된 운영 문서 경로를 공식 진입점으로 안내하지 않는다.
  - 공개 호출 방식, 대표 반환 형태, 오류/제한 동작을 skill과 불일치한 채 방치하지 않는다.
examples:
  - dartlab 테스트 · CI 운영 규칙 규칙 확인
  - testing 작업을 Skill OS에서 시작
source:
  type: absorbed_skills
  absorbedKey: testing
  format: markdown
lastUpdated: '2026-08-09'
testUniverse:
  market: KR
  stockCodes:
    - "005930"
---

## Skill OS 흡수 규칙

- 이 skill이 공식 진입점이다. 삭제된 운영 문서 경로를 다시 안내하지 않는다.
- 공개 호출 방식과 대표 반환 형태는 skill에서 확인하고, 세부 필드는 capability/docstring으로 검산한다.
- 분석이나 변경 결과는 ref, 실행 로그, 테스트 결과로 검증한다.

## 실행 순서

- 1. 핵심 원칙 — 4 개로 간다 기준을 확인한다.
- 2. 3-Tier CI 구조 기준을 확인한다.
- Tier 1 — `ci-fast.yml` (PR + master push, 목표 ≤ 3 분) 기준을 확인한다.
- Tier 2 — `ci-full.yml` (master push only, 목표 ≤ 10 분) 기준을 확인한다.
- Tier 3 — `ci-nightly.yml` (cron 15:00 UTC = KST 00:00, 목표 ≤ 45 분) 기준을 확인한다.
- **module scope 권장** — 파일 단위 로드·해제.
- **session scope 지양** — Company 여러 개 로드 누적 시 OOM.
- **function scope** — 필요하면 사용, `gc.collect()` 권장.
- root `dartlab` logger 에 stderr `StreamHandler` 자동 부착 (최초 1 회).

## L0~L1.5 완료 게이트

core/gather/providers(dart,edgar)/scan/frame/synth/reference 경계 변경은 Guard strict 명령을
통과해야 완료다. `edinet` 은 API 통신 불가 deferred provider 로 provider strict scope 에서 제외한다.

```bash
python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar
```

Guard strict 는 cycle scan, architecture pytest, provider mirror, gather gate, provider gate, public API smoke 를 순서대로 실행하고 `externalGates[]` 에 원 명령과 결과를 남긴다. CI Fast 의 `architecture-l0-l15` job 은 이 gate 를 warning 이 아니라 failure 로 다룬다.

## Guard Index 회귀 방지 체계

pytest 는 회귀를 실패시키는 표면이고, 전수조사는 AST/import graph/baseline scanner 가 맡는다. 전체 `pytest tests/ -v` 실행은 메모리·시간 비용이 커서 품질 증명의 기본값으로 쓰지 않는다.

공식 gate 는 3 단계다.

- `quick` — 변경 파일과 reverse dependency 영향 테스트만 실행한다. 목표 5~15 초. 개발 중 기본 확인.
- `strict-l0-l15` — L0~L1.5 architecture/provider/gather/public API gate. PR 필수 fail gate.
- `full-census` — 전체 repo 전수조사. nightly/release 전 확인.

Guard Index 공식 interface:

```bash
python -X utf8 tests/audit/dartlabGuard.py quick
python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar
python -X utf8 tests/audit/dartlabGuard.py full --baseline tests/audit/_baselines/dartlabGuard.json
python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar --json
```

기존 audit script 는 제거하지 않는다. Guard Index 는 기존 script 를 rule source 로 사용하고, AST index 와 baseline ledger 결과를 같은 실행 표면으로 묶는다. `full-census` 는 nightly/release 용 전수조사이며 `tests/audit/_baselines/dartlabGuard.json` 을 대표 원장으로 사용한다.

## audit / lint 스크립트 인벤토리

`tests/audit/` 의 모든 audit·lint 스크립트는 본 spec 또는 명시한 다른 SSOT 에 등록되어야 한다 (운영자↔AI feedback rule `feedback_no_orphan_scripts`). 표 외 신규 스크립트는 PR 차단. **`scripts/` 폴더 절대 금지** — 새 도구는 무조건 도메인 폴더 (`tests/audit/`, `src/dartlab/{engine}/`, `.github/scripts/`, `notebooks/_scripts/`, `landing/_scripts/`, `blog/_scripts/`, `.claude/`) 안에 둔다.

### Guard Index 가 subprocess 로 호출하는 게이트 (PR 필수)

`tests/audit/dartlabGuard.py` 의 `strict --scope l0-l15` 와 `full` 명령이 직접 실행한다. 단독 호출도 가능.

| 스크립트 | 룰 | 실행 트리거 |
|---|---|---|
| `tests/audit/cycleScan.py` | 모듈 import 양방향 사이클 검출 (단방향 허용). `--strict-toplevel` 옵션 | Guard `strict` 의 1 번째 게이트 |
| `tests/audit/folderMirror.py` | `providers/` 폴더 mirror 검증 (P-트랙 룰 2). `--providers dart,edgar --strict` | Guard `strict` 의 2 번째 |
| `tests/audit/gatherGate.py` | gather/ 도메인 8 룰 통합 audit (G+ 격상 후 G-트랙) | Guard `strict`/`full` |
| `tests/audit/providerGate.py` | P-트랙 11 룰 통합 gate (한 번에 11 audit). `--providers dart,edgar` | Guard `strict`/`full` |

### Provider P-트랙 룰별 단독 lint (providerGate 가 묶음 호출)

| 스크립트 | 룰 |
|---|---|
| `tests/audit/folderSize.py` | P-트랙 룰 3 — 폴더 vs 단일 `.py` 임계 검증 |
| `tests/audit/initThin.py` | P-트랙 룰 4 — `__init__.py` thin 검증 |
| `tests/audit/underscoreModules.py` | P-트랙 룰 5 — `_*.py` 파일명 검증 |
| `tests/audit/limitDefault.py` | P-트랙 룰 8 — provider collection-반환 메서드 `limit` keyword 기본값 검증 |
| `tests/audit/providerSymmetry.py` | P-PR 트랙 — provider method-level symmetry 측정 게이트 |
| `tests/audit/behaviorCoverage.py` | P-PR 트랙 — 행동 테스트 커버리지 (providers/ 공개 method ↔ tests/providers/ 매핑). `--mode baseline\|strict` |

### docstring 게이트

| 스크립트 | 룰 |
|---|---|
| `tests/audit/docstring4Section.py` | P-트랙 룰 6 — 4 섹션 (Args/Returns/Raises/Example) 최소 게이트. PR 차단 |
| `tests/audit/docstring9Section.py` | G+ 트랙 룰 6b — 9 섹션 rich docstring 측정 (warn-only) |
| `tests/audit/docstringNineSection.py` | P-PR 트랙 — providers 한정 9 섹션 측정 게이트 |
| `tests/audit/docstring_coverage.py` | W-C 트랙 — 9 섹션 충족률 측정 |

상세 9섹션 표준은 [operation.docstringStandard](/skills/operation.docstringStandard)를 따른다.

### 코드 품질·구조 게이트

| 스크립트 | 룰 |
|---|---|
| `tests/audit/qualityGate.py` | radon 복잡도 + vulture 죽은 코드 자동 검사 |
| `tests/audit/coreBoundary.py` | core 경계 lint. `src/dartlab/core/`의 거주 자격은 `operation.architecture`를 따른다. |
| `tests/audit/overSplitInventory.py` | 과분할 폴더 인벤토리 (operation.code 룰 1) |
| `tests/audit/staleImports.py` | stale top-level import lint — `from dartlab import X` / `import dartlab as Y` 잔존 검출 |
| `tests/audit/stale_references.py` | 폐기된 API/이름이 코드에 잔존하는지 검증 |
| `tests/audit/namingConsistency.py` | 매개변수 의미 일관성 lint — `core/naming/aliases.json` 표준 사전 검사 |
| `tests/audit/snakeCaseInventory.py` | camelCase 100% 인벤토리 — snake_case 식별자 카운트 |
| `tests/audit/structureMap.py` | dartlab 전체 구조 맵 자동 생성 (refactor 보조) |
| `tests/audit/testCoverageGate.py` | Track 6 — `src/` 새 함수 vs `tests/` 참조 매핑 강제 |
| `tests/audit/lint_camelcase_ast.py` | camelCase + docstring AST lint, diff 기준 (legacy 비차단) |
| `tests/audit/lint_layer_designation.py` | 계층 명명 lint — alias 금지 강행 |
| `tests/audit/checkSilentFail.py` | Silent-fail 패턴 lint (2026-04-19 사고 회귀 차단) |

### Smoke · timing · 데이터 품질

| 스크립트 | 룰 |
|---|---|
| `tests/audit/bootstrapTiming.py` | Company 첫 호출 5 초 약속 wall-clock regression. `--threshold 5.0` p95 |
| `tests/audit/mutationSmoke.py` | `dartlab.core` 자작 mutation smoke (Windows 호환, Track 5) |
| `tests/audit/productSmoke.py` | 사용자 공개 API 제품 스모크 |
| `tests/audit/externalVenvSmoke.py` | 외부 venv 설치된 dartlab 8 엔진 smoke (nightly CI + 수동 공용) |
| `tests/audit/dataQualityAudit.py` | 전 엔진 데이터 전수조사 (208 호출 품질) |
| `tests/audit/validateNotebooks.py` | Jupyter 노트북 코드 셀 Python syntax 검증 |
| `tests/audit/publicApiCoverage.py` | 공개 API 시나리오 매핑 감사 |
| `tests/audit/memoryBudgetAudit.py` | `withMemoryBudget` 공개 시나리오 매핑 감사. 메모리 작업 진입은 `CLAUDE.md`와 `operation.performanceProfile`을 따른다. |

> **flaky 처리 SSOT** = `tests/conftest.py` 의 `network` 마커 → `reruns=2` (pytest-rerunfailures). 별도 자동 quarantine 시스템(옛 flakyAudit)은 두지 않는다 — placeholder 였고 데이터소스(`flakyGates.json`) 부재로 작동 0이라 폐기(debt-honesty P2-8). flaky 의심 테스트는 `@pytest.mark.network` 부착으로 rerun 안전망에 든다.

### 진척 측정

| 스크립트 | 역할 |
|---|---|
| `src/dartlab/skills/measureProgress.py` | baseline 부채 · docstring backlog · pytest marker 분포 통합 시계열 |

