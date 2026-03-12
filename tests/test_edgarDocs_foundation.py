"""EDGAR docs 저장·로더 기반 테스트."""

from pathlib import Path

import polars as pl

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FIXTURE_EDGAR_DOCS = FIXTURE_DIR / "AAPL.edgarDocs.parquet"


def test_edgarDocs_fixture_loads():
    df = pl.read_parquet(FIXTURE_EDGAR_DOCS)

    assert df.height > 0
    assert "section_title" in df.columns
    assert "section_content" in df.columns


def test_edgarDocs_has_minimum_common_schema(tmp_path, monkeypatch):
    from dartlab.core.dataLoader import loadData

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    fixture.write_parquet(docsDir / "AAPL.parquet")

    from dartlab import config
    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    df = loadData("AAPL", category="edgarDocs")

    required = [
        "year",
        "filing_date",
        "report_type",
        "period_key",
        "section_order",
        "section_title",
        "section_content",
        "source",
        "entity_id",
        "doc_id",
        "doc_date",
        "doc_url",
    ]
    for col in required:
        assert col in df.columns, f"missing column: {col}"


def test_edgarDocs_preserves_edgar_specific_columns():
    df = pl.read_parquet(FIXTURE_EDGAR_DOCS)

    required = [
        "cik",
        "company_name",
        "ticker",
        "accession_no",
        "form_type",
        "filing_url",
    ]
    for col in required:
        assert col in df.columns, f"missing column: {col}"


def test_edgarDocs_common_view_values(tmp_path, monkeypatch):
    from dartlab.core.dataLoader import loadData

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    fixture.write_parquet(docsDir / "AAPL.parquet")

    from dartlab import config
    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    df = loadData("AAPL", category="edgarDocs")
    row = df.row(0, named=True)

    assert row["source"] == "edgar"
    assert row["entity_id"] == "AAPL"
    assert row["doc_id"] == row["accession_no"]
    assert row["doc_date"] == row["filing_date"]
    assert row["doc_url"] == row["filing_url"]


def test_extractCorpName_supports_company_name():
    from dartlab.core.dataLoader import extractCorpName

    df = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    assert extractCorpName(df) == "Apple Inc."


def test_buildIndex_supports_accession_no(tmp_path, monkeypatch):
    from dartlab import config
    from dartlab.core.dataLoader import buildIndex

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    fixture.write_parquet(docsDir / "AAPL.parquet")

    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    indexDf = buildIndex(category="edgarDocs")

    assert indexDf.height == 1

    row = indexDf.row(0, named=True)
    assert row["stockCode"] == "AAPL"
    assert row["corpName"] == "Apple Inc."
    assert row["nDocs"] == fixture["accession_no"].n_unique()


def test_data_releases_has_edgarDocs():
    from dartlab.core.dataConfig import DATA_RELEASES

    assert "edgarDocs" in DATA_RELEASES
    assert DATA_RELEASES["edgarDocs"]["dir"] == "edgar/docs"
    assert DATA_RELEASES["edgarDocs"]["tag"] == "data-edgar-docs"


def test_downloadAll_blocks_edgarDocs_bulk_download():
    import pytest

    from dartlab.core.dataLoader import downloadAll

    with pytest.raises(ValueError, match="edgarDocs"):
        downloadAll("edgarDocs")


def test_download_skips_edgarDocs(monkeypatch, capsys, tmp_path):
    from dartlab import config
    from dartlab.core import dataLoader

    calls: list[tuple[str, str]] = []

    def fakeDownload(stockCode: str, dest: Path, category: str = "docs") -> None:
        calls.append((stockCode, category))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("stub", encoding="utf-8")

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr(dataLoader, "_download", fakeDownload)

    dataLoader.download("AAPL")

    out = capsys.readouterr().out
    assert all(category != "edgarDocs" for _, category in calls)
    assert "SEC EDGAR 공시 문서 데이터" not in out


