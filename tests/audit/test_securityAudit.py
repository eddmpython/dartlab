"""설치판만 통과하거나 앞선 실패가 뒷검사를 생략시키는 보안 감사 회귀를 막는다."""

import pytest

from tests.audit import securityAudit

pytestmark = pytest.mark.unit


def testAuditsLockedDependenciesAndBothNpmProjectsAfterInstalledFailure(monkeypatch, tmp_path):
    calls = []

    def run(args, repo):
        calls.append(args)
        return (1, "installed vulnerability") if len(calls) == 1 else (0, "clean")

    monkeypatch.setattr(securityAudit, "runCommand", run)
    results = securityAudit.runAudits(tmp_path, tmp_path)
    assert [label for label, _, _ in results] == [
        "installed-python",
        "lock-export",
        "locked-python",
        "npm-workspace",
        "npm-push-hub",
    ]
    assert results[0][1] == 1
    assert "--locked" in calls[1]
    assert {"--all-groups", "--all-extras"} <= set(calls[1])
    assert "--no-deps" in calls[2] and "-r" in calls[2]
    assert calls[2][-1] == str(tmp_path / "requirements.txt")
    assert "infra/workers/pushHub" in calls[-1]


def testFailedExportCannotTurnIntoAnEmptySuccessfulLockAudit(monkeypatch, tmp_path):
    calls = []

    def run(args, repo):
        calls.append(args)
        return (2, "stale lock") if args[0] == "uv" else (0, "clean")

    monkeypatch.setattr(securityAudit, "runCommand", run)
    results = securityAudit.runAudits(tmp_path, tmp_path)
    assert next(code for label, code, _ in results if label == "locked-python") != 0
    assert not any("-r" in args for args in calls)
    assert sum("audit" in args for args in calls) == 2


def testMissingAuditToolFailsVisibly(monkeypatch, tmp_path):
    def missing(*args, **kwargs):
        raise FileNotFoundError("missing audit tool")

    monkeypatch.setattr(securityAudit.subprocess, "run", missing)
    code, output = securityAudit.runCommand(["missing"], tmp_path)
    assert code != 0
    assert "missing audit tool" in output
