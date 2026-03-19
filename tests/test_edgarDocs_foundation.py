"""EDGAR docs 저장·로더 기반 테스트."""

import json
from pathlib import Path

import polars as pl
import pytest

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


def test_getLocalEdgarDocsState_reads_latest_from_parquet(tmp_path):
    from dartlab.core.dataLoader import _getLocalEdgarDocsState

    df = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    path = tmp_path / "AAPL.parquet"
    df.write_parquet(path)

    state = _getLocalEdgarDocsState(path)

    assert state is not None
    assert state["latest_filing_date"] == "2026-01-30"
    assert state["latest_accession_no"] == "0000320193-26-000006"


def test_loadData_edgarDocs_local_only_uses_local_file(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadData

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)
    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    path = docsDir / "AAPL.parquet"
    fixture.write_parquet(path)

    monkeypatch.setattr(config, "dataDir", str(dataRoot))

    df = loadData("AAPL", category="edgarDocs", refresh="local_only")
    assert df.height == fixture.height


def test_loadData_edgarDocs_force_check_skips_rebuild_when_fresh(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadData

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)
    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    path = docsDir / "AAPL.parquet"
    fixture.write_parquet(path)

    monkeypatch.setattr(config, "dataDir", str(dataRoot))
    monkeypatch.setattr(
        "dartlab.core.dataLoader._getLatestRegularEdgarFiling",
        lambda stockCode, sinceYear=2009: {
            "ticker": "AAPL",
            "cik": "0000320193",
            "filing_date": "2024-11-01",
            "accession_no": fixture["accession_no"][0],
            "form_type": "10-K",
        },
    )

    rebuilt = {"called": False}
    monkeypatch.setattr(
        "dartlab.core.dataLoader._incrementalUpdateEdgarDocs",
        lambda *args, **kwargs: rebuilt.__setitem__("called", True),
    )

    loadData("AAPL", category="edgarDocs", refresh="force_check")
    assert rebuilt["called"] is False


