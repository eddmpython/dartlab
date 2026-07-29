"""기존 audit/pytest gate 실행 wrapper."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ARCHITECTURE_TESTS: tuple[str, ...] = (
    "tests/architecture/test_l15_entry_rule.py",
    "tests/architecture/test_l15_no_cross_import.py::test_l15_no_new_dynamic_cross_import",
)


@dataclass(frozen=True)
class ExternalGate:
    """외부 gate 실행 결과."""

    name: str
    command: str
    status: str
    durationMs: int
    returnCode: int
    outputTail: str

    def toDict(self) -> dict[str, Any]:
        """JSON 직렬화용 dict."""
        return asdict(self)


def runCommand(repoRoot: Path, name: str, command: list[str], *, env: dict[str, str] | None = None) -> ExternalGate:
    """subprocess gate 1개 실행."""
    fullEnv = os.environ.copy()
    if env:
        fullEnv.update(env)
    srcPath = str(repoRoot / "src")
    fullEnv["PYTHONPATH"] = srcPath + os.pathsep + fullEnv.get("PYTHONPATH", "")
    start = time.perf_counter()
    result = subprocess.run(command, cwd=repoRoot, capture_output=True, text=True, encoding="utf-8", env=fullEnv)
    durationMs = int((time.perf_counter() - start) * 1000)
    output = (result.stdout or "") + (result.stderr or "")
    return ExternalGate(
        name=name,
        command=commandToText(command),
        status="pass" if result.returncode == 0 else "fail",
        durationMs=durationMs,
        returnCode=result.returncode,
        outputTail=tail(output),
    )


def l0L15Gates(repoRoot: Path, providers: str) -> list[ExternalGate]:
    """현재 L0~L1.5 acceptance gate 묶음."""
    py = sys.executable
    providerEnv = {"DARTLAB_PROVIDER_SCOPE": providers}
    return [
        runCommand(repoRoot, "cycleScan", [py, "-X", "utf8", "tests/audit/cycleScan.py", "--strict-toplevel"]),
        runCommand(repoRoot, "architecturePytest", architectureCommand(py)),
        runCommand(
            repoRoot,
            "folderMirror",
            [py, "-X", "utf8", "tests/audit/folderMirror.py", "--providers", providers, "--strict"],
            env=providerEnv,
        ),
        runCommand(repoRoot, "gatherGate", [py, "-X", "utf8", "tests/audit/gatherGate.py"]),
        runCommand(
            repoRoot,
            "providerGate",
            [py, "-X", "utf8", "tests/audit/providerGate.py", "--providers", providers],
            env=providerEnv,
        ),
        runCommand(
            repoRoot,
            "publicApiSmoke",
            [
                py,
                "-X",
                "utf8",
                "-c",
                "import dartlab; from dartlab import Company; "
                "assert callable(Company); assert callable(dartlab.gather); assert callable(dartlab.scan)",
            ],
        ),
    ]


def fullGates(repoRoot: Path, providers: str) -> list[ExternalGate]:
    """full census v1 gate 묶음."""
    py = sys.executable
    providerEnv = {"DARTLAB_PROVIDER_SCOPE": providers}
    gates = l0L15Gates(repoRoot, providers)
    gates.append(
        runCommand(
            repoRoot,
            "structureMirror",
            [py, "-X", "utf8", "-m", "pytest", "tests/architecture/test_structureMirror.py", "-v", "--tb=short"],
            env=providerEnv,
        )
    )
    return gates


def quickGates(repoRoot: Path, changedFiles: list[str], providers: str) -> list[ExternalGate]:
    """변경 파일 기반 빠른 gate 선택."""
    py = sys.executable
    providerEnv = {"DARTLAB_PROVIDER_SCOPE": providers}
    normalized = [item.replace("\\", "/") for item in changedFiles]
    if not normalized or all(not item.endswith(".py") for item in normalized):
        return [runCommand(repoRoot, "diffCheck", ["git", "diff", "--check"])]

    gates: list[ExternalGate] = []
    needsArchitecture = any(
        item.startswith(
            (
                "src/dartlab/core/",
                "src/dartlab/scan/",
                "src/dartlab/frame/",
                "src/dartlab/synth/",
                "src/dartlab/reference/",
            )
        )
        for item in normalized
    )
    needsGather = any(item.startswith("src/dartlab/gather/") for item in normalized)
    needsProvider = any(
        item.startswith(("src/dartlab/providers/dart/", "src/dartlab/providers/edgar/")) for item in normalized
    )

    if needsArchitecture:
        gates.append(runCommand(repoRoot, "architecturePytest", architectureCommand(py)))
    if needsGather:
        gates.append(runCommand(repoRoot, "gatherGate", [py, "-X", "utf8", "tests/audit/gatherGate.py"]))
    if needsProvider:
        gates.append(
            runCommand(
                repoRoot,
                "providerGate",
                [py, "-X", "utf8", "tests/audit/providerGate.py", "--providers", providers],
                env=providerEnv,
            )
        )
    if not gates:
        gates.append(runCommand(repoRoot, "diffCheck", ["git", "diff", "--check"]))
    return gates


def changedFiles(repoRoot: Path, changedFrom: str) -> list[str]:
    """git diff 기반 변경 파일 목록. committed range 와 working tree 를 함께 본다."""
    commands = [
        ["git", "diff", "--name-only", f"{changedFrom}...HEAD"],
        ["git", "diff", "--name-only", "--cached"],
        ["git", "diff", "--name-only"],
    ]
    files: set[str] = set()
    for command in commands:
        result = subprocess.run(command, cwd=repoRoot, capture_output=True, text=True, encoding="utf-8")
        if result.returncode == 0:
            files.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(files)


def architectureCommand(py: str) -> list[str]:
    """Guard 내부 architecture pytest 명령. Guard pytest 자체 재귀 호출은 제외한다."""
    return [py, "-X", "utf8", "-m", "pytest", *ARCHITECTURE_TESTS, "-v"]


def commandToText(command: list[str]) -> str:
    """표시용 command string."""
    return " ".join(command)


def tail(text: str, maxLines: int = 40) -> str:
    """긴 gate 출력 tail."""
    lines = text.splitlines()
    return "\n".join(lines[-maxLines:])
