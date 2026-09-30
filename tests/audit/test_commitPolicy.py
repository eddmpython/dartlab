"""새 clone에서도 같은 공개 커밋 규칙과 실제 push 객체를 검사한다."""

from __future__ import annotations

import io
import sys

import pytest

from tests.audit import commitPolicy

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("arguments", "name"),
    [
        (["--check-staged"], "checkStaged"),
        (["--check-push"], "checkPush"),
        (["--check-commit-msg", "message"], "checkCommitMsg"),
    ],
)
def testCliModesReachCanonicalFunctions(arguments, name):
    parsed = commitPolicy.buildParser().parse_args(arguments)
    assert getattr(parsed, name)


def testCommitMessageRequiresMeaningfulKoreanSubject(tmp_path):
    message = tmp_path / "message.txt"
    message.write_text("수정: 배포 버전의 패치 증가를 강제한다\n", encoding="utf-8")
    assert commitPolicy.checkCommitMessage(str(message)) == 0
    message.write_text("fix: something\n", encoding="utf-8")
    assert commitPolicy.checkCommitMessage(str(message)) == 1


def testPushContentComesFromPushedObject(monkeypatch):
    commands = []
    monkeypatch.setattr(commitPolicy, "changedFilesInRange", lambda base, head: ["README.md"])

    def readGit(args):
        commands.append(args)
        return "내용"

    monkeypatch.setattr(commitPolicy, "runGit", readGit)
    assert commitPolicy.checkFilesInRange("base", "actualSha") == 0
    assert commands == [["show", "actualSha:README.md"]]


def testEmptyPushInputIsValid(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n"))
    assert commitPolicy.checkPush() == 0