def test_loadData_edgarDocs_force_check_runs_incremental_when_stale(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.core.dataLoader import loadData

    dataRoot = tmp_path / "data"
    docsDir = dataRoot / "edgar" / "docs"
    docsDir.mkdir(parents=True)
    fixture = pl.read_parquet(FIXTURE_EDGAR_DOCS)
    path = docsDir / "AAPL.parquet"
    fixture.write_parquet(path)

    monkeypatch.setattr(config, "dataDir", str(dataRoot))
    monkeypatch.setattr(
        "dartlab.core.dataLoader._getLatestRegularEdgarFiling",
        lambda stockCode, sinceYear=2009: {
            "ticker": "AAPL",
            "cik": "0000320193",
            "filing_date": "2026-05-01",
            "accession_no": "new-accession",
            "form_type": "10-Q",
        },
    )

    called = {}

    def fakeIncremental(stockCode: str, pathArg: Path, *, sinceYear: int, latestRemote: dict) -> None:
        called["stockCode"] = stockCode
        called["path"] = pathArg
        called["latest"] = latestRemote

    monkeypatch.setattr("dartlab.core.dataLoader._incrementalUpdateEdgarDocs", fakeIncremental)

    loadData("AAPL", category="edgarDocs", refresh="force_check")
    assert called["stockCode"] == "AAPL"
    assert called["latest"]["accession_no"] == "new-accession"


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

    universe = pl.DataFrame(
        {
            "ticker": ["AAPL", "MSFT", "OTCX"],
            "cik": ["0000320193", "0000789019", "0000123456"],
            "title": ["Apple Inc.", "Microsoft Corp.", "OTC Example"],
            "exchange": ["Nasdaq", "NYSE", "OTC"],
        }
    )

    fetched: list[tuple[str, int]] = []

    def fakeBuildEdgarCollectibleUniverse(
        *, limit: int = 2000, sinceYear: int = 2009, forceRefresh: bool = False
    ) -> pl.DataFrame:
        return universe

    def fakeFetchEdgarDocs(ticker: str, outPath: Path, *, sinceYear: int = 2009, maxFilings=None) -> Path:
        fetched.append((ticker, sinceYear))
        outPath.parent.mkdir(parents=True, exist_ok=True)
        pl.DataFrame({"ticker": [ticker]}).write_parquet(outPath)
        return outPath

    monkeypatch.setattr(
        "dartlab.engines.edgar.docs.fetch.buildEdgarCollectibleUniverse", fakeBuildEdgarCollectibleUniverse
    )
    monkeypatch.setattr("dartlab.engines.edgar.docs.fetch.fetchEdgarDocs", fakeFetchEdgarDocs)

    result = downloadListedEdgarDocs(limit=10, sinceYear=2009, batchSize=0, cooldownSeconds=0)

    assert fetched == [("AAPL", 2009), ("MSFT", 2009), ("OTCX", 2009)]
    assert result.filter(pl.col("status") == "downloaded").height == 3


def test_findFilings_includes_40f_and_excludes_6k():
    from dartlab.engines.edgar.docs.fetch import _findFilings

    submissions = {
        "cik": "0001308648",
        "filings": {
            "recent": {
                "form": ["6-K", "40-F", "20-F", "10-Q"],
                "filingDate": ["2025-01-10", "2024-03-01", "2023-03-01", "2024-05-10"],
                "reportDate": ["", "2023-12-31", "2022-12-31", "2024-03-31"],
                "accessionNumber": ["a", "b", "c", "d"],
                "primaryDocument": ["a.htm", "b.htm", "c.htm", "d.htm"],
            },
            "files": [],
        },
    }

    filings = _findFilings(submissions, 2009)

    assert [row["formType"] for row in filings] == ["20-F", "40-F", "10-Q"]


def test_periodKey_treats_40f_as_annual():
    from dartlab.engines.edgar.docs.fetch import _periodKey

    assert _periodKey("40-F", "2024-12-31", "2025") == "2024"
    assert _periodKey("40-F", None, "2024") == "2024"


def test_summarizeEdgarDocsFrame_flags_unexpected_full_document():
    from dartlab.engines.edgar.docs.fetch import summarizeEdgarDocsFrame

    df = pl.DataFrame(
        {
            "accession_no": ["a1", "a1", "a2"],
            "form_type": ["10-K", "10-K", "40-F"],
            "section_title": ["Full Document", "Item 1. Business", "Full Document"],
            "section_content": ["alpha", "| x | y |", "gamma"],
        }
    )

    summary = summarizeEdgarDocsFrame(df)

    assert summary["rows_saved"] == 3
    assert summary["filings_saved"] == 2
    assert summary["forms_found"] == ["10-K", "40-F"]
    assert summary["table_rows"] == 1
    assert "unexpected_full_document:10-K" in summary["quality_flags"]


def test_summarizeEdgarDocsFrame_allows_40f_full_document_fallback():
    from dartlab.engines.edgar.docs.fetch import summarizeEdgarDocsFrame

    df = pl.DataFrame(
        {
            "accession_no": ["a1"],
            "form_type": ["40-F"],
            "section_title": ["Full Document"],
            "section_content": ["plain text"],
        }
    )

    summary = summarizeEdgarDocsFrame(df)

    assert summary["quality_flags"] == []
    assert summary["full_document_rows"] == 1


def test_dedupeIssuerUniverse_prefers_base_ticker():
    from dartlab.engines.edgar.docs.fetch import _dedupeIssuerUniverse

    df = pl.DataFrame(
        {
            "ticker": ["AGM-PD", "AGM", "AGM-PE", "BRK-B", "BRK-A"],
            "cik": ["0001001", "0001001", "0001001", "0001002", "0001002"],
            "title": ["Farm Credit", "Farm Credit", "Farm Credit", "Berkshire", "Berkshire"],
            "exchange": ["NYSE", "NYSE", "NYSE", "NYSE", "NYSE"],
        }
    )

    result = _dedupeIssuerUniverse(df)

    assert result["ticker"].to_list() == ["AGM", "BRK-A"]


def test_interleaveIssuerUniverse_spreads_tickers_across_buckets():
    from dartlab.engines.edgar.docs.fetch import _interleaveIssuerUniverse

    df = pl.DataFrame(
        {
            "ticker": ["AAPL", "AAON", "AMZN", "BRK-A", "BMY", "C", "CRM"],
            "cik": ["1", "2", "3", "4", "5", "6", "7"],
            "title": ["a", "b", "c", "d", "e", "f", "g"],
            "exchange": ["Nasdaq"] * 7,
        }
    )

    result = _interleaveIssuerUniverse(df)

    assert result["ticker"].to_list() == ["AAON", "BMY", "C", "AAPL", "BRK-A", "CRM", "AMZN"]


def test_prepareEdgarCollectibleUniverse_writes_incremental_cache_and_progress(monkeypatch, tmp_path):
    from dartlab import config
    from dartlab.engines.edgar.docs.fetch import prepareEdgarCollectibleUniverse

    monkeypatch.setattr(config, "dataDir", str(tmp_path / "data"))

    listed = pl.DataFrame(
        {
            "ticker": ["AAPL", "BMY", "CRM"],
            "cik": ["0001", "0002", "0003"],
            "title": ["Apple", "Bristol", "Salesforce"],
            "exchange": ["Nasdaq", "NYSE", "NYSE"],
            "is_exchange_listed": [True, True, True],
        }
    )

    def fakeLoadListedUniverse():
        return listed

    def fakeGetSubmissions(cik: str):
        formMap = {
            "0001": ["10-K", "10-Q"],
            "0002": [],
            "0003": ["20-F"],
        }
        forms = formMap[cik]
        return {
            "cik": cik,
            "filings": {
                "recent": {
                    "form": forms,
                    "filingDate": ["2025-01-01"] * len(forms),
                    "reportDate": ["2024-12-31"] * len(forms),
                    "accessionNumber": [f"{cik}-{idx}" for idx in range(len(forms))],
                    "primaryDocument": [f"{idx}.htm" for idx in range(len(forms))],
                },
                "files": [],
            },
        }

    monkeypatch.setattr("dartlab.core.dataLoader.loadEdgarListedUniverse", fakeLoadListedUniverse)
    monkeypatch.setattr("dartlab.engines.edgar.docs.fetch._getSubmissions", fakeGetSubmissions)

    progressPath = tmp_path / "universe.progress.jsonl"
    result = prepareEdgarCollectibleUniverse(limit=2, sinceYear=2009, progressPath=progressPath, flushEvery=1)

    assert result["ticker"].to_list() == ["AAPL", "CRM"]
    assert result["candidate_order"].to_list() == [1, 2]
    assert result["supported_regular_forms"].to_list() == ["10-K,10-Q", "20-F"]

    cachePath = tmp_path / "data" / "edgar" / "docsCollectibleUniverse.parquet"
    assert cachePath.exists()
    assert progressPath.exists()
    progressLines = progressPath.read_text(encoding="utf-8").strip().splitlines()
    assert len(progressLines) == 3
    assert '"status": "supported"' in progressLines[0]
    assert any('"status": "unsupported_regular_forms"' in line for line in progressLines)


def test_download_batch_classifies_failure_kinds():
    import importlib.util
    from pathlib import Path

    import requests

    root = Path(__file__).resolve().parents[1]
    scriptPath = root / "experiments" / "057_edgarSectionMap_fail" / "002_downloadFirst2000.py"
    spec = importlib.util.spec_from_file_location("exp057_download", scriptPath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module._classifyFailure("A filing 없음", ValueError("A filing 없음")) == "no_supported_regular_filing"
    assert module._classifyFailure("section 추출 실패", ValueError("section 추출 실패")) == "parse_error"
    assert (
        module._classifyFailure("TLS CA certificate bundle", OSError("TLS CA certificate bundle")) == "legacy_env_error"
    )
    assert module._classifyFailure("timed out", TimeoutError("timed out")) == "fetch_timeout"
    assert module._classifyFailure("network", requests.RequestException("network")) == "fetch_error"
    assert module._classifyFailure("disk", OSError("disk")) == "storage_error"


def test_download_batch_lock_blocks_duplicate_run(tmp_path):
    import importlib.util
    from pathlib import Path

    import pytest

    root = Path(__file__).resolve().parents[1]
    scriptPath = root / "experiments" / "057_edgarSectionMap_fail" / "002_downloadFirst2000.py"
    spec = importlib.util.spec_from_file_location("exp057_download_lock", scriptPath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    lockPath = tmp_path / "download.lock"
    module._acquireLock(lockPath)
    try:
        with pytest.raises(RuntimeError, match="already running"):
            module._acquireLock(lockPath)
    finally:
        module._releaseLock(lockPath)


def test_download_batch_load_completed_requires_existing_parquet(tmp_path):
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scriptPath = root / "experiments" / "057_edgarSectionMap_fail" / "002_downloadFirst2000.py"
    spec = importlib.util.spec_from_file_location("exp057_download_completed", scriptPath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    docsDir = tmp_path / "docs"
    docsDir.mkdir()
    progressPath = tmp_path / "download.progress.jsonl"
    progressPath.write_text(
        "\n".join(
            [
                json.dumps({"ticker": "AAPL", "status": "downloaded", "path": str(docsDir / "AAPL.parquet")}),
                json.dumps({"ticker": "MSFT", "status": "downloaded", "path": str(docsDir / "MSFT.parquet")}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (docsDir / "MSFT.parquet").write_bytes(b"PAR1")

    completed = module._loadCompleted(progressPath, docsDir)

    assert completed == {"MSFT"}


def test_download_batch_prepare_state_archives_stale_progress(tmp_path):
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    scriptPath = root / "experiments" / "057_edgarSectionMap_fail" / "002_downloadFirst2000.py"
    spec = importlib.util.spec_from_file_location("exp057_download_state", scriptPath)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    docsDir = tmp_path / "docs"
    docsDir.mkdir()
    progressPath = tmp_path / "download.progress.jsonl"
    heartbeatPath = tmp_path / "download.heartbeat.json"
    monitorPath = tmp_path / "download.monitor.json"
    progressPath.write_text("old\n", encoding="utf-8")
    heartbeatPath.write_text("{}", encoding="utf-8")
    monitorPath.write_text("{}", encoding="utf-8")

    runId = module._prepareBatchState(
        docsDir=docsDir,
        progressPath=progressPath,
        heartbeatPath=heartbeatPath,
        monitorPath=monitorPath,
    )

    assert not progressPath.exists()
    assert not heartbeatPath.exists()
    assert not monitorPath.exists()
    assert len(list(tmp_path.glob(f"download.progress.stale-{runId}.jsonl"))) == 1
    assert len(list(tmp_path.glob(f"download.heartbeat.stale-{runId}.json"))) == 1
    assert len(list(tmp_path.glob(f"download.monitor.stale-{runId}.json"))) == 1


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
    assert "blockType" in df.columns
    # 연간 보고서는 Q4 라벨로 통일 (2024 → 2024Q4)
    assert "2024Q4" in df.columns or "2024" in df.columns
    assert "2024Q1" in df.columns
    assert "10-K::item1Business" in df["topic"].to_list()
    metaCols = {"topic", "blockType", "blockOrder", "textNodeType", "textLevel", "textPath"}
    periodCols = [c for c in df.columns if c not in metaCols]
    # 기간 정렬은 descending (최신 먼저)
    assert periodCols == sortPeriods(periodCols, descending=True)


def test_edgar_sections_pipeline_supports_form_native_structured_topics(tmp_path, monkeypatch):
    import importlib

    from dartlab.engines.edgar.docs.sections import sections

    pipelineModule = importlib.import_module("dartlab.engines.edgar.docs.sections.pipeline")

    df = pl.DataFrame(
        {
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
        }
    )
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

    assert sortPeriods(["2024", "2024Q1", "2023", "2024Q3"]) == ["2023", "2024Q1", "2024Q3", "2024"]
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
    assert (
        items[1]["title"]
        == "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
    )
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
    assert (
        "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
        in titles
    )
    assert "Part II - Item 1. Legal Proceedings" in titles
    assert "Part II - Item 1A. Risk Factors" in titles


def test_splitItems_splits_quarterly_items_with_en_dash_titles():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
PART I. FINANCIAL INFORMATION
Item 1 – Financial Statements
Quarterly statements body
Item 2 – Management's Discussion and Analysis of Financial Condition and Results of Operations
MD&A body
Item 3 – Quantitative and Qualitative Disclosures About Market Risk
Risk body
Item 4 – Controls and Procedures
Controls body
PART II. OTHER INFORMATION
Item 1 – Legal Proceedings
Legal body
Item 1A – Risk Factors
Risk factors body
Item 6 – Exhibits
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    titles = [item["title"] for item in items]
    assert "Part I - Item 1. Financial Statements" in titles
    assert (
        "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
        in titles
    )
    assert "Part II - Item 1A. Risk Factors" in titles


def test_splitItems_splits_quarterly_items_with_split_part_and_title_lines():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
PART
I – FINANCIAL INFORMATION
Item 1 – Financial
Statements
Quarterly statements body
Item 2 – Management’s
Discussion and Analysis of Financial Condition and Results of Operations
MD&A body
Item 3 – Quantitative and
Qualitative Disclosures About Market Risk
Risk body
Item 4 – Controls and
Procedures
Controls body
PART II
Item 1 – Legal
Proceedings
Legal body
Item 1A – Risk
Factors
Risk factors body
Item 6 –
Exhibits
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    titles = [item["title"] for item in items]
    assert "Part I - Item 1. Financial Statements" in titles
    assert (
        "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
        in titles
    )
    assert "Part II - Item 1A. Risk Factors" in titles


def test_splitItems_prefers_quarterly_body_items_over_toc_items():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
TABLE OF CONTENTS
| PART I. FINANCIAL INFORMATION |  |  | Page |  |  |
| Item 1: | Financial Statements |  |  |  |  |
| Item 2: | Management's Discussion and Analysis of Financial Condition and Results of Operations |  |  |  |  |
| Item 3: | Quantitative and Qualitative Disclosures About Market Risk |  |  | 40 |  |
| Item 4: | Controls and Procedures |  |  | 41 |  |
| PART II. OTHER INFORMATION |  |  |  |  |  |
| Item 1A: | Risk Factors |  |  | 42 |  |
| Item 6: | Exhibits |  |  | 42 |  |
| PART I. | FINANCIAL INFORMATION |
| Item 1. | Financial Statements |
Financial statements body
| Item 2. | Management's Discussion and Analysis of Financial Condition and Results of Operations |
MD&A body
| Item 3. | Quantitative and Qualitative Disclosures About Market Risk |
Market risk body
| Item 4. | Controls and Procedures |
Controls body
| PART II. | OTHER INFORMATION |
| Item 1A. | Risk Factors |
Risk factors body
| Item 6. | Exhibits |
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    titles = [item["title"] for item in items]
    assert titles == [
        "Part I - Item 1. Financial Statements",
        "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations",
        "Part I - Item 3. Quantitative and Qualitative Disclosures About Market Risk",
        "Part I - Item 4. Controls and Procedures",
        "Part II - Item 1A. Risk Factors",
        "Part II - Item 6. Exhibits",
    ]
    assert "Market risk body" in items[2]["content"]
    assert "Risk factors body" in items[4]["content"]


def test_splitItems_splits_quarterly_items_with_item_number_on_next_line():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
PART I. FINANCIAL INFORMATION
| Item 1. | Financial Statements |
Financial statements body
Item
2. Management's Discussion and Analysis of Financial Condition and Results of Operations
MD&A body
Item
3. Quantitative and Qualitative Disclosures About Market Risk
Risk body
Item
4. Controls and Procedures
Controls body
PART II. OTHER INFORMATION
Item
1A. Risk Factors
Risk factors body
Item
6. Exhibits
Exhibits body
""".strip()

    items = _splitItems(text, "10-Q")

    titles = [item["title"] for item in items]
    assert (
        "Part I - Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations"
        in titles
    )
    assert "Part I - Item 3. Quantitative and Qualitative Disclosures About Market Risk" in titles
    assert "Part II - Item 1A. Risk Factors" in titles


def test_splitItems_splits_10k_from_table_rows():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
| PART I |  |  |  |
| Item 1 |  | Business |  |
Business body
More business body
| Item 1A |  | Risk Factors |  |
Risk body
| Item 7 |  | Management's Discussion and Analysis of Financial Condition and Results of Operations |  |
MD&A body
| Item 8 |  | Financial Statements and Supplementary Data |  |
Financial body
""".strip()

    items = _splitItems(text, "10-K")

    titles = [item["title"] for item in items]
    assert "Item 1. Business" in titles
    assert "Item 1A. Risk Factors" in titles
    assert "Item 7. MD&A" in titles
    assert "Item 8. Financial Statements" in titles


def test_splitItems_prefers_10k_body_table_items_over_toc_rows():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
Table of Contents
| Item 1. |  | Business |  | 6 |
| Item 1A. |  | Risk Factors |  | 26 |
| Item 7. |  | Management's Discussion and Analysis of Financial Condition and Results of Operations |  | 57 |
| Item 8. |  | Financial Statements and Supplementary Data |  | 65 |
Part I
| Item 1. |  | Business |  |  |
Business body
| Item 1A. |  | Risk Factors |  |  |
Risk factors body
Part II
| Item 7. |  | Management's Discussion and Analysis of Financial Condition and Results of Operations |  |  |
MD&A body
| Item 8. |  | Financial Statements and Supplementary Data |  |  |
Financial body
""".strip()

    items = _splitItems(text, "10-K")

    assert "Business body" in items[0]["content"]
    assert "Risk factors body" in items[1]["content"]
    assert "MD&A body" in items[2]["content"]
    assert "Financial body" in items[3]["content"]


def test_splitItems_prefers_10k_body_items_over_toc_item_lines():
    from dartlab.engines.edgar.docs.fetch import _splitItems

    text = """
Table of Contents
Item 1. Business
Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
Item 8. Financial Statements and Supplementary Data
Part I
Item 1. Business
Business body
Part II
Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
MD&A body
Item 8. Financial Statements and Supplementary Data
Financial body
""".strip()

    items = _splitItems(text, "10-K")

    titles = [item["title"] for item in items]
    assert titles == [
        "Item 1. Business",
        "Item 7. MD&A",
        "Item 8. Financial Statements",
    ]
    assert "Business body" in items[0]["content"]
    assert "MD&A body" in items[1]["content"]
    assert "Financial body" in items[2]["content"]


def test_submissionTextUrl_uses_accession_txt_name():
    from dartlab.engines.edgar.docs.fetch import _filingIndexJsonUrl, _submissionTextUrl

    filing = {
        "accessionNumber": "0001907982-24-000049",
        "filingUrl": "https://www.sec.gov/Archives/edgar/data/0001907982/000190798224000049/qbts-20231231.htm",
    }

    assert _submissionTextUrl(filing) == (
        "https://www.sec.gov/Archives/edgar/data/0001907982/000190798224000049/0001907982-24-000049.txt"
    )
    assert _filingIndexJsonUrl(filing) == (
        "https://www.sec.gov/Archives/edgar/data/0001907982/000190798224000049/index.json"
    )


def test_classify40FDocumentName_identifies_supporting_documents():
    from dartlab.engines.edgar.docs.fetch import _classify40FDocumentName

    assert _classify40FDocumentName("a997-annualinformationfo.htm") == "Annual Information Form"
    assert _classify40FDocumentName("mda20250331q42025.htm") == "MD&A"
    assert _classify40FDocumentName("acb-20250331_d2.htm") == "Financial Statements"
    assert _classify40FDocumentName("exhibit311-ye2023.htm") is None


def test_split40FPrimaryText_splits_uppercase_headings():
    from dartlab.engines.edgar.docs.fetch import _split40FPrimaryText

    text = """
FORM 40-F
ANNUAL INFORMATION FORM
Annual info body
AUDITED ANNUAL FINANCIAL STATEMENTS
Financial statements body
MANAGEMENT'S DISCUSSION AND ANALYSIS
MD&A body
CASH REQUIREMENTS
Cash requirement body
EXHIBIT INDEX
Exhibit body
""".strip()

    items = _split40FPrimaryText(text)

    assert [item["title"] for item in items] == [
        "Annual Information Form",
        "Audited Annual Financial Statements",
        "Management'S Discussion And Analysis",
        "Cash Requirements",
        "Exhibit Index",
    ]
    assert "MD&A body" in items[2]["content"]


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


def test_priorityTickerCollection_load_completed_requires_existing_parquet(tmp_path):
    import importlib

    module = importlib.import_module("experiments.057_edgarSectionMap_fail.018_priorityTickerCollection")

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    progress_path = tmp_path / "priority.progress.jsonl"
    progress_path.write_text(
        "\n".join(
            [
                json.dumps({"ticker": "AAPL", "status": "downloaded"}),
                json.dumps({"ticker": "MSFT", "status": "failed"}),
            ]
        ),
        encoding="utf-8",
    )

    completed = module._load_completed(progress_path, docs_dir)
    assert completed == set()

    (docs_dir / "AAPL.parquet").write_text("stub", encoding="utf-8")
    completed = module._load_completed(progress_path, docs_dir)
    assert completed == {"AAPL"}


_HAS_EDGAR_TICKERS = (Path(__file__).resolve().parents[1] / "data" / "edgar" / "tickers.parquet").exists()
_skipNoEdgarTickers = pytest.mark.skipif(
    not _HAS_EDGAR_TICKERS,
    reason="EDGAR tickers.parquet 없음",
)


@_skipNoEdgarTickers
class TestEdgarCompanyInterface:
    def test_index_returns_dataframe_with_required_columns(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        idx = c.index
        assert isinstance(idx, pl.DataFrame)
        assert idx.height > 0
        assert set(["topic", "kind", "source", "periods", "shape", "preview"]).issubset(set(idx.columns))

    def test_index_includes_finance_and_docs(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        idx = c.index
        topics = idx["topic"].to_list()
        assert "BS" in topics
        assert "IS" in topics
        assert "CF" in topics
        assert "ratios" in topics
        docTopics = [t for t in topics if "::" in t]
        assert len(docTopics) > 0

    def test_show_finance_returns_dataframe(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        for stmt in ("BS", "IS", "CF"):
            df = c.show(stmt)
            assert isinstance(df, pl.DataFrame)
            assert df.height > 0

    def test_show_ratios_returns_block_index_and_data(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        idx = c.show("ratios")
        assert isinstance(idx, pl.DataFrame)
        assert "block" in idx.columns
        df = c.show("ratios", 0)
        assert isinstance(df, pl.DataFrame)
        assert "category" in df.columns

    def test_show_docs_topic_returns_dataframe(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        biz = c.show("10-K::item1Business")
        assert biz is None or isinstance(biz, pl.DataFrame)

    def test_show_nonexistent_topic_returns_none(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        assert c.show("completelyFakeTopic") is None

    def test_trace_finance_topic(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        traced = c.trace("BS")
        assert traced is not None
        assert traced["primarySource"] == "finance"
        assert traced["topic"] == "BS"

    def test_trace_ratios_topic(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        traced = c.trace("ratios")
        assert traced is not None
        assert traced["primarySource"] == "finance"
        assert "rowCount" in traced
        assert "yearCount" in traced
        assert "coverage" in traced
        assert traced["coverage"] in ("full", "partial", "missing")

    def test_trace_docs_topic(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        traced = c.trace("10-K::item1Business")
        assert traced is not None
        assert traced["primarySource"] == "docs"

    def test_trace_nonexistent_returns_none(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        assert c.trace("completelyFakeTopic") is None

    def test_topics_list_is_ordered(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        topics = c.topics
        assert isinstance(topics, pl.DataFrame)
        topicList = topics["topic"].to_list()
        assert topicList[:5] == ["BS", "IS", "CF", "CIS", "ratios"]

    def test_show_with_block_and_period_filter(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        df = c.show("BS", 0, period="2024")
        assert isinstance(df, pl.DataFrame)
        assert "2024" in df.columns

    def test_filings_returns_dataframe(self):
        from dartlab.engines.edgar.company import Company

        c = Company("AAPL")
        f = c.filings()
        assert f is None or isinstance(f, pl.DataFrame)