def test_loadData_falls_back_to_edgar_api(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadData

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    dataRoot = tmp_path / "data"
    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    def fakeDownload(stockCode: str, dest: Path, category: str = "docs") -> None:
        raise OSError("release missing")

    def fakeFetchEdgarDocs(ticker: str, outPath: Path, *, sinceYear: int = 2009) -> Path:
        assert ticker == "AAPL"
        assert sinceYear == 2009
        outPath.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_parquet(outPath)
        return outPath

    monkeypatch.setattr("dartlab.core.dataLoader._download", fakeDownload)
    monkeypatch.setattr("dartlab.engines.edgar.docs.fetch.fetchEdgarDocs", fakeFetchEdgarDocs)

    df = loadData("AAPL", category="edgarDocs")

    assert df.height == fixture.height
    assert "source" in df.columns
    assert df["source"][0] == "edgar"


def test_loadData_edgarDocs_sinceYear_override(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadData

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    dataRoot = tmp_path / "data"
    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    def fakeDownload(stockCode: str, dest: Path, category: str = "docs") -> None:
        raise OSError("release missing")

    called: dict[str, int] = {}

    def fakeFetchEdgarDocs(ticker: str, outPath: Path, *, sinceYear: int = 2009, maxFilings=None) -> Path:
        called["sinceYear"] = sinceYear
        outPath.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_parquet(outPath)
        return outPath

    monkeypatch.setattr("dartlab.core.dataLoader._download", fakeDownload)
    monkeypatch.setattr("dartlab.engines.edgar.docs.fetch.fetchEdgarDocs", fakeFetchEdgarDocs)

    loadData("AAPL", category="edgarDocs", sinceYear=2015)

    assert called["sinceYear"] == 2015


def test_selectEdgarReport_annual_and_quarter():
    from dartlab.core.dataLoader import _normalizeLoadedFrame
    from dartlab.core.reportSelector import selectEdgarReport

    df = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    df = _normalizeLoadedFrame(df, "edgarDocs")

    annual = selectEdgarReport(df, "2024")
    q1 = selectEdgarReport(df, "2024Q1")
    q2 = selectEdgarReport(df, "2024Q2")
    q3 = selectEdgarReport(df, "2024Q3")

    assert annual is not None
    assert q1 is not None
    assert q2 is not None
    assert q3 is not None
    assert annual["form_type"].unique().to_list() == ["10-K"]
    assert q1["form_type"].unique().to_list() == ["10-Q"]
    assert q2["form_type"].unique().to_list() == ["10-Q"]
    assert q3["form_type"].unique().to_list() == ["10-Q"]
    assert annual["period_key"].unique().to_list() == ["2024"]
    assert q1["period_key"].unique().to_list() == ["2024Q1"]


def test_htmlToText_preserves_table_markdown():
    from dartlab.engines.edgar.docs.fetch import _htmlToText

    html = """
    <html><body>
    <table>
      <tr><td></td><td></td></tr>
      <tr><th>Item</th><th>Amount</th></tr>
      <tr><td>Net sales</td><td>$ 10,167</td></tr>
    </table>
    </body></html>
    """

    text = _htmlToText(html)

    assert "| Item | Amount |" in text
    assert "| Net sales | $ 10,167 |" in text
    assert "| --- | --- |" in text


def test_htmlToText_table_cells_keep_word_boundaries():
    from dartlab.engines.edgar.docs.fetch import _htmlToText

    html = """
    <html><body>
    <table>
      <tr><th><span>Three Months</span><span> Ended</span></th><th>Value</th></tr>
      <tr><td><span>Research and</span><span> development</span></td><td>315</td></tr>
    </table>
    </body></html>
    """

    text = _htmlToText(html)

    assert "Three Months Ended" in text
    assert "Research and development" in text


def test_downloadListedEdgarDocs_uses_exchange_listed_universe(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.docs.fetch import downloadListedEdgarDocs

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))

    universe = pl.DataFrame({
        "ticker": ["AAPL", "MSFT", "OTCX"],
        "cik": ["0000320193", "0000789019", "0000123456"],
        "title": ["Apple Inc.", "Microsoft Corp.", "OTC Example"],
        "exchange": ["Nasdaq", "NYSE", "OTC"],
        "is_exchange_listed": [True, True, False],
        "is_otc": [False, False, True],
    })

    fetched: list[tuple[str, int]] = []

    def fakeLoadEdgarListedUniverse(*, forceUpdate: bool = False) -> pl.DataFrame:
        return universe

    def fakeFetchEdgarDocs(ticker: str, outPath: Path, *, sinceYear: int = 2009, maxFilings=None) -> Path:
        fetched.append((ticker, sinceYear))
        outPath.parent.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({"ticker": [ticker]}).write_parquet(outPath)
        return outPath

    monkeypatch.setattr("dartlab.core.dataLoader.loadEdgarListedUniverse", fakeLoadEdgarListedUniverse)
    monkeypatch.setattr("dartlab.engines.edgar.docs.fetch.fetchEdgarDocs", fakeFetchEdgarDocs)

    result = downloadListedEdgarDocs(limit=10, sinceYear=2009, batchSize=0, cooldownSeconds=0)

    assert fetched == [("AAPL", 2009), ("MSFT", 2009)]
    assert result.filter(pl.col("status") == "downloaded").height == 2


def test_edgar_sections_pipeline_builds_topic_period_view(tmp_path, monkeypatch):
    from dartlab import config
    from dartlab.engines.edgar.docs.sections import sections, sortPeriods

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)

    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    fixture.write_parquet(docsDir / "AAPL.parquet")
    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    df = sections("AAPL")

    assert df is not None
    assert "topic" in df.columns
    assert "2024" in df.columns
    assert "2024Q1" in df.columns
    assert "10-K::item1Business" in df["topic"].to_list()
    assert df.columns[1:] == sortPeriods(df.columns[1:])


