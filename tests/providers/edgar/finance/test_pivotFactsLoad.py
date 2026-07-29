"""mirror smoke — edgar/finance/pivotFactsLoad.py (split helper).

분할 helper 모듈의 임포트 가능성 + 룰 7 mirror 슬롯 충족.
"""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

pytestmark = pytest.mark.unit


def test_import() -> None:
    import dartlab.providers.edgar.finance.pivotFactsLoad as mod

    assert mod is not None


def test_load_facts_keeps_ifrs_full_for_foreign_issuer(tmp_path: Path) -> None:
    from dartlab.providers.edgar.finance.pivotFactsLoad import _loadFacts

    pl.DataFrame(
        {
            "namespace": ["ifrs-full", "dei"],
            "tag": ["Revenue", "EntityRegistrantName"],
        }
    ).write_parquet(tmp_path / "0000000001.parquet")

    result = _loadFacts(tmp_path, "0000000001")

    assert result is not None
    assert result["namespace"].unique().to_list() == ["ifrs-full"]
    assert result["tag"].to_list() == ["Revenue"]


def test_load_facts_prefers_us_gaap_when_both_taxonomies_exist(tmp_path: Path) -> None:
    from dartlab.providers.edgar.finance.pivotFactsLoad import _loadFacts

    pl.DataFrame(
        {
            "namespace": ["ifrs-full", "us-gaap"],
            "tag": ["Revenue", "Revenues"],
        }
    ).write_parquet(tmp_path / "0000000002.parquet")

    result = _loadFacts(tmp_path, "0000000002")

    assert result is not None
    assert result.to_dicts() == [{"namespace": "us-gaap", "tag": "Revenues"}]


def test_load_facts_rejects_unsupported_taxonomy_with_capability_context(tmp_path: Path) -> None:
    from dartlab.providers.edgar.finance.pivotFactsLoad import _loadFacts

    pl.DataFrame({"namespace": ["custom-gaap"], "tag": ["Revenue"]}).write_parquet(tmp_path / "0000000003.parquet")

    with pytest.raises(ValueError, match=r"available=custom-gaap.*supported=us-gaap, ifrs-full"):
        _loadFacts(tmp_path, "0000000003")
