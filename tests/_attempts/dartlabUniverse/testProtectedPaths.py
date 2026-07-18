"""Universe U0가 기존 runtime, frontend, content에 역의존이나 byte 변경을 만들지 않는지 검증한다."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests._attempts.dartlabUniverse.census import defaultRepoRoot, runFullCensus
from tests._attempts.dartlabUniverse.testSupport import fakeConfig, fakeHfApi
from tests._attempts.dartlabUniverse.validation.coverage import (
    assertProtectedPathsUnchanged,
    captureProtectedPathDigests,
)


def testProtectedPathDigestDetectsAddedRemovedAndChanged(tmp_path: Path):
    protected = tmp_path / "protected"
    protected.mkdir()
    target = protected / "value.txt"
    target.write_text("before", encoding="utf-8")
    before = captureProtectedPathDigests(tmp_path, ("protected",))
    assertProtectedPathsUnchanged(before, dict(before))

    target.write_text("after", encoding="utf-8")
    after = captureProtectedPathDigests(tmp_path, ("protected",))
    with pytest.raises(AssertionError):
        assertProtectedPathsUnchanged(before, after)


def testFakeFullCensusLeavesProtectedSystemsByteIdentical():
    repoRoot = defaultRepoRoot()
    before = captureProtectedPathDigests(repoRoot)

    runFullCensus(
        repoRoot,
        configModule=fakeConfig(),
        apiFactory=lambda: fakeHfApi(repoRoot),
        protectExisting=True,
    )

    after = captureProtectedPathDigests(repoRoot)
    assertProtectedPathsUnchanged(before, after)


def testExistingPythonPackagesDoNotImportUniverse():
    repoRoot = defaultRepoRoot()
    violations = []
    for path in sorted((repoRoot / "src" / "dartlab").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            if any(
                name.startswith("dartlab.universe") or name.startswith("tests._attempts.dartlabUniverse")
                for name in names
            ):
                violations.append(path.relative_to(repoRoot).as_posix())
    assert violations == []


def testUiDataCoreDoesNotReferenceUniverseImplementation():
    repoRoot = defaultRepoRoot()
    dataRoot = repoRoot / "ui" / "packages" / "runtime" / "src" / "data"
    violations = []
    for path in sorted(dataRoot.rglob("*")):
        if path.suffix not in {".ts", ".svelte", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        if "dartlabUniverse" in text or "@dartlab/universe" in text:
            violations.append(path.relative_to(repoRoot).as_posix())
    assert violations == []
