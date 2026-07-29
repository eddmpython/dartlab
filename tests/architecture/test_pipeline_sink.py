"""dartlab.pipeline = L4 sink 자격 가드 — 등록 누락 시 가드 무력화 차단.

``pipeline`` 은 gather fetch + providers build 를 동시에 import 하는 오케스트레이션
sink 다. 그 합법성은 Guard Index 계층표와 source package 발견에 의존한다. 빠지면
cycleScan/import_direction 가 pipeline 을 일반 계층으로 오인한다. 본 테스트가 그 등록과
단방향(``pipeline ↛ cli``)을 영구 lock 한다.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_REPO = Path(__file__).resolve().parents[2]
_PIPELINE = _REPO / "src" / "dartlab" / "pipeline"


def _declaredLayer() -> float | None:
    sys.path.insert(0, str(_REPO / "tests" / "architecture"))
    import test_import_direction as t  # noqa: PLC0415

    return t.LAYER_OF.get("pipeline")


def _primaryPackages() -> tuple[str, ...]:
    sys.path.insert(0, str(_REPO / "tests" / "audit"))
    import cycleScan as c  # noqa: PLC0415

    return tuple(c.PRIMARY_PACKAGES)


def test_pipeline_registered_as_sink() -> None:
    """pipeline 이 L4 계층표와 실제 source package 양쪽에 등재돼 있다."""
    assert _declaredLayer() == 4.0, "Guard Index LAYER_OF 에 pipeline L4 선언 누락"
    assert "pipeline" in _primaryPackages(), "cycleScan.PRIMARY_PACKAGES 에 'pipeline' 누락"


def test_pipeline_does_not_import_cli() -> None:
    """단방향 — pipeline 은 cli 를 import 하지 않는다 (cli → pipeline 만 허용)."""
    assert _PIPELINE.exists(), f"pipeline source root not found: {_PIPELINE}"
    violations: list[str] = []
    for pyFile in _PIPELINE.rglob("*.py"):
        if "__pycache__" in pyFile.parts:
            continue
        try:
            tree = ast.parse(pyFile.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        rel = pyFile.relative_to(_REPO).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("dartlab.cli"):
                violations.append(f"{rel}:{node.lineno}: from {node.module}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("dartlab.cli"):
                        violations.append(f"{rel}:{node.lineno}: import {alias.name}")
    assert not violations, "pipeline → cli 역방향 import 금지:\n" + "\n".join(violations)
