"""tests/run.py 의 GATES dict 와 .github/workflows/ci-*.yml 의 matrix.gate 일치 검증.

# Capabilities
GATES ↔ YAML matrix drift 차단. 한쪽에만 게이트 추가 시 PR fail.

# Example
    pytest tests/audit/test_runEntrypoint.py -v

# Returns
모든 게이트가 tier 별로 정확히 한 YAML 의 matrix.gate 에 등장 → 통과.
"""

from __future__ import annotations

import os
import pathlib
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests"))

from run import (  # noqa: E402
    DOC_TARGETS,
    GATES,
    GATES_BLOCK_END,
    GATES_BLOCK_START,
    REALDATA_SHARDS,
    renderGatesBlock,
    resolveGateEnv,
)

WORKFLOWS = REPO_ROOT / ".github" / "workflows"


def _extractInvokedGates(yaml_path: Path) -> set[str]:
    """YAML 안의 모든 `tests/run.py gate <name>` 호출 + matrix.include 의 `gate: X` 캡쳐.

    실제 게이트 호출이 정의 (matrix include or 직접 run 라인) 중 어디에 있든
    잡는다. fan-out 구조 (realdata-plan / realdata-suite 등) 도 포함.
    """
    text = yaml_path.read_text(encoding="utf-8")
    out: set[str] = set()
    # 1) `python ... tests/run.py gate <name>` 직접 호출
    for m in re.finditer(r"tests/run\.py\s+gate\s+([A-Za-z0-9_-]+)", text):
        out.add(m.group(1))
    # 2) `matrix.include` 의 `- gate: X` 또는 `gate: X` 한 줄
    for line in text.splitlines():
        m = re.match(r"\s*-?\s*gate:\s*([A-Za-z0-9_-]+)\s*$", line)
        if m:
            out.add(m.group(1))
    return out


@pytest.mark.unit
def test_gatesDictNoDuplicates():
    names = [g.name for g in GATES.values()]
    assert len(names) == len(set(names)), f"중복 name: {names}"


@pytest.mark.unit
def test_gatesAllHaveCmd():
    empty = [g.name for g in GATES.values() if not g.cmd]
    assert not empty, f"cmd 비어있는 게이트: {empty}"


@pytest.mark.unit
def test_matrixParamPlaceholderPresent():
    """matrix_param 설정된 게이트는 cmd 안에 placeholder 필수."""
    for gate in GATES.values():
        if gate.matrix_param == "python":
            assert "{cov_flags}" in gate.cmd, f"{gate.name}: {{cov_flags}} 누락"
        elif gate.matrix_param == "test":
            assert "{test_file}" in gate.cmd, f"{gate.name}: {{test_file}} 누락"


@pytest.mark.unit
def test_resolveGateEnvSubstitutesGithubWorkspace():
    env = resolveGateEnv(
        {
            "DARTLAB_DATA_DIR": "${{ github.workspace }}/tests/fixtures",
            "STATIC": "value",
            "UNSUPPORTED": "${{ github.output }}",
        },
        {"GITHUB_WORKSPACE": "/tmp/work/repo"},
    )
    assert env == {
        "DARTLAB_DATA_DIR": "/tmp/work/repo/tests/fixtures",
        "STATIC": "value",
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    "tier,filename",
    [
        ("fast", "ci-fast.yml"),
        ("full", "ci-full.yml"),
        ("nightly", "ci-nightly.yml"),
    ],
)
def test_gatesDictMatchesYamlMatrix(tier, filename):
    """GATES tier 별 → 대응 YAML 의 matrix.gate 와 정확히 일치."""
    yaml_path = WORKFLOWS / filename
    if not yaml_path.exists():
        pytest.skip(f"{filename} 미존재 (PR 머지 전 단계)")
    dict_gates = {g.name for g in GATES.values() if g.tier == tier}
    yaml_gates = _extractInvokedGates(yaml_path)
    if not yaml_gates:
        pytest.skip(f"{filename} 에 tests/run.py gate 호출 없음 — 신형 dispatch 미적용")
    only_dict = dict_gates - yaml_gates
    only_yaml = yaml_gates - dict_gates
    msg = []
    if only_dict:
        msg.append(f"GATES 에만 있음 ({tier}): {sorted(only_dict)}")
    if only_yaml:
        msg.append(f"YAML 에만 있음 ({filename}): {sorted(only_yaml)}")
    assert not msg, "\n".join(msg)


@pytest.mark.unit
def test_realdataShardsMatchNightlyMatrix():
    """REALDATA_SHARDS 상수 ↔ ci-nightly.yml realdata-suite-full matrix 일치."""
    yaml_path = WORKFLOWS / "ci-nightly.yml"
    if not yaml_path.exists():
        pytest.skip("ci-nightly.yml 미존재")
    text = yaml_path.read_text(encoding="utf-8")
    # test_file 블록 추출 — multi-line `-` items
    in_block = False
    yaml_shards: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("test_file:"):
            in_block = True
            continue
        if in_block:
            m = re.match(r"-\s*([\w.]+\.py)", s)
            if m:
                yaml_shards.add(m.group(1))
            elif s and not s.startswith("-") and not s.startswith("#"):
                in_block = False
    if not yaml_shards:
        pytest.skip("realdata-suite-full matrix 미발견 (신형 dispatch 적용 전)")
    diff_dict = set(REALDATA_SHARDS) - yaml_shards
    diff_yaml = yaml_shards - set(REALDATA_SHARDS)
    assert not diff_dict and not diff_yaml, f"REALDATA_SHARDS 에만: {sorted(diff_dict)}\nYAML 에만: {sorted(diff_yaml)}"


