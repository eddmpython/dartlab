from pathlib import Path

import polars as pl
import pytest


def _ticker_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "ticker": ["AAPL"],
            "cik": ["0000320193"],
            "title": ["Apple Inc."],
            "exchange": ["Nasdaq"],
            "is_exchange_listed": [True],
            "is_otc": [False],
        }
    )


def _submissions_payload() -> dict:
    return {
        "cik": "0000320193",
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q"],
                "filingDate": ["2024-11-01", "2025-02-01"],
                "reportDate": ["2024-09-28", "2024-12-28"],
                "acceptanceDateTime": ["20241101120000", "20250201120000"],
                "accessionNumber": ["0000320193-24-000111", "0000320193-25-000222"],
                "primaryDocument": ["aapl-20240928.htm", "aapl-20241228.htm"],
                "primaryDocDescription": ["10-K", "10-Q"],
            },
            "files": [{"name": "CIK0000320193-submissions-001.json", "filingTo": "2025-12-31"}],
        },
    }


def _extra_submissions_payload() -> dict:
    return {
        "form": ["20-F"],
        "filingDate": ["2023-03-15"],
        "reportDate": ["2022-12-31"],
        "acceptanceDateTime": ["20230315120000"],
        "accessionNumber": ["0000320193-23-000333"],
        "primaryDocument": ["aapl-20f.htm"],
        "primaryDocDescription": ["20-F"],
    }


def _companyfacts_payload() -> dict:
    return {
        "cik": "0000320193",
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Assets": {
                    "label": "Assets",
                    "units": {
                        "USD": [
                            {
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-11-01",
                                "end": "2024-09-28",
                                "val": 364980000000,
                                "accn": "0000320193-24-000111",
                            }
                        ]
                    },
                }
            }
        },
    }


def test_root_exports_openapi_names():
    from dartlab import Dart, OpenDart, OpenEdgar

    assert OpenDart is Dart
    assert OpenEdgar is not None


def test_resolveIssuer_supports_ticker_lower_and_cik(monkeypatch):
    from dartlab.engines.edgar.openapi.identity import resolveIssuer

    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())

    byTicker = resolveIssuer("AAPL")
    byLower = resolveIssuer("aapl")
    byCik = resolveIssuer("0000320193")

    assert byTicker["ticker"] == "AAPL"
    assert byLower["cik"] == "0000320193"
    assert byCik["title"] == "Apple Inc."

    with pytest.raises(ValueError, match="CIK"):
        resolveIssuer("ZZZZ")


def test_openedgar_raw_wrappers_and_filings(monkeypatch):
    from dartlab import OpenEdgar

    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())

    def fakeGetJson(self, url: str):
        if url.endswith("/submissions/CIK0000320193.json"):
            return _submissions_payload()
        if url.endswith("/submissions/CIK0000320193-submissions-001.json"):
            return _extra_submissions_payload()
        if url.endswith("/api/xbrl/companyfacts/CIK0000320193.json"):
            return _companyfacts_payload()
        if url.endswith("/api/xbrl/companyconcept/CIK0000320193/us-gaap/Assets.json"):
            return {"cik": "0000320193", "taxonomy": "us-gaap", "tag": "Assets"}
        if url.endswith("/api/xbrl/frames/us-gaap/Assets/USD/CY2024Q4I.json"):
            return {"taxonomy": "us-gaap", "tag": "Assets", "unit": "USD", "ccp": "CY2024Q4I"}
        raise AssertionError(url)

    monkeypatch.setattr("dartlab.engines.edgar.openapi.client.EdgarClient.getJson", fakeGetJson)

    e = OpenEdgar()
    raw = e.submissionsJson("aapl")
    filings = e.filings("AAPL", forms=["10-K", "10-Q"], since="2024", until="2025")

    assert "filings" in raw
    assert filings["form"].to_list() == ["10-K", "10-Q"]
    assert filings["ticker"].unique().to_list() == ["AAPL"]
    assert "0000320193-23-000333" not in filings["accession_no"].to_list()

    assert e.companyFactsJson("AAPL")["entityName"] == "Apple Inc."
    assert e.companyConceptJson("AAPL", "us-gaap", "Assets")["tag"] == "Assets"
    assert e.frameJson("us-gaap", "Assets", "USD", "CY2024Q4I")["ccp"] == "CY2024Q4I"


