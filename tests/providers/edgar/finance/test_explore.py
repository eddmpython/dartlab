"""providers/edgar/finance/explore.py mirror smoke — P6."""

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.finance.explore  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_explore_callable() -> None:
    """explore() callable smoke."""
    from dartlab.providers.edgar.finance.explore import explore

    assert callable(explore)


def test_iter_tags_callable() -> None:
    """iterTags() callable smoke."""
    from dartlab.providers.edgar.finance.explore import iterTags

    assert callable(iterTags)


def test_list_tags_callable() -> None:
    """listTags() callable smoke."""
    from dartlab.providers.edgar.finance.explore import listTags

    assert callable(listTags)


def test_list_tags_maps_ifrs_full_taxonomy(tmp_path: Path) -> None:
    from dartlab.providers.edgar.finance.explore import listTags

    pl.DataFrame(
        {
            "namespace": ["ifrs-full", "ifrs-full"],
            "tag": ["ProfitLoss", "ProfitLoss"],
        }
    ).write_parquet(tmp_path / "0000000001.parquet")

    result = listTags("0000000001", edgarDir=tmp_path)

    assert result is not None
    assert result.to_dicts() == [{"tag": "ProfitLoss", "count": 2, "snakeId": "net_profit", "stmt": "IS"}]
