"""gather/edgar/batch.py mirror smoke — P6."""

import os
from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.gather.edgar.batch  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_batch_collect_edgar_callable() -> None:
    """batchCollectEdgar() callable smoke."""
    from dartlab.gather.edgar.batch import batchCollectEdgar

    assert callable(batchCollectEdgar)


def test_batch_collect_edgar_all_callable() -> None:
    """batchCollectEdgarAll() callable smoke."""
    from dartlab.gather.edgar.batch import batchCollectEdgarAll

    assert callable(batchCollectEdgarAll)


def test_commit_staged_artifacts_rolls_back_every_category(tmp_path: Path, monkeypatch) -> None:
    from dartlab.gather.edgar.batch import _commitStagedArtifacts, _StagedArtifact

    financeDest = tmp_path / "finance.parquet"
    docsDest = tmp_path / "docs.parquet"
    financeTemp = tmp_path / "finance.tmp.parquet"
    docsTemp = tmp_path / "docs.tmp.parquet"
    pl.DataFrame({"value": ["old-finance"]}).write_parquet(financeDest)
    pl.DataFrame({"value": ["old-docs"]}).write_parquet(docsDest)
    pl.DataFrame({"value": ["new-finance"]}).write_parquet(financeTemp)
    pl.DataFrame({"value": ["new-docs"]}).write_parquet(docsTemp)

    originalReplace = os.replace
    failed = False

    def _replace(source, destination) -> None:
        nonlocal failed
        if Path(source) == docsTemp and Path(destination) == docsDest and not failed:
            failed = True
            raise OSError("docs commit failed")
        originalReplace(source, destination)

    monkeypatch.setattr(os, "replace", _replace)
    artifacts = [
        _StagedArtifact("finance", financeDest, financeTemp, 1),
        _StagedArtifact("docs", docsDest, docsTemp, 1),
    ]

    with pytest.raises(OSError, match="docs commit failed"):
        _commitStagedArtifacts(artifacts)

    assert pl.read_parquet(financeDest)["value"].to_list() == ["old-finance"]
    assert pl.read_parquet(docsDest)["value"].to_list() == ["old-docs"]
    assert not financeTemp.exists()
    assert not docsTemp.exists()


def test_batch_failure_preserves_previous_files_and_provenance(tmp_path: Path, monkeypatch) -> None:
    import dartlab.gather.edgar.batch as batch

    financeDest = tmp_path / "finance.parquet"
    financeTemp = tmp_path / "finance.tmp.parquet"
    pl.DataFrame({"value": ["old"]}).write_parquet(financeDest)

    class _Client:
        exhausted = False

        async def close(self) -> None:
            return None

    async def _finance(*args, **kwargs):
        pl.DataFrame({"value": ["new"]}).write_parquet(financeTemp)
        return batch._StagedArtifact("finance", financeDest, financeTemp, 1)

    async def _docs(*args, **kwargs):
        raise ValueError("invalid docs payload")

    monkeypatch.setattr(batch, "AsyncEdgarClient", _Client)
    monkeypatch.setattr(
        batch,
        "_resolveTickerMap",
        lambda tickers: {"AAPL": {"cik": "0000320193", "title": "Apple"}},
    )
    monkeypatch.setattr(batch, "_collectEdgarFinance", _finance)
    monkeypatch.setattr(batch, "_collectEdgarDocs", _docs)

    with pytest.raises(batch.EdgarBatchCollectionError) as excInfo:
        batch.batchCollectEdgar(["AAPL"], maxWorkers=1, showProgress=False)

    error = excInfo.value
    assert error.partialResults == {}
    assert error.failures["AAPL"] == {
        "category": "docs",
        "errorType": "ValueError",
        "message": "invalid docs payload",
    }
    assert pl.read_parquet(financeDest)["value"].to_list() == ["old"]
    assert not financeTemp.exists()


def test_batch_incremental_skip_is_success_not_failure(monkeypatch) -> None:
    import dartlab.gather.edgar.batch as batch

    class _Client:
        exhausted = False

        async def close(self) -> None:
            return None

    async def _finance(*args, **kwargs):
        return batch._StagedArtifact("finance", Path("unused.parquet"), None, 0)

    monkeypatch.setattr(batch, "AsyncEdgarClient", _Client)
    monkeypatch.setattr(
        batch,
        "_resolveTickerMap",
        lambda tickers: {"AAPL": {"cik": "0000320193", "title": "Apple"}},
    )
    monkeypatch.setattr(batch, "_collectEdgarFinance", _finance)

    result = batch.batchCollectEdgar(
        ["AAPL"],
        categories=["finance"],
        maxWorkers=1,
        showProgress=False,
    )

    assert result == {"AAPL": {"finance": 0}}


def test_batch_docs_not_applicable_is_skip_not_failure(tmp_path: Path, monkeypatch) -> None:
    """정기보고서가 없는 ticker(폐쇄형 펀드 등) 는 batch 실패가 아니라 0 행 skip 이다.

    예전에는 7,720 ticker 중 약 500 곳이 "filing 없음" 으로 실패로 집계돼 주간 docs 수집이
    다른 결함이 없어도 반드시 실패했다.
    """
    import dartlab.gather.edgar.batch as batch
    from dartlab.gather.edgar.docs import fetch

    class _Client:
        exhausted = False

        async def close(self) -> None:
            return None

    def _noFilings(ticker, outPath, **kwargs):
        raise fetch.EdgarDocsNotApplicableError(f"{ticker} EDGAR docs filing 없음 (since 2009)")

    monkeypatch.setattr(batch, "AsyncEdgarClient", _Client)
    monkeypatch.setattr(batch, "_resolveTickerMap", lambda tickers: {"PDI": {"cik": "0001510599", "title": "PIMCO"}})
    docsDir = tmp_path / "edgarDocs"
    docsDir.mkdir()
    monkeypatch.setattr(batch, "_edgarDataPath", lambda category, key: docsDir / f"{key}.parquet")
    monkeypatch.setattr(fetch, "fetchEdgarDocs", _noFilings)

    result = batch.batchCollectEdgar(["PDI"], categories=["docs"], maxWorkers=1, showProgress=False)

    assert result == {"PDI": {"docs": 0}}
    assert list(docsDir.iterdir()) == []  # 임시 산출물 잔존 없음


def test_docs_not_applicable_error_stays_value_error() -> None:
    """기존 ``except ValueError`` 호출자가 계속 잡을 수 있게 ValueError 하위 계약을 지킨다."""
    from dartlab.gather.edgar.docs.fetch import EdgarDocsNotApplicableError

    assert issubclass(EdgarDocsNotApplicableError, ValueError)
