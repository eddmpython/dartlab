"""데이터 워크플로우 호출 경로 회귀 가드."""

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_edgar_builder_public_facade_imports() -> None:
    from dartlab.scan.builders.edgar import buildEdgarFinance, buildEdgarPrebuild, buildEdgarScan

    assert callable(buildEdgarFinance)
    assert callable(buildEdgarPrebuild)
    assert callable(buildEdgarScan)


def test_edgar_sync_workflow_uses_current_builder_path() -> None:
    repoRoot = Path(__file__).resolve().parents[2]
    workflow = (repoRoot / ".github" / "workflows" / "edgarSync.yml").read_text(encoding="utf-8")

    assert "from dartlab.scan.builders.edgar import buildEdgarPrebuild" in workflow
    assert "buildEdgarFinance(sinceYear=2021" not in workflow
    assert "dartlab.scan.edgarBuilder" not in workflow