def test_edgar_sections_pipeline_supports_form_native_structured_topics(tmp_path, monkeypatch):
    import importlib

    from dartlab.engines.edgar.docs.sections import sections
    pipelineModule = importlib.import_module("dartlab.engines.edgar.docs.sections.pipeline")

    df = pl.DataFrame({
        "cik": ["0001", "0001", "0001", "0001"],
        "company_name": ["Test Corp."] * 4,
        "ticker": ["TEST"] * 4,
        "year": ["2024", "2024", "2024", "2024"],
        "filing_date": ["2024-11-01", "2024-05-01", "2024-05-01", "2024-05-01"],
        "period_end": ["2024-09-28", "2024-03-30", "2024-03-30", "2024-03-30"],
        "accession_no": ["annual-1", "q1-1", "q1-1", "q1-1"],
        "form_type": ["10-K", "10-Q", "10-Q", "10-Q"],
        "report_type": ["10-K (2024.09)", "10-Q (2024.03)", "10-Q (2024.03)", "10-Q (2024.03)"],
        "period_key": ["2024", "2024Q1", "2024Q1", "2024Q1"],
        "section_order": [0, 0, 1, 2],
        "section_title": [
            "Item 1. Business",
            "Part I - Item 1. Financial Statements",
            "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations",
            "Part II - Item 1A. Risk Factors",
        ],
        "filing_url": ["u1", "u2", "u2", "u2"],
        "section_content": ["Annual business", "Quarter statements", "Quarter mdna", "Quarter risks"],
    })
    monkeypatch.setattr(pipelineModule, "loadData", lambda stockCode, category="edgarDocs", sinceYear=None: df)

    result = sections("TEST")

    assert result is not None
    assert "10-Q::partIItem1FinancialStatements" in result["topic"].to_list()
    assert "10-Q::partIItem2Mdna" in result["topic"].to_list()
    assert "10-Q::partIIItem1ARiskFactors" in result["topic"].to_list()


def test_edgar_sections_artifacts_and_views():
    from dartlab.engines.edgar.docs.sections import (
        buildMarkdownWide,
        fallbackTopic,
        loadCanonicalRows,
        loadCoverageSnapshot,
        loadTopicDrafts,
        sortPeriods,
        topicNamespace,
    )

    assert sortPeriods(["2024", "2024Q1", "2023", "2024Q3"]) == ["2024", "2024Q3", "2024Q1", "2023"]
    assert topicNamespace("10-K", "item1Business") == "10-K::item1Business"
    assert fallbackTopic("10-Q") == "10-Q::fullDocument"
    assert loadCanonicalRows() is not None
    assert loadCoverageSnapshot() is not None
    assert loadTopicDrafts() is not None

    wide = buildMarkdownWide(pl.DataFrame({"topic": ["10-K::item1Business"], "2024": ["Text"]}))
    assert "| topic | 2024 |" in wide
    assert "| 10-K::item1Business | Text |" in wide


