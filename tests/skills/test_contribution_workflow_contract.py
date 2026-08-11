"""기여 흐름의 push 판단 계약 회귀 가드."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_ROOT = Path(__file__).resolve().parents[2]
_WORKFLOW = _ROOT / "src" / "dartlab" / "skills" / "specs" / "operation" / "contributionWorkflow.md"


def test_push_decision_uses_complete_cycle_not_request_only() -> None:
    """완결된 green master cycle은 요청 단어 없이도 자동 push 대상으로 판단한다."""
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "push는 별도 요청이 있을 때만 수행한다" not in text
    assert "적정 cycle의 일반 push를 수행한다" in text
    assert "git log origin/master..HEAD" in text
    assert "git diff --name-only origin/master..HEAD" in text


def test_push_decision_preserves_force_hold_and_ui_gates() -> None:
    """위험한 push와 UI 범위는 자동 판단의 예외로 명시한다."""
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "force push" in text
    assert "push 보류" in text
    for path in ("landing/src", "ui/packages/surfaces", "ui/packages/runtime", "ui/apps/local"):
        assert path in text
    assert "운영자의 시각 검수 또는 명시 승인을 기다린다" in text


def test_claude_routes_git_rules_without_duplicating_them() -> None:
    """루트 진입 문서는 기여 정본을 가리키고 세부 push 규칙을 복제하지 않는다."""
    text = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "| 기여, 브랜치, commit, push | `operation.contributionWorkflow` |" in text
    assert "UI 표면(`landing/src`" not in text
    assert "staging은 명시 경로만 한다" not in text
