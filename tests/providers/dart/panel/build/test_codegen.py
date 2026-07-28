"""providers/dart/panel/build/codegen.py mirror tests.

생성 모듈 후처리 (`_ruffFormat`) 의 단일 SSOT. 실제 ruff 를 돌리지 않고
`subprocess.run` 을 대역으로 갈아 호출 인자와 실패 흡수 계약만 검증한다.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from dartlab.providers.dart.panel.build.codegen import _ruffFormat

pytestmark = pytest.mark.unit


def test_ruffFormat_invokes_ruff_with_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """대상 경로를 그대로 실은 ruff format 명령 1 회."""
    seen: list[tuple] = []

    def fakeRun(*args, **kwargs):
        seen.append((args, kwargs))
        return "ok"

    monkeypatch.setattr(subprocess, "run", fakeRun)
    target = tmp_path / "generated.py"
    _ruffFormat(target)

    assert len(seen) == 1
    args, kwargs = seen[0]
    assert args[0] == ["uv", "run", "ruff", "format", str(target)]
    assert kwargs["check"] is False
    assert kwargs["capture_output"] is True
    assert kwargs["timeout"] == 60


@pytest.mark.parametrize(
    "boom",
    [
        OSError("ruff 없음"),
        subprocess.SubprocessError("실행 실패"),
        subprocess.TimeoutExpired(cmd="ruff", timeout=60),
    ],
)
def test_ruffFormat_absorbs_expected_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, boom: Exception) -> None:
    """ruff 부재·실행 실패·타임아웃은 흡수 (생성물은 이미 valid python)."""

    def fakeRun(*args, **kwargs):
        raise boom

    monkeypatch.setattr(subprocess, "run", fakeRun)
    assert _ruffFormat(tmp_path / "generated.py") is None


def test_ruffFormat_does_not_swallow_unexpected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """계약 밖 예외까지 삼키지는 않는다 (조용한 실패 확산 가드)."""

    def fakeRun(*args, **kwargs):
        raise RuntimeError("예상 밖")

    monkeypatch.setattr(subprocess, "run", fakeRun)
    with pytest.raises(RuntimeError):
        _ruffFormat(tmp_path / "generated.py")


def test_call_sites_share_one_definition() -> None:
    """noteTaxonomy 와 spineBuilder 가 사본이 아니라 같은 함수를 본다 (중복 재발 가드)."""
    from dartlab.providers.dart.panel.build import noteTaxonomy, spineBuilder

    assert noteTaxonomy._ruffFormat is _ruffFormat
    assert spineBuilder._ruffFormat is _ruffFormat
