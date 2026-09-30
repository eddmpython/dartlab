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
    assert "기본 완료 범위는 검토, 검증, 커밋, 일반 push까지" in text
    assert "별도 커밋·push 요청을 기다리지 않는다" in text
    assert "git log origin/master..HEAD" in text
    assert "git diff --name-only origin/master..HEAD" in text


def testPushPreservesHoldAndValidationWithoutExtraUiApproval() -> None:
    """일반 push 위임은 UI 검수를 포함하며 보류 지시와 위험한 이력 변경은 구분한다."""
    text = _WORKFLOW.read_text(encoding="utf-8")

    assert "force push" in text
    assert "push 보류" in text
    for path in ("landing/src", "ui/packages/surfaces", "ui/packages/runtime", "ui/apps/local"):
        assert path in text
    assert "검수를 통과한 UI 변경도 별도 승인 없이 일반 push한다" in text
    assert "검증 우회 플래그로 push하지 않는다" in text
    assert "그런 파일이 있다는 이유만으로 검증한" in text
    assert "본인 커밋의 push를 보류하지 않는다" in text


def test_claude_routes_git_rules_without_duplicating_them() -> None:
    """루트 진입 문서는 기여 정본을 가리키고 세부 push 규칙을 복제하지 않는다."""
    text = (_ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    assert "| 기여, 브랜치, commit, push | `operation.contributionWorkflow` |" in text
    assert "UI 표면(`landing/src`" not in text
    assert "staging은 명시 경로만 한다" not in text