def test_openedgar_company_proxy(monkeypatch):
    from dartlab import OpenEdgar
    from dartlab.engines.edgar.openapi.edgar import OpenEdgarCompany

    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr(
        "dartlab.engines.edgar.openapi.client.EdgarClient.getJson",
        lambda self, url: _submissions_payload() if "submissions/CIK0000320193.json" in url else _companyfacts_payload(),
    )

    company = OpenEdgar()("AAPL")

    assert isinstance(company, OpenEdgarCompany)
    assert company.info()["ticker"] == "AAPL"
    assert company.submissionsJson()["cik"] == "0000320193"


def test_saveDocs_writes_sections_compatible_parquet(monkeypatch, tmp_path):
    from dartlab import OpenEdgar, config
    from dartlab.engines.edgar.docs.sections.pipeline import sections

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadEdgarListedUniverse", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadTickers", lambda *args, **kwargs: _ticker_df())

    def fakeFetchEdgarDocs(ticker: str, outPath: Path, *, sinceYear: int = 2009, **kwargs) -> Path:
        df = pl.DataFrame(
            {
                "cik": ["0000320193"],
                "company_name": ["Apple Inc."],
                "ticker": [ticker],
                "year": ["2024"],
                "filing_date": ["2024-11-01"],
                "period_end": ["2024-09-28"],
                "accession_no": ["0000320193-24-000111"],
                "form_type": ["10-K"],
                "report_type": ["10-K (2024.09)"],
                "period_key": ["2024"],
                "section_order": [0],
                "section_title": ["Item 1. Business"],
                "filing_url": ["https://www.sec.gov/Archives/edgar/data/0000320193/000032019324000111/aapl-20240928.htm"],
                "section_content": ["Apple business overview"],
            }
        )
        outPath.parent.mkdir(parents=True, exist_ok=True)
        df.write_parquet(outPath)
        return outPath

    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.fetchEdgarDocs", fakeFetchEdgarDocs)

    company = OpenEdgar()("AAPL")
    path = company.saveDocs()

    assert path.exists()
    sec = sections("AAPL")
    assert sec is not None
    assert "10-K::item1Business" in sec["topic"].to_list()


def test_saveFinance_writes_companyfacts_parquet_compatible_with_pivot(monkeypatch, tmp_path):
    from dartlab import OpenEdgar, config
    from dartlab.engines.edgar.finance.pivot import buildTimeseries

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadEdgarListedUniverse", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadTickers", lambda *args, **kwargs: _ticker_df())

    def fakeGetJson(self, url: str):
        if url.endswith("/api/xbrl/companyfacts/CIK0000320193.json"):
            return _companyfacts_payload()
        raise AssertionError(url)

    monkeypatch.setattr("dartlab.engines.edgar.openapi.client.EdgarClient.getJson", fakeGetJson)

    company = OpenEdgar()("AAPL")
    path = company.saveFinance()

    assert path.exists()

    result = buildTimeseries("0000320193", edgarDir=path.parent)
    assert result is not None
    series, periods = result
    assert periods == ["2024-Q4"]
    assert series["BS"]["total_assets"] == [364980000000.0]


def test_companyFactsToRows_matches_existing_finance_schema():
    from dartlab.engines.edgar.openapi.facts import EDGAR_COMPANYFACTS_SCHEMA, companyFactsToRows

    df = companyFactsToRows(_companyfacts_payload())

    assert df.columns == [
        "cik",
        "entityName",
        "namespace",
        "tag",
        "label",
        "unit",
        "val",
        "fy",
        "fp",
        "form",
        "filed",
        "frame",
        "start",
        "end",
        "accn",
    ]
    assert df.schema == EDGAR_COMPANYFACTS_SCHEMA
    assert df.schema["fy"] == pl.Int32
    assert df.schema["filed"] == pl.Date
    assert df.schema["end"] == pl.Date


def test_saveDocs_schema_mismatch_preserves_existing_file(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.openapi.saver import saveDocs

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)
    existingPath = docsDir / "AAPL.parquet"
    original = pl.DataFrame(
        {
            "cik": ["0000320193"],
            "company_name": ["Apple Inc."],
            "ticker": ["AAPL"],
            "year": ["2024"],
            "filing_date": ["2024-11-01"],
            "period_end": ["2024-09-28"],
            "accession_no": ["old-doc"],
            "form_type": ["10-K"],
            "report_type": ["10-K (2024.09)"],
            "period_key": ["2024"],
            "section_order": [0],
            "section_title": ["Item 1. Business"],
            "filing_url": ["https://example.com/old.htm"],
            "section_content": ["old content"],
        }
    )
    original.write_parquet(existingPath)

    monkeypatch.setattr(config, "dataDir", str(dataRoot))
    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadEdgarListedUniverse", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadTickers", lambda *args, **kwargs: _ticker_df())

    def badFetch(ticker: str, outPath: Path, *, sinceYear: int = 2009, **kwargs) -> Path:
        pl.DataFrame({"ticker": [ticker], "bad": ["value"]}).write_parquet(outPath)
        return outPath

    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.fetchEdgarDocs", badFetch)

    with pytest.raises(ValueError, match="schema mismatch"):
        saveDocs("AAPL")

    current = pl.read_parquet(existingPath)
    assert current["accession_no"].to_list() == ["old-doc"]


