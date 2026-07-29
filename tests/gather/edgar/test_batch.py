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
