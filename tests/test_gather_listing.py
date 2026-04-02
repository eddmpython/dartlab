"""gather/listing.py 단위 테스트 — 종목 검색, 코드 매핑, fuzzy search.

외부 API (KRX KIND) 호출은 모두 mock 처리.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

pytestmark = pytest.mark.unit


# ── 테스트용 상장법인 데이터 ──


def _mock_listing_df() -> pl.DataFrame:
    """테스트용 상장법인 DataFrame."""
    return pl.DataFrame(
        {
            "종목코드": ["005930", "000660", "035420", "035720", "006400", "051910"],
            "회사명": ["삼성전자", "SK하이닉스", "NAVER", "카카오", "삼성SDI", "LG화학"],
            "업종": ["전자부품", "전자부품", "서비스업", "서비스업", "전기전자", "화학"],
            "주요제품": ["반도체", "반도체", "포털", "포털", "2차전지", "석유화학"],
        }
    )


@pytest.fixture(autouse=True)
def _mock_kind_list(monkeypatch):
    """모든 테스트에서 getKindList()를 mock 데이터로 대체."""
    mock_df = _mock_listing_df()

    # dartlab.gather is a lazy entry object; import the real module directly
    from dartlab.gather import listing as listing_mod

    monkeypatch.setattr(listing_mod, "_memory", mock_df)
    monkeypatch.setattr(listing_mod, "_memoryTs", 9999999999.0)  # 만료 안 됨

    # fuzzySearch 캐시 무효화 (새 데이터 반영)
    monkeypatch.setattr(listing_mod, "_searchCache", None)

    yield


# ══════════════════════════════════════
# 1. getKindList
# ══════════════════════════════════════


class TestGetKindList:
    def test_returns_dataframe(self):
        from dartlab.gather.listing import getKindList

        df = getKindList()
        assert isinstance(df, pl.DataFrame)
        assert df.height == 6

    def test_has_required_columns(self):
        from dartlab.gather.listing import getKindList

        df = getKindList()
        assert "종목코드" in df.columns
        assert "회사명" in df.columns

    def test_memory_cache_used(self):
        from dartlab.gather.listing import getKindList

        df1 = getKindList()
        df2 = getKindList()
        # Should be the same object (memory cache)
        assert df1 is df2


# ══════════════════════════════════════
# 2. codeToName
# ══════════════════════════════════════


class TestCodeToName:
    def test_existing_code(self):
        from dartlab.gather.listing import codeToName

        assert codeToName("005930") == "삼성전자"

    def test_existing_code_sk(self):
        from dartlab.gather.listing import codeToName

        assert codeToName("000660") == "SK하이닉스"

    def test_nonexistent_code(self):
        from dartlab.gather.listing import codeToName

        assert codeToName("999999") is None

    def test_empty_code(self):
        from dartlab.gather.listing import codeToName

        assert codeToName("") is None


# ══════════════════════════════════════
# 3. nameToCode
# ══════════════════════════════════════


class TestNameToCode:
    def test_exact_name(self):
        from dartlab.gather.listing import nameToCode

        assert nameToCode("삼성전자") == "005930"

    def test_exact_name_naver(self):
        from dartlab.gather.listing import nameToCode

        assert nameToCode("NAVER") == "035420"

    def test_nonexistent_name(self):
        from dartlab.gather.listing import nameToCode

        assert nameToCode("존재하지않는회사") is None

    def test_partial_name_no_match(self):
        from dartlab.gather.listing import nameToCode

        # nameToCode requires exact match
        assert nameToCode("삼성") is None


# ══════════════════════════════════════
# 4. searchName
# ══════════════════════════════════════


class TestSearchName:
    def test_partial_match(self):
        from dartlab.gather.listing import searchName

        result = searchName("삼성")
        assert isinstance(result, pl.DataFrame)
        assert result.height >= 2  # 삼성전자, 삼성SDI

    def test_exact_match(self):
        from dartlab.gather.listing import searchName

        result = searchName("삼성전자")
        assert result.height == 1
        assert result["종목코드"][0] == "005930"

    def test_english_name(self):
        from dartlab.gather.listing import searchName

        result = searchName("NAVER")
        assert result.height == 1

    def test_no_match(self):
        from dartlab.gather.listing import searchName

        result = searchName("존재하지않는키워드")
        assert result.height == 0

    def test_empty_keyword(self):
        from dartlab.gather.listing import searchName

        result = searchName("")
        assert result.height == 0

    def test_whitespace_keyword(self):
        from dartlab.gather.listing import searchName

        result = searchName("   ")
        assert result.height == 0


# ══════════════════════════════════════
# 5. fuzzySearch
# ══════════════════════════════════════


class TestFuzzySearch:
    def test_exact_match(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("삼성전자")
        assert result.height >= 1
        assert result["회사명"][0] == "삼성전자"

    def test_substring_match(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("하이닉스")
        assert result.height >= 1
        assert "SK하이닉스" in result["회사명"].to_list()

    def test_typo_tolerance(self):
        from dartlab.gather.listing import fuzzySearch

        # "카카옹" has edit distance 1 from "카카오" (3 chars, 1 edit allowed)
        result = fuzzySearch("카카옹")
        assert result.height >= 1

    def test_empty_keyword(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("")
        assert result.height == 0

    def test_max_results(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("삼성", maxResults=1)
        assert result.height <= 1

    def test_no_match(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("zzzzzzzzzzz")
        assert result.height == 0

    def test_prefix_match_ranked_higher(self):
        from dartlab.gather.listing import fuzzySearch

        result = fuzzySearch("LG")
        if result.height >= 1:
            # LG로 시작하는 회사가 먼저
            assert result["회사명"][0].startswith("LG")


# ══════════════════════════════════════
# 6. 한글 유틸리티 함수
# ══════════════════════════════════════


class TestKoreanUtils:
    def test_decompose_char_hangul(self):
        from dartlab.gather.listing import _decompose_char

        assert _decompose_char("삼") == "ㅅ"
        assert _decompose_char("전") == "ㅈ"
        assert _decompose_char("자") == "ㅈ"

    def test_decompose_char_already_jamo(self):
        from dartlab.gather.listing import _decompose_char

        assert _decompose_char("ㅅ") == "ㅅ"
        assert _decompose_char("ㄱ") == "ㄱ"

    def test_decompose_char_non_korean(self):
        from dartlab.gather.listing import _decompose_char

        assert _decompose_char("A") == "A"
        assert _decompose_char("1") == "1"

    def test_extract_chosung(self):
        from dartlab.gather.listing import _extract_chosung

        assert _extract_chosung("삼성") == "ㅅㅅ"
        assert _extract_chosung("카카오") == "ㅋㅋㅇ"

    def test_extract_chosung_mixed(self):
        from dartlab.gather.listing import _extract_chosung

        result = _extract_chosung("LG화학")
        assert result.startswith("LG")

    def test_is_all_chosung(self):
        from dartlab.gather.listing import _is_all_chosung

        assert _is_all_chosung("ㅅㅅ") is True
        assert _is_all_chosung("ㅅㅅㅈㅈ") is True
        assert _is_all_chosung("삼성") is False
        assert _is_all_chosung("AB") is False

    def test_levenshtein_identical(self):
        from dartlab.gather.listing import _levenshtein

        assert _levenshtein("abc", "abc") == 0

    def test_levenshtein_one_edit(self):
        from dartlab.gather.listing import _levenshtein

        assert _levenshtein("abc", "abd") == 1
        assert _levenshtein("abc", "ab") == 1
        assert _levenshtein("abc", "abcd") == 1

    def test_levenshtein_empty(self):
        from dartlab.gather.listing import _levenshtein

        assert _levenshtein("abc", "") == 3
        assert _levenshtein("", "") == 0

    def test_levenshtein_symmetric(self):
        from dartlab.gather.listing import _levenshtein

        assert _levenshtein("abc", "xyz") == _levenshtein("xyz", "abc")

    def test_levenshtein_korean(self):
        from dartlab.gather.listing import _levenshtein

        assert _levenshtein("카카오", "카카옹") == 1
        assert _levenshtein("삼성", "삼성전자") == 2


# ══════════════════════════════════════
# 7. _TableParser
# ══════════════════════════════════════


class TestTableParser:
    def test_parse_simple_table(self):
        from dartlab.gather.listing import _TableParser

        parser = _TableParser()
        html = "<table><tr><th>종목코드</th><th>회사명</th></tr><tr><td>005930</td><td>삼성전자</td></tr></table>"
        parser.feed(html)
        assert len(parser._rows) == 2
        assert parser._rows[0] == ["종목코드", "회사명"]
        assert parser._rows[1] == ["005930", "삼성전자"]

    def test_parse_empty_table(self):
        from dartlab.gather.listing import _TableParser

        parser = _TableParser()
        parser.feed("<table></table>")
        assert len(parser._rows) == 0

    def test_parse_no_table(self):
        from dartlab.gather.listing import _TableParser

        parser = _TableParser()
        parser.feed("<div>No table here</div>")
        assert len(parser._rows) == 0


# ══════════════════════════════════════
# 8. _fetchKind (mocked HTTP)
# ══════════════════════════════════════


class TestFetchKind:
    def test_returns_empty_on_timeout(self):
        import httpx

        from dartlab.gather.listing import _fetchKind

        with patch("dartlab.gather.listing.httpx.post", side_effect=httpx.TimeoutException("timeout")):
            df = _fetchKind()
            assert isinstance(df, pl.DataFrame)
            assert df.height == 0
            assert "종목코드" in df.columns

    def test_returns_empty_on_connect_error(self):
        import httpx

        from dartlab.gather.listing import _fetchKind

        with patch("dartlab.gather.listing.httpx.post", side_effect=httpx.ConnectError("refused")):
            df = _fetchKind()
            assert isinstance(df, pl.DataFrame)
            assert df.height == 0

    def test_parses_valid_html(self):
        from dartlab.gather.listing import _fetchKind

        html = "<table><tr><th>회사명</th><th>종목코드</th></tr><tr><td>테스트</td><td>123456</td></tr></table>"
        mock_response = MagicMock()
        mock_response.content = html.encode("euc-kr")

        with patch("dartlab.gather.listing.httpx.post", return_value=mock_response):
            df = _fetchKind()
            assert isinstance(df, pl.DataFrame)
            if df.height > 0:
                assert "종목코드" in df.columns


# ══════════════════════════════════════
# 9. _getSearchCache
# ══════════════════════════════════════


class TestSearchCache:
    def test_cache_populated(self):
        from dartlab.gather.listing import _getSearchCache

        cache = _getSearchCache()
        assert "names" in cache
        assert "names_lower" in cache
        assert "names_chosung" in cache
        assert len(cache["names"]) == 6

    def test_cache_reused(self):
        from dartlab.gather.listing import _getSearchCache

        cache1 = _getSearchCache()
        cache2 = _getSearchCache()
        assert cache1 is cache2
