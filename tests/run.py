"""dartlab CI 단일 진입점 — 로컬·CI 가 동일 명령으로 전체 게이트 실행.

본 파일은 ci-fast + ci-full + ci-nightly 게이트의 SSOT (`GATES` dict).
.github/workflows/ci-*.yml 은 matrix 디스패치만 담당하고, 실제 deps·env·cmd 는
모두 GATES dict 에서 가져온다. dict ↔ matrix drift 는 tests/audit/
test_runEntrypoint.py 가 차단하고, 게이트 개수·tier 분포도 같은 파일이 동결한다.
사람용 문서(POLICY.md·ci-fast-local skill)의 게이트 표는 손으로 적지 않고
`tests/run.py docs --write` 가 GATES 에서 렌더한 `gates:auto` 블록으로 채운다 —
숫자를 베껴 적던 27↔34 류 드리프트를 구조적으로 0 으로 만든다.

# Capabilities
1. `gate <name>` — 단일 게이트 실행 (CI matrix 호출용)
2. `tier <fast|full|nightly>` — 한 tier 의 blocking 게이트 전체
3. `preflight` — tier fast 의 blocking 만 (push 전 검증)
4. `list` — 전체 게이트 표 출력
5. `audit-self` — GATES 무결성 점검 (dup name · 미정의 tier · 모순)
6. `docs [--write]` — 사람용 문서의 게이트 표를 GATES 에서 렌더·동기화 (가드: test_runEntrypoint)

# Args
서브명령마다 다름. `gate` 는 `--dry-run` 으로 명령 문자열만 출력 (실행 안 함).
matrix 인자 (`--python`, `--test`, `--os`) 는 해당 gate 만 사용.

# Example
    uv run python -X utf8 tests/run.py preflight
    uv run python -X utf8 tests/run.py gate format
    uv run python -X utf8 tests/run.py gate test-full --python 3.13
    uv run python -X utf8 tests/run.py gate realdata-suite --test test_ai.py
    uv run python -X utf8 tests/run.py audit-self

# Returns
exit code 0 = 모든 명령 0. blocking=False gate 는 fail 해도 0 유지.

# Guide
- 신규 게이트 추가: GATES dict 에 `Gate(...)` 한 줄 + 해당 tier 의 ci-*.yml
  matrix.gate 에 항목 한 줄. 둘 중 하나만 추가하면 audit-self fail.
- 기존 게이트 명령 변경: 본 파일만 수정. YAML 은 손대지 않음.
- blocking=False 게이트는 fail 해도 PR 차단 안 함 (정보 표시용).
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parent.parent

Tier = Literal["fast", "full", "nightly"]


@dataclass(frozen=True)
class Gate:
    """단일 CI 게이트 정의 — deps + setup + cmd + env 4 종 SSOT.

    matrix-driven 게이트 (test-full / cross-os-smoke / realdata-suite) 의 cmd
    는 `{python}` / `{os}` / `{test_file}` 같은 placeholder 를 가질 수 있고,
    --python / --os / --test 인자로 채워진다.
    """

    name: str
    tier: Tier
    deps: tuple[str, ...] = ()
    install_pkg: Literal["editable", "non-editable", "none"] = "editable"
    setup: tuple[str, ...] = ()
    cmd: str = ""
    env: dict[str, str] = field(default_factory=dict)
    blocking: bool = True
    runner: str = "ubuntu-latest"
    fetch_depth: int = 1
    timeout_minutes: int = 20
    matrix_param: str | None = None  # "python" | "os" | "test" — None 이면 단일 잡


# 헬퍼 dep 묶음 — 반복 줄임.
PYTEST_CORE = ("pytest", "pytest-asyncio", "pytest-cov", "hypothesis")
PYTEST_PARALLEL = (*PYTEST_CORE, "pytest-xdist", "pytest-benchmark")
DEV_SCHEMA_SNAPSHOT = (
    "pandera[polars]>=0.29.0,!=0.32.0,<0.33",
    "vcrpy>=6.0.0",
    "syrupy>=4.7.0",
)  # <0.32: 0.32.0 isin 빌트인 회귀 (pyproject 주석 참조)
MCP_PIN = ("mcp[cli]>=1.0,!=1.27.1,<1.28.2",)

# Realdata 20 shard — ci-nightly.yml realdata-suite-full matrix 와 1:1.
REALDATA_SHARDS = (
    "test_ai.py",
    "test_analysis.py",
    "test_analysisAxes.py",
    "test_companyExhaustive.py",
    "test_companyFacade.py",
    "test_companyTopics.py",
    "test_credit.py",
    "test_creditAxes.py",
    "test_freshInstall.py",
    "test_gather.py",
    "test_gatherAxes.py",
    "test_industry.py",
    "test_macro.py",
    "test_macroAxes.py",
    "test_quant.py",
    "test_story.py",
    "test_scan.py",
    "test_scanAxes.py",
    "test_search.py",
    "test_topLevelApi.py",
)


# ──────────────────────────────────────────────────────────────────────────
# GATES — ci-*.yml matrix.gate 와 1:1. 개수·tier 분포·YAML 일치는 모두
# test_runEntrypoint.py 가 동결한다 (의도 없는 추가/삭제·드리프트 차단).
# ──────────────────────────────────────────────────────────────────────────

GATES: dict[str, Gate] = {
    # ─ Tier 1 — Fast ──────────────────────────────────────────────────────
    "format": Gate(
        name="format",
        tier="fast",
        deps=("ruff==0.11.6",),
        install_pkg="none",
        cmd="ruff format --check src/dartlab/ tests/ --exclude tests/_attempts",
    ),
    "lint": Gate(
        name="lint",
        tier="fast",
        deps=("ruff==0.11.6", "pyyaml", "networkx", "import-linter"),
        install_pkg="editable",
        fetch_depth=2,
        cmd=(
            "ruff check src/dartlab/ tests/ --exclude tests/_attempts && "
            "python -X utf8 tests/audit/noScriptsDir.py && "
            "python -X utf8 blog/_scripts/blogMediaGate.py --ref HEAD && "
            "python -X utf8 tests/audit/workspaceHygiene.py && "
            "python -X utf8 tests/audit/temporaryPlanBoundary.py && "
            "python -X utf8 tests/audit/checkSilentFail.py && "
            # checkSilentFail 은 "파일 부재 시 빈 값" 한 종류만 본다. 라이브러리에서
            # 실제로 지배적인 침묵은 광범위 catch 가 원인을 버리고 대체값을 돌려주는
            # 모양이라 별도로 센다. 통과 조건은 흐름 변경이 아니라 원인 한 줄 기록이다.
            "python -X utf8 tests/audit/silentSubstitute.py && "
            # 계약을 좁히면서 옛 이름을 부르던 소비처를 같이 안 고치면, 넓은 catch 가 그
            # AttributeError 를 지워 사용자 표면이 통째로 죽은 채 초록불이 된다. 2026-07-28
            # 하루에 열두 번 나왔다(보고서 백지 · 차트 다섯 · spec 생성기 일곱 · DCF 도구).
            "python -X utf8 tests/audit/deadCompanyAccessor.py && "
            "python tests/audit/stale_references.py && "
            "python -X utf8 tests/audit/lint_camelcase_ast.py --changed --strict && "
            # baseline 은 2-cycle 목록이다. 예전에는 개수만 적고 늘어나도 WARN 만 찍은
            # 뒤 0 을 돌려줬고, 게이트마저 실패를 삼켜 5 에서 10 으로 느는 동안 아무도
            # 몰랐다. 이제 baseline 밖 신규 cycle 이 생기면 여기서 멈춘다.
            "python -X utf8 tests/audit/cycleScan.py && "
            '(lint-imports || python -c "pass") && '
            # 키가 줄번호를 담던 동안에는 무관한 편집이 유령 위반을 만들어 strict 를
            # 걸 수 없었다. 키를 함수명 기반으로 바꾸고 사전 오류를 바로잡아 신규가
            # 0 이 된 지금은 조언이 아니라 차단으로 세운다.
            "python -X utf8 tests/audit/namingConsistency.py --strict && "
            "python -X utf8 tests/audit/checkEngineSpecSchema.py && "
            "python -X utf8 tests/audit/valuationPublishLint.py --strict && "
            "python -X utf8 tests/audit/dossierVerdictLint.py --strict && "
            "python -X utf8 tests/audit/deprecationAudit.py && "
            "python -X utf8 tests/audit/staleImports.py --check && "
            "python -X utf8 tests/audit/axisDeclaredCoverage.py --check --quiet && "
            "python -X utf8 tests/audit/workbenchPurity.py --check && "
            # 파일 크기 룰 3. 800 줄 초과 단일 파일 회귀를 차단한다. baseline 은 부채
            # 원장이라 baseline 밖 신규 위반만 fail 한다. 예전에는 providers 와 dataHub
            # 두 폴더만 걸려 있어 나머지 엔진이 무방비로 자랐다. 대상을 src/dartlab
            # 전역으로 올리고 baseline 을 그 superset 으로 잡아 기존 보장은 그대로 두면서
            # 어느 엔진에서든 새 위반이 들어오지 못하게 한다.
            "python -X utf8 tests/audit/folderSize.py src/dartlab "
            "--baseline tests/audit/_baselines/libSize.json && "
            # `__init__` 은 재export 파사드여야 하고 로직은 형제 모듈이 소유한다.
            # 대상을 전역으로 올려 어느 엔진에서든 새 위반이 들어오지 못하게 한다.
            "python -X utf8 tests/audit/initThin.py src/dartlab "
            "--baseline tests/audit/_baselines/libInitThin.json && "
            "python -X utf8 tests/audit/untrustedWrapAudit.py --strict && "
            "python -X utf8 tests/audit/checkAgentBoundary.py --strict && "
            # 색상 SSOT 가드 — 브랜드색(#ff3f6f/#fb923c/#ec4899/#ea4647) 토큰 우회 하드코딩 회귀 차단(baseline-ratchet).
            # node 는 CI 러너 기본 제공, 가드는 readdirSync 라 node 버전 무관.
            "node tests/audit/checkColorSsot.mjs"
        ),
    ),
    "architecture-l0-l15": Gate(
        name="architecture-l0-l15",
        tier="fast",
        # cycleScan._findCycles 가 networkx 로 3+ 모듈 cycle 을 잡는다. lint 게이트에만
        # 선언돼 있어 이 게이트와 test-fast 에서 ModuleNotFoundError 로 죽고 있었다.
        deps=(*PYTEST_PARALLEL, "networkx"),
        install_pkg="editable",
        env={"DARTLAB_PROVIDER_SCOPE": "dart,edgar"},
        cmd="python -X utf8 tests/audit/dartlabGuard.py strict --scope l0-l15 --providers dart,edgar",
    ),
    "typecheck": Gate(
        name="typecheck",
        tier="fast",
        deps=("pyright",),
        install_pkg="editable",
        cmd="pyright",
        blocking=False,  # 현 continue-on-error 명시화
    ),
    "smoke": Gate(
        name="smoke",
        tier="fast",
        install_pkg="editable",
        cmd=(
            'python -c "import dartlab; '
            "missing=[n for n in dartlab.__all__ if not hasattr(dartlab,n)]; "
            "import sys; (sys.exit(f'public API missing: {missing}') if missing else None); "
            "from dartlab import Company; assert callable(Company); "
            "print(f'smoke OK — {len(dartlab.__all__)} symbols')\" && "
            "python -X utf8 tests/audit/publicApiCoverage.py && "
            "python -X utf8 tests/audit/memoryBudgetAudit.py && "
            "python -X utf8 tests/audit/productSmoke.py --suite quick --data-mode fixtures "
            "--import-mode source --json-out product-smoke-quick.json"
        ),
    ),
    "test-fast": Gate(
        name="test-fast",
        tier="fast",
        # networkx: tests/architecture/test_cycleScan.py 와 test_no_cycles.py 가
        # cycleScan._findCycles 를 통해 요구한다.
        deps=(*PYTEST_PARALLEL, *DEV_SCHEMA_SNAPSHOT, *MCP_PIN, "networkx"),
        install_pkg="non-editable",
        env={
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "PYTEST_MEMORY_LIMIT_MB": "1900",
            "DARTLAB_TEST_LOCKED": "1",
            # Polars 네이티브 할당자가 놓은 페이지를 바로 OS 로 돌려주게 한다. 이 셋이
            # 없으면 워커가 파일을 이어 돌면서 RSS 가 단조 증가해 1900MB 가드에 걸려
            # 죽는다. 죽는 자리는 그때그때 다른 파일이라 결함처럼 보이지만 원인은 누적이다.
            # tests/test-lock.sh 가 같은 셋을 export 하는데 이 게이트는 그 스크립트를
            # 거치지 않아 못 받고 있었다.
            "MIMALLOC_PURGE_DELAY": "0",
            "MIMALLOC_PURGE_DECOMMITS": "1",
            "MALLOC_CONF": "dirty_decay_ms:0,muzzy_decay_ms:0",
        },
        cmd=(
            # DartLab import는 worker마다 Polars/Rust heap을 소유한다. auto는 운영자
            # Windows에서 16 worker를 띄워 무관한 callable import를 동시 OOM으로
            # 무너뜨렸다. CLAUDE.md 메모리 가드와 같은 상한을 CI 진입점에도 적용한다.
            "pytest tests/ -n 2 --dist loadfile --tb=short "
            "-m 'unit and not requires_data' "
            "--ignore=tests/_attempts "
            "--ignore=tests/test_fixture_analysis_real.py "
            "--ignore=tests/test_fixture_credit_real.py "
            "--ignore=tests/test_fixture_story_real.py "
            "--ignore=tests/realData "
            "--benchmark-disable --no-cov"
        ),
        timeout_minutes=60,
    ),
    "wheel-smoke": Gate(
        name="wheel-smoke",
        tier="fast",
        deps=("uv",),
        install_pkg="none",
        # 갓 구운 것만 남는 빈 폴더에 짓는다. 예전에는 `dist` 에 바로 굽고
        # `ls dist/*.whl | head -n1` 로 골랐다. CI 는 폴더가 비어 있어 문제가 없었지만
        # 로컬에는 옛 wheel 이 남아 있어 사전순 첫 파일, 즉 몇 버전 전 pyodide wheel 을
        # 검사했다. 릴리즈를 막아 서는 게이트가 낡은 산출물을 검사하고 통과시키면
        # 그것은 게이트가 아니다. 실제로 그 낡은 wheel 에는 없는 엔진이 있어 잡혔다.
        setup=(
            "rm -rf dist/wheelSmoke",
            "uv run --with build python -m build --wheel --outdir dist/wheelSmoke",
        ),
        cmd=(
            "WHL=$(ls dist/wheelSmoke/*.whl) && "
            'test "$(echo "$WHL" | wc -l)" -eq 1 && '
            'python -X utf8 .github/scripts/verifyWheel.py "$WHL"'
        ),
    ),
    "quality-gate": Gate(
        name="quality-gate",
        tier="fast",
        deps=("radon", "vulture"),
        install_pkg="none",
        cmd=("python tests/audit/qualityGate.py && python -X utf8 src/dartlab/skills/measureProgress.py"),
        # baseline 이 실재하는 자리를 가리키게 된 뒤 blocking 으로 올린다. 예전에는 금지된
        # `scripts/` 를 baseline 으로 봐서 늘 실패했고, non-blocking 이라 아무도 안 봤다.
        # 이제 복잡도와 죽은 코드는 줄어드는 방향으로만 갱신된다.
        blocking=True,
    ),
    "security": Gate(
        name="security",
        tier="fast",
        deps=("pip-audit",),
        install_pkg="editable",
        # T2-2 — baseline allowlist + blocking 승격 후속. 현재 known CVE 가 0 일 때만 strict 안전.
        # pip-audit --ignore-vuln <ID> 옵션으로 baseline 부채 원장 적용 가능.
        cmd="pip-audit --strict --desc on",
        blocking=False,  # T2-2 — baseline 구축 후 blocking=True 승격
    ),
    "deps-check": Gate(
        name="deps-check",
        tier="fast",
        deps=("deptry",),
        install_pkg="editable",
        cmd="deptry src/dartlab/ --ignore DEP002,DEP003 --extend-exclude _reference",
        blocking=False,
    ),
    "notebooks": Gate(
        name="notebooks",
        tier="fast",
        # notebookContract 는 skill spec frontmatter 를 읽어 pyyaml 이 필요하다. dartlab 자체는
        # 설치하지 않는다(Company 1 개 = 수백 MB. 게이트는 소스를 ast 로만 읽는다).
        deps=("pyyaml",),
        install_pkg="none",
        # validateNotebooks 는 ast.parse(문법)만 본다. notebookContract 는 셀이 부르는 심볼이
        # 공개 계약(engines capabilityRefs + dartlab.__all__) 안인지 본다. 미등재 내부 메서드가
        # 공개 노트북으로 새어 나가던 구멍(2026-07-09 c.audit 사건)을 막는다.
        cmd=("python tests/audit/validateNotebooks.py && python -X utf8 tests/audit/notebookContract.py"),
    ),
    "snapshot-regression": Gate(
        name="snapshot-regression",
        tier="fast",
        deps=(*PYTEST_CORE, "syrupy"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="pytest tests/cli/test_output_snapshots.py -v --tb=short --no-cov",
        timeout_minutes=5,
    ),
    "schema-drift": Gate(
        name="schema-drift",
        tier="fast",
        deps=(*PYTEST_CORE, "pandera[polars]>=0.29.0,!=0.32.0,<0.33"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="pytest tests/gather/dart/test_schemas.py -v --tb=short --no-cov",
        timeout_minutes=5,
    ),
    "eval-rule": Gate(
        name="eval-rule",
        tier="fast",
        deps=("pytest", "pytest-asyncio", "pytest-cov"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="pytest tests/_evals/test_eval_smoke.py -v --tb=short --no-cov",
        timeout_minutes=5,
        blocking=True,
    ),
    # T11-2 — eval full (live judge) 는 nightly 로 분리. smoke 만 fast PR gate.
    "eval-full": Gate(
        name="eval-full",
        tier="nightly",
        deps=("pytest", "pytest-asyncio", "pytest-cov"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="pytest tests/_evals/test_eval_live.py -v --tb=short --no-cov",
        timeout_minutes=30,
        blocking=False,  # nightly — 실패 시 알람만, PR 차단 X
    ),
    "mutation-smoke": Gate(
        name="mutation-smoke",
        tier="fast",
        deps=("pytest", "pytest-asyncio", "hypothesis"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="python -X utf8 tests/audit/mutationSmoke.py",
        timeout_minutes=5,
    ),
    "test-coverage-gate": Gate(
        name="test-coverage-gate",
        tier="fast",
        install_pkg="none",
        fetch_depth=0,
        cmd=("python -X utf8 tests/audit/testCoverageGate.py --diff origin/master --fail-on-missing --limit 30"),
        timeout_minutes=5,
    ),
    # ─ Tier 2 — Full ──────────────────────────────────────────────────────
    "test-full": Gate(
        name="test-full",
        tier="full",
        matrix_param="python",
        # networkx: tests/architecture/test_cycleScan.py 와 test_no_cycles.py 가
        # cycleScan._findCycles 를 통해 요구한다.
        deps=(*PYTEST_PARALLEL, *DEV_SCHEMA_SNAPSHOT, *MCP_PIN, "networkx", "pytest-timeout"),
        install_pkg="non-editable",
        env={
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "PYTEST_MEMORY_LIMIT_MB": "1900",
            "DARTLAB_TEST_LOCKED": "1",
        },
        # --timeout=300: 테스트 하나가 서면 job 전체(60분)가 아니라 그 테스트만 5분에
        # 죽는다. 실측(2026-08-04): analysis 통합 테스트 하나가 러너 네트워크 지연으로
        # 42분을 서서 job 이 타임아웃 취소됐다. test-full 정상 테스트 최장은 수십 초라
        # 300초는 검출 약화 없는 상한이다.
        cmd=(
            "pytest tests/ -n 2 --dist loadfile --tb=short --timeout=300 "
            "-m 'not requires_data and not heavy and not realData and not freshInstall' "
            "--ignore=tests/_attempts "
            "--ignore=tests/_fixtures/test_analysis_real.py "
            "--ignore=tests/_fixtures/test_credit_real.py "
            "--ignore=tests/_fixtures/test_story_real.py "
            "--ignore=tests/realData "
            "{cov_flags} --benchmark-disable"
        ),
        timeout_minutes=60,
    ),
    "fixture-integration": Gate(
        name="fixture-integration",
        tier="full",
        deps=("pytest", "pytest-asyncio", "hypothesis", "pytest-benchmark"),
        install_pkg="editable",
        env={
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "PYTEST_MEMORY_LIMIT_MB": "5000",
            "DARTLAB_TEST_LOCKED": "1",
        },
        cmd=(
            "for f in tests/_fixtures/test_analysis_real.py tests/_fixtures/test_credit_real.py "
            "tests/_fixtures/test_story_real.py; do "
            'echo "=== $f ==="; '
            'pytest "$f" --tb=short -q --benchmark-disable -p no:cacheprovider || exit 1; '
            "done"
        ),
        timeout_minutes=15,
    ),
    "cross-os-smoke": Gate(
        name="cross-os-smoke",
        tier="full",
        matrix_param="os",
        deps=("pytest", "pytest-asyncio", "hypothesis", "build", "pytest-cov", "pytest-benchmark"),
        install_pkg="editable",
        env={"PYTHONIOENCODING": "utf-8", "DARTLAB_TEST_LOCKED": "1"},
        cmd=(
            "python -X utf8 -m pytest tests/core/test_bundledResources.py "
            'tests/audit/test_wheelPackaging.py -m "unit and not heavy" --tb=short '
            "--no-cov --benchmark-disable && "
            "python -X utf8 tests/audit/checkSilentFail.py"
        ),
    ),
    "product-smoke-wheel": Gate(
        name="product-smoke-wheel",
        tier="full",
        deps=("uv",),
        install_pkg="none",
        env={"PYTHONUNBUFFERED": "1"},
        cmd="python -X utf8 tests/audit/runProductSmokeWheel.py",
        timeout_minutes=30,
    ),
    "realdata-plan": Gate(
        name="realdata-plan",
        tier="full",
        install_pkg="none",
        fetch_depth=0,
        env={"DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures"},
        cmd=(
            "python -X utf8 .github/scripts/ops/planRealdata.py > /tmp/tests.json && "
            "cat /tmp/tests.json && "
            "COUNT=$(python -c \"import json; print(len(json.load(open('/tmp/tests.json'))))\") && "
            'echo "tests=$(cat /tmp/tests.json)" >> "${GITHUB_OUTPUT:-/dev/null}" && '
            'if [ "$COUNT" -gt 0 ]; then '
            'echo hasAny=true >> "${GITHUB_OUTPUT:-/dev/null}"; '
            "python -m pip install --upgrade pip && "
            "pip install -e . && "
            "python -X utf8 .github/scripts/ops/prepareRealdataScanCache.py; "
            'else echo hasAny=false >> "${GITHUB_OUTPUT:-/dev/null}"; fi'
        ),
    ),
    "realdata-suite": Gate(
        name="realdata-suite",
        tier="full",
        matrix_param="test",
        deps=("pytest", "pytest-asyncio", "pytest-rerunfailures", "hypothesis"),
        install_pkg="editable",
        env={
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "PYTEST_MEMORY_LIMIT_MB": "6000",
            "DARTLAB_TEST_LOCKED": "1",
        },
        cmd="bash tests/test-realdata.sh tests/realData/{test_file} -v --tb=short",
        timeout_minutes=30,
    ),
    # ─ Tier 3 — Nightly ───────────────────────────────────────────────────
    "guard-full-census": Gate(
        name="guard-full-census",
        tier="nightly",
        deps=PYTEST_PARALLEL,
        install_pkg="editable",
        env={"DARTLAB_PROVIDER_SCOPE": "dart,edgar"},
        cmd=("python -X utf8 tests/audit/dartlabGuard.py full --baseline tests/audit/_baselines/dartlabGuard.json"),
        timeout_minutes=15,
    ),
    "realdata-suite-full": Gate(
        name="realdata-suite-full",
        tier="nightly",
        matrix_param="test",
        deps=("pytest", "pytest-asyncio", "pytest-rerunfailures", "hypothesis"),
        install_pkg="editable",
        env={
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "PYTEST_MEMORY_LIMIT_MB": "6000",
            "DARTLAB_TEST_LOCKED": "1",
        },
        cmd="bash tests/test-realdata.sh tests/realData/{test_file} -v --tb=short",
        timeout_minutes=30,
    ),
    "external-venv-smoke": Gate(
        name="external-venv-smoke",
        tier="nightly",
        deps=("uv",),
        install_pkg="none",
        setup=(
            "uv venv /tmp/smoke-venv --python 3.12",
            "uv pip install --python /tmp/smoke-venv dartlab",
        ),
        env={"PYTHONUNBUFFERED": "1"},
        cmd=(
            "/tmp/smoke-venv/bin/python -X utf8 tests/audit/productSmoke.py "
            "--suite release --data-mode empty --import-mode installed "
            "--json-out product-smoke-pypi-release.json"
        ),
        timeout_minutes=45,
    ),
    "freshInstall": Gate(
        name="freshInstall",
        tier="nightly",
        deps=("pytest", "pytest-asyncio", "pytest-rerunfailures", "hypothesis"),
        install_pkg="editable",
        env={"PYTEST_MEMORY_LIMIT_MB": "6000", "DARTLAB_TEST_LOCKED": "1"},
        cmd="bash tests/test-realdata.sh tests/realData/test_freshInstall.py -v --tb=short",
        timeout_minutes=30,
    ),
    "mutation-testing": Gate(
        name="mutation-testing",
        tier="nightly",
        deps=("pytest", "pytest-asyncio", "hypothesis", "mutmut>=3.0"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        setup=("rm -rf .mutmut-cache mutants/",),
        cmd=(
            "(mutmut run || true) && "
            "(mutmut results > mutation-results.txt 2>&1 || true) && "
            "cat mutation-results.txt | head -100"
        ),
        blocking=False,
        timeout_minutes=90,
    ),
    "dart-panel-only": Gate(
        name="dart-panel-only",
        tier="fast",
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="python -X utf8 tests/audit/dartPanelOnly.py",
        blocking=True,
        timeout_minutes=5,
    ),
    # T3-2 — benchmark weekly gate. nightly tier blocking=False (baseline ±10% 회귀만 알람)
    "benchmark-weekly": Gate(
        name="benchmark-weekly",
        tier="nightly",
        deps=("pytest", "pytest-benchmark"),
        install_pkg="editable",
        env={"DARTLAB_TEST_LOCKED": "1"},
        cmd="pytest tests/benchmarks/_scenarios/ -m benchmark --benchmark-only --benchmark-json=benchmark-results.json -v --tb=short",
        blocking=False,
        timeout_minutes=30,
    ),
}


# ──────────────────────────────────────────────────────────────────────────
# 실행 헬퍼
# ──────────────────────────────────────────────────────────────────────────


def _shellInvocation(shellCmd: str) -> tuple[list[str] | str, dict[str, object]]:
    """조합한 POSIX 명령을 실제로 POSIX shell 로 돌리게 만든다.

    게이트 명령은 CI 의 bash 를 전제로 쓰여 있다. 작은따옴표로 감싼 인자,
    `&&`, `$(...)`, 파이프가 그대로 들어 있다. 그런데 `shell=True` 는 Windows 에서
    `cmd.exe` 를 쓴다. `cmd.exe` 는 작은따옴표를 인용부호로 보지 않으므로 이런 일이 났다.

        pip install 'pandera[polars]>=0.29.0,<0.33'

    여기서 `>` 가 리다이렉션이 되어 repo 루트에 `0.29.0` 이라는 빈 파일이 생기고,
    pip 은 망가진 인자를 받는다. `pytest -m 'unit and not requires_data'` 도 마커
    표현식이 네 조각으로 쪼개져 죽는다. 그래서 이 도구가 로컬에서 늘 빨간불이었고,
    강행규칙이 가리키는 "CI 27 게이트 SSOT" 가 정작 운영자 기계에서 못 돌았다.

    Windows 에서는 bash 를 명시해 부른다. 그 밖에서는 `shell=True` 그대로다.

    Args:
        shellCmd: 조합된 POSIX shell 명령 한 줄.

    Returns:
        `subprocess.run` 에 넘길 (위치 인자 목록, 키워드 인자) 짝.
    """
    if os.name != "nt":
        return [shellCmd], {"shell": True}
    bash = shutil.which("bash")
    if bash is None:
        raise SystemExit(
            "게이트 명령은 POSIX shell 을 전제로 한다. bash 를 못 찾았다. Git for Windows 의 bash 를 PATH 에 넣어라."
        )
    return [[bash, "-c", shellCmd]], {}


def buildShellCommand(gate: Gate, mp: dict[str, str]) -> str:
    """deps + setup + cmd 를 단일 shell 명령으로 조합. CI 와 로컬 동일.

    mp: matrix param 치환용. python=3.13 / test_file=test_ai.py / os=ubuntu 등.
    """
    parts: list[str] = []

    # 1. deps install
    if gate.deps:
        parts.append("python -m pip install --upgrade pip")
        deps_quoted = " ".join(shlex.quote(d) for d in gate.deps)
        parts.append(f"pip install {deps_quoted}")

    # 2. package install — dartlab 은 single base install SSOT (extras 그룹 금지).
    if gate.install_pkg == "editable":
        parts.append("pip install -e .")
    elif gate.install_pkg == "non-editable":
        parts.append("pip install .")
    # "none" → 설치 안 함

    # 3. setup (wheel build · venv 생성 등)
    parts.extend(gate.setup)

    # 4. main cmd — placeholder 치환
    cmd = gate.cmd
    if gate.matrix_param == "python":
        # test-full 의 cov_flags 분기 — 3.12 만 cov 활성
        py = mp.get("python", "3.12")
        cov_flags = (
            "--cov=dartlab --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=40"
            if py == "3.12"
            else "--no-cov"
        )
        cmd = cmd.format(cov_flags=cov_flags)
    elif gate.matrix_param == "test":
        cmd = cmd.format(test_file=mp.get("test", REALDATA_SHARDS[0]))
    # os 는 cmd 자체 변형 없음 (runner 만 다름)
    parts.append(cmd)

    return " && ".join(p for p in parts if p)


def resolveGateEnv(raw: dict[str, str], base: dict[str, str] | None = None) -> dict[str, str]:
    """GATES env 값을 현재 실행 환경에 맞게 해석한다.

    GitHub Actions expression 은 workflow YAML 안에서만 평가된다. ``tests/run.py`` 의
    GATES dict 값은 Python 런타임 문자열이므로, CI 에서는 ``GITHUB_WORKSPACE`` 로 직접
    치환해야 한다.
    """
    base_env = base or os.environ
    workspace = base_env.get("GITHUB_WORKSPACE")
    out: dict[str, str] = {}
    for key, value in raw.items():
        if "${{ github.workspace }}" in value:
            if not workspace:
                continue
            out[key] = value.replace("${{ github.workspace }}", workspace)
            continue
        if "${{" in value:
            continue
        out[key] = value
    return out


def runGate(name: str, *, dry_run: bool, mp: dict[str, str]) -> int:
    """단일 게이트 실행. blocking=False 면 exit code 무관하게 0 반환."""
    if name not in GATES:
        print(f"[run.py] unknown gate: {name}", file=sys.stderr)
        print(f"  available: {', '.join(sorted(GATES))}", file=sys.stderr)
        return 2
    gate = GATES[name]

    # GITHUB_OUTPUT-style placeholder 는 로컬에선 의미 없으니 빼고 보여줌.
    # 단, GITHUB_WORKSPACE 는 tests/run.py 내부에서 직접 치환한다.
    env_local = resolveGateEnv(gate.env)
    if env_local:
        env_str = " ".join(f"{k}={shlex.quote(v)}" for k, v in env_local.items())
    else:
        env_str = ""

    shell_cmd = buildShellCommand(gate, mp)

    print(f"\n━━━ gate: {gate.name}  (tier={gate.tier}, blocking={gate.blocking}) ━━━")
    if env_str:
        print(f"env: {env_str}")
    print(f"cmd: {shell_cmd}\n")

    if dry_run:
        return 0

    full_env = os.environ.copy()
    full_env.update(env_local)
    runArgs, runKwargs = _shellInvocation(shell_cmd)
    proc = subprocess.run(  # noqa: S603 - CI dispatcher; cmd 는 본 파일 내부 dict 에서만 옴
        *runArgs, env=full_env, cwd=REPO_ROOT, **runKwargs
    )
    if proc.returncode != 0 and not gate.blocking:
        print(f"[run.py] {gate.name} fail (blocking=False) → 통과로 처리", file=sys.stderr)
        return 0
    return proc.returncode


def runTier(tier: Tier, *, blocking_only: bool, dry_run: bool) -> int:
    """tier 의 게이트들을 순차 실행. matrix-driven 게이트는 첫 항목만 (로컬 검증용)."""
    gates = [g for g in GATES.values() if g.tier == tier]
    if blocking_only:
        gates = [g for g in gates if g.blocking]
    failed: list[str] = []
    for gate in gates:
        mp: dict[str, str] = {}
        if gate.matrix_param == "python":
            mp = {"python": "3.12"}
        elif gate.matrix_param == "test":
            mp = {"test": REALDATA_SHARDS[0]}
        # matrix_param="os" 는 로컬 OS 그대로 (placeholder 없음)
        rc = runGate(gate.name, dry_run=dry_run, mp=mp)
        if rc != 0:
            failed.append(gate.name)
    if failed:
        print(f"\n[run.py] FAILED: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(f"\n[run.py] tier {tier} ({len(gates)} gates) PASSED")
    return 0


def cmdList() -> int:
    """전체 게이트 표 출력."""
    print(f"{'name':<26} {'tier':<8} {'block':<6} {'matrix':<8} {'runner'}")
    print("─" * 70)
    for gate in GATES.values():
        print(
            f"{gate.name:<26} {gate.tier:<8} "
            f"{'Y' if gate.blocking else 'N':<6} "
            f"{(gate.matrix_param or '-'):<8} {gate.runner}"
        )
    print(
        f"\ntotal: {len(GATES)} gates "
        f"(fast={sum(1 for g in GATES.values() if g.tier == 'fast')}, "
        f"full={sum(1 for g in GATES.values() if g.tier == 'full')}, "
        f"nightly={sum(1 for g in GATES.values() if g.tier == 'nightly')})"
    )
    return 0


def cmdAuditSelf() -> int:
    """GATES 무결성 검사 — 중복 name · 비어있는 cmd · matrix placeholder 누락."""
    errors: list[str] = []
    names = [g.name for g in GATES.values()]
    if len(names) != len(set(names)):
        errors.append("GATES 에 중복 name 존재")
    for gate in GATES.values():
        if not gate.cmd:
            errors.append(f"{gate.name}: cmd 비어있음")
        if gate.matrix_param == "python" and "{cov_flags}" not in gate.cmd:
            errors.append(f"{gate.name}: matrix_param=python 인데 {{cov_flags}} placeholder 없음")
        if gate.matrix_param == "test" and "{test_file}" not in gate.cmd:
            errors.append(f"{gate.name}: matrix_param=test 인데 {{test_file}} placeholder 없음")
        if gate.tier not in ("fast", "full", "nightly"):
            errors.append(f"{gate.name}: 알 수 없는 tier {gate.tier}")
    if errors:
        for e in errors:
            print(f"[audit-self] {e}", file=sys.stderr)
        return 1
    print(f"[audit-self] OK — {len(GATES)} gates 무결성 확인")
    return 0


# ──────────────────────────────────────────────────────────────────────────
# 사람용 문서 동기화 — GATES → gates:auto 블록 (드리프트 0)
# ──────────────────────────────────────────────────────────────────────────

# 사람용 문서가 호스팅하는 자동 블록 경계. 본 마커 쌍 사이는 손으로 적지 않고
# `tests/run.py docs --write` 가 GATES 에서 렌더한 표로 덮어쓴다.
GATES_BLOCK_START = "<!-- gates:auto:start — `tests/run.py docs --write` 가 생성. 손으로 편집 금지 -->"
GATES_BLOCK_END = "<!-- gates:auto:end -->"

# 자동 블록을 품는 문서 (REPO_ROOT 기준 상대경로). 새 문서 추가 시 한 줄 + 마커 삽입.
DOC_TARGETS: tuple[str, ...] = (
    "tests/POLICY.md",
    ".claude/skills/ci-fast-local/SKILL.md",
)


def renderGatesBlock() -> str:
    """GATES → 마크다운 게이트 표 (결정적). 문서 gates:auto 블록 내용 SSOT.

    test_runEntrypoint.py 가 각 DOC_TARGETS 의 블록이 본 렌더와 바이트 동일한지
    검사한다. 출력은 GATES insertion order 유지 → 안정적 diff.
    """
    fast = [g for g in GATES.values() if g.tier == "fast"]
    full = [g for g in GATES.values() if g.tier == "full"]
    nightly = [g for g in GATES.values() if g.tier == "nightly"]
    fastBlocking = sum(1 for g in fast if g.blocking)
    lines = [
        f"**합계 {len(GATES)} 게이트 — fast {len(fast)} · full {len(full)} · nightly {len(nightly)}. "
        f"push 전 `preflight` 차단 게이트(fast·blocking) {fastBlocking}.**",
        "",
        "| 게이트 | tier | 차단 | matrix | timeout |",
        "|---|---|---|---|---|",
    ]
    for g in GATES.values():
        lines.append(
            f"| `{g.name}` | {g.tier} | {'✅' if g.blocking else '—'} "
            f"| {g.matrix_param or '-'} | {g.timeout_minutes}m |"
        )
    return "\n".join(lines)


def _syncDocBlock(text: str, block: str) -> tuple[str, bool]:
    """문서 text 의 gates:auto 블록을 block 으로 교체. (새 text, 마커 존재 여부)."""
    start = text.find(GATES_BLOCK_START)
    end = text.find(GATES_BLOCK_END)
    if start == -1 or end == -1 or end < start:
        return text, False
    new_text = text[:start] + GATES_BLOCK_START + "\n" + block + "\n" + text[end:]
    return new_text, True


def cmdDocs(*, write: bool) -> int:
    """DOC_TARGETS 의 gates:auto 블록을 GATES 렌더와 동기화(--write) 또는 검사."""
    block = renderGatesBlock()
    drift: list[str] = []
    for rel in DOC_TARGETS:
        path = REPO_ROOT / rel
        if not path.exists():
            print(f"[docs] {rel}: 파일 없음", file=sys.stderr)
            drift.append(rel)
            continue
        text = path.read_text(encoding="utf-8")
        new_text, found = _syncDocBlock(text, block)
        if not found:
            print(f"[docs] {rel}: gates:auto 마커 쌍 없음 — 마커 삽입 필요", file=sys.stderr)
            drift.append(rel)
            continue
        if new_text == text:
            print(f"[docs] {rel}: in sync")
        elif write:
            path.write_text(new_text, encoding="utf-8")
            print(f"[docs] {rel}: 갱신")
        else:
            print(f"[docs] {rel}: OUT OF SYNC — `tests/run.py docs --write` 필요", file=sys.stderr)
            drift.append(rel)
    if write:
        return 0
    return 1 if drift else 0


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tests/run.py", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_gate = sub.add_parser("gate", help="단일 게이트 실행 (CI matrix 호출용)")
    p_gate.add_argument("name", help="게이트 이름 (list 로 확인)")
    p_gate.add_argument("--python", default="3.12", help="test-full matrix python 버전")
    p_gate.add_argument("--test", default=REALDATA_SHARDS[0], help="realdata-suite matrix 파일명")
    p_gate.add_argument("--os", default="ubuntu-latest", help="cross-os-smoke matrix OS")
    p_gate.add_argument("--dry-run", action="store_true", help="명령 문자열만 출력")

    p_tier = sub.add_parser("tier", help="tier 전체 실행")
    p_tier.add_argument("name", choices=["fast", "full", "nightly"])
    p_tier.add_argument("--blocking-only", action="store_true")
    p_tier.add_argument("--dry-run", action="store_true")

    sub.add_parser("preflight", help="tier fast 의 blocking 만 (push 전 검증)")
    sub.add_parser("list", help="전체 게이트 표")
    sub.add_parser("audit-self", help="GATES 무결성 점검")
    p_docs = sub.add_parser("docs", help="사람용 문서 게이트 표 동기화/검사")
    p_docs.add_argument("--write", action="store_true", help="문서에 렌더 블록 덮어쓰기 (없으면 검사만)")

    args = parser.parse_args(argv)

    if args.command == "gate":
        mp = {"python": args.python, "test": args.test, "os": args.os}
        return runGate(args.name, dry_run=args.dry_run, mp=mp)
    if args.command == "tier":
        return runTier(args.name, blocking_only=args.blocking_only, dry_run=args.dry_run)
    if args.command == "preflight":
        return runTier("fast", blocking_only=True, dry_run=False)
    if args.command == "list":
        return cmdList()
    if args.command == "audit-self":
        return cmdAuditSelf()
    if args.command == "docs":
        return cmdDocs(write=args.write)
    return 2


if __name__ == "__main__":
    sys.exit(main())
