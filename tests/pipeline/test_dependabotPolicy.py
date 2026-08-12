from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / ".github" / "scripts" / "dependabotPolicy.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "dependabotAutoMerge.yml"


def _module():
    spec = importlib.util.spec_from_file_location("dependabotPolicy", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _safePolicy(**overrides):
    values = {
        "actor": "dependabot[bot]",
        "author": "dependabot[bot]",
        "ecosystem": "pip",
        "updateType": "version-update:semver-patch",
        "baseRef": "master",
        "draft": False,
        "title": "보안(deps): update httpx",
        "maintainerChanges": False,
    }
    values.update(overrides)
    return _module().evaluatePolicy(**values)


@pytest.mark.unit
@pytest.mark.parametrize("updateType", ["version-update:semver-patch", "version-update:semver-minor"])
def testAllowsOnlyPythonPatchAndMinor(updateType):
    assert _safePolicy(updateType=updateType) == {"allowed": True, "reason": "safePythonPatchOrMinor"}


@pytest.mark.unit
@pytest.mark.parametrize(
    "override",
    [
        {"updateType": "version-update:semver-major"},
        {"ecosystem": "npm"},
        {"ecosystem": "github-actions"},
        {"actor": "maintainer"},
        {"author": "maintainer"},
        {"draft": True},
        {"title": "[CORELOOP-R] dependency change"},
        {"maintainerChanges": True},
    ],
)
def testRejectsExcludedDependabotClasses(override):
    assert _safePolicy(**override)["allowed"] is False


@pytest.mark.unit
def testChecksRequireEveryWorkflowAndGreenState():
    evaluate = _module().evaluateChecks
    green = [
        {"workflow": "CI Fast", "name": "test", "bucket": "pass"},
        {"workflow": "CodeQL", "name": "analyze", "bucket": "pass"},
        {"workflow": "Policy Check", "name": "policy", "bucket": "skipping"},
    ]
    assert evaluate(green)["allowed"] is True
    assert evaluate(green[:-1])["reason"] == "missingRequiredWorkflows"
    assert evaluate([*green, {"workflow": "extra", "name": "pending", "bucket": "pending"}])["reason"] == (
        "checksNotGreen"
    )


@pytest.mark.unit
def testWorkflowUsesTrustedMetadataAndPostCiMerge():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target:" in text
    assert "workflow_run:" in text
    assert "dependabot/fetch-metadata@v2" in text
    assert "CI Fast, CodeQL, Policy Check" in text
    assert "steps.checks.outputs.allowed == 'true'" in text
    assert 'gh pr merge "$PR_NUMBER" --squash' in text
    assert "--auto" not in text


@pytest.mark.unit
def testDependabotGroupsLimitUpdatesToPatchAndMinor():
    text = (REPO_ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")
    groups = text.split("    groups:", 1)[1].split("  # 정기 버전 범프 중단", 1)[0]
    assert groups.count("update-types:") == 3
    assert groups.count('- "minor"') == 3
    assert groups.count('- "patch"') == 3
