"""실데이터 실행기가 현재 tests 위치와 인자 경계를 유지하는지 검증한다."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("markerArgs", [[], ["-m", "realData and not network"]])
def testDefaultRunnerFindsEveryFileAndPreservesMarkerArguments(tmp_path, markerArgs):
    bash = "C:/Program Files/Git/bin/bash.exe" if os.name == "nt" else shutil.which("bash")
    assert bash, "실데이터 실행에 필요한 bash가 없습니다"
    repo = tmp_path / "project with spaces"
    tests = repo / "tests"
    realData = tests / "realData"
    realData.mkdir(parents=True)
    runner = tests / "test-realdata.sh"
    shutil.copyfile(REPO_ROOT / "tests/test-realdata.sh", runner)
    for name in ("test_first.py", "test_second.py"):
        (realData / name).write_text("", encoding="utf-8")
    (tests / "test-lock.sh").write_text(
        '#!/usr/bin/env bash\n[ -f "$1" ] || exit 73\nprintf "%s\\0" "$@" >> "$DARTLAB_RUNNER_RECORD"\n',
        encoding="utf-8",
    )
    record = tmp_path / "calls.bin"
    result = subprocess.run(
        [bash, runner.as_posix(), *markerArgs],
        cwd=tmp_path,
        env={**os.environ, "DARTLAB_RUNNER_RECORD": record.as_posix()},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = record.read_bytes().decode().split("\0")[:-1]
    assert calls == [
        part
        for name in ("test_first.py", "test_second.py")
        for part in (f"tests/realData/{name}", *(markerArgs or ["-m", "realData"]), "-v", "--tb=short")
    ]