def test_splitItems_splits_quarterly_items_with_inline_titles():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
| Part I | |
| Item 1. | Financial Statements |
PART I  —  FINANCIAL INFORMATION
Item 1.    Financial Statements
Quarterly statements body
Item 2.    Management's Discussion and Analysis of Financial Condition and Results of Operations
MD&A body
Item 3.    Quantitative and Qualitative Disclosures About Market Risk
Risk body
Item 4.    Controls and Procedures
Controls body
PART II  —  OTHER INFORMATION
Item 1.    Legal Proceedings
Legal body
Item 1A.    Risk Factors
Risk factors body
Item 6.    Exhibits
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    assert len(items) >= 7
    assert items[0]["title"] == "Part I - Item 1. Financial Statements"
    assert items[1]["title"] == "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
    assert any(item["title"] == "Part II - Item 1A. Risk Factors" for item in items)


def test_splitItems_splits_quarterly_items_with_standalone_headers():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
PART I. FINANCIAL INFORMATION
Item 1.
| Item 1. | Financial Statements | 3 |
Financial statements body
Item 2.
| Item 2. | Management's Discussion and Analysis of Financial Condition and Results of Operations | 21 |
MD&A body
Item 3.
| Item 3. | Quantitative and Qualitative Disclosures About Market Risk | 32 |
Risk body
PART II. OTHER INFORMATION
Item 1.
| Item 1. | Legal Proceedings | 34 |
Legal body
Item 1A.
| Item 1A. | Risk Factors | 34 |
Risk factors body
Item 6.
| Item 6. | Exhibits | 46 |
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    titles = [item["title"] for item in items]
    assert "Part I - Item 1. Financial Statements" in titles
    assert "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations" in titles
    assert "Part II - Item 1. Legal Proceedings" in titles
    assert "Part II - Item 1A. Risk Factors" in titles


def test_parseEdgarPeriodKey_and_extractEdgarReportYear():
    from dartlab.core.reportSelector import extractEdgarReportYear, parseEdgarPeriodKey

    assert parseEdgarPeriodKey("10-K (2024.09)") == "2024"
    assert parseEdgarPeriodKey("20-F (2024.12)") == "2024"
    assert parseEdgarPeriodKey("10-Q (2024.03)") == "2024Q1"
    assert parseEdgarPeriodKey("10-Q (2024.06)") == "2024Q2"
    assert parseEdgarPeriodKey("10-Q (2024.09)") == "2024Q3"
    assert parseEdgarPeriodKey("10-Q (2024.12)") is None
    assert extractEdgarReportYear("10-K (2024.09)") == 2024
    assert extractEdgarReportYear("invalid") is None


def test_updateEdgarListedUniverse_writes_cache(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadEdgarListedUniverse, updateEdgarListedUniverse

    payload = {
        "data": [
            [320193, "Apple Inc.", "AAPL", "Nasdaq"],
            [19617, "JPMorgan Chase & Co.", "JPM", "NYSE"],
            [987654, "Cboe Example", "CBOX", "CBOE"],
            [123456, "OTC Example", "OTCX", "OTC"],
        ]
    }

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr("dartlab.core.dataLoader._fetchJson", lambda url: payload)

    path = updateEdgarListedUniverse(force=True)
    df = loadEdgarListedUniverse()

    assert path.exists()
    assert df.height == 4
    assert "exchange" in df.columns
    assert "is_exchange_listed" in df.columns
    assert df.filter(pl.col("ticker") == "AAPL")["is_exchange_listed"][0] is True
    assert df.filter(pl.col("ticker") == "CBOX")["is_exchange_listed"][0] is True
    assert df.filter(pl.col("ticker") == "OTCX")["is_otc"][0] is True


def test_fetchJson_uses_sec_user_agent(monkeypatch):
    import json

    from dartlab.core.dataLoader import _fetchJson

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"ok": True}).encode("utf-8")

    def fakeUrlopen(request):
        assert request.headers["User-agent"] == "DartLab eddmpython@gmail.com"
        return FakeResponse()

    monkeypatch.setattr("dartlab.core.dataLoader.urlopen", fakeUrlopen)

    payload = _fetchJson("https://example.com/test.json")

    assert payload == {"ok": True}