def test_saveFinance_smoke_failure_preserves_existing_file(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.openapi.saver import saveFinance

    dataRoot = tmp_path / "data"
    financeDir = dataRoot / "edgar" / "finance"
    financeDir.mkdir(parents=True)
    existingPath = financeDir / "0000320193.parquet"
    original = pl.DataFrame(
        {
            "cik": ["0000320193"],
            "entityName": ["Apple Inc."],
            "namespace": ["us-gaap"],
            "tag": ["Assets"],
            "label": ["Assets"],
            "unit": ["USD"],
            "val": [1.0],
            "fy": [2023],
            "fp": ["FY"],
            "form": ["10-K"],
            "filed": [None],
            "frame": [None],
            "start": [None],
            "end": [None],
            "accn": ["old-fin"],
        },
        schema={
            "cik": pl.Utf8,
            "entityName": pl.Utf8,
            "namespace": pl.Utf8,
            "tag": pl.Utf8,
            "label": pl.Utf8,
            "unit": pl.Utf8,
            "val": pl.Float64,
            "fy": pl.Int32,
            "fp": pl.Utf8,
            "form": pl.Utf8,
            "filed": pl.Date,
            "frame": pl.Utf8,
            "start": pl.Date,
            "end": pl.Date,
            "accn": pl.Utf8,
        },
    )
    original.write_parquet(existingPath)

    monkeypatch.setattr(config, "dataDir", str(dataRoot))
    monkeypatch.setattr("dartlab.engines.edgar.openapi.identity.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadEdgarListedUniverse", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadTickers", lambda *args, **kwargs: _ticker_df())
    monkeypatch.setattr(
        "dartlab.engines.edgar.openapi.client.EdgarClient.getJson",
        lambda self, url: _companyfacts_payload(),
    )
    monkeypatch.setattr("dartlab.engines.edgar.finance.pivot.buildTimeseries", lambda *args, **kwargs: None)

    with pytest.raises(ValueError, match="consumer smoke check failed"):
        saveFinance("0000320193")

    current = pl.read_parquet(existingPath)
    assert current["accn"].to_list() == ["old-fin"]


def test_api_saved_data_is_immediately_usable_by_company(monkeypatch, tmp_path):
    from dartlab import Company, OpenEdgar, config
    from dartlab.engines.edgar.openapi.saver import verifyOpenEdgarSaveCompatibility

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))

    e = OpenEdgar()
    aapl = e("AAPL")
    aapl.saveFinance()
    aapl.saveDocs(sinceYear=2024)

    verified = verifyOpenEdgarSaveCompatibility("AAPL")
    company = Company("AAPL")

    assert verified["corpName"] == "Apple Inc."
    assert verified["hasTimeseries"] is True
    assert verified["financeBsShape"] is not None
    assert verified["docsSectionsShape"] is not None
    assert verified["sampleDocTopic"] is not None
    assert verified["sampleDocShowShape"] is not None
    assert verified["sampleDocTrace"]["primarySource"] == "docs"
    assert verified["bsTrace"]["primarySource"] == "finance"
    assert company.trace("10-K::item1Business")["primarySource"] == "docs"
    assert company.finance.BS is not None


def test_company_resolveTickerRow_falls_back_to_listed_universe(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.company import Company

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarListedUniverse",
        lambda *args, **kwargs: _ticker_df(),
    )
    monkeypatch.setattr("dartlab.engines.edgar.finance.pivot.buildTimeseries", lambda *args, **kwargs: None)

    c = Company("AAPL")
    assert c.cik == "0000320193"


def test_ensureIdentityCaches_allows_missing_listed_universe(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.openapi.saver import _ensureIdentityCaches

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))
    monkeypatch.setattr(
        "dartlab.engines.edgar.openapi.saver.loadEdgarListedUniverse",
        lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError("missing listed")),
    )
    monkeypatch.setattr("dartlab.engines.edgar.openapi.saver.loadTickers", lambda *args, **kwargs: _ticker_df())

    _ensureIdentityCaches()
