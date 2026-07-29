"""core.progress SSOT facade 단위 테스트 — 환경 분기 + track/progressBar (네트워크 없음).

pytest 는 stdout 캡처 → 'silent' 환경이라 바가 렌더되지 않는다(출력 오염 0). 비-silent
경로는 ``_detectEnv`` 를 monkeypatch 해 rich Progress 빌드까지 커버한다.
"""

from __future__ import annotations

import sys

import pytest

from dartlab.core import progress

pytestmark = pytest.mark.unit


def test_detectEnv_silentUnderCapture():
    """pytest 캡처(비-TTY·비-jupyter·비-marimo)에선 'silent'."""
    assert progress._detectEnv() == "silent"


def test_detectEnv_marimo(monkeypatch):
    """stdout 모듈이 marimo.* 면 'marimo'."""

    class _Stream:
        pass

    _Stream.__module__ = "marimo._messaging.streams"
    monkeypatch.setattr(sys, "stdout", _Stream())
    assert progress._detectEnv() == "marimo"


def test_consoleFor_marimoForcesTerminal():
    """마리모 console 은 force_terminal(라이브 ANSI emit)."""
    assert progress._consoleFor("marimo").is_terminal is True


def test_track_yieldsAllItems_silent():
    """track 은 항목을 그대로 전부 yield (silent → no-op 바)."""
    items = list(range(5))
    assert list(progress.track(items, desc="t")) == items


def test_progressBar_silentNoop():
    """silent 환경에서 progressBar 컨트롤러는 no-op (크래시 없음)."""
    with progress.progressBar(3, desc="t", detailed=True) as p:
        p.update(item="x", advance=1)
        p.advance()
        sub = p.subtask("s", 2)
        sub.advance()


def test_track_detailedRealProgress(monkeypatch):
    """비-silent(terminal) 강제 시 detailed rich Progress 빌드 + 전 항목 yield."""
    monkeypatch.setattr(progress, "_detectEnv", lambda: "terminal")
    assert list(progress.track(range(3), desc="t", detailed=True)) == [0, 1, 2]


def test_progressBar_realSubtask(monkeypatch):
    """비-silent 강제 시 progressBar + subtask + update(item) 가 크래시 없이 동작."""
    monkeypatch.setattr(progress, "_detectEnv", lambda: "terminal")
    with progress.progressBar(2, desc="outer", detailed=True) as p:
        p.update(item="a")
        sub = p.subtask("inner", 3)
        sub.advance(3)
        p.advance(2)


def test_track_totalFromLenless(monkeypatch):
    """len 불가 iterable 도 total=None 으로 동작 (스피너)."""
    monkeypatch.setattr(progress, "_detectEnv", lambda: "terminal")
    gen = (i for i in range(3))
    assert list(progress.track(gen, desc="t")) == [0, 1, 2]


def test_track_propagatesBrokenSizedLength():
    """Sized 구현체 내부의 TypeError를 unsized iterable로 오인하지 않는다."""

    class BrokenLength:
        def __iter__(self):
            return iter([1, 2])

        def __len__(self):
            raise TypeError("broken length")

    with pytest.raises(TypeError, match="broken length"):
        list(progress.track(BrokenLength(), desc="t"))


def test_track_explicitTotalDoesNotInspectLength():
    """호출자가 total을 주면 iterable의 길이 구현에 의존하지 않는다."""

    class BrokenLength:
        def __iter__(self):
            return iter([1, 2])

        def __len__(self):
            raise TypeError("broken length")

    assert list(progress.track(BrokenLength(), desc="t", total=2)) == [1, 2]
