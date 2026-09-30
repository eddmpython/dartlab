"""버전 번호를 임의로 올리거나 작업 트리와 push 대상을 바꿔 검사를 통과하지 못한다."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest

from tests.audit import releasePolicy

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("candidate", ["0.12.0", "0.12.1"])
def testPublishedOrNextPatch(candidate):
    releasePolicy.checkTransition("0.12.0", candidate)


@pytest.mark.parametrize("candidate", ["0.13.0", "1.0.0", "0.11.9", "0.12.2", "0.12.01", "0.12.1rc1"])
def testUnauthorizedVersionsBlocked(candidate):
    with pytest.raises(ValueError):
        releasePolicy.checkTransition("0.12.0", candidate)


def testOnlyNextUnpublishedPatchCanPublish():
    releasePolicy.checkTransition("0.12.0", "0.12.1", publishing=True)
    with pytest.raises(ValueError):
        releasePolicy.checkTransition("0.12.0", "0.12.0", publishing=True)


def testStageAndLockAreReadFromIndex(monkeypatch):
    observed = []

    def gitText(*args):
        observed.append(args)
        if args[-1] == ":pyproject.toml":
            return '[project]\nversion = "0.12.1"\n'
        return '[[package]]\nname = "dartlab"\nversion = "0.12.0"\n'

    monkeypatch.setattr(releasePolicy, "gitText", gitText)
    with pytest.raises(ValueError, match="버전 불일치"):
        releasePolicy.versionAt("")
    assert observed == [("show", ":pyproject.toml"), ("show", ":uv.lock")]


def testPushChecksActualShaNotHead(monkeypatch):
    observed = []
    monkeypatch.setattr(releasePolicy, "versionAt", lambda ref: observed.append(ref) or "0.13.0")
    with pytest.raises(ValueError, match="major/minor"):
        releasePolicy.checkPush("0.12.0", [f"refs/heads/other {'a' * 40} refs/heads/other {'0' * 40}"])
    assert observed == ["a" * 40]


@pytest.mark.parametrize("tag", ["v0.12.2", "v0.13.0"])
def testTagCannotDisagreeWithPackage(monkeypatch, tag):
    monkeypatch.setattr(releasePolicy, "versionAt", lambda ref: "0.12.1")
    with pytest.raises(ValueError, match="태그/패키지"):
        releasePolicy.checkPush("0.12.0", [f"refs/tags/{tag} {'a' * 40} refs/tags/{tag} {'0' * 40}"])


def testReleaseTagDeletionAndMovementAreBlocked(monkeypatch):
    monkeypatch.setattr(releasePolicy, "versionAt", lambda ref: "0.12.1")
    for localSha in ("0" * 40, "a" * 40):
        with pytest.raises(ValueError, match="공개 릴리즈 태그"):
            releasePolicy.checkPush("0.12.0", [f"refs/tags/v0.12.1 {localSha} refs/tags/v0.12.1 {'b' * 40}"])


def testInvalidIntermediateCommitCannotHideBehindValidHead(monkeypatch):
    monkeypatch.setattr(releasePolicy, "versionAt", lambda ref: "0.13.0" if ref == "bad" else "0.12.0")
    monkeypatch.setattr(releasePolicy, "gitText", lambda *args: "bad\n")
    with pytest.raises(ValueError, match="major/minor"):
        releasePolicy.checkPush("0.12.0", [f"refs/heads/master {'a' * 40} refs/heads/master {'b' * 40}"])


def testPypiUnavailableFailsClosed(monkeypatch, capsys):
    def unavailable():
        raise OSError("offline")

    monkeypatch.setattr(sys, "argv", ["releasePolicy", "--staged"])
    monkeypatch.setattr(releasePolicy, "publishedVersion", unavailable)
    assert releasePolicy.main() == 1
    assert "BLOCKED: offline" in capsys.readouterr().err


def testSkipVariablesDoNotAuthorizeMinor(monkeypatch):
    monkeypatch.setenv("DARTLAB_SKIP_PREPUSH", "1")
    monkeypatch.setenv("DARTLAB_ALLOW_MINOR", "1")
    monkeypatch.setattr(sys, "argv", ["releasePolicy", "--pre-push"])
    monkeypatch.setattr(sys, "stdin", io.StringIO(f"refs/heads/master {'a' * 40} refs/heads/master {'0' * 40}\n"))
    monkeypatch.setattr(releasePolicy, "publishedVersion", lambda: "0.12.0")
    monkeypatch.setattr(releasePolicy, "versionAt", lambda ref: "0.13.0")
    assert releasePolicy.main() == 1


def testHookPropagatesPreflightFailure(tmp_path):
    """실제 shell hook에서 preflight의 실패가 tail/skip 환경변수로 사라지지 않는다."""
    from tests.run import _windowsPosixBash

    bash = _windowsPosixBash()
    if bash is None:
        pytest.skip("POSIX shell 없음")
    root = Path(__file__).resolve().parents[2]
    hook = (root / ".githooks/pre-push").read_text(encoding="utf-8")
    # 버전/산출물 단계는 이미 성공한 상황을 재현하고 preflight의 원 종료코드를 검사한다.
    localHook = tmp_path / "pre-push"
    localHook.write_text(hook, encoding="utf-8", newline="\n")
    fakeBin = tmp_path / "bin"
    fakeBin.mkdir()
    for name, body in {"python3": "exit 0", "uv": "echo preflight-failed; exit 23"}.items():
        executable = fakeBin / name
        executable.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8", newline="\n")
        executable.chmod(0o755)
    result = subprocess.run(
        [
            bash,
            "-c",
            'PATH="$(cd "$1" && pwd):$PATH" DARTLAB_SKIP_PREPUSH=1 sh "$2"',
            "hook-test",
            fakeBin.as_posix(),
            str(localHook),
        ],
        cwd=tmp_path,
        input="",
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 23, result.stdout + result.stderr
    assert "preflight-failed" in result.stdout