@pytest.mark.unit
def test_totalGateCountFrozen():
    """30 게이트 동결 — 의도 없는 추가/삭제 방지. 변경 시 본 테스트 함께 수정."""
    assert len(GATES) == 30, f"게이트 수 변경: {len(GATES)} (의도된 변경이면 본 테스트도 수정)"


@pytest.mark.unit
def test_tierDistributionFrozen():
    from collections import Counter

    c = Counter(g.tier for g in GATES.values())
    assert dict(c) == {"fast": 17, "full": 6, "nightly": 7}, f"tier 분포 변경: {dict(c)}"


@pytest.mark.unit
def test_productSmokeDataModesKeepCiAndExternalSeparated():
    """Blocking CI product smoke must not depend on live HF availability."""
    run_product_wheel = (REPO_ROOT / "tests" / "audit" / "runProductSmokeWheel.py").read_text(encoding="utf-8")
    verify_wheel = (REPO_ROOT / ".github" / "scripts" / "verifyWheel.py").read_text(encoding="utf-8")

    assert "--data-mode fixtures" in GATES["smoke"].cmd
    assert '"fixtures"' in run_product_wheel
    assert '"fixtures"' in verify_wheel
    assert "--data-mode empty" in GATES["external-venv-smoke"].cmd


@pytest.mark.unit
@pytest.mark.parametrize("rel", DOC_TARGETS)
def test_docsGatesBlockInSync(rel):
    """사람용 문서의 gates:auto 블록 == GATES 렌더 (드리프트 차단).

    게이트 개수를 손으로 베껴 적어 어긋나는 회귀를 영구 차단.
    out of sync 시: `uv run python -X utf8 tests/run.py docs --write`.
    """
    path = REPO_ROOT / rel
    if not path.exists():
        pytest.skip(f"{rel} 미존재 (PR 머지 전 단계)")
    text = path.read_text(encoding="utf-8")
    start = text.find(GATES_BLOCK_START)
    end = text.find(GATES_BLOCK_END)
    assert start != -1 and end != -1 and start < end, (
        f"{rel}: gates:auto 마커 쌍 없음 — 마커 삽입 후 `tests/run.py docs --write`"
    )
    inner = text[start + len(GATES_BLOCK_START) : end].strip("\n")
    assert inner == renderGatesBlock(), f"{rel}: gates:auto 블록이 GATES 와 어긋남 — `tests/run.py docs --write` 실행"


@pytest.mark.unit
def testGateCommandsRunUnderPosixShell():
    """게이트 명령은 반드시 POSIX shell 로 돌아야 한다.

    명령 문자열은 CI 의 bash 를 전제로 쓰여 있다. 작은따옴표로 감싼 인자, `&&`,
    `$(...)`, 파이프가 그대로 들어 있다. 그런데 `subprocess.run(shell=True)` 는
    Windows 에서 `cmd.exe` 를 쓴다. `cmd.exe` 는 작은따옴표를 인용부호로 보지 않으므로

        pip install 'pandera[polars]>=0.29.0,<0.33'

    의 `>` 가 리다이렉션이 되어 repo 루트에 `0.29.0` 이라는 빈 파일이 생기고,
    `pytest -m 'unit and not requires_data'` 는 마커 표현식이 네 조각으로 쪼개져 죽는다.
    그래서 이 도구가 운영자 기계에서 늘 빨간불이었다. 강행규칙이 가리키는 "CI 게이트
    SSOT" 가 정작 로컬에서 못 도는 상태였고, 그 침묵이 회귀를 CI 까지 흘려보냈다.

    여기 고정하는 것은 Windows 에서 bash 를 명시해 부른다는 것 하나다.
    """
    import runpy

    module = runpy.run_path(str(REPO_ROOT / "tests" / "run.py"))
    invocation = module["_shellInvocation"]

    args, kwargs = invocation("echo hi")

    if os.name == "nt":
        assert kwargs == {}, "Windows 에서는 shell=True 를 쓰지 않는다"
        assert isinstance(args[0], list) and args[0][0].lower().endswith(("bash", "bash.exe")), (
            f"POSIX shell 이 아니다: {args[0]!r}"
        )
        assert args[0][1] == "-c"
    else:
        assert kwargs.get("shell") is True


@pytest.mark.unit
def testQuotedGateArgsSurviveTheShell():
    """따옴표 안의 부등호가 리다이렉션으로 새지 않는지 실제로 돌려서 본다."""
    import runpy
    import subprocess
    import tempfile

    module = runpy.run_path(str(REPO_ROOT / "tests" / "run.py"))
    invocation = module["_shellInvocation"]

    with tempfile.TemporaryDirectory() as work:
        args, kwargs = invocation("python -c \"import sys; print(sys.argv[1])\" 'pkg>=1.2,<3'")
        proc = subprocess.run(*args, cwd=work, capture_output=True, text=True, **kwargs)

        assert proc.returncode == 0, proc.stderr
        assert proc.stdout.strip() == "pkg>=1.2,<3", proc.stdout
        assert not list(pathlib.Path(work).iterdir()), "리다이렉션으로 잔재 파일이 생겼다"
