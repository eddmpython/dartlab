"""Company API 입력 검증 테스트."""

import pytest

pytestmark = pytest.mark.unit

from dartlab.server.services.company_api import _VALID_CODE


class TestCompanyCodeValidation:
    def test_valid_numeric_code(self):
        assert _VALID_CODE.match("005930")

    def test_valid_korean_name(self):
        assert _VALID_CODE.match("삼성전자")

    def test_valid_english_ticker(self):
        assert _VALID_CODE.match("AAPL")

    def test_valid_mixed(self):
        assert _VALID_CODE.match("LG전자")

    def test_rejects_path_traversal(self):
        assert not _VALID_CODE.match("../../etc/passwd")

    def test_rejects_slash(self):
        assert not _VALID_CODE.match("abc/def")

    def test_rejects_backslash(self):
        assert not _VALID_CODE.match("abc\\def")

    def test_rejects_dot_dot(self):
        assert not _VALID_CODE.match("..")

    def test_rejects_empty(self):
        assert not _VALID_CODE.match("")

    def test_rejects_too_long(self):
        assert not _VALID_CODE.match("a" * 21)

    def test_rejects_special_chars(self):
        assert not _VALID_CODE.match("abc;drop table")
        assert not _VALID_CODE.match("<script>")

    def test_rejects_space(self):
        assert not _VALID_CODE.match("삼성 전자")
