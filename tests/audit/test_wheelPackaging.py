"""Wheel packaging 계약 — 실제 빌드된 wheel 에 필수 리소스가 모두 들어가는지.

========================================
이 파일이 잡는 버그 클래스:
========================================
`python -m build` (또는 `uv build`) 로 실제 wheel 을 빌드한 뒤,
git-tracked 된 모든 번들 리소스(JSON/parquet/py.typed)가 wheel 에
포함됐는지 zip 파일 목록 수준에서 직접 검증한다.

과거 사고 (2026-04-19, 0.9.15 + 0.9.16 모두):
    PyPI 에 올라간 wheel 에 `src/dartlab/reference/data/parserMappings/` 누락 →
    외부 사용자가 `import dartlab` 하는 순간 `FileNotFoundError`.
    wheel-smoke job 이 별도로 빌드한 wheel 을 검증했기에 PyPI 에 올라간
    wheel 과 다른 대상을 본 게 원인. 이 테스트는 매 push 마다 실제 빌드를
    수행해서 packaging 설정 (pyproject.toml + .gitignore) 자체를 검증한다.

주의:
    - `mark unit` 이지만 실제 `python -m build` 를 호출하므로 ~10초 소요.
    - CI 에서 1회 실행만 해도 2026-04-19 class 회귀는 차단됨.
    - 로컬 호출 시 기존 `dist/` 를 건드리지 않도록 tmp_path 사용.
"""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src" / "dartlab"


