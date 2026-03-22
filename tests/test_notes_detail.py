"""finance.notesDetail 테스트."""

import polars as pl
import pytest

from tests.conftest import SAMSUNG, requires_samsung


@requires_samsung
class TestNotesDetail:
    def test_inventory(self):
        from dartlab.engines.company.dart.docs.finance.notesDetail import notesDetail

        r = notesDetail(SAMSUNG, "재고자산")
        assert r is not None
        assert r.corpName == "삼성전자"
        assert r.keyword == "재고자산"
        assert r.nYears >= 1

    def test_table_df(self):
        from dartlab.engines.company.dart.docs.finance.notesDetail import notesDetail

        r = notesDetail(SAMSUNG, "재고자산")
        assert r is not None
        assert r.tableDf is not None
        assert isinstance(r.tableDf, pl.DataFrame)
        assert "항목" in r.tableDf.columns
        assert len(r.tableDf) >= 1

    @pytest.mark.parametrize(
        "keyword",
        [
            "재고자산",
            "주당이익",
            "충당부채",
            "차입금",
            "매출채권",
            "무형자산",
        ],
    )
    def test_keywords(self, keyword):
        from dartlab.engines.company.dart.docs.finance.notesDetail import notesDetail

        r = notesDetail(SAMSUNG, keyword)
        assert r is not None
        assert r.keyword == keyword
        assert r.nYears >= 1

    def test_invalid_keyword_returns_none(self):
        from dartlab.engines.company.dart.docs.finance.notesDetail import notesDetail

        r = notesDetail(SAMSUNG, "존재하지않는키워드")
        assert r is None

    def test_notes_keywords_dict(self):
        from dartlab.engines.company.dart.docs.finance.notesDetail import NOTES_KEYWORDS

        assert len(NOTES_KEYWORDS) == 23
        assert "재고자산" in NOTES_KEYWORDS
        assert "특수관계자" in NOTES_KEYWORDS
        assert "우발부채" in NOTES_KEYWORDS

    def test_company_notes_access(self):
        from dartlab import Company

        c = Company(SAMSUNG)
        df = c.notes["차입금"]
        assert df is not None
        assert isinstance(df, pl.DataFrame)
