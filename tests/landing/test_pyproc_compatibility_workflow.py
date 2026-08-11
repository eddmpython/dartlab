"""pyproc npm dependency and compatibility workflow contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_pyproc_uses_npm_exact_dependency_update_flow() -> None:
    """pyproc updates use npm and Dependabot instead of a version rewrite scheduler."""
    package = json.loads(Path("landing/package.json").read_text(encoding="utf-8"))
    lock = json.loads(Path("package-lock.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path("landing/runtime-manifest.json").read_text(encoding="utf-8"))
    spec = package["dependencies"]["pyproc"]
    installed = lock["packages"]["node_modules/pyproc"]["version"]

    assert spec == "0.0.14"
    assert re.fullmatch(r"\d+\.\d+\.\d+", spec)
    assert lock["packages"]["landing"]["dependencies"]["pyproc"] == spec
    assert installed == spec
    assert "pyproc" not in manifest

    assert not Path(".github/workflows/pyprocPinBump.yml").exists()
    assert not Path(".github/scripts/pyprocResolvePin.mjs").exists()
    assert not Path(".github/scripts/pyprocApplyPin.mjs").exists()


def test_pyproc_pull_requests_run_all_compatibility_gates() -> None:
    workflow = Path(".github/workflows/pyprocCompatibility.yml").read_text(encoding="utf-8")
    dependabot = Path(".github/dependabot.yml").read_text(encoding="utf-8")

    assert "pull_request:" in workflow
    assert "push:" in workflow
    assert "workflow_dispatch:" in workflow
    assert "schedule:" not in workflow
    assert "contents: read" in workflow
    assert workflow.count('- "package.json"') == 2
    assert workflow.count('- "landing/svelte.config.js"') == 2
    assert "npm ci" in workflow
    assert "pyprocSmoke.mjs" in workflow
    assert "pyprocForkSmoke.mjs" in workflow
    assert "npm --workspace landing run check" in workflow
    assert "npm --workspace landing run test" in workflow
    assert "npm --workspace landing run build" in workflow
    assert "compatibility:" in workflow
    assert "needs: [gate-a, landing, gate-b]" in workflow

    assert 'dependency-name: "pyproc"' in dependabot
    assert 'versioning-strategy: "increase"' in dependabot
    assert 'interval: "daily"' in dependabot