def _gitTrackedBundleFiles() -> set[str]:
    """git 이 추적하는 src/dartlab/ 하위 번들 리소스 (JSON/parquet/py.typed)."""
    result = subprocess.run(
        ["git", "ls-files", "src/dartlab/"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    bundled: set[str] = set()
    for line in result.stdout.splitlines():
        if not line:
            continue
        if not (_REPO_ROOT / line).exists():
            continue
        # wheel 에 들어가면 안 되는 경로
        if "/_reference/" in line or "/_backup/" in line:
            continue
        if line.startswith("src/dartlab/engines/edinet/"):
            continue
        if line.startswith("src/dartlab/engines/esg/"):
            continue
        if line.startswith("src/dartlab/engines/event/"):
            continue
        if line.startswith("src/dartlab/engines/supply/"):
            continue
        if line.startswith("src/dartlab/engines/watch/"):
            continue
        if line.endswith((".json", ".parquet")) or line.endswith("py.typed"):
            bundled.add(line.removeprefix("src/"))  # "dartlab/..." 형태
    return bundled


@pytest.fixture(scope="module")
def builtWheel(tmp_path_factory) -> Path:
    """현재 소스로 wheel 을 빌드해서 경로 반환. 테스트 끝나면 tmp_path 자동 정리."""
    out = tmp_path_factory.mktemp("wheel-packaging-test")
    result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--outdir", str(out)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"wheel 빌드 실패 (python -m build 미설치 가능): {result.stderr[-500:]}")
    wheels = list(out.glob("*.whl"))
    if not wheels:
        pytest.skip("빌드 산출물에 wheel 없음")
    return wheels[0]


def test_bundleFiles_allIncludedInWheel(builtWheel: Path):
    """git-tracked 번들 리소스가 모두 wheel 에 포함됐는지 전수 검증.

    2026-04-19 사고 핵심 방어. packaging 설정이 깨져서 특정 디렉토리가
    통째로 빠지는 케이스를 파일 수준으로 잡는다.
    """
    with zipfile.ZipFile(builtWheel) as zf:
        inWheel = set(zf.namelist())

    expected = _gitTrackedBundleFiles()
    missing = sorted(f for f in expected if f not in inWheel)
    assert not missing, (
        f"wheel 에 누락된 git-tracked 번들 리소스 {len(missing)}건:\n"
        + "\n".join(f"  - {m}" for m in missing[:20])
        + (f"\n  ... +{len(missing) - 20} 건 더" if len(missing) > 20 else "")
        + "\n\npyproject.toml [tool.hatch.build.targets.wheel] 의 include/artifacts 확인 필요."
    )


def test_parserMappings_inWheel(builtWheel: Path):
    """2026-04-19 사고 직접 타겟 — parserMappings/ 4개 JSON 개별 확인."""
    with zipfile.ZipFile(builtWheel) as zf:
        names = zf.namelist()
    required = [
        "dartlab/providers/mappers/mapperData/parserMappings/panelTopics.json",
        "dartlab/providers/mappers/mapperData/parserMappings/affiliate.json",
        "dartlab/providers/mappers/mapperData/parserMappings/costByNature.json",
        "dartlab/providers/mappers/mapperData/parserMappings/sectorPriors.json",
    ]
    for req in required:
        assert req in names, (
            f"wheel 에 {req} 누락 — 2026-04-19 packaging 사고 직접 재현 조건.\n"
            f"외부 사용자가 pip install dartlab 후 `import dartlab` 만 해도 crash."
        )


def test_accountMappings_inWheel(builtWheel: Path):
    """accountMappings.json — 재무제표 라벨링 전멸 방지."""
    with zipfile.ZipFile(builtWheel) as zf:
        names = zf.namelist()
    assert "dartlab/reference/data/accountMappings.json" in names, (
        "accountMappings.json 누락 — 모든 계정 라벨이 snakeId 로만 표시되는 회귀"
    )


def test_sectionMappings_inWheel(builtWheel: Path):
    """DART + EDGAR + EDINET section mapping JSON 들."""
    with zipfile.ZipFile(builtWheel) as zf:
        names = zf.namelist()
    required = [
        "dartlab/providers/dart/sectionMappings.json",
        "dartlab/providers/edgar/docs/sections/mapperData/sectionMappings.json",
        "dartlab/providers/edinet/docs/sections/mapperData/sectionMappings.json",
    ]
    for req in required:
        assert req in names, f"wheel 에 {req} 누락"


def test_skillSpecs_inWheel(builtWheel: Path):
    """루트 Skill OS 원본이 wheel 런타임 package data로 포함되는지 검증."""
    with zipfile.ZipFile(builtWheel) as zf:
        names = set(zf.namelist())

    required = [
        "dartlab/skills/specs/start/dartlabSkillOs.md",
        "dartlab/skills/specs/engines/analysis/SKILL.md",
        "dartlab/skills/specs/engines/analysis/profitability.md",
        "dartlab/skills/specs/engines/scan/undervaluedQuality.md",
        "dartlab/skills/specs/operation/apiContract.md",
        "dartlab/skills/specs/runtime/mcp.md",
        "dartlab/skills/catalog.json",
        "dartlab/skills/pyodide.json",
    ]
    for req in required:
        assert req in names, f"wheel 에 Skill OS 리소스 누락: {req}"


@pytest.mark.heavy
def test_installedWheel_importAndSectionsLoad(builtWheel: Path, tmp_path):
    """빌드된 wheel 을 격리 venv 에 설치하고 실제로 panel topic 매핑 로더 호출.

    단순 파일 존재가 아니라 "설치 후 import → 런타임 체인 정상 동작" 까지 검증.
    2026-04-19 사고의 최종 증상(외부 사용자 첫 호출 crash)을 직접 재현.
    """
    import os
    import shutil
    import venv

    # venv 생성
    venvDir = tmp_path / "testvenv"
    venv.create(venvDir, with_pip=True)
    if os.name == "nt":
        py = venvDir / "Scripts" / "python.exe"
    else:
        py = venvDir / "bin" / "python"

    # wheel 설치
    install = subprocess.run(
        [str(py), "-m", "pip", "install", "--quiet", str(builtWheel)],
        capture_output=True,
        text=True,
    )
    if install.returncode != 0:
        pytest.skip(f"venv 에 wheel 설치 실패: {install.stderr[-300:]}")

    # loadSections().chapterByMajor 실제 호출 — 호환 이름, 실제 파일은 panelTopics.json
    check = subprocess.run(
        [
            str(py),
            "-X",
            "utf8",
            "-c",
            "from dartlab.providers.mappers.parserMapper import loadSections; "
            "s = loadSections(); "
            "assert s.get('chapterByMajor'), 'chapterByMajor empty — 2026-04-19 사고 재현'; "
            "print('OK chapterByMajor:', len(s['chapterByMajor']))",
        ],
        capture_output=True,
        text=True,
    )
    # venv 정리 (테스트 완료 후 자동이지만 명시적으로)
    try:
        shutil.rmtree(venvDir, ignore_errors=True)
    except Exception:
        pass

    assert check.returncode == 0, (
        f"설치된 wheel 에서 loadSections 호출 실패 — 2026-04-19 사고 재현:\n"
        f"STDOUT: {check.stdout}\n"
        f"STDERR: {check.stderr}"
    )


# ════════════════════════════════════════
# .gitignore 구조 lint — 2026-04-19 사고 원인 패턴 재유입 차단
# ════════════════════════════════════════


def _gitignoreDirPatterns() -> list[tuple[int, str]]:
    """`.gitignore` 에서 디렉토리 ignore 패턴을 (line_no, pattern) 로 수집.

    주석/빈 줄/negation(`!...`)/파일 확장자 패턴(`*.x`) 는 제외.
    """
    result: list[tuple[int, str]] = []
    gi = _REPO_ROOT / ".gitignore"
    for idx, raw in enumerate(gi.read_text(encoding="utf-8").splitlines(), start=1):
        s = raw.strip()
        if not s or s.startswith("#") or s.startswith("!"):
            continue
        # 디렉토리 패턴: 트레일링 슬래시 or 명확한 디렉토리 이름
        if s.endswith("/"):
            result.append((idx, s))
    return result


def test_gitignorePatterns_noUnrootedDirsOverlappingSrcDartlab():
    """`.gitignore` 의 루트-미지정 디렉토리 패턴이 src/dartlab 하위와 매치되지 않음.

    2026-04-19 사고 직접 원인: `.gitignore` 의 `data/` (leading `/` 없음) 이
    `src/dartlab/reference/data/` 까지 매치해서 wheel 에서 누락됨. 같은 class 의
    재유입을 lint 로 차단한다.

    검사: 각 unrooted 디렉토리 패턴 (예: `data/`, `_backup/`, `logs/`) 이
    `src/dartlab/` 하위에 동명 디렉토리와 매치되면 FAIL. leading `/` 를 붙여
    루트 스코프로 명시하거나, 구체 경로를 지정해야 함.

    단, 명백히 전체 repo 에서 제외돼도 안전한 패턴 (예: `__pycache__/`,
    `.venv`) 은 화이트리스트로 허용.
    """
    # src/dartlab 하위에 있어도 제외하는 게 실제로 의도된 패턴
    _SAFE_UNROOTED: frozenset[str] = frozenset(
        {
            "__pycache__/",
            "node_modules/",  # src/dartlab 내부에 존재 불가
            ".venv/",
        }
    )

    offenders: list[str] = []
    for lineNo, pattern in _gitignoreDirPatterns():
        if pattern.startswith("/"):
            continue  # 이미 루트 스코프
        if pattern in _SAFE_UNROOTED:
            continue
        # src/dartlab 하위에 동일 이름 디렉토리가 존재하면 위험 패턴
        dirName = pattern.rstrip("/")
        matches = list(_SRC_ROOT.rglob(dirName))
        matches = [m for m in matches if m.is_dir()]
        if matches:
            offenders.append(
                f"  .gitignore:{lineNo}  `{pattern}`  → 매치: "
                + ", ".join(str(m.relative_to(_REPO_ROOT)) for m in matches[:3])
            )

    assert not offenders, (
        "⚠ .gitignore 에 src/dartlab 하위와 매치되는 루트-미지정 디렉토리 패턴 발견:\n" + "\n".join(offenders) + "\n\n"
        "해결: 패턴 앞에 `/` 를 붙여 루트 스코프로 만들거나, 구체 경로를 지정하세요.\n"
        "  예: `data/` → `/data/`\n"
        "  예: `_backup/` → `/_backup/` 또는 `/providers/dart/finance/mapperData/_backup/`\n"
        "과거 사고 (2026-04-19) 와 동일 class 의 packaging 누락을 구조적으로 차단합니다."
    )


# ════════════════════════════════════════
# Loud-fail 로더 계약 — Phase A1 에서 전환한 로더들
# ════════════════════════════════════════


def test_dalio48Match_loadCases_loudFail_onMissingData(monkeypatch):
    """dalio48Match._loadCases 가 파일 부재 시 FileNotFoundError 발생."""
    from importlib import resources

    import dartlab.synth.dalio48Match as mod

    # 실제 파일이 있는 상태 기준선: 정상 로드
    cases = mod._loadCases()
    assert isinstance(cases, list)
    assert len(cases) > 0, "dalio48Cases.json 이 빈 cases — 번들 리소스 손상"

    # 파일 부재 시뮬레이션: resources.files 의 joinpath 를 가짜로 만들어 FNF 유도
    class _FakeRef:
        def open(self, *args, **kwargs):
            raise FileNotFoundError("simulated missing")

    class _FakeFiles:
        def joinpath(self, name):
            return _FakeRef()

    monkeypatch.setattr(resources, "files", lambda pkg: _FakeFiles())
    with pytest.raises(FileNotFoundError) as exc:
        mod._loadCases()
    assert "dalio48Cases.json" in str(exc.value)
    assert "pip install" in str(exc.value), "복구 명령 안내 누락"


def test_rrCrisisDB_loadRrCrises_loudFail_onMissingData(monkeypatch):
    """rrCrisisDB._loadRrCrises 가 파일 부재 시 FileNotFoundError 발생."""
    from importlib import resources

    import dartlab.macro.crisis.rrCrisisDB as mod

    crises = mod._loadRrCrises()
    assert isinstance(crises, list)
    assert len(crises) > 0

    class _FakeRef:
        def open(self, *args, **kwargs):
            raise FileNotFoundError("simulated missing")

    class _FakeFiles:
        def joinpath(self, name):
            return _FakeRef()

    monkeypatch.setattr(resources, "files", lambda pkg: _FakeFiles())
    with pytest.raises(FileNotFoundError) as exc:
        mod._loadRrCrises()
    assert "rrCrises800y.json" in str(exc.value)


# ── pyodide wheel 마커 게이트 (옛 pyodide/build.py strip 리스트 대체) ──
#
# pyodide(브라우저)는 같은 plain wheel 을 micropip.install(wheel) 로 설치한다. micropip 은 emscripten
# 에서 Requires-Dist 마커를 평가해 pyodide 비호환 dep 을 건너뛴다. 그래서 pyodide 에서 설치 불가하거나
# 순수휠 없는 transitive(marimo->msgspec 등)를 끄는 dep 은 반드시 "; sys_platform != 'emscripten'"
# 마커로 배제돼야 한다. 마커 없이 새 비호환 dep 이 들어오면 micropip.install(wheel) 이 조용히 깨진다
# (marimo 0.10.7 사고 class). 이 테스트가 그 회귀를 빌드 전에 차단한다. 마커가 유일 SSOT.
_PYODIDE_INCOMPATIBLE_DEPS = {
    "marimo",  # transitive msgspec 순수휠 부재 → micropip.install 깨짐
    "duckdb",
    "fastapi",
    "uvicorn",
    "sse-starlette",
    "mcp",
    "openai",
    "huggingface-hub",
    "plotly",
    "qrcode",
    "pyyaml",
}


def test_pyodideIncompatibleDeps_excludedUnderEmscripten():
    """pyodide 비호환 dep 이 emscripten 환경 마커로 전부 배제되는지 검증 (strip 리스트 대체 게이트)."""
    import tomllib

    from packaging.markers import default_environment
    from packaging.requirements import Requirement

    data = tomllib.loads((_REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data["project"]["dependencies"]

    env = default_environment()
    env["sys_platform"] = "emscripten"
    env["platform_system"] = "Emscripten"

    included = set()
    for raw in deps:
        req = Requirement(raw)
        if req.marker is None or req.marker.evaluate(env):
            included.add(req.name.lower().replace("_", "-"))

    leaked = _PYODIDE_INCOMPATIBLE_DEPS & included
    assert not leaked, (
        f"pyodide 비호환 dep 이 emscripten wheel 에 포함됨: {sorted(leaked)}. "
        "pyproject.toml 에서 해당 dep 에 \"; sys_platform != 'emscripten'\" 마커를 붙여라 "
        "(micropip.install(wheel) 이 브라우저에서 조용히 깨지는 회귀 차단)."
    )
