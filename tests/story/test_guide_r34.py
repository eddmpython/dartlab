"""R34 audit 회귀 — handleError feature 전달."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_handle_error_with_feature_includes_feature_label():
    """R34-1: feature 인자 전달 시 결과에 [feature] prefix 포함."""
    from dartlab.core.messagingErrors import handleError

    msg = handleError(ValueError("test"), feature="ai")
    assert "[ai]" in msg


def test_handle_error_without_feature_no_prefix():
    """feature 없으면 prefix 없음."""
    from dartlab.core.messagingErrors import handleError

    msg = handleError(ValueError("test"))
    assert "[ai]" not in msg
    assert "ValueError" in msg
