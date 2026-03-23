"""Company live filing methods tests."""

from __future__ import annotations

import polars as pl
import pytest

pytestmark = pytest.mark.unit


class TestDartCompanyLiveFilings:
    def test_live_filings_normalizes_open_dart_rows(self, monkeypatch):
        from dartlab.engines.company.dart.company import Company as DartCompany

        class FakeOpenDart:
            def filings(self, corp, start, end, *, final=False):
                assert corp == "005930"
                assert start == "2024-03-01"
                assert end == "2024-03-07"
                assert final is True
                return pl.DataFrame(
                    {
                        "corp_cls": ["Y", "Y"],
                        "corp_name": ["삼성전자", "삼성전자"],
                        "stock_code": ["005930", "005930"],
                        "report_nm": ["사업보고서", "단일판매공급계약체결"],
                        "rcept_no": ["20240305000001", "20240307000002"],
                        "rcept_dt": ["20240305", "20240307"],
                        "flr_nm": ["삼성전자", "삼성전자"],
                    }
                )

        monkeypatch.setattr("dartlab.engines.company.dart.openapi.dart.OpenDart", FakeOpenDart)

        company = DartCompany.__new__(DartCompany)
        company.stockCode = "005930"
        company.corpName = "삼성전자"
        company._cache = {}

        result = company.liveFilings(
            start="2024-03-01",
            end="2024-03-07",
            keyword="공급계약",
            limit=10,
            finalOnly=True,
        )

        assert result.height == 1
        assert result.item(0, "docId") == "20240307000002"
        assert result.item(0, "market") == "KR"
        assert "rcpNo=20240307000002" in result.item(0, "viewerUrl")

    def test_read_filing_accepts_viewer_url(self, monkeypatch):
        from dartlab.engines.company.dart.company import Company as DartCompany

        class FakeOpenDart:
            def documentText(self, rceptNo):
                assert rceptNo == "20240312000736"
                return "<html><body>단일판매공급계약 본문</body></html>"

        monkeypatch.setattr("dartlab.engines.company.dart.openapi.dart.OpenDart", FakeOpenDart)

        company = DartCompany.__new__(DartCompany)
        company.stockCode = "005930"
        company.corpName = "삼성전자"
        company._cache = {}

        result = company.readFiling(
            "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=20240312000736",
            maxChars=20,
        )

        assert result["docId"] == "20240312000736"
        assert result["truncated"] is True
        assert "단일판매공급계약" in result["text"]


class TestEdgarCompanyLiveFilings:
    def test_html_to_text_removes_hidden_inline_xbrl_noise(self):
        from dartlab.engines.company.edgar.docs.fetch import _htmlToText

        html = """
        <html>
          <body>
            <ix:header>hidden header</ix:header>
            <div style="display:none">secret</div>
            <p>FORM 10-K</p>
            <ix:nonnumeric>Apple Inc.</ix:nonnumeric>
            <table><tr><th>Item</th><th>Value</th></tr><tr><td>A</td><td>1</td></tr></table>
          </body>
        </html>
        """

        text = _htmlToText(html)

        assert "FORM 10-K" in text
        assert "Apple Inc." in text
        assert "hidden header" not in text
        assert "secret" not in text
        assert "| Item | Value |" in text

    def test_live_filings_normalizes_edgar_rows(self, monkeypatch):
        from dartlab.engines.company.edgar.company import Company as EdgarCompany

        class FakeOpenEdgarCompany:
            def filings(self, *, forms=None, since=None, until=None):
                assert forms == ["10-Q"]
                assert since == "2024-04-01"
                assert until == "2024-04-30"
                return pl.DataFrame(
                    {
                        "ticker": ["AAPL"],
                        "cik": ["0000320193"],
                        "title": ["Apple Inc."],
                        "form": ["10-Q"],
                        "filing_date": ["2024-04-30"],
                        "report_date": ["2024-03-30"],
                        "accession_no": ["0000320193-24-000123"],
                        "primary_document": ["aapl-20240330x10q.htm"],
                        "primary_doc_description": ["Quarterly report"],
                        "filing_url": [
                            "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240330x10q.htm"
                        ],
                        "filing_index_url": [
                            "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/index.json"
                        ],
                        "year": ["2024"],
                    }
                )

        class FakeOpenEdgar:
            def __call__(self, ticker):
                assert ticker == "AAPL"
                return FakeOpenEdgarCompany()

        monkeypatch.setattr("dartlab.engines.company.edgar.openapi.edgar.OpenEdgar", FakeOpenEdgar)

        company = EdgarCompany.__new__(EdgarCompany)
        company.ticker = "AAPL"
        company.cik = "0000320193"
        company.corpName = "Apple Inc."
        company._cache = {}

        result = company.liveFilings(
            start="2024-04-01",
            end="2024-04-30",
            forms=["10-Q"],
            keyword="quarterly",
            limit=5,
        )

        assert result.height == 1
        assert result.item(0, "docId") == "0000320193-24-000123"
        assert result.item(0, "market") == "US"
        assert result.item(0, "docUrl").endswith(".htm")

    def test_read_filing_uses_url_and_text_fallback(self, monkeypatch):
        from dartlab.engines.company.edgar.company import Company as EdgarCompany

        monkeypatch.setattr(
            "dartlab.engines.company.edgar.docs.fetch._downloadFilingSource",
            lambda filing: "<html><body>Quarterly filing body</body></html>",
        )
        monkeypatch.setattr(
            "dartlab.engines.company.edgar.docs.fetch._htmlToText",
            lambda raw: "Quarterly filing body",
        )

        company = EdgarCompany.__new__(EdgarCompany)
        company.ticker = "AAPL"
        company.cik = "0000320193"
        company.corpName = "Apple Inc."
        company._cache = {}

        result = company.readFiling(
            {
                "docId": "0000320193-24-000123",
                "docUrl": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240330x10q.htm",
                "title": "Apple Inc.",
            },
            maxChars=200,
        )

        assert result["docId"] == "0000320193-24-000123"
        assert result["docUrl"].endswith(".htm")
        assert result["text"] == "Quarterly filing body"
