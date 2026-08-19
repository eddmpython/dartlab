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

    # 버전 값 자체는 고정하지 않는다. Dependabot 이 npm/pyproc 을 daily 로 감시해 bump PR 을
    # 여는데 여기에 현재 버전을 박아 두면 모든 bump 가 이 테스트 하나 때문에 red 가 되고,
    # 사람이 매번 테스트를 손으로 고쳐야 통과한다 (2026-08 PR #113 실측: 호환성 게이트 4 개는
    # 전부 green 인데 이 assert 만 실패). 계약은 "캐럿 없는 정확 pin + lock 일치"이지
    # "특정 버전 유지"가 아니다. 버전 인상 판단은 릴리즈 노트 확인과 눈검수를 동반한 별도 작업이다.
    assert re.fullmatch(r"\d+\.\d+\.\d+", spec), f"pyproc 은 캐럿 없는 정확 버전이어야 한다: {spec!r}"
    assert lock["packages"]["landing"]["dependencies"]["pyproc"] == spec, (
        "lock 의 landing 워크스페이스 참조가 package.json 의 정확 pin 과 달라졌다 "
        f"(lock={lock['packages']['landing']['dependencies']['pyproc']!r}, package.json={spec!r})"
    )
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
