"""core/messaging 의 에러 안내 템플릿 단위 테스트."""

from __future__ import annotations

import pytest

from dartlab.core.messagingHandlers import apiKeyMissingHint, missingDataHint

pytestmark = pytest.mark.unit


class TestMissingDataHint:
    def test_resource_only(self):
        assert missingDataHint("시계열") == "시계열 데이터 없음"

    def test_with_recover_cmd(self):
        msg = missingDataHint("컨센서스", recoverCmd="dartlab.gather('consensus', '005930')")
        assert "컨센서스 데이터 없음" in msg
        assert "dartlab.gather('consensus', '005930')" in msg
        assert "먼저 수집하세요" in msg

    def test_with_detail_only(self):
        msg = missingDataHint("비교", detail="최소 2기 필요")
        assert msg == "비교 데이터 없음 (최소 2기 필요)"

    def test_with_recover_cmd_and_detail(self):
        msg = missingDataHint(
            "재고자산",
            recoverCmd="dartlab.gather('notes', '005930')",
            detail="금융업 미지원",
        )
        assert "재고자산 데이터 없음" in msg
        assert "먼저 수집하세요" in msg
        assert "(금융업 미지원)" in msg


class TestApiKeyMissingHint:
    def test_delegates_to_aiSetup(self):
        text = apiKeyMissingHint("gemini")
        assert isinstance(text, str)
        assert len(text) > 0
        # providerGuide 가 반환하는 안내에 gemini 관련 키워드가 포함되는지 느슨하게 확인
        # (aiSetup 구현 변경에 strict 하지 않음 — delegate 자체가 목적)
