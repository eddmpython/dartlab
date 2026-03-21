"""서버 resolve 메시지 빌더 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.server.resolve import ResolveResult, build_ambiguous_msg, build_not_found_msg


class TestResolveResult:
    def test_defaults(self):
        r = ResolveResult()
        assert r.company is None
        assert r.not_found is False
        assert r.ambiguous is False
        assert r.suggestions == []

    def test_not_found(self):
        r = ResolveResult(not_found=True, suggestions=[{"corpName": "삼성전자", "stockCode": "005930"}])
        assert r.not_found is True
        assert len(r.suggestions) == 1

    def test_ambiguous(self):
        r = ResolveResult(
            ambiguous=True,
            suggestions=[
                {"corpName": "LG전자", "stockCode": "066570"},
                {"corpName": "LG디스플레이", "stockCode": "034220"},
            ],
        )
        assert r.ambiguous is True
        assert len(r.suggestions) == 2


class TestBuildNotFoundMsg:
    def test_no_suggestions(self):
        msg = build_not_found_msg([])
        assert "찾을 수 없습니다" in msg
        assert "종목코드" in msg

    def test_with_suggestions(self):
        suggestions = [
            {"corpName": "삼성전자", "stockCode": "005930"},
            {"corpName": "삼성전기", "stockCode": "009150"},
        ]
        msg = build_not_found_msg(suggestions)
        assert "삼성전자" in msg
        assert "005930" in msg
        assert "삼성전기" in msg
        assert "찾지 못했습니다" in msg


class TestBuildAmbiguousMsg:
    def test_multiple_suggestions(self):
        suggestions = [
            {"corpName": "LG전자", "stockCode": "066570"},
            {"corpName": "LG디스플레이", "stockCode": "034220"},
        ]
        msg = build_ambiguous_msg(suggestions)
        assert "여러 종목" in msg
        assert "LG전자" in msg
        assert "066570" in msg
        assert "LG디스플레이" in msg
